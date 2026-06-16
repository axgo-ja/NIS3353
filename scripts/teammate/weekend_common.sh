#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_ROOT="${WANET_WEEKEND_RUN_ROOT:-${REPO_ROOT}/logs/weekend_20260614}"
USE_DEADLINE_GATING="${WANET_WEEKEND_USE_DEADLINE:-0}"
DEADLINE_STRING="${WANET_WEEKEND_DEADLINE:-2026-06-14 12:00:00}"
BUFFER_MINUTES="${WANET_WEEKEND_BUFFER_MINUTES:-20}"

if [[ "${USE_DEADLINE_GATING}" == "1" ]]; then
  DEADLINE_TS="$(date -d "${DEADLINE_STRING}" +%s)"
else
  DEADLINE_TS=""
fi

mkdir -p "${RUN_ROOT}/jobs" "${RUN_ROOT}/locks"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

ensure_model_env() {
  source /home/zilia/conda/etc/profile.d/conda.sh
  conda activate model
}

init_worker() {
  WORKER_NAME="$1"
  ensure_model_env
  printf '%s\n' "running" > "${RUN_ROOT}/${WORKER_NAME}.status"
  printf '%s\n' "$(timestamp)" > "${RUN_ROOT}/${WORKER_NAME}.started_at"
  : > "${RUN_ROOT}/${WORKER_NAME}.current"
}

finish_worker() {
  printf '%s\n' "completed" > "${RUN_ROOT}/${WORKER_NAME}.status"
  printf '%s\n' "$(timestamp)" > "${RUN_ROOT}/${WORKER_NAME}.finished_at"
  log_msg "worker completed"
}

fail_worker() {
  printf '%s\n' "failed" > "${RUN_ROOT}/${WORKER_NAME}.status"
  printf '%s\n' "$(timestamp)" > "${RUN_ROOT}/${WORKER_NAME}.finished_at"
  log_msg "worker failed"
}

log_msg() {
  local msg="$1"
  echo "$(timestamp) [${WORKER_NAME}] ${msg}" | tee -a "${RUN_ROOT}/controller.log"
}

append_summary() {
  local job_id="$1"
  local state="$2"
  printf '%s\t%s\t%s\t%s\n' "$(timestamp)" "${WORKER_NAME}" "${job_id}" "${state}" >> "${RUN_ROOT}/summary.tsv"
}

remaining_minutes() {
  if [[ "${USE_DEADLINE_GATING}" != "1" ]]; then
    echo 999999
    return 0
  fi
  local now_ts
  now_ts="$(date +%s)"
  echo $(( (DEADLINE_TS - now_ts) / 60 ))
}

enough_time_for() {
  local estimate_minutes="$1"
  if [[ "${USE_DEADLINE_GATING}" != "1" ]]; then
    return 0
  fi
  local remain
  remain="$(remaining_minutes)"
  (( remain >= estimate_minutes + BUFFER_MINUTES ))
}

gpu_free_mb() {
  local gpu_index="$1"
  nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | sed -n "$((gpu_index + 1))p"
}

wait_for_gpu() {
  local gpu_index="$1"
  local min_free_mb="$2"
  local poll_seconds="${3:-60}"

  while true; do
    local free_mb
    free_mb="$(gpu_free_mb "${gpu_index}")"
    if [[ -n "${free_mb}" ]] && (( free_mb >= min_free_mb )); then
      break
    fi
    log_msg "waiting for GPU${gpu_index}: free=${free_mb:-unknown}MB need=${min_free_mb}MB"
    sleep "${poll_seconds}"
  done
}

wait_for_path() {
  local target_path="$1"
  local timeout_minutes="$2"
  local label="$3"
  local waited=0

  while [[ ! -e "${target_path}" ]]; do
    if (( waited >= timeout_minutes )); then
      log_msg "timeout while waiting for ${label}: ${target_path}"
      return 1
    fi
    log_msg "waiting for ${label}: ${target_path}"
    sleep 60
    waited=$((waited + 1))
  done
  return 0
}

run_logged_cmd() {
  local job_id="$1"
  local gpu_index="$2"
  local min_free_mb="$3"
  local retries="$4"
  local estimate_minutes="$5"
  local optional="$6"
  local success_marker="$7"
  local command="$8"
  local freshness_references="${9:-}"

  output_is_fresh() {
    local output_path="$1"
    local reference_paths="${2:-}"

    [[ -n "${output_path}" ]] || return 1
    [[ -e "${output_path}" ]] || return 1

    if [[ -z "${reference_paths}" ]]; then
      return 0
    fi

    local reference_path
    for reference_path in ${reference_paths}; do
      [[ -e "${reference_path}" ]] || return 1
      [[ "${output_path}" -nt "${reference_path}" ]] || return 1
    done
    return 0
  }

  if output_is_fresh "${success_marker}" "${freshness_references}"; then
    log_msg "skip ${job_id}: output is up to date"
    append_summary "${job_id}" "skipped_exists"
    return 0
  fi

  if [[ "${optional}" == "optional" ]] && ! enough_time_for "${estimate_minutes}"; then
    log_msg "skip ${job_id}: not enough time before deadline"
    append_summary "${job_id}" "skipped_deadline"
    return 0
  fi

  printf '%s\n' "${job_id}" > "${RUN_ROOT}/${WORKER_NAME}.current"

  local lock_dir="${RUN_ROOT}/locks/${job_id}"
  while true; do
    if output_is_fresh "${success_marker}" "${freshness_references}"; then
      log_msg "skip ${job_id}: output is up to date while waiting on lock"
      append_summary "${job_id}" "skipped_exists"
      return 0
    fi

    if mkdir "${lock_dir}" 2>/dev/null; then
      printf '%s\n' "$$" > "${lock_dir}/pid"
      printf '%s\n' "${WORKER_NAME}" > "${lock_dir}/worker"
      printf '%s\n' "$(timestamp)" > "${lock_dir}/started_at"
      break
    fi

    local lock_pid=""
    if [[ -f "${lock_dir}/pid" ]]; then
      lock_pid="$(cat "${lock_dir}/pid" 2>/dev/null || true)"
    fi

    if [[ -z "${lock_pid}" ]] || ! kill -0 "${lock_pid}" 2>/dev/null; then
      log_msg "removing stale lock for ${job_id}"
      rm -rf "${lock_dir}"
      sleep 1
      continue
    fi

    log_msg "waiting for lock on ${job_id} held by pid=${lock_pid}"
    sleep 60
  done

  local attempt=1
  while (( attempt <= retries )); do
    if [[ "${gpu_index}" != "cpu" ]]; then
      wait_for_gpu "${gpu_index}" "${min_free_mb}"
    fi

    local log_path="${RUN_ROOT}/jobs/${WORKER_NAME}_${job_id}_attempt${attempt}.log"
    log_msg "start ${job_id} attempt=${attempt}"
    append_summary "${job_id}" "start_attempt_${attempt}"

    if [[ "${gpu_index}" == "cpu" ]]; then
      if bash -lc "cd '${REPO_ROOT}' && ${command}" 2>&1 | tee "${log_path}"; then
        log_msg "done ${job_id}"
        append_summary "${job_id}" "done"
        rm -rf "${lock_dir}"
        return 0
      fi
    else
      if CUDA_VISIBLE_DEVICES="${gpu_index}" PYTHONUNBUFFERED=1 bash -lc "cd '${REPO_ROOT}' && ${command}" 2>&1 | tee "${log_path}"; then
        log_msg "done ${job_id}"
        append_summary "${job_id}" "done"
        rm -rf "${lock_dir}"
        return 0
      fi
    fi

    log_msg "fail ${job_id} attempt=${attempt}"
    append_summary "${job_id}" "fail_attempt_${attempt}"
    attempt=$((attempt + 1))
    sleep 60
  done

  log_msg "give up ${job_id}"
  append_summary "${job_id}" "failed"
  rm -rf "${lock_dir}"
  return 1
}

checkpoint_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/checkpoints/${dataset}/${dataset}_${attack_mode}_morph.pth.tar"
}

train_code_references() {
  echo "${REPO_ROOT}/train.py ${REPO_ROOT}/config.py ${REPO_ROOT}/utils/runtime.py ${REPO_ROOT}/utils/dataloader.py ${REPO_ROOT}/networks/models.py"
}

eval_code_references() {
  local dataset="$1"
  local attack_mode="$2"
  echo "$(checkpoint_path "${dataset}" "${attack_mode}") ${REPO_ROOT}/eval.py ${REPO_ROOT}/config.py ${REPO_ROOT}/utils/runtime.py ${REPO_ROOT}/utils/dataloader.py ${REPO_ROOT}/networks/models.py"
}

strip_code_references() {
  local dataset="$1"
  local attack_mode="$2"
  echo "$(checkpoint_path "${dataset}" "${attack_mode}") ${REPO_ROOT}/defenses/STRIP/STRIP.py ${REPO_ROOT}/defenses/STRIP/config.py ${REPO_ROOT}/utils/runtime.py ${REPO_ROOT}/utils/dataloader.py ${REPO_ROOT}/networks/models.py"
}

fine_pruning_code_references() {
  local dataset="$1"
  local attack_mode="$2"
  local script_path="$3"
  echo "$(checkpoint_path "${dataset}" "${attack_mode}") ${REPO_ROOT}/${script_path} ${REPO_ROOT}/defenses/fine_pruning/config.py ${REPO_ROOT}/utils/runtime.py ${REPO_ROOT}/utils/dataloader.py ${REPO_ROOT}/networks/models.py"
}

neural_cleanse_code_references() {
  local dataset="$1"
  local attack_mode="$2"
  echo "$(checkpoint_path "${dataset}" "${attack_mode}") ${REPO_ROOT}/defenses/neural_cleanse/neural_cleanse.py ${REPO_ROOT}/defenses/neural_cleanse/detecting.py ${REPO_ROOT}/defenses/neural_cleanse/config.py ${REPO_ROOT}/utils/runtime.py ${REPO_ROOT}/utils/dataloader.py ${REPO_ROOT}/networks/models.py"
}

path_is_fresh_against_refs() {
  local output_path="$1"
  local reference_paths="$2"

  [[ -e "${output_path}" ]] || return 1

  local reference_path
  for reference_path in ${reference_paths}; do
    [[ -e "${reference_path}" ]] || return 1
    [[ "${output_path}" -nt "${reference_path}" ]] || return 1
  done
  return 0
}

train_complete_is_fresh() {
  local dataset="$1"
  local attack_mode="$2"
  local train_refs
  train_refs="$(train_code_references)"

  path_is_fresh_against_refs "$(train_complete_marker_path "${dataset}" "${attack_mode}")" "${train_refs}" \
    && path_is_fresh_against_refs "$(checkpoint_path "${dataset}" "${attack_mode}")" "${train_refs}"
}

wait_for_train_complete() {
  local dataset="$1"
  local attack_mode="$2"
  local timeout_minutes="$3"
  local label="$4"
  local waited=0

  while ! train_complete_is_fresh "${dataset}" "${attack_mode}"; do
    if (( waited >= timeout_minutes )); then
      log_msg "timeout while waiting for ${label}: $(train_complete_marker_path "${dataset}" "${attack_mode}")"
      return 1
    fi
    log_msg "waiting for ${label}: $(train_complete_marker_path "${dataset}" "${attack_mode}")"
    sleep 60
    waited=$((waited + 1))
  done
  return 0
}

train_result_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/checkpoints/${dataset}/${attack_mode}/results.json"
}

train_complete_marker_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/checkpoints/${dataset}/${attack_mode}/train_complete.marker"
}

eval_result_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/checkpoints/${dataset}/${attack_mode}/eval_results.json"
}

strip_result_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/defenses/STRIP/results/${dataset}/${attack_mode}/${dataset}_${attack_mode}_output.txt"
}

fine_pruning_result_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/defenses/fine_pruning/results/${dataset}/${attack_mode}/${dataset}_${attack_mode}_results.txt"
}

neural_cleanse_result_path() {
  local dataset="$1"
  local attack_mode="$2"
  echo "${REPO_ROOT}/defenses/neural_cleanse/results/${dataset}/${attack_mode}/${attack_mode}_${dataset}_output.txt"
}

train_model() {
  local dataset="$1"
  local attack_mode="$2"
  local gpu_index="$3"
  local min_free_mb="$4"
  local estimate_minutes="$5"
  local optional="${6:-core}"
  local cmd

  local train_refs
  train_refs="$(train_code_references)"
  if ! train_complete_is_fresh "${dataset}" "${attack_mode}"; then
    rm -f "$(train_complete_marker_path "${dataset}" "${attack_mode}")"
  fi

  cmd="python train.py --dataset ${dataset} --attack_mode ${attack_mode} --data_root ./data --checkpoints ./checkpoints --seed 0"
  if [[ -f "$(checkpoint_path "${dataset}" "${attack_mode}")" ]] \
    && [[ ! -f "$(train_complete_marker_path "${dataset}" "${attack_mode}")" ]] \
    && path_is_fresh_against_refs "$(checkpoint_path "${dataset}" "${attack_mode}")" "${train_refs}"; then
    cmd="${cmd} --continue_training"
  fi

  run_logged_cmd "train_${dataset}_${attack_mode}" "${gpu_index}" "${min_free_mb}" 3 "${estimate_minutes}" "${optional}" "$(train_complete_marker_path "${dataset}" "${attack_mode}")" "${cmd}" "${train_refs}"
}

eval_model() {
  local dataset="$1"
  local attack_mode="$2"
  local gpu_index="$3"
  local min_free_mb="$4"
  local estimate_minutes="$5"
  local optional="${6:-core}"

  run_logged_cmd "eval_${dataset}_${attack_mode}" "${gpu_index}" "${min_free_mb}" 3 "${estimate_minutes}" "${optional}" "$(eval_result_path "${dataset}" "${attack_mode}")" \
    "python eval.py --dataset ${dataset} --attack_mode ${attack_mode} --data_root ./data --checkpoints ./checkpoints --seed 0" \
    "$(eval_code_references "${dataset}" "${attack_mode}")"
}

strip_model() {
  local dataset="$1"
  local attack_mode="$2"
  local gpu_index="$3"
  local min_free_mb="$4"
  local estimate_minutes="$5"
  local optional="${6:-optional}"

  run_logged_cmd "strip_${dataset}_${attack_mode}" "${gpu_index}" "${min_free_mb}" 3 "${estimate_minutes}" "${optional}" "$(strip_result_path "${dataset}" "${attack_mode}")" \
    "python defenses/STRIP/STRIP.py --dataset ${dataset} --attack_mode ${attack_mode} --data_root ./data --checkpoints ./checkpoints --results ./defenses/STRIP/results --seed 0" \
    "$(strip_code_references "${dataset}" "${attack_mode}")"
}

fine_pruning_model() {
  local dataset="$1"
  local attack_mode="$2"
  local gpu_index="$3"
  local min_free_mb="$4"
  local estimate_minutes="$5"
  local optional="${6:-optional}"
  local script_path

  case "${dataset}" in
    mnist)
      script_path="defenses/fine_pruning/fine-pruning-mnist.py"
      ;;
    cifar10|gtsrb)
      script_path="defenses/fine_pruning/fine-pruning-cifar10-gtsrb.py"
      ;;
    celeba)
      script_path="defenses/fine_pruning/fine-pruning-celeba.py"
      ;;
    *)
      log_msg "unknown fine-pruning dataset: ${dataset}"
      return 1
      ;;
  esac

  run_logged_cmd "fine_pruning_${dataset}_${attack_mode}" "${gpu_index}" "${min_free_mb}" 2 "${estimate_minutes}" "${optional}" "$(fine_pruning_result_path "${dataset}" "${attack_mode}")" \
    "python ${script_path} --dataset ${dataset} --attack_mode ${attack_mode} --data_root ./data --checkpoints ./checkpoints --seed 0" \
    "$(fine_pruning_code_references "${dataset}" "${attack_mode}" "${script_path}")"
}

neural_cleanse_model() {
  local dataset="$1"
  local attack_mode="$2"
  local gpu_index="$3"
  local min_free_mb="$4"
  local estimate_minutes="$5"
  local optional="${6:-optional}"

  run_logged_cmd "neural_cleanse_${dataset}_${attack_mode}" "${gpu_index}" "${min_free_mb}" 2 "${estimate_minutes}" "${optional}" "$(neural_cleanse_result_path "${dataset}" "${attack_mode}")" \
    "python defenses/neural_cleanse/neural_cleanse.py --dataset ${dataset} --attack_mode ${attack_mode} --data_root ./data --checkpoints ./checkpoints --result ./defenses/neural_cleanse/results --seed 0" \
    "$(neural_cleanse_code_references "${dataset}" "${attack_mode}")"
}
