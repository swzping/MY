#!/usr/bin/env python3
"""
分析第一策略事后最优票画像。

读取排序对比明细 CSV，提取每个交易日的事后最佳候选，并回查同日候选池中的
价格、成交额、题材热度等可提前观察的特征。
"""

from __future__ import annotations

import csv
import importlib.util
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports" / "strategy_01" / "_archive" / "best_profile"
BACKTEST_SCRIPT = ROOT / "scripts" / "_archive" / "backtest_strategy_01.py"

spec = importlib.util.spec_from_file_location("backtest_strategy_01", BACKTEST_SCRIPT)
backtest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["backtest_strategy_01"] = backtest
spec.loader.exec_module(backtest)


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def price_bucket(price: float) -> str:
    if price < 10:
        return "0-10"
    if price < 20:
        return "10-20"
    if price < 50:
        return "20-50"
    return "50+"


def amount_bucket(amount_yi: float) -> str:
    if amount_yi < 3:
        return "0-3亿"
    if amount_yi < 10:
        return "3-10亿"
    if amount_yi < 30:
        return "10-30亿"
    if amount_yi < 100:
        return "30-100亿"
    return "100亿+"


def heat_bucket(heat: float) -> str:
    if heat <= 1:
        return "0-1"
    if heat <= 3:
        return "2-3"
    if heat <= 7:
        return "4-7"
    return "8+"


def read_detail_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def unique_best_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_date: dict[str, dict[str, Any]] = {}
    for row in rows:
        date = row.get("交易日", "")
        code = row.get("事后最佳代码", "")
        if not date or not code or date in by_date:
            continue
        by_date[date] = {
            "date": date,
            "code": code,
            "name": row.get("事后最佳名称", ""),
            "return_pct": to_float(row.get("事后最佳开盘收益%")),
        }
    return [by_date[d] for d in sorted(by_date)]


def candidate_lookup(start: str, end: str, branch: str) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for trade_date in backtest.date_range(start, end):
        for candidate in backtest.candidates_for_date(trade_date):
            if branch != "ALL" and candidate.get("branch") != branch:
                continue
            lookup[(trade_date, candidate["code"])] = candidate
    return lookup


def enrich_best_rows(best_rows: list[dict[str, Any]], lookup: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for row in best_rows:
        candidate = lookup.get((row["date"], row["code"]), {})
        price = to_float(candidate.get("buy_price"))
        amount = to_float(candidate.get("amount_yi"))
        heat = to_float(candidate.get("topic_heat"))
        enriched.append({
            **row,
            "price": price,
            "amount_yi": amount,
            "topic_heat": heat,
            "price_bucket": price_bucket(price),
            "amount_bucket": amount_bucket(amount),
            "heat_bucket": heat_bucket(heat),
            "reasons": candidate.get("reasons", ""),
            "risks": candidate.get("risks", ""),
        })
    return enriched


def bucket_summary(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row[field]), []).append(row)
    summary = []
    for bucket, items in groups.items():
        returns = [to_float(item["return_pct"]) for item in items]
        summary.append({
            "bucket": bucket,
            "count": len(items),
            "avg_return_pct": round(statistics.mean(returns), 2) if returns else 0,
        })
    return sorted(summary, key=lambda x: (x["count"], x["avg_return_pct"]), reverse=True)


def selection_gap_summary(detail_rows: list[dict[str, str]], best_features: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, float]]] = {}
    for row in detail_rows:
        best_code = row.get("事后最佳代码", "")
        best = best_features.get(best_code)
        if not best:
            continue
        ranker = row.get("排序规则", "")
        groups.setdefault(ranker, []).append({
            "price_diff": to_float(row.get("买入价")) - to_float(best.get("price")),
            "amount_diff": to_float(row.get("成交额(亿)")) - to_float(best.get("amount_yi")),
            "heat_diff": to_float(row.get("题材热度")) - to_float(best.get("topic_heat")),
            "return_gap": to_float(best.get("return_pct")) - to_float(row.get("开盘收益%")),
        })
    summary = []
    for ranker, items in groups.items():
        summary.append({
            "ranker": ranker,
            "samples": len(items),
            "avg_price_diff": round(statistics.mean(item["price_diff"] for item in items), 2),
            "avg_amount_diff": round(statistics.mean(item["amount_diff"] for item in items), 2),
            "avg_heat_diff": round(statistics.mean(item["heat_diff"] for item in items), 2),
            "avg_return_gap": round(statistics.mean(item["return_gap"] for item in items), 2),
        })
    return sorted(summary, key=lambda x: x["avg_return_gap"])


def write_report(start: str, end: str, branch: str, rows: list[dict[str, Any]], gap_rows: list[dict[str, Any]] | None = None) -> Path:
    stamp = f"{start}_to_{end}_{branch}"
    md_path = OUT_DIR / f"{stamp}.md"
    lines = [
        f"# 第一策略事后最优票画像：{start} 到 {end}",
        "",
        f"- 分支：{branch}",
        f"- 样本数：{len(rows)}",
        "",
        "## 价格区间",
        "",
        "| 价格区间 | 样本数 | 平均开盘收益 |",
        "| --- | ---: | ---: |",
    ]
    for item in bucket_summary(rows, "price_bucket"):
        lines.append(f"| {item['bucket']} | {item['count']} | {item['avg_return_pct']:.2f}% |")
    lines.extend([
        "",
        "## 成交额区间",
        "",
        "| 成交额区间 | 样本数 | 平均开盘收益 |",
        "| --- | ---: | ---: |",
    ])
    for item in bucket_summary(rows, "amount_bucket"):
        lines.append(f"| {item['bucket']} | {item['count']} | {item['avg_return_pct']:.2f}% |")
    lines.extend([
        "",
        "## 题材热度区间",
        "",
        "| 题材热度 | 样本数 | 平均开盘收益 |",
        "| --- | ---: | ---: |",
    ])
    for item in bucket_summary(rows, "heat_bucket"):
        lines.append(f"| {item['bucket']} | {item['count']} | {item['avg_return_pct']:.2f}% |")
    if gap_rows:
        lines.extend([
            "",
            "## 排序漏选相对差异",
            "",
            "说明：差异 = 排序选中票 - 事后最优票。正数表示选中票更贵、成交额更大或题材热度更高。",
            "",
            "| 排序规则 | 样本数 | 平均价格差 | 平均成交额差 | 平均题材热度差 | 平均收益差 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ])
        for item in gap_rows:
            lines.append(
                f"| {item['ranker']} | {item['samples']} | {item['avg_price_diff']:.2f} | "
                f"{item['avg_amount_diff']:.2f}亿 | {item['avg_heat_diff']:.2f} | "
                f"{item['avg_return_gap']:.2f}% |"
            )
    lines.extend([
        "",
        "## 每日事后最优",
        "",
        "| 交易日 | 代码 | 名称 | 开盘收益 | 价格 | 成交额 | 题材热度 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ])
    for row in rows:
        lines.append(
            f"| {row['date']} | {row['code']} | {row['name']} | {row['return_pct']:.2f}% | "
            f"{row['price']:.2f} | {row['amount_yi']:.2f}亿 | {row['topic_heat']:.0f} |"
        )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def run_profile(start: str, end: str, branch: str = "01B") -> Path:
    detail_path = ROOT / "reports" / "strategy_01" / "_archive" / "ranking_compare" / f"{start}_to_{end}_{branch}_details.csv"
    detail_rows = read_detail_rows(detail_path)
    best_rows = unique_best_rows(detail_rows)
    lookup = candidate_lookup(start, end, branch)
    enriched = enrich_best_rows(best_rows, lookup)
    best_features = {row["code"]: row for row in enriched}
    gap_rows = selection_gap_summary(detail_rows, best_features)
    return write_report(start, end, branch, enriched, gap_rows)


def main() -> int:
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-05-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2026-06-22"
    branch = sys.argv[3] if len(sys.argv) > 3 else "01B"
    path = run_profile(start, end, branch)
    print(f"报告: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
