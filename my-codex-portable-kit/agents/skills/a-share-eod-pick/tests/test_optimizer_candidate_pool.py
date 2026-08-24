import importlib
import json
import types
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class OptimizerCandidatePoolTests(unittest.TestCase):
    def setUp(self):
        self.optimizer = importlib.import_module("optimizer")

    def test_backtest_with_weights_reselects_daily_top1_from_candidate_pool(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.1},
                "F2_volume_price_sync": {"weight": 0.4},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F5_sector_heat": {"weight": 0.05},
                "F6_news_catalyst": {"weight": 0.05},
                "F7_float_mv_fit": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 80, "F4_tail_rally_strength": 80},
                "max_factor_scores": {"F7_float_mv_fit": 70},
            },
        }
        samples = [
            {
                "date": "2026-06-24",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 70,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 70,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 90,
                        },
                        "return": -0.03,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 85,
                            "F3_technical_pattern": 70,
                            "F4_tail_rally_strength": 90,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 60,
                        },
                        "return": 0.02,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_candidate_pool(samples, config)

        self.assertEqual(result["trade_samples"], 1)
        self.assertEqual(result["win_rate"], 1.0)
        self.assertEqual(result["picks"][0]["symbol"], "600002")

    def test_rejects_candidate_pool_change_when_win_rate_flat_and_risk_worse(self):
        old_bt = {
            "samples": 30,
            "trade_samples": 30,
            "empty_days": 0,
            "win_rate": 0.3333,
            "avg_return": -0.0083,
            "max_consecutive_loss": 4,
        }
        new_bt = {
            "samples": 30,
            "trade_samples": 27,
            "empty_days": 3,
            "win_rate": 0.3333,
            "avg_return": -0.0093,
            "max_consecutive_loss": 8,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertFalse(accepted)
        self.assertIn("未真实改善", reason)
        self.assertIn("最大连亏", reason)

    def test_rejects_candidate_pool_change_when_total_win_rate_drops(self):
        old_bt = {
            "samples": 160,
            "trade_samples": 130,
            "empty_days": 30,
            "win_rate": 0.2923,
            "avg_return": -0.0083,
            "max_consecutive_loss": 7,
        }
        new_bt = {
            "samples": 160,
            "trade_samples": 131,
            "empty_days": 29,
            "win_rate": 0.2901,
            "avg_return": -0.0079,
            "max_consecutive_loss": 7,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertFalse(accepted)
        self.assertIn("胜率下降", reason)

    def test_rejects_tiny_winrate_gain_when_participation_is_already_too_low(self):
        old_bt = {
            "samples": 260,
            "trade_samples": 48,
            "empty_days": 212,
            "win_rate": 0.5,
            "avg_return": 0.0025,
            "max_consecutive_loss": 4,
        }
        new_bt = {
            "samples": 260,
            "trade_samples": 41,
            "empty_days": 219,
            "win_rate": 0.5122,
            "avg_return": 0.0035,
            "max_consecutive_loss": 4,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertFalse(accepted)
        self.assertIn("出手率已低", reason)

    def test_accepts_high_confidence_filter_with_enough_trades_despite_more_empty_days(self):
        old_bt = {
            "samples": 260,
            "trade_samples": 219,
            "empty_days": 41,
            "win_rate": 0.3014,
            "avg_return": -0.0068,
            "max_consecutive_loss": 10,
        }
        new_bt = {
            "samples": 260,
            "trade_samples": 112,
            "empty_days": 148,
            "win_rate": 0.4107,
            "avg_return": -0.0003,
            "max_consecutive_loss": 6,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertTrue(accepted)
        self.assertIn("空仓", reason)

    def test_accepts_high_confidence_filter_scaled_to_validation_segment_size(self):
        old_bt = {
            "samples": 78,
            "trade_samples": 64,
            "empty_days": 14,
            "win_rate": 0.3125,
            "avg_return": -0.0097,
            "max_consecutive_loss": 6,
        }
        new_bt = {
            "samples": 78,
            "trade_samples": 33,
            "empty_days": 45,
            "win_rate": 0.4242,
            "avg_return": -0.0004,
            "max_consecutive_loss": 6,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertTrue(accepted)
        self.assertIn("高置信过滤", reason)

    def test_accepts_candidate_pool_change_when_return_improves_without_more_risk(self):
        old_bt = {
            "samples": 30,
            "trade_samples": 30,
            "empty_days": 0,
            "win_rate": 0.3333,
            "avg_return": -0.0083,
            "max_consecutive_loss": 4,
        }
        new_bt = {
            "samples": 30,
            "trade_samples": 29,
            "empty_days": 1,
            "win_rate": 0.3793,
            "avg_return": -0.0021,
            "max_consecutive_loss": 4,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertTrue(accepted)
        self.assertIn("胜率", reason)
        self.assertIn("平均收益", reason)

    def test_backtest_candidate_pool_includes_regret_metrics(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-24",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {"F1_tail_fund_inflow": 90},
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 80},
                        "return": 0.05,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_candidate_pool(samples, config)

        self.assertEqual(result["avg_regret"], 0.04)
        self.assertEqual(result["total_regret"], 0.04)
        self.assertEqual(result["exact_best_hit_rate"], 0.0)
        self.assertEqual(result["top3_hit_rate"], 1.0)
        self.assertEqual(result["avg_oracle_return"], 0.05)

    def test_compact_backtest_preserves_regret_metrics_for_version_logs(self):
        compact = self.optimizer._compact_backtest({
            "samples": 30,
            "trade_samples": 20,
            "win_rate": 0.7,
            "avg_regret": 0.018,
            "total_regret": 0.54,
            "exact_best_hit_rate": 0.1,
            "top3_hit_rate": 0.3,
            "avg_oracle_return": 0.025,
            "picks": [{"symbol": "600001"}],
        })

        self.assertEqual(compact["avg_regret"], 0.018)
        self.assertEqual(compact["total_regret"], 0.54)
        self.assertEqual(compact["exact_best_hit_rate"], 0.1)
        self.assertEqual(compact["top3_hit_rate"], 0.3)
        self.assertEqual(compact["avg_oracle_return"], 0.025)
        self.assertNotIn("picks", compact)

    def test_evaluate_candidate_accepts_regret_reduction_when_risk_not_worse(self):
        old_bt = {
            "samples": 30,
            "trade_samples": 30,
            "empty_days": 0,
            "win_rate": 0.7,
            "avg_return": 0.004,
            "total_return": 0.12,
            "max_consecutive_loss": 2,
            "avg_regret": 0.025,
            "exact_best_hit_rate": 0.03,
        }
        new_bt = {
            "samples": 30,
            "trade_samples": 30,
            "empty_days": 0,
            "win_rate": 0.7,
            "avg_return": 0.004,
            "total_return": 0.12,
            "max_consecutive_loss": 2,
            "avg_regret": 0.018,
            "exact_best_hit_rate": 0.1,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertTrue(accepted)
        self.assertIn("机会损失", reason)
        self.assertIn("最优命中", reason)

    def test_evaluate_candidate_accepts_top3_hit_improvement_with_regret_reduction(self):
        old_bt = {
            "samples": 30,
            "trade_samples": 30,
            "empty_days": 0,
            "win_rate": 0.78,
            "avg_return": 0.006,
            "total_return": 0.18,
            "max_consecutive_loss": 2,
            "avg_regret": 0.025,
            "exact_best_hit_rate": 0.03,
            "top3_hit_rate": 0.20,
        }
        new_bt = {
            "samples": 30,
            "trade_samples": 30,
            "empty_days": 0,
            "win_rate": 0.77,
            "avg_return": 0.006,
            "total_return": 0.18,
            "max_consecutive_loss": 2,
            "avg_regret": 0.022,
            "exact_best_hit_rate": 0.03,
            "top3_hit_rate": 0.30,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertTrue(accepted)
        self.assertIn("Top3命中", reason)

    def test_candidate_cycle_prioritizes_lower_regret_and_best_hit_when_accepted(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
            "optimization": {},
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {"F1_tail_fund_inflow": 100, "F2_volume_price_sync": 0},
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 0, "F2_volume_price_sync": 100},
                        "return": 0.05,
                    },
                ],
            }
        ] * 5

        with mock.patch.object(self.optimizer, "_candidate_configs", return_value=[
            (
                "profit_only",
                {
                    **config,
                    "factors": {
                        "F1_tail_fund_inflow": {"weight": 1.0},
                        "F2_volume_price_sync": {"weight": 0.0},
                    },
                },
                {"old_weights": {}, "new_weights": {}, "correlations": {}, "changes": {}},
            ),
            (
                "oracle_first",
                {
                    **config,
                    "factors": {
                        "F1_tail_fund_inflow": {"weight": 0.0},
                        "F2_volume_price_sync": {"weight": 1.0},
                    },
                },
                {"old_weights": {}, "new_weights": {}, "correlations": {}, "changes": {}},
            ),
        ]), mock.patch.object(self.optimizer, "build_gated_regret_ranker_candidate", side_effect=AssertionError):
            result = self.optimizer._run_candidate_selection_cycle(
                config,
                {},
                samples,
                [],
                [],
                False,
            )

        self.assertEqual(result["candidate_name"], "oracle_first")
        self.assertEqual(result["new_candidate_backtest"]["avg_regret"], 0.0)
        self.assertEqual(result["new_candidate_backtest"]["exact_best_hit_rate"], 1.0)

    def test_optimize_regret_zero_persists_target_and_version_log(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
            "optimization": {},
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {"F1_tail_fund_inflow": 100, "F2_volume_price_sync": 0},
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 0, "F2_volume_price_sync": 100},
                        "return": 0.05,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {"F1_tail_fund_inflow": 100, "F2_volume_price_sync": 0},
                        "return": 0.01,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {"F1_tail_fund_inflow": 0, "F2_volume_price_sync": 100},
                        "return": 0.05,
                    },
                ],
            },
        ]
        writes = {}

        def fake_load(path):
            name = Path(path).name
            if name == "strategy_params.json":
                return json.loads(json.dumps(config))
            if name == "strategy_samples.json":
                return {"samples": samples}
            if name == "trades.json":
                return {"trades": []}
            if name == "strategy_version.json":
                return {"version": "1.0.0", "history": []}
            return {}

        def fake_save(path, data):
            writes[Path(path).name] = data

        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load), \
                mock.patch.object(self.optimizer, "_save_json", side_effect=fake_save), \
                mock.patch.object(self.optimizer, "_candidate_configs", return_value=[
                    (
                        "oracle_first",
                        {
                            **config,
                            "factors": {
                                "F1_tail_fund_inflow": {"weight": 0.0},
                                "F2_volume_price_sync": {"weight": 1.0},
                            },
                        },
                        {"old_weights": {}, "new_weights": {}, "correlations": {}, "changes": {}},
                    )
                ]), \
                mock.patch.object(self.optimizer, "build_gated_regret_ranker_candidate", return_value={
                    "name": "gated_noop",
                    "base_config": config,
                    "attack_config": config,
                    "min_attack_score_advantage": 999,
                    "attack_min_factor_scores": {},
                    "change_log": {"old_weights": {}, "new_weights": {}, "correlations": {}, "changes": {}},
                }):
            result = self.optimizer.optimize_regret_zero(
                validation_ratio=0.5,
                min_validation_samples=1,
            )

        self.assertEqual(result["status"], "optimized")
        saved_config = writes["strategy_params.json"]
        self.assertEqual(saved_config["strategy_mode"], "regret_zero_oracle_hit")
        self.assertEqual(saved_config["regret_zero_target"]["validation_ratio"], 0.5)
        version_entry = writes["strategy_version.json"]["history"][-1]
        self.assertEqual(version_entry["strategy_mode"], "regret_zero_oracle_hit")
        self.assertEqual(version_entry["new_candidate_backtest"]["avg_regret"], 0.0)

    def test_rejects_win_rate_only_gain_when_average_and_total_return_worse(self):
        old_bt = {
            "samples": 260,
            "trade_samples": 102,
            "empty_days": 158,
            "win_rate": 0.7843,
            "avg_return": 0.0053,
            "total_return": 0.5382,
            "max_consecutive_loss": 2,
        }
        new_bt = {
            "samples": 260,
            "trade_samples": 117,
            "empty_days": 143,
            "win_rate": 0.7900,
            "avg_return": 0.0048,
            "total_return": 0.5300,
            "max_consecutive_loss": 2,
        }

        accepted, reason = self.optimizer.evaluate_optimization_candidate(old_bt, new_bt)

        self.assertFalse(accepted)
        self.assertIn("收益未改善", reason)

    def test_optimize_weekly_accepts_selection_rule_candidate_from_candidate_pool(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {
                "min_samples": 1,
                "review_window": 2,
                "rollback_if_worse": True,
            },
        }
        trades = [
            {"buy_date": "2026-06-24", "score": 65, "return": -0.01, "factor_scores": {}},
            {"buy_date": "2026-06-25", "score": 66, "return": -0.02, "factor_scores": {}},
        ]
        samples = [
            {
                "date": "2026-06-24",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 75,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 80,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 30,
                        },
                        "return": -0.02,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 80,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 70,
                        },
                        "return": 0.03,
                    },
                ],
            },
            {
                "date": "2026-06-25",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 75,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 80,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 30,
                        },
                        "return": -0.01,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 80,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 70,
                        },
                        "return": 0.02,
                    },
                ],
            },
        ]
        writes = {}

        def fake_load(path):
            name = Path(path).name
            if name == "strategy_params.json":
                return json.loads(json.dumps(config))
            if name == "trades.json":
                return {"trades": trades}
            if name == "strategy_samples.json":
                return {"samples": samples}
            if name == "strategy_version.json":
                return {"version": "1.0.0", "history": []}
            return {}

        def fake_save(path, data):
            writes[Path(path).name] = data

        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load), \
                mock.patch.object(self.optimizer, "_save_json", side_effect=fake_save):
            result = self.optimizer.optimize_weekly()

        self.assertEqual(result["status"], "optimized")
        self.assertEqual(result["old_winrate"], 0.0)
        self.assertEqual(result["new_winrate"], 1.0)
        self.assertIn("selection_rules", result["optimization_method"])
        saved_config = writes["strategy_params.json"]
        self.assertNotIn("F2_volume_price_sync", saved_config["selection"]["min_factor_scores"])
        self.assertNotIn("F7_float_mv_fit", saved_config["selection"]["max_factor_scores"])
        version_entry = writes["strategy_version.json"]["history"][-1]
        self.assertTrue(any(
            item["name"] == "gated_regret_balanced_oracle_ranker"
            for item in version_entry["evaluated_candidates"]
        ))

    def test_candidate_configs_searches_f4_guardrail_and_mid_f7_cap(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            candidate["selection"]["max_factor_scores"].get("F7_float_mv_fit") == 50
            and candidate["selection"]["min_factor_scores"].get("F4_tail_rally_strength") == 55
            for _, candidate, _ in candidates
        ))

    def test_soft_penalty_reduces_score_without_rejecting_candidate(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {},
                "max_factor_scores": {},
                "soft_penalties": {
                    "F2_volume_price_sync": {
                        "direction": "below",
                        "threshold": 70,
                        "max_penalty": 6,
                    },
                    "F7_float_mv_fit": {
                        "direction": "above",
                        "threshold": 40,
                        "max_penalty": 4,
                    },
                },
            },
        }
        sample = {
            "date": "2026-06-24",
            "candidate_pool": [
                {
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 85,
                        "F4_tail_rally_strength": 80,
                        "F5_sector_heat": 50,
                        "F6_news_catalyst": 50,
                        "F7_float_mv_fit": 60,
                    },
                    "return": 0.01,
                }
            ],
        }

        pick = self.optimizer.pick_from_candidate_pool(sample, config)

        factors = sample["candidate_pool"][0]["factor_scores"]
        raw_score = sum(
            config["factors"][key]["weight"] * factors[key]
            for key in self.optimizer.FACTOR_KEYS
            if key in config["factors"]
        )
        self.assertIsNotNone(pick)
        self.assertLess(pick["_new_score"], raw_score)
        self.assertEqual(pick["symbol"], "600001")

    def test_learned_ranker_weights_prefer_profitable_factor_direction(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 50,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 80,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 20,
                        },
                        "return": 0.03,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 40,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 40,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 90,
                        },
                        "return": -0.02,
                    },
                ],
            },
            {
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 75,
                            "F2_volume_price_sync": 75,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 78,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 30,
                        },
                        "return": 0.02,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 75,
                            "F2_volume_price_sync": 45,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 45,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 85,
                        },
                        "return": -0.01,
                    },
                ],
            },
        ]

        learned_config, log = self.optimizer.build_learned_ranker_config(samples, config)

        self.assertGreater(learned_config["factors"]["F2_volume_price_sync"]["weight"], 0.15)
        self.assertGreater(learned_config["factors"]["F4_tail_rally_strength"]["weight"], 0.15)
        self.assertLess(learned_config["factors"]["F7_float_mv_fit"]["weight"], 0.1)
        self.assertEqual(log["changes"]["learned_ranker"]["training_rows"], 4)

    def test_candidate_configs_include_learned_ranker_when_training_samples_available(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 50,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
            "optimization": {},
        }
        samples = [
            {
                "candidate_pool": [
                    {
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 80,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 20,
                        },
                        "return": 0.03,
                    }
                ]
            }
        ] * 5

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
            training_samples=samples,
        )

        self.assertTrue(any(name == "learned_ranker_weights" for name, _, _ in candidates))

    def test_build_oracle_ranker_prefers_factors_lifted_in_daily_best(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.2},
                "F8_overnight_risk_control": {"weight": 0.2},
                "F9_overheat_control": {"weight": 0.2},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70, "F9_overheat_control": 85},
                "max_factor_scores": {"F8_overnight_risk_control": 90},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F8_overnight_risk_control": 60,
                            "F9_overheat_control": 50,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 40,
                            "F2_volume_price_sync": 90,
                            "F8_overnight_risk_control": 95,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 85,
                            "F2_volume_price_sync": 55,
                            "F8_overnight_risk_control": 65,
                            "F9_overheat_control": 55,
                        },
                        "return": 0.04,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 35,
                            "F2_volume_price_sync": 88,
                            "F8_overnight_risk_control": 96,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.0,
                    },
                ],
            },
        ] * 3

        new_config, log = self.optimizer.build_oracle_ranker_config(samples, config)

        self.assertGreater(
            new_config["factors"]["F1_tail_fund_inflow"]["weight"],
            new_config["factors"]["F2_volume_price_sync"]["weight"],
        )
        self.assertLess(
            new_config["factors"]["F9_overheat_control"]["weight"],
            config["factors"]["F9_overheat_control"]["weight"],
        )
        self.assertNotIn("F2_volume_price_sync", new_config["selection"]["min_factor_scores"])
        self.assertNotIn("F9_overheat_control", new_config["selection"]["min_factor_scores"])
        self.assertNotIn("F8_overnight_risk_control", new_config["selection"]["max_factor_scores"])
        self.assertEqual(
            log["changes"]["oracle_ranker"]["method"],
            "daily_oracle_factor_lift",
        )

    def test_candidate_configs_include_oracle_ranker_when_training_samples_available(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.2},
                "F8_overnight_risk_control": {"weight": 0.2},
                "F9_overheat_control": {"weight": 0.2},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F8_overnight_risk_control": 90},
            },
            "optimization": {},
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 50,
                            "F8_overnight_risk_control": 60,
                            "F9_overheat_control": 50,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 30,
                            "F2_volume_price_sync": 90,
                            "F8_overnight_risk_control": 95,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            }
        ] * 5

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
            training_samples=samples,
        )

        self.assertTrue(any(name == "oracle_ranker_weights" for name, _, _ in candidates))

    def test_candidate_configs_include_regret_balanced_oracle_ranker(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.2},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.2},
                "F8_overnight_risk_control": {"weight": 0.2},
                "F9_overheat_control": {"weight": 0.2},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {
                    "F2_volume_price_sync": 70,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {"F8_overnight_risk_control": 90},
            },
            "optimization": {},
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 62,
                            "F3_technical_pattern": 75,
                            "F4_tail_rally_strength": 72,
                            "F8_overnight_risk_control": 64,
                            "F9_overheat_control": 60,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 35,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 70,
                            "F4_tail_rally_strength": 70,
                            "F8_overnight_risk_control": 95,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.02,
                    },
                ],
            }
        ] * 5

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
            training_samples=samples,
        )
        matched = [
            candidate for name, candidate, _ in candidates
            if name == "regret_balanced_oracle_ranker"
        ]

        self.assertTrue(matched)
        balanced = matched[0]
        self.assertLessEqual(balanced["selection"]["score_threshold"], 55)
        self.assertLessEqual(
            balanced["selection"]["min_factor_scores"]["F2_volume_price_sync"],
            62,
        )
        self.assertLessEqual(
            balanced["selection"]["min_factor_scores"]["F8_overnight_risk_control"],
            64,
        )
        self.assertNotIn("F9_overheat_control", balanced["selection"]["min_factor_scores"])
        self.assertNotIn("F8_overnight_risk_control", balanced["selection"]["max_factor_scores"])

    def test_gated_regret_ranker_uses_attack_pick_only_when_score_advantage_is_large(self):
        base_config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
        }
        attack_config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.0},
                "F2_volume_price_sync": {"weight": 1.0},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {"F1_tail_fund_inflow": 95, "F2_volume_price_sync": 50},
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 80, "F2_volume_price_sync": 100},
                        "return": 0.05,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {"F1_tail_fund_inflow": 90, "F2_volume_price_sync": 84},
                        "return": 0.04,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {"F1_tail_fund_inflow": 85, "F2_volume_price_sync": 86},
                        "return": -0.02,
                    },
                ],
            },
        ]

        result = self.optimizer.backtest_gated_candidate_pool(
            samples,
            base_config,
            attack_config,
            min_attack_score_advantage=5,
        )

        self.assertEqual(result["picks"][0]["symbol"], "600002")
        self.assertEqual(result["picks"][0]["mode"], "attack")
        self.assertEqual(result["picks"][1]["symbol"], "600003")
        self.assertEqual(result["picks"][1]["mode"], "base")
        self.assertEqual(result["avg_regret"], 0.0)
        self.assertEqual(result["exact_best_hit_rate"], 1.0)

    def test_gated_regret_ranker_requires_attack_factor_floor(self):
        base_config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {"score_threshold": 0, "min_factor_scores": {}, "max_factor_scores": {}},
        }
        attack_config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.8},
            },
            "selection": {"score_threshold": 0, "min_factor_scores": {}, "max_factor_scores": {}},
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 50,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.04,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 95,
                            "F9_overheat_control": 40,
                        },
                        "return": -0.03,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_gated_candidate_pool(
            samples,
            base_config,
            attack_config,
            min_attack_score_advantage=5,
            attack_min_factor_scores={"F9_overheat_control": 80},
        )

        self.assertEqual(result["picks"][0]["symbol"], "600001")
        self.assertEqual(result["picks"][0]["mode"], "base")

    def test_counterfactual_rescue_gate_can_select_high_potential_blocked_candidate(self):
        base_config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 50,
                    "F1_tail_fund_inflow": 90,
                },
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 78,
                            "F4_tail_rally_strength": 82,
                            "F7_float_mv_fit": 88,
                            "F8_overnight_risk_control": 76,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.08,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 45,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 50,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            base_config,
            rescue_score_threshold=65,
            max_blockers=3,
        )

        self.assertEqual(result["picks"][0]["symbol"], "600001")
        self.assertEqual(result["picks"][0]["mode"], "rescue")
        self.assertEqual(result["avg_regret"], 0.0)
        self.assertEqual(result["exact_best_hit_rate"], 1.0)

    def test_counterfactual_rescue_gate_can_require_extra_factor_floors(self):
        base_config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 50,
                    "F1_tail_fund_inflow": 90,
                },
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 96,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 79,
                            "F4_tail_rally_strength": 90,
                            "F7_float_mv_fit": 88,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.08,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 45,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 50,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 96,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 82,
                            "F4_tail_rally_strength": 90,
                            "F7_float_mv_fit": 58,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.07,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 45,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 50,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600005",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 96,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 82,
                            "F4_tail_rally_strength": 90,
                            "F7_float_mv_fit": 65,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.06,
                    },
                    {
                        "symbol": "600006",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 45,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 50,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            },
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            base_config,
            rescue_score_threshold=65,
            max_blockers=3,
            rescue_min_factor_scores={
                "F3_technical_pattern": 80,
                "F7_float_mv_fit": 60,
            },
        )

        self.assertEqual([p["symbol"] for p in result["picks"]], [
            "600002",
            "600004",
            "600005",
        ])
        self.assertEqual(result["picks"][0]["mode"], "base")
        self.assertEqual(result["picks"][1]["mode"], "base")
        self.assertEqual(result["picks"][2]["mode"], "rescue")

    def test_pick_from_candidate_pool_honors_persisted_counterfactual_rescue_gate(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 50,
                    "F1_tail_fund_inflow": 90,
                },
                "counterfactual_rescue": {
                    "enabled": True,
                    "rescue_score_threshold": 65,
                    "max_blockers": 3,
                    "min_rescue_score_advantage": 12,
                    "rescue_min_factor_scores": {
                        "F3_technical_pattern": 80,
                        "F7_float_mv_fit": 60,
                    },
                },
            },
        }
        sample = {
            "date": "2026-06-01",
            "candidate_pool": [
                {
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 96,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 82,
                        "F4_tail_rally_strength": 90,
                        "F7_float_mv_fit": 65,
                        "F8_overnight_risk_control": 80,
                        "F9_overheat_control": 100,
                    },
                    "return": 0.06,
                },
                {
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 45,
                        "F2_volume_price_sync": 90,
                        "F3_technical_pattern": 80,
                        "F4_tail_rally_strength": 50,
                        "F7_float_mv_fit": 40,
                        "F8_overnight_risk_control": 80,
                        "F9_overheat_control": 100,
                    },
                    "return": -0.01,
                },
            ],
        }

        pick = self.optimizer.pick_from_candidate_pool(sample, config)

        self.assertEqual(pick["symbol"], "600001")
        self.assertEqual(pick["_selection_mode"], "rescue")

    def test_build_gated_regret_ranker_candidate_uses_default_f8_f9_gate(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.2},
                "F8_overnight_risk_control": {"weight": 0.2},
                "F9_overheat_control": {"weight": 0.2},
            },
            "selection": {"score_threshold": 55, "min_factor_scores": {}, "max_factor_scores": {}},
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 95,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 40,
                            "F2_volume_price_sync": 90,
                            "F8_overnight_risk_control": 60,
                            "F9_overheat_control": 40,
                        },
                        "return": -0.01,
                    },
                ],
            }
        ] * 5

        candidate = self.optimizer.build_gated_regret_ranker_candidate(samples, config)

        self.assertEqual(candidate["name"], "gated_regret_balanced_oracle_ranker")
        self.assertEqual(candidate["attack_min_factor_scores"], {
            "F8_overnight_risk_control": 75,
            "F9_overheat_control": 90,
        })
        self.assertEqual(candidate["min_attack_score_advantage"], 0)
        self.assertIn("attack_config", candidate)

    def test_mine_oracle_rescue_segments_finds_regret_reducing_blocker_pattern(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F3_technical_pattern": {"weight": 0.4},
                "F4_tail_rally_strength": {"weight": 0.2},
                "F7_float_mv_fit": {"weight": 0.2},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {},
                "max_factor_scores": {"F7_float_mv_fit": 50},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F3_technical_pattern": 70,
                            "F4_tail_rally_strength": 70,
                            "F7_float_mv_fit": 40,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 85,
                            "F3_technical_pattern": 90,
                            "F4_tail_rally_strength": 85,
                            "F7_float_mv_fit": 80,
                        },
                        "return": 0.05,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 72,
                            "F3_technical_pattern": 72,
                            "F4_tail_rally_strength": 72,
                            "F7_float_mv_fit": 45,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 88,
                            "F3_technical_pattern": 92,
                            "F4_tail_rally_strength": 86,
                            "F7_float_mv_fit": 82,
                        },
                        "return": 0.06,
                    },
                ],
            },
        ]

        segments = self.optimizer.mine_oracle_rescue_segments(
            samples,
            config,
            min_segment_hits=2,
            floor_quantiles=(0.0, 0.5),
        )

        self.assertTrue(segments)
        best = segments[0]
        self.assertEqual(best["allowed_blockers"], ("F7_float_mv_fit>max",))
        self.assertLess(best["backtest"]["avg_regret"], best["base_backtest"]["avg_regret"])
        self.assertEqual(best["backtest"]["exact_best_hit_rate"], 1.0)
        self.assertIn("train_backtest", best)
        self.assertIn("validation_backtest", best)
        self.assertTrue(any(segment["floor_quantile"] == 0.5 for segment in segments))

    def test_counterfactual_rescue_gate_can_apply_factor_ceilings(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.2},
                "F3_technical_pattern": {"weight": 0.3},
                "F4_tail_rally_strength": {"weight": 0.3},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F1_tail_fund_inflow": 97},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 75,
                            "F4_tail_rally_strength": 75,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 98,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 95,
                            "F4_tail_rally_strength": 95,
                        },
                        "return": -0.04,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            min_rescue_score_advantage=0,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_min_factor_scores={"F3_technical_pattern": 80},
            rescue_max_factor_scores={"F1_tail_fund_inflow": 90},
        )

        self.assertEqual(result["picks"][0]["symbol"], "600001")
        self.assertEqual(result["picks"][0]["mode"], "base")

    def test_counterfactual_rescue_gate_can_limit_score_advantage_window(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F1_tail_fund_inflow": 97},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                        },
                        "return": -0.04,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            min_rescue_score_advantage=0,
            max_rescue_score_advantage=10,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
        )

        self.assertEqual(result["picks"][0]["symbol"], "600001")
        self.assertEqual(result["picks"][0]["mode"], "base")

    def test_counterfactual_rescue_gate_can_only_rescue_empty_base_days(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.05,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.05,
                    },
                ],
            },
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            min_rescue_score_advantage=0,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
        )

        self.assertEqual(result["picks"][0]["symbol"], "600001")
        self.assertEqual(result["picks"][0]["mode"], "rescue")
        self.assertEqual(result["picks"][1]["symbol"], "600002")
        self.assertEqual(result["picks"][1]["mode"], "base")

    def test_persisted_counterfactual_rescue_can_only_rescue_empty_base_days(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
                "counterfactual_rescue": {
                    "enabled": True,
                    "rescue_score_threshold": 70,
                    "max_blockers": 1,
                    "min_rescue_score_advantage": 0,
                    "allowed_blocker_prefixes": ["F2_volume_price_sync<min"],
                    "rescue_when_base_absent_only": True,
                },
            },
        }
        sample = {
            "date": "2026-06-02",
            "candidate_pool": [
                {
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 70,
                        "F2_volume_price_sync": 80,
                    },
                    "return": 0.01,
                },
                {
                    "symbol": "600003",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 95,
                        "F2_volume_price_sync": 60,
                    },
                    "return": 0.05,
                },
            ],
        }

        pick = self.optimizer.pick_from_candidate_pool(sample, config)

        self.assertEqual(pick["symbol"], "600002")
        self.assertEqual(pick["_selection_mode"], "base")

    def test_backtest_candidate_pool_honors_persisted_neighbor_rescue_memory(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
                "neighbor_counterfactual_rescue": {
                    "enabled": True,
                    "rescue_score_threshold": 70,
                    "max_blockers": 1,
                    "allowed_blocker_prefixes": ["F2_volume_price_sync<min"],
                    "required_blocker_prefixes": ["F2_volume_price_sync<min"],
                    "rescue_when_base_absent_only": True,
                    "neighbor_factor_keys": [
                        "F1_tail_fund_inflow",
                        "F3_technical_pattern",
                    ],
                    "nearest_neighbor_count": 1,
                    "min_prior_neighbors": 1,
                    "min_neighbor_win_rate": 1.0,
                    "min_neighbor_avg_return": 0.0,
                },
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 90,
                    },
                    "return": 0.04,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [{
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 40,
                    },
                    "return": -0.03,
                }],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [{
                    "symbol": "600003",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 91,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 39,
                    },
                    "return": 0.05,
                }],
            },
        ]

        result = self.optimizer.backtest_candidate_pool(samples, config)

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600002"])
        self.assertEqual(result["picks"][0]["mode"], "neighbor_rescue")
        self.assertEqual(result["empty_days"], 2)

    def test_counterfactual_rescue_gate_can_require_full_pool_score_rank(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F1_tail_fund_inflow": 97},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 98,
                            "F2_volume_price_sync": 50,
                        },
                        "return": -0.01,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            min_rescue_score_advantage=0,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
            max_rescue_score_rank=1,
        )

        self.assertEqual(result["trade_samples"], 0)
        self.assertEqual(result["empty_days"], 1)

    def test_counterfactual_rescue_gate_can_require_minimum_full_pool_score_rank(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.01,
                    },
                ],
            }
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            min_rescue_score_advantage=0,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            min_rescue_score_rank=2,
        )

        self.assertEqual(result["picks"][0]["symbol"], "600002")
        self.assertEqual(result["empty_days"], 0)

    def test_counterfactual_rescue_gate_can_require_specific_blocker(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F7_float_mv_fit": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F7_float_mv_fit": 50},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F7_float_mv_fit": 40,
                        },
                        "return": 0.05,
                    }
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F7_float_mv_fit": 80,
                        },
                        "return": 0.06,
                    }
                ],
            },
        ]

        result = self.optimizer.backtest_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=2,
            min_rescue_score_advantage=0,
            allowed_blocker_prefixes=("F2_volume_price_sync<min", "F7_float_mv_fit>max"),
            required_blocker_prefixes=("F7_float_mv_fit>max",),
            rescue_when_base_absent_only=True,
        )

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600002"])

    def test_rolling_counterfactual_rescue_requires_recent_segment_edge(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.02,
                    }
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 91,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.03,
                    }
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 92,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.04,
                    }
                ],
            },
            {
                "date": "2026-06-04",
                "candidate_pool": [
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 93,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.05,
                    }
                ],
            },
        ]

        result = self.optimizer.backtest_rolling_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
            min_prior_segment_trades=2,
            min_prior_segment_win_rate=1.0,
            min_prior_segment_avg_return=0.0,
        )

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600003", "600004"])
        self.assertEqual(result["picks"][0]["mode"], "rolling_rescue")

    def test_rolling_counterfactual_rescue_can_use_recent_segment_window(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F2_volume_price_sync": 60},
                    "return": 0.03,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [{
                    "symbol": "600002",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F2_volume_price_sync": 60},
                    "return": 0.03,
                }],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [{
                    "symbol": "600003",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F2_volume_price_sync": 60},
                    "return": -0.02,
                }],
            },
            {
                "date": "2026-06-04",
                "candidate_pool": [{
                    "symbol": "600004",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F2_volume_price_sync": 60},
                    "return": 0.04,
                }],
            },
        ]

        result = self.optimizer.backtest_rolling_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
            min_prior_segment_trades=2,
            min_prior_segment_win_rate=1.0,
            min_prior_segment_avg_return=0.0,
            segment_history_window=2,
        )

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600003"])

    def test_neighbor_counterfactual_rescue_uses_similar_prior_candidates(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 90,
                    },
                    "return": 0.04,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [{
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 40,
                    },
                    "return": -0.03,
                }],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [{
                    "symbol": "600003",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 91,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 39,
                    },
                    "return": 0.05,
                }],
            },
        ]

        result = self.optimizer.backtest_neighbor_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
            neighbor_factor_keys=("F1_tail_fund_inflow", "F3_technical_pattern"),
            nearest_neighbor_count=1,
            min_prior_neighbors=1,
            min_neighbor_win_rate=1.0,
            min_neighbor_avg_return=0.0,
        )

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600002"])

    def test_neighbor_counterfactual_rescue_can_require_minimum_score_rank(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.04,
                    },
                    {
                        "symbol": "600010",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 91,
                            "F2_volume_price_sync": 60,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600011",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.01,
                    },
                ],
            },
        ]

        result = self.optimizer.backtest_neighbor_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=False,
            min_rescue_score_rank=2,
            neighbor_factor_keys=("F1_tail_fund_inflow",),
            nearest_neighbor_count=1,
            min_prior_neighbors=1,
            min_neighbor_win_rate=1.0,
            min_neighbor_avg_return=0.0,
        )

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600010", "600011"])

    def test_neighbor_counterfactual_rescue_can_use_cross_section_context_similarity(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F9_overheat_control": 40,
                        },
                        "return": 0.04,
                    },
                    {
                        "symbol": "600010",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 80,
                            "F9_overheat_control": 90,
                        },
                        "return": 0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F9_overheat_control": 40,
                        },
                        "return": -0.03,
                    },
                    {
                        "symbol": "600011",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 80,
                            "F9_overheat_control": 90,
                        },
                        "return": 0.01,
                    },
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                            "F9_overheat_control": 40,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600012",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 80,
                            "F9_overheat_control": 90,
                        },
                        "return": 0.01,
                    },
                ],
            },
        ]

        result = self.optimizer.backtest_neighbor_counterfactual_rescue_pool(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=False,
            neighbor_factor_keys=("CTX_F1_percentile",),
            nearest_neighbor_count=1,
            min_prior_neighbors=1,
            min_neighbor_win_rate=1.0,
            min_neighbor_avg_return=0.0,
        )

        self.assertEqual([pick["symbol"] for pick in result["picks"]], ["600010", "600011", "600012"])

    def test_fast_neighbor_rescue_matches_standard_backtest(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 90,
                    },
                    "return": 0.04,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [{
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 40,
                    },
                    "return": -0.03,
                }],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [{
                    "symbol": "600003",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 91,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 39,
                    },
                    "return": 0.05,
                }],
            },
        ]
        params = {
            "rescue_score_threshold": 70,
            "max_blockers": 1,
            "allowed_blocker_prefixes": ("F2_volume_price_sync<min",),
            "required_blocker_prefixes": ("F2_volume_price_sync<min",),
            "rescue_when_base_absent_only": True,
            "neighbor_factor_keys": ("F1_tail_fund_inflow", "F3_technical_pattern"),
            "nearest_neighbor_count": 1,
            "min_prior_neighbors": 1,
            "min_neighbor_win_rate": 1.0,
            "min_neighbor_avg_return": 0.0,
        }

        standard = self.optimizer.backtest_neighbor_counterfactual_rescue_pool(
            samples,
            config,
            **params,
        )
        prepared = self.optimizer.prepare_neighbor_rescue_backtest(samples, config)
        fast = self.optimizer.backtest_prepared_neighbor_rescue_pool(prepared, **params)

        self.assertEqual(fast["picks"], standard["picks"])
        for key in (
            "trade_samples",
            "empty_days",
            "win_rate",
            "avg_return",
            "total_return",
            "max_consecutive_loss",
            "avg_regret",
            "exact_best_hit_rate",
        ):
            self.assertEqual(fast[key], standard[key])

    def test_prepare_neighbor_rescue_backtest_adds_cross_section_context_features(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
        }
        samples = [{
            "date": "2026-06-01",
            "candidate_pool": [
                {
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 100,
                        "F9_overheat_control": 30,
                    },
                    "return": 0.04,
                },
                {
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 80,
                        "F9_overheat_control": 60,
                    },
                    "return": 0.01,
                },
                {
                    "symbol": "600003",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 20,
                        "F9_overheat_control": 90,
                    },
                    "return": -0.01,
                },
            ],
        }]

        prepared = self.optimizer.prepare_neighbor_rescue_backtest(samples, config)
        by_symbol = {
            item["symbol"]: item["factor_scores"]
            for item in prepared[0]["candidates"]
        }

        self.assertEqual(by_symbol["600001"]["CTX_F1_percentile"], 100.0)
        self.assertEqual(by_symbol["600001"]["CTX_F9_percentile"], 33.3333)
        self.assertEqual(by_symbol["600001"]["CTX_strong_f1_low_f9_share"], 33.3333)
        self.assertEqual(by_symbol["600003"]["CTX_F1_percentile"], 33.3333)
        self.assertEqual(by_symbol["600003"]["CTX_F9_percentile"], 100.0)

    def test_fast_neighbor_rescue_matches_standard_with_base_pick_and_rank_cap(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.0},
                "F4_tail_rally_strength": {"weight": 0.0},
                "F7_float_mv_fit": {"weight": 0.0},
                "F8_overnight_risk_control": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {},
                "max_factor_scores": {"F7_float_mv_fit": 50},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 90,
                            "F4_tail_rally_strength": 75,
                            "F7_float_mv_fit": 85,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 95,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 60,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 90,
                        },
                        "return": 0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 96,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 89,
                            "F4_tail_rally_strength": 76,
                            "F7_float_mv_fit": 86,
                            "F8_overnight_risk_control": 81,
                            "F9_overheat_control": 96,
                        },
                        "return": 0.06,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 72,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 60,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 90,
                        },
                        "return": -0.02,
                    },
                ],
            },
        ]
        params = {
            "rescue_score_threshold": 90,
            "max_blockers": 1,
            "min_rescue_score_advantage": 10,
            "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
            "required_blocker_prefixes": ("F7_float_mv_fit>max",),
            "rescue_when_base_absent_only": False,
            "min_rescue_score_rank": 1,
            "max_rescue_score_rank": 1,
            "neighbor_factor_keys": (
                "F1_tail_fund_inflow",
                "F3_technical_pattern",
                "F4_tail_rally_strength",
                "F7_float_mv_fit",
                "F8_overnight_risk_control",
                "F9_overheat_control",
            ),
            "nearest_neighbor_count": 1,
            "min_prior_neighbors": 1,
            "min_neighbor_win_rate": 1.0,
            "min_neighbor_avg_return": 0.0,
        }

        standard = self.optimizer.backtest_neighbor_counterfactual_rescue_pool(
            samples,
            config,
            **params,
        )
        prepared = self.optimizer.prepare_neighbor_rescue_backtest(samples, config)
        fast = self.optimizer.backtest_prepared_neighbor_rescue_pool(prepared, **params)

        self.assertEqual(fast["picks"], standard["picks"])
        self.assertEqual(fast["picks"][1]["symbol"], "600003")

    def test_candidate_selection_cycle_records_gated_regret_candidate(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.5},
                "F2_volume_price_sync": {"weight": 0.2},
                "F8_overnight_risk_control": {"weight": 0.2},
                "F9_overheat_control": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 0,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 50,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 95,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 100,
                            "F8_overnight_risk_control": 82,
                            "F9_overheat_control": 96,
                        },
                        "return": 0.05,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 88,
                            "F2_volume_price_sync": 52,
                            "F8_overnight_risk_control": 81,
                            "F9_overheat_control": 95,
                        },
                        "return": 0.0,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 78,
                            "F2_volume_price_sync": 98,
                            "F8_overnight_risk_control": 82,
                            "F9_overheat_control": 96,
                        },
                        "return": 0.04,
                    },
                ],
            },
        ] * 3

        result = self.optimizer._run_candidate_selection_cycle(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
            samples,
            samples,
            samples,
            True,
        )

        gated = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "gated_regret_balanced_oracle_ranker"
        ]
        self.assertTrue(gated)
        self.assertIn("gated_config", gated[0])
        self.assertEqual(gated[0]["gated_config"]["attack_min_factor_scores"], {
            "F8_overnight_risk_control": 75,
            "F9_overheat_control": 90,
        })

    def test_candidate_selection_cycle_records_counterfactual_rescue_candidate(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 50,
                    "F1_tail_fund_inflow": 90,
                },
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 78,
                            "F4_tail_rally_strength": 82,
                            "F7_float_mv_fit": 88,
                            "F8_overnight_risk_control": 76,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.08,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 45,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 50,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 96,
                            "F2_volume_price_sync": 61,
                            "F3_technical_pattern": 79,
                            "F4_tail_rally_strength": 83,
                            "F7_float_mv_fit": 89,
                            "F8_overnight_risk_control": 77,
                            "F9_overheat_control": 100,
                        },
                        "return": 0.07,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 45,
                            "F2_volume_price_sync": 90,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 50,
                            "F7_float_mv_fit": 40,
                            "F8_overnight_risk_control": 80,
                            "F9_overheat_control": 100,
                        },
                        "return": -0.01,
                    },
                ],
            },
        ] * 3

        result = self.optimizer._run_candidate_selection_cycle(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
            samples,
            samples,
            samples,
            True,
        )

        rescue = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "counterfactual_rescue_gate"
        ]
        self.assertTrue(rescue)
        self.assertEqual(rescue[0]["rescue_config"]["rescue_score_threshold"], 80)
        self.assertEqual(rescue[0]["rescue_config"]["max_blockers"], 3)
        self.assertEqual(rescue[0]["rescue_config"]["min_rescue_score_advantage"], 12)
        self.assertEqual(rescue[0]["rescue_config"]["rescue_min_factor_scores"], {
            "F3_technical_pattern": 80,
            "F7_float_mv_fit": 60,
        })
        f7_rescue = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "counterfactual_rescue_f7_empty_only_guarded_gate"
        ]
        self.assertTrue(f7_rescue)
        self.assertEqual(
            f7_rescue[0]["rescue_config"]["required_blocker_prefixes"],
            ("F7_float_mv_fit>max",),
        )
        self.assertTrue(f7_rescue[0]["rescue_config"]["rescue_when_base_absent_only"])
        self.assertEqual(
            f7_rescue[0]["rescue_config"]["rescue_max_factor_scores"],
            {"F1_tail_fund_inflow": 80, "F7_float_mv_fit": 90},
        )

    def test_candidate_selection_cycle_records_neighbor_rescue_candidate(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 50,
                    "F1_tail_fund_inflow": 90,
                },
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 88,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 80,
                        "F4_tail_rally_strength": 68,
                        "F7_float_mv_fit": 48,
                        "F8_overnight_risk_control": 72,
                        "F9_overheat_control": 90,
                    },
                    "return": 0.04,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [{
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 87,
                        "F2_volume_price_sync": 61,
                        "F3_technical_pattern": 81,
                        "F4_tail_rally_strength": 67,
                        "F7_float_mv_fit": 49,
                        "F8_overnight_risk_control": 73,
                        "F9_overheat_control": 91,
                    },
                    "return": 0.05,
                }],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [{
                    "symbol": "600003",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 86,
                        "F2_volume_price_sync": 62,
                        "F3_technical_pattern": 82,
                        "F4_tail_rally_strength": 66,
                        "F7_float_mv_fit": 50,
                        "F8_overnight_risk_control": 74,
                        "F9_overheat_control": 92,
                    },
                    "return": 0.06,
                }],
            },
        ] * 3

        result = self.optimizer._run_candidate_selection_cycle(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
            samples,
            samples,
            samples,
            True,
        )

        neighbor = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "neighbor_counterfactual_rescue_gate"
        ]
        self.assertTrue(neighbor)
        self.assertEqual(neighbor[0]["neighbor_rescue_config"]["nearest_neighbor_count"], 3)
        self.assertEqual(neighbor[0]["neighbor_rescue_config"]["min_prior_neighbors"], 2)
        self.assertEqual(
            neighbor[0]["neighbor_rescue_config"]["required_blocker_prefixes"],
            ("F2_volume_price_sync<min",),
        )
        self.assertTrue(neighbor[0]["neighbor_rescue_config"]["rescue_when_base_absent_only"])
        rank_floor = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "neighbor_counterfactual_rescue_rank_floor_gate"
        ]
        self.assertTrue(rank_floor)
        self.assertEqual(rank_floor[0]["neighbor_rescue_config"]["min_rescue_score_rank"], 6)
        self.assertEqual(
            rank_floor[0]["neighbor_rescue_config"]["required_blocker_prefixes"],
            ("F2_volume_price_sync<min", "F9_overheat_control<min"),
        )
        f7_empty_only = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "neighbor_counterfactual_rescue_f7_empty_only_gate"
        ]
        self.assertTrue(f7_empty_only)
        self.assertEqual(
            f7_empty_only[0]["neighbor_rescue_config"]["required_blocker_prefixes"],
            ("F7_float_mv_fit>max",),
        )
        self.assertTrue(
            f7_empty_only[0]["neighbor_rescue_config"]["rescue_when_base_absent_only"]
        )
        self.assertEqual(
            f7_empty_only[0]["neighbor_rescue_config"]["rescue_min_factor_scores"]["F9_overheat_control"],
            80,
        )
        f7_guarded = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "neighbor_counterfactual_rescue_f7_empty_only_guarded_gate"
        ]
        self.assertTrue(f7_guarded)
        self.assertEqual(
            f7_guarded[0]["neighbor_rescue_config"]["rescue_max_factor_scores"],
            {"F1_tail_fund_inflow": 80, "F7_float_mv_fit": 90},
        )

    def test_candidate_selection_cycle_promotes_accepted_neighbor_rescue_to_live_config(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {"F2_volume_price_sync": 65},
                "max_factor_scores": {},
            },
        }
        samples = [{
            "date": "2026-06-01",
            "candidate_pool": [{
                "symbol": "600001",
                "factor_scores": {
                    "F1_tail_fund_inflow": 90,
                    "F2_volume_price_sync": 60,
                    "F3_technical_pattern": 80,
                    "F4_tail_rally_strength": 70,
                    "F7_float_mv_fit": 50,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 90,
                },
                "return": 0.04,
            }],
        }] * 3

        def fake_evaluate(*args):
            full_new_backtest = args[5]
            return (
                full_new_backtest.get("_candidate") == "neighbor",
                "forced neighbor acceptance",
            )

        def fake_neighbor_backtest(*args, **kwargs):
            return {
                "_candidate": "neighbor",
                "win_rate": 1.0,
                "avg_return": 0.05,
                "total_return": 0.15,
                "max_consecutive_loss": 0,
                "trade_samples": 3,
                "avg_regret": 0.0,
                "exact_best_hit_rate": 1.0,
            }

        with mock.patch.object(
            self.optimizer,
            "backtest_neighbor_counterfactual_rescue_pool",
            side_effect=fake_neighbor_backtest,
        ), mock.patch.object(
            self.optimizer,
            "evaluate_walk_forward_candidate",
            side_effect=fake_evaluate,
        ):
            result = self.optimizer._run_candidate_selection_cycle(
                config,
                {key: 0 for key in self.optimizer.FACTOR_KEYS},
                samples,
                samples,
                samples,
                True,
            )

        neighbor = [
            item for item in result["evaluated_candidates"]
            if item["name"] == "neighbor_counterfactual_rescue_gate"
        ]
        self.assertTrue(neighbor)
        self.assertTrue(neighbor[0]["accepted"])
        self.assertEqual(result["candidate_name"], "neighbor_counterfactual_rescue_gate")
        persisted = result["config"]["selection"]["neighbor_counterfactual_rescue"]
        self.assertTrue(persisted["enabled"])
        self.assertEqual(persisted["nearest_neighbor_count"], 3)
        self.assertEqual(persisted["required_blocker_prefixes"], ("F2_volume_price_sync<min",))

    def test_candidate_selection_cycle_promotes_rank_floor_neighbor_rescue_config(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.25},
                "F2_volume_price_sync": {"weight": 0.1},
                "F3_technical_pattern": {"weight": 0.1},
                "F4_tail_rally_strength": {"weight": 0.3},
                "F7_float_mv_fit": {"weight": 0.05},
                "F8_overnight_risk_control": {"weight": 0.15},
                "F9_overheat_control": {"weight": 0.05},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {"F2_volume_price_sync": 65},
                "max_factor_scores": {},
            },
        }
        samples = [{
            "date": "2026-06-01",
            "candidate_pool": [{
                "symbol": "600001",
                "factor_scores": {
                    "F1_tail_fund_inflow": 90,
                    "F2_volume_price_sync": 60,
                    "F3_technical_pattern": 80,
                    "F4_tail_rally_strength": 70,
                    "F7_float_mv_fit": 50,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 70,
                },
                "return": 0.04,
            }],
        }] * 3

        def fake_evaluate(*args):
            full_new_backtest = args[5]
            return (
                full_new_backtest.get("_candidate") == "rank_floor",
                "forced rank-floor neighbor acceptance",
            )

        def fake_neighbor_backtest(*args, **kwargs):
            return {
                "_candidate": "rank_floor" if kwargs.get("min_rescue_score_rank") == 6 else "neighbor",
                "win_rate": 1.0,
                "avg_return": 0.05,
                "total_return": 0.15,
                "max_consecutive_loss": 0,
                "trade_samples": 3,
                "avg_regret": 0.0,
                "exact_best_hit_rate": 1.0,
            }

        with mock.patch.object(
            self.optimizer,
            "backtest_neighbor_counterfactual_rescue_pool",
            side_effect=fake_neighbor_backtest,
        ), mock.patch.object(
            self.optimizer,
            "evaluate_walk_forward_candidate",
            side_effect=fake_evaluate,
        ):
            result = self.optimizer._run_candidate_selection_cycle(
                config,
                {key: 0 for key in self.optimizer.FACTOR_KEYS},
                samples,
                samples,
                samples,
                True,
            )

        self.assertEqual(result["candidate_name"], "neighbor_counterfactual_rescue_rank_floor_gate")
        persisted = result["config"]["selection"]["neighbor_counterfactual_rescue"]
        self.assertEqual(persisted["min_rescue_score_rank"], 6)
        self.assertEqual(persisted["required_blocker_prefixes"], (
            "F2_volume_price_sync<min",
            "F9_overheat_control<min",
        ))

    def test_candidate_configs_include_soft_penalty_search(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            "soft_penalty" in name
            and candidate["selection"].get("soft_penalties", {}).get("F2_volume_price_sync")
            for name, candidate, _ in candidates
        ))

    def test_candidate_configs_include_overnight_risk_control_search_when_available(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {},
                "max_factor_scores": {},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            "F8_overnight_risk_control" in candidate["selection"].get("min_factor_scores", {})
            or "F8_overnight_risk_control" in candidate["selection"].get("soft_penalties", {})
            for _, candidate, _ in candidates
        ))

    def test_candidate_configs_search_high_confidence_f2_f7_f8_combo(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {"F2_volume_price_sync": 70, "F4_tail_rally_strength": 55},
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            candidate["selection"].get("score_threshold") == 60
            and candidate["selection"].get("min_factor_scores", {}).get("F2_volume_price_sync") == 75
            and candidate["selection"].get("min_factor_scores", {}).get("F8_overnight_risk_control") == 70
            and candidate["selection"].get("max_factor_scores", {}).get("F7_float_mv_fit") == 30
            for _, candidate, _ in candidates
        ))

    def test_candidate_configs_search_f3_technical_confirmation_combo(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {
                    "F2_volume_price_sync": 75,
                    "F4_tail_rally_strength": 55,
                    "F8_overnight_risk_control": 70,
                },
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            candidate["selection"].get("score_threshold") == 60
            and candidate["selection"].get("min_factor_scores", {}).get("F2_volume_price_sync") == 75
            and candidate["selection"].get("min_factor_scores", {}).get("F3_technical_pattern") == 70
            and candidate["selection"].get("min_factor_scores", {}).get("F8_overnight_risk_control") == 70
            and candidate["selection"].get("max_factor_scores", {}).get("F7_float_mv_fit") == 40
            for _, candidate, _ in candidates
        ))

    def test_candidate_configs_search_overheat_control_combo(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {
                    "F2_volume_price_sync": 75,
                    "F3_technical_pattern": 70,
                    "F4_tail_rally_strength": 55,
                    "F8_overnight_risk_control": 70,
                },
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            candidate["selection"].get("min_factor_scores", {}).get("F9_overheat_control") == 80
            for _, candidate, _ in candidates
        ))

    def test_candidate_configs_search_fund_and_risk_upper_caps(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 75,
                    "F3_technical_pattern": 70,
                    "F4_tail_rally_strength": 55,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {"F7_float_mv_fit": 40},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            candidate["selection"].get("min_factor_scores", {}).get("F2_volume_price_sync") == 75
            and candidate["selection"].get("min_factor_scores", {}).get("F4_tail_rally_strength") == 75
            and candidate["selection"].get("max_factor_scores", {}).get("F1_tail_fund_inflow") == 90
            and candidate["selection"].get("max_factor_scores", {}).get("F8_overnight_risk_control") == 90
            for _, candidate, _ in candidates
        ))

    def test_candidate_configs_search_stricter_overnight_risk_floor(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {"F8_overnight_risk_control": 70},
                "max_factor_scores": {},
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            candidate["selection"].get("min_factor_scores", {}).get("F8_overnight_risk_control") == 78
            for _, candidate, _ in candidates
        ))

    def test_candidate_configs_search_participation_recovery_soft_guards(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 75,
                    "F3_technical_pattern": 70,
                    "F4_tail_rally_strength": 75,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 40,
                    "F1_tail_fund_inflow": 90,
                    "F8_overnight_risk_control": 90,
                },
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            "participation_recovery" in name
            and "F2_volume_price_sync" not in candidate["selection"].get("min_factor_scores", {})
            and "F4_tail_rally_strength" not in candidate["selection"].get("min_factor_scores", {})
            and "F7_float_mv_fit" not in candidate["selection"].get("max_factor_scores", {})
            and candidate["selection"].get("soft_penalties", {}).get("F2_volume_price_sync", {}).get("threshold") == 65
            and candidate["selection"].get("soft_penalties", {}).get("F4_tail_rally_strength", {}).get("threshold") == 65
            and candidate["selection"].get("soft_penalties", {}).get("F7_float_mv_fit", {}).get("threshold") == 60
            for name, candidate, _ in candidates
        ))

    def test_candidate_configs_search_controlled_participation_recovery(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
                "F8_overnight_risk_control": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 75,
                    "F3_technical_pattern": 70,
                    "F4_tail_rally_strength": 75,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 40,
                    "F1_tail_fund_inflow": 90,
                    "F8_overnight_risk_control": 90,
                },
            },
            "optimization": {},
        }

        candidates = self.optimizer._candidate_configs(
            config,
            {key: 0 for key in self.optimizer.FACTOR_KEYS},
        )

        self.assertTrue(any(
            "controlled_participation" in name
            and candidate["selection"]["min_factor_scores"].get("F2_volume_price_sync") == 70
            and candidate["selection"]["min_factor_scores"].get("F4_tail_rally_strength") == 70
            and candidate["selection"]["max_factor_scores"].get("F7_float_mv_fit") == 60
            for name, candidate, _ in candidates
        ))

    def test_walk_forward_rejects_training_only_improvement_when_validation_worse(self):
        train_old = {
            "samples": 40,
            "trade_samples": 40,
            "empty_days": 0,
            "win_rate": 0.3,
            "avg_return": -0.008,
            "max_consecutive_loss": 5,
        }
        train_new = {
            "samples": 40,
            "trade_samples": 40,
            "empty_days": 0,
            "win_rate": 0.45,
            "avg_return": -0.001,
            "max_consecutive_loss": 4,
        }
        validation_old = {
            "samples": 20,
            "trade_samples": 20,
            "empty_days": 0,
            "win_rate": 0.35,
            "avg_return": -0.004,
            "max_consecutive_loss": 3,
        }
        validation_new = {
            "samples": 20,
            "trade_samples": 20,
            "empty_days": 0,
            "win_rate": 0.2,
            "avg_return": -0.012,
            "max_consecutive_loss": 6,
        }

        accepted, reason = self.optimizer.evaluate_walk_forward_candidate(
            train_old,
            train_new,
            validation_old,
            validation_new,
        )

        self.assertFalse(accepted)
        self.assertIn("验证段", reason)

    def test_walk_forward_accepts_validation_regret_priority_when_risk_not_worse(self):
        train_old = {
            "samples": 100,
            "trade_samples": 50,
            "empty_days": 50,
            "win_rate": 0.79,
            "avg_return": 0.006,
            "total_return": 0.30,
            "max_consecutive_loss": 2,
            "avg_regret": 0.021,
            "exact_best_hit_rate": 0.07,
        }
        train_new = {
            "samples": 100,
            "trade_samples": 55,
            "empty_days": 45,
            "win_rate": 0.80,
            "avg_return": 0.0062,
            "total_return": 0.341,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0206,
            "exact_best_hit_rate": 0.08,
        }
        validation_old = {
            "samples": 40,
            "trade_samples": 20,
            "empty_days": 20,
            "win_rate": 0.8333,
            "avg_return": 0.0061,
            "total_return": 0.122,
            "max_consecutive_loss": 1,
            "avg_regret": 0.0233,
            "exact_best_hit_rate": 0.0385,
        }
        validation_new = {
            "samples": 40,
            "trade_samples": 24,
            "empty_days": 16,
            "win_rate": 0.825,
            "avg_return": 0.0063,
            "total_return": 0.1512,
            "max_consecutive_loss": 1,
            "avg_regret": 0.0229,
            "exact_best_hit_rate": 0.0513,
        }
        full_old = {
            "samples": 140,
            "trade_samples": 70,
            "empty_days": 70,
            "win_rate": 0.805,
            "avg_return": 0.006,
            "total_return": 0.42,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0217,
            "exact_best_hit_rate": 0.0615,
        }
        full_new = {
            "samples": 140,
            "trade_samples": 79,
            "empty_days": 61,
            "win_rate": 0.79,
            "avg_return": 0.0062,
            "total_return": 0.4898,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0213,
            "exact_best_hit_rate": 0.0731,
        }

        accepted, reason = self.optimizer.evaluate_walk_forward_candidate(
            train_old,
            train_new,
            validation_old,
            validation_new,
            full_old,
            full_new,
        )

        self.assertTrue(accepted)
        self.assertIn("验证段", reason)
        self.assertIn("机会损失", reason)
        self.assertIn("最优命中", reason)

    def test_walk_forward_rejects_full_sample_regret_and_best_hit_regression(self):
        train_old = {
            "samples": 100,
            "trade_samples": 50,
            "empty_days": 50,
            "win_rate": 0.78,
            "avg_return": 0.0058,
            "total_return": 0.29,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0221,
            "exact_best_hit_rate": 0.0538,
        }
        train_new = {
            "samples": 100,
            "trade_samples": 45,
            "empty_days": 55,
            "win_rate": 0.825,
            "avg_return": 0.0061,
            "total_return": 0.2745,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0224,
            "exact_best_hit_rate": 0.0462,
        }
        validation_old = {
            "samples": 40,
            "trade_samples": 20,
            "empty_days": 20,
            "win_rate": 0.8333,
            "avg_return": 0.0061,
            "total_return": 0.122,
            "max_consecutive_loss": 1,
            "avg_regret": 0.0233,
            "exact_best_hit_rate": 0.0385,
        }
        validation_new = {
            "samples": 40,
            "trade_samples": 19,
            "empty_days": 21,
            "win_rate": 0.8387,
            "avg_return": 0.0071,
            "total_return": 0.1349,
            "max_consecutive_loss": 1,
            "avg_regret": 0.0236,
            "exact_best_hit_rate": 0.0256,
        }
        full_old = {
            "samples": 140,
            "trade_samples": 70,
            "empty_days": 70,
            "win_rate": 0.7939,
            "avg_return": 0.0059,
            "total_return": 0.768,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0221,
            "exact_best_hit_rate": 0.0538,
        }
        full_new = {
            "samples": 140,
            "trade_samples": 64,
            "empty_days": 76,
            "win_rate": 0.8288,
            "avg_return": 0.0064,
            "total_return": 0.7087,
            "max_consecutive_loss": 2,
            "avg_regret": 0.0224,
            "exact_best_hit_rate": 0.0462,
        }

        accepted, reason = self.optimizer.evaluate_walk_forward_candidate(
            train_old,
            train_new,
            validation_old,
            validation_new,
            full_old,
            full_new,
        )

        self.assertFalse(accepted)
        self.assertIn("全样本机会损失退化", reason)
        self.assertIn("全样本最优命中退化", reason)

    def test_split_walk_forward_samples_keeps_latest_dates_for_validation(self):
        samples = [{"date": f"2026-06-{day:02d}", "candidate_pool": [{}]} for day in range(1, 11)]

        train, validation = self.optimizer.split_walk_forward_samples(
            samples,
            validation_ratio=0.3,
            min_validation_samples=1,
        )

        self.assertEqual([s["date"] for s in train], [f"2026-06-{day:02d}" for day in range(1, 8)])
        self.assertEqual([s["date"] for s in validation], [f"2026-06-{day:02d}" for day in range(8, 11)])

    def test_optimize_iterative_runs_multiple_rounds_and_updates_version(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 70,
                    "F4_tail_rally_strength": 70,
                },
                "max_factor_scores": {
                    "F7_float_mv_fit": 40,
                },
            },
            "optimization": {
                "review_window": 30,
                "min_samples": 1,
                "walk_forward_validation_ratio": 0.3,
                "walk_forward_min_validation_samples": 1,
            },
        }
        trades = [
            {
                "buy_date": f"2026-06-{d:02d}",
                "score": 60,
                "return": 0.01,
                "factor_scores": {
                    "F1_tail_fund_inflow": 60,
                    "F2_volume_price_sync": 70,
                    "F3_technical_pattern": 70,
                    "F4_tail_rally_strength": 70,
                    "F5_sector_heat": 50,
                    "F6_news_catalyst": 50,
                    "F7_float_mv_fit": 50,
                },
            }
            for d in range(1, 16)
        ]
        samples = []
        for d in range(1, 16):
            date = f"2026-06-{d:02d}"
            samples.append(
                {
                    "date": date,
                    "candidate_pool": [
                        {
                            "symbol": "600001",
                            "factor_scores": {
                                "F1_tail_fund_inflow": 80,
                                "F2_volume_price_sync": 80,
                                "F3_technical_pattern": 80,
                                "F4_tail_rally_strength": 80,
                                "F5_sector_heat": 50,
                                "F6_news_catalyst": 50,
                                "F7_float_mv_fit": 30,
                            },
                            "return": 0.02,
                        },
                        {
                            "symbol": "600002",
                            "factor_scores": {
                                "F1_tail_fund_inflow": 70,
                                "F2_volume_price_sync": 60,
                                "F3_technical_pattern": 70,
                                "F4_tail_rally_strength": 75,
                                "F5_sector_heat": 50,
                                "F6_news_catalyst": 50,
                                "F7_float_mv_fit": 60,
                            },
                            "return": -0.01,
                        },
                    ],
                }
            )

        writes = {}

        def fake_load(path):
            p = Path(path).name
            if p == "strategy_params.json":
                return dict(config)
            if p == "trades.json":
                return {"trades": trades}
            if p == "strategy_samples.json":
                return {"samples": samples}
            if p == "strategy_version.json":
                return {
                    "version": "1.0.0",
                    "history": [],
                }
            if p == "metrics_snapshots.json":
                return {"snapshots": []}
            if p == "adjustments.json":
                return {}
            return {}

        def fake_save(path, data):
            p = Path(path).name
            writes[p] = data

        fake_feedback = types.ModuleType("feedback_loop")
        fake_feedback.collect_metrics = mock.MagicMock(
            side_effect=["MS-pre", "MS-mid", "MS-post", "MS-post2"],
        )
        candidate_cycle = {
            "selected": True,
            "accepted": True,
            "reason": "mock pass",
            "candidate_name": "mock_cycle",
            "config": config,
            "change_log": {"old_weights": {}, "new_weights": {}},
            "old_candidate_backtest": {
                "win_rate": 0.30,
                "avg_return": 0.001,
                "max_consecutive_loss": 3,
                "samples": 15,
                "trade_samples": 15,
                "empty_days": 0,
                "total_return": 0.02,
            },
            "new_candidate_backtest": {
                "win_rate": 0.35,
                "avg_return": 0.002,
                "max_consecutive_loss": 2,
                "samples": 15,
                "trade_samples": 15,
                "empty_days": 0,
                "total_return": 0.025,
            },
            "train_backtest": {
                "win_rate": 0.30,
                "avg_return": 0.001,
                "max_consecutive_loss": 3,
                "samples": 10,
                "trade_samples": 10,
                "empty_days": 0,
                "total_return": 0.01,
            },
            "validation_backtest": {
                "win_rate": 0.35,
                "avg_return": 0.002,
                "max_consecutive_loss": 2,
                "samples": 5,
                "trade_samples": 5,
                "empty_days": 0,
                "total_return": 0.005,
            },
            "evaluated_candidates": [{"name": "mock", "accepted": True}],
        }
        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load), \
                mock.patch.object(self.optimizer, "_save_json", side_effect=fake_save), \
                mock.patch.object(self.optimizer, "_run_candidate_selection_cycle", return_value=candidate_cycle), \
                mock.patch.dict("sys.modules", {"feedback_loop": fake_feedback}):
            result = self.optimizer.optimize_iterative(
                rounds=2,
                walk_forward_ratio=0.2,
                min_validation_samples=1,
            )

        self.assertEqual(result["status"], "optimized")
        self.assertEqual(result["rounds_executed"], 2)
        self.assertEqual(result["old_version"], "1.0.0")
        self.assertEqual(result["new_version"], "1.0.1")
        self.assertIn("strategy_params.json", writes)
        self.assertIn("strategy_version.json", writes)

    def test_optimize_iterative_skips_when_candidate_pool_empty(self):
        config = {
            "version": "1.0.0",
            "factors": {"F1_tail_fund_inflow": {"weight": 0.2}},
            "selection": {"score_threshold": 55, "min_factor_scores": {}, "max_factor_scores": {}},
            "optimization": {"min_samples": 1, "walk_forward_validation_ratio": 0.3, "walk_forward_min_validation_samples": 1},
        }
        trades = [{
            "buy_date": "2026-06-01",
            "score": 60,
            "return": 0.01,
            "factor_scores": {"F1_tail_fund_inflow": 60},
        }]
        samples = [{"date": "2026-06-01", "candidate_pool": []}]

        def fake_load(path):
            p = Path(path).name
            if p == "strategy_params.json":
                return dict(config)
            if p == "trades.json":
                return {"trades": trades}
            if p == "strategy_samples.json":
                return {"samples": samples}
            if p == "strategy_version.json":
                return {"version": "1.0.0", "history": []}
            return {}

        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load),                 mock.patch.object(self.optimizer, "_save_json"):
            result = self.optimizer.optimize_iterative(rounds=2)

        self.assertEqual(result["status"], "skipped")
        self.assertIn("候选池样本不足", result["reason"])




    def test_evaluate_balance_candidate_accepts_target_band(self):
        bt = {
            "samples": 260,
            "trade_samples": 104,
            "win_rate": 0.7115,
            "avg_return": 0.0021,
            "max_consecutive_loss": 3,
        }

        accepted, reason, score = self.optimizer.evaluate_balance_candidate(
            bt,
            min_participation=0.30,
            max_participation=0.45,
            min_win_rate=0.70,
            max_consecutive_loss=3,
            min_avg_return=0.0,
        )

        self.assertTrue(accepted)
        self.assertGreater(score, 0)
        self.assertIn("出手率", reason)

    def test_evaluate_balance_candidate_rejects_unbalanced_candidates(self):
        cases = [
            ({"samples": 260, "trade_samples": 50, "win_rate": 0.84, "avg_return": 0.004, "max_consecutive_loss": 2}, "出手率低于目标"),
            ({"samples": 260, "trade_samples": 221, "win_rate": 0.6606, "avg_return": 0.0016, "max_consecutive_loss": 5}, "出手率高于目标"),
            ({"samples": 260, "trade_samples": 104, "win_rate": 0.69, "avg_return": 0.002, "max_consecutive_loss": 3}, "胜率低于目标"),
            ({"samples": 260, "trade_samples": 104, "win_rate": 0.72, "avg_return": -0.001, "max_consecutive_loss": 3}, "平均收益不达标"),
            ({"samples": 260, "trade_samples": 104, "win_rate": 0.72, "avg_return": 0.002, "max_consecutive_loss": 4}, "最大连亏超限"),
        ]

        for bt, expected in cases:
            accepted, reason, _ = self.optimizer.evaluate_balance_candidate(
                bt,
                min_participation=0.30,
                max_participation=0.45,
                min_win_rate=0.70,
                max_consecutive_loss=3,
                min_avg_return=0.0,
            )
            self.assertFalse(accepted)
            self.assertIn(expected, reason)

    def test_optimize_balance_updates_single_formal_strategy(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 70,
                "min_factor_scores": {"F2_volume_price_sync": 90},
                "max_factor_scores": {},
            },
            "optimization": {},
        }
        trades = [{"buy_date": "2026-06-01", "return": 0.01, "score": 70, "factor_scores": {}}]
        samples = []
        for idx in range(10):
            samples.append({
                "date": f"2026-06-{idx + 1:02d}",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 65,
                            "F3_technical_pattern": 80,
                            "F4_tail_rally_strength": 75 if idx < 3 else 55,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 40,
                        },
                        "return": 0.02 if idx < 3 else -0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 50,
                            "F2_volume_price_sync": 50,
                            "F3_technical_pattern": 50,
                            "F4_tail_rally_strength": 50,
                            "F5_sector_heat": 50,
                            "F6_news_catalyst": 50,
                            "F7_float_mv_fit": 50,
                        },
                        "return": -0.02,
                    },
                ],
            })
        writes = {}

        def fake_load(path):
            name = Path(path).name
            if name == "strategy_params.json":
                return json.loads(json.dumps(config))
            if name == "strategy_samples.json":
                return {"samples": samples}
            if name == "strategy_version.json":
                return {"version": "1.0.0", "history": []}
            if name == "trades.json":
                return {"trades": trades}
            return {}

        def fake_save(path, data):
            writes[Path(path).name] = data

        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load), \
                mock.patch.object(self.optimizer, "_save_json", side_effect=fake_save):
            result = self.optimizer.optimize_balance(
                min_participation=0.30,
                max_participation=0.40,
                min_win_rate=0.70,
                max_consecutive_loss=3,
            )

        self.assertEqual(result["status"], "optimized")
        self.assertEqual(result["new_candidate_backtest"]["trade_samples"], 3)
        self.assertEqual(result["new_version"], "1.0.1")
        self.assertEqual(writes["strategy_params.json"]["strategy_mode"], "single_formal_balance")
        self.assertIn("strategy_version.json", writes)

    def test_optimize_balance_records_walk_forward_backtests(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 70,
                "min_factor_scores": {"F2_volume_price_sync": 90},
                "max_factor_scores": {},
            },
            "optimization": {},
        }
        samples = []
        for idx in range(12):
            samples.append({
                "date": f"2026-06-{idx + 1:02d}",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 80,
                        "F2_volume_price_sync": 65,
                        "F3_technical_pattern": 80,
                        "F4_tail_rally_strength": 75,
                        "F5_sector_heat": 50,
                        "F6_news_catalyst": 50,
                        "F7_float_mv_fit": 40,
                    },
                    "return": 0.02 if idx not in (1, 5, 9) else -0.01,
                }],
            })
        writes = {}

        def fake_load(path):
            name = Path(path).name
            if name == "strategy_params.json":
                return json.loads(json.dumps(config))
            if name == "strategy_samples.json":
                return {"samples": samples}
            if name == "strategy_version.json":
                return {"version": "1.0.0", "history": []}
            if name == "trades.json":
                return {"trades": []}
            return {}

        def fake_save(path, data):
            writes[Path(path).name] = data

        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load), \
                mock.patch.object(self.optimizer, "_save_json", side_effect=fake_save):
            result = self.optimizer.optimize_balance(
                min_participation=0.70,
                max_participation=1.0,
                min_win_rate=0.70,
                max_consecutive_loss=2,
                min_validation_samples=3,
            )

        self.assertEqual(result["status"], "optimized")
        self.assertIn("train_backtest", result)
        self.assertIn("validation_backtest", result)
        self.assertGreaterEqual(result["validation_backtest"]["win_rate"], 0.70)
        last_history = writes["strategy_version.json"]["history"][-1]
        self.assertIn("train_backtest", last_history)
        self.assertIn("validation_backtest", last_history)

    def test_optimize_balance_rejects_candidate_when_latest_validation_fails(self):
        config = {
            "version": "1.0.0",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.15},
                "F3_technical_pattern": {"weight": 0.2},
                "F4_tail_rally_strength": {"weight": 0.15},
                "F5_sector_heat": {"weight": 0.1},
                "F6_news_catalyst": {"weight": 0.1},
                "F7_float_mv_fit": {"weight": 0.1},
            },
            "selection": {
                "score_threshold": 70,
                "min_factor_scores": {"F2_volume_price_sync": 90},
                "max_factor_scores": {},
            },
            "optimization": {},
        }
        samples = []
        for idx in range(12):
            samples.append({
                "date": f"2026-06-{idx + 1:02d}",
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 80,
                        "F2_volume_price_sync": 65,
                        "F3_technical_pattern": 80,
                        "F4_tail_rally_strength": 75,
                        "F5_sector_heat": 50,
                        "F6_news_catalyst": 50,
                        "F7_float_mv_fit": 40,
                    },
                    "return": -0.01 if idx >= 9 else 0.02,
                }],
            })

        def fake_load(path):
            name = Path(path).name
            if name == "strategy_params.json":
                return json.loads(json.dumps(config))
            if name == "strategy_samples.json":
                return {"samples": samples}
            if name == "strategy_version.json":
                return {"version": "1.0.0", "history": []}
            if name == "trades.json":
                return {"trades": []}
            return {}

        with mock.patch.object(self.optimizer, "_load_json", side_effect=fake_load), \
                mock.patch.object(self.optimizer, "_save_json") as save:
            result = self.optimizer.optimize_balance(
                min_participation=0.70,
                max_participation=1.0,
                min_win_rate=0.70,
                max_consecutive_loss=3,
                min_validation_samples=3,
            )

        self.assertEqual(result["status"], "rolled_back")
        self.assertIn("最近验证段", result["reason"])
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
