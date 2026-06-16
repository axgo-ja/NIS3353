#!/usr/bin/env python
"""
频域 Warping 后门检测器 —— 我们的创新点
核心思路: WaNet 的 warping 使用 grid_sample + bilinear interpolation
         插值运算会在频域留下可检测的痕迹
         现有防御(STRIP/NC)看模型行为 → 我们直接看图像信号
"""
import os, sys, json, argparse
import numpy as np
import torch
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from sklearn.svm import SVC
from sklearn.metrics import roc_curve, auc, accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift

# 项目路径
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_ROOT)
from utils.runtime import build_warp_grids, safe_torch_load
from networks.models import NetC_MNIST, Normalizer, Denormalizer
from classifier_models import PreActResNet18
from config import get_arguments


# ======================== 频域特征提取 ========================

def extract_freq_features(img_np):
    """
    对单张图像提取频域特征
    img_np: (C, H, W) numpy array, 灰度图则为 (H, W)
    返回: 特征向量 (6维)
    """
    if img_np.ndim == 3:
        # 彩色图: 对每个通道分别提取, 取平均
        feats = []
        for c in range(img_np.shape[0]):
            feats.append(_extract_single(img_np[c]))
        return np.mean(feats, axis=0)
    else:
        return _extract_single(img_np)


def _extract_single(channel):
    """对单通道图像提取频域特征"""
    # FFT
    f = fft2(channel)
    fshift = fftshift(f)
    magnitude = np.abs(fshift)

    H, W = magnitude.shape
    total = np.sum(magnitude)

    if total == 0:
        return np.zeros(6)

    # 特征1: 高频能量占比 (高频 = 外圈 50% 区域)
    cy, cx = H // 2, W // 2
    Y, X = np.ogrid[:H, :W]
    radius = np.sqrt((X - cx)**2 + (Y - cy)**2)
    max_r = np.sqrt(cx**2 + cy**2)
    high_mask = radius > (max_r * 0.5)
    high_energy_ratio = np.sum(magnitude[high_mask]) / total

    # 特征2: 频谱熵
    norm_mag = magnitude / total
    norm_mag = norm_mag[norm_mag > 0]
    spectral_entropy = -np.sum(norm_mag * np.log2(norm_mag))

    # 特征3: 频谱均值 (weighted mean frequency)
    mean_freq = np.sum(radius * magnitude) / total

    # 特征4: 频谱方差
    var_freq = np.sum((radius - mean_freq)**2 * magnitude) / total

    # 特征5: 低频能量占比 (内圈 25%)
    low_mask = radius < (max_r * 0.25)
    low_energy_ratio = np.sum(magnitude[low_mask]) / total

    # 特征6: 中频能量占比 (25%-50%)
    mid_mask = (radius >= max_r * 0.25) & (radius <= max_r * 0.5)
    mid_energy_ratio = np.sum(magnitude[mid_mask]) / total

    return np.array([high_energy_ratio, spectral_entropy, mean_freq,
                     var_freq, low_energy_ratio, mid_energy_ratio])


# ======================== Warping 函数 ========================

def create_warped_batch(images, noise_grid, identity_grid, opt):
    """对一批图像应用 WaNet warping"""
    bs = images.shape[0]
    grid_temps = (identity_grid + opt.s * noise_grid / opt.input_height) * opt.grid_rescale
    grid_temps = torch.clamp(grid_temps, -1, 1)
    warped = F.grid_sample(images, grid_temps.repeat(bs, 1, 1, 1), align_corners=True)
    return warped


# ======================== 检测器主流程 ========================

def build_dataset(opt, noise_grid, identity_grid, denormalizer, n_samples=500):
    """
    构建 clean vs warped 图像对, 提取频域特征
    返回: X (features), y (0=clean, 1=warped)
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])

    dataset = torchvision.datasets.CIFAR10(opt.data_root, train=False, transform=transform)
    loader = torch.utils.data.DataLoader(dataset, batch_size=128, shuffle=False, num_workers=2)

    X_clean, X_warped = [], []

    print(f"  Processing {n_samples} images...")
    count = 0
    for images, _ in loader:
        if count >= n_samples:
            break

        images = images.to(opt.device)
        warped = create_warped_batch(images, noise_grid, identity_grid, opt)

        # Denormalize to pixel space
        if denormalizer:
            images_pix = denormalizer(images)
            warped_pix = denormalizer(warped)
        else:
            images_pix = images
            warped_pix = warped

        # Convert to numpy [0, 255]
        images_np = (images_pix.cpu().numpy() + 1) / 2 * 255
        warped_np = (warped_pix.cpu().numpy() + 1) / 2 * 255
        images_np = np.clip(images_np, 0, 255)
        warped_np = np.clip(warped_np, 0, 255)

        for i in range(images.shape[0]):
            if count >= n_samples:
                break
            X_clean.append(extract_freq_features(images_np[i]))
            X_warped.append(extract_freq_features(warped_np[i]))
            count += 1

    X = np.vstack([np.array(X_clean), np.array(X_warped)])
    y = np.hstack([np.zeros(len(X_clean)), np.ones(len(X_warped))])

    print(f"  Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"  Clean: {len(X_clean)}, Warped: {len(X_warped)}")
    return X, y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="cifar10")
    parser.add_argument("--data_root", default=os.path.join(REPO_ROOT, "data"))
    parser.add_argument("--checkpoint", default=os.path.join(REPO_ROOT, "checkpoints/ablation_noisemode_with"))
    parser.add_argument("--output_dir", default=os.path.join(REPO_ROOT, "results/freq_detector"))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--n_samples", type=int, default=500)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 加载模型
    opt = get_arguments().parse_args([])
    opt.dataset = args.dataset
    opt.data_root = args.data_root
    opt.device = args.device
    opt.s = 0.5
    opt.k = 4
    opt.grid_rescale = 1.0

    from utils.runtime import populate_dataset_attributes
    opt = populate_dataset_attributes(opt)

    print("=" * 60)
    print(" 频域 Warping 后门检测器")
    print("=" * 60)

    # 加载训练好的模型
    print("\n[1/5] Loading trained WaNet model...")
    ckpt_path = os.path.join(args.checkpoint, opt.dataset, f"{opt.dataset}_all2one_morph.pth.tar")
    state_dict = safe_torch_load(ckpt_path, device=opt.device)

    if opt.dataset == "mnist":
        netC = NetC_MNIST().to(opt.device)
    else:
        netC = PreActResNet18(num_classes=opt.num_classes).to(opt.device)
    netC.load_state_dict(state_dict["netC"])
    netC.eval()

    noise_grid = state_dict["noise_grid"].to(opt.device)
    identity_grid = state_dict["identity_grid"].to(opt.device)
    denormalizer = Denormalizer(opt)
    print(f"  Model loaded. Clean Acc (reported): {state_dict.get('clean_acc', 'N/A')}")

    # 构建频域特征数据集
    print("\n[2/5] Extracting frequency-domain features...")
    X, y = build_dataset(opt, noise_grid, identity_grid, denormalizer, args.n_samples)
    print(f"  Feature range: [{X.min():.4f}, {X.max():.4f}]")

    # 训练/测试分割
    print("\n[3/5] Training SVM detector...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    svm = SVC(kernel='rbf', probability=True, random_state=42)
    svm.fit(X_train_scaled, y_train)

    y_pred = svm.predict(X_test_scaled)
    y_prob = svm.predict_proba(X_test_scaled)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    print(f"\n  Detection Accuracy: {acc*100:.2f}%")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred,
          target_names=['Clean', 'Warped (Backdoor)']))

    # ROC 曲线
    print("\n[4/5] Computing ROC curve...")
    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)

    # 保存结果
    results = {
        "detection_accuracy": float(acc),
        "roc_auc": float(roc_auc),
        "n_samples": args.n_samples,
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
    }
    with open(os.path.join(args.output_dir, "freq_detector_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    # 绘制 ROC 曲线
    print("\n[5/5] Plotting ROC curve...")
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.plot(fpr, tpr, 'b-', linewidth=2.5, label=f'Freq Detector (AUC={roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5, label='Random (AUC=0.500)')

    # 标注 STRIP 检测效果 (来自队友的结果: STRIP 完全无法区分)
    ax.scatter([0.45], [0.55], color='red', s=150, marker='X', zorder=5,
               label='STRIP (AUC≈0.50, fails)')

    ax.set_xlabel('False Positive Rate', fontsize=13)
    ax.set_ylabel('True Positive Rate', fontsize=13)
    ax.set_title('ROC: Frequency-Domain Warping Detector vs STRIP',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "roc_curve.png"), dpi=150)
    plt.close()
    print(f"  ROC curve saved.")

    # 特征可视化
    print("\n  Visualizing feature distributions...")
    feature_names = ['High-Freq Ratio', 'Spectral Entropy', 'Mean Freq',
                     'Var Freq', 'Low-Freq Ratio', 'Mid-Freq Ratio']

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    X_clean_subset = X[y == 0]
    X_warped_subset = X[y == 1]

    for i, (ax, name) in enumerate(zip(axes.flatten(), feature_names)):
        ax.hist(X_clean_subset[:, i], bins=30, alpha=0.5, label='Clean', color='steelblue', density=True)
        ax.hist(X_warped_subset[:, i], bins=30, alpha=0.5, label='Warped', color='crimson', density=True)
        ax.set_title(name, fontsize=12, fontweight='bold')
        ax.set_xlabel('Feature Value')
        ax.set_ylabel('Density')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Frequency-Domain Feature Distributions: Clean vs Warped Images',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "feature_distributions.png"), dpi=150)
    plt.close()
    print("  Feature distributions saved.")

    # FFT 频谱对比图
    print("\n  Generating FFT spectrum comparison...")
    transform = transforms.Compose([transforms.ToTensor()])
    ds = torchvision.datasets.CIFAR10(args.data_root, train=False, transform=transform)
    sample_img, _ = ds[0]
    sample_img = sample_img.unsqueeze(0).to(opt.device)
    sample_warped = create_warped_batch(sample_img, noise_grid, identity_grid, opt)

    if denormalizer:
        sample_pix = denormalizer(sample_img)
        warp_pix = denormalizer(sample_warped)
    else:
        sample_pix = sample_img
        warp_pix = sample_warped

    sample_np = (sample_pix[0].cpu().numpy() + 1) / 2
    warp_np = (warp_pix[0].cpu().numpy() + 1) / 2

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))

    # Row 1: clean image
    img_show = sample_np.transpose(1, 2, 0)
    axes[0, 0].imshow(np.clip(img_show, 0, 1))
    axes[0, 0].set_title('Clean Image', fontsize=13, fontweight='bold')
    axes[0, 0].axis('off')

    # FFT clean
    gray_clean = np.mean(sample_np, axis=0)
    f_clean = fftshift(fft2(gray_clean))
    mag_clean = np.log(np.abs(f_clean) + 1e-8)
    axes[0, 1].imshow(mag_clean, cmap='inferno')
    axes[0, 1].set_title('FFT Spectrum (Clean)', fontsize=13, fontweight='bold')
    axes[0, 1].axis('off')

    # Radial profile clean
    axes[0, 2].set_title('Radial Frequency Profile', fontsize=13, fontweight='bold')

    # Row 2: warped image
    img_show_w = warp_np.transpose(1, 2, 0)
    axes[1, 0].imshow(np.clip(img_show_w, 0, 1))
    axes[1, 0].set_title('Warped Image (Backdoor)', fontsize=13, fontweight='bold')
    axes[1, 0].axis('off')

    # FFT warped
    gray_warp = np.mean(warp_np, axis=0)
    f_warp = fftshift(fft2(gray_warp))
    mag_warp = np.log(np.abs(f_warp) + 1e-8)
    axes[1, 1].imshow(mag_warp, cmap='inferno')
    axes[1, 1].set_title('FFT Spectrum (Warped)', fontsize=13, fontweight='bold')
    axes[1, 1].axis('off')

    # Difference
    mag_diff = np.abs(np.abs(f_warp) - np.abs(f_clean))
    mag_diff_log = np.log(mag_diff + 1e-8)
    axes[1, 2].imshow(mag_diff_log, cmap='hot')
    axes[1, 2].set_title('FFT Difference (Warped - Clean)', fontsize=13, fontweight='bold')
    axes[1, 2].axis('off')

    plt.suptitle('Frequency-Domain Analysis: Warping Leaves Detectable Traces',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "fft_spectrum_comparison.png"), dpi=150)
    plt.close()
    print("  FFT comparison saved.")

    print(f"\n{'='*60}")
    print(f" 频域检测器完成！")
    print(f" 检测准确率: {acc*100:.2f}%")
    print(f" ROC AUC:    {roc_auc:.3f}")
    print(f" vs STRIP:   AUC≈0.50 (完全检测不到)")
    print(f" 结果保存至: {args.output_dir}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
