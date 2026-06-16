#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /home/zilia/conda/etc/profile.d/conda.sh
conda activate model

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONUNBUFFERED=1

python "${REPO_ROOT}/defenses/STRIP/STRIP.py" \
  --dataset cifar10 \
  --attack_mode all2one \
  --data_root "${REPO_ROOT}/data" \
  --checkpoints "${REPO_ROOT}/checkpoints" \
  --results "${REPO_ROOT}/defenses/STRIP/results" \
  --seed 0 \
  "$@"
