import argparse
import os


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def get_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_root", type=str, default=os.path.join(REPO_ROOT, "data"))
    parser.add_argument("--checkpoints", type=str, default=os.path.join(REPO_ROOT, "checkpoints"))
    parser.add_argument("--temps", type=str, default=os.path.join(REPO_ROOT, "defenses", "fine_pruning", "temps"))
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--deterministic", action="store_true")

    parser.add_argument("--dataset", type=str, default="celeba")
    parser.add_argument("--input_height", type=int, default=None)
    parser.add_argument("--input_width", type=int, default=None)
    parser.add_argument("--input_channel", type=int, default=None)
    parser.add_argument("--num_classes", type=int, default=10)

    parser.add_argument("--bs", type=int, default=100)
    parser.add_argument("--num_workers", type=int, default=2)

    parser.add_argument("--attack_mode", type=str, default="all2one", help="all2one or all2all")
    parser.add_argument("--target_label", type=int, default=0)
    parser.add_argument("--outfile", type=str, default=os.path.join(REPO_ROOT, "defenses", "fine_pruning", "results.txt"))
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--s", type=float, default=0.5)
    parser.add_argument("--grid_rescale", type=float, default=1)

    return parser
