# NIS3353 - AI安全课程设计

## WaNet: Imperceptible Warping-based Backdoor Attack 复现与分析

**ICLR 2021 论文复现 | 消融实验 | 频域后门检测器**

---

## 项目简介

深度学习模型在训练阶段容易被植入后门——攻击者通过污染训练数据，使模型在遇到特定触发器时输出攻击者指定的标签。传统后门攻击使用可见的图案（如白色方块、水印等）作为触发器，人眼可察觉，防御方法也能检测到。

WaNet (ICLR 2021) 提出了一种更隐蔽的方式：**用图像空间形变 (Warping) 替代可见的触发器**。通过对图像施加微小的、人眼不可察觉的几何扭曲，模型能学会将这种特定的"扭曲模式"关联到目标标签。WaNet 声称这种方法能绕过 STRIP、Fine-Pruning、Neural Cleanse 等所有现有防御。

本项目完成了三件事：

1. **复现验证**：在 CIFAR-10 上复现 WaNet，确认其攻击有效性（ASR 99.15%）和防御绕过能力
2. **消融分析**：系统拆解 Warping 机制，分析 Noise Mode、Warping 强度 s、网格大小 k 对攻击效果的影响
3. **频域检测器（创新点）**：发现 Warping = 插值运算 = 频域留痕，设计了首个从图像频域信号检测 Warping 后门的方法，AUC 达到 0.735（远超 STRIP 的 0.50）

---

## 成员分工

| 成员 | 工作内容 | 产出 |
|------|---------|------|
| **周争妍** | 环境配置、主实验复现（3 数据集 × 2 攻击模式）、STRIP / Fine-Pruning / Neural Cleanse 防御实验、结果整理 | `docs/teammate_main_report.md` |
| **蒋竺君** | 消融实验（Noise Mode / s / k 参数扫描）、频域检测器设计与实现、可视化、交互式 Dashboard、PPT 制作 | `freq_detector.py` `dashboard/` `WaNet.pptx` |

---

## 核心发现

### 1. Noise Mode 是绕过防御的关键

| 配置 | Clean Acc | ASR | Cross Acc | Neural Cleanse |
|------|-----------|-----|-----------|----------------|
| With Noise Mode | 92.84% | 99.15% | 89.71% | 检测不到 |
| Without Noise Mode | 92.74% | 98.21% | **0.00%** | 能检测到 |

> 没有 Noise Mode 时，模型学到的是像素级捷径而非真正的 Warping 变换，被 Neural Cleanse 轻易发现。

### 2. Warping 参数高度敏感

| 参数 | 取值 | ASR | 结论 |
|------|------|-----|------|
| s (Warping 强度) | 0.25 | 74.12% | 太弱，攻击失效 |
| | 0.50 | 99.59% | 最优 |
| | 1.00 | 98.29% | 性能饱和 |
| k (网格大小) | 2 | 92.82% | 太粗，被当成噪声 |
| | 4 | 99.15% | 最优 |
| | 8 | 97.55% | 接近饱和 |

### 3. 频域检测器：我们的创新

Warping 使用 `grid_sample` + bilinear interpolation（双线性插值）。插值运算本质上是信号处理操作，必然在频域留下可检测的痕迹。

- 现有防御（STRIP/Neural Cleanse）看模型行为 → 检测不到
- 我们直接看图像频域信号 → **能检测到**

| 方法 | AUC | 准确率 |
|------|-----|--------|
| **频域检测器 (Ours)** | **0.735** | 67.33% |
| STRIP | ~0.50 | 等同随机 |

---

## 项目结构

```
├── train.py / eval.py / config.py    # WaNet 训练与评估 (基于官方实现)
├── freq_detector.py                  # ★ 频域 Warping 检测器 (我们的创新)
│
├── utils/                            # 工具函数 (dataloader, runtime, warp grids)
├── networks/                         # 网络模型定义
├── classifier_models/                # 分类器模型 (PreActResNet18 等)
├── defenses/                         # 防御方法
│   ├── STRIP/                        # STRIP 检测 + 结果
│   ├── fine_pruning/                 # Fine-Pruning + 结果
│   └── neural_cleanse/               # Neural Cleanse + 结果
│
├── scripts/                          # 消融实验运行脚本
│   ├── run_ablation_noisemode.sh     # Noise Mode 消融
│   ├── run_ablation_warping_s.sh     # s 参数扫描
│   ├── run_ablation_grid_k.sh        # k 参数扫描
│   ├── run_multiseed.sh              # 多随机种子
│   ├── run_celeba.sh                 # CelebA 数据集
│   ├── run_neural_cleanse_complete.sh # NC 防御补全
│   └── teammate/                     # 队友的主实验运行脚本
│
├── configs/                          # 实验参数配置
├── visualization/                    # 可视化代码 (warping field, PSNR/SSIM)
├── dashboard/                        # ★ 交互式 Web 演示平台
│   └── index.html                    # 浏览器打开即可展示
│
├── results/                          # 实验结果
│   ├── ablation_*.json               # 消融实验数据 (10 组)
│   ├── ablation_*_summary.csv         # 消融实验汇总
│   ├── multiseed_*.json              # 多种子实验数据
│   ├── freq_detector/                # 频域检测器结果
│   │   ├── roc_curve.png             # ROC 曲线
│   │   ├── fft_spectrum_comparison.png # FFT 频谱对比
│   │   ├── feature_distributions.png # 特征分布
│   │   └── freq_detector_results.json # 量化结果
│   └── visualization/                # 可视化图表
│       ├── warping_field.png         # Warping 控制网格
│       ├── image_comparison.png      # 原图 vs 变形图
│       ├── perceptual_metrics.png    # PSNR/SSIM 分布
│       ├── parameter_effects.png     # (s,k) 参数矩阵
│       └── ablation_summary.png      # 消融实验汇总
│
├── docs/                             # 文档
│   ├── teammate_main_report.md       # 主实验复现报告
│   └── reproduction_guide.md         # 复现流程文档
│
├── WaNet.pptx                        # PPT
└── README.md                         # 本文件
```

---

## 快速开始

### 环境

```bash
conda create -n wanet python=3.10
conda activate wanet
pip install torch torchvision kornia opencv-python scikit-learn scipy matplotlib tqdm
```

### 运行频域检测器

```bash
# 需要先训练一个 WaNet 模型 (或使用预训练权重)
python train.py --dataset cifar10 --attack_mode all2one

# 运行频域检测器
python freq_detector.py
```

### 查看 Dashboard

浏览器打开 `dashboard/index.html` 即可。

### 查看 PPT

打开 `WaNet答辩.pptx`。

---

## 参考资料

- WaNet 论文: [WaNet - Imperceptible Warping-based Backdoor Attack](https://openreview.net/forum?id=eEn8KTtJOx) (ICLR 2021)
- 官方实现: [VinAIResearch/Warping-based_Backdoor_Attack-release](https://github.com/VinAIResearch/Warping-based_Backdoor_Attack-release)

---

## License

本项目为 AI 安全课程作业，仅供学习研究使用。
