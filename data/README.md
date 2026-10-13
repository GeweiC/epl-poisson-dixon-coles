# Data provenance and setup

The original project analysed six completed English Premier League seasons (2018/19–2023/24), using match results sourced from **football-data.co.uk**, as credited in the dissertation.

Raw season files are intentionally **not redistributed in this public-repository draft**, pending confirmation of the source's permissions to redistribute historical CSVs. Download the appropriate match result files directly from the provider under its current terms, or use your own legally obtained copies.

Put these CSVs into `data/raw/` using the following names:

- `epl_1819.csv`
- `epl_1920.csv`
- `epl_2021.csv` (2020/21 season)
- `epl_2122.csv`
- `epl_2223.csv`
- `epl_2324.csv`

The script reads `Date`, `HomeTeam`, `AwayTeam`, `FTHG`, and `FTAG` from each CSV. Running `python scripts/prepare_data.py` creates `data/processed/epl_model_ready.csv` with team indices and days since the latest fixture. Both the raw and model-ready CSVs are ignored by Git by default.

Expected validation: **2,280 matches, 28 distinct teams, 2018-08-10 to 2024-05-19**. Results depend on keeping the same underlying source data and team naming conventions.
