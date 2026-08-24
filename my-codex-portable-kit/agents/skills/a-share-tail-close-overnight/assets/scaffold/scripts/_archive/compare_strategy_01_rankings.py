#!/usr/bin/env python3
"""
比较第一策略候选的不同 Top1 排序规则。

这个脚本不改变正式策略，只用相同历史候选比较不同排序方式的次日开盘表现。
"""

from __future__ import annotations

import csv
import importlib.util
import statistics
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports" / "strategy_01" / "_archive" / "ranking_compare"
BACKTEST_SCRIPT = ROOT / "scripts" / "_archive" / "backtest_strategy_01.py"

spec = importlib.util.spec_from_file_location("backtest_strategy_01", BACKTEST_SCRIPT)
backtest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["backtest_strategy_01"] = backtest
spec.loader.exec_module(backtest)


def by_liquid_leader(row: dict[str, Any]) -> tuple[float, float, float, float]:
    return (row["score"], row["close_position_pct"], row.get("amount_yi", 0), 0)


def by_topic_heat(row: dict[str, Any]) -> tuple[float, float, float, float]:
    return (row["score"], row.get("topic_heat", 0), row["close_position_pct"], row.get("amount_yi", 0))


def by_elastic_price(row: dict[str, Any]) -> tuple[float, float, float, float]:
    price = float(row.get("buy_price", 0) or 0)
    amount = float(row.get("amount_yi", 0) or 0)
    price_fit = -abs(price - 20)
    return (row["score"], row["close_position_pct"], price_fit, amount)


def by_topic_and_elastic(row: dict[str, Any]) -> tuple[float, float, float, float]:
    price = float(row.get("buy_price", 0) or 0)
    price_fit = -abs(price - 20)
    return (row["score"], row.get("topic_heat", 0), price_fit, row["close_position_pct"])


def by_low_price_relay(row: dict[str, Any]) -> tuple[float, float, float, float]:
    price = float(row.get("buy_price", 0) or 0)
    amount = float(row.get("amount_yi", 0) or 0)
    price_bonus = -price
    amount_fit = -abs(amount - 8)
    return (row["score"], row.get("topic_heat", 0), price_bonus, amount_fit)


RANKERS: dict[str, Callable[[dict[str, Any]], tuple[float, float, float, float]]] = {
    "liquid_leader": by_liquid_leader,
    "topic_heat": by_topic_heat,
    "elastic_price": by_elastic_price,
    "topic_elastic": by_topic_and_elastic,
    "low_price_relay": by_low_price_relay,
}


def build_candidate_map(start: str, end: str) -> dict[str, list[dict[str, Any]]]:
    candidate_map = {}
    for trade_date in backtest.date_range(start, end):
        print(f"生成候选：{trade_date}", flush=True)
        candidate_map[trade_date] = backtest.candidates_for_date(trade_date)
    return candidate_map


def filter_candidates(candidates: list[dict[str, Any]], branch: str = "ALL") -> list[dict[str, Any]]:
    if branch == "ALL":
        return candidates
    return [row for row in candidates if row.get("branch") == branch]


def evaluate_ranker(candidate_map: dict[str, list[dict[str, Any]]], ranker: Callable[[dict[str, Any]], tuple[float, float, float, float]], branch: str = "ALL") -> list[dict[str, Any]]:
    results = []
    for _trade_date, candidates in candidate_map.items():
        candidates = filter_candidates(candidates, branch)
        if not candidates:
            continue
        top = sorted(candidates, key=ranker, reverse=True)[0]
        reviewed = backtest.evaluate_next_open(top)
        if reviewed:
            reviewed_all = [r for r in (backtest.evaluate_next_open(c) for c in candidates) if r]
            best_possible = max(reviewed_all, key=lambda r: r["open_return_pct"]) if reviewed_all else reviewed
            reviewed["best_possible_code"] = best_possible["code"]
            reviewed["best_possible_name"] = best_possible["name"]
            reviewed["best_possible_return_pct"] = best_possible["open_return_pct"]
            reviewed["ranking_gap_pct"] = best_possible["open_return_pct"] - reviewed["open_return_pct"]
            results.append(reviewed)
    return results


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [r["open_return_pct"] for r in rows]
    gaps = [r.get("ranking_gap_pct", 0) for r in rows]
    return {
        "samples": len(rows),
        "win_rate": sum(1 for x in returns if x > 0) / len(returns) * 100 if returns else 0,
        "avg_return": statistics.mean(returns) if returns else 0,
        "median_return": statistics.median(returns) if returns else 0,
        "min_return": min(returns) if returns else 0,
        "max_return": max(returns) if returns else 0,
        "avg_gap": statistics.mean(gaps) if gaps else 0,
    }


def run_compare(start: str, end: str, branch: str = "ALL") -> tuple[Path, Path, list[dict[str, Any]]]:
    summaries = []
    detail_rows = []
    candidate_map = build_candidate_map(start, end)
    for name, ranker in RANKERS.items():
        print(f"比较排序：{name}", flush=True)
        rows = evaluate_ranker(candidate_map, ranker, branch=branch)
        summary = summarize(rows)
        summary["ranker"] = name
        summaries.append(summary)
        for row in rows:
            detail_rows.append({"ranker": name, **row})

    suffix = "" if branch == "ALL" else f"_{branch}"
    stamp = f"{start}_to_{end}{suffix}"
    csv_path = OUT_DIR / f"{stamp}.csv"
    md_path = OUT_DIR / f"{stamp}.md"
    detail_csv_path = OUT_DIR / f"{stamp}_details.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["排序规则", "样本数", "胜率%", "平均开盘收益%", "中位数%", "最差%", "最佳%", "平均排序损失%"])
        for s in summaries:
            writer.writerow([
                s["ranker"], s["samples"], f"{s['win_rate']:.2f}", f"{s['avg_return']:.2f}",
                f"{s['median_return']:.2f}", f"{s['min_return']:.2f}", f"{s['max_return']:.2f}",
                f"{s['avg_gap']:.2f}",
            ])

    detail_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with detail_csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["排序规则", "交易日", "次日", "分支", "代码", "名称", "评分", "题材热度", "买入价", "成交额(亿)", "开盘收益%", "事后最佳代码", "事后最佳名称", "事后最佳开盘收益%", "排序损失%", "理由", "风险"])
        for r in detail_rows:
            writer.writerow([
                r["ranker"], r["date"], r.get("next_date", ""), r["branch"], r["code"], r["name"],
                r["score"], r.get("topic_heat", 0), f"{r['buy_price']:.2f}", f"{r.get('amount_yi', 0):.2f}",
                f"{r['open_return_pct']:.2f}", r.get("best_possible_code", ""), r.get("best_possible_name", ""),
                f"{r.get('best_possible_return_pct', 0):.2f}", f"{r.get('ranking_gap_pct', 0):.2f}",
                r.get("reasons", ""), r.get("risks", ""),
            ])

    lines = [
        f"# 第一策略排序规则对比：{start} 到 {end}",
        "",
        f"- 分支过滤：{branch}",
        f"- 明细CSV：{detail_csv_path.name}",
        "",
        "| 排序规则 | 样本数 | 胜率 | 平均开盘收益 | 中位数 | 最差 | 最佳 | 平均排序损失 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in sorted(summaries, key=lambda x: (x["avg_return"], x["win_rate"]), reverse=True):
        lines.append(
            f"| {s['ranker']} | {s['samples']} | {s['win_rate']:.1f}% | {s['avg_return']:.2f}% | "
            f"{s['median_return']:.2f}% | {s['min_return']:.2f}% | {s['max_return']:.2f}% | "
            f"{s['avg_gap']:.2f}% |"
        )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path, summaries


def main() -> int:
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2026-06-22"
    branch = sys.argv[3] if len(sys.argv) > 3 else "ALL"
    csv_path, md_path, _ = run_compare(start, end, branch=branch)
    print(f"CSV: {csv_path}")
    print(f"报告: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
