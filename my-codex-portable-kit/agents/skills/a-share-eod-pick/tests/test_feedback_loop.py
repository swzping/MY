import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class FeedbackLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

        self.feedback_loop = importlib.import_module("feedback_loop")
        self.feedback_loop.DATA_DIR = self.base / "data"
        self.feedback_loop.FEEDBACK_DIR = self.feedback_loop.DATA_DIR / "feedback"
        self.feedback_loop.CONFIG_PATH = self.base / "config" / "strategy_params.json"
        self.feedback_loop.TRADES_PATH = self.feedback_loop.DATA_DIR / "trades.json"
        self.feedback_loop.SAMPLE_POOL_PATH = self.feedback_loop.DATA_DIR / "strategy_samples.json"
        self.feedback_loop.ADJUSTMENTS_PATH = self.feedback_loop.FEEDBACK_DIR / "adjustments.json"
        self.feedback_loop.SNAPSHOTS_PATH = self.feedback_loop.FEEDBACK_DIR / "metrics_snapshots.json"
        self.feedback_loop.ACTIONS_PATH = self.feedback_loop.FEEDBACK_DIR / "feedback_actions.json"

        self.feedback_loop.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_loop.CONFIG_PATH.write_text(
            json.dumps(
                {
                    "version": "test",
                    "risk_control": {
                        "win_rate_7d_alert": 0.5,
                        "win_rate_30d_alert": 0.55,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_samples(self, samples):
        self.feedback_loop.SAMPLE_POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_loop.SAMPLE_POOL_PATH.write_text(
            json.dumps({"samples": samples}, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_layered_metrics_split_historical_live_and_combined_with_empty_days(self):
        self.write_samples(
            [
                {
                    "date": "2026-06-20",
                    "sample_type": "historical_training",
                    "selected": True,
                    "return": 0.02,
                    "win": True,
                },
                {
                    "date": "2026-06-21",
                    "sample_type": "historical_training",
                    "selected": False,
                    "empty_reason": "score_below_threshold",
                },
                {
                    "date": "2026-06-22",
                    "sample_type": "live_paper",
                    "selected": True,
                    "return": -0.01,
                    "win": False,
                },
            ]
        )

        metrics = self.feedback_loop.compute_sample_metrics()

        self.assertEqual(metrics["historical_training"]["samples"], 2)
        self.assertEqual(metrics["historical_training"]["trade_samples"], 1)
        self.assertEqual(metrics["historical_training"]["empty_days"], 1)
        self.assertEqual(metrics["historical_training"]["empty_rate"], 0.5)
        self.assertEqual(metrics["historical_training"]["win_rate"], 1.0)
        self.assertEqual(metrics["live_paper"]["win_rate"], 0.0)
        self.assertEqual(metrics["combined"]["samples"], 3)
        self.assertEqual(metrics["combined"]["trade_samples"], 2)
        self.assertEqual(metrics["combined"]["win_rate"], 0.5)

    def test_metrics_separate_empty_days_from_skips_and_use_net_return(self):
        metrics = self.feedback_loop.compute_sample_metrics(
            [
                {"date": "2026-06-20", "sample_type": "historical_training", "selected": True, "execution_status": "filled", "gross_return": 0.012, "net_return": 0.01},
                {"date": "2026-06-21", "sample_type": "historical_training", "selected": True, "execution_status": "skipped", "skip_reason": "invalid_t1_row"},
                {"date": "2026-06-22", "sample_type": "historical_training", "selected": False, "empty_reason": "score_below_threshold"},
            ]
        )
        layer = metrics["historical_training"]

        self.assertEqual(layer["selected_days"], 2)
        self.assertEqual(layer["executable_trades"], 1)
        self.assertEqual(layer["skipped_executions"], 1)
        self.assertEqual(layer["empty_days"], 1)
        self.assertEqual(layer["net_avg_return"], 0.01)
        self.assertEqual(layer["execution_coverage"], 0.5)

    def test_collect_metrics_uses_unified_sample_pool(self):
        self.write_samples(
            [
                {
                    "date": "2026-06-20",
                    "sample_type": "historical_training",
                    "selected": True,
                    "return": 0.02,
                    "win": True,
                },
                {
                    "date": "2026-06-21",
                    "sample_type": "live_paper",
                    "selected": False,
                    "empty_reason": "no_candidate",
                },
            ]
        )
        self.feedback_loop._probe_data_sources = lambda: {"tencent": "ok"}

        sid = self.feedback_loop.collect_metrics("unit")
        snapshots = json.loads(self.feedback_loop.SNAPSHOTS_PATH.read_text(encoding="utf-8"))["snapshots"]
        snap = snapshots[0]

        self.assertEqual(sid, snap["id"])
        self.assertIn("sample_metrics", snap)
        self.assertEqual(snap["sample_metrics"]["historical_training"]["win_rate"], 1.0)
        self.assertEqual(snap["sample_metrics"]["live_paper"]["empty_rate"], 1.0)
        self.assertEqual(snap["trades_count"], 2)

    def test_compare_snapshots_reports_layered_degradation_and_live_deviation(self):
        baseline = {
            "sample_metrics": {
                "historical_training": {"win_rate": 0.60, "empty_rate": 0.10, "max_consecutive_loss": 2, "trade_samples": 30},
                "live_paper": {"win_rate": 0.55, "empty_rate": 0.10, "max_consecutive_loss": 2, "trade_samples": 10},
                "combined": {"win_rate": 0.58, "empty_rate": 0.10, "max_consecutive_loss": 2, "trade_samples": 40},
            },
            "data_sources_status": {"tencent": "ok"},
        }
        post = {
            "sample_metrics": {
                "historical_training": {"win_rate": 0.60, "empty_rate": 0.10, "max_consecutive_loss": 2, "trade_samples": 30},
                "live_paper": {"win_rate": 0.35, "empty_rate": 0.30, "max_consecutive_loss": 5, "trade_samples": 10},
                "combined": {"win_rate": 0.50, "empty_rate": 0.15, "max_consecutive_loss": 5, "trade_samples": 40},
            },
            "data_sources_status": {"tencent": "ok"},
        }

        findings = self.feedback_loop._compare_snapshots(baseline, post)
        text = "\n".join(f["finding"] for f in findings)

        self.assertIn("综合胜率下降", text)
        self.assertIn("实际执行胜率低于历史训练", text)
        self.assertIn("最大连亏扩大", text)
        self.assertIn("空仓率上升", text)
        self.assertTrue(all(f["status_hint"] == "suggestion_only" for f in findings))

    def test_main_exposes_full_feedback_loop_commands(self):
        main = importlib.import_module("main")
        for cmd in [
            "plan_optimization",
            "implement_action",
            "verify_action",
            "reject_action",
            "close_loop",
        ]:
            self.assertIn(cmd, main.COMMANDS)


class ReportFeedbackSummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.report_generator = importlib.import_module("report_generator")
        self.report_generator.DATA_DIR = self.base / "data"
        self.report_generator.REPORTS_DIR = self.base / "reports"
        self.report_generator.CONFIG_PATH = self.base / "config" / "strategy_params.json"
        self.report_generator.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.report_generator.CONFIG_PATH.write_text(
            json.dumps({"factors": {}, "risk_control": {}}, ensure_ascii=False),
            encoding="utf-8",
        )
        self.report_generator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (self.report_generator.DATA_DIR / "performance.json").write_text("{}", encoding="utf-8")
        (self.report_generator.DATA_DIR / "strategy_version.json").write_text("{}", encoding="utf-8")
        (self.report_generator.DATA_DIR / "trades.json").write_text('{"trades":[]}', encoding="utf-8")
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            '{"samples":[]}',
            encoding="utf-8",
        )
        (self.report_generator.DATA_DIR / "feedback" / "metrics_snapshots.json").parent.mkdir(
            parents=True, exist_ok=True
        )
        (self.report_generator.DATA_DIR / "feedback" / "metrics_snapshots.json").write_text(
            json.dumps(
                {
                    "snapshots": [
                        {
                            "id": "MS-test",
                            "sample_metrics": {
                                "historical_training": {
                                    "win_rate": 0.6,
                                    "samples": 10,
                                    "trade_samples": 8,
                                    "empty_rate": 0.2,
                                    "max_consecutive_loss": 2,
                                },
                                "live_paper": {
                                    "win_rate": 0,
                                    "samples": 0,
                                    "trade_samples": 0,
                                    "empty_rate": 0,
                                    "max_consecutive_loss": 0,
                                },
                                "combined": {
                                    "win_rate": 0.6,
                                    "samples": 10,
                                    "trade_samples": 8,
                                    "empty_rate": 0.2,
                                    "max_consecutive_loss": 2,
                                },
                            },
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_report_contains_feedback_summary(self):
        content = self.report_generator.render_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn("反馈闭环摘要", content)
        self.assertIn("历史训练", content)
        self.assertIn("实际执行", content)
        self.assertIn("不足以判断", content)

    def test_report_contains_strategy_diagnostics_and_candidate_experiment_summary(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-01",
                            "sample_type": "historical_training",
                            "candidate_pool": [{
                                "symbol": "600001",
                                "factor_scores": {
                                    "F1_tail_fund_inflow": 90,
                                    "F3_technical_pattern": 80,
                                    "F4_tail_rally_strength": 70,
                                    "F7_float_mv_fit": 80,
                                    "F8_overnight_risk_control": 80,
                                    "F9_overheat_control": 90,
                                },
                                "return": 0.04,
                            }],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.report_generator.CONFIG_PATH.write_text(
            json.dumps(
                {
                    "factors": {
                        "F1_tail_fund_inflow": {"weight": 1.0},
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
                    "risk_control": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator.render_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn("策略诊断与候选实验", content)
        self.assertIn("累计机会损失", content)
        self.assertIn("F7 条件救援推广门槛", content)
        self.assertIn("f7_empty_only_high_quality", content)

    def test_generate_writes_markdown_and_html_report_for_same_date(self):
        path = self.report_generator.generate(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertEqual(path.name, "2026-06-26.md")
        self.assertTrue((self.report_generator.REPORTS_DIR / "2026-06-26.md").exists())
        self.assertTrue((self.report_generator.REPORTS_DIR / "2026-06-26.html").exists())

    def test_html_report_contains_searchable_paginated_history_tables(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-24",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600001",
                            "name": "测试历史",
                            "buy_price": 10.0,
                            "sell_price": 10.2,
                            "return": 0.02,
                            "buy_price_source": "T_close",
                            "actual_best": {"symbol": "600002", "name": "最佳股", "return": 0.03},
                            "missed_best_reason": "已选测试",
                        },
                        {
                            "date": "2026-06-25",
                            "sample_type": "live_paper",
                            "selected": False,
                            "selected_at": "2026-06-25 14:50:00",
                            "empty_reason": "无超阈值",
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn('id="historySearch"', html)
        self.assertIn('id="historyPageSize"', html)
        self.assertIn('data-table="historical"', html)
        self.assertIn('data-table="live"', html)
        self.assertIn("测试历史", html)
        self.assertIn("无超阈值", html)
        self.assertIn("function renderTable", html)

    def test_html_report_contains_strategy_rule_and_parameter_explanations(self):
        self.report_generator.CONFIG_PATH.write_text(
            json.dumps(
                {
                    "factors": {
                        "F1_tail_fund_inflow": {
                            "weight": 0.2,
                            "desc": "尾盘资金净流入",
                            "calc": "main_net_1430_1500 / float_mv",
                            "score_range": [0, 100],
                        }
                    },
                    "prefilter": {"amount_min": 50000000},
                    "selection": {
                        "score_threshold": 55,
                        "market_drop_threshold": -0.02,
                        "counterfactual_rescue": {"enabled": True},
                        "neighbor_counterfactual_rescue": {
                            "enabled": True,
                            "neighbor_factor_keys": ["F1_tail_fund_inflow"],
                        },
                    },
                    "execution_model": {"buy_mode": "tail_advice"},
                    "validation": {"sell_mode": "next_open"},
                    "optimization": {"candidate_pool_size": 20},
                    "risk_control": {"max_consecutive_loss": 3},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn("策略规则与参数说明", html)
        self.assertIn("F1_tail_fund_inflow", html)
        self.assertIn("score_threshold", html)
        self.assertIn("counterfactual_rescue", html)
        self.assertIn("neighbor_counterfactual_rescue", html)
        self.assertIn("market_drop_threshold", html)

    def test_html_report_places_decision_overview_above_history_table(self):
        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {"sh_pct": -0.021, "source": "unit"},
                "empty_reason": "上证跌幅超过阈值，空仓",
                "errors": [],
            }
        )

        self.assertIn("决策总览", html)
        self.assertIn("今日买入外部影响风险说明", html)
        self.assertIn("市场行情", html)
        self.assertLess(html.index("决策总览"), html.index("完整历史训练记录"))

    def test_html_report_uses_dashboard_ux_and_accessibility_details(self):
        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn("quick-filter", html)
        self.assertIn("收益为正", html)
        self.assertIn("收益为负", html)
        self.assertIn("aria-label=\"搜索完整历史训练记录\"", html)
        self.assertIn("@media (prefers-reduced-motion: reduce)", html)
        self.assertIn("function decorateReturn", html)

    def test_html_report_shows_filter_count_badges(self):
        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn('class="filter-count"', html)
        self.assertIn("function updateFilterCounts", html)
        self.assertIn("data-count-for=\"win\"", html)
        self.assertIn("aria-live=\"polite\"", html)

    def test_html_report_filters_buy_source_and_uses_readable_source_labels(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-24",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600001",
                            "name": "来源测试",
                            "buy_price": 10.0,
                            "sell_price": 10.1,
                            "return": 0.01,
                            "buy_price_source": "T_tail_advice_proxy_no_minutes",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn("尾盘建议价", html)
        self.assertNotIn("T_tail_advice_proxy_no_minutes", html)
        self.assertIn('id="historySourceFilter"', html)
        self.assertIn("function matchesSourceFilter", html)

    def test_html_report_shows_opportunity_loss_and_rule_score_details(self):
        self.report_generator.CONFIG_PATH.write_text(
            json.dumps(
                {
                    "factors": {
                        "F2_volume_price_sync": {"desc": "量价协同"},
                    },
                    "selection": {
                        "min_factor_scores": {"F2_volume_price_sync": 70},
                        "max_factor_scores": {},
                    },
                    "risk_control": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-24",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600001",
                            "name": "已选股",
                            "buy_price": 10.0,
                            "sell_price": 10.1,
                            "return": 0.01,
                            "buy_price_source": "T_close",
                            "actual_best": {
                                "symbol": "600002",
                                "name": "实际最优",
                                "return": 0.03,
                                "factor_scores": {"F2_volume_price_sync": 52.55},
                            },
                            "missed_best_reason": "次日实际最优未过当日规则：F2_volume_price_sync低于70",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        html = self.report_generator.render_html_report(
            {
                "date": "2026-06-26",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "unit",
                "errors": [],
            }
        )

        self.assertIn("机会损失", html)
        self.assertIn("+2.00%", html)
        self.assertIn("未过规则", html)
        self.assertIn("量价协同 52.55 / 70.00", html)
        self.assertIn("差 17.45", html)
        self.assertNotIn("F2_volume_price_sync低于70", html)


if __name__ == "__main__":
    unittest.main()
