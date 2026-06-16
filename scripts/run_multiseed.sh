#!/usr/bin/env bash
# =============================================================================
# 多随机种子实验 - 统计显著性验证
# 对 CIFAR-10 all2one 用 seed 0-4 各训练一次
# =============================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../configs/ablation_configs.sh"

echo "============================================"
echo " 多随机种子实验 (Multi-Seed)"
echo "============================================"
echo " 数据集: CIFAR-10 all2one"
echo " Seeds: 0, 1, 2, 3, 4"
echo " 目的: 计算 mean±std，验证结果稳定性"
echo ""

SEEDS=(0 1 2 3 4)

for seed in "${SEEDS[@]}"; do
    log "========== Seed = ${seed} =========="
    run_train "multiseed_${seed}" \
        --s "${DEFAULT_S}" \
        --k "${DEFAULT_K}" \
        --cross_ratio "${CROSS_RATIO}" \
        --seed "${seed}"
done

# ---------- 汇总多种子结果 ----------
log ""
log "========== 汇总多种子结果 =========="
SUMMARY_FILE="${RESULTS_ROOT}/multiseed_summary.csv"
echo "seed,clean_acc,bd_acc,cross_acc" > "${SUMMARY_FILE}"

for seed in "${SEEDS[@]}"; do
    RESULT_FILE="${RESULTS_ROOT}/multiseed_${seed}.json"
    if [ -f "${RESULT_FILE}" ]; then
        python -c "
import json
with open('${RESULT_FILE}') as f:
    r = json.load(f)
print(f'${seed},{r[\"clean_acc\"]:.2f},{r[\"bd_acc\"]:.2f},{r[\"cross_acc\"]:.2f}')
" >> "${SUMMARY_FILE}"
    fi
done

log "多种子结果汇总表:"
cat "${SUMMARY_FILE}"

# 计算 mean 和 std
log ""
log "统计:"
python -c "
import csv
import numpy as np

clean, bd, cross = [], [], []
with open('${SUMMARY_FILE}') as f:
    reader = csv.DictReader(f)
    for row in reader:
        clean.append(float(row['clean_acc']))
        bd.append(float(row['bd_acc']))
        cross.append(float(row['cross_acc']))

print(f'Clean  Acc: {np.mean(clean):.2f} ± {np.std(clean):.2f}')
print(f'Attack Acc: {np.mean(bd):.2f} ± {np.std(bd):.2f}')
print(f'Cross  Acc: {np.mean(cross):.2f} ± {np.std(cross):.2f}')
"

log ""
log "============================================"
log " 多随机种子实验完成！"
log " 汇总: ${SUMMARY_FILE}"
log "============================================"
