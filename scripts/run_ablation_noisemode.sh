#!/usr/bin/env bash
# =============================================================================
# 消融实验 1: Noise Mode 消融
# 验证 noise mode (cross samples) 是绕过 Neural Cleanse 的关键
# =============================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../configs/ablation_configs.sh"

echo "============================================"
echo " 消融实验 1: Noise Mode Ablation"
echo "============================================"
echo " 目的: 对比有/无 noise mode 对 Neural Cleanse 检测的影响"
echo " 论文结论: 无 noise mode -> 模型学到像素级产物 -> 被 Neural Cleanse 检测到"
echo ""

# ---------- 实验 1a: 有 noise mode (cross_ratio=2, 即默认设置) ----------
log "========== 实验 1a: WITH noise mode (cross_ratio=2) =========="
run_train "ablation_noisemode_with" \
    --s "${DEFAULT_S}" \
    --k "${DEFAULT_K}" \
    --cross_ratio 2

# ---------- 实验 1b: 无 noise mode (cross_ratio=0) ----------
log "========== 实验 1b: WITHOUT noise mode (cross_ratio=0) =========="
run_train "ablation_noisemode_without" \
    --s "${DEFAULT_S}" \
    --k "${DEFAULT_K}" \
    --cross_ratio 0

# ---------- Neural Cleanse 对比检测 ----------
log ""
log "========== 运行 Neural Cleanse 对比检测 =========="

for exp in "ablation_noisemode_with" "ablation_noisemode_without"; do
    CKPT_DIR="${CHECKPOINTS_ROOT}/${exp}"
    NC_RESULT="${RESULTS_ROOT}/${exp}_neural_cleanse.txt"

    log "Running Neural Cleanse on: ${exp}"
    cd "${REPO_ROOT}/defenses/neural_cleanse"
    python neural_cleanse.py \
        --dataset "${DATASET}" \
        --attack_mode "${ATTACK_MODE}" \
        --checkpoints "${CKPT_DIR}" \
        --data_root "${DATA_ROOT}" \
        --device "${DEVICE}" \
        2>&1 | tee "${NC_RESULT}"
    cd "${REPO_ROOT}"
done

log ""
log "============================================"
log " Noise Mode 消融实验完成！"
log " 结果文件:"
log "   有 noise: ${RESULTS_ROOT}/ablation_noisemode_with.json"
log "   无 noise: ${RESULTS_ROOT}/ablation_noisemode_without.json"
log "   NC检测(有noise): ${RESULTS_ROOT}/ablation_noisemode_with_neural_cleanse.txt"
log "   NC检测(无noise): ${RESULTS_ROOT}/ablation_noisemode_without_neural_cleanse.txt"
log "============================================"
