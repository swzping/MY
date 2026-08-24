#!/usr/bin/env python3
"""
生成第一策略近一个月尾盘买入与次日开盘/冲高收益报告。

注意：历史分钟线当前不可稳定获取时，尾盘具体时间点使用“收盘价近似”。
后续真实尾盘运行时，应以 14:45/14:50/14:55 快照替换该近似值。
"""

from __future__ import annotations

import csv
import importlib.util
import re
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "strategy_01"
DATA_DIR = REPORT_DIR / "_data"
OUT_DIR = DATA_DIR / "tail_entry"
BACKTEST_SCRIPT = ROOT / "scripts" / "_archive" / "backtest_strategy_01.py"

spec = importlib.util.spec_from_file_location("backtest_strategy_01", BACKTEST_SCRIPT)
backtest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["backtest_strategy_01"] = backtest
spec.loader.exec_module(backtest)


def return_pct(entry: float, exit_price: float) -> float:
    return (exit_price / entry - 1) * 100 if entry else 0


def tail_entry_label(value: str | None) -> str:
    return value or "收盘价近似"


def pick_best_trade(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return sorted(rows, key=lambda r: (r["open_return_pct"], r["high_return_pct"]), reverse=True)[0]


def default_start(end: str) -> str:
    end_dt = datetime.strptime(end, "%Y-%m-%d").date()
    return (end_dt - timedelta(days=35)).isoformat()


def candidate_trade_rows(trade_date: str) -> list[dict[str, Any]]:
    ledger_rows = paper_trade_rows(trade_date)
    if ledger_rows:
        return ledger_rows
    return []


def backtest_candidate_trade_rows(trade_date: str) -> list[dict[str, Any]]:
    fallback_reviews, fallback_next_date = saved_next_open_reviews(trade_date)
    rows = []
    for candidate in backtest.candidates_for_date(trade_date):
        if candidate.get("branch") != "01B":
            continue
        reviewed = backtest.evaluate_next_open(candidate)
        if not reviewed:
            reviewed = merge_saved_review(candidate, fallback_reviews.get(candidate["code"]), fallback_next_date)
        if not reviewed:
            continue
        rows.append({
            **reviewed,
            "tail_entry_time": None,
            "tail_entry_price": reviewed["buy_price"],
            "open_return_pct": return_pct(reviewed["buy_price"], reviewed["next_open"]),
            "high_return_pct": return_pct(reviewed["buy_price"], reviewed["next_high"]),
        })
    return rows


def paper_trade_rows(trade_date: str) -> list[dict[str, Any]]:
    path = data_file("paper_trades.csv")
    if not path.exists():
        return []
    fallback_reviews, fallback_next_date = saved_next_open_reviews(trade_date)
    rows = []
    with path.open(encoding="utf-8-sig") as f:
        for trade in csv.DictReader(f):
            if trade.get("交易日") != trade_date:
                continue
            reviewed = merge_paper_trade_review(trade, fallback_reviews.get(trade.get("代码", "")), fallback_next_date)
            if reviewed:
                rows.append(reviewed)
    return rows


def merge_paper_trade_review(trade: dict[str, str], row: dict[str, Any] | None, next_date: str = "") -> dict[str, Any] | None:
    if not row:
        return None
    buy_price = float(trade.get("尾盘买入价") or row.get("买入价") or 0)
    if not buy_price:
        return None
    next_open = float(row["次日开盘"])
    next_high = float(row["次日最高"])
    return {
        "date": trade["交易日"],
        "code": trade["代码"],
        "name": trade.get("名称", ""),
        "branch": trade.get("分支", ""),
        "score": float(trade.get("评分") or 0),
        "topic_heat": 0,
        "tail_entry_time": trade.get("买入时间点") or None,
        "tail_entry_price": buy_price,
        "amount_yi": 0,
        "next_date": next_date,
        "next_open": next_open,
        "next_high": next_high,
        "next_close": float(row["次日收盘"]),
        "open_return_pct": return_pct(buy_price, next_open),
        "high_return_pct": return_pct(buy_price, next_high),
        "close_return_pct": return_pct(buy_price, float(row["次日收盘"])),
        "risks": trade.get("风险", ""),
        "source": trade.get("来源", ""),
    }


def saved_next_open_reviews(trade_date: str) -> tuple[dict[str, dict[str, Any]], str]:
    """读取已生成的次日开盘复盘，补足最新交易日 K 线缓存未更新的情况。"""
    path = data_file(f"{trade_date}_next_open_review.csv")
    if not path.exists():
        return {}, ""
    md_path = path.with_suffix(".md")
    next_date = ""
    if md_path.exists():
        match = re.search(rf"{re.escape(trade_date)}\s*->\s*(\d{{4}}-\d{{2}}-\d{{2}})", md_path.read_text(encoding="utf-8"))
        if match:
            next_date = match.group(1)
    with path.open(encoding="utf-8-sig") as f:
        return {row["代码"]: row for row in csv.DictReader(f)}, next_date


def merge_saved_review(candidate: dict[str, Any], row: dict[str, Any] | None, next_date: str = "") -> dict[str, Any] | None:
    if not row:
        return None
    buy_price = float(row["买入价"])
    next_open = float(row["次日开盘"])
    next_high = float(row["次日最高"])
    return {
        **candidate,
        "buy_price": buy_price,
        "next_date": next_date,
        "next_open": next_open,
        "next_high": next_high,
        "next_close": float(row["次日收盘"]),
        "open_return_pct": return_pct(buy_price, next_open),
        "high_return_pct": return_pct(buy_price, next_high),
        "close_return_pct": return_pct(buy_price, float(row["次日收盘"])),
    }


def pick_strategy_trade(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    # 保持当前策略方向：强度分、尾盘位置优先；避免超大成交额龙头偏置，成交额接近 3-30 亿更优。
    def key(row: dict[str, Any]) -> tuple[float, float, float, float]:
        amount = float(row.get("amount_yi", 0))
        amount_fit = -abs(amount - 8)
        oversized_penalty = -100 if amount > 30 else 0
        return (row["score"], row.get("topic_heat", 0), oversized_penalty, amount_fit)

    return sorted(rows, key=key, reverse=True)[0]


def today_recommendation_lines(trade_date: str) -> list[str]:
    path = data_file(f"{trade_date}_candidates.csv")
    unavailable = unavailable_candidates(trade_date)
    lines = ["## 今日入选推荐股", ""]
    if not path.exists():
        return lines + ["- 暂无今日入选推荐股。", ""]

    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    available_rows = [row for row in rows if row.get("代码", "") not in unavailable]
    unavailable_rows = [row for row in rows if row.get("代码", "") in unavailable]
    if available_rows:
        lines.extend([
            "| 排名 | 股票 | 分支 | 评分 | 可买入评分 | 模拟买入价 | 风险 |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- |",
        ])
        for idx, row in enumerate(available_rows, 1):
            lines.append(
                f"| {idx} | {row.get('代码', '')} {row.get('名称', '')} | "
                f"{row.get('分支', '')} | {row.get('评分', '')} | {row.get('可买入评分', row.get('评分', ''))} | "
                f"{row.get('模拟买入价', '')} | "
                f"{row.get('风险', '') or '无'} |"
            )
        lines.append("")
    else:
        lines.extend(["- 暂无可买入推荐股。", ""])
    if unavailable_rows:
        lines.extend([
            "## 不可买入信号观察",
            "",
            "| 股票 | 原因 |",
            "| --- | --- |",
        ])
        for row in unavailable_rows:
            code = row.get("代码", "")
            lines.append(f"| {code} {row.get('名称', '')} | {unavailable.get(code, '不可买入')} |")
        lines.append("")
    return lines


def unavailable_candidates(trade_date: str) -> dict[str, str]:
    path = data_file(f"{trade_date}_unavailable.csv")
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as f:
        return {row.get("代码", ""): row.get("原因", "") or "不可买入" for row in csv.DictReader(f) if row.get("代码")}


def data_file(name: str) -> Path:
    report_dir = ROOT / "reports" / "strategy_01"
    internal = report_dir / "_data" / name
    if internal.exists():
        return internal
    return report_dir / name


def run_report(start: str, end: str, recommendation_date: str | None = None) -> tuple[Path, Path, list[dict[str, Any]]]:
    recommendation_date = recommendation_date or end
    results = []
    for trade_date in backtest.date_range(start, end):
        print(f"读取纸面交易 {trade_date}", flush=True)
        rows = candidate_trade_rows(trade_date)
        selected = pick_strategy_trade(rows)
        best = pick_best_trade(rows)
        if not selected or not best:
            continue
        selected["best_code"] = best.get("best_code", best["code"])
        selected["best_name"] = best.get("best_name", best["name"])
        selected["best_open_return_pct"] = best.get("best_open_return_pct", best["open_return_pct"])
        selected["best_high_return_pct"] = best.get("best_high_return_pct", best["high_return_pct"])
        selected["ranking_gap_pct"] = best.get("ranking_gap_pct", best["open_return_pct"] - selected["open_return_pct"])
        results.append(selected)

    stamp = f"{start}_to_{end}"
    csv_path = OUT_DIR / f"{stamp}.csv"
    md_path = OUT_DIR / f"{stamp}.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "交易日", "买入时间点", "代码", "名称", "分支", "评分", "题材热度", "尾盘买入价",
            "成交额(亿)", "次日", "次日开盘", "开盘收益%", "次日最高", "最高收益%",
            "事后最佳", "事后最佳开盘收益%", "事后最佳最高收益%", "排序损失%", "风险", "来源", "说明",
        ])
        for row in results:
            writer.writerow([
                row["date"], tail_entry_label(row.get("tail_entry_time")), row["code"], row["name"], row["branch"],
                row["score"], row.get("topic_heat", 0), f"{row['tail_entry_price']:.2f}", f"{row.get('amount_yi', 0):.2f}",
                row["next_date"], f"{row['next_open']:.2f}", f"{row['open_return_pct']:.2f}",
                f"{row['next_high']:.2f}", f"{row['high_return_pct']:.2f}",
                f"{row['best_code']} {row['best_name']}", f"{row['best_open_return_pct']:.2f}",
                f"{row['best_high_return_pct']:.2f}", f"{row['ranking_gap_pct']:.2f}",
                row.get("risks", ""), row.get("source", ""), "每日交易来自纸面持仓台账，不重新拉取候选池",
            ])

    open_returns = [r["open_return_pct"] for r in results]
    high_returns = [r["high_return_pct"] for r in results]
    ranking_gaps = [r["ranking_gap_pct"] for r in results]
    win_rate = sum(1 for x in open_returns if x > 0) / len(open_returns) * 100 if open_returns else 0
    default_top1_count = sum(1 for r in results if r.get("source") in {"策略Top1", "默认Top1"})
    user_selected_count = sum(1 for r in results if "用户" in str(r.get("source", "")) or "指定" in str(r.get("source", "")))
    lines = [
        f"# 近期尾盘买入与次日收益报告：{start} 到 {end}",
        "",
        "## 数据说明",
        "",
        "- 历史分钟线接口当前不可稳定获取近一个月 14:45/14:50/14:55 数据。",
        "- 本报告的“买入时间点”先标为“收盘价近似”，尾盘买入价使用当日收盘价近似。",
        "- 本报告的每日交易只读取纸面持仓台账：策略推荐 Top1 或用户明确确认买入的标的。",
        "- 生成收益报告时不重新拉取每日候选池，避免把事后重算候选误当成真实纸面交易。",
        "- 后续真实盘中运行会保存 14:45、14:50、14:55 快照，再替换为真实最佳买入时间点。",
        "",
        "## 汇总",
        "",
        f"- 交易样本：{len(results)}",
        f"- 次日开盘胜率：{win_rate:.1f}%",
        f"- 平均开盘收益：{statistics.mean(open_returns):.2f}%" if open_returns else "- 平均开盘收益：0.00%",
        f"- 中位开盘收益：{statistics.median(open_returns):.2f}%" if open_returns else "- 中位开盘收益：0.00%",
        f"- 平均次日最高收益：{statistics.mean(high_returns):.2f}%" if high_returns else "- 平均次日最高收益：0.00%",
        f"- 中位次日最高收益：{statistics.median(high_returns):.2f}%" if high_returns else "- 中位次日最高收益：0.00%",
        f"- 平均排序损失：{statistics.mean(ranking_gaps):.2f}%" if ranking_gaps else "- 平均排序损失：0.00%",
        "",
        "## 策略反馈闭环",
        "",
        f"- 默认Top1样本：{default_top1_count}",
        f"- 用户指定样本：{user_selected_count}",
        "- 后续只用纸面持仓台账中的真实记录回看胜率、开盘收益和冲高收益。",
        "- 多日样本稳定后，再把亏损原因或错过机会沉淀为可买入评分、风险扣分或空仓规则。",
        "",
        *today_recommendation_lines(recommendation_date),
        "## 每日交易",
        "",
        "| 交易日 | 买入时间点 | 股票 | 买入价 | 次日开盘收益 | 次日最高收益 | 来源 |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in results:
        lines.append(
            f"| {row['date']} | {tail_entry_label(row.get('tail_entry_time'))} | {row['code']} {row['name']} | "
            f"{row['tail_entry_price']:.2f} | {row['open_return_pct']:.2f}% | {row['high_return_pct']:.2f}% | "
            f"{row.get('source', '') or '纸面交易台账'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path, results


def main() -> int:
    end = sys.argv[2] if len(sys.argv) > 2 else "2026-06-23"
    start = sys.argv[1] if len(sys.argv) > 1 else default_start(end)
    recommendation_date = sys.argv[3] if len(sys.argv) > 3 else None
    csv_path, md_path, rows = run_report(start, end, recommendation_date=recommendation_date)
    print(f"样本数: {len(rows)}")
    print(f"CSV: {csv_path}")
    print(f"报告: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
