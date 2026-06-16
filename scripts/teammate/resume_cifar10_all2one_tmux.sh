#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_AT="${1:-strip}"
SESSION_NAME="${2:-wanet_cifar10_all2one_resume_${START_AT}_$(date +%Y%m%d_%H%M%S)}"
WINDOW_NAME="pipeline"
LOG_DIR="${REPO_ROOT}/logs/cifar10_all2one"

mkdir -p "${LOG_DIR}"

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  echo "tmux session already exists: ${SESSION_NAME}" >&2
  exit 1
fi

tmux new-session -d -s "${SESSION_NAME}" -n "${WINDOW_NAME}" \
  "bash -lc 'cd \"${REPO_ROOT}\" && PIPELINE_START_AT=\"${START_AT}\" bash scripts/run_cifar10_all2one_pipeline.sh \"${START_AT}\"'"

printf '%s\n' "${SESSION_NAME}" > "${LOG_DIR}/session_name.txt"
echo "started tmux session: ${SESSION_NAME} from step ${START_AT}"
