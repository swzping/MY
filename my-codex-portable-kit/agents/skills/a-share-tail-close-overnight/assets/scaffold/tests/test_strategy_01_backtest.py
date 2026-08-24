import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "_archive" / "backtest_strategy_01.py"
spec = importlib.util.spec_from_file_location("backtest_strategy_01", MODULE_PATH)
backtest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["backtest_strategy_01"] = backtest
spec.loader.exec_module(backtest)


def test_pick_daily_top_prefers_high_score_then_position():
    rows = [
        {"code": "000001", "score": 80, "close_position_pct": 90, "amount_yi": 2},
        {"code": "000002", "score": 90, "close_position_pct": 70, "amount_yi": 1},
        {"code": "000003", "score": 90, "close_position_pct": 95, "amount_yi": 1},
    ]
    assert backtest.pick_daily_top(rows)["code"] == "000003"


def test_open_return_pct_uses_buy_price_and_next_open():
    assert round(backtest.open_return_pct(10, 10.5), 2) == 5.00


def test_pick_daily_top_prefers_liquid_leader_for_01b_tie():
    rows = [
        {"code": "600584", "branch": "01B", "score": 100, "close_position_pct": 100, "amount_yi": 209.18, "price": 91.23},
        {"code": "002418", "branch": "01B", "score": 100, "close_position_pct": 100, "amount_yi": 2.33, "price": 4.66},
    ]
    assert backtest.pick_daily_top(rows)["code"] == "600584"


def test_date_range_uses_weekdays_only():
    assert backtest.date_range("2026-06-19", "2026-06-22") == ["2026-06-19", "2026-06-22"]


def test_topic_heat_counts_reason_tags_once_per_stock():
    pool = [
        {"reason": "光模块+AI算力+光模块"},
        {"reason": "AI算力+PCB"},
    ]
    heat = backtest.topic_heat(pool)
    assert heat["光模块"] == 1
    assert heat["AI算力"] == 2
