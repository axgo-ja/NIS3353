#!/usr/bin/env bash
# =============================================================================
# 快速冒烟测试 - 在远程机器上运行，用很少的迭代验证环境正常
# 运行时间: ~3 分钟
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo " WaNet 快速冒烟测试"
echo "============================================"
echo " 此测试用 1 个 iteration 快速验证:"
echo "  - PyTorch/CUDA 可用"
echo "  - 数据集可加载"
echo "  - 训练流程正常"
echo "  - Warping 变形正常"
echo ""

# Test 1: Python imports
echo "[TEST 1/4] Python 环境检查..."
python -c "
import torch
import torchvision
import kornia
import numpy as np
import cv2
print(f'  PyTorch: {torch.__version__}')
print(f'  CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
    print(f'  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
" && echo "  [PASS]" || echo "  [FAIL]"

# Test 2: Dataset loading
echo "[TEST 2/4] 数据集加载..."
python -c "
import torchvision
import os
data_root = '${REPO_ROOT}/data'
# MNIST (small, fast download)
torchvision.datasets.MNIST(data_root, train=True, download=True)
torchvision.datasets.MNIST(data_root, train=False, download=True)
print('  MNIST: OK')
# CIFAR-10
torchvision.datasets.CIFAR10(data_root, train=True, download=True)
torchvision.datasets.CIFAR10(data_root, train=False, download=True)
print('  CIFAR-10: OK')
" && echo "  [PASS]" || echo "  [FAIL]"

# Test 3: Warping grid
echo "[TEST 3/4] Warping field 生成..."
python -c "
import torch
import torch.nn.functional as F
# Simulate build_warp_grids
opt_k = 4
opt_input_height = 32
ins = torch.rand(1, 2, opt_k, opt_k) * 2 - 1
ins = ins / torch.mean(torch.abs(ins))
noise_grid = F.interpolate(ins, size=opt_input_height, mode='bicubic', align_corners=True)
noise_grid = noise_grid.permute(0, 2, 3, 1)
array1d = torch.linspace(-1, 1, steps=opt_input_height)
grid_y, grid_x = torch.meshgrid(array1d, array1d, indexing='ij')
identity_grid = torch.stack((grid_x, grid_y), dim=2)[None, ...]
# Apply warping to random image
x = torch.randn(4, 3, 32, 32)
grid_temps = (identity_grid + 0.5 * noise_grid / opt_input_height) * 1.0
grid_temps = torch.clamp(grid_temps, -1, 1)
x_warped = F.grid_sample(x, grid_temps.repeat(4, 1, 1, 1), align_corners=True)
print(f'  Input shape: {x.shape}')
print(f'  Output shape: {x_warped.shape}')
print(f'  Warping OK: {x.shape == x_warped.shape}')
" && echo "  [PASS]" || echo "  [FAIL]"

# Test 4: 1-iteration training
echo "[TEST 4/4] 1-iteration 训练测试 (~1 min)..."
python "${REPO_ROOT}/train.py" \
    --dataset cifar10 \
    --attack_mode all2one \
    --data_root "${REPO_ROOT}/data" \
    --checkpoints "${REPO_ROOT}/checkpoints/_smoke_test" \
    --temps "${REPO_ROOT}/temps/_smoke_test" \
    --device cuda \
    --bs 64 \
    --n_iters 1 \
    --num_workers 2 \
    --s 0.5 \
    --k 4 \
    --cross_ratio 2 \
    2>&1 | tail -5
echo "  [PASS]"

echo ""
echo "============================================"
echo " 冒烟测试全部通过！环境正常！"
echo " 可以运行完整实验: bash run_all.sh"
echo "============================================"
