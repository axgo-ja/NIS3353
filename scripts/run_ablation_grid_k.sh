#!/usr/bin/env bash
# =============================================================================
# 消融实验 3: Grid Size (k) 参数扫描
# 论文 Section 4.6 - Effect of Warping Hyper-parameters
# k 控制 warping 控制网格的分辨率
# =============================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../configs/ablation_configs.sh"

echo "============================================"
echo " 消融实验 3: Grid Size k Ablation"
echo "============================================"
echo " 参数: k ∈ {2, 4, 6, 8}"
echo " 固定: s = ${DEFAULT_S}, cross_ratio = ${CROSS_RATIO}"
echo " 论文结论: k 过小 -> Attack Acc 下降(被当作标签噪声); k 增大 -> Attack Acc 饱和"
echo ""

K_VALUES=(2 4 6 8)

for k in "${K_VALUES[@]}"; do
    log "========== k = ${k} =========="
    run_train "ablation_k_${k}" \
        --s "${DEFAULT_S}" \
        --k "${k}" \
        --cross_ratio "${CROSS_RATIO}"
done

# ---------- 汇总 k 消融结果 ----------
log ""
log "========== 汇总 Grid Size 消融结果 =========="
SUMMARY_FILE="${RESULTS_ROOT}/ablation_k_summary.csv"
echo "k,clean_acc,bd_acc,cross_acc" > "${SUMMARY_FILE}"

for k in "${K_VALUES[@]}"; do
    RESULT_FILE="${RESULTS_ROOT}/ablation_k_${k}.json"
    if [ -f "${RESULT_FILE}" ]; then
        python -c "
import json
with open('${RESULT_FILE}') as f:
    r = json.load(f)
print(f'${k},{r[\"clean_acc\"]:.2f},{r[\"bd_acc\"]:.2f},{r[\"cross_acc\"]:.2f}')
" >> "${SUMMARY_FILE}"
    fi
done

log "Grid Size 消融汇总表:"
cat "${SUMMARY_FILE}"
log ""
log "============================================"
log " Grid Size 消融实验完成！"
log " 汇总: ${SUMMARY_FILE}"
log "============================================"
