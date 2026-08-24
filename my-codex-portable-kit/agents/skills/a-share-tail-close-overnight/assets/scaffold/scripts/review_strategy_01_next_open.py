#!/usr/bin/env python3
"""
复盘第一策略：用次日开盘表现反推前一交易日更优隔夜票。

示例：
  .venv/bin/python scripts/review_strategy_01_next_open.py 2026-06-22 2026-06-23
"""

from __future__ import annotations

import csv
import importlib.util
import statistics
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "strategy_01" / "_data"
SCRIPT = ROOT / "scripts" / "run_strategy_01.py"

spec = importlib.util.spec_from_file_location("run_strategy_01", SCRIPT)
strategy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["run_strategy_01"] = strategy
spec.loader.exec_module(strategy)


def kline_by_date(code: str) -> dict[str, dict[str, Any]]:
    rows = strategy.daily_kline(code)
    return {row["date"]: row for row in rows if row.get("date")}


def build_candidates(trade_date: str) -> list[Any]:
    market = strategy.ths_hot_reason(trade_date)
    if not market:
        market = strategy.eastmoney_strong_pool()

    # 复盘历史日时，腾讯实时价不可用于昨日条件；核心价格仍以历史 K 线覆盖。
    candidates = []
    for stock in market:
        try:
            rows = strategy.daily_kline(stock["code"])
            hist = [r for r in rows if r.get("date", "") <= trade_date]
            if not hist:
                continue
            day = hist[-1]
            stock = {
                **stock,
                "price": day["close"],
                "open": day["open"],
                "high": day["high"],
                "low": day["low"],
                "amount": stock.get("amount") or day["amount"],
            }
            for branch in ("01A", "01B"):
                candidate = strategy.evaluate_candidate(stock, hist, market_score=18, sector_score=14, branch=branch)
                if candidate:
                    candidates.append(candidate)
        except Exception:
            continue
        time.sleep(0.05)
    candidates.sort(key=lambda c: (c.score, c.close_position_pct, c.amount_yi), reverse=True)
    return candidates


def review(trade_date: str, next_date: str) -> tuple[Path, Path, list[dict[str, Any]]]:
    candidates = build_candidates(trade_date)
    rows = []
    for candidate in candidates:
        date_map = kline_by_date(candidate.code)
        next_day = date_map.get(next_date)
        if not next_day:
            continue
        open_price = next_day["open"]
        high_price = next_day["high"]
        close_price = next_day["close"]
        rows.append({
            **asdict(candidate),
            "next_open": open_price,
            "next_high": high_price,
            "next_close": close_price,
            "open_return_pct": (open_price / candidate.buy_price - 1) * 100,
            "high_return_pct": (high_price / candidate.buy_price - 1) * 100,
            "close_return_pct": (close_price / candidate.buy_price - 1) * 100,
        })
    rows.sort(key=lambda r: (r["open_return_pct"], r["high_return_pct"], r["score"]), reverse=True)

    csv_path = OUT_DIR / f"{trade_date}_next_open_review.csv"
    md_path = OUT_DIR / f"{trade_date}_next_open_review.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["排名", "分支", "代码", "名称", "评分", "买入价", "次日开盘", "次日最高", "次日收盘", "开盘收益%", "最高收益%", "收盘收益%", "理由", "风险"])
        for index, row in enumerate(rows, 1):
            writer.writerow([
                index, row["branch"], row["code"], row["name"], row["score"],
                f"{row['buy_price']:.2f}", f"{row['next_open']:.2f}", f"{row['next_high']:.2f}", f"{row['next_close']:.2f}",
                f"{row['open_return_pct']:.2f}", f"{row['high_return_pct']:.2f}", f"{row['close_return_pct']:.2f}",
                "；".join(row["reasons"]), "；".join(row["risks"]),
            ])

    win_rate = 0
    avg_open = 0
    if rows:
        win_rate = sum(1 for r in rows if r["open_return_pct"] > 0) / len(rows) * 100
        avg_open = statistics.mean(r["open_return_pct"] for r in rows)
    lines = [
        f"# 第一策略次日开盘复盘：{trade_date} -> {next_date}",
        "",
        "## 概况",
        "",
        f"- 复盘候选数：{len(rows)}",
        f"- 次日开盘胜率：{win_rate:.1f}%",
        f"- 平均开盘收益：{avg_open:.2f}%",
        "",
        "## 次日开盘表现 Top 10",
        "",
        "| 排名 | 分支 | 代码 | 名称 | 评分 | 买入价 | 次日开盘 | 开盘收益 | 次日最高收益 | 收盘收益 |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(rows[:10], 1):
        lines.append(
            f"| {index} | {row['branch']} | {row['code']} | {row['name']} | {row['score']:.1f} | "
            f"{row['buy_price']:.2f} | {row['next_open']:.2f} | {row['open_return_pct']:.2f}% | "
            f"{row['high_return_pct']:.2f}% | {row['close_return_pct']:.2f}% |"
        )
    if rows:
        best = rows[0]
        lines.extend([
            "",
            "## 复盘结论",
            "",
            f"- 按次日开盘收益，昨天最优隔夜票是：{best['code']} {best['name']}。",
            f"- 分支：{best['branch']}。",
            f"- 昨日模拟买入价：{best['buy_price']:.2f}。",
            f"- 今日开盘价：{best['next_open']:.2f}，开盘收益 {best['open_return_pct']:.2f}%。",
            f"- 今日最高收益 {best['high_return_pct']:.2f}%。",
        ])
    else:
        lines.extend(["", "## 复盘结论", "", "没有可复盘候选。"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path, rows


def main() -> int:
    trade_date = sys.argv[1] if len(sys.argv) > 1 else "2026-06-22"
    next_date = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
    csv_path, md_path, rows = review(trade_date, next_date)
    print(f"复盘候选: {len(rows)}")
    print(f"CSV: {csv_path}")
    print(f"报告: {md_path}")
    if rows:
        best = rows[0]
        print(f"最优: {best['code']} {best['name']} {best['branch']} 开盘收益={best['open_return_pct']:.2f}% 最高收益={best['high_return_pct']:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
