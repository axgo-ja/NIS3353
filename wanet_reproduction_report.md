# WaNet 论文复现实验报告

## 论文信息

- 论文题目：WaNet: Imperceptible Warping-based Backdoor Attack
- 作者：Tuan Anh Nguyen, Anh Tuan Tran
- 会议：ICLR 2021
- 论文方向：AI 安全，后门攻击，模型鲁棒性评估
- 官方实现：https://github.com/VinAIResearch/Warping-based_Backdoor_Attack-release
- OpenReview：https://openreview.net/forum?id=eEn8KTtJOx

## 背景：关注什么问题

深度神经网络在图像分类等任务中表现良好，但训练数据和模型训练流程一旦被攻击者污染，模型可能学到隐藏的后门行为。后门攻击的典型目标是：模型在正常输入上保持较高准确率，但在带有特定触发器的输入上输出攻击者指定的标签。

传统后门攻击通常依赖可见的贴片、图案或局部扰动作为触发器。这类触发器虽然容易实现，但也更容易被人工检查、数据增强、异常检测或防御方法发现。WaNet 关注的问题是：能否构造一种视觉上更隐蔽、更难被已有防御发现的后门触发方式。

## 问题：挑战是什么

WaNet 需要同时满足三个目标：

1. 隐蔽性：触发器不能像固定贴片一样明显，输入图像被攻击后应尽量保持自然。
2. 有效性：后门样本应能以较高概率被分类到攻击目标标签，攻击成功率要高。
3. 正常性能：模型在干净测试集上的准确率不能明显下降，否则攻击容易暴露。

复现实验本身也有挑战。该论文的攻击依赖随机形变网格、训练过程中的 poisoned samples 和 noise samples，同时 defense 实验涉及 STRIP、Fine-Pruning、Neural Cleanse 等不同流程。为了避免只复现单一配置，本次实验覆盖了多个数据集和攻击模式。

## 方法：如何解决挑战

WaNet 的核心思想是使用图像形变作为后门触发器，而不是添加显式贴片。攻击者生成一个平滑的 warping field，对输入图像做轻微空间扭曲，使图像内容整体保持自然，但模型会学习到这种空间形变与目标标签之间的关联。

本次复现使用官方实现，并在本地环境中补充了运行脚本和结果管理逻辑。主要实验设置如下：

- 数据集：MNIST、CIFAR-10、GTSRB
- 攻击模式：all2one、all2all
- 主指标：Clean test accuracy、Attack test accuracy、Noise test accuracy
- Defense：STRIP、Fine-Pruning、Neural Cleanse
- 随机种子：seed 0
- 运行方式：使用 tmux 后台运行，GPU0/GPU1 并行执行任务

核心复现命令如下：

```bash
cd /home/zilia/project/experiment/wanet
bash scripts/start_weekend_tmux.sh
```

状态检查命令如下：

```bash
bash scripts/status_weekend.sh
tail -f logs/weekend_latest/summary.tsv
```

## 实验运行和结果截图

实验使用 tmux 后台运行。最终 CPU、GPU0、GPU1 三个 worker 均正常完成。

下面两张截图来自真实 tmux pane，通过 `tmux capture-pane` 捕获最终运行界面。完整捕获文本保存在 `report_assets/tmux_gpu0_final.txt` 和 `report_assets/tmux_gpu1_final.txt`。

![GPU0 tmux 最终界面](report_assets/real_tmux_gpu0_final.png)

![GPU1 tmux 最终界面](report_assets/real_tmux_gpu1_final.png)

下面截图来自真实运行日志 `logs/weekend_20260613_194939/summary.tsv` 的尾部，记录了训练、评估和防御任务完成时间。

![summary.tsv 运行日志截图](report_assets/real_summary_tsv_tail.png)

主实验结果截图来自 6 个真实 `eval_results.json` 文件，路径为 `checkpoints/<dataset>/<attack_mode>/eval_results.json`。

![eval_results.json 文件截图](report_assets/real_eval_json_files.png)

STRIP 防御结果截图来自 `defenses/STRIP/results/` 下的真实输出文件。由于原文件每行包含 1000 个 entropy 数值，截图中展示每个文件的行数、样本数以及前缀内容。

![STRIP 结果文件截图](report_assets/real_strip_file_snippets.png)

Fine-Pruning 防御结果截图来自 `defenses/fine_pruning/results/` 下的真实结果文件，展示每个文件的开头和结尾部分。

![Fine-Pruning 结果文件截图](report_assets/real_fine_pruning_file_snippets.png)

Neural Cleanse 结果截图来自 `defenses/neural_cleanse/results/` 下的真实输出文件。本次只运行了 MNIST all2one 和 CIFAR-10 all2one 两组 Neural Cleanse。

![Neural Cleanse 结果文件截图](report_assets/real_neural_cleanse_file_tail.png)

## 结果：效果如何

### 主实验结果

all2one 参考值来自官方 README 的 Results 表；all2all 参考值使用论文/复现整理中的对应参考值。官方 README 说明 Noise test 可能由于随机噪声生成而存在波动。

| 数据集 | 攻击模式 | 复现 Clean | 复现 Attack | 复现 Noise | 参考 Clean | 参考 Attack | 参考 Noise | 差异 Clean | 差异 Attack | 差异 Noise |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MNIST | all2one | 99.50 | 99.98 | 99.16 | 99.52 | 99.86 | 98.20 | -0.02 | +0.12 | +0.96 |
| CIFAR-10 | all2one | 94.52 | 99.37 | 92.52 | 94.15 | 99.55 | 93.55 | +0.37 | -0.18 | -1.03 |
| GTSRB | all2one | 99.34 | 99.75 | 99.03 | 98.87 | 99.33 | 98.01 | +0.47 | +0.42 | +1.02 |
| MNIST | all2all | 99.45 | 99.16 | 99.18 | 99.44 | 95.90 | 94.34 | +0.01 | +3.26 | +4.84 |
| CIFAR-10 | all2all | 94.36 | 93.52 | 92.65 | 94.43 | 93.36 | 91.47 | -0.07 | +0.16 | +1.18 |
| GTSRB | all2all | 99.59 | 99.22 | 99.14 | 99.39 | 98.31 | 98.96 | +0.20 | +0.91 | +0.18 |

总体来看，6 个主设置均成功复现出高 clean accuracy 和高 attack accuracy。all2one 的三组结果与官方表基本一致；CIFAR-10 all2one 的 Noise accuracy 比参考值低约 1.03 个百分点，但仍在可接受波动范围内。MNIST all2all 的 Attack 和 Noise 指标高于参考值，说明本次训练得到的后门更强，但 clean accuracy 与参考值保持一致。

### STRIP 结果

STRIP 在本次复现中的检测阈值为 0.2。6 个设置的 trojan entropy 最小值均显著高于 0.2，因此 STRIP 不会将这些样本稳定判定为后门样本。这与论文中 WaNet 能绕过 STRIP 的结论一致。

| 数据集 | 攻击模式 | Trojan entropy 最小值 | Trojan entropy 均值 | Benign entropy 均值 |
|---|---|---:|---:|---:|
| MNIST | all2one | 1.177 | 1.703 | 1.772 |
| MNIST | all2all | 1.734 | 2.295 | 1.916 |
| CIFAR-10 | all2one | 2.216 | 2.684 | 2.637 |
| CIFAR-10 | all2all | 2.019 | 2.761 | 2.700 |
| GTSRB | all2one | 9.270 | 11.999 | 10.588 |
| GTSRB | all2all | 10.189 | 12.804 | 12.565 |

### Fine-Pruning 结果

Fine-Pruning 的趋势也与论文结论一致：当 clean accuracy 仍然保持在 90% 以上时，attack accuracy 通常仍然较高。这说明 WaNet 后门并不容易通过简单剪枝完全消除。

| 数据集 | 攻击模式 | 原始 Clean / Attack | Clean 仍大于 90% 时的最后结果 |
|---|---|---:|---:|
| MNIST | all2one | 99.50 / 99.98 | 90.69 / 99.91 |
| MNIST | all2all | 99.45 / 99.16 | 90.22 / 95.97 |
| CIFAR-10 | all2one | 94.52 / 99.37 | 90.02 / 99.91 |
| CIFAR-10 | all2all | 94.36 / 93.52 | 90.36 / 86.74 |
| GTSRB | all2one | 99.34 / 99.75 | 90.27 / 99.76 |
| GTSRB | all2all | 99.59 / 99.22 | 90.35 / 70.38 |

### Neural Cleanse 结果

Neural Cleanse 仅复现了 MNIST all2one 和 CIFAR-10 all2one。官方实现说明 Neural Cleanse 本身不稳定，anomaly index 可能随运行变化。本次复现中 anomaly index 没有形成持续稳定的强检测信号，整体符合 WaNet 难以被 Neural Cleanse 稳定检出的趋势。

### 复现范围说明

本次已完成：

- MNIST、CIFAR-10、GTSRB 三个数据集的 all2one 和 all2all 主结果
- STRIP：3 个数据集 × 2 个攻击模式
- Fine-Pruning：3 个数据集 × 2 个攻击模式
- Neural Cleanse：MNIST all2one、CIFAR-10 all2one

本次未覆盖：

- CelebA 实验
- 多随机种子平均和方差
- 论文中的所有消融实验
- 所有可视化与感知性分析
- Neural Cleanse 在所有数据集和攻击模式上的完整组合

## 结论

本次复现实验成功复现了 WaNet 的主要攻击效果。模型在干净样本上保持较高准确率，同时在后门样本上具有较高攻击成功率，说明基于图像空间形变的后门触发器能够兼顾隐蔽性和攻击有效性。防御实验也显示，STRIP 和 Fine-Pruning 难以稳定消除或检测 WaNet 后门，Neural Cleanse 的检测结果也不稳定。这与论文对 WaNet 隐蔽性和防御绕过能力的分析基本一致。

## 成员贡献

- 周争妍：完成论文选择与资料整理；配置本地 Conda/GPU 实验环境；修复官方代码在当前环境中的兼容性和结果污染问题；编写 tmux 后台运行脚本；完成 MNIST、CIFAR-10、GTSRB 上 all2one/all2all 主实验；完成 STRIP、Fine-Pruning、Neural Cleanse 防御实验；整理实验结果、截图和报告。
- 成员 2：
