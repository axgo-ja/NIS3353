from detecting import *
from config import get_argument
import numpy as np
import sys
import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, REPO_ROOT)
from utils.runtime import configure_runtime, populate_dataset_attributes


def create_dir(path_dir):
    os.makedirs(path_dir, exist_ok=True)


def outlier_detection(l1_norm_list, idx_mapping, opt):
    print("-" * 30)
    print("Determining whether model is backdoor")
    consistency_constant = 1.4826
    median = torch.median(l1_norm_list)
    mad = consistency_constant * torch.median(torch.abs(l1_norm_list - median))
    min_mad = torch.abs(torch.min(l1_norm_list) - median) / mad

    print("Median: {}, MAD: {}".format(median, mad))
    print("Anomaly index: {}".format(min_mad))

    if min_mad < 2:
        print("Not a backdoor model")
    else:
        print("This is a backdoor model")

    if opt.to_file:
        output_path = os.path.join(
            opt.result_path, "{}_{}_output.txt".format(opt.attack_mode, opt.dataset)
        )
        with open(output_path, "a+") as f:
            f.write(
                str(median.cpu().numpy()) + ", " + str(mad.cpu().numpy()) + ", " + str(min_mad.cpu().numpy()) + "\n"
            )
            l1_norm_list_to_save = [str(value) for value in l1_norm_list.cpu().numpy()]
            f.write(", ".join(l1_norm_list_to_save) + "\n")

    flag_list = []
    for y_label in idx_mapping:
        if l1_norm_list[idx_mapping[y_label]] > median:
            continue
        if torch.abs(l1_norm_list[idx_mapping[y_label]] - median) / mad > 2:
            flag_list.append((y_label, l1_norm_list[idx_mapping[y_label]]))

    if len(flag_list) > 0:
        flag_list = sorted(flag_list, key=lambda x: x[1])

    print(
        "Flagged label list: {}".format(",".join(["{}: {}".format(y_label, l_norm) for y_label, l_norm in flag_list]))
    )


def main():

    opt = configure_runtime(populate_dataset_attributes(get_argument().parse_args()))
    opt.total_label = opt.num_classes

    result_path = os.path.join(opt.result, opt.dataset, opt.attack_mode)
    create_dir(result_path)
    opt.result_path = result_path
    opt.summary_output_path = os.path.join(result_path, "{}_{}_output.txt".format(opt.attack_mode, opt.dataset))
    opt.output_path = os.path.join(result_path, "{}_{}_output_clean.txt".format(opt.attack_mode, opt.dataset))
    if opt.to_file:
        with open(opt.summary_output_path, "w+") as f:
            f.write("")
        with open(opt.output_path, "w+") as f:
            f.write("Output for cleanse:  - {}".format(opt.attack_mode, opt.dataset) + "\n")

    init_mask = np.ones((1, opt.input_height, opt.input_width)).astype(np.float32)
    init_pattern = np.ones((opt.input_channel, opt.input_height, opt.input_width)).astype(np.float32)

    for test in range(opt.n_times_test):
        print("Test {}:".format(test))
        if opt.to_file:
            with open(opt.output_path, "a+") as f:
                f.write("-" * 30 + "\n")
                f.write("Test {}:".format(str(test)) + "\n")

        masks = []
        idx_mapping = {}

        for target_label in range(opt.total_label):
            print("----------------- Analyzing label: {} -----------------".format(target_label))
            opt.target_label = target_label
            recorder, opt = train(opt, init_mask, init_pattern)

            mask = recorder.mask_best
            masks.append(mask)
            idx_mapping[target_label] = len(masks) - 1

        l1_norm_list = torch.stack([torch.norm(m, p=opt.use_norm) for m in masks])
        print("{} labels found".format(len(l1_norm_list)))
        print("Norm values: {}".format(l1_norm_list))
        outlier_detection(l1_norm_list, idx_mapping, opt)


if __name__ == "__main__":
    main()
