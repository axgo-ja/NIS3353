#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
RUN_ROOT="${WANET_WEEKEND_RUN_ROOT:-${REPO_ROOT}/logs/weekend_${STAMP}}"

CPU_SESSION="wanet_weekend_cpu_${STAMP}"
GPU0_SESSION="wanet_weekend_gpu0_${STAMP}"
GPU1_SESSION="wanet_weekend_gpu1_${STAMP}"

mkdir -p "${RUN_ROOT}"
mkdir -p "${REPO_ROOT}/logs"
ln -sfn "${RUN_ROOT}" "${REPO_ROOT}/logs/weekend_latest"

tmux new-session -d -s "${CPU_SESSION}" -n cpu \
  "bash -lc 'cd \"${REPO_ROOT}\" && WANET_WEEKEND_RUN_ROOT=\"${RUN_ROOT}\" bash scripts/weekend_cpu.sh; echo; echo \"CPU worker finished. Press Ctrl-D to close.\"; exec bash'"

tmux new-session -d -s "${GPU0_SESSION}" -n gpu0 \
  "bash -lc 'cd \"${REPO_ROOT}\" && WANET_WEEKEND_RUN_ROOT=\"${RUN_ROOT}\" bash scripts/weekend_gpu0.sh; echo; echo \"GPU0 worker finished. Press Ctrl-D to close.\"; exec bash'"

tmux new-session -d -s "${GPU1_SESSION}" -n gpu1 \
  "bash -lc 'cd \"${REPO_ROOT}\" && WANET_WEEKEND_RUN_ROOT=\"${RUN_ROOT}\" bash scripts/weekend_gpu1.sh; echo; echo \"GPU1 worker finished. Press Ctrl-D to close.\"; exec bash'"

cat > "${RUN_ROOT}/sessions.txt" <<EOF
${CPU_SESSION}
${GPU0_SESSION}
${GPU1_SESSION}
EOF

echo "started:"
cat "${RUN_ROOT}/sessions.txt"
