"""
High-participation replay simulator.

This module does not change the live strategy. It replays the existing
historical candidate pool and asks: if we must trade on X% of days, what does
the win rate / payoff look like?
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import optimizer


SKILL_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_ROOT / "data"
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
SAMPLE_POOL_PATH = DATA_DIR / "strategy_samples.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _profit_loss_ratio(returns: list[float]) -> float:
    wins = [r for r in returns if r > 0]
    losses = [-r for r in returns if r < 0]
    if not wins:
        return 0.0
    if not losses:
        return 999.0
    avg_win = sum(wins) / len(wins)
    avg_loss = sum(losses) / len(losses)
    if avg_loss <= 0:
        return 999.0
    return round(avg_win / avg_loss, 4)


def _max_consecutive_loss(picks: list[dict]) -> int:
    max_loss = 0
    current = 0
    for pick in sorted(picks, key=lambda p: str(p.get("date", ""))):
        if pick.get("return", 0) > 0:
            current = 0
        else:
            current += 1
            max_loss = max(max_loss, current)
    return max_loss


def _best_candidate_for_day(sample: dict, config: dict) -> dict | None:
    candidates = []
    for raw in sample.get("candidate_pool", []):
        if not isinstance(raw.get("return"), (int, float)):
            continue
        item = dict(raw)
        if config.get("factors"):
            item["_new_score"] = optimizer._score_candidate(item, config)
        else:
            item["_new_score"] = float(
                item.get("score", item.get("factor_scores", {}).get("score", 0)) or 0
            )
        candidates.append(item)
    if not candidates:
        return None
    candidates.sort(
        key=lambda x: (
            -float(x.get("_new_score", x.get("score", 0)) or 0),
            -float(x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0) or 0),
            -float(x.get("factor_scores", {}).get("F4_tail_rally_strength", 0) or 0),
        )
    )
    return candidates[0]


def _daily_ranked_picks(samples: list[dict], config: dict) -> list[dict]:
    picks = []
    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        candidate = _best_candidate_for_day(sample, config)
        if candidate is None:
            continue
        picks.append({
            "date": sample.get("date", ""),
            "symbol": candidate.get("symbol", ""),
            "name": candidate.get("name", ""),
            "score": round(float(candidate.get("_new_score", candidate.get("score", 0)) or 0), 4),
            "return": float(candidate.get("return", 0) or 0),
            "win": float(candidate.get("return", 0) or 0) > 0,
            "buy_price": candidate.get("buy_price"),
            "buy_price_source": candidate.get("buy_price_source", ""),
            "sell_price": candidate.get("sell_price"),
            "sell_price_source": candidate.get("sell_price_source", ""),
        })
    return picks


def _summarize_target(all_picks: list[dict], total_days: int, target: float) -> dict:
    requested = max(0.0, min(float(target), 1.0))
    target_trades = int(math.ceil(total_days * requested))
    chosen = sorted(all_picks, key=lambda p: (-p.get("score", 0), str(p.get("date", ""))))[:target_trades]
    chosen = sorted(chosen, key=lambda p: str(p.get("date", "")))
    returns = [float(p.get("return", 0) or 0) for p in chosen]
    wins = [p for p in chosen if p.get("win")]
    trade_samples = len(chosen)
    return {
        "target_coverage": requested,
        "actual_coverage": round(trade_samples / total_days, 4) if total_days else 0,
        "target_trades": target_trades,
        "trade_samples": trade_samples,
        "empty_days": max(total_days - trade_samples, 0),
        "win_rate": round(len(wins) / trade_samples, 4) if trade_samples else 0,
        "avg_return": round(sum(returns) / trade_samples, 4) if trade_samples else 0,
        "total_return": round(sum(returns), 4),
        "profit_loss_ratio": _profit_loss_ratio(returns),
        "max_consecutive_loss": _max_consecutive_loss(chosen),
        "picks": chosen,
    }


def simulate_targets(samples: list[dict], config: dict,
                     targets: list[float] | None = None) -> dict:
    targets = targets or [0.75, 0.80, 0.85]
    usable = [s for s in samples if s.get("candidate_pool")]
    total_days = len(usable)
    all_picks = _daily_ranked_picks(usable, config)
    return {
        "total_days": total_days,
        "days_with_candidate": len(all_picks),
        "max_possible_coverage": round(len(all_picks) / total_days, 4) if total_days else 0,
        "targets": [_summarize_target(all_picks, total_days, target) for target in targets],
    }


def simulate_from_files(targets: list[float] | None = None) -> dict:
    config = _load_json(CONFIG_PATH)
    samples = [
        s for s in _load_json(SAMPLE_POOL_PATH).get("samples", [])
        if s.get("sample_type") == "historical_training"
    ]
    return simulate_targets(samples, config, targets=targets)


def format_summary(result: dict, include_picks: int = 0) -> str:
    lines = [
        "=== 高出手率模拟 ===",
        f"样本日: {result.get('total_days', 0)}",
        f"可选候选日: {result.get('days_with_candidate', 0)}",
        f"理论最高出手率: {result.get('max_possible_coverage', 0):.2%}",
        "",
        "| 目标出手率 | 实际出手率 | 出手/空仓 | 胜率 | 平均收益 | 盈亏比 | 最大连亏 |",
        "|------------|------------|-----------|------|----------|--------|----------|",
    ]
    for tier in result.get("targets", []):
        pl = tier.get("profit_loss_ratio", 0)
        pl_text = "-" if pl == 0 else ("∞" if pl >= 999 else f"1:{pl:.2f}")
        lines.append(
            f"| {tier.get('target_coverage', 0):.0%} | "
            f"{tier.get('actual_coverage', 0):.2%} | "
            f"{tier.get('trade_samples', 0)}/{tier.get('empty_days', 0)} | "
            f"{tier.get('win_rate', 0):.2%} | "
            f"{tier.get('avg_return', 0):.2%} | "
            f"{pl_text} | "
            f"{tier.get('max_consecutive_loss', 0)} |"
        )
        if include_picks:
            for pick in tier.get("picks", [])[-include_picks:]:
                lines.append(
                    f"  - {pick.get('date')} {pick.get('symbol')} "
                    f"{pick.get('return', 0):.2%} score={pick.get('score', 0):.2f}"
                )
    return "\n".join(lines)
