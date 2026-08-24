import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_daily_tail_strategy.py"
spec = importlib.util.spec_from_file_location("run_daily_tail_strategy", MODULE_PATH)
daily = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["run_daily_tail_strategy"] = daily
spec.loader.exec_module(daily)


def test_pick_mode_only_runs_recommendation(tmp_path):
    calls = []

    def fake_run(cmd, cwd, timeout=180):
        calls.append(cmd)
        return 0, "ok"

    with (
        patch.object(sys, "argv", ["run_daily_tail_strategy.py", str(tmp_path), "--date", "2026-06-24", "--mode", "pick"]),
        patch.object(daily.subprocess, "run"),
        patch.object(daily, "run", side_effect=fake_run),
        patch.object(daily, "write_run_report", return_value=tmp_path / "daily.md"),
    ):
        assert daily.main() == 0

    joined = [" ".join(cmd) for cmd in calls]
    assert any("scripts/run_strategy_01.py" in cmd for cmd in joined)
    assert not any("scripts/report_strategy_01_tail_entry.py" in cmd for cmd in joined)
    assert not any("scripts/review_strategy_01_next_open.py" in cmd for cmd in joined)


def test_pick_report_lists_top_three_and_default_trade(tmp_path):
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    data_dir = report_dir / "_data"
    data_dir.mkdir()
    (data_dir / "2026-06-24_candidates.csv").write_text(
        "\ufeff排名,分支,代码,名称,评分,可买入评分,模拟买入价,涨幅%,日内位置%,成交额(亿),MA5,MA10,MA20,止损价,理由,风险\n"
        "1,01B,002897,意华股份,100,100.0,93.16,10.00,100.00,20.00,90,88,84,90.00,强封板,\n"
        "2,01B,600563,法拉电子,100,100.0,178.76,10.00,100.00,18.00,170,165,160,173.00,强封板,\n"
        "3,01B,605277,新亚电子,100,100.0,19.50,10.00,100.00,10.00,18,17,16,18.90,强封板,\n",
        encoding="utf-8",
    )
    (data_dir / "paper_trades.csv").write_text(
        "\ufeff交易日,代码,名称,分支,评分,尾盘买入价,买入时间点,风险,来源\n"
        "2026-06-24,002897,意华股份,01B,100,93.16,收盘价近似,,策略Top1\n",
        encoding="utf-8",
    )

    path = daily.write_pick_report(tmp_path, "2026-06-24", "ok")
    content = path.read_text(encoding="utf-8")

    assert "| 1 | 002897 意华股份 | 01B | 100 | 100.0 | 93.16 | 无 |" in content
    assert "| 3 | 605277 新亚电子 | 01B | 100 | 100.0 | 19.50 | 无 |" in content
    assert "默认纸面交易：002897 意华股份，来源=策略Top1" in content


def test_internal_outputs_are_moved_under_data_dir(tmp_path):
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    for name in [
        "2026-06-24_candidates.csv",
        "2026-06-24_report.md",
        "2026-06-23_next_open_review.csv",
        "2026-06-23_next_open_review.md",
        "paper_trades.csv",
    ]:
        (report_dir / name).write_text("x", encoding="utf-8")
    tail_entry = report_dir / "tail_entry"
    tail_entry.mkdir()
    (tail_entry / "2026-05-20_to_2026-06-24.md").write_text("x", encoding="utf-8")

    daily.consolidate_internal_outputs(tmp_path)

    root_files = sorted(p.name for p in report_dir.iterdir() if p.is_file())
    assert root_files == []
    assert (report_dir / "_data" / "2026-06-24_candidates.csv").exists()
    assert (report_dir / "_data" / "paper_trades.csv").exists()
    assert (report_dir / "_data" / "tail_entry" / "2026-05-20_to_2026-06-24.md").exists()


def test_full_report_combines_today_pick_and_history_metrics(tmp_path):
    report_dir = tmp_path / "reports" / "strategy_01"
    data_dir = report_dir / "_data"
    data_dir.mkdir(parents=True)
    (data_dir / "2026-06-24_candidates.csv").write_text(
        "\ufeff排名,分支,代码,名称,评分,可买入评分,模拟买入价,风险\n"
        "1,01B,002897,意华股份,100,100.0,93.16,\n",
        encoding="utf-8",
    )
    (data_dir / "paper_trades.csv").write_text(
        "\ufeff交易日,代码,名称,分支,评分,尾盘买入价,买入时间点,风险,来源\n"
        "2026-06-24,002897,意华股份,01B,100,93.16,收盘价近似,,策略Top1\n",
        encoding="utf-8",
    )
    tail_entry = data_dir / "tail_entry"
    tail_entry.mkdir()
    (tail_entry / "2026-05-20_to_2026-06-24.md").write_text(
        "\n".join([
            "# 近期尾盘买入与次日收益报告：2026-05-20 到 2026-06-24",
            "- 交易样本：3",
            "- 次日开盘胜率：66.7%",
            "- 平均开盘收益：1.20%",
            "- 中位开盘收益：0.80%",
            "- 平均次日最高收益：3.20%",
            "- 中位次日最高收益：2.80%",
        ]),
        encoding="utf-8",
    )

    path = daily.write_run_report(tmp_path, "2026-06-24", "2026-05-20", "ok", "ok", "")
    content = path.read_text(encoding="utf-8")

    assert "## 今日优选" in content
    assert "| 1 | 002897 意华股份 | 01B | 100 | 100.0 | 93.16 | 无 |" in content
    assert "## 历史交易复盘" in content
    assert "- 样本数：3" in content
    assert "- 次日开盘胜率：66.7%" in content
    assert "## 输出文件" not in content


def test_importing_scaffold_modules_does_not_create_empty_report_dirs(tmp_path):
    scaffold = Path(__file__).resolve().parents[1] / "assets" / "scaffold"
    modules = [
        scaffold / "scripts" / "report_strategy_01_tail_entry.py",
        scaffold / "scripts" / "review_strategy_01_next_open.py",
        scaffold / "scripts" / "_archive" / "analyze_strategy_01_best_profile.py",
        scaffold / "scripts" / "_archive" / "compare_strategy_01_rankings.py",
        scaffold / "scripts" / "_archive" / "study_strategy_01_close_position.py",
    ]
    for index, module_path in enumerate(modules):
        spec = importlib.util.spec_from_file_location(f"import_check_{index}", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

    empty_report_dirs = [
        path for path in (scaffold / "reports").rglob("*")
        if path.is_dir() and not any(path.iterdir())
    ] if (scaffold / "reports").exists() else []
    assert empty_report_dirs == []
