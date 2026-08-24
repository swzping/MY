import importlib
import json
import sys
import tempfile
import unittest
import datetime as real_datetime
from pathlib import Path
from unittest import mock

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
REAL_DATETIME = real_datetime.datetime


def kline(rows):
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume", "amount"])


def minute_kline(rows):
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume", "amount"])


class TrainingSplitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.backtest_runner = importlib.import_module("backtest_runner")
        self.main = importlib.import_module("main")

        self.backtest_runner.DATA_DIR = self.base / "data"
        self.backtest_runner.TRADES_PATH = self.backtest_runner.DATA_DIR / "trades.json"
        self.backtest_runner.PERF_PATH = self.backtest_runner.DATA_DIR / "performance.json"
        self.backtest_runner.SAMPLE_POOL_PATH = self.backtest_runner.DATA_DIR / "strategy_samples.json"
        self.backtest_runner.BACKTEST_META_PATH = self.backtest_runner.DATA_DIR / "backtest_meta.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_train_history_default_uses_full_training_window(self):
        observed = {}

        def fake_run_backtest(trading_days, universe_size, overrides=None):
            observed["trading_days"] = trading_days
            observed["universe_size"] = universe_size
            observed["overrides"] = overrides
            return {
                "trades": [],
                "samples": [],
                "performance": {},
                "meta": {},
            }

        with mock.patch.object(sys, "argv", ["main.py", "train_history"]), \
                mock.patch.object(self.backtest_runner, "run_backtest", side_effect=fake_run_backtest), \
                mock.patch.dict(sys.modules, {"backtest_runner": self.backtest_runner}), \
                mock.patch("feedback_loop.collect_metrics", return_value="snapshot-unit"), \
                mock.patch("report_generator.generate", return_value="reports/unit.md"):
            self.main.cmd_train_history()

        self.assertEqual(observed["trading_days"], self.backtest_runner.DEFAULT_TRAINING_DAYS)
        self.assertEqual(observed["universe_size"], 150)
        self.assertIsNone(observed["overrides"])

    def test_run_today_report_passes_runtime_overrides_without_saving_config(self):
        observed = {}

        def fake_run_selection(overrides=None, mode=None):
            observed["overrides"] = overrides
            observed["mode"] = mode
            return {
                "date": "2026-06-29",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "测试空仓",
            }

        with mock.patch.object(
            sys,
            "argv",
            [
                "main.py",
                "run_today_report",
                "--f2-min",
                "50",
                "--score-min",
                "40",
                "--f8-min",
                "50",
                "--f9-min",
                "80",
            ],
        ), \
                mock.patch("validator.sync_previous_live_paper", return_value={"status": "no_pending"}), \
                mock.patch("validator.save_empty_pending"), \
                mock.patch("strategy_engine.run_selection", side_effect=fake_run_selection), \
                mock.patch("report_generator.generate", return_value="/tmp/report.md"):
            self.main.cmd_run_today_report()

        self.assertEqual(
            observed["overrides"],
            {
                "F2_volume_price_sync_min": 50.0,
                "score_threshold": 40.0,
                "F8_overnight_risk_control_min": 50.0,
                "F9_overheat_control_min": 80.0,
            },
        )
        self.assertEqual(observed["mode"], "balanced")

    def test_run_today_report_accepts_attack_mode(self):
        observed = {}

        def fake_run_selection(overrides=None, mode=None):
            observed["mode"] = mode
            return {
                "date": "2026-06-29",
                "recommendations": [],
                "market_overview": {},
                "empty_reason": "测试空仓",
            }

        with mock.patch.object(sys, "argv", ["main.py", "run_today_report", "--mode", "attack"]), \
                mock.patch("validator.sync_previous_live_paper", return_value={"status": "no_pending"}), \
                mock.patch("validator.save_empty_pending"), \
                mock.patch("strategy_engine.run_selection", side_effect=fake_run_selection), \
                mock.patch("report_generator.generate", return_value="/tmp/report.md"):
            self.main.cmd_run_today_report()

        self.assertEqual(observed["mode"], "attack")

    def test_train_history_passes_f2_min_override(self):
        observed = {}

        def fake_run_backtest(trading_days, universe_size, overrides=None):
            observed["trading_days"] = trading_days
            observed["universe_size"] = universe_size
            observed["overrides"] = overrides
            return {
                "trades": [],
                "samples": [],
                "performance": {},
                "meta": {},
            }

        with mock.patch.object(sys, "argv", ["main.py", "train_history", "--f2-min", "45"]), \
                mock.patch.object(self.backtest_runner, "run_backtest", side_effect=fake_run_backtest), \
                mock.patch.dict(sys.modules, {"backtest_runner": self.backtest_runner}), \
                mock.patch("feedback_loop.collect_metrics", return_value="snapshot-unit"), \
                mock.patch("report_generator.generate", return_value="reports/unit.md"):
            self.main.cmd_train_history()

        self.assertEqual(observed["overrides"], {"F2_volume_price_sync_min": 45.0})

    def test_backtest_cli_default_uses_full_training_window(self):
        observed = {}

        def fake_run_backtest(trading_days, universe_size):
            observed["trading_days"] = trading_days
            observed["universe_size"] = universe_size
            return {"samples": [], "trades": [], "performance": {}, "meta": {}}

        with mock.patch.object(sys, "argv", ["backtest_runner.py"]), \
                mock.patch.object(self.backtest_runner, "run_backtest", side_effect=fake_run_backtest), \
                mock.patch.object(self.backtest_runner, "generate_training_report", return_value="reports/unit.md"):
            self.backtest_runner.main()

        self.assertEqual(observed["trading_days"], self.backtest_runner.DEFAULT_TRAINING_DAYS)
        self.assertEqual(observed["universe_size"], 150)

    def test_default_backtest_dates_include_previous_trading_day_when_t1_exists(self):
        all_dates_desc = ["2026-06-29", "2026-06-26", "2026-06-25", "2026-06-24"]

        dates = self.backtest_runner.select_backtest_dates(all_dates_desc, trading_days=None)

        self.assertEqual(dates[-1], "2026-06-26")
        self.assertIn("2026-06-26", dates)

    def test_strategy_overrides_adjust_thresholds_without_mutating_original_config(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "selection": {
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F3_technical_pattern": 70,
                "F8_overnight_risk_control": 70,
                "F9_overheat_control": 85,
                }
            }
        }

        adjusted = strategy_engine.apply_runtime_overrides(
            config,
            {
                "F2_volume_price_sync_min": 50,
                "score_threshold": 40,
                "F8_overnight_risk_control_min": 50,
                "F9_overheat_control_min": 80,
            },
        )

        self.assertEqual(adjusted["selection"]["min_factor_scores"]["F2_volume_price_sync"], 50)
        self.assertEqual(adjusted["selection"]["score_threshold"], 40)
        self.assertEqual(adjusted["selection"]["min_factor_scores"]["F8_overnight_risk_control"], 50)
        self.assertEqual(adjusted["selection"]["min_factor_scores"]["F9_overheat_control"], 80)
        self.assertEqual(config["selection"]["min_factor_scores"]["F2_volume_price_sync"], 65)
        self.assertEqual(config["selection"]["score_threshold"], 55)
        self.assertEqual(config["selection"]["min_factor_scores"]["F8_overnight_risk_control"], 70)
        self.assertEqual(config["selection"]["min_factor_scores"]["F9_overheat_control"], 85)
        self.assertEqual(adjusted["runtime_overrides"]["F2_volume_price_sync_min"]["before"], 65)
        self.assertEqual(adjusted["runtime_overrides"]["F2_volume_price_sync_min"]["after"], 50)
        self.assertEqual(adjusted["runtime_overrides"]["score_threshold"]["before"], 55)
        self.assertEqual(adjusted["runtime_overrides"]["score_threshold"]["after"], 40)
        self.assertEqual(adjusted["runtime_overrides"]["F8_overnight_risk_control_min"]["before"], 70)
        self.assertEqual(adjusted["runtime_overrides"]["F8_overnight_risk_control_min"]["after"], 50)
        self.assertEqual(adjusted["runtime_overrides"]["F9_overheat_control_min"]["before"], 85)
        self.assertEqual(adjusted["runtime_overrides"]["F9_overheat_control_min"]["after"], 80)

    def test_build_daily_sample_keeps_selected_signal_when_execution_is_skipped(self):
        config = {
            "version": "test",
            "selection": {"score_threshold": 55, "min_factor_scores": {}, "max_factor_scores": {}},
            "optimization": {"candidate_pool_size": 20},
        }
        stock = {
            "symbol": "000001",
            "name": "测试股",
            "score": 80,
            "factor_scores": {"F1_tail_fund_inflow": 80, "F4_tail_rally_strength": 70},
        }

        sample = self.backtest_runner.build_daily_sample(
            "2026-01-05",
            "2026-01-06",
            [stock],
            config,
            candidate_validations={
                "000001": {"execution_status": "skipped", "skip_reason": "exit_unfillable_limit"}
            },
        )

        self.assertTrue(sample["selected"])
        self.assertEqual(sample["execution_status"], "skipped")
        self.assertEqual(sample["skip_reason"], "exit_unfillable_limit")
        self.assertIsNone(sample["return"])

    def test_intraday_attack_signal_prefers_accelerating_supported_candidate(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
            },
            "selection": {
                "min_factor_scores": {
                    "F8_overnight_risk_control": 40,
                    "F9_overheat_control": 30,
                },
                "max_factor_scores": {},
            },
        }
        scored = [
            {
                "symbol": "000417",
                "name": "静态高分",
                "score": 52,
                "sector": "一般零售",
                "factor_scores": {
                    "F5_sector_heat": 50,
                    "F8_overnight_risk_control": 60,
                    "F9_overheat_control": 60,
                },
                "intraday_profile": {
                    "pct_change": 0.018,
                    "position_in_range": 0.52,
                    "drawdown_from_high": 0.018,
                    "tail_return": 0.001,
                    "tail_volume_share": 0.05,
                    "volume_ratio": 1.05,
                },
            },
            {
                "symbol": "600867",
                "name": "通化东宝",
                "score": 46,
                "sector": "生物制品",
                "factor_scores": {
                    "F5_sector_heat": 82,
                    "F8_overnight_risk_control": 64,
                    "F9_overheat_control": 58,
                },
                "intraday_profile": {
                    "pct_change": 0.055,
                    "position_in_range": 0.78,
                    "drawdown_from_high": 0.006,
                    "tail_return": 0.012,
                    "tail_volume_share": 0.18,
                    "volume_ratio": 2.4,
                },
            },
        ]

        signals = strategy_engine.build_opportunity_signals(
            scored,
            config,
            market_overview={"sh_pct": 0.006, "limit_up_count": 70, "limit_down_count": 5},
            mode="balanced",
        )

        self.assertEqual(signals[0]["symbol"], "600867")
        self.assertEqual(signals[0]["action"], "BUY_NOW")
        self.assertEqual(signals[0]["strategy_case"], "intraday_attack")
        self.assertEqual(signals[0]["entry_price_source"], "current_price")

    def test_intraday_opportunity_can_wait_for_next_recheck_when_signal_incomplete(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600001",
                "name": "待确认",
                "score": 61,
                "sector": "测试",
                "factor_scores": {"F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.025,
                    "position_in_range": 0.62,
                    "drawdown_from_high": 0.012,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.12,
                },
            }
        ]

        with mock.patch.object(strategy_engine.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 13, 20)
            signals = strategy_engine.build_opportunity_signals(
                scored,
                config,
                market_overview={"sh_pct": 0.002, "limit_up_count": 35, "limit_down_count": 4},
                mode="balanced",
            )

        self.assertEqual(signals[0]["action"], "WAIT_RECHECK")
        self.assertTrue(signals[0]["next_check_at"])

    def test_intraday_recheck_time_tracks_live_candidate_instead_of_fixed_checkpoint(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
                "alive_recheck_minutes": 12,
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600001",
                "name": "待放量",
                "score": 61,
                "sector": "测试",
                "factor_scores": {"F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.025,
                    "position_in_range": 0.62,
                    "drawdown_from_high": 0.012,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.12,
                },
            }
        ]

        signals = strategy_engine.build_opportunity_signals(
            scored,
            config,
            market_overview={"sh_pct": 0.002, "limit_up_count": 35, "limit_down_count": 4},
            mode="balanced",
            decision_time=REAL_DATETIME(2026, 6, 29, 13, 41),
        )

        self.assertEqual(signals[0]["action"], "WAIT_RECHECK")
        self.assertEqual(signals[0]["next_check_at"], "13:53")

    def test_intraday_recheck_time_gets_urgent_when_candidate_weakens(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
                "weak_recheck_minutes": 5,
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600002",
                "name": "承接转弱",
                "score": 62,
                "sector": "测试",
                "factor_scores": {"F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.021,
                    "position_in_range": 0.46,
                    "drawdown_from_high": 0.026,
                    "tail_return": -0.003,
                    "tail_volume_share": 0.07,
                    "volume_ratio": 1.05,
                },
            }
        ]

        signals = strategy_engine.build_opportunity_signals(
            scored,
            config,
            market_overview={"sh_pct": 0.002, "limit_up_count": 35, "limit_down_count": 4},
            mode="balanced",
            decision_time=REAL_DATETIME(2026, 6, 29, 13, 41),
        )

        self.assertEqual(signals[0]["action"], "WAIT_RECHECK")
        self.assertEqual(signals[0]["next_check_at"], "13:46")

    def test_intraday_recheck_time_keeps_hot_candidate_on_short_watch(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
                "hot_recheck_minutes": 5,
                "alive_recheck_minutes": 12,
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600933",
                "name": "爱柯迪",
                "score": 49.04,
                "sector": "汽车零部件",
                "factor_scores": {"F5_sector_heat": 80, "F8_overnight_risk_control": 64, "F9_overheat_control": 50},
                "intraday_profile": {
                    "pct_change": 0.0222,
                    "position_in_range": 0.66,
                    "drawdown_from_high": 0.0154,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.12,
                },
            }
        ]

        signals = strategy_engine.build_opportunity_signals(
            scored,
            config,
            market_overview={"sh_pct": 0.006, "limit_up_count": 70, "limit_down_count": 5},
            mode="balanced",
            decision_time=REAL_DATETIME(2026, 6, 30, 13, 54),
        )

        self.assertEqual(signals[0]["action"], "WAIT_RECHECK")
        self.assertEqual(signals[0]["next_check_at"], "13:59")

    def test_intraday_opportunity_confirms_when_live_tape_strengthens_after_last_recheck(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600918",
                "name": "中泰证券",
                "score": 40.47,
                "sector": "证券 II",
                "factor_scores": {"F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.032,
                    "position_in_range": 0.72,
                    "drawdown_from_high": 0.008,
                    "tail_return": 0.006,
                    "tail_volume_share": 0.12,
                    "volume_ratio": 1.35,
                },
            }
        ]

        with mock.patch.object(strategy_engine.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 14, 49)
            signals = strategy_engine.build_opportunity_signals(
                scored,
                config,
                market_overview={"sh_pct": 0.002, "limit_up_count": 35, "limit_down_count": 4},
                mode="balanced",
            )

        self.assertIn(signals[0]["action"], {"BUY_NOW", "TAIL_CONFIRM"})
        self.assertEqual(signals[0]["next_check_at"], "")

    def test_intraday_opportunity_still_judges_live_tape_after_advice_window_before_close(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600109",
                "name": "国金证券",
                "score": 40.8,
                "sector": "证券 II",
                "factor_scores": {"F5_sector_heat": 79, "F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.024,
                    "position_in_range": 0.74,
                    "drawdown_from_high": 0.009,
                    "tail_return": 0.005,
                    "tail_volume_share": 0.12,
                    "volume_ratio": 1.3,
                },
            }
        ]

        with mock.patch.object(strategy_engine.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 14, 57)
            signals = strategy_engine.build_opportunity_signals(
                scored,
                config,
                market_overview={"sh_pct": 0.006, "limit_up_count": 60, "limit_down_count": 4},
                mode="balanced",
            )

        self.assertIn(signals[0]["action"], {"BUY_NOW", "TAIL_CONFIRM"})
        self.assertEqual(signals[0]["next_check_at"], "")

    def test_tail_confirm_candidate_remains_actionable_after_advice_window_before_close(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600109",
                "name": "国金证券",
                "score": 40.8,
                "sector": "证券 II",
                "factor_scores": {"F5_sector_heat": 79, "F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.0182,
                    "position_in_range": 0.74,
                    "drawdown_from_high": 0.009,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.05,
                },
            }
        ]

        with mock.patch.object(strategy_engine.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 14, 57)
            signals = strategy_engine.build_opportunity_signals(
                scored,
                config,
                market_overview={"sh_pct": 0.006, "limit_up_count": 60, "limit_down_count": 4},
                mode="balanced",
            )

        self.assertEqual(signals[0]["action"], "TAIL_CONFIRM")
        self.assertEqual(signals[0]["next_check_at"], "")

    def test_tail_confirm_candidate_is_not_actionable_after_market_close(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["10:00", "13:00", "14:00", "14:40"]},
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600109",
                "name": "国金证券",
                "score": 40.8,
                "sector": "证券 II",
                "factor_scores": {"F5_sector_heat": 79, "F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.0182,
                    "position_in_range": 0.74,
                    "drawdown_from_high": 0.009,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.05,
                },
            }
        ]

        with mock.patch.object(strategy_engine.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 15, 1)
            signals = strategy_engine.build_opportunity_signals(
                scored,
                config,
                market_overview={"sh_pct": 0.006, "limit_up_count": 60, "limit_down_count": 4},
                mode="balanced",
            )

        self.assertEqual(signals[0]["action"], "NO_TRADE")
        self.assertEqual(signals[0]["next_check_at"], "")

    def test_intraday_opportunity_does_not_emit_expired_recheck_time(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {
                "enabled": True,
                "checkpoints": ["10:00", "13:00", "14:00", "14:40"],
            },
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600918",
                "name": "中泰证券",
                "score": 40.47,
                "sector": "证券 II",
                "factor_scores": {"F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.025,
                    "position_in_range": 0.62,
                    "drawdown_from_high": 0.012,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.12,
                },
            }
        ]

        with mock.patch.object(strategy_engine.dt, "datetime") as fake_datetime:
            fake_datetime.now.return_value = REAL_DATETIME(2026, 6, 29, 14, 49)
            signals = strategy_engine.build_opportunity_signals(
                scored,
                config,
                market_overview={"sh_pct": 0.002, "limit_up_count": 35, "limit_down_count": 4},
                mode="balanced",
            )

        self.assertNotEqual(signals[0]["next_check_at"], "14:40")
        self.assertNotEqual(signals[0]["action"], "WAIT_RECHECK")

    def test_intraday_opportunity_uses_explicit_decision_time_for_recheck(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["10:00", "13:00", "14:00", "14:40"]},
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600918",
                "name": "中泰证券",
                "score": 40.47,
                "sector": "证券 II",
                "factor_scores": {"F8_overnight_risk_control": 70, "F9_overheat_control": 70},
                "intraday_profile": {
                    "pct_change": 0.025,
                    "position_in_range": 0.62,
                    "drawdown_from_high": 0.012,
                    "tail_return": 0.002,
                    "tail_volume_share": 0.08,
                    "volume_ratio": 1.12,
                },
            }
        ]

        signals = strategy_engine.build_opportunity_signals(
            scored,
            config,
            market_overview={"sh_pct": 0.002, "limit_up_count": 35, "limit_down_count": 4},
            mode="balanced",
            decision_time=REAL_DATETIME(2026, 6, 29, 14, 57),
        )

        self.assertEqual(signals[0]["next_check_at"], "")
        self.assertNotEqual(signals[0]["action"], "WAIT_RECHECK")
        self.assertEqual(signals[0]["decision_time"], "2026-06-29 14:57:00")

    def test_tail_only_mode_does_not_emit_intraday_buy_now(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "checkpoints": ["13:00", "14:40"]},
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
        }
        scored = [
            {
                "symbol": "600867",
                "name": "通化东宝",
                "score": 46,
                "sector": "生物制品",
                "factor_scores": {"F5_sector_heat": 82, "F8_overnight_risk_control": 64, "F9_overheat_control": 58},
                "intraday_profile": {
                    "pct_change": 0.055,
                    "position_in_range": 0.78,
                    "drawdown_from_high": 0.006,
                    "tail_return": 0.012,
                    "tail_volume_share": 0.18,
                    "volume_ratio": 2.4,
                },
            }
        ]

        signals = strategy_engine.build_opportunity_signals(
            scored,
            config,
            market_overview={"sh_pct": 0.006, "limit_up_count": 70, "limit_down_count": 5},
            mode="tail-only",
        )

        self.assertEqual(signals[0]["action"], "TAIL_CONFIRM")
        self.assertEqual(signals[0]["strategy_case"], "tail_confirm")

    def test_strong_market_rescue_promotes_high_opportunity_tail_confirm_blocked_only_by_f2(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "selection": {
                "top_n": 1,
                "max_per_sector": 1,
                "score_threshold": 55,
                "min_factor_scores": {
                    "F2_volume_price_sync": 65,
                    "F8_overnight_risk_control": 40,
                },
                "max_factor_scores": {},
                "strong_market_f2_rescue": {
                    "enabled": True,
                    "min_opportunity_score": 75,
                    "min_score": 40,
                    "min_sh_pct": 0.003,
                    "min_limit_up_count": 50,
                    "max_limit_down_count": 10,
                    "allowed_actions": ["BUY_NOW", "TAIL_CONFIRM"],
                },
            }
        }
        scored = [
            {
                "symbol": "600877",
                "name": "电科芯片",
                "score": 43.5,
                "sector": "半导体",
                "F2_volume_price_sync": 20,
                "F8_overnight_risk_control": 64,
                "factor_scores": {
                    "F2_volume_price_sync": {"score": 20},
                    "F8_overnight_risk_control": {"score": 64},
                },
            }
        ]
        opportunity_signals = [
            {
                **scored[0],
                "action": "TAIL_CONFIRM",
                "strategy_case": "tail_confirm",
                "opportunity_score": 81.8,
                "risks": ["量能确认不足"],
                "reasons": ["强市场下尾盘承接确认"],
            }
        ]

        picks = strategy_engine.select_formal_picks(
            scored,
            opportunity_signals,
            config,
            {"sh_pct": 0.006, "limit_up_count": 70, "limit_down_count": 5},
            mode="balanced",
        )

        self.assertEqual(picks[0]["symbol"], "600877")
        self.assertEqual(picks[0]["selection_mode"], "strong_market_f2_rescue")
        self.assertIn("F2不足由强市场救援", picks[0]["risks"])

    def test_strong_market_rescue_does_not_promote_no_trade_or_weak_market(self):
        strategy_engine = importlib.import_module("strategy_engine")
        config = {
            "selection": {
                "top_n": 1,
                "max_per_sector": 1,
                "score_threshold": 55,
                "min_factor_scores": {"F2_volume_price_sync": 65},
                "max_factor_scores": {},
                "strong_market_f2_rescue": {"enabled": True, "min_opportunity_score": 75},
            }
        }
        scored = [
            {
                "symbol": "600884",
                "name": "杉杉股份",
                "score": 45,
                "sector": "电池",
                "F2_volume_price_sync": 20,
                "factor_scores": {"F2_volume_price_sync": {"score": 20}},
            }
        ]

        no_trade = strategy_engine.select_formal_picks(
            scored,
            [{**scored[0], "action": "NO_TRADE", "opportunity_score": 90}],
            config,
            {"sh_pct": 0.008, "limit_up_count": 80, "limit_down_count": 3},
            mode="balanced",
        )
        weak_market = strategy_engine.select_formal_picks(
            scored,
            [{**scored[0], "action": "TAIL_CONFIRM", "opportunity_score": 90}],
            config,
            {"sh_pct": -0.002, "limit_up_count": 18, "limit_down_count": 20},
            mode="balanced",
        )

        self.assertEqual(no_trade, [])
        self.assertEqual(weak_market, [])

    def test_validate_close_to_next_open_uses_t_close_buy_and_t1_open_sell(self):
        df = kline(
            [
                ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
            ]
        )

        result = self.backtest_runner.validate_close_to_next_open(df)

        self.assertEqual(result["buy_price"], 10.0)
        self.assertEqual(result["sell_price"], 10.5)
        self.assertEqual(result["return"], 0.05)
        self.assertTrue(result["win"])
        self.assertEqual(result["sell_reason"], "next_open")

    def test_validate_close_to_next_open_can_skip_chasing_near_high_close(self):
        df = kline(
            [
                ["2026-06-24", 9.5, 10.2, 9.4, 10.18, 1000, 100000],
                ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
            ]
        )

        result = self.backtest_runner.validate_close_to_next_open(
            df,
            execution_model={"buy_mode": "anti_chase", "max_close_position": 0.9},
        )

        self.assertIsNone(result)

    def test_validate_close_to_next_open_can_use_tail_minute_execution_price(self):
        df = kline(
            [
                ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
            ]
        )
        tail = minute_kline(
            [
                ["2026-06-24 14:30:00", 9.80, 9.85, 9.78, 9.82, 100, 98200],
                ["2026-06-24 14:45:00", 9.90, 9.95, 9.88, 9.92, 120, 119040],
                ["2026-06-24 15:00:00", 9.98, 10.02, 9.96, 10.00, 130, 130000],
            ]
        )

        result = self.backtest_runner.validate_close_to_next_open(
            df,
            execution_model={"buy_mode": "minute_at", "buy_time": "14:45"},
            tail_minutes=tail,
        )

        self.assertEqual(result["buy_price"], 9.92)
        self.assertEqual(result["buy_price_source"], "T_minute_14:45")
        self.assertEqual(result["return"], 0.0585)

    def test_validate_close_to_next_open_can_use_next_open_window_average_sell(self):
        df = kline(
            [
                ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
            ]
        )
        open_minutes = minute_kline(
            [
                ["2026-06-25 09:30:00", 10.50, 10.55, 10.48, 10.52, 100, 105200],
                ["2026-06-25 09:35:00", 10.56, 10.62, 10.55, 10.60, 120, 127200],
                ["2026-06-25 09:40:00", 10.58, 10.61, 10.54, 10.58, 110, 116380],
            ]
        )

        result = self.backtest_runner.validate_close_to_next_open(
            df,
            execution_model={"sell_mode": "open_window_avg", "sell_window_end": "09:40"},
            t1_open_minutes=open_minutes,
        )

        self.assertEqual(result["sell_price"], 10.567)
        self.assertEqual(result["sell_price_source"], "T1_open_window_avg_09:30_09:40")
        self.assertEqual(result["sell_reason"], "next_open_window")
        self.assertEqual(result["return"], 0.0567)

    def test_validate_close_to_next_open_marks_open_window_fallback_when_minutes_missing(self):
        df = kline(
            [
                ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
            ]
        )

        result = self.backtest_runner.validate_close_to_next_open(
            df,
            execution_model={"sell_mode": "open_window_avg", "sell_window_end": "09:40"},
        )

        self.assertEqual(result["sell_price"], 10.5)
        self.assertEqual(result["sell_price_source"], "T1_open_fallback_no_minutes")
        self.assertEqual(result["sell_reason"], "next_open_fallback")

    def test_validate_close_to_next_open_rejects_bad_zero_volume_t1_kline(self):
        df = kline(
            [
                ["2026-06-25", 5.65, 6.27, 5.55, 6.11, 463474, 278218368],
                ["2026-06-26", 6.11, 6.11, 6.11, 6.11, 0, 0],
            ]
        )

        result = self.backtest_runner.validate_close_to_next_open(
            df,
            t_date="2026-06-25",
            t1_date="2026-06-26",
        )

        self.assertIsNone(result)

    def test_build_daily_sample_records_top1_or_empty_for_each_trading_day(self):
        config = {
            "version": "unit",
            "selection": {"score_threshold": 60, "top_n": 1},
        }
        scored = [
            {"symbol": "600001", "score": 70, "factor_scores": {"score": 70}},
            {"symbol": "600002", "score": 68, "factor_scores": {"score": 68}},
        ]
        trade_sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            next_kline=kline(
                [
                    ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            ),
        )

        self.assertTrue(trade_sample["selected"])
        self.assertEqual(trade_sample["sample_type"], "historical_training")
        self.assertEqual(trade_sample["symbol"], "600001")
        self.assertEqual(trade_sample["buy_price_source"], "T_close")
        self.assertEqual(trade_sample["sell_price_source"], "T1_open")

        empty_sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-25",
            t1_date="2026-06-26",
            scored_stocks=[],
            config=config,
            next_kline=pd.DataFrame(),
        )
        self.assertFalse(empty_sample["selected"])
        self.assertEqual(empty_sample["empty_reason"], "无候选")

    def test_build_daily_sample_applies_configured_execution_model(self):
        config = {
            "version": "unit",
            "selection": {"score_threshold": 60, "top_n": 1},
            "execution_model": {"buy_mode": "anti_chase", "max_close_position": 0.9},
        }
        scored = [
            {"symbol": "600001", "score": 70, "factor_scores": {"score": 70}},
        ]

        sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            next_kline=kline(
                [
                    ["2026-06-24", 9.5, 10.2, 9.4, 10.18, 1000, 100000],
                    ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            ),
        )

        self.assertFalse(sample["selected"])
        self.assertEqual(sample["empty_reason"], "缺少有效次日开盘验证数据")

    def test_build_daily_sample_marks_minute_execution_fallback_when_minutes_missing(self):
        config = {
            "version": "unit",
            "selection": {"score_threshold": 60, "top_n": 1},
            "execution_model": {"buy_mode": "minute_at", "buy_time": "14:45"},
        }
        scored = [
            {"symbol": "600001", "score": 70, "factor_scores": {"score": 70}},
        ]

        sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            next_kline=kline(
                [
                    ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            ),
        )

        self.assertTrue(sample["selected"])
        self.assertEqual(sample["buy_price"], 10.0)
        self.assertEqual(sample["buy_price_source"], "T_close_fallback_no_minutes")

    def test_build_daily_sample_uses_tail_advice_proxy_when_minutes_missing(self):
        config = {
            "version": "unit",
            "selection": {"score_threshold": 60, "top_n": 1},
            "execution_model": {"buy_mode": "tail_advice", "buy_time": "14:45"},
        }
        scored = [
            {"symbol": "600001", "score": 70, "factor_scores": {"score": 70}},
        ]

        sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            next_kline=kline(
                [
                    ["2026-06-24", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-25", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            ),
        )

        self.assertTrue(sample["selected"])
        self.assertLess(sample["buy_price"], 10.0)
        self.assertEqual(sample["buy_price_source"], "T_tail_advice_proxy_no_minutes")
        self.assertEqual(sample["sell_price"], 10.5)
        self.assertEqual(sample["sell_price_source"], "T1_open")

    def test_build_daily_sample_applies_factor_guardrails_and_keeps_candidate_pool(self):
        config = {
            "version": "unit",
            "selection": {
                "score_threshold": 60,
                "top_n": 1,
                "min_factor_scores": {"F2_volume_price_sync": 80},
                "max_factor_scores": {"F7_float_mv_fit": 70},
            },
        }
        scored = [
            {
                "symbol": "600001",
                "score": 90,
                "factor_scores": {
                    "F2_volume_price_sync": 85,
                    "F7_float_mv_fit": 90,
                    "score": 90,
                },
            },
            {
                "symbol": "600002",
                "score": 80,
                "factor_scores": {
                    "F2_volume_price_sync": 82,
                    "F7_float_mv_fit": 60,
                    "score": 80,
                },
            },
        ]

        sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            candidate_validations={
                "600001": {"return": -0.02, "win": False, "buy_price": 10, "sell_price": 9.8},
                "600002": {
                    "buy_price": 20,
                    "sell_price": 20.4,
                    "return": 0.02,
                    "win": True,
                    "sell_reason": "next_open",
                    "buy_price_source": "T_close",
                    "sell_price_source": "T1_open",
                },
            },
        )

        self.assertTrue(sample["selected"])
        self.assertEqual(sample["symbol"], "600002")
        self.assertEqual(sample["return"], 0.02)
        self.assertEqual(sample["actual_best"]["symbol"], "600002")
        self.assertEqual(sample["missed_best_reason"], "已选中次日实际最优")
        self.assertEqual(len(sample["candidate_pool"]), 2)
        self.assertEqual(sample["candidate_pool"][0]["symbol"], "600001")
        self.assertEqual(sample["candidate_pool"][0]["return"], -0.02)

    def test_build_daily_sample_can_apply_neighbor_rescue_history(self):
        config = {
            "version": "unit",
            "factors": {
                "F1_tail_fund_inflow": {"weight": 1.0},
                "F2_volume_price_sync": {"weight": 0.0},
                "F3_technical_pattern": {"weight": 0.0},
            },
            "selection": {
                "score_threshold": 60,
                "top_n": 1,
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
            "optimization": {"candidate_pool_size": 20},
        }
        neighbor_history = {
            ("F2_volume_price_sync<min",): [
                {
                    "symbol": "600001",
                    "factor_scores": {
                        "F1_tail_fund_inflow": 90,
                        "F2_volume_price_sync": 60,
                        "F3_technical_pattern": 40,
                    },
                    "return": 0.04,
                }
            ]
        }
        scored = [
            {
                "symbol": "600002",
                "name": "救援候选",
                "score": 91,
                "factor_scores": {
                    "F1_tail_fund_inflow": 91,
                    "F2_volume_price_sync": 60,
                    "F3_technical_pattern": 39,
                },
            }
        ]

        sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            candidate_validations={
                "600002": {
                    "buy_price": 10.0,
                    "sell_price": 10.5,
                    "return": 0.05,
                    "win": True,
                    "sell_reason": "next_open",
                    "buy_price_source": "T_close",
                    "sell_price_source": "T1_open",
                },
            },
            neighbor_rescue_history=neighbor_history,
        )

        self.assertTrue(sample["selected"])
        self.assertEqual(sample["symbol"], "600002")
        self.assertEqual(sample["selection_mode"], "neighbor_rescue")

    def test_build_daily_sample_explains_why_actual_best_was_not_selected(self):
        config = {
            "version": "unit",
            "selection": {"score_threshold": 60, "top_n": 1},
        }
        scored = [
            {"symbol": "600001", "score": 80, "factor_scores": {"score": 80}},
            {"symbol": "600002", "score": 70, "factor_scores": {"score": 70}},
        ]

        sample = self.backtest_runner.build_daily_sample(
            t_date="2026-06-24",
            t1_date="2026-06-25",
            scored_stocks=scored,
            config=config,
            candidate_validations={
                "600001": {
                    "buy_price": 10,
                    "sell_price": 9.8,
                    "return": -0.02,
                    "win": False,
                    "sell_reason": "next_open",
                    "buy_price_source": "T_close",
                    "sell_price_source": "T1_open",
                },
                "600002": {"return": 0.03, "win": True, "buy_price": 20, "sell_price": 20.6},
            },
        )

        self.assertEqual(sample["symbol"], "600001")
        self.assertEqual(sample["actual_best"]["symbol"], "600002")
        self.assertIn("当时综合分 70.00 低于已选 80.00", sample["missed_best_reason"])

    def test_fill_sample_names_uses_tencent_fallback_for_picks_and_actual_best(self):
        samples = [
            {
                "selected": True,
                "symbol": "600001",
                "name": "",
                "candidate_pool": [{"symbol": "600002", "name": ""}],
                "actual_best": {"symbol": "600002", "name": "", "return": 0.03},
            }
        ]
        original_symbols = self.backtest_runner.data_loader.get_a_share_symbols
        original_quote = self.backtest_runner.data_loader.tencent_quote
        try:
            self.backtest_runner.data_loader.get_a_share_symbols = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
            self.backtest_runner.data_loader.tencent_quote = lambda codes: {
                "600001": {"name": "选中股"},
                "600002": {"name": "实际最优"},
            }

            self.backtest_runner.fill_sample_names(samples)
        finally:
            self.backtest_runner.data_loader.get_a_share_symbols = original_symbols
            self.backtest_runner.data_loader.tencent_quote = original_quote

        self.assertEqual(samples[0]["name"], "选中股")
        self.assertEqual(samples[0]["candidate_pool"][0]["name"], "实际最优")
        self.assertEqual(samples[0]["actual_best"]["name"], "实际最优")

    def test_save_strategy_samples_upserts_by_date_and_sample_type(self):
        old = {
            "date": "2026-06-24",
            "sample_type": "historical_training",
            "selected": False,
            "empty_reason": "old",
        }
        new = {
            "date": "2026-06-24",
            "sample_type": "historical_training",
            "selected": True,
            "symbol": "600001",
            "return": 0.01,
        }
        live = {
            "date": "2026-06-24",
            "sample_type": "live_paper",
            "selected": True,
            "symbol": "600002",
            "return": -0.01,
        }
        self.backtest_runner.save_strategy_samples([old])
        self.backtest_runner.save_strategy_samples([new, live])

        doc = json.loads(self.backtest_runner.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        samples = sorted(doc["samples"], key=lambda s: s["sample_type"])

        self.assertEqual(len(samples), 2)
        self.assertTrue(any(s.get("symbol") == "600001" for s in samples))
        self.assertTrue(any(s.get("sample_type") == "live_paper" for s in samples))

    def test_save_strategy_samples_replaces_historical_training_layer_but_keeps_live_paper(self):
        existing = {
            "samples": [
                {
                    "date": "2026-06-20",
                    "sample_type": "historical_training",
                    "selected": True,
                    "symbol": "600020",
                },
                {
                    "date": "2026-06-20",
                    "sample_type": "live_paper",
                    "selected": True,
                    "symbol": "600021",
                },
            ]
        }
        self.backtest_runner.SAMPLE_POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.backtest_runner.SAMPLE_POOL_PATH.write_text(
            json.dumps(existing, ensure_ascii=False),
            encoding="utf-8",
        )

        self.backtest_runner.save_strategy_samples([
            {
                "date": "2026-06-24",
                "sample_type": "historical_training",
                "selected": True,
                "symbol": "600024",
            }
        ])

        doc = json.loads(self.backtest_runner.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        historical = [s for s in doc["samples"] if s.get("sample_type") == "historical_training"]
        live = [s for s in doc["samples"] if s.get("sample_type") == "live_paper"]

        self.assertEqual([s.get("symbol") for s in historical], ["600024"])
        self.assertEqual([s.get("symbol") for s in live], ["600021"])

    def test_generate_training_report_writes_readable_markdown(self):
        self.backtest_runner.REPORTS_DIR = self.base / "reports"
        result = {
            "samples": [
                {
                    "date": "2026-06-24",
                    "sample_type": "historical_training",
                    "selected": True,
                    "symbol": "600001",
                    "name": "测试A",
                    "score": 72.5,
                    "buy_price": 10,
                    "sell_price": 10.2,
                    "return": 0.02,
                    "win": True,
                    "actual_best": {"symbol": "600002", "name": "测试B", "return": 0.03},
                    "missed_best_reason": "当时综合分 70.00 低于已选 72.50",
                },
                {
                    "date": "2026-06-25",
                    "sample_type": "historical_training",
                    "selected": False,
                    "empty_reason": "无超阈值",
                    "actual_best": {"symbol": "600003", "name": "测试C", "return": 0.01},
                    "missed_best_reason": "次日实际最优未过当日规则：无超阈值",
                },
            ],
            "performance": {
                "total": {
                    "win_rate": 1.0,
                    "avg_win": 0.02,
                    "avg_loss": 0,
                    "total_return": 0.02,
                    "max_consecutive_loss": 0,
                    "samples": 1,
                }
            },
            "ranking_loss": 0.5,
            "backtest_period": {"start": "2026-06-24", "end": "2026-06-25", "trading_days": 2},
        }

        path = self.backtest_runner.generate_training_report(result, date_str="2026-06-26")
        content = path.read_text(encoding="utf-8")

        self.assertEqual(path.name, "2026-06-26.md")
        self.assertEqual(path.parent.name, "reports")
        self.assertIn("历史训练报告", content)
        self.assertIn("T 日收盘", content)
        self.assertIn("测试A", content)
        self.assertIn("空仓", content)
        self.assertIn("次日实际最优", content)
        self.assertIn("测试B", content)
        self.assertIn("当时综合分", content)

    def test_history_fetch_window_scales_beyond_default_limit(self):
        days = self.backtest_runner.history_fetch_days(160)

        self.assertGreaterEqual(days, 210)

    def test_calendar_limit_scales_beyond_requested_training_days(self):
        limit = self.backtest_runner.history_calendar_limit(160)

        self.assertGreaterEqual(limit, 165)

    def test_overnight_risk_control_penalizes_upper_shadow_and_chase_setup(self):
        safe = kline(
            [
                ["2026-06-01", 10.0, 10.2, 9.9, 10.0, 1000, 100000],
                ["2026-06-02", 10.0, 10.3, 9.9, 10.1, 1000, 101000],
                ["2026-06-03", 10.1, 10.3, 10.0, 10.15, 1000, 101500],
                ["2026-06-04", 10.15, 10.35, 10.05, 10.2, 1000, 102000],
                ["2026-06-05", 10.2, 10.35, 10.1, 10.25, 1000, 102500],
            ]
        )
        risky = kline(
            [
                ["2026-06-01", 10.0, 10.4, 9.9, 10.3, 1000, 103000],
                ["2026-06-02", 10.3, 10.8, 10.2, 10.7, 1200, 128400],
                ["2026-06-03", 10.7, 11.4, 10.6, 11.2, 1600, 179200],
                ["2026-06-04", 11.2, 12.0, 11.1, 11.8, 2300, 271400],
                ["2026-06-05", 11.8, 13.2, 11.7, 12.0, 4200, 504000],
            ]
        )

        safe_score = self.backtest_runner.calc_F8_overnight_risk_control(safe)
        risky_score = self.backtest_runner.calc_F8_overnight_risk_control(risky)

        self.assertGreaterEqual(safe_score, 70)
        self.assertLessEqual(risky_score, 45)

    def test_overheat_control_penalizes_extended_move_above_moving_averages(self):
        calm = kline(
            [
                ["2026-06-01", 10.0, 10.2, 9.9, 10.0, 1000, 100000],
                ["2026-06-02", 10.0, 10.2, 9.9, 10.05, 1000, 100500],
                ["2026-06-03", 10.05, 10.25, 10.0, 10.1, 1000, 101000],
                ["2026-06-04", 10.1, 10.3, 10.05, 10.15, 1000, 101500],
                ["2026-06-05", 10.15, 10.35, 10.1, 10.2, 1000, 102000],
                ["2026-06-08", 10.2, 10.35, 10.1, 10.25, 1000, 102500],
                ["2026-06-09", 10.25, 10.4, 10.15, 10.3, 1000, 103000],
                ["2026-06-10", 10.3, 10.45, 10.2, 10.35, 1000, 103500],
                ["2026-06-11", 10.35, 10.5, 10.25, 10.4, 1000, 104000],
                ["2026-06-12", 10.4, 10.55, 10.3, 10.45, 1000, 104500],
            ]
        )
        overheated = kline(
            [
                ["2026-06-01", 10.0, 10.2, 9.9, 10.0, 1000, 100000],
                ["2026-06-02", 10.0, 10.4, 10.0, 10.3, 1100, 113300],
                ["2026-06-03", 10.3, 10.9, 10.2, 10.8, 1400, 151200],
                ["2026-06-04", 10.8, 11.5, 10.7, 11.4, 1700, 193800],
                ["2026-06-05", 11.4, 12.3, 11.3, 12.1, 2200, 266200],
                ["2026-06-08", 12.1, 13.2, 12.0, 13.0, 2800, 364000],
                ["2026-06-09", 13.0, 14.1, 12.9, 13.9, 3300, 458700],
                ["2026-06-10", 13.9, 15.0, 13.8, 14.8, 3900, 577200],
                ["2026-06-11", 14.8, 16.0, 14.7, 15.8, 4500, 711000],
                ["2026-06-12", 15.8, 17.0, 15.7, 16.8, 5200, 873600],
            ]
        )

        calm_score = self.backtest_runner.calc_F9_overheat_control(calm)
        overheat_score = self.backtest_runner.calc_F9_overheat_control(overheated)

        self.assertGreaterEqual(calm_score, 80)
        self.assertLessEqual(overheat_score, 45)

    def test_training_report_orders_history_descending(self):
        self.backtest_runner.REPORTS_DIR = self.base / "reports"
        result = {
            "samples": [
                {"date": "2026-06-24", "selected": False, "empty_reason": "旧"},
                {"date": "2026-06-26", "selected": False, "empty_reason": "新"},
                {"date": "2026-06-25", "selected": False, "empty_reason": "中"},
            ],
            "performance": {"total": {}},
            "backtest_period": {},
        }

        content = self.backtest_runner.render_training_report(result)

        self.assertLess(content.index("2026-06-26"), content.index("2026-06-25"))
        self.assertLess(content.index("2026-06-25"), content.index("2026-06-24"))

    def test_main_exposes_train_history_and_config_top1(self):
        self.assertIn("train_history", self.main.COMMANDS)
        config = json.loads((ROOT / "config" / "strategy_params.json").read_text(encoding="utf-8"))
        self.assertEqual(config["selection"]["top_n"], 1)


class LiveSamplePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.validator = importlib.import_module("validator")
        self.validator.DATA_DIR = self.base / "data"
        self.validator.SAMPLE_POOL_PATH = self.validator.DATA_DIR / "strategy_samples.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_validator_persists_live_paper_samples(self):
        self.validator._save_live_samples(
            [
                {
                    "symbol": "600001",
                    "name": "测试",
                    "recommend_date": "2026-06-25",
                    "buy_date": "2026-06-26",
                    "buy_price": 10,
                    "sell_price": 10.2,
                    "return": 0.02,
                    "sell_reason": "next_open",
                }
            ]
        )

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(doc["samples"][0]["sample_type"], "live_paper")
        self.assertTrue(doc["samples"][0]["selected"])
        self.assertEqual(doc["samples"][0]["symbol"], "600001")

    def test_save_pending_recommendations_records_selection_time_and_snapshot(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        original_now = self.validator._now
        try:
            self.validator._now = lambda: self.validator.dt.datetime(2026, 6, 25, 14, 55, 12)
            self.validator.save_pending_recommendations(
                [
                    {
                        "symbol": "600001",
                        "name": "测试股",
                        "score": 72.5,
                        "sector": "测试行业",
                        "F1_tail_fund_inflow": 80,
                        "strategy_case": "intraday_attack",
                        "action": "BUY_NOW",
                        "entry_price_source": "current_price",
                        "next_check_at": "",
                    }
                ]
            )
        finally:
            self.validator._now = original_now

        doc = json.loads((self.validator.DATA_DIR / "pending_recommendations.json").read_text(encoding="utf-8"))
        rec = doc["2026-06-25"][0]
        self.assertEqual(rec["selected_at"], "2026-06-25 14:55:12")
        self.assertEqual(rec["selection_date"], "2026-06-25")
        self.assertEqual(rec["score"], 72.5)
        self.assertEqual(rec["factor_scores"]["F1_tail_fund_inflow"], 80)
        self.assertEqual(rec["strategy_case"], "intraday_attack")
        self.assertEqual(rec["action"], "BUY_NOW")
        self.assertEqual(rec["entry_price_source"], "current_price")

    def test_validator_persists_empty_live_paper_samples(self):
        self.validator._save_live_samples(
            [
                {
                    "recommend_date": "2026-06-25",
                    "selected": False,
                    "empty_reason": "当日空仓",
                }
            ]
        )

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        sample = doc["samples"][0]
        self.assertEqual(sample["sample_type"], "live_paper")
        self.assertFalse(sample["selected"])
        self.assertEqual(sample["empty_reason"], "当日空仓")

    def test_save_empty_pending_records_selection_time_and_reason(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        original_now = self.validator._now
        try:
            self.validator._now = lambda: self.validator.dt.datetime(2026, 6, 25, 14, 56, 0)
            self.validator.save_empty_pending("2026-06-25", reason="市场风险空仓")
        finally:
            self.validator._now = original_now

        doc = json.loads((self.validator.DATA_DIR / "pending_recommendations.json").read_text(encoding="utf-8"))
        pending = doc["2026-06-25"]
        self.assertFalse(pending["selected"])
        self.assertEqual(pending["selected_at"], "2026-06-25 14:56:00")
        self.assertEqual(pending["empty_reason"], "市场风险空仓")

    def test_sync_previous_live_paper_records_empty_pending_once(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.validator.PERF_PATH = self.validator.DATA_DIR / "performance.json"
        self.validator.TRADES_PATH = self.validator.DATA_DIR / "trades.json"
        pending_path = self.validator.DATA_DIR / "pending_recommendations.json"
        pending_path.write_text(
            json.dumps(
                {
                    "2026-06-25": {
                        "selected": False,
                        "selected_at": "2026-06-25 14:56:00",
                        "empty_reason": "当日空仓",
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        first = self.validator.sync_previous_live_paper(today="2026-06-26")
        second = self.validator.sync_previous_live_paper(today="2026-06-26")

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        live_samples = [s for s in doc["samples"] if s.get("sample_type") == "live_paper"]
        self.assertEqual(first["status"], "empty")
        self.assertEqual(second["status"], "already_synced")
        self.assertEqual(len(live_samples), 1)
        self.assertFalse(live_samples[0]["selected"])
        self.assertEqual(live_samples[0]["selected_at"], "2026-06-25 14:56:00")

    def test_sync_previous_live_paper_uses_tail_advice_to_next_open_for_recommendation(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.validator.PERF_PATH = self.validator.DATA_DIR / "performance.json"
        self.validator.TRADES_PATH = self.validator.DATA_DIR / "trades.json"
        pending_path = self.validator.DATA_DIR / "pending_recommendations.json"
        pending_path.write_text(
            json.dumps(
                {
                    "2026-06-25": [
                        {
                            "symbol": "600001",
                            "name": "测试股",
                            "selected_at": "2026-06-25 14:55:12",
                            "score": 72.5,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        original_get_daily_kline = self.validator.data_loader.get_daily_kline
        try:
            self.validator.data_loader.get_daily_kline = lambda symbol, days=10: kline(
                [
                    ["2026-06-25", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-26", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            )
            result = self.validator.sync_previous_live_paper(today="2026-06-26")
        finally:
            self.validator.data_loader.get_daily_kline = original_get_daily_kline

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        sample = doc["samples"][0]
        self.assertEqual(result["status"], "validated")
        self.assertLess(sample["buy_price"], 10.0)
        self.assertEqual(sample["buy_price_source"], "T_tail_advice_proxy_no_minutes")
        self.assertEqual(sample["sell_price"], 10.5)
        self.assertEqual(sample["sell_price_source"], "T1_open")
        self.assertEqual(sample["sell_reason"], "next_open")
        self.assertEqual(sample["selected_at"], "2026-06-25 14:55:12")
        self.assertEqual(sample["score"], 72.5)

    def test_validate_close_to_next_open_uses_open_window_average_when_available(self):
        original_get_daily_kline = self.validator.data_loader.get_daily_kline
        original_load_config = self.validator.data_loader.load_config
        original_open_window = self.validator._get_open_window_average_sell_price
        try:
            self.validator.data_loader.get_daily_kline = lambda symbol, days=10: kline(
                [
                    ["2026-06-25", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-26", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            )
            self.validator.data_loader.load_config = lambda: {
                "validation": {
                    "sell_mode": "open_window_avg",
                    "sell_window_start": "09:30",
                    "sell_window_end": "09:40",
                }
            }
            self.validator._get_open_window_average_sell_price = (
                lambda symbol, date_str, window_start="09:30", window_end="09:40":
                (10.567, "T1_open_window_avg_09:30_09:40")
            )

            result = self.validator.validate_close_to_next_open(
                "600001",
                "测试股",
                "2026-06-25",
                "2026-06-26",
            )
        finally:
            self.validator.data_loader.get_daily_kline = original_get_daily_kline
            self.validator.data_loader.load_config = original_load_config
            self.validator._get_open_window_average_sell_price = original_open_window

        self.assertEqual(result["sell_price"], 10.567)
        self.assertEqual(result["sell_reason"], "next_open_window")
        self.assertEqual(result["sell_price_source"], "T1_open_window_avg_09:30_09:40")

    def test_validator_uses_tail_advice_proxy_buy_when_configured(self):
        original_get_daily_kline = self.validator.data_loader.get_daily_kline
        original_load_config = self.validator.data_loader.load_config
        try:
            self.validator.data_loader.get_daily_kline = lambda symbol, days=10: kline(
                [
                    ["2026-06-25", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-26", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            )
            self.validator.data_loader.load_config = lambda: {
                "execution_model": {"buy_mode": "tail_advice", "buy_time": "14:45"},
                "validation": {"sell_mode": "next_open"},
            }

            result = self.validator.validate_close_to_next_open(
                "600001",
                "测试股",
                "2026-06-25",
                "2026-06-26",
            )
        finally:
            self.validator.data_loader.get_daily_kline = original_get_daily_kline
            self.validator.data_loader.load_config = original_load_config

        self.assertLess(result["buy_price"], 10.0)
        self.assertEqual(result["buy_price_source"], "T_tail_advice_proxy_no_minutes")
        self.assertEqual(result["sell_price"], 10.5)
        self.assertEqual(result["sell_price_source"], "T1_open")

    def test_sync_previous_live_paper_fills_missing_name_from_quote(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.validator.PERF_PATH = self.validator.DATA_DIR / "performance.json"
        self.validator.TRADES_PATH = self.validator.DATA_DIR / "trades.json"
        pending_path = self.validator.DATA_DIR / "pending_recommendations.json"
        pending_path.write_text(
            json.dumps({"2026-06-25": [{"symbol": "600001", "name": ""}]}, ensure_ascii=False),
            encoding="utf-8",
        )

        original_get_daily_kline = self.validator.data_loader.get_daily_kline
        original_tencent_quote = self.validator.data_loader.tencent_quote
        try:
            self.validator.data_loader.get_daily_kline = lambda symbol, days=10: kline(
                [
                    ["2026-06-25", 9.5, 10.2, 9.4, 10.0, 1000, 100000],
                    ["2026-06-26", 10.5, 11.0, 10.4, 10.8, 1200, 120000],
                ]
            )
            self.validator.data_loader.tencent_quote = lambda codes: {"600001": {"name": "腾讯名称"}}
            self.validator.sync_previous_live_paper(today="2026-06-26")
        finally:
            self.validator.data_loader.get_daily_kline = original_get_daily_kline
            self.validator.data_loader.tencent_quote = original_tencent_quote

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(doc["samples"][0]["name"], "腾讯名称")

    def test_sync_previous_live_paper_can_validate_from_sqlite_cache(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.validator.PERF_PATH = self.validator.DATA_DIR / "performance.json"
        self.validator.TRADES_PATH = self.validator.DATA_DIR / "trades.json"
        self.validator.CACHE_DB = self.validator.DATA_DIR / "cache" / "backtest_kline.db"
        self.validator.CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
        pending_path = self.validator.DATA_DIR / "pending_recommendations.json"
        pending_path.write_text(
            json.dumps({"2026-06-25": [{"symbol": "600001", "name": "测试股"}]}, ensure_ascii=False),
            encoding="utf-8",
        )

        import sqlite3
        conn = sqlite3.connect(str(self.validator.CACHE_DB))
        conn.execute(
            """
            CREATE TABLE kline_cache (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                cached_at TEXT,
                cache_version TEXT,
                PRIMARY KEY (symbol, date)
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO kline_cache
            (symbol, date, open, high, low, close, volume, amount, cached_at, cache_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("600001", "2026-06-25", 9.5, 10.2, 9.4, 10.0, 1000, 100000, "now", "test"),
                ("600001", "2026-06-26", 10.5, 11.0, 10.4, 10.8, 1200, 120000, "now", "test"),
            ],
        )
        conn.commit()
        conn.close()

        original_get_daily_kline = self.validator.data_loader.get_daily_kline
        try:
            self.validator.data_loader.get_daily_kline = lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("cache hit should not fetch network kline")
            )
            result = self.validator.sync_previous_live_paper(today="2026-06-26")
        finally:
            self.validator.data_loader.get_daily_kline = original_get_daily_kline

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        sample = doc["samples"][0]
        self.assertEqual(result["status"], "validated")
        self.assertLess(sample["buy_price"], 10.0)
        self.assertEqual(sample["buy_price_source"], "T_tail_advice_proxy_no_minutes")
        self.assertEqual(sample["sell_price"], 10.5)
        self.assertEqual(sample["sell_price_source"], "T1_open")

    def test_sync_previous_live_paper_retries_unverifiable_sample(self):
        self.validator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.validator.PERF_PATH = self.validator.DATA_DIR / "performance.json"
        self.validator.TRADES_PATH = self.validator.DATA_DIR / "trades.json"
        self.validator.SAMPLE_POOL_PATH.write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-25",
                            "sample_type": "live_paper",
                            "selected": False,
                            "symbol": "600172",
                            "name": "黄河旋风",
                            "buy_date": "2026-06-25",
                            "sell_date": "2026-06-26",
                            "buy_price": 0,
                            "sell_price": 0,
                            "return": 0,
                            "sell_reason": "no_valid_kline",
                            "empty_reason": "数据不足以验证: 无法获取 600172 的日K线",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        original_get_daily_kline = self.validator.data_loader.get_daily_kline
        try:
            self.validator.data_loader.get_daily_kline = lambda symbol, days=10: kline(
                [
                    ["2026-06-25", 16.83, 18.81, 15.60, 18.27, 401468168, 6812273190],
                    ["2026-06-26", 17.45, 17.78, 16.54, 16.90, 230968738, 3976775633],
                ]
            )
            result = self.validator.sync_previous_live_paper(today="2026-06-26")
        finally:
            self.validator.data_loader.get_daily_kline = original_get_daily_kline

        doc = json.loads(self.validator.SAMPLE_POOL_PATH.read_text(encoding="utf-8"))
        sample = [s for s in doc["samples"] if s.get("sample_type") == "live_paper"][0]
        self.assertEqual(result["status"], "validated")
        self.assertTrue(sample["selected"])
        self.assertLess(sample["buy_price"], 18.27)
        self.assertEqual(sample["buy_price_source"], "T_tail_advice_proxy_no_minutes")
        self.assertEqual(sample["sell_price"], 17.45)
        self.assertEqual(sample["sell_price_source"], "T1_open")
        self.assertEqual(sample["gross_return"], -0.026)
        self.assertEqual(sample["net_return"], -0.028)
        self.assertEqual(sample["return"], sample["net_return"])
        self.assertNotIn("empty_reason", sample)


class ReportDataIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.report_generator = importlib.import_module("report_generator")
        self.report_generator.DATA_DIR = self.base / "data"
        self.report_generator.CONFIG_PATH = self.base / "config" / "strategy_params.json"
        self.report_generator.REPORTS_DIR = self.base / "reports"
        self.report_generator.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.report_generator.CONFIG_PATH.write_text(
            json.dumps({"factors": {}, "risk_control": {}}, ensure_ascii=False),
            encoding="utf-8",
        )
        self.report_generator.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (self.report_generator.DATA_DIR / "trades.json").write_text(
            json.dumps(
                {
                    "trades": [
                        {
                            "symbol": "600724",
                            "name": "历史样本",
                            "buy_date": "2026-06-25",
                            "buy_price": 6.11,
                            "sell_price": 6.11,
                            "return": 0,
                        }
                    ]
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
                            "date": "2026-06-25",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600724",
                            "return": 0,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_validation_section_ignores_historical_training_samples(self):
        content = self.report_generator._render_validation([], "2026-06-26")

        self.assertIn("无实际执行验证记录", content)
        self.assertNotIn("600724", content)

    def test_validation_section_shows_live_empty_position(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-25",
                            "sample_type": "live_paper",
                            "selected": False,
                            "empty_reason": "当日空仓",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_validation([], "2026-06-26")

        self.assertIn("2026-06-25", content)
        self.assertIn("空仓", content)
        self.assertIn("当日空仓", content)

    def test_validation_section_shows_selection_execution_time(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-25",
                            "sample_type": "live_paper",
                            "selected": True,
                            "symbol": "600001",
                            "name": "测试股",
                            "selected_at": "2026-06-25 14:55:12",
                            "buy_price": 10,
                            "sell_price": 10.5,
                            "return": 0.05,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_validation([], "2026-06-26")

        self.assertIn("昨日选股执行时间：2026-06-25 14:55:12", content)
        self.assertIn("测试股", content)

    def test_history_section_includes_empty_training_days(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-25",
                            "sample_type": "historical_training",
                            "selected": False,
                            "empty_reason": "缺少有效次日开盘验证数据",
                        },
                        {
                            "date": "2026-06-24",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600843",
                            "buy_price": 8.77,
                            "sell_price": 8.72,
                            "return": -0.0057,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_history([])

        self.assertIn("2026-06-25", content)
        self.assertIn("空仓", content)
        self.assertIn("缺少有效次日开盘验证数据", content)
        self.assertIn("600843", content)

    def test_history_section_fills_missing_name_from_trades(self):
        (self.report_generator.DATA_DIR / "trades.json").write_text(
            json.dumps(
                {
                    "trades": [
                        {
                            "date": "2026-06-24",
                            "symbol": "600843",
                            "name": "上工申贝",
                        }
                    ]
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
                            "symbol": "600843",
                            "name": "",
                            "buy_price": 8.77,
                            "sell_price": 8.72,
                            "return": -0.0057,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_history([])

        self.assertIn("| 2026-06-24 | 出手 | 600843 | 上工申贝 |", content)

    def test_history_section_prefers_historical_training_over_live_paper_same_date(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-25",
                            "sample_type": "historical_training",
                            "selected": False,
                            "empty_reason": "缺少有效次日开盘验证数据",
                        },
                        {
                            "date": "2026-06-25",
                            "sample_type": "live_paper",
                            "selected": True,
                            "symbol": "600172",
                            "name": "黄河旋风",
                            "buy_price": 18.27,
                            "sell_price": 17.45,
                            "return": -0.0449,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_history([])

        self.assertIn("| 2026-06-25 | 空仓 | - | - | - | - | - | - | 缺少有效次日开盘验证数据 |", content)
        self.assertNotIn("600172", content)

    def test_history_section_does_not_truncate_to_recent_10(self):
        samples = []
        for day in range(1, 13):
            samples.append(
                {
                    "date": f"2026-06-{day:02d}",
                    "sample_type": "historical_training",
                    "selected": False,
                    "empty_reason": "测试空仓",
                }
            )
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps({"samples": samples}, ensure_ascii=False),
            encoding="utf-8",
        )

        content = self.report_generator._render_history([])

        self.assertIn("完整历史训练记录", content)
        self.assertIn("2026-06-01", content)
        self.assertIn("2026-06-12", content)

    def test_live_execution_section_keeps_actual_live_paper_records_separate(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-25",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600078",
                            "name": "澄星股份",
                            "buy_price": 15.29,
                            "sell_price": 14.81,
                            "return": -0.0314,
                        },
                        {
                            "date": "2026-06-25",
                            "sample_type": "live_paper",
                            "selected": True,
                            "symbol": "600172",
                            "name": "黄河旋风",
                            "selected_at": "2026-06-25 14:55:12",
                            "buy_price": 18.27,
                            "sell_price": 17.45,
                            "return": -0.0449,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_live_execution_history()

        self.assertIn("实际执行验证记录", content)
        self.assertIn("| 2026-06-25 | 出手 | 600172 | 黄河旋风 |", content)
        self.assertIn("2026-06-25 14:55:12", content)
        self.assertNotIn("600078", content)

    def test_render_report_includes_coverage_simulation_section(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-24",
                            "sample_type": "historical_training",
                            "candidate_pool": [
                                {
                                    "symbol": "600001",
                                    "score": 80,
                                    "factor_scores": {"score": 80},
                                    "return": 0.01,
                                }
                            ],
                        },
                        {
                            "date": "2026-06-25",
                            "sample_type": "historical_training",
                            "candidate_pool": [
                                {
                                    "symbol": "600002",
                                    "score": 70,
                                    "factor_scores": {"score": 70},
                                    "return": -0.01,
                                }
                            ],
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator.render_report({"date": "2026-06-26"})

        self.assertIn("## 六、高出手率模拟", content)
        self.assertIn("目标出手率", content)
        self.assertIn("85%", content)

    def test_render_report_includes_walk_forward_validation_summary(self):
        (self.report_generator.DATA_DIR / "strategy_version.json").write_text(
            json.dumps(
                {
                    "version": "1.0.12",
                    "next_optimize_date": "2026-07-04",
                    "history": [
                        {
                            "version": "1.0.12",
                            "strategy_mode": "single_formal_balance",
                            "train_backtest": {
                                "samples": 182,
                                "trade_samples": 79,
                                "win_rate": 0.7468,
                                "avg_return": 0.0045,
                                "max_consecutive_loss": 2,
                            },
                            "validation_backtest": {
                                "samples": 78,
                                "trade_samples": 27,
                                "win_rate": 0.8148,
                                "avg_return": 0.0064,
                                "max_consecutive_loss": 2,
                            },
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator.render_report({"date": "2026-06-26"})

        self.assertIn("训练/验证分段", content)
        self.assertIn("| 训练段 | 79/182 | 74.68% | 0.45% | 2 |", content)
        self.assertIn("| 最近验证段 | 27/78 | 81.48% | 0.64% | 2 |", content)

    def test_recommendation_section_shows_tail_execution_advice(self):
        self.report_generator.CONFIG_PATH.write_text(
            json.dumps(
                {
                    "factors": {
                        "F1_tail_fund_inflow": {"desc": "尾盘资金净流入"},
                        "F3_technical_pattern": {"desc": "技术形态"},
                        "F4_tail_rally_strength": {"desc": "尾盘拉升强度"},
                    },
                    "risk_control": {},
                    "execution_advice": {
                        "window_start": "14:40",
                        "window_end": "14:55",
                        "preferred_price": "靠近尾盘均价，不追全天高位",
                        "confirm_condition": "尾盘资金和量价继续确认",
                        "give_up_condition": "14:50后冲到全天高位附近且承接转弱",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_recommendations(
            [
                {
                    "symbol": "600001",
                    "name": "测试股",
                    "score": 80,
                    "F1_tail_fund_inflow": 88,
                    "F3_technical_pattern": 82,
                    "F4_tail_rally_strength": 79,
                }
            ],
            self.report_generator._load_config(),
        )

        self.assertIn("建议执行窗口：14:40-14:55", content)
        self.assertIn("靠近尾盘均价，不追全天高位", content)
        self.assertIn("尾盘资金和量价继续确认", content)
        self.assertIn("14:50后冲到全天高位附近且承接转弱", content)

    def test_recommendation_section_shows_tail_execution_advice_when_empty(self):
        config = {
            "factors": {},
            "risk_control": {},
            "execution_advice": {
                "window_start": "14:40",
                "window_end": "14:55",
                "preferred_price": "靠近尾盘均价，不追全天高位",
                "confirm_condition": "尾盘资金和量价继续确认",
                "give_up_condition": "14:50后冲到全天高位附近且承接转弱",
            },
        }

        content = self.report_generator._render_recommendations([], config)

        self.assertIn("今日无满足阈值的推荐，空仓观望", content)
        self.assertIn("建议执行窗口：14:40-14:55", content)
        self.assertIn("靠近尾盘均价，不追全天高位", content)

    def test_execution_timing_advice_uses_candidate_intraday_strength(self):
        config = {
            "factors": {},
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "early_entry_threshold_score": 80, "checkpoints": ["10:00"]},
        }

        advice, condition = self.report_generator._eval_early_entry_condition(
            {"market_overview": {"sh_pct": 0.004, "limit_up_count": 50, "limit_down_count": 5}},
            {
                "score": 86,
                "intraday_profile": {
                    "pct_change": 0.018,
                    "position_in_range": 0.62,
                    "tail_return": 0.006,
                    "tail_volume_share": 0.18,
                    "drawdown_from_high": 0.012,
                    "volume_ratio": 1.25,
                },
            },
            config,
            {"sh_pct": 0.004, "limit_up_count": 50, "limit_down_count": 5},
        )

        self.assertIn("分批提前介入", advice)
        self.assertIn("今日行情偏强", condition)
        self.assertIn("分时承接", condition)

    def test_execution_timing_advice_gives_up_on_intraday_reversal(self):
        config = {
            "factors": {},
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "early_entry_threshold_score": 80, "checkpoints": ["10:00"]},
        }

        advice, condition = self.report_generator._eval_early_entry_condition(
            {"market_overview": {"sh_pct": 0.002, "limit_up_count": 30, "limit_down_count": 8}},
            {
                "score": 88,
                "intraday_profile": {
                    "pct_change": 0.045,
                    "position_in_range": 0.96,
                    "tail_return": -0.012,
                    "tail_volume_share": 0.08,
                    "drawdown_from_high": 0.035,
                    "volume_ratio": 2.2,
                },
            },
            config,
            {"sh_pct": 0.002, "limit_up_count": 30, "limit_down_count": 8},
        )

        self.assertIn("放弃买入", advice)
        self.assertIn("冲高回落", condition)

    def test_execution_timing_advice_waits_when_market_is_shocked(self):
        config = {
            "factors": {},
            "selection": {"min_factor_scores": {}, "max_factor_scores": {}},
            "execution_advice": {"window_start": "14:40", "window_end": "14:55"},
            "execution_revisit": {"enabled": True, "early_entry_threshold_score": 80, "checkpoints": ["10:00"]},
        }

        advice, condition = self.report_generator._eval_early_entry_condition(
            {"market_overview": {"sh_pct": -0.031, "limit_up_count": 20, "limit_down_count": 80}},
            {
                "score": 91,
                "intraday_profile": {
                    "pct_change": 0.018,
                    "position_in_range": 0.58,
                    "tail_return": 0.004,
                    "tail_volume_share": 0.18,
                    "drawdown_from_high": 0.01,
                },
            },
            config,
            {"sh_pct": -0.031, "limit_up_count": 20, "limit_down_count": 80},
        )

        self.assertIn("不建议提前", advice)
        self.assertIn("今日行情偏弱", condition)

    def test_history_section_shows_buy_price_source(self):
        (self.report_generator.DATA_DIR / "strategy_samples.json").write_text(
            json.dumps(
                {
                    "samples": [
                        {
                            "date": "2026-06-24",
                            "sample_type": "historical_training",
                            "selected": True,
                            "symbol": "600843",
                            "name": "上工申贝",
                            "buy_price": 8.77,
                            "sell_price": 8.72,
                            "buy_price_source": "T_close",
                            "sell_price_source": "T1_open",
                            "return": -0.0057,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator._render_history([])

        self.assertIn("买入价来源", content)
        self.assertIn("T_close", content)

    def test_render_report_includes_history_and_actual_execution_sections(self):
        content = self.report_generator.render_report({"date": "2026-06-26"})

        self.assertNotIn("昨日推荐验证结果", content)
        self.assertIn("## 三、今日优选", content)
        self.assertIn("## 四、完整历史训练记录", content)
        self.assertIn("## 五、实际执行验证记录", content)
        self.assertIn("## 六、高出手率模拟", content)
        self.assertNotIn("## 五、完整历史训练记录", content)

    def test_render_report_includes_strategy_rule_and_parameter_explanations(self):
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
                    "prefilter": {
                        "price_min": 3,
                        "price_max": 100,
                        "amount_min": 50000000,
                    },
                    "selection": {
                        "top_n": 1,
                        "score_threshold": 55,
                        "market_drop_threshold": -0.02,
                        "counterfactual_rescue": {
                            "enabled": True,
                            "rescue_score_threshold": 80,
                        },
                        "neighbor_counterfactual_rescue": {
                            "enabled": True,
                            "neighbor_factor_keys": [
                                "F1_tail_fund_inflow",
                                "CTX_F1_percentile",
                            ],
                        },
                    },
                    "execution_model": {"buy_mode": "tail_advice"},
                    "validation": {"sell_mode": "next_open"},
                    "optimization": {"review_window": 30},
                    "risk_control": {"max_consecutive_loss": 3},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        content = self.report_generator.render_report({"date": "2026-06-26"})

        self.assertIn("## 十、策略规则与参数说明", content)
        self.assertIn("F1_tail_fund_inflow", content)
        self.assertIn("main_net_1430_1500 / float_mv", content)
        self.assertIn("score_threshold", content)
        self.assertIn("market_drop_threshold", content)
        self.assertIn("counterfactual_rescue", content)
        self.assertIn("neighbor_counterfactual_rescue", content)
        self.assertIn("CTX_F1_percentile", content)


class RunTodayReportFlowTests(unittest.TestCase):
    def test_run_today_report_syncs_previous_live_paper_without_training(self):
        main = importlib.import_module("main")
        strategy_engine = importlib.import_module("strategy_engine")
        report_generator = importlib.import_module("report_generator")
        validator = importlib.import_module("validator")
        backtest_runner = importlib.import_module("backtest_runner")

        calls = []
        original_sync = validator.sync_previous_live_paper
        original_run_selection = strategy_engine.run_selection
        original_generate = report_generator.generate
        original_save_empty = validator.save_empty_pending
        original_run_backtest = backtest_runner.run_backtest
        try:
            validator.sync_previous_live_paper = lambda: calls.append("sync") or {
                "status": "empty",
                "date": "2026-06-25",
                "validated": 0,
            }
            strategy_engine.run_selection = lambda **kwargs: calls.append("selection") or {
                "date": "2026-06-26",
                "recommendations": [],
                "total_candidates": 0,
                "total_scored": 0,
                "empty_reason": "测试空仓",
            }
            report_generator.generate = lambda result: calls.append("report") or Path("/tmp/report.md")
            validator.save_empty_pending = lambda date_str=None, reason="": calls.append("save_empty")
            backtest_runner.run_backtest = lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("run_today_report must not train history")
            )

            main.cmd_run_today_report()
        finally:
            validator.sync_previous_live_paper = original_sync
            strategy_engine.run_selection = original_run_selection
            report_generator.generate = original_generate
            validator.save_empty_pending = original_save_empty
            backtest_runner.run_backtest = original_run_backtest

        self.assertEqual(calls[:2], ["sync", "selection"])
        self.assertIn("report", calls)
        self.assertNotIn("train", calls)

    def test_train_history_regenerates_single_daily_report_with_today_pick_section(self):
        main = importlib.import_module("main")
        backtest_runner = importlib.import_module("backtest_runner")
        report_generator = importlib.import_module("report_generator")
        feedback_loop = importlib.import_module("feedback_loop")

        calls = []
        original_run_backtest = backtest_runner.run_backtest
        original_generate_training = backtest_runner.generate_training_report
        original_generate_report = report_generator.generate
        original_collect = feedback_loop.collect_metrics
        original_argv = sys.argv
        try:
            sys.argv = ["main.py", "train_history"]
            backtest_runner.run_backtest = lambda trading_days=None, universe_size=150, overrides=None: {
                "samples": [],
                "trades": [],
                "performance": {},
            }
            backtest_runner.generate_training_report = lambda result: calls.append("training_report")
            report_generator.generate = lambda selection: calls.append(selection) or Path("/tmp/daily.md")
            feedback_loop.collect_metrics = lambda label: "MS-test"

            main.cmd_train_history()
        finally:
            backtest_runner.run_backtest = original_run_backtest
            backtest_runner.generate_training_report = original_generate_training
            report_generator.generate = original_generate_report
            feedback_loop.collect_metrics = original_collect
            sys.argv = original_argv

        self.assertNotIn("training_report", calls)
        self.assertEqual(calls[0]["recommendations"], [])
        self.assertEqual(calls[0]["empty_reason"], "历史训练完成，今日优选保持当前策略实时结果")


if __name__ == "__main__":
    unittest.main()
