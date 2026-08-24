import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "report_strategy_01_tail_entry.py"
spec = importlib.util.spec_from_file_location("report_strategy_01_tail_entry", MODULE_PATH)
report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["report_strategy_01_tail_entry"] = report
spec.loader.exec_module(report)


def test_return_pct_uses_entry_price():
    assert round(report.return_pct(10, 10.5), 2) == 5.0


def test_pick_best_trade_prefers_open_then_high_return():
    rows = [
        {"code": "A", "open_return_pct": 1.0, "high_return_pct": 5.0},
        {"code": "B", "open_return_pct": 2.0, "high_return_pct": 3.0},
    ]
    assert report.pick_best_trade(rows)["code"] == "B"


def test_tail_entry_label_marks_close_proxy():
    assert report.tail_entry_label(None) == "收盘价近似"
    assert report.tail_entry_label("14:50") == "14:50"


def test_merge_saved_review_uses_saved_next_day_prices():
    candidate = {"date": "2026-06-23", "code": "002584", "name": "西陇科学", "branch": "01B"}
    row = {"买入价": "10.02", "次日开盘": "11.02", "次日最高": "11.02", "次日收盘": "11.02"}
    merged = report.merge_saved_review(candidate, row, "2026-06-24")

    assert merged["next_date"] == "2026-06-24"
    assert round(merged["open_return_pct"], 2) == 9.98
    assert round(merged["high_return_pct"], 2) == 9.98


def test_today_recommendations_read_candidate_csv(tmp_path):
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    (report_dir / "2026-06-24_candidates.csv").write_text(
        "\ufeff排名,分支,代码,名称,评分,模拟买入价,涨幅%,日内位置%,成交额(亿),MA5,MA10,MA20,止损价,理由,风险\n"
        "1,01B,002803,吉宏股份,100,26.13,10.02,100.00,5.10,23.84,22.59,21.95,23.45,强封板,短期乖离偏大\n",
        encoding="utf-8",
    )

    with patch.object(report, "ROOT", tmp_path):
        lines = report.today_recommendation_lines("2026-06-24")

    assert "## 今日入选推荐股" in lines
    assert "| 1 | 002803 吉宏股份 | 01B | 100 | 100 | 26.13 | 短期乖离偏大 |" in lines


def test_today_recommendations_move_unavailable_candidates_to_observation(tmp_path):
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    (report_dir / "2026-06-24_candidates.csv").write_text(
        "\ufeff排名,分支,代码,名称,评分,模拟买入价,涨幅%,日内位置%,成交额(亿),MA5,MA10,MA20,止损价,理由,风险\n"
        "1,01B,600176,中国巨石,100,64.82,9.99,100.00,107.07,58.05,50.77,44.90,57.46,强封板,短期乖离偏大\n"
        "2,01B,603083,剑桥科技,100,262.21,10.00,100.00,76.28,230.88,208.38,200.72,235.65,强封板,短期乖离偏大\n",
        encoding="utf-8",
    )
    (report_dir / "2026-06-24_unavailable.csv").write_text(
        "\ufeff代码,原因\n600176,已涨停不可买入\n",
        encoding="utf-8",
    )

    with patch.object(report, "ROOT", tmp_path):
        lines = report.today_recommendation_lines("2026-06-24")

    content = "\n".join(lines)
    assert "| 1 | 603083 剑桥科技 | 01B | 100 | 100 | 262.21 | 短期乖离偏大 |" in content
    assert "## 不可买入信号观察" in content
    assert "| 600176 中国巨石 | 已涨停不可买入 |" in content


def test_run_report_uses_recent_title_and_today_recommendations(tmp_path):
    out_dir = tmp_path / "tail_entry"
    out_dir.mkdir()
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    (report_dir / "paper_trades.csv").write_text(
        "\ufeff交易日,代码,名称,分支,评分,尾盘买入价,买入时间点,风险,来源\n"
        "2026-06-24,002803,吉宏股份,01B,100,26.13,收盘价近似,,策略Top1\n",
        encoding="utf-8",
    )
    (report_dir / "2026-06-24_next_open_review.csv").write_text(
        "\ufeff代码,买入价,次日开盘,次日最高,次日收盘\n"
        "002803,26.13,27.0,28.0,27.5\n",
        encoding="utf-8",
    )
    (report_dir / "2026-06-24_next_open_review.md").write_text(
        "# 第一策略次日开盘复盘：2026-06-24 -> 2026-06-25\n",
        encoding="utf-8",
    )

    with (
        patch.object(report, "ROOT", tmp_path),
        patch.object(report, "OUT_DIR", out_dir),
        patch.object(report.backtest, "date_range", return_value=["2026-06-24"]),
        patch.object(report, "today_recommendation_lines", return_value=["## 今日入选推荐股", "", "- 暂无今日入选推荐股。"]),
    ):
        _, md_path, _ = report.run_report("2026-06-24", "2026-06-24")

    content = md_path.read_text(encoding="utf-8")
    assert content.startswith("# 近期尾盘买入与次日收益报告：2026-06-24 到 2026-06-24")
    assert "## 今日入选推荐股" in content
    assert "## 每日交易" in content
    assert "002803 吉宏股份" in content


def test_run_report_reads_paper_trades_without_rebuilding_candidates(tmp_path):
    out_dir = tmp_path / "tail_entry"
    out_dir.mkdir()
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    (report_dir / "paper_trades.csv").write_text(
        "\ufeff交易日,代码,名称,分支,评分,尾盘买入价,买入时间点,风险,来源\n"
        "2026-06-24,002803,吉宏股份,01B,100,26.13,收盘价近似,,用户确认买入\n",
        encoding="utf-8",
    )
    (report_dir / "2026-06-24_next_open_review.csv").write_text(
        "\ufeff代码,买入价,次日开盘,次日最高,次日收盘\n"
        "002803,26.13,27.0,28.0,27.5\n",
        encoding="utf-8",
    )

    def fail_candidate_scan(_trade_date):
        raise AssertionError("每日交易不应该重新拉取候选池")

    with (
        patch.object(report, "ROOT", tmp_path),
        patch.object(report, "OUT_DIR", out_dir),
        patch.object(report.backtest, "date_range", return_value=["2026-06-24"]),
        patch.object(report.backtest, "candidates_for_date", side_effect=fail_candidate_scan),
        patch.object(report, "today_recommendation_lines", return_value=[]),
    ):
        _, md_path, rows = report.run_report("2026-06-24", "2026-06-24")

    content = md_path.read_text(encoding="utf-8")
    assert len(rows) == 1
    assert "用户确认买入" in content


def test_run_report_marks_trade_source_and_feedback_loop(tmp_path):
    out_dir = tmp_path / "tail_entry"
    out_dir.mkdir()
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    (report_dir / "paper_trades.csv").write_text(
        "\ufeff交易日,代码,名称,分支,评分,尾盘买入价,买入时间点,风险,来源\n"
        "2026-06-24,002897,意华股份,01B,100,93.16,收盘价近似,,策略Top1\n",
        encoding="utf-8",
    )
    (report_dir / "2026-06-24_next_open_review.csv").write_text(
        "\ufeff代码,买入价,次日开盘,次日最高,次日收盘\n"
        "002897,93.16,95.00,98.00,94.00\n",
        encoding="utf-8",
    )

    with (
        patch.object(report, "ROOT", tmp_path),
        patch.object(report, "OUT_DIR", out_dir),
        patch.object(report.backtest, "date_range", return_value=["2026-06-24"]),
        patch.object(report, "today_recommendation_lines", return_value=[]),
    ):
        _, md_path, _ = report.run_report("2026-06-24", "2026-06-24")

    content = md_path.read_text(encoding="utf-8")
    assert "## 策略反馈闭环" in content
    assert "默认Top1样本：1" in content
    assert "| 2026-06-24 | 收盘价近似 | 002897 意华股份 | 93.16 | 1.98% | 5.20% | 策略Top1 |" in content


def test_run_report_can_use_separate_recommendation_date(tmp_path):
    out_dir = tmp_path / "tail_entry"
    out_dir.mkdir()

    with (
        patch.object(report, "OUT_DIR", out_dir),
        patch.object(report.backtest, "date_range", return_value=[]),
        patch.object(report, "today_recommendation_lines", return_value=["## 今日入选推荐股", "", "- 2026-06-24 推荐"]),
    ):
        _, md_path, _ = report.run_report("2026-05-20", "2026-06-01", recommendation_date="2026-06-24")

    content = md_path.read_text(encoding="utf-8")
    assert "# 近期尾盘买入与次日收益报告：2026-05-20 到 2026-06-01" in content
    assert "- 2026-06-24 推荐" in content
