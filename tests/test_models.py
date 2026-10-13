"""Small tests that run without the proprietary/source EPL season CSV files."""

import unittest
import numpy as np
import pandas as pd
from src.models import MatchData, reduced_nll, tau_correction


class ModelTests(unittest.TestCase):
    def test_tau_correction(self):
        x = np.array([0, 0, 1, 1, 2])
        y = np.array([0, 1, 0, 1, 2])
        a = np.full(5, 1.2)
        b = np.full(5, 0.8)
        result = tau_correction(x, y, a, b, -0.1)
        np.testing.assert_allclose(result, [1.096, 0.88, 0.92, 1.1, 1.0])

    def test_rho_zero_recovers_baseline(self):
        frame = pd.DataFrame({
            "home_team": ["Team A", "Team B"],
            "away_team": ["Team B", "Team A"],
            "home_goals": [1, 0],
            "away_goals": [0, 1],
            "days_from_latest": [5, 0],
        })
        data = MatchData.from_frame(frame)
        base = np.zeros(2 * len(data.teams) + 1)
        dc = np.r_[base, 0.0]
        self.assertAlmostEqual(reduced_nll(base, data, "baseline"),
                               reduced_nll(dc, data, "dc"))
        self.assertAlmostEqual(reduced_nll(dc, data, "dc"),
                               reduced_nll(dc, data, "weighted_dc", xi=0))


if __name__ == "__main__":
    unittest.main()
