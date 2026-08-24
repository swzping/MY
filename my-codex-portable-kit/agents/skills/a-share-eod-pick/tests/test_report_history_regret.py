import importlib
import datetime as real_datetime
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
REAL_DATETIME = real_datetime.datetime


class ReportHistoryRegretTests(unittest.TestCase):
    def setUp(self):
        self.report_generator = importlib.import_module("report_generator")

    def test_history_table_shows_daily_regret_and_best_hit(self):
        samples = [
            {
                "date": "2026-06-24",
                "sample_type": "historical_training",
                "selected": True,
                "symbol": "600001",
                "name": "已选",
                "buy_price": 10.0,
                "sell_price": 10.1,
                "buy_price_source": "T_close",
                "return": 0.01,
                "actual_best": {"symbol": "600002", "name": "最优", "return": 0.05},
                "missed_best_reason": "同日排序规则优先选择了已选标的",
            },
            {
                "date": "2026-06-25",
                "sample_type": "historical_training",
                "selected": True,
                "symbol": "600003",
                "name": "命中",
                "buy_price": 11.0,
                "sell_price": 11.55,
                "buy_price_source": "T_close",
                "return": 0.05,
                "actual_best": {"symbol": "600003", "name": "命中", "return": 0.05},
                "missed_best_reason": "已选中次日实际最优",
            },
        ]

        with mock.patch.object(self.report_generator, "_load_strategy_samples", return_value=samples), \
                mock.patch.object(self.report_generator, "_load_trades", return_value=[]):
            output = self.report_generator._render_history([])

        self.assertIn("机会损失", output)
        self.assertIn("命中最优", output)
        self.assertIn("4.00%", output)
        self.assertIn("未命中", output)
        self.assertIn("命中", output)

    def test_empty_html_report_does_not_show_buy_timing_advice(self):
        selection_result = {
            "date": "2026-06-29",
            "recommendations": [],
            "empty_reason": "今日无满足阈值的推荐，空仓观望。",
            "market_overview": {
                "sh_pct": -0.0015,
                "sz_pct": 0.0062,
                "cy_pct": 0.0129,
                "limit_up_count": 54,
                "limit_down_count": 6,
                "source": "tencent",
            },
        }
        config = {
            "version": "v-test",
            "execution_advice": {
                "window_start": "14:40",
                "window_end": "14:55",
                "give_up_condition": "14:50后冲到全天高位附近且承接转弱",
            },
            "execution_revisit": {
                "enabled": True,
                "early_entry_threshold_score": 88,
                "checkpoints": ["10:00", "13:00", "14:00", "14:15", "14:40"],
            },
            "selection": {},
            "factors": {},
        }
        perf = {"total": {"max_consecutive_loss": 2, "samples": 102}}

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_performance", return_value=perf), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_history_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_live_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_render_alerts", return_value=""), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]):
            output = self.report_generator.render_html_report(selection_result)

        self.assertIn("不买入，继续观察", output)
        self.assertIn("空仓触发原因", output)
        self.assertNotIn("建议继续等尾盘买入", output)

    def test_empty_html_report_collapses_secondary_diagnostics(self):
        watchlist = [
            {
                "symbol": f"60000{i}",
                "name": f"观察{i}",
                "score": 42 + i / 10,
                "sector": "测试行业",
                "block_reason": "F9_overheat_control低于85",
                "F2_volume_price_sync": 20,
                "F3_technical_pattern": 75,
                "F8_overnight_risk_control": 50,
            }
            for i in range(1, 6)
        ]
        selection_result = {
            "date": "2026-06-29",
            "recommendations": [],
            "empty_reason": "今日无满足阈值的推荐，空仓观望。",
            "runtime_overrides": {
                "F2_volume_price_sync_min": {"before": 65, "after": 20},
                "score_threshold": {"before": 55, "after": 40},
                "F8_overnight_risk_control_min": {"before": 70, "after": 50},
                "F9_overheat_control_min": {"before": 85, "after": 80},
            },
            "selection_diagnostics": {
                "total_scored": 50,
                "below_score_threshold": 39,
                "guardrail_blockers": {
                    "F3_technical_pattern低于70": 31,
                    "F9_overheat_control低于85": 19,
                },
                "error_counts": {"fund_flow": 50},
            },
            "watchlist": watchlist,
            "market_overview": {"sh_pct": 0.0017, "source": "tencent"},
        }
        config = {
            "version": "v-test",
            "execution_revisit": {"enabled": True, "checkpoints": ["10:00", "13:00", "14:40"]},
            "selection": {},
            "factors": {},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_history_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_live_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_render_alerts", return_value=""), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]):
            output = self.report_generator.render_html_report(selection_result)

        self.assertIn("主要阻挡", output)
        self.assertIn("观察池 Top5", output)
        self.assertIn("<details class=\"empty-diagnostics-detail\">", output)
        self.assertIn("完整诊断与参数覆盖", output)
        self.assertIn("F9_overheat_control_min", output)
        self.assertIn("85 → 80", output)
        self.assertIn("600001", output)
        self.assertIn("600005", output)

    def test_empty_markdown_report_does_not_show_buy_timing_advice(self):
        selection_result = {
            "date": "2026-06-29",
            "recommendations": [],
            "empty_reason": "今日无满足阈值的推荐，空仓观望。",
            "market_overview": {"sh_pct": -0.0015},
            "runtime_overrides": {
                "F2_volume_price_sync_min": {"before": 65, "after": 50},
            },
            "selection_diagnostics": {
                "total_scored": 50,
                "below_score_threshold": 40,
                "guardrail_blockers": {"F2_volume_price_sync低于50": 35},
                "error_counts": {"fund_flow": 50},
            },
            "watchlist": [
                {
                    "symbol": "600001",
                    "name": "观察A",
                    "score": 54.2,
                    "sector": "测试行业",
                    "block_reason": "F2_volume_price_sync低于50",
                    "F2_volume_price_sync": 48.0,
                    "F3_technical_pattern": 80.0,
                    "F8_overnight_risk_control": 75.0,
                }
            ],
        }
        config = {
            "version": "v-test",
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["14:40"]},
            "selection": {},
            "factors": {},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_trades", return_value=[]), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_load_strategy_samples", return_value=[]), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]):
            output = self.report_generator.render_report(selection_result)

        self.assertIn("### 空仓触发原因", output)
        self.assertIn("动作：不买入，继续观察", output)
        self.assertIn("本次参数覆盖", output)
        self.assertIn("F2_volume_price_sync_min：65 → 50", output)
        self.assertIn("空仓诊断", output)
        self.assertIn("F2_volume_price_sync低于50：35只", output)
        self.assertIn("观察池 Top", output)
        self.assertIn("600001", output)
        self.assertNotIn("建议继续等尾盘买入", output)

    def test_recommendation_report_uses_runtime_thresholds_for_execution_advice(self):
        selection_result = {
            "date": "2026-06-29",
            "recommendations": [
                {
                    "symbol": "000417",
                    "name": "合百集团",
                    "score": 42.5,
                    "sector": "一般零售",
                    "factor_scores": {
                        "F2_volume_price_sync": 20.0,
                        "F3_technical_pattern": 77.0,
                        "F8_overnight_risk_control": 50.0,
                        "F9_overheat_control": 50.0,
                    },
                }
            ],
            "market_overview": {"sh_pct": 0.001},
            "runtime_overrides": {
                "F2_volume_price_sync_min": {"before": 65, "after": 20},
                "score_threshold": {"before": 55, "after": 40},
                "F8_overnight_risk_control_min": {"before": 70, "after": 50},
                "F9_overheat_control_min": {"before": 85, "after": 30},
            },
        }
        config = {
            "version": "v-test",
            "factors": {
                "F2_volume_price_sync": {"weight": 0.1, "desc": "量价协同"},
                "F3_technical_pattern": {"weight": 0.1, "desc": "技术形态"},
                "F8_overnight_risk_control": {"weight": 0.1, "desc": "隔夜追高风险控制"},
                "F9_overheat_control": {"weight": 0.1, "desc": "过热控制"},
            },
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F3_technical_pattern": 70,
                    "F8_overnight_risk_control": 70,
                    "F9_overheat_control": 85,
                },
                "max_factor_scores": {},
            },
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "early_entry_threshold_score": 88, "checkpoints": ["14:40"]},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_trades", return_value=[]), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_load_strategy_samples", return_value=[]), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]):
            output = self.report_generator.render_report(selection_result)

        self.assertIn("推荐1：000417 合百集团", output)
        self.assertNotIn("F2_volume_price_sync低于65.00", output)
        self.assertNotIn("F8_overnight_risk_control低于70.00", output)
        self.assertNotIn("F9_overheat_control低于85.00", output)
        self.assertNotIn("F2_volume_price_sync(20.00)低于阈值65", output)
        self.assertIn("分数未满足提前触发条件", output)

    def test_html_report_surfaces_intraday_buy_now_signal_as_primary_decision(self):
        selection_result = {
            "date": "2026-06-29",
            "recommendations": [
                {
                    "symbol": "000417",
                    "name": "合百集团",
                    "score": 42.5,
                    "sector": "一般零售",
                    "factor_scores": {},
                }
            ],
            "opportunity_signals": [
                {
                    "symbol": "600867",
                    "name": "通化东宝",
                    "score": 46,
                    "opportunity_score": 84.2,
                    "sector": "生物制品",
                    "action": "BUY_NOW",
                    "action_label": "现在可买",
                    "strategy_case": "intraday_attack",
                    "case_label": "盘中机会",
                    "entry_price_source": "current_price",
                    "next_check_at": "",
                    "reasons": ["午后放量加速", "板块联动较强"],
                    "risks": ["距涨停仍有空间，避免回落追高"],
                }
            ],
            "watchlist": [
                {
                    "symbol": "600867",
                    "name": "通化东宝",
                    "score": 46,
                    "sector": "生物制品",
                    "block_reason": "盘中机会观察",
                }
            ],
            "market_overview": {"sh_pct": 0.006, "source": "tencent"},
        }
        config = {
            "version": "v-test",
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["13:00", "14:00", "14:40"]},
            "selection": {},
            "factors": {},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_history_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_live_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_render_alerts", return_value=""), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]):
            output = self.report_generator.render_html_report(selection_result)

        self.assertIn("现在可买", output)
        self.assertIn("600867 通化东宝", output)
        self.assertIn("盘中机会", output)
        self.assertIn("午后放量加速", output)
        self.assertIn("尾盘隔夜推荐", output)
        self.assertIn("000417 合百集团", output)

    def test_html_report_shows_tail_confirm_as_executable_inside_tail_window(self):
        selection_result = {
            "date": "2026-06-29",
            "recommendations": [],
            "opportunity_signals": [
                {
                    "symbol": "600109",
                    "name": "国金证券",
                    "score": 40.8,
                    "opportunity_score": 51.32,
                    "sector": "证券 II",
                    "action": "TAIL_CONFIRM",
                    "strategy_case": "tail_confirm",
                    "entry_price_source": "tail_advice_price",
                    "next_check_at": "",
                    "reasons": ["板块热度较强"],
                    "risks": ["未触发明显风险"],
                }
            ],
            "market_overview": {"sh_pct": 0.006, "source": "tencent"},
        }
        config = {
            "version": "v-test",
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["13:00", "14:00", "14:40"]},
            "validation": {"sell_mode": "next_open"},
            "selection": {},
            "factors": {},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_history_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_live_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_render_alerts", return_value=""), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]), \
                mock.patch.object(self.report_generator.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 14, 45)
            output = self.report_generator.render_html_report(selection_result)

        self.assertIn("尾盘可执行", output)
        self.assertIn("当前动作：尾盘可执行", output)

    def test_html_report_uses_selection_decision_time_for_next_check_display(self):
        selection_result = {
            "date": "2026-06-29",
            "decision_time": "2026-06-29 14:57:00",
            "recommendations": [],
            "opportunity_signals": [
                {
                    "symbol": "600918",
                    "name": "中泰证券",
                    "score": 40.47,
                    "opportunity_score": 53.1,
                    "sector": "证券 II",
                    "action": "TAIL_CONFIRM",
                    "strategy_case": "tail_confirm",
                    "entry_price_source": "tail_advice_price",
                    "next_check_at": "",
                    "decision_time": "2026-06-29 14:57:00",
                    "reasons": ["已过建议窗口但仍在收盘前，按实时盘面做最后确认"],
                    "risks": ["未触发明显风险"],
                }
            ],
            "market_overview": {"sh_pct": 0.006, "source": "tencent"},
        }
        config = {
            "version": "v-test",
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["13:00", "14:00", "14:40"]},
            "validation": {"sell_mode": "next_open"},
            "selection": {},
            "factors": {},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_history_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_live_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_render_alerts", return_value=""), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]), \
                mock.patch.object(self.report_generator.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 13, 20)
            output = self.report_generator.render_html_report(selection_result)

        self.assertIn("收盘前确认", output)
        self.assertNotIn("下一复核：14:40", output)
        self.assertNotIn("14:40 已过", output)

    def test_html_report_surfaces_oracle_hit_and_regret_metrics(self):
        selection_result = {
            "date": "2026-06-30",
            "recommendations": [],
            "opportunity_signals": [],
            "market_overview": {"sh_pct": 0.002, "source": "tencent"},
        }
        samples = [
            {
                "date": "2026-06-24",
                "sample_type": "historical_training",
                "selected": False,
                "actual_best": {"symbol": "600001", "return": 0.04},
                "candidate_pool": [
                    {"symbol": "600001", "return": 0.04},
                    {"symbol": "600002", "return": 0.02},
                ],
            },
            {
                "date": "2026-06-25",
                "sample_type": "historical_training",
                "selected": True,
                "symbol": "600003",
                "return": 0.01,
                "actual_best": {"symbol": "600004", "return": 0.03},
                "candidate_pool": [
                    {"symbol": "600004", "return": 0.03},
                    {"symbol": "600003", "return": 0.01},
                ],
            },
            {
                "date": "2026-06-26",
                "sample_type": "historical_training",
                "selected": True,
                "symbol": "600005",
                "return": 0.02,
                "actual_best": {"symbol": "600005", "return": 0.02},
                "candidate_pool": [
                    {"symbol": "600005", "return": 0.02},
                    {"symbol": "600006", "return": 0.01},
                ],
            },
        ]
        config = {
            "version": "v-test",
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "selection": {},
            "factors": {},
        }

        with mock.patch.object(self.report_generator, "_load_config", return_value=config), \
                mock.patch.object(self.report_generator, "_load_performance", return_value={}), \
                mock.patch.object(self.report_generator, "_load_version", return_value={"version": "v-test"}), \
                mock.patch.object(self.report_generator, "_load_strategy_samples", return_value=samples), \
                mock.patch.object(self.report_generator, "_history_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_live_records", return_value=[]), \
                mock.patch.object(self.report_generator, "_render_alerts", return_value=""), \
                mock.patch.object(self.report_generator, "_calc_factor_contrib_rows", return_value=[]):
            output = self.report_generator.render_html_report(selection_result)

        self.assertIn("命中最优", output)
        self.assertIn("Top3邻近", output)
        self.assertIn("机会损失", output)
        self.assertIn("33.33%", output)
        self.assertIn("2.00%", output)

if __name__ == "__main__":
    unittest.main()
