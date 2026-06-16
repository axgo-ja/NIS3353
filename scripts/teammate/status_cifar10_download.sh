#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="${REPO_ROOT}/data/cifar-10-python.tar.gz"
LOG_FILE="${REPO_ROOT}/logs/cifar10_download.log"

if [[ -f "${ARCHIVE}" ]]; then
  ls -lh "${ARCHIVE}"
else
  echo "archive not found: ${ARCHIVE}"
fi

if [[ -f "${LOG_FILE}" ]]; then
  tail -n 20 "${LOG_FILE}"
else
  echo "download log not found: ${LOG_FILE}"
fi
