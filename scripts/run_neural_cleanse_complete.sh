#!/usr/bin/env bash
# =============================================================================
# Neural Cleanse 补全实验
# 队友已完成: MNIST all2one, CIFAR-10 all2one
# 待补全:     MNIST all2all, CIFAR-10 all2all, GTSRB all2one, GTSRB all2all
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${REPO_ROOT}/data"
RESULTS_ROOT="${REPO_ROOT}/results"
DEVICE="cuda"

# 需要队友的 checkpoints（如果机器上没有的话，需要先传过去）
# 假设队友的 checkpoints 在这个路径
TEAMMATE_CKPTS="${REPO_ROOT}/teammate_checkpoints"

mkdir -p "${RESULTS_ROOT}"

echo "============================================"
echo " Neural Cleanse 补全实验"
echo "============================================"
echo ""

# 定义要跑的组合
declare -A NC_TASKS
NC_TASKS["mnist_all2all"]="mnist|all2all"
NC_TASKS["cifar10_all2all"]="cifar10|all2all"
NC_TASKS["gtsrb_all2one"]="gtsrb|all2one"
NC_TASKS["gtsrb_all2all"]="gtsrb|all2all"

run_nc() {
    local dataset="$1"
    local attack_mode="$2"
    local ckpt_dir="$3"
    local result_file="${RESULTS_ROOT}/neural_cleanse_${dataset}_${attack_mode}.txt"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Neural Cleanse: ${dataset} ${attack_mode}"

    cd "${REPO_ROOT}/defenses/neural_cleanse"
    python neural_cleanse.py \
        --dataset "${dataset}" \
        --attack_mode "${attack_mode}" \
        --checkpoints "${ckpt_dir}" \
        --data_root "${DATA_ROOT}" \
        --device "${DEVICE}" \
        2>&1 | tee "${result_file}"
    cd "${REPO_ROOT}"
    echo ""
}

for task_name in "${!NC_TASKS[@]}"; do
    IFS='|' read -r ds am <<< "${NC_TASKS[$task_name]}"

    # 先检查队友 checkpoints 里有没有
    CKPT_DIR=""
    if [ -d "${TEAMMATE_CKPTS}/${ds}" ]; then
        CKPT_DIR="${TEAMMATE_CKPTS}/${ds}"
    elif [ -d "${REPO_ROOT}/checkpoints/${ds}" ]; then
        CKPT_DIR="${REPO_ROOT}/checkpoints/${ds}"
    else
        echo "[SKIP] ${ds} ${am}: checkpoints not found. Please copy teammate's checkpoints to ${TEAMMATE_CKPTS}/${ds}/"
        echo "  Or re-train with: python train.py --dataset ${ds} --attack_mode ${am}"
        continue
    fi

    run_nc "${ds}" "${am}" "${CKPT_DIR}"
done

echo ""
echo "============================================"
echo " Neural Cleanse 补全实验完成！"
echo "============================================"
