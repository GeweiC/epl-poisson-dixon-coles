"""Build publication-friendly figures from saved model parameter tables."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def comparison(results: Path, figures: Path, quantity: str, left: str, right: str,
               number: int = 10):
    first = pd.read_csv(results / f"{quantity}_table_{left}.csv")
    second = pd.read_csv(results / f"{quantity}_table_{right}.csv")
    common = first.head(number)["team"].tolist()
    lookup1 = first.set_index("team")[quantity]
    lookup2 = second.set_index("team")[quantity]
    x = np.arange(len(common))
    width = 0.36
    fig, ax = plt.subplots(figsize=(11, 5.5))
    labels = {"baseline": "Baseline Poisson", "dc": "Dixon–Coles",
              "weighted_dc": "Weighted Dixon–Coles"}
    ax.bar(x - width / 2, lookup1.loc[common], width, label=labels[left])
    ax.bar(x + width / 2, lookup2.loc[common], width, label=labels[right])
    ax.set_xticks(x, common, rotation=35, ha="right")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_ylabel(f"Estimated {quantity} strength")
    ax.set_title(f"{quantity.title()} strengths: {labels[left]} vs {labels[right]}\n"
                 f"Top {number} teams ranked by {labels[left]} estimate")
    ax.legend()
    fig.tight_layout()
    destination = figures / f"{quantity}_{left}_vs_{right}.png"
    fig.savefig(destination, dpi=170)
    plt.close(fig)
    return destination


def time_decay(figures: Path, days: int = 2109):
    t = np.arange(days + 1)
    fig, ax = plt.subplots(figsize=(9, 4.7))
    for xi in (0.0005, 0.001, 0.002):
        ax.plot(t, np.exp(-xi * t), label=f"xi = {xi}")
    ax.set_xlabel("Days before latest match")
    ax.set_ylabel("Time-decay weight")
    ax.set_title("Exponential discounting of historical matches")
    ax.legend()
    fig.tight_layout()
    dest = figures / "exponential_time_decay.png"
    fig.savefig(dest, dpi=170)
    plt.close(fig)
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--figures", type=Path, default=Path("figures"))
    args = parser.parse_args()
    args.figures.mkdir(parents=True, exist_ok=True)
    for quantity in ("attack", "defence"):
        for left, right in (("baseline", "dc"), ("dc", "weighted_dc")):
            path = comparison(args.results, args.figures, quantity, left, right)
            print("Wrote", path)
    print("Wrote", time_decay(args.figures))


if __name__ == "__main__":
    main()
