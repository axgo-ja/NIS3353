#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
LOG_DIR="${REPO_ROOT}/logs"
URL="${CIFAR10_URL:-https://mindspore-website.obs.cn-north-4.myhuaweicloud.com/notebook/datasets/cifar-10-python.tar.gz}"

mkdir -p "${DATA_DIR}" "${LOG_DIR}"
wget -c "${URL}" -O "${DATA_DIR}/cifar-10-python.tar.gz"
tar -xzf "${DATA_DIR}/cifar-10-python.tar.gz" -C "${DATA_DIR}"

echo "CIFAR-10 is available under ${DATA_DIR}/cifar-10-batches-py"
