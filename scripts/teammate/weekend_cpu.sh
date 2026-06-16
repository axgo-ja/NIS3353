#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/weekend_common.sh"
init_worker "cpu"
trap 'fail_worker' ERR
trap 'status=$?; if (( status != 0 )); then fail_worker; fi' EXIT

run_logged_cmd "download_gtsrb" "cpu" 0 3 60 "core" "${REPO_ROOT}/data/GTSRB/.ready" "bash scripts/download_gtsrb.sh" || true

finish_worker
trap - ERR EXIT
