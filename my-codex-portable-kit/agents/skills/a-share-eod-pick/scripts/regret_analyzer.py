"""
Opportunity-regret diagnostics for the A-share overnight strategy.

This module is intentionally non-invasive: it replays the stored candidate
pool, compares the strategy pick with the next-day oracle best candidate, and
reports where the oracle candidate was blocked by the current selection rules.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

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


def _candidate_return(candidate: dict) -> float | None:
    value = candidate.get("return")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _oracle_best(sample: dict) -> dict | None:
    candidates = [
        candidate for candidate in sample.get("candidate_pool", [])
        if _candidate_return(candidate) is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda c: float(c.get("return", 0) or 0))


def _oracle_blockers(candidate: dict, config: dict) -> list[str]:
    blockers = []
    scored = dict(candidate)
    scored["_new_score"] = optimizer._score_candidate(scored, config)
    selection = config.get("selection", {})
    score_threshold = float(selection.get("score_threshold", 60) or 0)
    if float(scored.get("_new_score", 0) or 0) < score_threshold:
        blockers.append("score<threshold")

    fs = scored.get("factor_scores", {})
    for key, min_value in selection.get("min_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) < float(min_value):
            blockers.append(f"{key}<min")
    for key, max_value in selection.get("max_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) > float(max_value):
            blockers.append(f"{key}>max")

    if not blockers:
        blockers.append("passes_current_rules")
    return blockers


def _rescue_config(config: dict) -> dict:
    rescue = config.get("selection", {}).get("counterfactual_rescue", {})
    return rescue if isinstance(rescue, dict) else {}


def _oracle_rescue_eligible(sample: dict, oracle: dict, config: dict) -> bool:
    rescue = _rescue_config(config)
    if not rescue.get("enabled"):
        return False
    rescue_pick = optimizer._pick_counterfactual_rescue_candidate(
        sample,
        config,
        rescue_score_threshold=float(rescue.get("rescue_score_threshold", 80) or 80),
        max_blockers=int(rescue.get("max_blockers", 3) or 3),
        allowed_blocker_prefixes=tuple(rescue.get("allowed_blocker_prefixes", ()) or ()),
        required_blocker_prefixes=tuple(rescue.get("required_blocker_prefixes", ()) or ()),
        rescue_min_factor_scores=rescue.get("rescue_min_factor_scores", {}),
    )
    return bool(rescue_pick and rescue_pick.get("symbol") == oracle.get("symbol"))


def _rank_by_new_score(sample: dict, config: dict) -> list[dict]:
    ranked = []
    for raw in sample.get("candidate_pool", []):
        if _candidate_return(raw) is None:
            continue
        candidate = dict(raw)
        candidate["_new_score"] = optimizer._score_candidate(candidate, config)
        ranked.append(candidate)
    ranked.sort(
        key=lambda c: (
            -float(c.get("_new_score", 0) or 0),
            -float(c.get("factor_scores", {}).get("F1_tail_fund_inflow", 0) or 0),
            -float(c.get("factor_scores", {}).get("F4_tail_rally_strength", 0) or 0),
        )
    )
    return ranked


def _symbol_rank(ranked: list[dict], symbol: str | None) -> int | None:
    if not symbol:
        return None
    for index, candidate in enumerate(ranked, start=1):
        if candidate.get("symbol") == symbol:
            return index
    return None


def _numeric_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"avg": 0, "min": 0, "max": 0}
    return {
        "avg": round(sum(values) / len(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def _factor_summary(rows: list[dict]) -> dict[str, dict[str, float]]:
    keys = sorted({
        key
        for row in rows
        for key in row.get("factor_scores", {})
    })
    return {
        key: _numeric_summary([
            float(row.get("factor_scores", {}).get(key, 0) or 0)
            for row in rows
        ])
        for key in keys
    }


def _context_summary(rows: list[dict]) -> dict[str, dict[str, float]]:
    return {
        key: _numeric_summary([
            float(row.get(key, 0) or 0)
            for row in rows
        ])
        for key in ("candidate_pool_size", "rescue_candidate_count")
    }


def analyze_rescue_profile(
    samples: list[dict],
    config: dict,
    rescue_score_threshold: float = 68.0,
    max_blockers: int = 3,
    min_rescue_score_advantage: float = 0.0,
    max_rescue_score_advantage: float | None = None,
    allowed_blocker_prefixes: tuple[str, ...] | None = None,
    required_blocker_prefixes: tuple[str, ...] | None = None,
    rescue_min_factor_scores: dict | None = None,
    rescue_max_factor_scores: dict | None = None,
    rescue_when_base_absent_only: bool = False,
    rescue_when_base_present_only: bool = False,
    min_rescue_score_rank: int | None = None,
    max_rescue_score_rank: int | None = None,
) -> dict[str, Any]:
    """Profile rescue-mode trades by outcome and context."""
    rescue_rows = []
    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            candidate for candidate in sample.get("candidate_pool", [])
            if _candidate_return(candidate) is not None
        ]
        if not valid_candidates:
            continue
        base_pick = optimizer._base_pick_from_candidate_pool(sample, config)
        rescue_pick = optimizer._pick_counterfactual_rescue_candidate(
            sample,
            config,
            rescue_score_threshold=rescue_score_threshold,
            max_blockers=max_blockers,
            allowed_blocker_prefixes=allowed_blocker_prefixes,
            required_blocker_prefixes=required_blocker_prefixes,
            rescue_min_factor_scores=rescue_min_factor_scores,
            rescue_max_factor_scores=rescue_max_factor_scores,
        )
        if rescue_pick is None:
            continue

        rescue_candidate_count = 0
        for raw in valid_candidates:
            item = dict(raw)
            item["_new_score"] = optimizer._score_candidate(item, config)
            if optimizer._passes_selection(item, config):
                continue
            fs = item.get("factor_scores", {})
            if any(
                float(fs.get(key, 0) or 0) < float(value)
                for key, value in (rescue_min_factor_scores or {}).items()
            ):
                continue
            if any(
                float(fs.get(key, 0) or 0) > float(value)
                for key, value in (rescue_max_factor_scores or {}).items()
            ):
                continue
            blockers = optimizer._selection_blockers(item, config)
            hard_blockers = [b for b in blockers if b != "score<threshold"]
            allowed_prefixes = allowed_blocker_prefixes or (
                "F1_tail_fund_inflow>max",
                "F2_volume_price_sync<min",
                "F3_technical_pattern<min",
                "F7_float_mv_fit>max",
                "F8_overnight_risk_control<min",
                "F8_overnight_risk_control>max",
                "F9_overheat_control<min",
            )
            if len(hard_blockers) > max_blockers:
                continue
            if not all(any(b.startswith(prefix) for prefix in allowed_prefixes) for b in hard_blockers):
                continue
            if not all(
                any(b.startswith(prefix) for b in hard_blockers)
                for prefix in (required_blocker_prefixes or ())
            ):
                continue
            if float(item.get("_new_score", 0) or 0) < rescue_score_threshold:
                continue
            rescue_candidate_count += 1

        ranked = _rank_by_new_score(sample, config)
        rescue_rank = _symbol_rank(ranked, rescue_pick.get("symbol"))
        if min_rescue_score_rank is not None or max_rescue_score_rank is not None:
            if not optimizer._rescue_rank_allowed(
                rescue_rank,
                min_rescue_score_rank,
                max_rescue_score_rank,
            ):
                continue

        mode = None
        if base_pick is None:
            if not rescue_when_base_present_only:
                mode = "rescue"
        elif not rescue_when_base_absent_only:
            rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
            base_score = float(base_pick.get("_new_score", 0) or 0)
            score_advantage = rescue_score - base_score
            max_advantage_ok = (
                max_rescue_score_advantage is None
                or score_advantage <= float(max_rescue_score_advantage)
            )
            if score_advantage >= min_rescue_score_advantage and max_advantage_ok:
                mode = "rescue"
        if mode != "rescue":
            continue

        oracle = _oracle_best(sample)
        rescue_return = float(rescue_pick.get("return", 0) or 0)
        rescue_rows.append({
            "date": sample.get("date", ""),
            "month": str(sample.get("date", ""))[:7],
            "symbol": rescue_pick.get("symbol"),
            "return": rescue_return,
            "win": rescue_return > 0,
            "score": rescue_pick.get("_new_score"),
            "score_rank": rescue_rank,
            "factor_scores": dict(rescue_pick.get("factor_scores", {})),
            "candidate_pool_size": len(valid_candidates),
            "rescue_candidate_count": rescue_candidate_count,
            "blockers": rescue_pick.get("_rescue_blockers", []),
            "oracle_symbol": oracle.get("symbol") if oracle else None,
            "hit_oracle": bool(oracle and rescue_pick.get("symbol") == oracle.get("symbol")),
        })

    win_rows = [row for row in rescue_rows if row["win"]]
    loss_rows = [row for row in rescue_rows if not row["win"]]

    def count_many(rows: list[dict], key: str) -> Counter:
        counter = Counter()
        for row in rows:
            values = row.get(key, [])
            if isinstance(values, list):
                counter.update(values)
            elif values:
                counter.update([values])
        return counter

    returns = [row["return"] for row in rescue_rows]
    return {
        "rescue_trades": len(rescue_rows),
        "rescue_wins": len(win_rows),
        "rescue_losses": len(loss_rows),
        "rescue_win_rate": round(len(win_rows) / len(rescue_rows), 4) if rescue_rows else 0,
        "avg_rescue_return": round(sum(returns) / len(returns), 4) if returns else 0,
        "oracle_hits": sum(1 for row in rescue_rows if row["hit_oracle"]),
        "win_blockers": dict(count_many(win_rows, "blockers")),
        "loss_blockers": dict(count_many(loss_rows, "blockers")),
        "win_months": dict(count_many(win_rows, "month")),
        "loss_months": dict(count_many(loss_rows, "month")),
        "win_factor_summary": _factor_summary(win_rows),
        "loss_factor_summary": _factor_summary(loss_rows),
        "win_context_summary": _context_summary(win_rows),
        "loss_context_summary": _context_summary(loss_rows),
        "top_losses": sorted(loss_rows, key=lambda row: (row["return"], row["date"]))[:10],
        "top_wins": sorted(win_rows, key=lambda row: (-row["return"], row["date"]))[:10],
    }


def analyze_rescue_delta(
    samples: list[dict],
    config: dict,
    rescue_score_threshold: float = 68.0,
    max_blockers: int = 3,
    min_rescue_score_advantage: float = 0.0,
    max_rescue_score_advantage: float | None = None,
    allowed_blocker_prefixes: tuple[str, ...] | None = None,
    required_blocker_prefixes: tuple[str, ...] | None = None,
    rescue_min_factor_scores: dict | None = None,
    rescue_max_factor_scores: dict | None = None,
    rescue_when_base_absent_only: bool = False,
    rescue_when_base_present_only: bool = False,
    min_rescue_score_rank: int | None = None,
    max_rescue_score_rank: int | None = None,
) -> dict[str, Any]:
    """Compare a raw rescue gate against the base pick day by day."""
    rows = []
    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            candidate for candidate in sample.get("candidate_pool", [])
            if _candidate_return(candidate) is not None
        ]
        if not valid_candidates:
            continue

        oracle = _oracle_best(sample)
        oracle_return = float(oracle.get("return", 0) or 0) if oracle else 0.0
        base_pick = optimizer._base_pick_from_candidate_pool(sample, config)
        rescue_pick = optimizer._pick_counterfactual_rescue_candidate(
            sample,
            config,
            rescue_score_threshold=rescue_score_threshold,
            max_blockers=max_blockers,
            allowed_blocker_prefixes=allowed_blocker_prefixes,
            required_blocker_prefixes=required_blocker_prefixes,
            rescue_min_factor_scores=rescue_min_factor_scores,
            rescue_max_factor_scores=rescue_max_factor_scores,
        )
        if rescue_pick is None:
            continue

        ranked = _rank_by_new_score(sample, config)
        rescue_rank = _symbol_rank(ranked, rescue_pick.get("symbol"))
        if min_rescue_score_rank is not None or max_rescue_score_rank is not None:
            if not optimizer._rescue_rank_allowed(
                rescue_rank,
                min_rescue_score_rank,
                max_rescue_score_rank,
            ):
                continue

        if base_pick is not None and rescue_when_base_absent_only:
            continue
        if base_pick is None and rescue_when_base_present_only:
            continue

        base_return = float(base_pick.get("return", 0) or 0) if base_pick else 0.0
        rescue_return = float(rescue_pick.get("return", 0) or 0)
        if base_pick is not None:
            rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
            base_score = float(base_pick.get("_new_score", 0) or 0)
            score_advantage = rescue_score - base_score
            max_advantage_ok = (
                max_rescue_score_advantage is None
                or score_advantage <= float(max_rescue_score_advantage)
            )
            if score_advantage < min_rescue_score_advantage or not max_advantage_ok:
                continue

        base_symbol = base_pick.get("symbol") if base_pick else None
        rescue_symbol = rescue_pick.get("symbol")
        if base_symbol == rescue_symbol:
            continue

        base_regret = max(0.0, oracle_return - base_return)
        rescue_regret = max(0.0, oracle_return - rescue_return)
        return_delta = rescue_return - base_return
        regret_delta = rescue_regret - base_regret
        rows.append({
            "date": sample.get("date", ""),
            "change_type": "replaced" if base_pick else "added",
            "base_symbol": base_symbol,
            "base_return": round(base_return, 4),
            "rescue_symbol": rescue_symbol,
            "rescue_return": round(rescue_return, 4),
            "return_delta": round(return_delta, 4),
            "oracle_symbol": oracle.get("symbol") if oracle else None,
            "oracle_return": round(oracle_return, 4),
            "base_regret": round(base_regret, 4),
            "rescue_regret": round(rescue_regret, 4),
            "regret_delta": round(regret_delta, 4),
            "rescue_score": rescue_pick.get("_new_score"),
            "rescue_score_rank": rescue_rank,
            "rescue_blockers": rescue_pick.get("_rescue_blockers", []),
            "rescue_factor_scores": dict(rescue_pick.get("factor_scores", {})),
        })

    rows.sort(key=lambda row: (float(row["return_delta"]), str(row["date"])))
    net_return_delta = sum(float(row["return_delta"]) for row in rows)
    net_regret_delta = sum(float(row["regret_delta"]) for row in rows)
    return {
        "changed_days": len(rows),
        "added_trade_days": sum(1 for row in rows if row["change_type"] == "added"),
        "replaced_trade_days": sum(1 for row in rows if row["change_type"] == "replaced"),
        "improved_days": sum(1 for row in rows if float(row["return_delta"]) > 0),
        "worsened_days": sum(1 for row in rows if float(row["return_delta"]) < 0),
        "net_return_delta": round(net_return_delta, 4),
        "net_regret_delta": round(net_regret_delta, 4),
        "avg_return_delta": round(net_return_delta / len(rows), 4) if rows else 0,
        "avg_regret_delta": round(net_regret_delta / len(rows), 4) if rows else 0,
        "blocker_counts": dict(Counter(
            blocker
            for row in rows
            for blocker in row.get("rescue_blockers", [])
        )),
        "changed_rows": rows,
    }


def analyze_rescue_delta_segments(
    delta_result: dict[str, Any],
    factor_keys: tuple[str, ...] = (
        "F1_tail_fund_inflow",
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F7_float_mv_fit",
        "F8_overnight_risk_control",
        "F9_overheat_control",
    ),
    factor_bins: tuple[float, ...] = (70, 80, 90),
) -> dict[str, Any]:
    """Aggregate rescue delta rows into interpretable profit/regret segments."""
    rows = list(delta_result.get("changed_rows", []) or [])

    def rank_bucket(row: dict) -> str:
        rank = row.get("rescue_score_rank")
        if not isinstance(rank, int):
            return "NA"
        if rank == 1:
            return "1"
        if rank <= 3:
            return "2-3"
        if rank <= 5:
            return "4-5"
        return "6+"

    def factor_bucket(value: float) -> str:
        lower = 0.0
        for boundary in factor_bins:
            if value < boundary:
                return f"{int(lower)}-{int(boundary)}"
            lower = boundary
        return f"{int(lower)}+"

    def summarize(grouped: dict[str, list[dict]]) -> list[dict]:
        summaries = []
        for segment, segment_rows in grouped.items():
            net_return_delta = sum(float(row.get("return_delta", 0) or 0) for row in segment_rows)
            net_regret_delta = sum(float(row.get("regret_delta", 0) or 0) for row in segment_rows)
            summaries.append({
                "segment": segment,
                "days": len(segment_rows),
                "improved_days": sum(1 for row in segment_rows if float(row.get("return_delta", 0) or 0) > 0),
                "worsened_days": sum(1 for row in segment_rows if float(row.get("return_delta", 0) or 0) < 0),
                "net_return_delta": round(net_return_delta, 4),
                "avg_return_delta": round(net_return_delta / len(segment_rows), 4) if segment_rows else 0,
                "net_regret_delta": round(net_regret_delta, 4),
                "avg_regret_delta": round(net_regret_delta / len(segment_rows), 4) if segment_rows else 0,
            })
        summaries.sort(key=lambda item: (str(item["segment"])))
        return summaries

    change_groups: dict[str, list[dict]] = defaultdict(list)
    rank_groups: dict[str, list[dict]] = defaultdict(list)
    factor_groups: dict[str, dict[str, list[dict]]] = {
        key: defaultdict(list)
        for key in factor_keys
    }
    for row in rows:
        change_groups[str(row.get("change_type", "unknown"))].append(row)
        rank_groups[rank_bucket(row)].append(row)
        fs = row.get("rescue_factor_scores", {}) or {}
        for key in factor_keys:
            value = float(fs.get(key, 0) or 0)
            factor_groups[key][factor_bucket(value)].append(row)

    return {
        "change_type": summarize(change_groups),
        "rank_bucket": summarize(rank_groups),
        "factor_bins": {
            key: summarize(groups)
            for key, groups in factor_groups.items()
        },
    }


def _split_for_validation(samples: list[dict], validation_ratio: float) -> tuple[list[dict], list[dict]]:
    ordered = sorted(samples, key=lambda sample: str(sample.get("date", "")))
    if not ordered:
        return [], []
    validation_size = max(1, int(round(len(ordered) * float(validation_ratio))))
    validation_size = min(validation_size, len(ordered))
    return ordered[:-validation_size], ordered[-validation_size:]


def _rescue_delta_score(delta: dict[str, Any]) -> dict[str, Any]:
    rows = list(delta.get("changed_rows", []) or [])
    return {
        "changed_days": int(delta.get("changed_days", 0) or 0),
        "added_trade_days": int(delta.get("added_trade_days", 0) or 0),
        "replaced_trade_days": int(delta.get("replaced_trade_days", 0) or 0),
        "improved_days": int(delta.get("improved_days", 0) or 0),
        "worsened_days": int(delta.get("worsened_days", 0) or 0),
        "total_return_delta": round(sum(float(row.get("return_delta", 0) or 0) for row in rows), 4),
        "total_regret_delta": round(sum(float(row.get("regret_delta", 0) or 0) for row in rows), 4),
    }


def analyze_rescue_experiments(
    samples: list[dict],
    config: dict,
    experiments: list[dict],
    validation_ratio: float = 0.3,
) -> dict[str, Any]:
    """Rank rescue experiments by full-sample and validation regret impact."""
    _, validation_samples = _split_for_validation(samples, validation_ratio)
    rows = []
    for experiment in experiments:
        params = dict(experiment.get("params", {}) or {})
        full_delta = analyze_rescue_delta(samples, config, **params)
        validation_delta = analyze_rescue_delta(validation_samples, config, **params)
        full_score = _rescue_delta_score(full_delta)
        validation_score = _rescue_delta_score(validation_delta)
        if validation_score["total_regret_delta"] > 0:
            decision = "reject_validation_regret"
        elif validation_score["changed_days"] == 0:
            decision = "reject_no_validation_signal"
        elif full_score["total_regret_delta"] > 0:
            decision = "reject_full_regret"
        else:
            decision = "candidate_watch"
        rows.append({
            "name": experiment.get("name", "unnamed"),
            "params": params,
            "decision": decision,
            "full": full_score,
            "validation": validation_score,
        })
    rows.sort(
        key=lambda row: (
            float(row.get("validation", {}).get("total_regret_delta", 0) or 0),
            float(row.get("full", {}).get("total_regret_delta", 0) or 0),
            str(row.get("name", "")),
        )
    )
    return {
        "validation_ratio": validation_ratio,
        "validation_days": len(validation_samples),
        "experiments": rows,
    }


def analyze_high_return_miss_segments(
    samples: list[dict],
    config: dict,
    min_oracle_return: float = 0.05,
) -> dict[str, Any]:
    """Segment the largest missed next-day winners by actionable context."""
    rows = []
    neighbor_rescue = config.get("selection", {}).get("neighbor_counterfactual_rescue", {})
    neighbor_segment_history: dict[tuple[str, ...], list[dict]] = {}

    def rank_bucket(rank: int | None) -> str:
        if rank is None:
            return "NA"
        if rank == 1:
            return "1"
        if rank <= 3:
            return "2-3"
        if rank <= 5:
            return "4-5"
        if rank <= 10:
            return "6-10"
        return "11+"

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        if not sample.get("candidate_pool"):
            continue
        oracle = _oracle_best(sample)
        if oracle is None:
            continue
        oracle_return = float(oracle.get("return", 0) or 0)
        if oracle_return < float(min_oracle_return):
            continue

        ranked = _rank_by_new_score(sample, config)
        if isinstance(neighbor_rescue, dict) and neighbor_rescue.get("enabled"):
            pick = optimizer._pick_neighbor_counterfactual_rescue_candidate(
                sample,
                config,
                neighbor_rescue,
                neighbor_segment_history,
            )
        else:
            pick = optimizer.pick_from_candidate_pool(sample, config)

        if pick is None:
            selected_return = 0.0
            selected_symbol = None
            miss_type = "empty"
        else:
            selected_return = float(pick.get("return", 0) or 0)
            selected_symbol = pick.get("symbol")
            miss_type = "replacement"

        regret = max(0.0, oracle_return - selected_return)
        if regret <= 0 or selected_symbol == oracle.get("symbol"):
            continue

        oracle_rank = _symbol_rank(ranked, oracle.get("symbol"))
        blockers = _oracle_blockers(oracle, config)
        blocker_combo = "+".join(blockers) if blockers else "passes_current_rules"
        rows.append({
            "date": sample.get("date", ""),
            "miss_type": miss_type,
            "regret": round(regret, 4),
            "selected_symbol": selected_symbol,
            "selected_return": round(selected_return, 4),
            "oracle_symbol": oracle.get("symbol"),
            "oracle_name": oracle.get("name", ""),
            "oracle_return": round(oracle_return, 4),
            "oracle_score": round(float(oracle.get("_new_score", oracle.get("score", 0)) or 0), 4),
            "oracle_rank": oracle_rank,
            "oracle_rank_bucket": rank_bucket(oracle_rank),
            "oracle_blockers": blockers,
            "blocker_combo": blocker_combo,
            "oracle_factor_scores": dict(oracle.get("factor_scores", {})),
        })

    def summarize(key: str) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(key, "unknown"))].append(row)
        summaries = []
        for segment, segment_rows in grouped.items():
            total_regret = sum(float(row.get("regret", 0) or 0) for row in segment_rows)
            summaries.append({
                "segment": segment,
                "days": len(segment_rows),
                "total_regret": round(total_regret, 4),
                "avg_regret": round(total_regret / len(segment_rows), 4) if segment_rows else 0,
                "avg_oracle_return": round(
                    sum(float(row.get("oracle_return", 0) or 0) for row in segment_rows) / len(segment_rows),
                    4,
                ) if segment_rows else 0,
                "oracle_factor_summary": _factor_summary([
                    {"factor_scores": row.get("oracle_factor_scores", {})}
                    for row in segment_rows
                ]),
            })
        summaries.sort(
            key=lambda item: (
                -float(item.get("total_regret", 0) or 0),
                str(item.get("segment", "")),
            )
        )
        return summaries

    rows.sort(key=lambda row: (-float(row.get("regret", 0) or 0), str(row.get("date", ""))))
    total_regret = sum(float(row.get("regret", 0) or 0) for row in rows)
    return {
        "min_oracle_return": min_oracle_return,
        "major_miss_days": len(rows),
        "total_major_regret": round(total_regret, 4),
        "avg_major_regret": round(total_regret / len(rows), 4) if rows else 0,
        "by_miss_type": summarize("miss_type"),
        "by_oracle_rank": summarize("oracle_rank_bucket"),
        "by_blocker_combo": summarize("blocker_combo"),
        "top_misses": rows[:10],
    }


def analyze_replacement_decoy_profile(
    samples: list[dict],
    config: dict,
    min_oracle_return: float = 0.05,
) -> dict[str, Any]:
    """Compare wrongly selected replacement picks against high-return oracles."""
    rows = []
    neighbor_rescue = config.get("selection", {}).get("neighbor_counterfactual_rescue", {})
    neighbor_segment_history: dict[tuple[str, ...], list[dict]] = {}

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        if not sample.get("candidate_pool"):
            continue
        oracle = _oracle_best(sample)
        if oracle is None:
            continue
        oracle_return = float(oracle.get("return", 0) or 0)
        if oracle_return < float(min_oracle_return):
            continue

        ranked = _rank_by_new_score(sample, config)
        if isinstance(neighbor_rescue, dict) and neighbor_rescue.get("enabled"):
            pick = optimizer._pick_neighbor_counterfactual_rescue_candidate(
                sample,
                config,
                neighbor_rescue,
                neighbor_segment_history,
            )
        else:
            pick = optimizer.pick_from_candidate_pool(sample, config)
        if pick is None or pick.get("symbol") == oracle.get("symbol"):
            continue

        selected_return = float(pick.get("return", 0) or 0)
        regret = max(0.0, oracle_return - selected_return)
        if regret <= 0:
            continue

        selected_fs = dict(pick.get("factor_scores", {}))
        oracle_fs = dict(oracle.get("factor_scores", {}))
        factor_keys = sorted(set(selected_fs) | set(oracle_fs))
        factor_delta = {
            key: float(selected_fs.get(key, 0) or 0) - float(oracle_fs.get(key, 0) or 0)
            for key in factor_keys
        }
        selected_rank = _symbol_rank(ranked, pick.get("symbol"))
        oracle_rank = _symbol_rank(ranked, oracle.get("symbol"))
        rank_delta = (
            selected_rank - oracle_rank
            if selected_rank is not None and oracle_rank is not None
            else None
        )
        rows.append({
            "date": sample.get("date", ""),
            "regret": round(regret, 4),
            "selected_symbol": pick.get("symbol"),
            "selected_return": round(selected_return, 4),
            "selected_rank": selected_rank,
            "oracle_symbol": oracle.get("symbol"),
            "oracle_name": oracle.get("name", ""),
            "oracle_return": round(oracle_return, 4),
            "oracle_rank": oracle_rank,
            "rank_delta": rank_delta,
            "return_delta": round(selected_return - oracle_return, 4),
            "selected_factor_scores": selected_fs,
            "oracle_factor_scores": oracle_fs,
            "decoy_minus_oracle_factor_delta": factor_delta,
            "oracle_blockers": _oracle_blockers(oracle, config),
        })

    delta_rows = [
        {"factor_scores": row.get("decoy_minus_oracle_factor_delta", {})}
        for row in rows
    ]
    selected_rows = [
        {"factor_scores": row.get("selected_factor_scores", {})}
        for row in rows
    ]
    oracle_rows = [
        {"factor_scores": row.get("oracle_factor_scores", {})}
        for row in rows
    ]
    rank_deltas = [
        float(row["rank_delta"])
        for row in rows
        if isinstance(row.get("rank_delta"), (int, float))
    ]
    rows.sort(key=lambda row: (float(row.get("return_delta", 0) or 0), str(row.get("date", ""))))
    total_regret = sum(float(row.get("regret", 0) or 0) for row in rows)
    return {
        "min_oracle_return": min_oracle_return,
        "replacement_miss_days": len(rows),
        "total_replacement_regret": round(total_regret, 4),
        "avg_replacement_regret": round(total_regret / len(rows), 4) if rows else 0,
        "avg_rank_delta": round(sum(rank_deltas) / len(rank_deltas), 4) if rank_deltas else 0,
        "selected_factor_summary": _factor_summary(selected_rows),
        "oracle_factor_summary": _factor_summary(oracle_rows),
        "decoy_minus_oracle_factor_delta": _factor_summary(delta_rows),
        "top_decoys": rows[:10],
    }


def _percentile_rank(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return round(sum(1 for item in values if item <= value) / len(values), 4)


def analyze_oracle_context_profile(
    samples: list[dict],
    config: dict,
    min_oracle_return: float = 0.05,
    strong_f1_threshold: float = 80.0,
    low_f9_threshold: float = 50.0,
) -> dict[str, Any]:
    """Profile high-return oracle misses against same-day candidate-pool context."""
    rows = []
    neighbor_rescue = config.get("selection", {}).get("neighbor_counterfactual_rescue", {})
    neighbor_segment_history: dict[tuple[str, ...], list[dict]] = {}

    def share_bucket(share: float) -> str:
        if share >= 0.4:
            return ">=40%"
        if share >= 0.2:
            return "20-40%"
        if share > 0:
            return "0-20%"
        return "0%"

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            candidate for candidate in sample.get("candidate_pool", [])
            if _candidate_return(candidate) is not None
        ]
        if not valid_candidates:
            continue
        oracle = _oracle_best(sample)
        if oracle is None:
            continue
        oracle_return = float(oracle.get("return", 0) or 0)
        if oracle_return < float(min_oracle_return):
            continue

        if isinstance(neighbor_rescue, dict) and neighbor_rescue.get("enabled"):
            pick = optimizer._pick_neighbor_counterfactual_rescue_candidate(
                sample,
                config,
                neighbor_rescue,
                neighbor_segment_history,
            )
        else:
            pick = optimizer.pick_from_candidate_pool(sample, config)
        selected_return = float(pick.get("return", 0) or 0) if pick else 0.0
        if pick is not None and pick.get("symbol") == oracle.get("symbol"):
            continue
        regret = max(0.0, oracle_return - selected_return)
        if regret <= 0:
            continue

        f1_values = [
            float(candidate.get("factor_scores", {}).get("F1_tail_fund_inflow", 0) or 0)
            for candidate in valid_candidates
        ]
        f9_values = [
            float(candidate.get("factor_scores", {}).get("F9_overheat_control", 0) or 0)
            for candidate in valid_candidates
        ]
        oracle_fs = oracle.get("factor_scores", {})
        oracle_f1 = float(oracle_fs.get("F1_tail_fund_inflow", 0) or 0)
        oracle_f9 = float(oracle_fs.get("F9_overheat_control", 0) or 0)
        strong_low_heat_count = sum(
            1
            for candidate in valid_candidates
            if float(candidate.get("factor_scores", {}).get("F1_tail_fund_inflow", 0) or 0)
            >= float(strong_f1_threshold)
            and float(candidate.get("factor_scores", {}).get("F9_overheat_control", 0) or 0)
            <= float(low_f9_threshold)
        )
        strong_low_heat_share = round(strong_low_heat_count / len(valid_candidates), 4)
        rows.append({
            "date": sample.get("date", ""),
            "regret": round(regret, 4),
            "oracle_symbol": oracle.get("symbol"),
            "oracle_name": oracle.get("name", ""),
            "oracle_return": round(oracle_return, 4),
            "selected_symbol": pick.get("symbol") if pick else None,
            "selected_return": round(selected_return, 4),
            "candidate_pool_size": len(valid_candidates),
            "oracle_f1": round(oracle_f1, 4),
            "oracle_f9": round(oracle_f9, 4),
            "oracle_f1_percentile": _percentile_rank(f1_values, oracle_f1),
            "oracle_f9_percentile": _percentile_rank(f9_values, oracle_f9),
            "strong_f1_low_f9_count": strong_low_heat_count,
            "strong_f1_low_f9_share": strong_low_heat_share,
            "strong_low_heat_share_bucket": share_bucket(strong_low_heat_share),
            "oracle_blockers": _oracle_blockers(oracle, config),
        })

    def average(key: str) -> float:
        values = [float(row.get(key, 0) or 0) for row in rows]
        return round(sum(values) / len(values), 4) if values else 0

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["strong_low_heat_share_bucket"]].append(row)
    share_segments = []
    for segment, segment_rows in grouped.items():
        total_regret = sum(float(row.get("regret", 0) or 0) for row in segment_rows)
        share_segments.append({
            "segment": segment,
            "days": len(segment_rows),
            "total_regret": round(total_regret, 4),
            "avg_regret": round(total_regret / len(segment_rows), 4) if segment_rows else 0,
            "avg_oracle_return": round(
                sum(float(row.get("oracle_return", 0) or 0) for row in segment_rows) / len(segment_rows),
                4,
            ) if segment_rows else 0,
        })
    share_segments.sort(key=lambda row: (-float(row.get("total_regret", 0) or 0), row["segment"]))

    rows.sort(key=lambda row: (-float(row.get("regret", 0) or 0), str(row.get("date", ""))))
    return {
        "min_oracle_return": min_oracle_return,
        "strong_f1_threshold": strong_f1_threshold,
        "low_f9_threshold": low_f9_threshold,
        "context_days": len(rows),
        "avg_candidate_pool_size": average("candidate_pool_size"),
        "avg_oracle_f1_percentile": average("oracle_f1_percentile"),
        "avg_oracle_f9_percentile": average("oracle_f9_percentile"),
        "avg_strong_f1_low_f9_share": average("strong_f1_low_f9_share"),
        "by_strong_low_heat_share": share_segments,
        "top_contexts": rows[:10],
    }


def analyze_miss_factor_deltas(samples: list[dict], config: dict) -> dict[str, Any]:
    """Compare oracle winners with the strategy pick on missed-opportunity days."""
    rows = []
    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        if not sample.get("candidate_pool"):
            continue
        oracle = _oracle_best(sample)
        if oracle is None:
            continue
        pick = optimizer.pick_from_candidate_pool(sample, config)
        if pick is None:
            selected_fs = {}
            selected_symbol = None
            selected_return = 0.0
            miss_type = "empty"
        else:
            selected_fs = dict(pick.get("factor_scores", {}))
            selected_symbol = pick.get("symbol")
            selected_return = float(pick.get("return", 0) or 0)
            miss_type = "replacement"
        oracle_return = float(oracle.get("return", 0) or 0)
        regret = max(0.0, oracle_return - selected_return)
        if regret <= 0 or selected_symbol == oracle.get("symbol"):
            continue

        oracle_fs = dict(oracle.get("factor_scores", {}))
        keys = sorted(set(oracle_fs) | set(selected_fs))
        deltas = {
            key: float(oracle_fs.get(key, 0) or 0) - float(selected_fs.get(key, 0) or 0)
            for key in keys
        }
        rows.append({
            "date": sample.get("date", ""),
            "regret": regret,
            "oracle_symbol": oracle.get("symbol"),
            "selected_symbol": selected_symbol,
            "oracle_factor_scores": oracle_fs,
            "selected_factor_scores": selected_fs,
            "factor_deltas": deltas,
            "miss_type": miss_type,
        })

    empty_rows = [row for row in rows if row["miss_type"] == "empty"]
    replacement_rows = [row for row in rows if row["miss_type"] == "replacement"]
    oracle_rows = [
        {"factor_scores": row["oracle_factor_scores"]}
        for row in rows
    ]
    selected_rows = [
        {"factor_scores": row["selected_factor_scores"]}
        for row in rows
    ]
    delta_rows = [
        {"factor_scores": row["factor_deltas"]}
        for row in rows
    ]
    empty_oracle_rows = [
        {"factor_scores": row["oracle_factor_scores"]}
        for row in empty_rows
    ]
    replacement_delta_rows = [
        {"factor_scores": row["factor_deltas"]}
        for row in replacement_rows
    ]
    delta_summary = _factor_summary(delta_rows)
    replacement_delta_summary = _factor_summary(replacement_delta_rows)
    ranked_deltas = [
        {
            "factor": factor,
            **summary,
        }
        for factor, summary in delta_summary.items()
    ]
    ranked_deltas.sort(key=lambda item: (-item["avg"], item["factor"]))

    return {
        "miss_days": len(rows),
        "empty_miss_days": len(empty_rows),
        "replacement_miss_days": len(replacement_rows),
        "oracle_factor_summary": _factor_summary(oracle_rows),
        "selected_factor_summary": _factor_summary(selected_rows),
        "delta_summary": delta_summary,
        "empty_miss_factor_summary": _factor_summary(empty_oracle_rows),
        "replacement_delta_summary": replacement_delta_summary,
        "top_positive_deltas": ranked_deltas[:10],
        "top_negative_deltas": sorted(ranked_deltas, key=lambda item: (item["avg"], item["factor"]))[:10],
        "top_misses": sorted(rows, key=lambda row: (-row["regret"], str(row["date"])))[:10],
    }


def analyze_regret(samples: list[dict], config: dict, top_miss_count: int = 12) -> dict[str, Any]:
    """Replay candidate pools and summarize opportunity loss.

    Regret is measured against the same T close -> T+1 open return used by the
    strategy: max(0, oracle_best_return - selected_return). Empty days count as
    selected_return = 0 because the missed opportunity is the paper-trading
    return that could have been selected from that day's stored candidate pool.
    """
    days = 0
    trade_days = 0
    exact_best_hits = 0
    top3_best_hits = 0
    top5_best_hits = 0
    oracle_rescue_eligible = 0
    selected_returns = []
    oracle_returns = []
    regrets = []
    blockers = Counter()
    misses = []
    neighbor_rescue = config.get("selection", {}).get("neighbor_counterfactual_rescue", {})
    neighbor_segment_history: dict[tuple[str, ...], list[dict]] = {}

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        if not sample.get("candidate_pool"):
            continue
        oracle = _oracle_best(sample)
        if oracle is None:
            continue

        days += 1
        ranked = _rank_by_new_score(sample, config)
        if isinstance(neighbor_rescue, dict) and neighbor_rescue.get("enabled"):
            pick = optimizer._pick_neighbor_counterfactual_rescue_candidate(
                sample,
                config,
                neighbor_rescue,
                neighbor_segment_history,
            )
        else:
            pick = optimizer.pick_from_candidate_pool(sample, config)
        oracle_return = float(oracle.get("return", 0) or 0)
        oracle_returns.append(oracle_return)

        if pick is None:
            selected_return = 0.0
            selected_symbol = None
            selected_score = None
        else:
            trade_days += 1
            selected_return = float(pick.get("return", 0) or 0)
            selected_symbol = pick.get("symbol")
            selected_score = pick.get("_new_score", pick.get("score"))
            selected_returns.append(selected_return)

        oracle_symbol = oracle.get("symbol")
        oracle_rank = _symbol_rank(ranked, oracle_symbol)
        selected_rank = _symbol_rank(ranked, selected_symbol)
        if selected_symbol == oracle_symbol:
            exact_best_hits += 1
        if oracle_rank is not None and selected_rank is not None:
            if oracle_rank <= 3 and selected_rank <= 3:
                top3_best_hits += 1
            if oracle_rank <= 5 and selected_rank <= 5:
                top5_best_hits += 1

        oracle_blockers = _oracle_blockers(oracle, config)
        rescue_eligible = _oracle_rescue_eligible(sample, oracle, config)
        if rescue_eligible:
            oracle_rescue_eligible += 1
            oracle_blockers = [*oracle_blockers, "rescue_eligible"]
        blockers.update(oracle_blockers)

        regret = max(0.0, oracle_return - selected_return)
        regrets.append(regret)
        if regret > 0:
            misses.append({
                "date": sample.get("date", ""),
                "regret": round(regret, 4),
                "selected_symbol": selected_symbol,
                "selected_return": round(selected_return, 4),
                "selected_score": selected_score,
                "selected_rank": selected_rank,
                "oracle_symbol": oracle_symbol,
                "oracle_name": oracle.get("name", ""),
                "oracle_return": round(oracle_return, 4),
                "oracle_score": round(float(oracle.get("_new_score", oracle.get("score", 0)) or 0), 4),
                "oracle_rank": oracle_rank,
                "oracle_blockers": oracle_blockers,
                "oracle_rescue_eligible": rescue_eligible,
            })

    misses.sort(key=lambda item: (-item["regret"], str(item["date"])))
    selected_denominator = trade_days or 1
    day_denominator = days or 1
    return {
        "days": days,
        "trade_days": trade_days,
        "empty_days": max(days - trade_days, 0),
        "coverage": round(trade_days / day_denominator, 4),
        "exact_best_hits": exact_best_hits,
        "exact_best_hit_rate": round(exact_best_hits / day_denominator, 4),
        "trade_exact_best_hit_rate": round(exact_best_hits / selected_denominator, 4),
        "top3_best_hit_rate": round(top3_best_hits / day_denominator, 4),
        "top5_best_hit_rate": round(top5_best_hits / day_denominator, 4),
        "oracle_rescue_eligible": oracle_rescue_eligible,
        "oracle_rescue_eligible_rate": round(oracle_rescue_eligible / day_denominator, 4),
        "avg_regret": round(sum(regrets) / day_denominator, 4),
        "total_regret": round(sum(regrets), 4),
        "avg_oracle_return": round(sum(oracle_returns) / day_denominator, 4),
        "avg_selected_return": round(sum(selected_returns) / selected_denominator, 4),
        "oracle_blockers": dict(blockers),
        "top_misses": misses[:top_miss_count],
    }


def analyze_from_files(sample_type: str = "historical_training") -> dict[str, Any]:
    config = _load_json(CONFIG_PATH)
    samples = [
        sample for sample in _load_json(SAMPLE_POOL_PATH).get("samples", [])
        if sample.get("sample_type") == sample_type
    ]
    return analyze_regret(samples, config)


def analyze_blocker_combo_regret(samples: list[dict], config: dict,
                                 top_combo_count: int = 20,
                                 top_miss_per_combo: int = 5) -> list[dict[str, Any]]:
    """Rank blocker combinations by cumulative opportunity loss."""
    sample_by_date = {
        str(sample.get("date", "")): sample
        for sample in samples
        if sample.get("candidate_pool")
    }
    regret = analyze_regret(
        samples,
        config,
        top_miss_count=max(len(samples), top_combo_count * top_miss_per_combo),
    )
    grouped: dict[tuple[str, ...], list[dict]] = {}
    for miss in regret.get("top_misses", []):
        if float(miss.get("regret", 0) or 0) <= 0:
            continue
        blockers = tuple(
            blocker for blocker in miss.get("oracle_blockers", [])
            if blocker != "rescue_eligible"
        )
        if not blockers:
            blockers = ("passes_current_rules",)
        grouped.setdefault(blockers, []).append(miss)

    rows = []
    for blockers, misses in grouped.items():
        ordered = sorted(
            misses,
            key=lambda row: (-float(row.get("regret", 0) or 0), str(row.get("date", ""))),
        )
        total_regret = sum(float(row.get("regret", 0) or 0) for row in ordered)
        oracle_factor_rows = []
        for miss in ordered:
            sample = sample_by_date.get(str(miss.get("date", "")))
            oracle = _oracle_best(sample or {})
            if oracle is not None:
                oracle_factor_rows.append({"factor_scores": dict(oracle.get("factor_scores", {}))})
        rows.append({
            "blockers": list(blockers),
            "miss_days": len(ordered),
            "total_regret": round(total_regret, 4),
            "avg_regret": round(total_regret / len(ordered), 4) if ordered else 0,
            "oracle_factor_summary": _factor_summary(oracle_factor_rows),
            "top_misses": ordered[:top_miss_per_combo],
        })

    rows.sort(
        key=lambda row: (
            -float(row.get("total_regret", 0) or 0),
            -int(row.get("miss_days", 0) or 0),
            row.get("blockers", []),
        )
    )
    return rows[:top_combo_count]


def format_summary(result: dict[str, Any],
                   combo_rows: list[dict[str, Any]] | None = None) -> str:
    lines = [
        "=== 机会损失诊断 ===",
        f"候选池样本日: {result.get('days', 0)}",
        f"出手/空仓: {result.get('trade_days', 0)}/{result.get('empty_days', 0)}",
        f"出手率: {result.get('coverage', 0):.2%}",
        f"命中次日最优: {result.get('exact_best_hit_rate', 0):.2%}",
        f"Top3邻近命中: {result.get('top3_best_hit_rate', 0):.2%}",
        f"oracle可被救援门接住: {result.get('oracle_rescue_eligible_rate', 0):.2%}",
        f"平均机会损失: {result.get('avg_regret', 0):.2%}",
        f"累计机会损失: {result.get('total_regret', 0):.2%}",
        f"oracle平均收益: {result.get('avg_oracle_return', 0):.2%}",
        f"当前选择平均收益: {result.get('avg_selected_return', 0):.2%}",
        "",
        "oracle最优票被当前规则拦截原因:",
    ]
    blockers = sorted(
        result.get("oracle_blockers", {}).items(),
        key=lambda item: (-item[1], item[0]),
    )
    for reason, count in blockers[:12]:
        lines.append(f"- {reason}: {count}")
    if combo_rows:
        lines.append("")
        lines.append("按 blocker 组合聚合的机会损失:")
        for row in combo_rows[:5]:
            factors = row.get("oracle_factor_summary", {})
            factor_text = " ".join(
                f"{key}={factors.get(key, {}).get('avg', 0):.1f}"
                for key in (
                    "F1_tail_fund_inflow",
                    "F3_technical_pattern",
                    "F4_tail_rally_strength",
                    "F7_float_mv_fit",
                    "F8_overnight_risk_control",
                    "F9_overheat_control",
                )
                if key in factors
            )
            lines.append(
                f"- regret={row.get('total_regret', 0):.2%} "
                f"days={row.get('miss_days', 0)} "
                f"avg={row.get('avg_regret', 0):.2%} "
                f"blockers={'+'.join(row.get('blockers', []))} "
                f"{factor_text}".rstrip()
            )
    lines.append("")
    lines.append("最大机会损失样本:")
    for miss in result.get("top_misses", [])[:8]:
        lines.append(
            f"- {miss.get('date')} regret={miss.get('regret', 0):.2%} "
            f"selected={miss.get('selected_symbol') or '空仓'} "
            f"({miss.get('selected_return', 0):.2%}) -> "
            f"oracle={miss.get('oracle_symbol')} {miss.get('oracle_name', '')} "
            f"({miss.get('oracle_return', 0):.2%})"
        )
    return "\n".join(lines)


def format_rescue_delta_segments(label: str, segments: dict[str, Any]) -> str:
    """Format compact rescue-delta segment diagnostics."""
    lines = [f"=== 救援增量分段: {label} ==="]

    def add_rows(prefix: str, rows: list[dict]):
        for row in rows:
            lines.append(
                f"- {prefix} {row.get('segment')}: "
                f"days={row.get('days', 0)} "
                f"improve/worse={row.get('improved_days', 0)}/{row.get('worsened_days', 0)} "
                f"net_return={row.get('net_return_delta', 0):.2%} "
                f"net_regret={row.get('net_regret_delta', 0):.2%}"
            )

    add_rows("change_type", segments.get("change_type", [])[:4])
    add_rows("rank", segments.get("rank_bucket", [])[:4])
    for factor in (
        "F1_tail_fund_inflow",
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F7_float_mv_fit",
        "F8_overnight_risk_control",
        "F9_overheat_control",
    ):
        factor_rows = segments.get("factor_bins", {}).get(factor, [])
        useful_rows = [
            row for row in factor_rows
            if int(row.get("days", 0) or 0) >= 2
            or abs(float(row.get("net_return_delta", 0) or 0)) >= 0.01
        ]
        add_rows(factor, useful_rows[:4])
    return "\n".join(lines)


def format_rescue_experiment_summary(label: str, result: dict[str, Any]) -> str:
    """Format promotion-gate results for rescue experiments."""
    lines = [
        f"=== 救援候选实验: {label} ===",
        f"验证段天数: {result.get('validation_days', 0)}",
    ]
    for row in result.get("experiments", [])[:10]:
        full = row.get("full", {})
        validation = row.get("validation", {})
        lines.append(
            f"- {row.get('name')}: {row.get('decision')} "
            f"full变更={full.get('changed_days', 0)} "
            f"full_regret={full.get('total_regret_delta', 0):.2%} "
            f"full_return={full.get('total_return_delta', 0):.2%} "
            f"验证变更={validation.get('changed_days', 0)} "
            f"验证regret={validation.get('total_regret_delta', 0):.2%} "
            f"验证return={validation.get('total_return_delta', 0):.2%}"
        )
    return "\n".join(lines)


def format_high_return_miss_segments(label: str, result: dict[str, Any]) -> str:
    """Format major missed-winner segments for strategy search."""
    lines = [
        f"=== 高收益 miss 分段: {label} ===",
        f"oracle收益阈值: {result.get('min_oracle_return', 0):.2%}",
        f"大额miss天数: {result.get('major_miss_days', 0)}",
        f"大额累计机会损失: {result.get('total_major_regret', 0):.2%}",
    ]

    def add_rows(title: str, rows: list[dict], limit: int = 5):
        lines.append(title)
        for row in rows[:limit]:
            factors = row.get("oracle_factor_summary", {})
            factor_text = " ".join(
                f"{key}={factors.get(key, {}).get('avg', 0):.1f}"
                for key in (
                    "F1_tail_fund_inflow",
                    "F2_volume_price_sync",
                    "F3_technical_pattern",
                    "F4_tail_rally_strength",
                    "F7_float_mv_fit",
                    "F8_overnight_risk_control",
                    "F9_overheat_control",
                )
                if key in factors
            )
            lines.append(
                f"- {row.get('segment')}: "
                f"days={row.get('days', 0)} "
                f"regret={row.get('total_regret', 0):.2%} "
                f"avg={row.get('avg_regret', 0):.2%} "
                f"oracle_avg={row.get('avg_oracle_return', 0):.2%} "
                f"{factor_text}".rstrip()
            )

    add_rows("按 miss 类型:", result.get("by_miss_type", []))
    add_rows("按 oracle 当日得分排名:", result.get("by_oracle_rank", []))
    add_rows("按 blocker 组合:", result.get("by_blocker_combo", []))

    lines.append("大额 miss 样本:")
    for miss in result.get("top_misses", [])[:6]:
        lines.append(
            f"- {miss.get('date')} regret={miss.get('regret', 0):.2%} "
            f"type={miss.get('miss_type')} rank={miss.get('oracle_rank')} "
            f"selected={miss.get('selected_symbol') or '空仓'} "
            f"oracle={miss.get('oracle_symbol')} {miss.get('oracle_name', '')} "
            f"({miss.get('oracle_return', 0):.2%}) "
            f"blockers={'+'.join(miss.get('oracle_blockers', []))}"
        )
    return "\n".join(lines)


def format_replacement_decoy_profile(label: str, result: dict[str, Any]) -> str:
    """Format selected-decoy diagnostics for high-return replacement misses."""
    lines = [
        f"=== 替换错选 decoy 画像: {label} ===",
        f"oracle收益阈值: {result.get('min_oracle_return', 0):.2%}",
        f"replacement miss天数: {result.get('replacement_miss_days', 0)}",
        f"replacement累计机会损失: {result.get('total_replacement_regret', 0):.2%}",
        f"平均排名差(selected-oracle): {result.get('avg_rank_delta', 0):.2f}",
    ]
    delta = result.get("decoy_minus_oracle_factor_delta", {})
    if delta:
        lines.append("decoy - oracle 因子均值差:")
        for key in (
            "F1_tail_fund_inflow",
            "F2_volume_price_sync",
            "F3_technical_pattern",
            "F4_tail_rally_strength",
            "F7_float_mv_fit",
            "F8_overnight_risk_control",
            "F9_overheat_control",
        ):
            if key in delta:
                lines.append(f"- {key}: avg={delta[key].get('avg', 0):.2f}")
    lines.append("最伤 decoy 样本:")
    for row in result.get("top_decoys", [])[:6]:
        lines.append(
            f"- {row.get('date')} regret={row.get('regret', 0):.2%} "
            f"selected={row.get('selected_symbol')} "
            f"({row.get('selected_return', 0):.2%}, rank={row.get('selected_rank')}) -> "
            f"oracle={row.get('oracle_symbol')} {row.get('oracle_name', '')} "
            f"({row.get('oracle_return', 0):.2%}, rank={row.get('oracle_rank')}) "
            f"blockers={'+'.join(row.get('oracle_blockers', []))}"
        )
    return "\n".join(lines)


def format_oracle_context_profile(label: str, result: dict[str, Any]) -> str:
    """Format cross-sectional context around high-return oracle misses."""
    lines = [
        f"=== oracle 横截面上下文: {label} ===",
        f"oracle收益阈值: {result.get('min_oracle_return', 0):.2%}",
        f"上下文样本天数: {result.get('context_days', 0)}",
        f"平均候选池大小: {result.get('avg_candidate_pool_size', 0):.2f}",
        f"oracle F1分位均值: {result.get('avg_oracle_f1_percentile', 0):.2%}",
        f"oracle F9分位均值: {result.get('avg_oracle_f9_percentile', 0):.2%}",
        f"强F1低F9候选占比均值: {result.get('avg_strong_f1_low_f9_share', 0):.2%}",
    ]
    lines.append("按强F1低F9候选占比分段:")
    for row in result.get("by_strong_low_heat_share", [])[:5]:
        lines.append(
            f"- {row.get('segment')}: days={row.get('days', 0)} "
            f"regret={row.get('total_regret', 0):.2%} "
            f"avg={row.get('avg_regret', 0):.2%} "
            f"oracle_avg={row.get('avg_oracle_return', 0):.2%}"
        )
    lines.append("上下文样本:")
    for row in result.get("top_contexts", [])[:6]:
        lines.append(
            f"- {row.get('date')} regret={row.get('regret', 0):.2%} "
            f"oracle={row.get('oracle_symbol')} {row.get('oracle_name', '')} "
            f"F1pct={row.get('oracle_f1_percentile', 0):.2%} "
            f"F9pct={row.get('oracle_f9_percentile', 0):.2%} "
            f"strong_low_heat={row.get('strong_f1_low_f9_share', 0):.2%} "
            f"pool={row.get('candidate_pool_size', 0)}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    current_config = _load_json(CONFIG_PATH)
    current_samples = [
        sample for sample in _load_json(SAMPLE_POOL_PATH).get("samples", [])
        if sample.get("sample_type") == "historical_training"
    ]
    _, validation_samples = optimizer.split_walk_forward_samples(current_samples)
    print(format_summary(
        analyze_regret(current_samples, current_config),
        analyze_blocker_combo_regret(current_samples, current_config, top_combo_count=5),
    ))
    print()
    print(format_high_return_miss_segments(
        "全样本 oracle>=5%",
        analyze_high_return_miss_segments(
            current_samples,
            current_config,
            min_oracle_return=0.05,
        ),
    ))
    print()
    print(format_replacement_decoy_profile(
        "全样本 oracle>=5%",
        analyze_replacement_decoy_profile(
            current_samples,
            current_config,
            min_oracle_return=0.05,
        ),
    ))
    print()
    print(format_oracle_context_profile(
        "全样本 oracle>=5%",
        analyze_oracle_context_profile(
            current_samples,
            current_config,
            min_oracle_return=0.05,
        ),
    ))
    f7_experiments = [
        {
            "name": "f7_empty_only_high_quality",
            "params": {
                "rescue_score_threshold": 65,
                "max_blockers": 1,
                "min_rescue_score_advantage": 0,
                "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                "rescue_min_factor_scores": {
                    "F3_technical_pattern": 75,
                    "F4_tail_rally_strength": 60,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 80,
                },
                "rescue_when_base_absent_only": True,
            },
        },
        {
            "name": "f7_empty_only_rank6_plus",
            "params": {
                "rescue_score_threshold": 65,
                "max_blockers": 1,
                "min_rescue_score_advantage": 0,
                "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                "rescue_min_factor_scores": {
                    "F3_technical_pattern": 75,
                    "F4_tail_rally_strength": 60,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 80,
                },
                "rescue_when_base_absent_only": True,
                "min_rescue_score_rank": 6,
            },
        },
        {
            "name": "f7_empty_only_f7_cap90",
            "params": {
                "rescue_score_threshold": 65,
                "max_blockers": 1,
                "min_rescue_score_advantage": 0,
                "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                "rescue_min_factor_scores": {
                    "F3_technical_pattern": 75,
                    "F4_tail_rally_strength": 60,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 80,
                },
                "rescue_max_factor_scores": {
                    "F7_float_mv_fit": 90,
                },
                "rescue_when_base_absent_only": True,
            },
        },
        {
            "name": "f7_empty_only_f1_cap80_f7_cap90",
            "params": {
                "rescue_score_threshold": 65,
                "max_blockers": 1,
                "min_rescue_score_advantage": 0,
                "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                "rescue_min_factor_scores": {
                    "F3_technical_pattern": 75,
                    "F4_tail_rally_strength": 60,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 80,
                },
                "rescue_max_factor_scores": {
                    "F1_tail_fund_inflow": 80,
                    "F7_float_mv_fit": 90,
                },
                "rescue_when_base_absent_only": True,
            },
        },
        {
            "name": "f7_empty_only_rank4_5_f7_cap90",
            "params": {
                "rescue_score_threshold": 65,
                "max_blockers": 1,
                "min_rescue_score_advantage": 0,
                "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                "rescue_min_factor_scores": {
                    "F3_technical_pattern": 75,
                    "F4_tail_rally_strength": 60,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 80,
                },
                "rescue_max_factor_scores": {
                    "F7_float_mv_fit": 90,
                },
                "rescue_when_base_absent_only": True,
                "min_rescue_score_rank": 4,
                "max_rescue_score_rank": 5,
            },
        },
        {
            "name": "f7_replace_allowed_guarded",
            "params": {
                "rescue_score_threshold": 65,
                "max_blockers": 1,
                "min_rescue_score_advantage": 0,
                "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
                "required_blocker_prefixes": ("F7_float_mv_fit>max",),
                "rescue_min_factor_scores": {
                    "F3_technical_pattern": 75,
                    "F4_tail_rally_strength": 60,
                    "F8_overnight_risk_control": 75,
                    "F9_overheat_control": 80,
                },
            },
        },
    ]
    print()
    print(format_rescue_experiment_summary(
        "F7 条件救援推广门槛",
        analyze_rescue_experiments(
            current_samples,
            current_config,
            f7_experiments,
            validation_ratio=0.3,
        ),
    ))
    f7_delta = analyze_rescue_delta(
        validation_samples,
        current_config,
        rescue_score_threshold=65,
        max_blockers=1,
        min_rescue_score_advantage=0,
        allowed_blocker_prefixes=("F7_float_mv_fit>max",),
        required_blocker_prefixes=("F7_float_mv_fit>max",),
        rescue_min_factor_scores={
            "F3_technical_pattern": 75,
            "F4_tail_rally_strength": 60,
            "F8_overnight_risk_control": 75,
            "F9_overheat_control": 80,
        },
    )
    print()
    print(format_rescue_delta_segments(
        "验证段 F7 单 blocker raw rescue",
        analyze_rescue_delta_segments(f7_delta),
    ))
    f2_f9_delta = analyze_rescue_delta(
        validation_samples,
        current_config,
        rescue_score_threshold=60,
        max_blockers=2,
        min_rescue_score_advantage=0,
        allowed_blocker_prefixes=("F2_volume_price_sync<min", "F9_overheat_control<min"),
        required_blocker_prefixes=("F2_volume_price_sync<min", "F9_overheat_control<min"),
        rescue_min_factor_scores={
            "F1_tail_fund_inflow": 80,
            "F3_technical_pattern": 75,
            "F4_tail_rally_strength": 70,
            "F8_overnight_risk_control": 70,
        },
        rescue_max_factor_scores={"F9_overheat_control": 85},
        rescue_when_base_absent_only=True,
        min_rescue_score_rank=6,
    )
    print()
    print(format_rescue_delta_segments(
        "验证段 F2+F9 rank-floor rescue",
        analyze_rescue_delta_segments(f2_f9_delta),
    ))
