#!/usr/bin/env python3
"""
研究第一策略 01B 候选的尾盘位置与次日收益关系。

这个脚本用于验证“必须接近封板”是否过严。它不复用正式入选规则里的
01B 强封过滤，而是直接从历史热点池和 K 线重建 7%-10.2% 强势候选，
比较不同尾盘位置、可成交强度的次日开盘和次日最高收益。
"""

from __future__ import annotations

import csv
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports" / "strategy_01" / "_archive" / "close_position_study"
BACKTEST_SCRIPT = ROOT / "scripts" / "_archive" / "backtest_strategy_01.py"

spec = importlib.util.spec_from_file_location("backtest_strategy_01", BACKTEST_SCRIPT)
backtest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["backtest_strategy_01"] = backtest
spec.loader.exec_module(backtest)


def close_position_bucket(close_position_pct: float) -> str:
    if close_position_pct < 85:
        return "65-85"
    if close_position_pct < 95:
        return "85-95"
    if close_position_pct < 99.5:
        return "95-99.5"
    return "99.5+"


def tradeability_bucket(change_pct: float, close_position_pct: float) -> str:
    if change_pct >= 9.5 and close_position_pct >= 99.5:
        return "强封可能不可成交"
    if change_pct >= 9.3 and close_position_pct >= 95:
        return "可成交强势"
    return "弱封/回落"


def open_return_pct(buy_price: float, next_price: float) -> float:
    return (next_price / buy_price - 1) * 100 if buy_price else 0


def summarize_bucket(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row[field]), []).append(row)
    summary = []
    for bucket, items in groups.items():
        open_returns = [float(x["open_return_pct"]) for x in items]
        high_returns = [float(x["high_return_pct"]) for x in items]
        summary.append({
            "bucket": bucket,
            "samples": len(items),
            "open_win_rate": round(sum(1 for x in open_returns if x > 0) / len(open_returns) * 100, 1),
            "avg_open_return": round(statistics.mean(open_returns), 2),
            "median_open_return": round(statistics.median(open_returns), 2),
            "avg_high_return": round(statistics.mean(high_returns), 2),
            "median_high_return": round(statistics.median(high_returns), 2),
            "worst_open_return": round(min(open_returns), 2),
        })
    return sorted(summary, key=lambda x: x["bucket"])


def candidate_rows_for_date(trade_date: str) -> list[dict[str, Any]]:
    pool = backtest.cached_hot_reason(trade_date)
    rows = []
    for stock in pool:
        try:
            code = stock["code"]
            kline = backtest.cached_kline(code)
            hist = [r for r in kline if r.get("date", "") <= trade_date]
            next_rows = [r for r in kline if r.get("date", "") > trade_date]
            if len(hist) < 18 or not next_rows:
                continue
            day = hist[-1]
            close = float(day["close"])
            high = float(day["high"])
            low = float(day["low"])
            change_pct = float(stock.get("change_pct") or 0)
            amount = float(stock.get("amount") or day.get("amount") or 0)
            if change_pct < 7 or change_pct > 10.2:
                continue
            if amount < 100_000_000 or high <= low:
                continue
            close_position_pct = (close - low) / (high - low) * 100
            if close_position_pct < 65:
                continue
            next_day = next_rows[0]
            rows.append({
                "date": trade_date,
                "next_date": next_day["date"],
                "code": code,
                "name": stock.get("name", ""),
                "change_pct": change_pct,
                "buy_price": close,
                "close_position_pct": close_position_pct,
                "amount_yi": amount / 100_000_000,
                "bucket": close_position_bucket(close_position_pct),
                "tradeability": tradeability_bucket(change_pct, close_position_pct),
                "next_open": next_day["open"],
                "next_high": next_day["high"],
                "open_return_pct": open_return_pct(close, next_day["open"]),
                "high_return_pct": open_return_pct(close, next_day["high"]),
                "reason": stock.get("reason", ""),
            })
        except Exception:
            continue
        time.sleep(0.01)
    return rows


def run_study(start: str, end: str) -> tuple[Path, Path, list[dict[str, Any]]]:
    rows = []
    for trade_date in backtest.date_range(start, end):
        print(f"研究 {trade_date}", flush=True)
        rows.extend(candidate_rows_for_date(trade_date))

    stamp = f"{start}_to_{end}"
    csv_path = OUT_DIR / f"{stamp}.csv"
    md_path = OUT_DIR / f"{stamp}.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["交易日", "次日", "代码", "名称", "涨幅%", "买入价", "日内位置%", "成交额(亿)", "位置分桶", "可成交分桶", "次日开盘", "次日最高", "开盘收益%", "最高收益%", "题材"])
        for row in rows:
            writer.writerow([
                row["date"], row["next_date"], row["code"], row["name"], f"{row['change_pct']:.2f}",
                f"{row['buy_price']:.2f}", f"{row['close_position_pct']:.2f}", f"{row['amount_yi']:.2f}",
                row["bucket"], row["tradeability"], f"{row['next_open']:.2f}", f"{row['next_high']:.2f}",
                f"{row['open_return_pct']:.2f}", f"{row['high_return_pct']:.2f}", row["reason"],
            ])

    lines = [
        f"# 01B 尾盘位置与次日收益研究：{start} 到 {end}",
        "",
        f"- 样本数：{len(rows)}",
        "",
        "## 按尾盘位置分桶",
        "",
        "| 位置分桶 | 样本数 | 开盘胜率 | 平均开盘收益 | 中位开盘收益 | 平均最高收益 | 中位最高收益 | 最差开盘 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summarize_bucket(rows, "bucket"):
        lines.append(
            f"| {item['bucket']} | {item['samples']} | {item['open_win_rate']:.1f}% | "
            f"{item['avg_open_return']:.2f}% | {item['median_open_return']:.2f}% | "
            f"{item['avg_high_return']:.2f}% | {item['median_high_return']:.2f}% | "
            f"{item['worst_open_return']:.2f}% |"
        )
    lines.extend([
        "",
        "## 按可成交强度分桶",
        "",
        "| 分桶 | 样本数 | 开盘胜率 | 平均开盘收益 | 中位开盘收益 | 平均最高收益 | 中位最高收益 | 最差开盘 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for item in summarize_bucket(rows, "tradeability"):
        lines.append(
            f"| {item['bucket']} | {item['samples']} | {item['open_win_rate']:.1f}% | "
            f"{item['avg_open_return']:.2f}% | {item['median_open_return']:.2f}% | "
            f"{item['avg_high_return']:.2f}% | {item['median_high_return']:.2f}% | "
            f"{item['worst_open_return']:.2f}% |"
        )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path, rows


def main() -> int:
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-05-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2026-06-23"
    csv_path, md_path, rows = run_study(start, end)
    print(f"样本数: {len(rows)}")
    print(f"CSV: {csv_path}")
    print(f"报告: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
