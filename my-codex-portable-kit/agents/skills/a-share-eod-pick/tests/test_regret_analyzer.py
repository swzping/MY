import importlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class RegretAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.regret_analyzer = importlib.import_module("regret_analyzer")

    def test_analyze_regret_reports_oracle_gap_and_hit_rates(self):
        config = {
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
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {"F1_tail_fund_inflow": 90, "F2_volume_price_sync": 50},
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 80, "F2_volume_price_sync": 50},
                        "return": 0.05,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {"F1_tail_fund_inflow": 95, "F2_volume_price_sync": 50},
                        "return": 0.04,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {"F1_tail_fund_inflow": 70, "F2_volume_price_sync": 50},
                        "return": -0.02,
                    },
                ],
            },
        ]

        result = self.regret_analyzer.analyze_regret(samples, config)

        self.assertEqual(result["days"], 2)
        self.assertEqual(result["trade_days"], 2)
        self.assertEqual(result["exact_best_hits"], 1)
        self.assertEqual(result["exact_best_hit_rate"], 0.5)
        self.assertEqual(result["avg_regret"], 0.02)
        self.assertEqual(result["total_regret"], 0.04)
        self.assertEqual(result["avg_oracle_return"], 0.045)
        self.assertEqual(result["avg_selected_return"], 0.025)
        self.assertEqual(result["top_misses"][0]["date"], "2026-06-01")
        self.assertEqual(result["top_misses"][0]["oracle_symbol"], "600002")

    def test_analyze_regret_counts_oracle_rule_blockers(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F1_tail_fund_inflow": 90},
            },
        }
        samples = [
            {
                "date": "2026-06-01",
                "candidate_pool": [
                    {
                        "symbol": "600001",
                        "factor_scores": {"F1_tail_fund_inflow": 95, "F2_volume_price_sync": 60},
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 80, "F2_volume_price_sync": 80},
                        "return": 0.01,
                    },
                ],
            }
        ]

        result = self.regret_analyzer.analyze_regret(samples, config)

        self.assertEqual(result["oracle_blockers"]["F2_volume_price_sync<min"], 1)
        self.assertEqual(result["oracle_blockers"]["F1_tail_fund_inflow>max"], 1)
        self.assertEqual(result["top_misses"][0]["oracle_blockers"], [
            "F2_volume_price_sync<min",
            "F1_tail_fund_inflow>max",
        ])

    def test_analyze_regret_marks_oracle_rescue_eligibility(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.2},
                "F2_volume_price_sync": {"weight": 0.2},
                "F3_technical_pattern": {"weight": 0.4},
                "F7_float_mv_fit": {"weight": 0.2},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {},
                "counterfactual_rescue": {
                    "enabled": True,
                    "rescue_score_threshold": 70,
                    "max_blockers": 2,
                    "min_rescue_score_advantage": 50,
                    "rescue_min_factor_scores": {
                        "F3_technical_pattern": 80,
                        "F7_float_mv_fit": 60,
                    },
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
                            "F1_tail_fund_inflow": 85,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 90,
                            "F7_float_mv_fit": 80,
                        },
                        "return": 0.05,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 65,
                            "F7_float_mv_fit": 70,
                        },
                        "return": 0.01,
                    },
                ],
            }
        ]

        result = self.regret_analyzer.analyze_regret(samples, config)

        self.assertEqual(result["oracle_rescue_eligible"], 1)
        self.assertEqual(result["oracle_blockers"]["rescue_eligible"], 1)
        self.assertTrue(result["top_misses"][0]["oracle_rescue_eligible"])

    def test_analyze_regret_honors_persisted_neighbor_rescue_memory(self):
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

        result = self.regret_analyzer.analyze_regret(samples, config)

        self.assertEqual(result["days"], 3)
        self.assertEqual(result["trade_days"], 1)
        self.assertEqual(result["exact_best_hits"], 1)
        self.assertEqual(result["exact_best_hit_rate"], 0.3333)
        self.assertEqual(result["avg_selected_return"], -0.03)

    def test_analyze_blocker_combo_regret_ranks_cumulative_opportunity_loss(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F7_float_mv_fit": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F7_float_mv_fit": 70},
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
                            "F7_float_mv_fit": 80,
                        },
                        "return": 0.08,
                    }
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 92,
                            "F2_volume_price_sync": 80,
                            "F7_float_mv_fit": 85,
                        },
                        "return": 0.04,
                    }
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 91,
                            "F2_volume_price_sync": 60,
                            "F7_float_mv_fit": 50,
                        },
                        "return": 0.03,
                    }
                ],
            },
        ]

        rows = self.regret_analyzer.analyze_blocker_combo_regret(samples, config)

        self.assertEqual(rows[0]["blockers"], [
            "F2_volume_price_sync<min",
            "F7_float_mv_fit>max",
        ])
        self.assertEqual(rows[0]["miss_days"], 1)
        self.assertEqual(rows[0]["total_regret"], 0.08)
        self.assertEqual(rows[0]["oracle_factor_summary"]["F1_tail_fund_inflow"]["avg"], 95.0)
        self.assertEqual(rows[0]["oracle_factor_summary"]["F7_float_mv_fit"]["avg"], 80.0)
        self.assertEqual(rows[0]["top_misses"][0]["date"], "2026-06-01")
        self.assertEqual(rows[1]["blockers"], ["F7_float_mv_fit>max"])

    def test_analyze_rescue_profile_splits_rescue_wins_and_losses(self):
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
                    }
                ],
            },
            {
                "date": "2026-07-01",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 60,
                        },
                        "return": -0.03,
                    }
                ],
            },
        ]

        result = self.regret_analyzer.analyze_rescue_profile(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
        )

        self.assertEqual(result["rescue_trades"], 2)
        self.assertEqual(result["rescue_wins"], 1)
        self.assertEqual(result["rescue_losses"], 1)
        self.assertEqual(result["win_blockers"]["F2_volume_price_sync<min"], 1)
        self.assertEqual(result["loss_blockers"]["F2_volume_price_sync<min"], 1)
        self.assertEqual(result["win_months"]["2026-06"], 1)
        self.assertEqual(result["loss_months"]["2026-07"], 1)

    def test_analyze_rescue_profile_reports_factor_and_pool_context(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.5},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.5},
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
                            "F3_technical_pattern": 80,
                        },
                        "return": 0.03,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 40,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 40,
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
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 60,
                            "F3_technical_pattern": 60,
                        },
                        "return": -0.02,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 40,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 40,
                        },
                        "return": 0.01,
                    },
                ],
            },
        ]

        result = self.regret_analyzer.analyze_rescue_profile(
            samples,
            config,
            rescue_score_threshold=60,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=True,
        )

        self.assertEqual(result["win_factor_summary"]["F1_tail_fund_inflow"]["avg"], 90.0)
        self.assertEqual(result["loss_factor_summary"]["F3_technical_pattern"]["avg"], 60.0)
        self.assertEqual(result["win_context_summary"]["candidate_pool_size"]["avg"], 2.0)
        self.assertEqual(result["loss_context_summary"]["rescue_candidate_count"]["avg"], 1.0)
        self.assertEqual(result["top_wins"][0]["candidate_pool_size"], 2)
        self.assertEqual(result["top_losses"][0]["rescue_candidate_count"], 1)

    def test_analyze_rescue_delta_reports_added_and_replaced_pick_contribution(self):
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
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                    },
                    "return": 0.04,
                }],
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
                        "return": -0.03,
                    },
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.01,
                    },
                ],
            },
        ]

        result = self.regret_analyzer.analyze_rescue_delta(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            min_rescue_score_advantage=10,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            rescue_when_base_absent_only=False,
        )

        self.assertEqual(result["changed_days"], 2)
        self.assertEqual(result["added_trade_days"], 1)
        self.assertEqual(result["replaced_trade_days"], 1)
        self.assertEqual(result["net_return_delta"], 0.0)
        self.assertEqual(result["net_regret_delta"], 0.0)
        self.assertEqual(result["worsened_days"], 1)
        self.assertEqual(result["improved_days"], 1)
        self.assertEqual(result["changed_rows"][0]["change_type"], "replaced")
        self.assertEqual(result["changed_rows"][0]["return_delta"], -0.04)

    def test_analyze_rescue_delta_can_require_minimum_score_rank(self):
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
        samples = [{
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
                    "symbol": "600002",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 70,
                        "F2_volume_price_sync": 80,
                    },
                    "return": 0.01,
                },
            ],
        }]

        result = self.regret_analyzer.analyze_rescue_delta(
            samples,
            config,
            rescue_score_threshold=70,
            max_blockers=1,
            allowed_blocker_prefixes=("F2_volume_price_sync<min",),
            required_blocker_prefixes=("F2_volume_price_sync<min",),
            min_rescue_score_rank=2,
        )

        self.assertEqual(result["changed_days"], 0)

    def test_analyze_rescue_delta_segments_groups_rank_and_factor_bins(self):
        delta = {
            "changed_rows": [
                {
                    "change_type": "added",
                    "return_delta": 0.04,
                    "regret_delta": -0.04,
                    "rescue_score_rank": 1,
                    "rescue_factor_scores": {"F7_float_mv_fit": 96},
                },
                {
                    "change_type": "added",
                    "return_delta": -0.01,
                    "regret_delta": 0.01,
                    "rescue_score_rank": 4,
                    "rescue_factor_scores": {"F7_float_mv_fit": 74},
                },
                {
                    "change_type": "replaced",
                    "return_delta": -0.03,
                    "regret_delta": 0.03,
                    "rescue_score_rank": 9,
                    "rescue_factor_scores": {"F7_float_mv_fit": 88},
                },
            ]
        }

        result = self.regret_analyzer.analyze_rescue_delta_segments(
            delta,
            factor_keys=("F7_float_mv_fit",),
            factor_bins=(70, 80, 90),
        )

        self.assertEqual(result["change_type"][0]["segment"], "added")
        self.assertEqual(result["change_type"][0]["net_return_delta"], 0.03)
        self.assertEqual(result["change_type"][1]["segment"], "replaced")
        self.assertEqual(result["change_type"][1]["net_return_delta"], -0.03)
        self.assertEqual(result["rank_bucket"][0]["segment"], "1")
        self.assertEqual(result["rank_bucket"][0]["net_regret_delta"], -0.04)
        f7_segments = result["factor_bins"]["F7_float_mv_fit"]
        self.assertEqual(f7_segments[0]["segment"], "70-80")
        self.assertEqual(f7_segments[-1]["segment"], "90+")
        self.assertEqual(f7_segments[-1]["improved_days"], 1)

    def test_analyze_rescue_experiments_ranks_validation_regret_improvement(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F7_float_mv_fit": {"weight": 0.0},
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
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F7_float_mv_fit": 80},
                    "return": 0.04,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [{
                    "symbol": "600002",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F7_float_mv_fit": 80},
                    "return": 0.05,
                }],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {"F1_tail_fund_inflow": 90, "F7_float_mv_fit": 80},
                        "return": -0.03,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {"F1_tail_fund_inflow": 80, "F7_float_mv_fit": 80},
                        "return": 0.05,
                    },
                ],
            },
        ]
        experiments = [
            {
                "name": "f7_empty_only",
                "params": {
                    "rescue_score_threshold": 70,
                    "max_blockers": 1,
                    "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                    "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                    "rescue_when_base_absent_only": True,
                },
            }
        ]

        result = self.regret_analyzer.analyze_rescue_experiments(
            samples,
            config,
            experiments,
            validation_ratio=1 / 3,
        )

        row = result["experiments"][0]
        self.assertEqual(row["name"], "f7_empty_only")
        self.assertEqual(row["full"]["total_regret_delta"], -0.06)
        self.assertEqual(row["validation"]["total_regret_delta"], 0.03)
        self.assertEqual(row["decision"], "reject_validation_regret")

    def test_format_rescue_experiment_summary_reports_rejected_candidate(self):
        summary = {
            "experiments": [
                {
                    "name": "f7_empty_only",
                    "decision": "reject_validation_regret",
                    "full": {
                        "changed_days": 10,
                        "total_regret_delta": -0.05,
                        "total_return_delta": 0.04,
                    },
                    "validation": {
                        "changed_days": 2,
                        "total_regret_delta": 0.03,
                        "total_return_delta": -0.03,
                    },
                }
            ]
        }

        text = self.regret_analyzer.format_rescue_experiment_summary("F7救援实验", summary)

        self.assertIn("F7救援实验", text)
        self.assertIn("f7_empty_only", text)
        self.assertIn("reject_validation_regret", text)
        self.assertIn("验证regret", text)

    def test_analyze_rescue_experiments_accepts_factor_ceiling_sub_bucket(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F7_float_mv_fit": {"weight": 0.0},
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
                "candidate_pool": [{
                    "symbol": "600001",
                    "factor_scores": {"F1_tail_fund_inflow": 90, "F7_float_mv_fit": 85},
                    "return": 0.04,
                }],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600002",
                        "factor_scores": {"F1_tail_fund_inflow": 90, "F7_float_mv_fit": 95},
                        "return": -0.03,
                    },
                    {
                        "symbol": "600003",
                        "factor_scores": {"F1_tail_fund_inflow": 80, "F7_float_mv_fit": 95},
                        "return": 0.02,
                    },
                ],
            },
        ]
        experiments = [
            {
                "name": "f7_no_ceiling",
                "params": {
                    "rescue_score_threshold": 70,
                    "max_blockers": 1,
                    "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                    "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                    "rescue_when_base_absent_only": True,
                },
            },
            {
                "name": "f7_cap_90",
                "params": {
                    "rescue_score_threshold": 70,
                    "max_blockers": 1,
                    "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                    "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                    "rescue_when_base_absent_only": True,
                    "rescue_max_factor_scores": {"F7_float_mv_fit": 90},
                },
            },
        ]

        result = self.regret_analyzer.analyze_rescue_experiments(
            samples,
            config,
            experiments,
            validation_ratio=0.5,
        )

        by_name = {row["name"]: row for row in result["experiments"]}
        self.assertEqual(by_name["f7_no_ceiling"]["decision"], "reject_validation_regret")
        self.assertEqual(by_name["f7_cap_90"]["decision"], "reject_no_validation_signal")
        self.assertEqual(by_name["f7_cap_90"]["full"]["total_regret_delta"], -0.04)

    def test_analyze_high_return_miss_segments_groups_major_regret_by_context(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F7_float_mv_fit": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "min_factor_scores": {"F2_volume_price_sync": 70},
                "max_factor_scores": {"F7_float_mv_fit": 80},
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
                            "F7_float_mv_fit": 70,
                        },
                        "return": 0.08,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 80,
                            "F7_float_mv_fit": 70,
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
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 80,
                            "F7_float_mv_fit": 90,
                        },
                        "return": 0.07,
                    }
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 75,
                            "F2_volume_price_sync": 80,
                            "F7_float_mv_fit": 70,
                        },
                        "return": 0.02,
                    }
                ],
            },
        ]

        result = self.regret_analyzer.analyze_high_return_miss_segments(
            samples,
            config,
            min_oracle_return=0.05,
        )

        self.assertEqual(result["major_miss_days"], 2)
        self.assertEqual(result["total_major_regret"], 0.14)
        self.assertEqual(result["by_miss_type"][0]["segment"], "empty")
        self.assertEqual(result["by_miss_type"][0]["total_regret"], 0.07)
        self.assertEqual(result["by_miss_type"][1]["segment"], "replacement")
        self.assertEqual(result["by_miss_type"][1]["total_regret"], 0.07)
        self.assertEqual(result["by_oracle_rank"][0]["segment"], "1")
        self.assertEqual(result["by_blocker_combo"][0]["segment"], "F2_volume_price_sync<min")
        self.assertEqual(result["top_misses"][0]["date"], "2026-06-01")

    def test_analyze_replacement_decoy_profile_compares_selected_to_oracle(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F9_overheat_control": {"weight": 0.0},
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
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 80,
                            "F9_overheat_control": 95,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 60,
                            "F9_overheat_control": 40,
                        },
                        "return": 0.08,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F2_volume_price_sync": 80,
                            "F9_overheat_control": 90,
                        },
                        "return": -0.01,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 70,
                            "F2_volume_price_sync": 65,
                            "F9_overheat_control": 50,
                        },
                        "return": 0.07,
                    },
                ],
            },
            {
                "date": "2026-06-03",
                "candidate_pool": [
                    {
                        "symbol": "600005",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 85,
                            "F2_volume_price_sync": 80,
                            "F9_overheat_control": 80,
                        },
                        "return": 0.02,
                    }
                ],
            },
        ]

        result = self.regret_analyzer.analyze_replacement_decoy_profile(
            samples,
            config,
            min_oracle_return=0.05,
        )

        self.assertEqual(result["replacement_miss_days"], 2)
        self.assertEqual(result["total_replacement_regret"], 0.15)
        self.assertEqual(result["avg_rank_delta"], -1.0)
        self.assertEqual(result["decoy_minus_oracle_factor_delta"]["F1_tail_fund_inflow"]["avg"], 17.5)
        self.assertEqual(result["decoy_minus_oracle_factor_delta"]["F9_overheat_control"]["avg"], 47.5)
        self.assertEqual(result["top_decoys"][0]["date"], "2026-06-02")
        self.assertEqual(result["top_decoys"][0]["return_delta"], -0.08)

    def test_analyze_oracle_context_profile_reports_cross_sectional_regime(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 0.0},
                "F9_overheat_control": {"weight": 1.0},
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
                            "F1_tail_fund_inflow": 100,
                            "F9_overheat_control": 30,
                        },
                        "return": 0.08,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 90,
                            "F9_overheat_control": 40,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 10,
                            "F9_overheat_control": 95,
                        },
                        "return": 0.0,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 20,
                            "F9_overheat_control": 90,
                        },
                        "return": -0.01,
                    },
                ],
            },
            {
                "date": "2026-06-02",
                "candidate_pool": [
                    {
                        "symbol": "600005",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F9_overheat_control": 80,
                        },
                        "return": 0.02,
                    }
                ],
            },
        ]

        result = self.regret_analyzer.analyze_oracle_context_profile(
            samples,
            config,
            min_oracle_return=0.05,
            strong_f1_threshold=80,
            low_f9_threshold=50,
        )

        self.assertEqual(result["context_days"], 1)
        self.assertEqual(result["avg_candidate_pool_size"], 4.0)
        self.assertEqual(result["avg_oracle_f1_percentile"], 1.0)
        self.assertEqual(result["avg_oracle_f9_percentile"], 0.25)
        self.assertEqual(result["avg_strong_f1_low_f9_share"], 0.5)
        self.assertEqual(result["by_strong_low_heat_share"][0]["segment"], ">=40%")
        self.assertEqual(result["top_contexts"][0]["date"], "2026-06-01")

    def test_analyze_miss_factor_deltas_compares_oracle_to_selected_pick(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.0},
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
                            "F3_technical_pattern": 60,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600002",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 70,
                            "F3_technical_pattern": 90,
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
                            "F1_tail_fund_inflow": 95,
                            "F2_volume_price_sync": 50,
                            "F3_technical_pattern": 50,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600004",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 85,
                            "F2_volume_price_sync": 80,
                            "F3_technical_pattern": 70,
                        },
                        "return": 0.04,
                    },
                ],
            },
        ]

        result = self.regret_analyzer.analyze_miss_factor_deltas(samples, config)

        self.assertEqual(result["miss_days"], 2)
        self.assertEqual(result["oracle_factor_summary"]["F2_volume_price_sync"]["avg"], 75.0)
        self.assertEqual(result["selected_factor_summary"]["F2_volume_price_sync"]["avg"], 50.0)
        self.assertEqual(result["delta_summary"]["F2_volume_price_sync"]["avg"], 25.0)
        self.assertEqual(result["delta_summary"]["F3_technical_pattern"]["avg"], 25.0)
        self.assertEqual(result["top_positive_deltas"][0]["factor"], "F2_volume_price_sync")
        self.assertEqual(result["empty_miss_factor_summary"], {})

    def test_analyze_miss_factor_deltas_splits_empty_and_replacement_misses(self):
        config = {
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 70,
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
                            "F1_tail_fund_inflow": 60,
                            "F2_volume_price_sync": 90,
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
                            "F2_volume_price_sync": 50,
                        },
                        "return": 0.01,
                    },
                    {
                        "symbol": "600003",
                        "factor_scores": {
                            "F1_tail_fund_inflow": 80,
                            "F2_volume_price_sync": 80,
                        },
                        "return": 0.04,
                    },
                ],
            },
        ]

        result = self.regret_analyzer.analyze_miss_factor_deltas(samples, config)

        self.assertEqual(result["empty_miss_days"], 1)
        self.assertEqual(result["replacement_miss_days"], 1)
        self.assertEqual(result["empty_miss_factor_summary"]["F2_volume_price_sync"]["avg"], 90.0)
        self.assertEqual(result["replacement_delta_summary"]["F2_volume_price_sync"]["avg"], 30.0)

    def test_format_rescue_delta_segments_prints_key_profit_buckets(self):
        segments = {
            "change_type": [
                {
                    "segment": "added",
                    "days": 3,
                    "improved_days": 2,
                    "worsened_days": 1,
                    "net_return_delta": 0.03,
                    "net_regret_delta": -0.03,
                }
            ],
            "rank_bucket": [
                {
                    "segment": "6+",
                    "days": 2,
                    "improved_days": 1,
                    "worsened_days": 1,
                    "net_return_delta": -0.01,
                    "net_regret_delta": 0.01,
                }
            ],
            "factor_bins": {
                "F9_overheat_control": [
                    {
                        "segment": "80-90",
                        "days": 1,
                        "improved_days": 1,
                        "worsened_days": 0,
                        "net_return_delta": 0.02,
                        "net_regret_delta": -0.02,
                    }
                ]
            },
        }

        text = self.regret_analyzer.format_rescue_delta_segments(
            "F2+F9 rank-floor",
            segments,
        )

        self.assertIn("F2+F9 rank-floor", text)
        self.assertIn("change_type added", text)
        self.assertIn("rank 6+", text)
        self.assertIn("F9_overheat_control 80-90", text)


if __name__ == "__main__":
    unittest.main()
