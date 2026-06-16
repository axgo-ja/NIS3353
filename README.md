# NIS3353 - AI安全课程设计

## WaNet: Imperceptible Warping-based Backdoor Attack 复现与分析

**ICLR 2021 论文复现 | 消融实验 | 频域后门检测器**

---

## 项目简介

深度学习模型在训练阶段容易被植入后门。攻击者通过污染训练数据，使模型在遇到特定触发器时输出指定标签。传统后门攻击通常依赖可见图案，容易被人眼察觉，也更容易被防御方法检测。

WaNet (ICLR 2021) 提出了一种更隐蔽的方式：使用图像空间形变作为触发器。通过对图像施加微小且不易察觉的几何扭曲，模型会把这种特定的扭曲模式关联到目标标签。围绕这一攻击，我们在本仓库中完成了复现、分析和补充实验。

本项目主要包含三部分工作：

1. **复现验证**：在 CIFAR-10 上复现 WaNet，并验证攻击有效性与对常见防御的绕过能力。
2. **消融分析**：分析 Noise Mode、Warping 强度 `s`、网格大小 `k` 等关键因素对攻击效果的影响。
3. **扩展研究**：补充频域检测器、可视化、Dashboard、报告与答辩材料。

---

## 成员分工

| 成员 | 工作内容 | 产出 |
|------|---------|------|
| **周争妍** | 环境配置、主实验复现（3 数据集 × 2 攻击模式）、STRIP / Fine-Pruning / Neural Cleanse 防御实验、结果整理 | `docs/teammate_main_report.md` |
| **蒋竺君** | 消融实验（Noise Mode / `s` / `k` 参数扫描）、频域检测器设计与实现、可视化、交互式 Dashboard、PPT 制作 | `freq_detector.py` `dashboard/` `WaNet.pptx` |

---

## 快速入口

- 课程项目总览：本 README
- 复现流程文档：`REPRODUCTION.md`
- 复现实验报告：`wanet_reproduction_report.md`
- 防御实验代码：`defenses/`
- 模型训练与评估：`train.py`、`eval.py`
- 交互式演示：`dashboard/index.html`
- PPT：`WaNet.pptx`

---

## 核心结果

### 1. Noise Mode 是绕过防御的关键

| 配置 | Clean Acc | ASR | Cross Acc | Neural Cleanse |
|------|-----------|-----|-----------|----------------|
| With Noise Mode | 92.84% | 99.15% | 89.71% | 检测不到 |
| Without Noise Mode | 92.74% | 98.21% | 0.00% | 能检测到 |

> 没有 Noise Mode 时，模型学到的是像素级捷径而非真正的 Warping 变换。

### 2. Warping 参数 s / k 敏感性

| s | ASR | | k | ASR |
|----|-----|-|----|-----|
| 0.25 | 74.12% | | 2 | 92.82% |
| 0.50 | 99.59% | | 4 | 99.15% |
| 1.00 | 98.29% | | 8 | 97.55% |

### 3. 频域检测器（创新点）

发现 Warping = 插值运算 = 频域留痕，设计频域特征 + SVM 分类器，AUC 0.735（STRIP 仅 0.50）。

| 方法 | AUC | 准确率 |
|------|-----|--------|
| 频域检测器 (Ours) | 0.735 | 67.33% |
| STRIP | ~0.50 | 等同随机 |

---

## 项目结构

```text
├── train.py / eval.py / config.py    # WaNet 训练与评估
├── freq_detector.py                  # 频域 Warping 检测器
├── utils/                            # 数据加载、运行时与通用工具
├── networks/                         # 网络模型定义
├── classifier_models/                # 分类器模型 (PreActResNet18 等)
├── defenses/                         # STRIP / Fine-Pruning / Neural Cleanse
├── checkpoints/                      # 训练好的模型权重 (.pth.tar)
├── scripts/                          # 消融实验运行脚本
│   └── teammate/                     # 主实验运行脚本 (tmux 等)
├── configs/                          # 消融实验参数配置
├── visualization/                    # 可视化代码
├── dashboard/                        # 交互式 Web 演示 (浏览器打开即可)
│   └── index.html
├── results/                          # 全部实验数据与图表
│   ├── ablation_*.json / *.csv       # 消融实验数据 (10 组)
│   ├── multiseed_*.json              # 多种子结果
│   ├── freq_detector/                # 频域检测器 (ROC/FFT/特征分布)
│   └── visualization/                # 可视化图表 (warping field/PSNR等)
├── docs/                             # 主实验报告 + 复现流程文档
├── report_assets/                    # 报告配图
├── WaNet.pptx                        # PPT
├── REPRODUCTION.md                   # 复现流程说明
├── wanet_reproduction_report.md      # 复现实验报告
└── wanet_reproduction_report.pdf     # 报告导出版本
```

---

## 运行说明

### 环境

```bash
conda create -n wanet python=3.10
conda activate wanet
pip install torch torchvision kornia opencv-python scikit-learn scipy matplotlib tqdm
```

### 训练

```bash
python train.py --dataset cifar10 --attack_mode all2one
```

### 评估

```bash
python eval.py --dataset cifar10 --attack_mode all2one
```

### 频域检测器

```bash
python freq_detector.py
```

### 防御实验

相关脚本位于 `defenses/STRIP`、`defenses/fine_pruning`、`defenses/neural_cleanse`。

---

## 参考资料

- WaNet 论文: [WaNet - Imperceptible Warping-based Backdoor Attack](https://openreview.net/forum?id=eEn8KTtJOx)
- 官方实现: [VinAIResearch/Warping-based_Backdoor_Attack-release](https://github.com/VinAIResearch/Warping-based_Backdoor_Attack-release)

---

## License

本项目为 AI 安全课程作业，仅供学习研究使用。
