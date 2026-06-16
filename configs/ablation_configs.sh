#!/usr/bin/env bash
# =============================================================================
# WaNet 消融实验 - 统一参数配置
# 所有消融脚本 source 此文件即可获得一致的默认参数
# =============================================================================

# ---------- 固定参数 ----------
DATASET="cifar10"
ATTACK_MODE="all2one"
N_ITERS=1000
BS=128
LR_C=0.01
NUM_WORKERS=4
DEVICE="cuda"
TARGET_LABEL=0
PC=0.1
CROSS_RATIO=2
RANDOM_ROTATION=10
RANDOM_CROP=5
GRID_RESCALE=1

# ---------- 默认消融参数 ----------
DEFAULT_S=0.5
DEFAULT_K=4

# ---------- 路径 ----------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${REPO_ROOT}/data"
CHECKPOINTS_ROOT="${REPO_ROOT}/checkpoints"
RESULTS_ROOT="${REPO_ROOT}/results"
TEMPS_ROOT="${REPO_ROOT}/temps"

# 确保目录存在
mkdir -p "${DATA_ROOT}" "${CHECKPOINTS_ROOT}" "${RESULTS_ROOT}" "${TEMPS_ROOT}"

# ---------- 日志函数 ----------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

run_train() {
    # 用法: run_train <exp_name> [额外参数...]
    local EXP_NAME="$1"; shift
    local CKPT_DIR="${CHECKPOINTS_ROOT}/${EXP_NAME}"
    local RESULT_FILE="${RESULTS_ROOT}/${EXP_NAME}.json"
    local LOG_FILE="${RESULTS_ROOT}/${EXP_NAME}.log"

    mkdir -p "${CKPT_DIR}" "$(dirname "${RESULT_FILE}")"

    log "Starting: ${EXP_NAME}"
    log "  Checkpoint dir: ${CKPT_DIR}"
    log "  Result file:    ${RESULT_FILE}"
    log "  Log file:       ${LOG_FILE}"

    python "${REPO_ROOT}/train.py" \
        --dataset "${DATASET}" \
        --attack_mode "${ATTACK_MODE}" \
        --data_root "${DATA_ROOT}" \
        --checkpoints "${CKPT_DIR}" \
        --temps "${TEMPS_ROOT}/${EXP_NAME}" \
        --device "${DEVICE}" \
        --bs "${BS}" \
        --lr_C "${LR_C}" \
        --n_iters "${N_ITERS}" \
        --num_workers "${NUM_WORKERS}" \
        --target_label "${TARGET_LABEL}" \
        --pc "${PC}" \
        --random_rotation "${RANDOM_ROTATION}" \
        --random_crop "${RANDOM_CROP}" \
        --grid_rescale "${GRID_RESCALE}" \
        "$@" \
        2>&1 | tee "${LOG_FILE}"

    # 复制最优结果到统一结果目录
    local SRC_RESULT="${CKPT_DIR}/${DATASET}/${ATTACK_MODE}/results.json"
    if [ -f "${SRC_RESULT}" ]; then
        cp "${SRC_RESULT}" "${RESULT_FILE}"
        log "Completed: ${EXP_NAME}"
        python -c "
import json
with open('${RESULT_FILE}') as f:
    r = json.load(f)
print(f'  Clean Acc: {r[\"clean_acc\"]:.2f}%')
print(f'  Attack Acc: {r[\"bd_acc\"]:.2f}%')
print(f'  Cross Acc: {r[\"cross_acc\"]:.2f}%')
"
    else
        log "WARNING: ${EXP_NAME} completed but no results.json found!"
    fi
    echo ""
}
