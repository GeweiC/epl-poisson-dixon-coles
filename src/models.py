"""Baseline Poisson and (weighted) Dixon-Coles football score models.

Scoring intensities follow the original undergraduate dissertation:
    home_lambda = exp(attack_home - defence_away + home_advantage)
    away_mu     = exp(attack_away - defence_home)

Attack parameters are identified by the sum-to-zero constraint.
Likelihood values omit the (parameter-independent) log-factorial terms.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass
class MatchData:
    home: np.ndarray
    away: np.ndarray
    home_goals: np.ndarray
    away_goals: np.ndarray
    days_from_latest: np.ndarray
    teams: list[str]

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> "MatchData":
        required = {"home_team", "away_team", "home_goals", "away_goals", "days_from_latest"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        teams = sorted(set(frame["home_team"]).union(frame["away_team"]))
        lookup = {team: index for index, team in enumerate(teams)}
        return cls(
            home=frame["home_team"].map(lookup).to_numpy(dtype=int),
            away=frame["away_team"].map(lookup).to_numpy(dtype=int),
            home_goals=frame["home_goals"].to_numpy(dtype=int),
            away_goals=frame["away_goals"].to_numpy(dtype=int),
            days_from_latest=frame["days_from_latest"].to_numpy(dtype=float),
            teams=teams,
        )


@dataclass
class FittedModel:
    name: str
    params: np.ndarray
    reduced_nll: float
    home_advantage: float
    rho: float | None
    success: bool
    message: str
    iterations: int
    effective_parameters: int
    teams: list[str]

    def table(self, measure: str) -> pd.DataFrame:
        if measure not in {"attack", "defence"}:
            raise ValueError("measure must be attack or defence")
        size = len(self.teams)
        strengths = self.params[:size] if measure == "attack" else self.params[size:2 * size]
        return pd.DataFrame({"team": self.teams, measure: strengths}).sort_values(
            measure, ascending=False
        ).reset_index(drop=True)


def tau_correction(x, y, home_lambda, away_mu, rho):
    """Return the Dixon-Coles adjustment for observed goal counts."""
    x, y, home_lambda, away_mu = np.broadcast_arrays(x, y, home_lambda, away_mu)
    tau = np.ones_like(home_lambda, dtype=float)
    masks = {
        "00": (x == 0) & (y == 0),
        "01": (x == 0) & (y == 1),
        "10": (x == 1) & (y == 0),
        "11": (x == 1) & (y == 1),
    }
    tau[masks["00"]] = 1 - home_lambda[masks["00"]] * away_mu[masks["00"]] * rho
    tau[masks["01"]] = 1 + home_lambda[masks["01"]] * rho
    tau[masks["10"]] = 1 + away_mu[masks["10"]] * rho
    tau[masks["11"]] = 1 - rho
    return tau


def reduced_nll(params, data: MatchData, model: str, xi: float = 0.001):
    """Compute negative (weighted) log likelihood up to common factorial constants."""
    n = len(data.teams)
    attack, defence = params[:n], params[n:2 * n]
    home_adv = params[2 * n]
    log_home = attack[data.home] - defence[data.away] + home_adv
    log_away = attack[data.away] - defence[data.home]
    # Guard numerical optimisation against overflow; no effect near the optimum.
    if np.any(np.abs(log_home) > 20) or np.any(np.abs(log_away) > 20):
        return 1e12
    with np.errstate(over="ignore", invalid="ignore"):
        home_lambda, away_mu = np.exp(log_home), np.exp(log_away)
        contributions = (data.home_goals * log_home - home_lambda
                         + data.away_goals * log_away - away_mu)
        if model in {"dc", "weighted_dc"}:
            tau = tau_correction(data.home_goals, data.away_goals,
                                 home_lambda, away_mu, params[-1])
            if np.any(tau <= 0) or not np.all(np.isfinite(tau)):
                return 1e12
            contributions = contributions + np.log(tau)
        if model == "weighted_dc":
            contributions = contributions * np.exp(-xi * data.days_from_latest)
    value = -float(np.sum(contributions))
    return value if np.isfinite(value) else 1e12


def fit_model(data: MatchData, model: str, xi: float = 0.001) -> FittedModel:
    if model not in {"baseline", "dc", "weighted_dc"}:
        raise ValueError("model must be baseline, dc or weighted_dc")
    if xi < 0:
        raise ValueError("xi must be non-negative")
    n = len(data.teams)
    has_rho = model != "baseline"
    initial_params = np.zeros(2 * n + 1 + int(has_rho))
    constraints = [{"type": "eq", "fun": lambda p: np.sum(p[:n])}]
    bounds = ([(None, None)] * (2 * n + 1) + [(-0.2, 0.2)]) if has_rho else None
    result = minimize(
        reduced_nll,
        initial_params,
        args=(data, model, xi),
        method="SLSQP",
        constraints=constraints,
        bounds=bounds,
        options={"maxiter": 2000, "ftol": 1e-9},
    )
    return FittedModel(
        name=model,
        params=result.x,
        reduced_nll=float(result.fun),
        home_advantage=float(result.x[2 * n]),
        rho=float(result.x[-1]) if has_rho else None,
        success=bool(result.success),
        message=str(result.message),
        iterations=int(result.nit),
        effective_parameters=2 * n + int(has_rho),  # sum(attack) = 0
        teams=data.teams,
    )
