import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "_archive" / "study_strategy_01_close_position.py"
spec = importlib.util.spec_from_file_location("study_strategy_01_close_position", MODULE_PATH)
study = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["study_strategy_01_close_position"] = study
spec.loader.exec_module(study)


def test_close_position_bucket_names_ranges():
    assert study.close_position_bucket(70) == "65-85"
    assert study.close_position_bucket(90) == "85-95"
    assert study.close_position_bucket(98) == "95-99.5"
    assert study.close_position_bucket(100) == "99.5+"


def test_tradeability_bucket_splits_unsealed_and_strong_sealed():
    assert study.tradeability_bucket(9.7, 97.0) == "可成交强势"
    assert study.tradeability_bucket(10.0, 100.0) == "强封可能不可成交"
    assert study.tradeability_bucket(8.8, 90.0) == "弱封/回落"


def test_summarize_bucket_reports_open_and_high_returns():
    rows = [
        {"bucket": "A", "open_return_pct": 1.0, "high_return_pct": 3.0},
        {"bucket": "A", "open_return_pct": -1.0, "high_return_pct": 2.0},
        {"bucket": "B", "open_return_pct": 2.0, "high_return_pct": 4.0},
    ]
    summary = study.summarize_bucket(rows, "bucket")
    assert summary[0]["bucket"] == "A"
    assert summary[0]["samples"] == 2
    assert summary[0]["open_win_rate"] == 50.0
    assert summary[0]["avg_high_return"] == 2.5
