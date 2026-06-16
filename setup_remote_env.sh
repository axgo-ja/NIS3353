#!/usr/bin/env bash
# =============================================================================
# WaNet 复现 - 成员2 远程机器一键环境配置
# 适用: Ubuntu 22.04 + RTX 3090 + conda
# 用法: bash setup_remote_env.sh
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "============================================"
echo " WaNet Member 2 - 远程环境配置"
echo " 项目路径: ${REPO_ROOT}"
echo "============================================"

# ---------- 1. 检测/初始化 conda ----------
CONDA_BASE=""
for candidate in \
    /root/miniconda3 \
    /opt/conda \
    /home/linux/miniconda3 \
    /home/linux/anaconda3 \
    /root/anaconda3; do
    if [ -f "${candidate}/etc/profile.d/conda.sh" ]; then
        CONDA_BASE="${candidate}"
        break
    fi
done

if [ -z "${CONDA_BASE}" ]; then
    echo "[ERROR] 未找到 conda 安装, 请先安装 Miniconda:"
    echo "  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  bash Miniconda3-latest-Linux-x86_64.sh -b -p /home/linux/miniconda3"
    exit 1
fi

source "${CONDA_BASE}/etc/profile.d/conda.sh"
echo "[OK] conda found at: ${CONDA_BASE}"

# ---------- 2. 创建 conda 环境 ----------
ENV_NAME="wanet_member2"
if conda env list | grep -q "${ENV_NAME}"; then
    echo "[INFO] conda env '${ENV_NAME}' already exists, skipping creation."
else
    echo "[INFO] Creating conda env: ${ENV_NAME} (Python 3.10)"
    conda create -y -n "${ENV_NAME}" python=3.10
fi

conda activate "${ENV_NAME}"
echo "[OK] Using Python: $(python --version)"

# ---------- 3. 安装 PyTorch 2.4 + CUDA 12.1 ----------
echo "[INFO] Installing PyTorch 2.4.0 with CUDA 12.1..."
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121

echo "[OK] PyTorch installed: $(python -c 'import torch; print(f"PyTorch {torch.__version__}, CUDA {torch.version.cuda}, GPU available: {torch.cuda.is_available()}")')"

# ---------- 4. 安装其他依赖 ----------
echo "[INFO] Installing other dependencies..."
pip install -U \
    numpy \
    opencv-python-headless \
    matplotlib \
    Pillow \
    tensorboard \
    tensorboardX \
    scipy \
    kornia \
    lpips \
    scikit-image \
    tqdm

echo "[OK] All dependencies installed."

# ---------- 5. 下载数据集 ----------
echo "[INFO] Checking datasets..."

# CIFAR-10
if [ ! -d "${REPO_ROOT}/data/cifar-10-batches-py" ]; then
    echo "[INFO] Downloading CIFAR-10..."
    mkdir -p "${REPO_ROOT}/data"
    # Use a domestic mirror for faster download
    CIFAR10_URL="${CIFAR10_URL:-https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz}"
    wget -O /tmp/cifar-10-python.tar.gz "$CIFAR10_URL"
    tar -xzf /tmp/cifar-10-python.tar.gz -C "${REPO_ROOT}/data/"
    rm -f /tmp/cifar-10-python.tar.gz
    echo "[OK] CIFAR-10 downloaded."
else
    echo "[OK] CIFAR-10 already exists."
fi

# MNIST (auto-download by torchvision)
echo "[INFO] Pre-downloading MNIST (torchvision will handle this)..."
python -c "
import torchvision
torchvision.datasets.MNIST('${REPO_ROOT}/data', train=True, download=True)
torchvision.datasets.MNIST('${REPO_ROOT}/data', train=False, download=True)
print('MNIST ready.')
"

# CelebA
if [ ! -d "${REPO_ROOT}/data/celeba" ]; then
    echo "[INFO] Downloading CelebA (this may take a while)..."
    python -c "
import torchvision
torchvision.datasets.CelebA('${REPO_ROOT}/data', split='train', target_type='attr', download=True)
torchvision.datasets.CelebA('${REPO_ROOT}/data', split='test', target_type='attr', download=True)
print('CelebA ready.')
"
    echo "[OK] CelebA downloaded."
else
    echo "[OK] CelebA already exists."
fi

# GTSRB
if [ ! -d "${REPO_ROOT}/data/GTSRB" ]; then
    echo "[INFO] Downloading GTSRB..."
    bash "${REPO_ROOT}/gtsrb_download.sh"
    echo "[OK] GTSRB downloaded."
else
    echo "[OK] GTSRB already exists."
fi

# ---------- 6. 验证 ----------
echo ""
echo "============================================"
echo " 环境配置完成！"
echo "============================================"
echo " 环境名称: ${ENV_NAME}"
echo " 激活命令: conda activate ${ENV_NAME}"
echo " 项目路径: ${REPO_ROOT}"
echo ""
echo " 验证:"
python -c "
import torch
import kornia
import torchvision
import numpy as np
import cv2
print(f'PyTorch:  {torch.__version__}')
print(f'CUDA:     {torch.version.cuda}')
print(f'GPU:      {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')
print(f'torchvision: {torchvision.__version__}')
print(f'kornia:   {kornia.__version__}')
print(f'numpy:    {np.__version__}')
print(f'OpenCV:   {cv2.__version__}')
print('All imports OK!')
"
echo ""
echo " 下一步: bash run_all.sh"
echo "============================================"
