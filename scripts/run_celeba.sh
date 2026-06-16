#!/usr/bin/env bash
# =============================================================================
# CelebA 数据集实验
# 8 类面部属性分类 (Heavy Makeup, Mouth Slightly Open, Smiling 的组合)
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${REPO_ROOT}/data"
CHECKPOINTS_ROOT="${REPO_ROOT}/checkpoints"
RESULTS_ROOT="${REPO_ROOT}/results"
TEMPS_ROOT="${REPO_ROOT}/temps"

mkdir -p "${DATA_ROOT}" "${CHECKPOINTS_ROOT}" "${RESULTS_ROOT}" "${TEMPS_ROOT}"

echo "============================================"
echo " CelebA 数据集实验"
echo "============================================"
echo " 数据集: CelebA (8-class face attributes)"
echo " 攻击模式: all2one + all2all"
echo " 模型: ResNet18"
echo ""

# CelebA 共用参数
N_ITERS=1000
BS=64
LR_C=0.01
NUM_WORKERS=4
DEVICE="cuda"
TARGET_LABEL=0
PC=0.1
CROSS_RATIO=2
S=0.5
K=4
RANDOM_ROTATION=10
RANDOM_CROP=5
GRID_RESCALE=1
SEED=0

run_celeba_train() {
    local ATTACK_MODE="$1"
    local EXP_NAME="celeba_${ATTACK_MODE}"
    local CKPT_DIR="${CHECKPOINTS_ROOT}/${EXP_NAME}"
    local LOG_FILE="${RESULTS_ROOT}/${EXP_NAME}.log"

    mkdir -p "${CKPT_DIR}"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Training CelebA ${ATTACK_MODE}..."
    echo "  Checkpoint: ${CKPT_DIR}"

    python "${REPO_ROOT}/train.py" \
        --dataset celeba \
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
        --cross_ratio "${CROSS_RATIO}" \
        --s "${S}" \
        --k "${K}" \
        --random_rotation "${RANDOM_ROTATION}" \
        --random_crop "${RANDOM_CROP}" \
        --grid_rescale "${GRID_RESCALE}" \
        --seed "${SEED}" \
        2>&1 | tee "${LOG_FILE}"

    # Copy result
    local SRC_RESULT="${CKPT_DIR}/${ATTACK_MODE}/results.json"
    if [ -f "${SRC_RESULT}" ]; then
        cp "${SRC_RESULT}" "${RESULTS_ROOT}/${EXP_NAME}.json"
        echo "  CelebA ${ATTACK_MODE} completed!"
    fi
    echo ""
}

# ---------- CelebA all2one ----------
run_celeba_train "all2one"

# ---------- CelebA all2all ----------
run_celeba_train "all2all"

# ---------- STRIP on CelebA ----------
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running STRIP on CelebA..."

for attack_mode in "all2one" "all2all"; do
    cd "${REPO_ROOT}/defenses/STRIP"
    python STRIP.py \
        --dataset celeba \
        --attack_mode "${attack_mode}" \
        --checkpoints "${CHECKPOINTS_ROOT}/celeba_${attack_mode}" \
        --data_root "${DATA_ROOT}" \
        --device "${DEVICE}" \
        2>&1 | tee "${RESULTS_ROOT}/celeba_${attack_mode}_strip.log"
    cd "${REPO_ROOT}"
done

echo ""
echo "============================================"
echo " CelebA 实验完成！"
echo " 结果: ${RESULTS_ROOT}/celeba_all2one.json"
echo "       ${RESULTS_ROOT}/celeba_all2all.json"
echo "============================================"
