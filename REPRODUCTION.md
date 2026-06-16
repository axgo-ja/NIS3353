# WaNet 复现流程

这个目录已经调整到可直接在本机 `model` 环境下运行，默认主复现实验是论文 README 中最常用的 `CIFAR-10 + all2one`。

## 1. 环境

```bash
cd /home/zilia/project/experiment/wanet
bash scripts/setup_model_env.sh
```

当前按本机实际环境适配的是：

- Python `3.10`
- PyTorch `2.6.0+cu124`
- torchvision `0.21.0`
- GPU 默认使用 `CUDA_VISIBLE_DEVICES=0`

## 2. 数据

下载 CIFAR-10：

```bash
bash scripts/download_cifar10.sh
```

默认会使用一个国内可达性更好的镜像源。如果你想手动切换下载地址，可以覆盖环境变量：

```bash
CIFAR10_URL="https://mindspore-website.obs.cn-north-4.myhuaweicloud.com/notebook/datasets/cifar-10-python.tar.gz" \
bash scripts/download_cifar10.sh
```

如果你已经在后台下载过，可以查看状态：

```bash
bash scripts/status_cifar10_download.sh
```

数据成功后应存在：

```text
data/cifar-10-batches-py
```

## 3. 主实验

训练：

```bash
bash scripts/train_cifar10_all2one.sh
```

如果训练中断，可以直接续跑：

```bash
bash scripts/train_cifar10_all2one.sh --continue_training
```

如果你想先做快速冒烟测试：

```bash
bash scripts/train_cifar10_all2one.sh --n_iters 1 --bs 128 --num_workers 2 --checkpoints ./checkpoints_dryrun
```

评测：

```bash
bash scripts/eval_cifar10_all2one.sh
```

评测结果会额外写到：

```text
checkpoints/cifar10/eval_results.json
```

训练保存的最优结果在：

```text
checkpoints/cifar10/results.txt
```

论文 README 给出的参考结果：

| Dataset | Clean test | Attack test | Noise test |
| --- | ---: | ---: | ---: |
| CIFAR-10 | 94.15 | 99.55 | 93.55 |

在这份代码里：

- `clean_acc` 对应 clean test
- `bd_acc` 对应 attack test
- `cross_acc` 对应 README 中的 noise test

## 4. Defense

先跑一个最容易交差的 defense：`STRIP`

```bash
bash scripts/strip_cifar10_all2one.sh
```

输出会写到：

```text
defenses/STRIP/results/cifar10/all2one/cifar10_all2one_output.txt
```

如果你还要补论文里的其他 defense：

```bash
cd defenses/fine_pruning
python fine-pruning-cifar10-gtsrb.py --dataset cifar10 --attack_mode all2one

cd ../neural_cleanse
python neural_cleanse.py --dataset cifar10 --attack_mode all2one
```

## 5. 建议交付内容

你的作业报告至少保留下面这些信息：

1. 论文信息：`WaNet`, `ICLR 2021`
2. 机器配置：GPU、CUDA、PyTorch 版本
3. 训练命令、随机种子、batch size、总 epoch/iter
4. 复现结果表：`clean_acc / bd_acc / cross_acc`
5. 与论文参考结果对比
6. 偏差分析：下载源、随机性、PyTorch 版本差异、训练时长是否一致

## 6. 常用命令

完整跑一遍：

```bash
bash scripts/reproduce_cifar10_all2one.sh
```

指定另一张 GPU：

```bash
CUDA_VISIBLE_DEVICES=1 bash scripts/train_cifar10_all2one.sh
```
