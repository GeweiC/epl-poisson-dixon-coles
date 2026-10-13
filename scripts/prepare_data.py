"""Combine the six raw EPL season CSVs into the original model-ready format.

Run from the repository root: python scripts/prepare_data.py
Raw data is not redistributed; see data/README.md for provenance.
"""

import argparse
from pathlib import Path

import pandas as pd

SEASON_FILES = ["epl_1819.csv", "epl_1920.csv", "epl_2021.csv",
                "epl_2122.csv", "epl_2223.csv", "epl_2324.csv"]


def prepare(input_directory: Path, output_file: Path) -> pd.DataFrame:
    required = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]
    frames = []
    for filename in SEASON_FILES:
        source = input_directory / filename
        if not source.exists():
            raise FileNotFoundError(f"Missing {source}. See data/README.md")
        raw = pd.read_csv(source)
        if not set(required).issubset(raw.columns):
            raise ValueError(f"Missing required columns in {filename}")
        df = raw[required].copy()
        df.columns = ["date", "home_team", "away_team", "home_goals", "away_goals"]
        df["season"] = filename.removeprefix("epl_").removesuffix(".csv")
        frames.append(df)

    full = pd.concat(frames, ignore_index=True)
    full["date"] = pd.to_datetime(full["date"], dayfirst=True, errors="raise")
    full["home_goals"] = pd.to_numeric(full["home_goals"], errors="raise")
    full["away_goals"] = pd.to_numeric(full["away_goals"], errors="raise")
    if full.isna().any().any():
        raise ValueError("Missing values found in modelling data")
    if full.duplicated(["date", "home_team", "away_team"]).any():
        raise ValueError("Duplicate fixtures found")
    full = full.sort_values("date", kind="stable").reset_index(drop=True)
    teams = sorted(set(full["home_team"]).union(full["away_team"]))
    team_map = {team: idx for idx, team in enumerate(teams)}
    full["home_idx"] = full["home_team"].map(team_map)
    full["away_idx"] = full["away_team"].map(team_map)
    full["days_from_latest"] = (full["date"].max() - full["date"]).dt.days
    output_file.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(output_file, index=False)
    print(f"Saved {len(full):,} fixtures, {len(teams)} teams to {output_file}")
    return full


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/epl_model_ready.csv"))
    args = parser.parse_args()
    prepare(args.raw_dir, args.output)
