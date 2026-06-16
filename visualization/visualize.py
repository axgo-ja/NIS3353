#!/usr/bin/env python
# =============================================================================
# WaNet 可视化与感知分析
# 功能:
#   1. Warping field 可视化 (控制网格 + 变形场)
#   2. 原图 vs 变形图对比
#   3. PSNR / SSIM / LPIPS 量化不可感知性
#   4. 不同 s, k 参数下的变形效果对比
# =============================================================================
import os
import sys
import json
import argparse
import numpy as np
import torch
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from skimage.metrics import structural_similarity as ssim

# Add project root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from utils.runtime import build_warp_grids, populate_dataset_attributes
import config


# ======================== 配置 ========================

DATASET_CONFIGS = {
    "mnist":    {"num_classes": 10, "input_height": 28, "input_width": 28, "input_channel": 1},
    "cifar10":  {"num_classes": 10, "input_height": 32, "input_width": 32, "input_channel": 3},
    "gtsrb":    {"num_classes": 43, "input_height": 32, "input_width": 32, "input_channel": 3},
    "celeba":   {"num_classes": 8,  "input_height": 64, "input_width": 64, "input_channel": 3},
}

OUTPUT_DIR = os.path.join(REPO_ROOT, "results", "visualization")


# ======================== Warping 函数 ========================

def create_warped_images(images, noise_grid, identity_grid, s, k, input_height, grid_rescale=1.0):
    """
    对输入图像应用 WaNet warping。
    返回: warped_images, cross_images
    """
    bs = images.shape[0]
    device = images.device

    # 标准 warping
    grid_temps = (identity_grid + s * noise_grid / input_height) * grid_rescale
    grid_temps = torch.clamp(grid_temps, -1, 1)
    warped = F.grid_sample(images, grid_temps.repeat(bs, 1, 1, 1), align_corners=True)

    # Cross warping (随机扰动)
    ins = torch.rand(bs, input_height, input_height, 2).to(device) * 2 - 1
    grid_temps2 = grid_temps.repeat(bs, 1, 1, 1) + ins / input_height
    grid_temps2 = torch.clamp(grid_temps2, -1, 1)
    warped_cross = F.grid_sample(images, grid_temps2, align_corners=True)

    return warped, warped_cross


# ======================== PSNR / SSIM 计算 ========================

def compute_psnr(img1, img2):
    """计算两张图像之间的 PSNR (dB)"""
    mse = torch.mean((img1 - img2) ** 2).item()
    if mse == 0:
        return float("inf")
    return 20 * np.log10(2.0) - 10 * np.log10(mse)  # 像素范围 [-1, 1] -> max=2


def compute_ssim(img1, img2, multichannel=True):
    """计算两张图像之间的 SSIM"""
    # 转换到 [0, 1]
    img1_np = ((img1.permute(1, 2, 0).cpu().numpy() + 1) / 2).astype(np.float64)
    img2_np = ((img2.permute(1, 2, 0).cpu().numpy() + 1) / 2).astype(np.float64)
    data_range = 1.0

    if img1_np.shape[-1] == 1:
        multichannel = False

    return ssim(img1_np, img2_np, data_range=data_range, channel_axis=-1 if multichannel else None)


# ======================== 可视化 1: Warping Field ========================

def visualize_warping_field(opt, save_path):
    """可视化 control grid 和 warping field"""
    noise_grid, identity_grid = build_warp_grids(opt)
    noise_grid_np = noise_grid.squeeze(0).cpu().numpy()
    identity_np = identity_grid.squeeze(0).cpu().numpy()

    h, w = opt.input_height, opt.input_width

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # (a) Identity grid
    axes[0].set_title("Identity Grid", fontsize=14, fontweight="bold")
    step = max(h // 8, 2)
    for i in range(0, h, step):
        axes[0].plot(identity_np[i, :, 0], identity_np[i, :, 1], "b-", alpha=0.4, linewidth=0.5)
    for j in range(0, w, step):
        axes[0].plot(identity_np[:, j, 0], identity_np[:, j, 1], "b-", alpha=0.4, linewidth=0.5)
    axes[0].set_xlim(-1.1, 1.1)
    axes[0].set_ylim(-1.1, 1.1)
    axes[0].set_aspect("equal")

    # (b) Warped grid (identity + s * noise)
    s = opt.s
    warped_grid = identity_np + s * noise_grid_np / h
    axes[1].set_title(f"Warped Grid (s={s}, k={opt.k})", fontsize=14, fontweight="bold")
    for i in range(0, h, step):
        axes[1].plot(warped_grid[i, :, 0], warped_grid[i, :, 1], "r-", alpha=0.4, linewidth=0.5)
    for j in range(0, w, step):
        axes[1].plot(warped_grid[:, j, 0], warped_grid[:, j, 1], "r-", alpha=0.4, linewidth=0.5)
    axes[1].set_xlim(-1.1, 1.1)
    axes[1].set_ylim(-1.1, 1.1)
    axes[1].set_aspect("equal")

    # (c) Deformation magnitude heatmap
    deformation = np.sqrt(
        (warped_grid[:, :, 0] - identity_np[:, :, 0]) ** 2
        + (warped_grid[:, :, 1] - identity_np[:, :, 1]) ** 2
    )
    im = axes[2].imshow(deformation, cmap="hot", origin="lower")
    axes[2].set_title("Deformation Magnitude", fontsize=14, fontweight="bold")
    plt.colorbar(im, ax=axes[2], fraction=0.046)

    plt.suptitle(f"WaNet Warping Field ({opt.dataset.upper()}, s={s}, k={opt.k})",
                 fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Warping field saved to: {save_path}")


# ======================== 可视化 2: 原图 vs 变形图 ========================

def visualize_image_comparison(opt, dataloader, noise_grid, identity_grid, save_path, n_samples=8):
    """对比原图、后门图、Cross 图、残差"""
    # 获取一批数据
    images, labels = next(iter(dataloader))
    images = images[:n_samples].to(opt.device)

    # 生成变形图像
    bd_images, cross_images = create_warped_images(
        images, noise_grid, identity_grid, opt.s, opt.k, opt.input_height
    )

    # 计算残差 (放大 5 倍以便可视化)
    residuals = (bd_images - images).abs() * 5
    residuals = torch.clamp(residuals, 0, 1)

    # Denormalize
    denorm = get_denormalizer(opt)
    images = denorm(images) if denorm else images
    bd_images = denorm(bd_images) if denorm else bd_images
    cross_images = denorm(cross_images) if denorm else cross_images

    # 转为 [0, 1]
    images = torch.clamp((images + 1) / 2, 0, 1)
    bd_images = torch.clamp((bd_images + 1) / 2, 0, 1)
    cross_images = torch.clamp((cross_images + 1) / 2, 0, 1)

    n_rows = min(n_samples, 8)
    fig, axes = plt.subplots(n_rows, 4, figsize=(12, 2.5 * n_rows))

    titles = ["Original", "Backdoor (M)", "Cross (M')", "Residual ×5"]
    for col, title in enumerate(titles):
        axes[0, col].set_title(title, fontsize=12, fontweight="bold")

    for row in range(n_rows):
        # Original
        img = images[row].cpu().permute(1, 2, 0).numpy()
        if img.shape[-1] == 1:
            img = img.repeat(3, axis=-1)
        axes[row, 0].imshow(np.clip(img, 0, 1))
        axes[row, 0].axis("off")

        # Backdoor
        img_bd = bd_images[row].cpu().permute(1, 2, 0).numpy()
        if img_bd.shape[-1] == 1:
            img_bd = img_bd.repeat(3, axis=-1)
        axes[row, 1].imshow(np.clip(img_bd, 0, 1))
        axes[row, 1].axis("off")

        # Cross
        img_cross = cross_images[row].cpu().permute(1, 2, 0).numpy()
        if img_cross.shape[-1] == 1:
            img_cross = img_cross.repeat(3, axis=-1)
        axes[row, 2].imshow(np.clip(img_cross, 0, 1))
        axes[row, 2].axis("off")

        # Residual
        res = residuals[row].cpu().permute(1, 2, 0).numpy()
        if res.shape[-1] == 1:
            res = res.repeat(3, axis=-1)
        axes[row, 3].imshow(np.clip(res, 0, 1))
        axes[row, 3].axis("off")

    plt.suptitle(f"WaNet Image Comparison: {opt.dataset.upper()} (s={opt.s}, k={opt.k})",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Image comparison saved to: {save_path}")


# ======================== 可视化 3: PSNR/SSIM 统计分析 ========================

def compute_perceptual_metrics(opt, dataloader, noise_grid, identity_grid, save_path, n_samples=100):
    """计算 PSNR, SSIM 并绘制直方图"""
    all_psnr = []
    all_ssim = []

    denorm = get_denormalizer(opt)
    total = 0

    for images, _ in dataloader:
        if total >= n_samples:
            break
        images = images[: min(images.shape[0], n_samples - total)].to(opt.device)
        total += images.shape[0]

        bd_images, _ = create_warped_images(
            images, noise_grid, identity_grid, opt.s, opt.k, opt.input_height
        )

        # 计算 PSNR (在 pixel space)
        if denorm:
            images_pix = denorm(images)
            bd_images_pix = denorm(bd_images)
        else:
            images_pix = images
            bd_images_pix = bd_images

        for i in range(images.shape[0]):
            psnr_val = compute_psnr(images_pix[i], bd_images_pix[i])
            ssim_val = compute_ssim(images_pix[i], bd_images_pix[i],
                                    multichannel=(images_pix[i].shape[0] == 3))
            all_psnr.append(psnr_val)
            all_ssim.append(ssim_val)

    all_psnr = np.array(all_psnr)
    all_ssim = np.array(all_ssim)

    # 绘制直方图
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(all_psnr, bins=30, color="steelblue", edgecolor="white", alpha=0.8)
    axes[0].axvline(np.mean(all_psnr), color="red", linestyle="--",
                    label=f"Mean: {np.mean(all_psnr):.2f} dB")
    axes[0].axvline(np.median(all_psnr), color="orange", linestyle="--",
                    label=f"Median: {np.median(all_psnr):.2f} dB")
    axes[0].set_xlabel("PSNR (dB)", fontsize=12)
    axes[0].set_ylabel("Count", fontsize=12)
    axes[0].set_title(f"PSNR Distribution ({opt.dataset.upper()})", fontsize=14, fontweight="bold")
    axes[0].legend()

    axes[1].hist(all_ssim, bins=30, color="darkgreen", edgecolor="white", alpha=0.8)
    axes[1].axvline(np.mean(all_ssim), color="red", linestyle="--",
                    label=f"Mean: {np.mean(all_ssim):.4f}")
    axes[1].axvline(np.median(all_ssim), color="orange", linestyle="--",
                    label=f"Median: {np.median(all_ssim):.4f}")
    axes[1].set_xlabel("SSIM", fontsize=12)
    axes[1].set_ylabel("Count", fontsize=12)
    axes[1].set_title(f"SSIM Distribution ({opt.dataset.upper()})", fontsize=14, fontweight="bold")
    axes[1].legend()

    plt.suptitle(f"WaNet Perceptual Quality (s={opt.s}, k={opt.k})",
                 fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    # 输出统计
    stats = {
        "dataset": opt.dataset,
        "s": opt.s,
        "k": opt.k,
        "n_samples": int(total),
        "psnr_mean": float(np.mean(all_psnr)),
        "psnr_std": float(np.std(all_psnr)),
        "psnr_min": float(np.min(all_psnr)),
        "psnr_median": float(np.median(all_psnr)),
        "ssim_mean": float(np.mean(all_ssim)),
        "ssim_std": float(np.std(all_ssim)),
        "ssim_min": float(np.min(all_ssim)),
    }
    stats_path = save_path.replace(".png", ".json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"[OK] PSNR/SSIM analysis saved to: {save_path}")
    print(f"     Stats saved to: {stats_path}")
    print(f"     PSNR: {stats['psnr_mean']:.2f} ± {stats['psnr_std']:.2f} dB")
    print(f"     SSIM: {stats['ssim_mean']:.4f} ± {stats['ssim_std']:.4f}")

    return stats


# ======================== 可视化 4: 不同 s/k 参数对比 ========================

def visualize_parameter_effects(opt, dataloader, save_path):
    """展示不同 s 和 k 参数下变形效果的对比"""
    images, _ = next(iter(dataloader))
    img = images[0:1].to(opt.device)  # 只取一张图

    s_values = [0.25, 0.5, 0.75, 1.0]
    k_values = [2, 4, 6, 8]

    denorm = get_denormalizer(opt)

    fig, axes = plt.subplots(len(s_values), len(k_values), figsize=(16, 14))

    for i, s in enumerate(s_values):
        for j, k in enumerate(k_values):
            # 为每组 (s, k) 创建新的 warp grids
            ins = torch.rand(1, 2, k, k) * 2 - 1
            ins = ins / torch.mean(torch.abs(ins))
            noise_grid = F.interpolate(
                ins, size=opt.input_height, mode="bicubic", align_corners=True
            )
            noise_grid = noise_grid.permute(0, 2, 3, 1).to(opt.device)

            array1d = torch.linspace(-1, 1, steps=opt.input_height)
            grid_y, grid_x = torch.meshgrid(array1d, array1d, indexing="ij")
            identity_grid = torch.stack((grid_x, grid_y), dim=2)[None, ...].to(opt.device)

            bd, _ = create_warped_images(img, noise_grid, identity_grid, s, k, opt.input_height)

            if denorm:
                bd_disp = denorm(bd)
            else:
                bd_disp = bd
            bd_disp = torch.clamp((bd_disp + 1) / 2, 0, 1)

            bd_np = bd_disp[0].cpu().permute(1, 2, 0).numpy()
            if bd_np.shape[-1] == 1:
                bd_np = bd_np.repeat(3, axis=-1)

            axes[i, j].imshow(np.clip(bd_np, 0, 1))
            axes[i, j].set_title(f"s={s}, k={k}", fontsize=10)
            axes[i, j].axis("off")

    # 行标题
    for i, s in enumerate(s_values):
        axes[i, 0].set_ylabel(f"s = {s}", fontsize=14, fontweight="bold", rotation=90, labelpad=20)
    # 列标题
    for j, k in enumerate(k_values):
        axes[0, j].set_title(f"k = {k}", fontsize=14, fontweight="bold", pad=10)

    plt.suptitle("WaNet: Effect of Warping Parameters (s, k) on Image Appearance",
                 fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Parameter effects saved to: {save_path}")


# ======================== 可视化 5: 消融结果汇总图 ========================

def visualize_ablation_summary(results_dir, save_path):
    """绘制消融实验的 Clean/Attack/Cross accuracy 曲线"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # --- (a) s 消融 ---
    s_values = [0.25, 0.5, 0.75, 1.0]
    s_clean, s_bd, s_cross = [], [], []
    for s in s_values:
        result_file = os.path.join(results_dir, f"ablation_s_{s}.json")
        if os.path.exists(result_file):
            with open(result_file) as f:
                r = json.load(f)
            s_clean.append(r["clean_acc"])
            s_bd.append(r["bd_acc"])
            s_cross.append(r["cross_acc"])
        else:
            s_clean.append(None)
            s_bd.append(None)
            s_cross.append(None)

    s_vals_plot = [v for v, c in zip(s_values, s_clean) if c is not None]

    axes[0].plot(s_vals_plot, [c for c in s_clean if c is not None], "o-", label="Clean", linewidth=2, markersize=8)
    axes[0].plot(s_vals_plot, [c for c in s_bd if c is not None], "s-", label="Backdoor", linewidth=2, markersize=8)
    axes[0].plot(s_vals_plot, [c for c in s_cross if c is not None], "^-", label="Cross/Noise", linewidth=2, markersize=8)
    axes[0].set_xlabel("Warping Strength s", fontsize=12)
    axes[0].set_ylabel("Accuracy (%)", fontsize=12)
    axes[0].set_title("Effect of Warping Strength s", fontsize=13, fontweight="bold")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # --- (b) k 消融 ---
    k_values = [2, 4, 6, 8]
    k_clean, k_bd, k_cross = [], [], []
    for k in k_values:
        result_file = os.path.join(results_dir, f"ablation_k_{k}.json")
        if os.path.exists(result_file):
            with open(result_file) as f:
                r = json.load(f)
            k_clean.append(r["clean_acc"])
            k_bd.append(r["bd_acc"])
            k_cross.append(r["cross_acc"])
        else:
            k_clean.append(None)
            k_bd.append(None)
            k_cross.append(None)

    k_vals_plot = [v for v, c in zip(k_values, k_clean) if c is not None]

    axes[1].plot(k_vals_plot, [c for c in k_clean if c is not None], "o-", label="Clean", linewidth=2, markersize=8)
    axes[1].plot(k_vals_plot, [c for c in k_bd if c is not None], "s-", label="Backdoor", linewidth=2, markersize=8)
    axes[1].plot(k_vals_plot, [c for c in k_cross if c is not None], "^-", label="Cross/Noise", linewidth=2, markersize=8)
    axes[1].set_xlabel("Grid Size k", fontsize=12)
    axes[1].set_ylabel("Accuracy (%)", fontsize=12)
    axes[1].set_title("Effect of Grid Size k", fontsize=13, fontweight="bold")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # --- (c) Noise Mode 对比 ---
    noise_labels = []
    noise_clean, noise_bd, noise_cross = [], [], []
    for mode, label in [("with", "With Noise"), ("without", "Without Noise")]:
        result_file = os.path.join(results_dir, f"ablation_noisemode_{mode}.json")
        if os.path.exists(result_file):
            with open(result_file) as f:
                r = json.load(f)
            noise_labels.append(label)
            noise_clean.append(r["clean_acc"])
            noise_bd.append(r["bd_acc"])
            noise_cross.append(r.get("cross_acc", 0))

    x = np.arange(len(noise_labels))
    width = 0.25
    axes[2].bar(x - width, noise_clean, width, label="Clean", color="steelblue")
    axes[2].bar(x, noise_bd, width, label="Backdoor", color="crimson")
    axes[2].bar(x + width, noise_cross, width, label="Cross/Noise", color="darkgreen")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(noise_labels)
    axes[2].set_ylabel("Accuracy (%)", fontsize=12)
    axes[2].set_title("Effect of Noise Mode", fontsize=13, fontweight="bold")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3, axis="y")

    plt.suptitle("WaNet Ablation Study Summary (CIFAR-10)", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Ablation summary saved to: {save_path}")


# ======================== 辅助函数 ========================

def get_denormalizer(opt):
    """返回 denormalization 函数（None 表示不需要）"""
    if opt.dataset == "cifar10":
        mean = torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1).to(opt.device)
        std = torch.tensor([0.247, 0.243, 0.261]).view(1, 3, 1, 1).to(opt.device)
        return lambda x: x * std + mean
    elif opt.dataset == "mnist":
        return lambda x: x * 0.5 + 0.5
    else:
        return None


def get_dataloader(opt, n_samples=128):
    """获取测试集 dataloader"""
    transform = transforms.Compose([
        transforms.Resize((opt.input_height, opt.input_width)),
        transforms.ToTensor(),
    ])

    if opt.dataset == "cifar10":
        dataset = torchvision.datasets.CIFAR10(opt.data_root, train=False, transform=transform)
    elif opt.dataset == "mnist":
        transform = transforms.Compose([
            transforms.Resize((opt.input_height, opt.input_width)),
            transforms.ToTensor(),
        ])
        dataset = torchvision.datasets.MNIST(opt.data_root, train=False, transform=transform)
    elif opt.dataset == "gtsrb":
        from utils.dataloader import GTSRB
        dataset = GTSRB(opt, train=False, transforms=transform)
    else:
        raise ValueError(f"Unsupported dataset: {opt.dataset}")

    return torch.utils.data.DataLoader(
        dataset,
        batch_size=min(n_samples, 128),
        shuffle=True,
        num_workers=2,
    )


# ======================== 主函数 ========================

def main():
    parser = argparse.ArgumentParser(description="WaNet Visualization & Perceptual Analysis")
    parser.add_argument("--dataset", type=str, default="cifar10",
                        choices=["mnist", "cifar10", "gtsrb"])
    parser.add_argument("--data_root", type=str,
                        default=os.path.join(REPO_ROOT, "data"))
    parser.add_argument("--output_dir", type=str, default=OUTPUT_DIR)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--s", type=float, default=0.5)
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--results_dir", type=str,
                        default=os.path.join(REPO_ROOT, "results"))
    parser.add_argument("--all_datasets", action="store_true",
                        help="Run visualization on all datasets")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    datasets_to_run = DATASET_CONFIGS.keys() if args.all_datasets else [args.dataset]

    for ds_name in datasets_to_run:
        print(f"\n{'='*60}")
        print(f" Processing dataset: {ds_name.upper()}")
        print(f"{'='*60}")

        # 构造 opt
        opt = argparse.Namespace()
        for key, val in DATASET_CONFIGS[ds_name].items():
            setattr(opt, key, val)
        opt.dataset = ds_name
        opt.data_root = args.data_root
        opt.device = args.device
        opt.s = args.s
        opt.k = args.k
        opt.grid_rescale = 1.0

        # 生成 warping grids
        noise_grid, identity_grid = build_warp_grids(opt)
        dataloader = get_dataloader(opt)

        ds_output = os.path.join(args.output_dir, ds_name)
        os.makedirs(ds_output, exist_ok=True)

        # 1. Warping field 可视化
        visualize_warping_field(opt, os.path.join(ds_output, "warping_field.png"))

        # 2. 原图 vs 变形图对比
        visualize_image_comparison(
            opt, dataloader, noise_grid, identity_grid,
            os.path.join(ds_output, "image_comparison.png")
        )

        # 3. PSNR/SSIM 统计
        compute_perceptual_metrics(
            opt, dataloader, noise_grid, identity_grid,
            os.path.join(ds_output, "perceptual_metrics.png")
        )

    # 4. 不同 s/k 参数效果对比（只对第一个数据集）
    opt_main = argparse.Namespace()
    for key, val in DATASET_CONFIGS[args.dataset].items():
        setattr(opt_main, key, val)
    opt_main.dataset = args.dataset
    opt_main.data_root = args.data_root
    opt_main.device = args.device
    opt_main.s = args.s
    opt_main.k = args.k
    opt_main.grid_rescale = 1.0

    dl = get_dataloader(opt_main)
    visualize_parameter_effects(
        opt_main, dl,
        os.path.join(args.output_dir, "parameter_effects.png")
    )

    # 5. 消融结果汇总图
    visualize_ablation_summary(
        args.results_dir,
        os.path.join(args.output_dir, "ablation_summary.png")
    )

    print(f"\n{'='*60}")
    print(f" All visualizations saved to: {args.output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
