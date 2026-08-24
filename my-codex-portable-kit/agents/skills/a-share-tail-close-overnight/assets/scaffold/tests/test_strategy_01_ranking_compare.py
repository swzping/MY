import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "_archive" / "compare_strategy_01_rankings.py"
spec = importlib.util.spec_from_file_location("compare_strategy_01_rankings", MODULE_PATH)
compare = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["compare_strategy_01_rankings"] = compare
spec.loader.exec_module(compare)


def test_topic_heat_ranker_prefers_hotter_topic_after_score():
    low_heat = {"score": 100, "topic_heat": 1, "close_position_pct": 100, "amount_yi": 300}
    high_heat = {"score": 100, "topic_heat": 5, "close_position_pct": 90, "amount_yi": 10}
    assert compare.by_topic_heat(high_heat) > compare.by_topic_heat(low_heat)


def test_summarize_reports_win_rate_and_average():
    rows = [
        {"open_return_pct": 2.0, "ranking_gap_pct": 1.0},
        {"open_return_pct": -1.0, "ranking_gap_pct": 4.0},
        {"open_return_pct": 3.0, "ranking_gap_pct": 0.0},
    ]
    summary = compare.summarize(rows)
    assert round(summary["win_rate"], 1) == 66.7
    assert round(summary["avg_return"], 2) == 1.33
    assert round(summary["avg_gap"], 2) == 1.67


def test_low_price_relay_prefers_lower_price_after_topic_heat():
    expensive = {"score": 100, "topic_heat": 3, "buy_price": 91.23, "close_position_pct": 100, "amount_yi": 209.18}
    cheap = {"score": 100, "topic_heat": 3, "buy_price": 4.66, "close_position_pct": 100, "amount_yi": 2.33}
    assert compare.by_low_price_relay(cheap) > compare.by_low_price_relay(expensive)


def test_filter_candidates_can_keep_only_01b():
    candidates = [
        {"code": "000001", "branch": "01A"},
        {"code": "000002", "branch": "01B"},
    ]
    assert compare.filter_candidates(candidates, "01B") == [{"code": "000002", "branch": "01B"}]


def test_evaluate_ranker_records_best_possible_gap(monkeypatch):
    candidate_map = {
        "2026-06-22": [
            {"date": "2026-06-22", "code": "600584", "name": "长电科技", "branch": "01B", "score": 100, "buy_price": 91.23, "close_position_pct": 100, "amount_yi": 209.18, "topic_heat": 2},
            {"date": "2026-06-22", "code": "002418", "name": "康盛股份", "branch": "01B", "score": 100, "buy_price": 4.66, "close_position_pct": 100, "amount_yi": 2.33, "topic_heat": 2},
        ]
    }

    def fake_review(row):
        returns = {"600584": 0.8, "002418": 10.09}
        return {**row, "next_date": "2026-06-23", "open_return_pct": returns[row["code"]]}

    monkeypatch.setattr(compare.backtest, "evaluate_next_open", fake_review)

    rows = compare.evaluate_ranker(candidate_map, compare.by_liquid_leader, branch="01B")

    assert rows[0]["code"] == "600584"
    assert rows[0]["best_possible_code"] == "002418"
    assert round(rows[0]["ranking_gap_pct"], 2) == 9.29
