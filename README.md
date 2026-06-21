# WaNet 复现与分析

**ICLR 2021 论文复现 | 消融实验 | 频域后门检测器**

---

## 项目简介

WaNet (ICLR 2021) 提出使用图像空间形变 (warping) 作为后门触发器——通过对图像施加人眼不可察觉的几何扭曲，实现高攻击成功率的同时绕过现有防御。

本项目完成了三部分工作：
1. 在 CIFAR-10 / MNIST / GTSRB 上复现 WaNet，验证其攻击有效性和防御绕过能力
2. 通过消融实验系统分析 Noise Mode、warping 强度 s、网格大小 k 对攻击效果的影响
3. 基于 warping 依赖插值运算这一观察，设计频域检测器，AUC 0.735（STRIP 仅 0.50）

---

## 项目结构

```
├── train.py / eval.py / config.py    # 训练、评估、参数配置
├── freq_detector.py                  # 频域 Warping 检测器
├── requirements.txt
│
├── utils/                            # 数据加载、运行时、warp 工具
├── networks/                         # 网络模型定义
├── classifier_models/                # 分类器 (PreActResNet18 等)
├── defenses/                         # STRIP / Fine-Pruning / Neural Cleanse
├── checkpoints/                      # 训练好的模型权重
├── scripts/                          # 消融实验脚本
│   └── teammate/                     # 队友主实验运行脚本
├── configs/                          # 消融参数配置
├── visualization/                    # 可视化代码
├── dashboard/                        # 交互式演示页面
├── results/                          # 全部实验数据与图表
│   ├── ablation_*.json / *.csv       # 消融实验数据
│   ├── freq_detector/                # 频域检测器结果
│   └── visualization/                # 可视化图表
├── docs/                             # 复现文档与报告
└── report_assets/                    # 报告配图
```

---

## 核心结果

### Noise Mode 是绕过防御的关键

| | Clean Acc | ASR | Cross Acc |
|------|-----------|-----|-----------|
| With Noise | 92.84% | 99.15% | 89.71% |
| Without Noise | 92.74% | 98.21% | **0.00%** |

### s / k 参数敏感性

| s | ASR | | k | ASR |
|----|-----|-|----|-----|
| 0.25 | 74.12% | | 2 | 92.82% |
| 0.50 | 99.59% | | 4 | 99.15% |
| 1.00 | 98.29% | | 8 | 97.55% |

### 频域检测器 vs STRIP

| 方法 | AUC | 准确率 |
|------|-----|--------|
| 频域检测器 | **0.735** | 67.33% |
| STRIP | ~0.50 | 等同随机 |

---

## 快速开始

```bash
conda create -n wanet python=3.10 && conda activate wanet
pip install torch torchvision kornia opencv-python scikit-learn scipy matplotlib tqdm
python train.py --dataset cifar10 --attack_mode all2one    # 训练
python eval.py --dataset cifar10 --attack_mode all2one     # 评估
python freq_detector.py                                     # 频域检测器
```

---

## 参考资料

- WaNet: [Imperceptible Warping-based Backdoor Attack](https://openreview.net/forum?id=eEn8KTtJOx) (ICLR 2021)
- 官方实现: [VinAIResearch/Warping-based_Backdoor_Attack-release](https://github.com/VinAIResearch/Warping-based_Backdoor_Attack-release)
