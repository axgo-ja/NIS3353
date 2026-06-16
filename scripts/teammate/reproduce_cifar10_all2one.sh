#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"${REPO_ROOT}/scripts/download_cifar10.sh"
"${REPO_ROOT}/scripts/train_cifar10_all2one.sh"
"${REPO_ROOT}/scripts/eval_cifar10_all2one.sh"
"${REPO_ROOT}/scripts/strip_cifar10_all2one.sh"
