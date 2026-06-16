#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_RUN_ROOT="${REPO_ROOT}/logs/weekend_latest"
if [[ ! -e "${DEFAULT_RUN_ROOT}" && -d "${REPO_ROOT}/logs/weekend_20260614" ]]; then
  DEFAULT_RUN_ROOT="${REPO_ROOT}/logs/weekend_20260614"
fi
RUN_ROOT="${WANET_WEEKEND_RUN_ROOT:-${DEFAULT_RUN_ROOT}}"

echo "run_root: ${RUN_ROOT}"
echo

echo "sessions:"
if [[ -f "${RUN_ROOT}/sessions.txt" ]]; then
  cat "${RUN_ROOT}/sessions.txt"
else
  echo "no sessions file"
fi

echo
echo "tmux:"
tmux ls 2>/dev/null || true

echo
for worker in cpu gpu0 gpu1; do
  echo "== ${worker} =="
  printf 'status: '; cat "${RUN_ROOT}/${worker}.status" 2>/dev/null || echo "missing"
  printf 'current: '; cat "${RUN_ROOT}/${worker}.current" 2>/dev/null || echo "missing"
  printf 'started: '; cat "${RUN_ROOT}/${worker}.started_at" 2>/dev/null || echo "missing"
  printf 'finished: '; cat "${RUN_ROOT}/${worker}.finished_at" 2>/dev/null || echo "missing"
  echo
done

echo "recent summary:"
tail -n 40 "${RUN_ROOT}/summary.tsv" 2>/dev/null || true
