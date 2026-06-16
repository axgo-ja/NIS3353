#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/weekend_common.sh"
init_worker "gpu0"
trap 'fail_worker' ERR
trap 'status=$?; if (( status != 0 )); then fail_worker; fi' EXIT

train_model cifar10 all2one 0 12000 420 core || true
if train_complete_is_fresh cifar10 all2one; then
  eval_model cifar10 all2one 0 8000 20 core || true
else
  log_msg "skip eval_cifar10_all2one: training is not fresh"
fi

train_model cifar10 all2all 0 12000 420 core || true
if train_complete_is_fresh cifar10 all2all; then
  eval_model cifar10 all2all 0 8000 20 core || true
else
  log_msg "skip eval_cifar10_all2all: training is not fresh"
fi

if wait_for_path "${REPO_ROOT}/data/GTSRB/.ready" 180 "gtsrb_ready"; then
  train_model gtsrb all2one 0 12000 420 core || true
  if train_complete_is_fresh gtsrb all2one; then
    eval_model gtsrb all2one 0 8000 20 core || true
  else
    log_msg "skip eval_gtsrb_all2one: training is not fresh"
  fi

  train_model gtsrb all2all 0 12000 420 core || true
  if train_complete_is_fresh gtsrb all2all; then
    eval_model gtsrb all2all 0 8000 20 core || true
  else
    log_msg "skip eval_gtsrb_all2all: training is not fresh"
  fi

  if train_complete_is_fresh gtsrb all2one; then
    fine_pruning_model gtsrb all2one 0 10000 180 optional || true
  fi
  if train_complete_is_fresh gtsrb all2all; then
    fine_pruning_model gtsrb all2all 0 10000 180 optional || true
  fi
fi

if train_complete_is_fresh mnist all2one; then
  neural_cleanse_model mnist all2one 0 6000 240 optional || true
fi

finish_worker
trap - ERR EXIT
