# WaNet 复现报告模板

## 1. 论文信息

- 论文标题：WaNet: Imperceptible Warping-based Backdoor Attack
- 作者：Tuan Anh Nguyen, Anh Tuan Tran
- 会议：ICLR 2021
- 任务方向：AI 安全 / Backdoor Attack

## 2. 复现目标

本次复现选择论文中的 `CIFAR-10 + all2one` 主实验，目标是复现模型在 clean test、attack test、noise test 上的性能，并补充至少一个 defense 实验。

## 3. 实验环境

- 服务器：
- GPU：
- CUDA：
- Python：
- PyTorch：
- torchvision：
- 运行环境：`conda activate model`

## 4. 复现设置

- 数据集：CIFAR-10
- 攻击模式：all2one
- 目标标签：0
- batch size：
- 训练轮数：
- 随机种子：
- 关键命令：

```bash
bash scripts/train_cifar10_all2one.sh
bash scripts/eval_cifar10_all2one.sh
```

## 5. 结果对比

| 指标 | 论文结果 | 我的结果 | 绝对差值 |
| --- | ---: | ---: | ---: |
| Clean test | 94.15 |  |  |
| Attack test | 99.55 |  |  |
| Noise test | 93.55 |  |  |

## 6. Defense 结果

### STRIP

- 命令：

```bash
bash scripts/strip_cifar10_all2one.sh
```

- 现象：
- 结果文件：

## 7. 误差分析

- 与论文不一致的部分：
- 可能原因：
- 是否影响结论：

## 8. 结论

本次复现是否成功：
