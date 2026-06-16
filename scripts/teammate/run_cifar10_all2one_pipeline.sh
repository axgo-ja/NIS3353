#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${REPO_ROOT}/logs/cifar10_all2one"
mkdir -p "${RUN_ROOT}"
START_AT="${1:-${PIPELINE_START_AT:-download}}"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

run_step() {
  local name="$1"
  shift

  echo "$(timestamp) [START] ${name}" | tee -a "${RUN_ROOT}/pipeline.log"
  printf '%s\n' "${name}" > "${RUN_ROOT}/current_step.txt"

  if "$@" 2>&1 | tee "${RUN_ROOT}/${name}.log"; then
    echo "$(timestamp) [DONE] ${name}" | tee -a "${RUN_ROOT}/pipeline.log"
  else
    local exit_code=$?
    echo "$(timestamp) [FAIL] ${name} (exit=${exit_code})" | tee -a "${RUN_ROOT}/pipeline.log"
    printf '%s\n' "${name}" > "${RUN_ROOT}/failed_step.txt"
    printf 'failed\n' > "${RUN_ROOT}/status.txt"
    exit "${exit_code}"
  fi
}

printf '%s\n' "$(timestamp)" > "${RUN_ROOT}/started_at.txt"
printf 'running\n' > "${RUN_ROOT}/status.txt"
rm -f "${RUN_ROOT}/failed_step.txt" "${RUN_ROOT}/finished_at.txt"

cd "${REPO_ROOT}"

case "${START_AT}" in
  download)
    run_step download bash scripts/download_cifar10.sh
    ;&
  train)
    run_step train bash scripts/train_cifar10_all2one.sh
    ;&
  eval)
    run_step eval bash scripts/eval_cifar10_all2one.sh
    ;&
  strip)
    run_step strip bash scripts/strip_cifar10_all2one.sh
    ;;
  *)
    echo "invalid start step: ${START_AT}" | tee -a "${RUN_ROOT}/pipeline.log"
    printf 'failed\n' > "${RUN_ROOT}/status.txt"
    exit 2
    ;;
esac

printf '%s\n' "$(timestamp)" > "${RUN_ROOT}/finished_at.txt"
printf 'completed\n' > "${RUN_ROOT}/status.txt"
echo "$(timestamp) [DONE] pipeline" | tee -a "${RUN_ROOT}/pipeline.log"
