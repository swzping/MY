#!/usr/bin/env python3
"""
第一策略滚动回测：按历史日候选排序选 Top1，统计次日开盘收益。

默认以同花顺热点历史强势股作为候选池，适合检验隔夜票策略在近期行情中的表现。

示例：
  .venv/bin/python scripts/_archive/backtest_strategy_01.py 2026-06-01 2026-06-22
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import statistics
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports" / "strategy_01" / "_archive" / "backtests"
CACHE_DIR = ROOT / "data" / "cache"
KLINE_CACHE_DIR = CACHE_DIR / "kline"
HOT_CACHE_DIR = CACHE_DIR / "hot_reason"
KLINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
HOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
SCRIPT = ROOT / "scripts" / "run_strategy_01.py"
KLINE_CACHE: dict[str, list[dict[str, Any]]] = {}

spec = importlib.util.spec_from_file_location("run_strategy_01", SCRIPT)
strategy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["run_strategy_01"] = strategy
spec.loader.exec_module(strategy)


def date_range(start: str, end: str) -> list[str]:
    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end, "%Y-%m-%d").date()
    days = []
    cur = start_dt
    while cur <= end_dt:
        if cur.weekday() < 5:
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def pick_daily_top(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return sorted(rows, key=ranking_key, reverse=True)[0]


def ranking_key(row: dict[str, Any]) -> tuple[float, float, float, float]:
    amount = float(row.get("amount_yi", 0))
    if row.get("branch") == "01B":
        return (row["score"], row["close_position_pct"], amount, 0)
    return (row["score"], row["close_position_pct"], amount, 0)


def open_return_pct(buy_price: float, next_open: float) -> float:
    return (next_open / buy_price - 1) * 100


def next_trade_day_from_kline(code: str, trade_date: str) -> str | None:
    rows = cached_kline(code)
    dates = [r["date"] for r in rows if r.get("date", "") > trade_date]
    return dates[0] if dates else None


def cached_kline(code: str) -> list[dict[str, Any]]:
    if code not in KLINE_CACHE:
        path = KLINE_CACHE_DIR / f"{code}.json"
        if path.exists():
            KLINE_CACHE[code] = json.loads(path.read_text(encoding="utf-8"))
        else:
            KLINE_CACHE[code] = strategy.daily_kline(code)
            path.write_text(json.dumps(KLINE_CACHE[code], ensure_ascii=False), encoding="utf-8")
    return KLINE_CACHE[code]


def cached_hot_reason(trade_date: str) -> list[dict[str, Any]]:
    path = HOT_CACHE_DIR / f"{trade_date}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    pool = strategy.ths_hot_reason(trade_date)
    path.write_text(json.dumps(pool, ensure_ascii=False), encoding="utf-8")
    return pool


def candidates_for_date(trade_date: str) -> list[dict[str, Any]]:
    pool = cached_hot_reason(trade_date)
    if not pool:
        return []
    heat = topic_heat(pool)
    candidates = []
    for stock in pool:
        try:
            rows = cached_kline(stock["code"])
            hist = [r for r in rows if r.get("date", "") <= trade_date]
            if len(hist) < 18:
                continue
            day = hist[-1]
            stock_for_eval = {
                **stock,
                "price": day["close"],
                "open": day["open"],
                "high": day["high"],
                "low": day["low"],
                "amount": stock.get("amount") or day["amount"],
            }
            for branch in ("01A", "01B"):
                candidate = strategy.evaluate_candidate(stock_for_eval, hist, market_score=18, sector_score=14, branch=branch)
                if candidate:
                    stock_topic_heat = max((heat.get(tag, 0) for tag in extract_topics(stock.get("reason", ""))), default=0)
                    candidates.append({
                        "date": trade_date,
                        "code": candidate.code,
                        "name": candidate.name,
                        "branch": candidate.branch,
                        "score": candidate.score,
                        "buy_price": candidate.buy_price,
                        "close_position_pct": candidate.close_position_pct,
                        "amount_yi": candidate.amount_yi,
                        "topic_heat": stock_topic_heat,
                        "reasons": "；".join(candidate.reasons),
                        "risks": "；".join(candidate.risks),
                    })
        except Exception:
            continue
        time.sleep(0.04)
    return candidates


def extract_topics(reason: str) -> list[str]:
    parts = re.split(r"[+＋/、，,;；\\s]+", reason or "")
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def topic_heat(pool: list[dict[str, Any]]) -> dict[str, int]:
    heat: dict[str, int] = {}
    for stock in pool:
        seen = set(extract_topics(stock.get("reason", "")))
        for tag in seen:
            heat[tag] = heat.get(tag, 0) + 1
    return heat


def evaluate_next_open(row: dict[str, Any]) -> dict[str, Any] | None:
    rows = cached_kline(row["code"])
    next_rows = [r for r in rows if r.get("date", "") > row["date"]]
    if not next_rows:
        return None
    next_day = next_rows[0]
    return {
        **row,
        "next_date": next_day["date"],
        "next_open": next_day["open"],
        "next_high": next_day["high"],
        "next_close": next_day["close"],
        "open_return_pct": open_return_pct(row["buy_price"], next_day["open"]),
        "high_return_pct": open_return_pct(row["buy_price"], next_day["high"]),
        "close_return_pct": open_return_pct(row["buy_price"], next_day["close"]),
    }


def run_backtest(start: str, end: str) -> tuple[Path, Path, list[dict[str, Any]]]:
    results = []
    for trade_date in date_range(start, end):
        print(f"回测 {trade_date} ...", flush=True)
        candidates = candidates_for_date(trade_date)
        top = pick_daily_top(candidates)
        if not top:
            continue
        reviewed = evaluate_next_open(top)
        if reviewed:
            reviewed_all = [r for r in (evaluate_next_open(c) for c in candidates) if r]
            best_possible = max(reviewed_all, key=lambda r: r["open_return_pct"]) if reviewed_all else reviewed
            reviewed["best_possible_code"] = best_possible["code"]
            reviewed["best_possible_name"] = best_possible["name"]
            reviewed["best_possible_return_pct"] = best_possible["open_return_pct"]
            reviewed["ranking_gap_pct"] = best_possible["open_return_pct"] - reviewed["open_return_pct"]
            results.append(reviewed)

    stamp = f"{start}_to_{end}"
    csv_path = OUT_DIR / f"{stamp}.csv"
    md_path = OUT_DIR / f"{stamp}.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["交易日", "次日", "分支", "代码", "名称", "评分", "题材热度", "买入价", "次日开盘", "开盘收益%", "最高收益%", "收盘收益%", "事后最佳代码", "事后最佳名称", "事后最佳开盘收益%", "排序损失%", "理由", "风险"])
        for r in results:
            writer.writerow([
                r["date"], r["next_date"], r["branch"], r["code"], r["name"], r["score"], r.get("topic_heat", 0),
                f"{r['buy_price']:.2f}", f"{r['next_open']:.2f}", f"{r['open_return_pct']:.2f}",
                f"{r['high_return_pct']:.2f}", f"{r['close_return_pct']:.2f}",
                r["best_possible_code"], r["best_possible_name"], f"{r['best_possible_return_pct']:.2f}",
                f"{r['ranking_gap_pct']:.2f}", r["reasons"], r["risks"],
            ])

    returns = [r["open_return_pct"] for r in results]
    win_rate = sum(1 for x in returns if x > 0) / len(returns) * 100 if returns else 0
    avg_return = statistics.mean(returns) if returns else 0
    median_return = statistics.median(returns) if returns else 0
    ranking_gaps = [r["ranking_gap_pct"] for r in results]
    avg_gap = statistics.mean(ranking_gaps) if ranking_gaps else 0
    worst = min(results, key=lambda r: r["open_return_pct"]) if results else None
    best = max(results, key=lambda r: r["open_return_pct"]) if results else None
    lines = [
        f"# 第一策略滚动回测：{start} 到 {end}",
        "",
        "## 核心指标",
        "",
        f"- 有交易样本：{len(results)}",
        f"- 次日开盘胜率：{win_rate:.1f}%",
        f"- 平均开盘收益：{avg_return:.2f}%",
        f"- 中位数开盘收益：{median_return:.2f}%",
        f"- 平均排序损失：{avg_gap:.2f}%",
    ]
    if best:
        lines.extend([
            f"- 最佳：{best['date']} {best['code']} {best['name']}，开盘收益 {best['open_return_pct']:.2f}%",
            f"- 最差：{worst['date']} {worst['code']} {worst['name']}，开盘收益 {worst['open_return_pct']:.2f}%",
        ])
    lines.extend([
        "",
        "## 每日 Top1",
        "",
        "| 交易日 | 次日 | 分支 | 代码 | 名称 | 评分 | 题材热度 | 开盘收益 | 事后最佳 | 排序损失 |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ])
    for r in results:
        lines.append(
            f"| {r['date']} | {r['next_date']} | {r['branch']} | {r['code']} | {r['name']} | "
            f"{r['score']:.1f} | {r.get('topic_heat', 0)} | {r['open_return_pct']:.2f}% | "
            f"{r['best_possible_code']} {r['best_possible_name']} {r['best_possible_return_pct']:.2f}% | "
            f"{r['ranking_gap_pct']:.2f}% |"
        )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path, results


def main() -> int:
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2026-06-22"
    csv_path, md_path, results = run_backtest(start, end)
    print(f"样本数: {len(results)}")
    print(f"CSV: {csv_path}")
    print(f"报告: {md_path}")
    if results:
        returns = [r["open_return_pct"] for r in results]
        print(f"胜率: {sum(1 for x in returns if x > 0) / len(returns) * 100:.1f}%")
        print(f"平均开盘收益: {statistics.mean(returns):.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
