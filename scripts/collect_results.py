#!/usr/bin/env python
# =============================================================================
# 结果收集与汇总脚本
# 扫描 results/ 目录下的所有 JSON/CSV 结果，生成最终汇总表
# =============================================================================
import os
import sys
import json
import argparse
import csv
from collections import defaultdict


def collect_results(results_dir):
    """收集所有实验结果到一个结构化字典"""
    summary = {
        "ablation_noise_mode": {},
        "ablation_s": {},
        "ablation_k": {},
        "multiseed": {},
        "celeba": {},
        "perceptual": {},
    }

    # --- Noise Mode 消融 ---
    for mode in ["with", "without"]:
        path = os.path.join(results_dir, f"ablation_noisemode_{mode}.json")
        if os.path.exists(path):
            with open(path) as f:
                summary["ablation_noise_mode"][f"noise_{mode}"] = json.load(f)

    # --- s 消融 ---
    for s in [0.25, 0.5, 0.75, 1.0]:
        path = os.path.join(results_dir, f"ablation_s_{s}.json")
        if os.path.exists(path):
            with open(path) as f:
                summary["ablation_s"][f"s_{s}"] = json.load(f)

    # --- k 消融 ---
    for k in [2, 4, 6, 8]:
        path = os.path.join(results_dir, f"ablation_k_{k}.json")
        if os.path.exists(path):
            with open(path) as f:
                summary["ablation_k"][f"k_{k}"] = json.load(f)

    # --- 多种子 ---
    multiseed_data = {"clean_acc": [], "bd_acc": [], "cross_acc": []}
    for seed in range(5):
        path = os.path.join(results_dir, f"multiseed_{seed}.json")
        if os.path.exists(path):
            with open(path) as f:
                r = json.load(f)
            multiseed_data["clean_acc"].append(r["clean_acc"])
            multiseed_data["bd_acc"].append(r["bd_acc"])
            multiseed_data["cross_acc"].append(r.get("cross_acc", 0))
    if multiseed_data["clean_acc"]:
        import numpy as np
        summary["multiseed"] = {
            "seeds": list(range(len(multiseed_data["clean_acc"]))),
            "clean_mean": float(np.mean(multiseed_data["clean_acc"])),
            "clean_std": float(np.std(multiseed_data["clean_acc"])),
            "bd_mean": float(np.mean(multiseed_data["bd_acc"])),
            "bd_std": float(np.std(multiseed_data["bd_acc"])),
            "cross_mean": float(np.mean(multiseed_data["cross_acc"])),
            "cross_std": float(np.std(multiseed_data["cross_acc"])),
        }

    # --- CelebA ---
    for mode in ["all2one", "all2all"]:
        path = os.path.join(results_dir, f"celeba_{mode}.json")
        if os.path.exists(path):
            with open(path) as f:
                summary["celeba"][mode] = json.load(f)

    # --- 感知质量 ---
    for ds in ["cifar10", "mnist", "gtsrb"]:
        vis_dir = os.path.join(results_dir, "visualization", ds)
        stats_path = os.path.join(vis_dir, "perceptual_metrics.json")
        if os.path.exists(stats_path):
            with open(stats_path) as f:
                summary["perceptual"][ds] = json.load(f)

    return summary


def print_summary_table(summary):
    """打印人类可读的汇总表"""
    print("\n" + "=" * 80)
    print("  WaNet 成员2 - 实验最终汇总")
    print("=" * 80)

    # --- 消融实验: s ---
    if summary["ablation_s"]:
        print("\n--- 消融实验: Warping Strength (s) ---")
        print(f"{'s':<10} {'Clean Acc':<15} {'Attack Acc':<15} {'Cross Acc':<15}")
        print("-" * 55)
        for key in sorted(summary["ablation_s"].keys(), key=lambda x: float(x.split("_")[1])):
            r = summary["ablation_s"][key]
            print(f"{key:<10} {r['clean_acc']:<15.2f} {r['bd_acc']:<15.2f} {r['cross_acc']:<15.2f}")

    # --- 消融实验: k ---
    if summary["ablation_k"]:
        print("\n--- 消融实验: Grid Size (k) ---")
        print(f"{'k':<10} {'Clean Acc':<15} {'Attack Acc':<15} {'Cross Acc':<15}")
        print("-" * 55)
        for key in sorted(summary["ablation_k"].keys(), key=lambda x: int(x.split("_")[1])):
            r = summary["ablation_k"][key]
            print(f"{key:<10} {r['clean_acc']:<15.2f} {r['bd_acc']:<15.2f} {r['cross_acc']:<15.2f}")

    # --- Noise Mode 消融 ---
    if summary["ablation_noise_mode"]:
        print("\n--- 消融实验: Noise Mode ---")
        print(f"{'Mode':<20} {'Clean Acc':<15} {'Attack Acc':<15} {'Cross Acc':<15}")
        print("-" * 65)
        for key, r in summary["ablation_noise_mode"].items():
            cross = r.get("cross_acc", 0) if isinstance(r.get("cross_acc"), (int, float)) else 0
            print(f"{key:<20} {r['clean_acc']:<15.2f} {r['bd_acc']:<15.2f} {cross:<15.2f}")

    # --- 多种子 ---
    if summary["multiseed"]:
        ms = summary["multiseed"]
        print(f"\n--- 多随机种子 (CIFAR-10 all2one, {ms.get('seeds', [])} seeds) ---")
        print(f"  Clean  Acc: {ms['clean_mean']:.2f} ± {ms['clean_std']:.2f}")
        print(f"  Attack Acc: {ms['bd_mean']:.2f} ± {ms['bd_std']:.2f}")
        print(f"  Cross  Acc: {ms['cross_mean']:.2f} ± {ms['cross_std']:.2f}")

    # --- CelebA ---
    if summary["celeba"]:
        print("\n--- CelebA 实验结果 ---")
        for mode, r in summary["celeba"].items():
            print(f"  {mode}: Clean={r['clean_acc']:.2f}, Attack={r['bd_acc']:.2f}, Cross={r.get('cross_acc', 0):.2f}")

    # --- 感知质量 ---
    if summary["perceptual"]:
        print("\n--- 感知质量 (PSNR/SSIM) ---")
        print(f"{'Dataset':<12} {'PSNR (dB)':<20} {'SSIM':<20}")
        print("-" * 52)
        for ds, stats in summary["perceptual"].items():
            print(f"{ds:<12} {stats['psnr_mean']:.2f} ± {stats['psnr_std']:.2f}     {stats['ssim_mean']:.4f} ± {stats['ssim_std']:.4f}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Collect and summarize WaNet experiment results")
    parser.add_argument("--results_dir", type=str, required=True)
    parser.add_argument("--output", type=str, default="final_summary.json")
    args = parser.parse_args()

    summary = collect_results(args.results_dir)

    # 保存 JSON 汇总
    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n[OK] Summary saved to: {args.output}")

    # 打印汇总表
    print_summary_table(summary)


if __name__ == "__main__":
    main()
