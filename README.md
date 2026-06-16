# NIS3353 - AI安全课程设计

## WaNet: Imperceptible Warping-based Backdoor Attack 复现与分析

**ICLR 2021 论文复现 | 消融实验 | 频域后门检测器**

### 成员分工

| 成员 | 工作 |
|------|------|
| 周争妍 | 主实验复现 (MNIST/CIFAR-10/GTSRB + all2one/all2all) + STRIP/Fine-Pruning/Neural Cleanse 防御 |
| 成员2 | 消融实验 (Noise Mode/s/k 参数扫描) + 频域检测器 + 可视化平台 |

### 项目结构

```
├── train.py / eval.py / config.py  # WaNet 训练与评估 (基于官方实现)
├── freq_detector.py                # ★ 频域 Warping 后门检测器 (我们的创新)
├── utils/                          # 工具函数 (dataloader, runtime)
├── networks/                       # 网络模型定义
├── classifier_models/              # 分类器模型
├── defenses/                       # STRIP / Fine-Pruning / Neural Cleanse
├── scripts/                        # 消融实验运行脚本
├── visualization/                  # 可视化代码
├── dashboard/                      # ★ 交互式 Web 演示平台
│   └── index.html                  # 打开即可答辩展示
├── results/                        # 实验结果 (JSON + 图表)
│   ├── freq_detector/              # 频域检测器结果
│   └── visualization/              # 可视化图表
└── configs/                        # 实验参数配置
```

### 核心发现

1. **Noise Mode 是绕过防御的关键** — 无 Noise 时 Cross Acc = 0%
2. **Warping 参数高度敏感** — s<0.5 或 k<4 时 ASR 大幅下降
3. **频域检测器 (我们的创新)** — 首次从图像信号层面检测 warping 后门，AUC 0.735 vs STRIP 0.50

### 快速开始

```bash
# 安装依赖
conda create -n wanet python=3.10
conda activate wanet
pip install torch torchvision kornia opencv-python scikit-learn scipy matplotlib tqdm

# 运行频域检测器
python freq_detector.py

# 查看 Dashboard
# 浏览器打开 dashboard/index.html
```

### 答辩展示

打开 `dashboard/index.html` 即可在浏览器中进行交互式演示，包含：
- 交互式消融实验图表
- FFT 频谱对比
- ROC 曲线 (频域检测器 vs STRIP)
- 实时 Warping 变形演示
