"""Fit the three dissertation models and export comparisons and parameter tables.

Run from repository root: python scripts/run_analysis.py
"""

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.models import MatchData, fit_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/epl_model_ready.csv"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--xi", type=float, default=0.001)
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    data = MatchData.from_frame(frame)
    print(f"Loaded {len(frame)} matches, {len(data.teams)} teams")
    args.output.mkdir(parents=True, exist_ok=True)
    fits = {}
    for model in ("baseline", "dc", "weighted_dc"):
        fit = fit_model(data, model, xi=args.xi)
        if not fit.success:
            raise RuntimeError(f"{model} did not converge: {fit.message}")
        fits[model] = fit
        print(f"{model}: reduced NLL={fit.reduced_nll:.6f}, h={fit.home_advantage:.6f}, "
              f"rho={fit.rho}, iterations={fit.iterations}")
        for category in ("attack", "defence"):
            fit.table(category).to_csv(args.output / f"{category}_table_{model}.csv", index=False)

    baseline, dc, weighted = (fits[key] for key in ("baseline", "dc", "weighted_dc"))
    lr_stat = 2 * (baseline.reduced_nll - dc.reduced_nll)
    print(f"LRT baseline vs DC: chi-square(1)={lr_stat:.6f}, p={chi2.sf(lr_stat, 1):.6f}")
    rows = []
    for fit in (baseline, dc, weighted):
        rows.append({
            "model": fit.name,
            "reduced_nll": fit.reduced_nll,
            "home_advantage": fit.home_advantage,
            "rho": fit.rho if fit.rho is not None else np.nan,
            "relative_aic_without_constant": (
                2 * fit.effective_parameters + 2 * fit.reduced_nll
                if fit.name != "weighted_dc" else np.nan
            ),
            "iterations": fit.iterations,
        })
    pd.DataFrame(rows).to_csv(args.output / "model_comparison.csv", index=False)
    print("NOTE: Weighted NLL is NOT comparable to unweighted NLL.")
    print("NOTE: AIC in table omits common log-factorial terms; only differences are meaningful.")


if __name__ == "__main__":
    main()
