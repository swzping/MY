import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "_archive" / "analyze_strategy_01_best_profile.py"
spec = importlib.util.spec_from_file_location("analyze_strategy_01_best_profile", MODULE_PATH)
profile = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["analyze_strategy_01_best_profile"] = profile
spec.loader.exec_module(profile)


def test_price_bucket_groups_observable_ranges():
    assert profile.price_bucket(4.66) == "0-10"
    assert profile.price_bucket(17.61) == "10-20"
    assert profile.price_bucket(91.23) == "50+"


def test_unique_best_rows_keeps_one_best_per_date():
    rows = [
        {"交易日": "2026-06-22", "事后最佳代码": "002418", "事后最佳名称": "康盛股份", "事后最佳开盘收益%": "10.09"},
        {"交易日": "2026-06-22", "事后最佳代码": "002418", "事后最佳名称": "康盛股份", "事后最佳开盘收益%": "10.09"},
        {"交易日": "2026-06-21", "事后最佳代码": "", "事后最佳名称": "", "事后最佳开盘收益%": ""},
    ]

    best = profile.unique_best_rows(rows)

    assert best == [{"date": "2026-06-22", "code": "002418", "name": "康盛股份", "return_pct": 10.09}]


def test_bucket_summary_counts_rows_and_average_return():
    rows = [
        {"bucket": "0-10", "return_pct": 10.0},
        {"bucket": "0-10", "return_pct": 8.0},
        {"bucket": "10-20", "return_pct": 4.0},
    ]

    summary = profile.bucket_summary(rows, "bucket")

    assert summary[0]["bucket"] == "0-10"
    assert summary[0]["count"] == 2
    assert summary[0]["avg_return_pct"] == 9.0


def test_selection_gap_summary_compares_selected_to_best():
    rows = [
        {"排序规则": "liquid", "买入价": "90", "成交额(亿)": "100", "题材热度": "5", "开盘收益%": "1", "事后最佳代码": "000001"},
        {"排序规则": "liquid", "买入价": "30", "成交额(亿)": "20", "题材热度": "2", "开盘收益%": "4", "事后最佳代码": "000002"},
    ]
    best_features = {
        "000001": {"price": 10, "amount_yi": 5, "topic_heat": 3, "return_pct": 10},
        "000002": {"price": 20, "amount_yi": 10, "topic_heat": 1, "return_pct": 8},
    }

    summary = profile.selection_gap_summary(rows, best_features)

    assert summary[0]["ranker"] == "liquid"
    assert summary[0]["samples"] == 2
    assert summary[0]["avg_price_diff"] == 45.0
    assert summary[0]["avg_amount_diff"] == 52.5
    assert summary[0]["avg_return_gap"] == 6.5
