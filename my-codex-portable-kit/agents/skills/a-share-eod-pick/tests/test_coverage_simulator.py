import importlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class CoverageSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.coverage_simulator = importlib.import_module("coverage_simulator")

    def test_simulate_targets_selects_highest_score_days_to_reach_coverage(self):
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "score": 90,
                        "factor_scores": {"score": 90},
                        "return": 0.01,
                    }
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "score": 70,
                        "factor_scores": {"score": 70},
                        "return": -0.02,
                    }
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "score": 80,
                        "factor_scores": {"score": 80},
                        "return": 0.03,
                    }
                ],
            },
            {
                "date": "2026-06-04",
                "candidate_pool": [
                    {
                        "symbol": "600004",
                        "score": 60,
                        "factor_scores": {"score": 60},
                        "return": -0.01,
                    }
                ],
            },
        ]
        config = {
            "factors": {},
            "selection": {"score_threshold": 0, "min_factor_scores": {}, "max_factor_scores": {}},
        }

        result = self.coverage_simulator.simulate_targets(samples, config, targets=[0.5])

        tier = result["targets"][0]
        self.assertEqual(tier["target_coverage"], 0.5)
        self.assertEqual(tier["trade_samples"], 2)
        self.assertEqual(tier["actual_coverage"], 0.5)
        self.assertEqual(tier["win_rate"], 1.0)
        self.assertEqual([p["symbol"] for p in tier["picks"]], ["600001", "600003"])

    def test_simulate_targets_reports_profit_loss_ratio_and_drawdown(self):
        samples = [
            {
                "date": f"2026-06-0{i}",
                "candidate_pool": [
                    {
                        "symbol": f"60000{i}",
                        "score": 100 - i,
                        "factor_scores": {"score": 100 - i},
                        "return": ret,
                    }
                ],
            }
            for i, ret in enumerate([0.02, -0.01, -0.03, 0.01], start=1)
        ]
        config = {
            "factors": {},
            "selection": {"score_threshold": 0, "min_factor_scores": {}, "max_factor_scores": {}},
        }

        result = self.coverage_simulator.simulate_targets(samples, config, targets=[1.0])

        tier = result["targets"][0]
        self.assertEqual(tier["trade_samples"], 4)
        self.assertEqual(tier["win_rate"], 0.5)
        self.assertEqual(tier["profit_loss_ratio"], 0.75)
        self.assertEqual(tier["max_consecutive_loss"], 2)


if __name__ == "__main__":
    unittest.main()
