import random

import numpy as np
import torch
import torch.nn.functional as F


DATASET_CONFIGS = {
    "cifar10": {"num_classes": 10, "input_height": 32, "input_width": 32, "input_channel": 3},
    "gtsrb": {"num_classes": 43, "input_height": 32, "input_width": 32, "input_channel": 3},
    "mnist": {"num_classes": 10, "input_height": 28, "input_width": 28, "input_channel": 1},
    "celeba": {"num_classes": 8, "input_height": 64, "input_width": 64, "input_channel": 3},
}


def populate_dataset_attributes(opt):
    try:
        dataset_config = DATASET_CONFIGS[opt.dataset]
    except KeyError as exc:
        raise Exception("Invalid Dataset") from exc

    for key, value in dataset_config.items():
        setattr(opt, key, value)
    return opt


def configure_runtime(opt):
    opt.num_workers = int(opt.num_workers)
    if opt.device == "cuda" and not torch.cuda.is_available():
        opt.device = "cpu"

    seed = getattr(opt, "seed", None)
    deterministic = bool(getattr(opt, "deterministic", False))
    if seed is not None:
        set_seed(seed, deterministic)
    elif deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    return opt


def set_seed(seed, deterministic=False):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = deterministic
    torch.backends.cudnn.benchmark = not deterministic


def safe_torch_load(path, device=None):
    kwargs = {}
    if device is not None:
        kwargs["map_location"] = device
    try:
        return torch.load(path, weights_only=False, **kwargs)
    except TypeError:
        return torch.load(path, **kwargs)


def build_warp_grids(opt):
    ins = torch.rand(1, 2, opt.k, opt.k) * 2 - 1
    ins = ins / torch.mean(torch.abs(ins))
    noise_grid = F.interpolate(ins, size=opt.input_height, mode="bicubic", align_corners=True)
    noise_grid = noise_grid.permute(0, 2, 3, 1).to(opt.device)

    array1d = torch.linspace(-1, 1, steps=opt.input_height)
    grid_y, grid_x = torch.meshgrid(array1d, array1d, indexing="ij")
    identity_grid = torch.stack((grid_x, grid_y), dim=2)[None, ...].to(opt.device)
    return noise_grid, identity_grid
