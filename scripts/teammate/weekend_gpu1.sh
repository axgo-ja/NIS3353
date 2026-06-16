#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/weekend_common.sh"
init_worker "gpu1"
trap 'fail_worker' ERR
trap 'status=$?; if (( status != 0 )); then fail_worker; fi' EXIT

train_model mnist all2one 1 3000 120 core || true
if train_complete_is_fresh mnist all2one; then
  eval_model mnist all2one 1 2000 15 core || true
  strip_model mnist all2one 1 2000 30 core || true
  fine_pruning_model mnist all2one 1 3000 90 optional || true
else
  log_msg "skip mnist_all2one dependents: training is not fresh"
fi

train_model mnist all2all 1 3000 120 core || true
if train_complete_is_fresh mnist all2all; then
  eval_model mnist all2all 1 2000 15 core || true
  strip_model mnist all2all 1 2000 30 core || true
  fine_pruning_model mnist all2all 1 3000 90 optional || true
else
  log_msg "skip mnist_all2all dependents: training is not fresh"
fi

if wait_for_train_complete cifar10 all2one 4320 "cifar10_all2one_complete"; then
  strip_model cifar10 all2one 1 6000 60 core || true
fi

if wait_for_train_complete cifar10 all2all 4320 "cifar10_all2all_complete"; then
  strip_model cifar10 all2all 1 6000 60 core || true
fi
if train_complete_is_fresh cifar10 all2one; then
  fine_pruning_model cifar10 all2one 1 8000 180 optional || true
fi
if train_complete_is_fresh cifar10 all2all; then
  fine_pruning_model cifar10 all2all 1 8000 180 optional || true
fi

if wait_for_train_complete gtsrb all2one 4320 "gtsrb_all2one_complete"; then
  strip_model gtsrb all2one 1 8000 60 core || true
fi

if wait_for_train_complete gtsrb all2all 4320 "gtsrb_all2all_complete"; then
  strip_model gtsrb all2all 1 8000 60 core || true
fi

if train_complete_is_fresh gtsrb all2one; then
  fine_pruning_model gtsrb all2one 1 10000 180 optional || true
fi
if train_complete_is_fresh gtsrb all2all; then
  fine_pruning_model gtsrb all2all 1 10000 180 optional || true
fi
if train_complete_is_fresh cifar10 all2one; then
  neural_cleanse_model cifar10 all2one 1 8000 360 optional || true
fi

finish_worker
trap - ERR EXIT
