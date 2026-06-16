#!/usr/bin/env bash
# =============================================================================
# 消融实验 2: Warping Strength (s) 参数扫描
# 论文 Section 4.6 - Effect of Warping Hyper-parameters
# s 控制 warping 变形的幅度
# =============================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../configs/ablation_configs.sh"

echo "============================================"
echo " 消融实验 2: Warping Strength s Ablation"
echo "============================================"
echo " 参数: s ∈ {0.25, 0.5, 0.75, 1.0}"
echo " 固定: k = ${DEFAULT_K}, cross_ratio = ${CROSS_RATIO}"
echo " 论文结论: s 过小 -> Attack Acc 下降; s 增大 -> Attack Acc 饱和接近 100%"
echo ""

S_VALUES=(0.25 0.5 0.75 1.0)

for s in "${S_VALUES[@]}"; do
    log "========== s = ${s} =========="
    run_train "ablation_s_${s}" \
        --s "${s}" \
        --k "${DEFAULT_K}" \
        --cross_ratio "${CROSS_RATIO}"
done

# ---------- 汇总 s 消融结果 ----------
log ""
log "========== 汇总 Warping Strength 消融结果 =========="
SUMMARY_FILE="${RESULTS_ROOT}/ablation_s_summary.csv"
echo "s,clean_acc,bd_acc,cross_acc" > "${SUMMARY_FILE}"

for s in "${S_VALUES[@]}"; do
    RESULT_FILE="${RESULTS_ROOT}/ablation_s_${s}.json"
    if [ -f "${RESULT_FILE}" ]; then
        python -c "
import json
with open('${RESULT_FILE}') as f:
    r = json.load(f)
print(f'${s},{r[\"clean_acc\"]:.2f},{r[\"bd_acc\"]:.2f},{r[\"cross_acc\"]:.2f}')
" >> "${SUMMARY_FILE}"
    fi
done

log "Warping Strength 消融汇总表:"
cat "${SUMMARY_FILE}"
log ""
log "============================================"
log " Warping Strength 消融实验完成！"
log " 汇总: ${SUMMARY_FILE}"
log "============================================"
