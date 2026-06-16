#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /home/zilia/conda/etc/profile.d/conda.sh
conda activate model

python -m pip install -U kornia tensorboard tensorboardX opencv-python-headless matplotlib

echo "model environment is ready."
echo "repo: ${REPO_ROOT}"
