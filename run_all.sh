#!/usr/bin/env bash
# =============================================================================
# WaNet 成员2 - 批量运行全部实验
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
RESULTS_DIR="${REPO_ROOT}/results"
LOG_DIR="${RESULTS_DIR}/logs"

mkdir -p "${RESULTS_DIR}" "${LOG_DIR}"

NOW=$(date '+%Y%m%d_%H%M%S')
MASTER_LOG="${LOG_DIR}/master_${NOW}.log"

log_master() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${MASTER_LOG}"
}

echo "============================================"
echo " WaNet 成员2 - 全部实验"
echo " 开始时间: $(date)"
echo " 日志文件: ${MASTER_LOG}"
echo "============================================"
echo ""

# ==================== Phase 1: 消融实验 ====================
log_master "========== Phase 1: 消融实验 =========="

log_master ""
log_master ">>> 1a: Noise Mode 消融"
bash "${SCRIPTS_DIR}/run_ablation_noisemode.sh" 2>&1 | tee -a "${LOG_DIR}/noisemode_${NOW}.log"

log_master ""
log_master ">>> 1b: Warping Strength (s) 消融"
bash "${SCRIPTS_DIR}/run_ablation_warping_s.sh" 2>&1 | tee -a "${LOG_DIR}/warping_s_${NOW}.log"

log_master ""
log_master ">>> 1c: Grid Size (k) 消融"
bash "${SCRIPTS_DIR}/run_ablation_grid_k.sh" 2>&1 | tee -a "${LOG_DIR}/grid_k_${NOW}.log"

# ==================== Phase 2: 多种子实验 ====================
log_master ""
log_master "========== Phase 2: 多随机种子 =========="
bash "${SCRIPTS_DIR}/run_multiseed.sh" 2>&1 | tee -a "${LOG_DIR}/multiseed_${NOW}.log"

# ==================== Phase 3: 可视化 ====================
log_master ""
log_master "========== Phase 3: 可视化与感知分析 =========="

source "${REPO_ROOT}/setup_remote_env.sh" 2>/dev/null || true
# Try to activate the conda env if available
if command -v conda &> /dev/null; then
    conda activate wanet_member2 2>/dev/null || true
fi

python "${REPO_ROOT}/visualization/visualize.py" \
    --all_datasets \
    --data_root "${REPO_ROOT}/data" \
    --output_dir "${RESULTS_DIR}/visualization" \
    --results_dir "${RESULTS_DIR}" \
    --device cuda \
    2>&1 | tee -a "${LOG_DIR}/visualization_${NOW}.log"

# ==================== Phase 4: 结果汇总 ====================
log_master ""
log_master "========== Phase 4: 结果汇总 =========="

python "${REPO_ROOT}/scripts/collect_results.py" \
    --results_dir "${RESULTS_DIR}" \
    --output "${RESULTS_DIR}/final_summary.json" \
    2>&1 | tee -a "${LOG_DIR}/collect_${NOW}.log"

# ==================== 完成 ====================
log_master ""
log_master "============================================"
log_master " 全部实验完成！"
log_master " 结束时间: $(date)"
log_master " 结果目录: ${RESULTS_DIR}"
log_master " 可视化:   ${RESULTS_DIR}/visualization/"
log_master " 汇总:     ${RESULTS_DIR}/final_summary.json"
log_master "============================================"

# 列出所有结果文件
echo ""
echo "生成的结果文件:"
find "${RESULTS_DIR}" -name "*.json" -o -name "*.csv" -o -name "*.png" | sort
