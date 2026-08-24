#!/usr/bin/env python3
"""Run the standalone tail-close overnight strategy inside a target workspace."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
INIT_SCRIPT = SKILL_DIR / "scripts" / "init_tail_strategy.py"
REPORT_SUBDIR = Path("reports") / "strategy_01"
DATA_SUBDIR = REPORT_SUBDIR / "_data"


def run(cmd: list[str], cwd: Path, timeout: int = 180) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return 124, f"[超时 {timeout}s]\n{output}"


def latest_weekday(before_or_equal: date) -> date:
    cur = before_or_equal
    while cur.weekday() >= 5:
        cur -= timedelta(days=1)
    return cur


def one_month_start(end: date) -> date:
    return end - timedelta(days=35)


def report_dir(workspace: Path) -> Path:
    return workspace / REPORT_SUBDIR


def data_dir(workspace: Path) -> Path:
    return workspace / DATA_SUBDIR


def archive_dir(workspace: Path) -> Path:
    return report_dir(workspace) / "_archive"


def report_data_path(workspace: Path, name: str) -> Path:
    internal = data_dir(workspace) / name
    if internal.exists():
        return internal
    return report_dir(workspace) / name


def read_top_candidate(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else None


def read_candidate_rows(path: Path, limit: int = 3) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))[:limit]


def read_paper_trade(workspace: Path, trade_date: str) -> dict[str, str] | None:
    path = report_data_path(workspace, "paper_trades.csv")
    if not path.exists():
        return None
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("交易日") == trade_date:
                return row
    return None


def move_if_exists(src: Path, dst: Path) -> None:
    if not src.exists() or src.resolve() == dst.resolve():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    src.rename(dst)


def consolidate_internal_outputs(workspace: Path) -> None:
    base = report_dir(workspace)
    internal = data_dir(workspace)
    internal.mkdir(parents=True, exist_ok=True)
    patterns = [
        "*_candidates.csv",
        "*_report.md",
        "*_next_open_review.csv",
        "*_next_open_review.md",
        "*_unavailable.csv",
        "paper_trades.csv",
    ]
    for pattern in patterns:
        for path in base.glob(pattern):
            move_if_exists(path, internal / path.name)
    for dirname in ["tail_entry"]:
        src_dir = base / dirname
        if not src_dir.exists():
            continue
        dst_dir = internal / dirname
        dst_dir.mkdir(parents=True, exist_ok=True)
        for path in src_dir.rglob("*"):
            if path.is_file():
                move_if_exists(path, dst_dir / path.relative_to(src_dir))
        for path in sorted(src_dir.rglob("*"), reverse=True):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        try:
            src_dir.rmdir()
        except OSError:
            pass
    archive = archive_dir(workspace)
    for dirname in ["backtests", "ranking_compare", "best_profile", "close_position_study"]:
        src_dir = base / dirname
        if not src_dir.exists():
            continue
        dst_dir = archive / dirname
        dst_dir.mkdir(parents=True, exist_ok=True)
        for path in src_dir.rglob("*"):
            if path.is_file():
                move_if_exists(path, dst_dir / path.relative_to(src_dir))
        for path in sorted(src_dir.rglob("*"), reverse=True):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        try:
            src_dir.rmdir()
        except OSError:
            pass


def read_tail_metrics(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    metrics: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- 交易样本："):
            metrics["samples"] = line.split("：", 1)[1]
        elif line.startswith("- 次日开盘胜率："):
            metrics["win_rate"] = line.split("：", 1)[1]
        elif line.startswith("- 平均开盘收益："):
            metrics["avg_open"] = line.split("：", 1)[1]
        elif line.startswith("- 中位开盘收益："):
            metrics["median_open"] = line.split("：", 1)[1]
        elif line.startswith("- 平均次日最高收益："):
            metrics["avg_high"] = line.split("：", 1)[1]
        elif line.startswith("- 中位次日最高收益："):
            metrics["median_high"] = line.split("：", 1)[1]
    return metrics


def write_run_report(
    workspace: Path,
    trade_date: str,
    start_date: str,
    recommendation_output: str,
    rolling_output: str,
    review_output: str,
) -> Path:
    base = report_dir(workspace)
    base.mkdir(parents=True, exist_ok=True)
    report_path = base / f"daily_run_{trade_date}.md"
    daily_strategy_report = report_data_path(workspace, f"{trade_date}_report.md")
    daily_candidates_csv = report_data_path(workspace, f"{trade_date}_candidates.csv")
    candidates = read_candidate_rows(daily_candidates_csv)
    paper_trade = read_paper_trade(workspace, trade_date)
    rolling_path = data_dir(workspace) / "tail_entry" / f"{start_date}_to_{trade_date}.md"
    if not rolling_path.exists():
        rolling_path = base / "tail_entry" / f"{start_date}_to_{trade_date}.md"
    ensure_status_reports(daily_strategy_report, daily_candidates_csv, rolling_path, trade_date, start_date)
    metrics = read_tail_metrics(rolling_path)

    lines = [
        f"# 每日尾盘纸面交易报告：{trade_date}",
        "",
        "## 今日优选",
        "",
    ]
    if candidates:
        lines.extend(format_candidate_table(candidates))
        lines.extend(["", "- 买入时间点：收盘价近似；若实时执行，应保存 14:45/14:50/14:55 快照。"])
        if paper_trade:
            lines.append(
                f"- 默认纸面交易：{paper_trade.get('代码', '')} {paper_trade.get('名称', '')}，"
                f"来源={paper_trade.get('来源', '') or '纸面交易台账'}。"
            )
    else:
        lines.append("- 无合格候选或行情接口暂不可用，按策略记录为空仓/待复核。")

    lines.extend(
        [
            "",
            "## 历史交易复盘",
            "",
            f"- 区间：{start_date} 到 {trade_date}",
            f"- 样本数：{metrics.get('samples', '暂无')}",
            f"- 次日开盘胜率：{metrics.get('win_rate', '暂无')}",
            f"- 平均/中位开盘收益：{metrics.get('avg_open', '暂无')} / {metrics.get('median_open', '暂无')}",
            f"- 平均/中位次日最高收益：{metrics.get('avg_high', '暂无')} / {metrics.get('median_high', '暂无')}",
            "",
            "## 策略反馈闭环",
            "",
            "- 每日交易只使用纸面交易台账，不用事后重算候选充当交易。",
            "- 单日异常只记录观察；多日样本稳定后再调整可买入评分、风险扣分或空仓规则。",
            "- 本报告只用于纸面交易观察，不构成投资建议。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def format_candidate_table(candidates: list[dict[str, str]]) -> list[str]:
    lines = [
        "| 排名 | 股票 | 分支 | 评分 | 可买入评分 | 模拟买入价 | 风险 |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in candidates:
        lines.append(
            f"| {row.get('排名', '')} | {row.get('代码', '')} {row.get('名称', '')} | "
            f"{row.get('分支', '')} | {row.get('评分', '')} | {row.get('可买入评分', row.get('评分', ''))} | "
            f"{row.get('模拟买入价', '')} | {row.get('风险', '') or '无'} |"
        )
    return lines


def write_pick_report(workspace: Path, trade_date: str, recommendation_output: str) -> Path:
    base = report_dir(workspace)
    base.mkdir(parents=True, exist_ok=True)
    report_path = base / f"daily_run_{trade_date}.md"
    candidates = read_candidate_rows(report_data_path(workspace, f"{trade_date}_candidates.csv"))
    paper_trade = read_paper_trade(workspace, trade_date)
    lines = [
        f"# 每日尾盘纸面交易报告：{trade_date}",
        "",
        "## 今日优选",
        "",
    ]
    if candidates:
        lines.extend(format_candidate_table(candidates))
        lines.extend([
            "",
            "- 买入时间点：收盘价近似；若实时执行，应保存 14:45/14:50/14:55 快照。",
        ])
        if paper_trade:
            lines.append(
                f"- 默认纸面交易：{paper_trade.get('代码', '')} {paper_trade.get('名称', '')}，"
                f"来源={paper_trade.get('来源', '') or '纸面交易台账'}。"
            )
    else:
        lines.append("- 无合格候选或行情接口暂不可用，按策略记录为空仓/待复核。")
    lines.extend([
        "",
        "## 历史交易复盘",
        "",
        "- 本次只执行今日优选；历史复盘需执行完整模式后更新。",
        "",
        "## 策略反馈闭环",
        "",
        "- 今日默认纸面交易会进入台账，后续只用真实台账样本复盘胜率与收益。",
        "- 本报告只用于纸面交易观察，不构成投资建议。",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def ensure_status_reports(daily_report: Path, candidates_csv: Path, rolling_report: Path, trade_date: str, start_date: str) -> None:
    if not daily_report.exists():
        daily_report.write_text(
            "\n".join(
                [
                    f"# 第一策略执行报告：{trade_date}",
                    "",
                    "## 今日结论",
                    "",
                    "行情筛选尚未成功完成或已超时。本文件为独立工作区兜底状态报告。",
                    "",
                    "后续可在本目录重跑每日执行命令补齐正式候选。",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    if not candidates_csv.exists():
        candidates_csv.write_text("排名,分支,代码,名称,评分,模拟买入价,风险\n", encoding="utf-8-sig")
    if not rolling_report.exists():
        rolling_report.parent.mkdir(parents=True, exist_ok=True)
        rolling_report.write_text(
            "\n".join(
                [
                    f"# 第一策略尾盘买入与次日收益报告：{start_date} 到 {trade_date}",
                    "",
                    "## 数据说明",
                    "",
                    "- 本报告由独立工作区每日执行器创建。",
                    "- 近一月滚动回测尚未成功完成或已超时，当前为兜底状态报告。",
                    "- 请后续在本目录重跑，或缩短区间后补齐样本。",
                    "",
                    "## 汇总",
                    "",
                    "- 交易样本：0",
                    "- 次日开盘胜率：暂无",
                    "- 平均开盘收益：暂无",
                    "- 中位开盘收益：暂无",
                    "- 平均次日最高收益：暂无",
                    "- 中位次日最高收益：暂无",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", help="Workspace to initialize and run in; use . for current directory")
    parser.add_argument("--date", default=None, help="Trade date, YYYY-MM-DD; defaults to latest weekday")
    parser.add_argument("--start", default=None, help="Rolling report start date, YYYY-MM-DD")
    parser.add_argument("--mode", choices=["pick", "full"], default="pick", help="pick only screens today's tail candidates; full also runs rolling report and review")
    parser.add_argument("--skip-venv", action="store_true", help="Use system Python instead of .venv/bin/python")
    parser.add_argument("--recommend-timeout", type=int, default=120)
    parser.add_argument("--rolling-timeout", type=int, default=60)
    parser.add_argument("--review-timeout", type=int, default=60)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    subprocess.run([sys.executable, str(INIT_SCRIPT), str(workspace)], check=True)

    trade_day = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else latest_weekday(date.today())
    start_day = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else one_month_start(trade_day)
    py = workspace / ".venv" / "bin" / "python"
    python_cmd = str(py) if py.exists() and not args.skip_venv else sys.executable

    rec_code, rec_out = run(
        [python_cmd, "scripts/run_strategy_01.py", trade_day.isoformat()],
        workspace,
        timeout=args.recommend_timeout,
    )
    consolidate_internal_outputs(workspace)
    if args.mode == "pick":
        report_path = write_pick_report(
            workspace,
            trade_day.isoformat(),
            rec_out if rec_code == 0 else f"[失败 exit={rec_code}]\n{rec_out}",
        )
        consolidate_internal_outputs(workspace)
        print(f"Workspace: {workspace}")
        print(f"Daily report: {report_path}")
        print(f"Recommendation exit: {rec_code}")
        print("Mode: pick")
        return 0 if rec_code == 0 or report_path.exists() else rec_code

    roll_code, roll_out = run(
        [python_cmd, "scripts/report_strategy_01_tail_entry.py", start_day.isoformat(), trade_day.isoformat()],
        workspace,
        timeout=args.rolling_timeout,
    )
    consolidate_internal_outputs(workspace)
    prev_trade_day = latest_weekday(trade_day - timedelta(days=1))
    review_code, review_out = run(
        [python_cmd, "scripts/review_strategy_01_next_open.py", prev_trade_day.isoformat()],
        workspace,
        timeout=args.review_timeout,
    )
    consolidate_internal_outputs(workspace)
    report_path = write_run_report(
        workspace,
        trade_day.isoformat(),
        start_day.isoformat(),
        rec_out if rec_code == 0 else f"[失败 exit={rec_code}]\n{rec_out}",
        roll_out if roll_code == 0 else f"[失败 exit={roll_code}]\n{roll_out}",
        review_out if review_code == 0 else f"[失败 exit={review_code}]\n{review_out}",
    )
    consolidate_internal_outputs(workspace)
    print(f"Workspace: {workspace}")
    print(f"Daily report: {report_path}")
    print(f"Recommendation exit: {rec_code}")
    print(f"Rolling report exit: {roll_code}")
    print(f"Review exit: {review_code}")
    return 0 if rec_code == 0 or report_path.exists() else rec_code


if __name__ == "__main__":
    raise SystemExit(main())
