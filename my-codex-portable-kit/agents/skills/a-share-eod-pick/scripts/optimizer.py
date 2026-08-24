"""
A股尾盘隔夜策略 - 策略优化器

周度执行：
1. 读取最近 N 笔已验证交易
2. 排序损失分析（各因子分 vs 收益率的 Spearman 秩相关）
3. 调整因子权重（高分相关 +，低分相关 -）
4. 回测验证改善，恶化则回滚
5. 写回 strategy_params.json + 追加 strategy_version.json
"""

import json
import math
import datetime as dt
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
try:
    from scipy.stats import spearmanr
except Exception:
    spearmanr = None

SKILL_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_ROOT / "data"
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
TRADES_PATH = DATA_DIR / "trades.json"
PERF_PATH = DATA_DIR / "performance.json"
VERSION_PATH = DATA_DIR / "strategy_version.json"
SAMPLE_POOL_PATH = DATA_DIR / "strategy_samples.json"

FACTOR_KEYS = [
    "F1_tail_fund_inflow", "F2_volume_price_sync",
    "F3_technical_pattern", "F4_tail_rally_strength",
    "F5_sector_heat", "F6_news_catalyst", "F7_float_mv_fit",
    "F8_overnight_risk_control", "F9_overheat_control",
    "F10_trend_momentum", "F11_financial_quality", "F12_market_sentiment",
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_trades() -> list[dict]:
    return _load_json(TRADES_PATH).get("trades", [])


def _load_samples() -> list[dict]:
    return _load_json(SAMPLE_POOL_PATH).get("samples", [])


# ---------------------------------------------------------------------------
# 排序损失分析
# ---------------------------------------------------------------------------

def _active_factor_keys(config: dict) -> list[str]:
    return [fk for fk, meta in (config.get("factors") or {}).items() if isinstance(meta, dict)]


def compute_factor_correlations(
    trades: list[dict],
    config: dict | None = None,
) -> dict[str, float]:
    """计算各因子分与收益率的 Spearman 秩相关系数。

    需要 trades 中包含 factor_scores 字段（选股时保存）。
    若缺失，返回全 0 并标记。
    """
    cfg = config if isinstance(config, dict) else _load_json(CONFIG_PATH)
    active_keys = _active_factor_keys(cfg)
    factor_returns = {fk: [] for fk in active_keys}
    returns = []

    for t in trades:
        fs = t.get("factor_scores", {})
        if not fs:
            continue
        for fk in active_keys:
            if fk in fs:
                factor_returns[fk].append(fs[fk])
        returns.append(t.get("return", 0))

    if len(returns) < 5:
        return {fk: 0.0 for fk in active_keys}

    correlations = {}
    for fk in active_keys:
        scores = factor_returns[fk]
        if len(scores) == len(returns) and len(scores) >= 5:
            try:
                if spearmanr is None:
                    correlations[fk] = _rank_correlation(scores, returns)
                    continue
                rho, _ = spearmanr(scores, returns)
                correlations[fk] = round(float(rho) if not np.isnan(rho) else 0, 4)
            except Exception:
                correlations[fk] = 0.0
        else:
            correlations[fk] = 0.0

    return correlations


def _rank_correlation(xs: list[float], ys: list[float]) -> float:
    """Small Spearman fallback for environments without scipy."""
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0

    def ranks(values):
        ordered = sorted(enumerate(values), key=lambda item: item[1])
        result = [0.0] * len(values)
        i = 0
        while i < len(ordered):
            j = i
            while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                result[ordered[k][0]] = avg_rank
            i = j + 1
        return result

    rx = ranks(xs)
    ry = ranks(ys)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in rx))
    den_y = math.sqrt(sum((b - my) ** 2 for b in ry))
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 4)


def compute_ranking_loss(trades: list[dict]) -> float:
    """计算理想排序(按收益率)与实际排序(按Score)的 Kendall τ 距离。

    返回归一化损失 [0, 1]，越小越好。
    """
    scored_trades = [t for t in trades if "score" in t and "return" in t]
    if len(scored_trades) < 5:
        return 1.0

    # 实际排序（按 score 降序）
    actual_order = sorted(scored_trades, key=lambda x: -x["score"])
    # 理想排序（按 return 降序）
    ideal_order = sorted(scored_trades, key=lambda x: -x["return"])

    # 构建位置映射
    actual_pos = {id(t): i for i, t in enumerate(actual_order)}
    ideal_pos = {id(t): i for i, t in enumerate(ideal_order)}

    # Kendall τ 距离
    n = len(scored_trades)
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            a_i, a_j = actual_pos[id(actual_order[i])], actual_pos[id(actual_order[j])]
            i_i, i_j = ideal_pos[id(actual_order[i])], ideal_pos[id(actual_order[j])]
            # 实际顺序与理想顺序不一致
            if (a_i - a_j) * (i_i - i_j) < 0:
                discordant += 1

    total_pairs = n * (n - 1) / 2
    loss = discordant / total_pairs if total_pairs > 0 else 1.0
    return round(loss, 4)


# ---------------------------------------------------------------------------
# 权重调整
# ---------------------------------------------------------------------------

def adjust_weights(config: dict, correlations: dict[str, float]) -> tuple[dict, dict]:
    """根据相关性调整权重，返回 (new_config, change_log)。"""
    opt = config.get("optimization", {})
    step = opt.get("adjust_step", 0.03)
    max_step = opt.get("adjust_max_step", 0.05)
    top_n = opt.get("top_factors_boost", 2)
    bottom_n = opt.get("bottom_factors_cut", 2)

    # 按相关性排序
    active_factor_keys = _active_factor_keys(config)
    sorted_factors = sorted(
        [(fk, correlations.get(fk, 0.0)) for fk in active_factor_keys],
        key=lambda x: -x[1],
    )

    old_weights = {fk: config["factors"][fk]["weight"] for fk in _active_factor_keys(config)}
    new_weights = dict(old_weights)

    changes = {}

    # 提升 top 因子
    for fk, rho in sorted_factors[:top_n]:
        delta = min(step, max_step)
        new_weights[fk] = old_weights[fk] + delta
        changes[fk] = {"delta": +delta, "rho": rho, "action": "boost"}

    # 降低 bottom 因子
    for fk, rho in sorted_factors[-bottom_n:]:
        delta = min(step, max_step)
        new_weights[fk] = old_weights[fk] - delta
        changes[fk] = {"delta": -delta, "rho": rho, "action": "cut"}

    # 归一化
    total = sum(new_weights.values())
    if total > 0:
        for fk in new_weights:
            new_weights[fk] = round(new_weights[fk] / total, 4)

    # 写回 config
    new_config = json.loads(json.dumps(config))  # deep copy
    for fk in old_weights:
        new_config["factors"][fk]["weight"] = new_weights[fk]

    change_log = {
        "old_weights": old_weights,
        "new_weights": new_weights,
        "correlations": correlations,
        "changes": changes,
    }

    return new_config, change_log


def _candidate_pool_rows(samples: list[dict]) -> list[dict]:
    rows = []
    for sample in samples:
        for candidate in sample.get("candidate_pool", []):
            if not isinstance(candidate.get("return"), (int, float)):
                continue
            fs = candidate.get("factor_scores", {})
            if not fs:
                continue
            rows.append(candidate)
    return rows


def build_learned_ranker_config(samples: list[dict], config: dict) -> tuple[dict, dict]:
    """从训练候选池的因子收益相关性反推排序权重。"""
    rows = _candidate_pool_rows(samples)
    old_weights = {
        fk: config["factors"][fk]["weight"]
        for fk in _active_factor_keys(config)
        if fk in config.get("factors", {})
    }
    if len(rows) < 4 or not old_weights:
        return json.loads(json.dumps(config)), {
            "old_weights": old_weights,
            "new_weights": old_weights,
            "correlations": {},
            "changes": {"learned_ranker": {"training_rows": len(rows), "status": "insufficient"}},
        }

    returns = [float(row.get("return", 0) or 0) for row in rows]
    correlations = {}
    for fk in old_weights:
        values = [float(row.get("factor_scores", {}).get(fk, 50) or 0) for row in rows]
        correlations[fk] = _rank_correlation(values, returns)

    positive = {fk: max(correlations.get(fk, 0), 0.0) for fk in old_weights}
    if sum(positive.values()) <= 0:
        learned = dict(old_weights)
    else:
        # Blend, rather than replace, so one noisy training window cannot dominate.
        corr_total = sum(positive.values())
        corr_weights = {fk: positive[fk] / corr_total for fk in old_weights}
        learned = {
            fk: (old_weights[fk] * 0.5) + (corr_weights[fk] * 0.5)
            for fk in old_weights
        }

    # Keep a small floor for active factors and allow negatively correlated factors to shrink.
    for fk in learned:
        if old_weights[fk] > 0:
            floor = 0.02
        else:
            floor = 0.0
        if correlations.get(fk, 0) < 0:
            learned[fk] = min(learned[fk], max(floor, old_weights[fk] * 0.5))
        learned[fk] = max(floor, learned[fk])

    total = sum(learned.values())
    new_weights = {
        fk: round(learned[fk] / total, 4)
        for fk in learned
    } if total > 0 else dict(old_weights)

    new_config = json.loads(json.dumps(config))
    for fk, weight in new_weights.items():
        new_config["factors"][fk]["weight"] = weight

    # Learned ranker should rank broadly; existing guardrails still apply unless optimizer candidates override them.
    log = {
        "old_weights": old_weights,
        "new_weights": new_weights,
        "correlations": correlations,
        "changes": {
            "learned_ranker": {
                "training_rows": len(rows),
                "method": "candidate_pool_factor_return_spearman_blend",
            },
        },
    }
    return new_config, log


def build_oracle_ranker_config(samples: list[dict], config: dict,
                               min_training_days: int = 5) -> tuple[dict, dict]:
    """Learn factor weights from each day's next-day best candidate.

    This targets opportunity loss directly: per candidate-pool day, the stock
    with the highest T close -> T+1 open return is treated as the oracle label.
    Factors that are higher on oracle candidates than on same-day peers gain
    weight; factors that are lower shrink.
    """
    old_weights = {
        fk: config["factors"][fk]["weight"]
        for fk in _active_factor_keys(config)
        if fk in config.get("factors", {})
    }
    if not old_weights:
        return json.loads(json.dumps(config)), {
            "old_weights": old_weights,
            "new_weights": old_weights,
            "correlations": {},
            "changes": {"oracle_ranker": {"training_days": 0, "status": "insufficient"}},
        }

    oracle_values = {fk: [] for fk in old_weights}
    peer_values = {fk: [] for fk in old_weights}
    training_days = 0

    for sample in samples:
        pool = [
            candidate for candidate in sample.get("candidate_pool", [])
            if isinstance(candidate.get("return"), (int, float))
            and candidate.get("factor_scores")
        ]
        if len(pool) < 2:
            continue
        oracle = max(pool, key=lambda c: float(c.get("return", 0) or 0))
        peers = [candidate for candidate in pool if candidate is not oracle]
        if not peers:
            continue
        training_days += 1
        oracle_fs = oracle.get("factor_scores", {})
        for fk in old_weights:
            oracle_values[fk].append(float(oracle_fs.get(fk, 50) or 0))
            peer_values[fk].append(
                sum(float(p.get("factor_scores", {}).get(fk, 50) or 0) for p in peers) / len(peers)
            )

    if training_days < min_training_days:
        return json.loads(json.dumps(config)), {
            "old_weights": old_weights,
            "new_weights": old_weights,
            "correlations": {},
            "changes": {
                "oracle_ranker": {
                    "training_days": training_days,
                    "min_training_days": min_training_days,
                    "status": "insufficient",
                }
            },
        }

    lifts = {}
    for fk in old_weights:
        oracle_avg = sum(oracle_values[fk]) / len(oracle_values[fk])
        peer_avg = sum(peer_values[fk]) / len(peer_values[fk])
        lifts[fk] = round((oracle_avg - peer_avg) / 100, 4)

    positive_lifts = {fk: max(lift, 0.0) for fk, lift in lifts.items()}
    if sum(positive_lifts.values()) > 0:
        lift_total = sum(positive_lifts.values())
        lift_weights = {fk: positive_lifts[fk] / lift_total for fk in old_weights}
        learned = {
            fk: old_weights[fk] * 0.35 + lift_weights[fk] * 0.65
            for fk in old_weights
        }
    else:
        learned = dict(old_weights)

    for fk, lift in lifts.items():
        if lift < 0:
            learned[fk] = min(learned[fk], max(0.0, old_weights[fk] * 0.35))
        elif old_weights[fk] > 0:
            learned[fk] = max(learned[fk], 0.02)

    total = sum(max(weight, 0.0) for weight in learned.values())
    new_weights = {
        fk: round(max(learned[fk], 0.0) / total, 4)
        for fk in learned
    } if total > 0 else dict(old_weights)

    new_config = json.loads(json.dumps(config))
    for fk, weight in new_weights.items():
        new_config["factors"][fk]["weight"] = weight

    selection = new_config.setdefault("selection", {})
    selection["score_threshold"] = min(float(selection.get("score_threshold", 60) or 60), 55.0)
    min_scores = dict(selection.get("min_factor_scores", {}))
    max_scores = dict(selection.get("max_factor_scores", {}))

    # These guards were observed to block many oracle winners; let the scorer
    # rank them instead of hard-rejecting them in this candidate configuration.
    for key in ("F2_volume_price_sync", "F8_overnight_risk_control", "F9_overheat_control"):
        min_scores.pop(key, None)
    for key in ("F1_tail_fund_inflow", "F7_float_mv_fit", "F8_overnight_risk_control"):
        max_scores.pop(key, None)
    selection["min_factor_scores"] = min_scores
    selection["max_factor_scores"] = max_scores
    selection["soft_penalties"] = {}

    log = {
        "old_weights": old_weights,
        "new_weights": new_weights,
        "correlations": {},
        "changes": {
            "oracle_ranker": {
                "training_days": training_days,
                "method": "daily_oracle_factor_lift",
                "factor_lift": lifts,
                "selection_relaxation": {
                    "removed_min": [
                        "F2_volume_price_sync",
                        "F8_overnight_risk_control",
                        "F9_overheat_control",
                    ],
                    "removed_max": [
                        "F1_tail_fund_inflow",
                        "F7_float_mv_fit",
                        "F8_overnight_risk_control",
                    ],
                },
            },
        },
    }
    return new_config, log


def build_regret_balanced_oracle_config(samples: list[dict], config: dict) -> tuple[dict, dict]:
    """Oracle-ranker variant with guardrails calibrated from oracle winners."""
    oracle_config, oracle_log = build_oracle_ranker_config(samples, config)
    if oracle_log.get("changes", {}).get("oracle_ranker", {}).get("status") == "insufficient":
        return oracle_config, {
            **oracle_log,
            "changes": {"regret_balanced_oracle": {"status": "insufficient"}},
        }

    oracle_factor_values = {fk: [] for fk in _active_factor_keys(config) if fk in oracle_config.get("factors", {})}
    for sample in samples:
        pool = [
            candidate for candidate in sample.get("candidate_pool", [])
            if isinstance(candidate.get("return"), (int, float))
            and candidate.get("factor_scores")
        ]
        if not pool:
            continue
        oracle = max(pool, key=lambda c: float(c.get("return", 0) or 0))
        fs = oracle.get("factor_scores", {})
        for fk in oracle_factor_values:
            oracle_factor_values[fk].append(float(fs.get(fk, 50) or 0))

    def percentile(values: list[float], pct: float, default: float) -> float:
        if not values:
            return default
        ordered = sorted(values)
        idx = int(round((len(ordered) - 1) * pct))
        return float(ordered[max(0, min(idx, len(ordered) - 1))])

    new_config = json.loads(json.dumps(oracle_config))
    selection = new_config.setdefault("selection", {})
    selection["score_threshold"] = min(float(selection.get("score_threshold", 60) or 60), 55.0)
    min_scores = dict(config.get("selection", {}).get("min_factor_scores", {}))
    max_scores = dict(config.get("selection", {}).get("max_factor_scores", {}))

    calibrated_mins = {}
    for fk in (
        "F2_volume_price_sync",
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F8_overnight_risk_control",
    ):
        if fk not in new_config.get("factors", {}):
            continue
        current = float(min_scores.get(fk, 0) or 0)
        oracle_floor = percentile(oracle_factor_values.get(fk, []), 0.25, current)
        if current > 0:
            calibrated_mins[fk] = int(max(0, min(current, oracle_floor)))
        elif fk in ("F3_technical_pattern", "F4_tail_rally_strength"):
            calibrated_mins[fk] = int(max(55, min(70, oracle_floor)))

    min_scores.update({k: v for k, v in calibrated_mins.items() if v > 0})
    min_scores.pop("F9_overheat_control", None)
    max_scores.pop("F8_overnight_risk_control", None)
    if "F7_float_mv_fit" in max_scores:
        max_scores["F7_float_mv_fit"] = max(
            float(max_scores["F7_float_mv_fit"]),
            percentile(oracle_factor_values.get("F7_float_mv_fit", []), 0.75, max_scores["F7_float_mv_fit"]),
        )

    selection["min_factor_scores"] = min_scores
    selection["max_factor_scores"] = max_scores
    selection["soft_penalties"] = {
        "F2_volume_price_sync": {
            "direction": "below",
            "threshold": min_scores.get("F2_volume_price_sync", 60),
            "max_penalty": 2,
        },
        "F8_overnight_risk_control": {
            "direction": "below",
            "threshold": min_scores.get("F8_overnight_risk_control", 60),
            "max_penalty": 2,
        },
    }

    log = json.loads(json.dumps(oracle_log))
    log["changes"]["regret_balanced_oracle"] = {
        "method": "daily_oracle_factor_lift_with_oracle_quantile_guardrails",
        "calibrated_min_scores": calibrated_mins,
        "removed_min": ["F9_overheat_control"],
        "removed_max": ["F8_overnight_risk_control"],
    }
    return new_config, log


def build_gated_regret_ranker_candidate(samples: list[dict], config: dict) -> dict:
    """Build the current best gated regret-ranker candidate package."""
    attack_config, log = build_regret_balanced_oracle_config(samples, config)
    return {
        "name": "gated_regret_balanced_oracle_ranker",
        "base_config": json.loads(json.dumps(config)),
        "attack_config": attack_config,
        "min_attack_score_advantage": 0,
        "attack_min_factor_scores": {
            "F8_overnight_risk_control": 75,
            "F9_overheat_control": 90,
        },
        "change_log": {
            **log,
            "changes": {
                **log.get("changes", {}),
                "gated_regret_ranker": {
                    "method": "attack_only_when_f8_f9_regime_is_strong",
                    "attack_min_factor_scores": {
                        "F8_overnight_risk_control": 75,
                        "F9_overheat_control": 90,
                    },
                    "min_attack_score_advantage": 0,
                },
            },
        },
    }


def _candidate_configs(config: dict, correlations: dict[str, float],
                       training_samples: list[dict] | None = None) -> list[tuple[str, dict, dict]]:
    """生成一组小步候选配置，交给候选池回测验证。"""
    configs = []

    weighted_config, weighted_log = adjust_weights(config, correlations)
    configs.append(("factor_correlation_weights", weighted_config, weighted_log))
    if training_samples:
        learned_config, learned_log = build_learned_ranker_config(training_samples, config)
        if learned_log.get("changes", {}).get("learned_ranker", {}).get("status") != "insufficient":
            configs.append(("learned_ranker_weights", learned_config, learned_log))
        oracle_config, oracle_log = build_oracle_ranker_config(training_samples, config)
        if oracle_log.get("changes", {}).get("oracle_ranker", {}).get("status") != "insufficient":
            configs.append(("oracle_ranker_weights", oracle_config, oracle_log))
        balanced_config, balanced_log = build_regret_balanced_oracle_config(training_samples, config)
        if balanced_log.get("changes", {}).get("regret_balanced_oracle", {}).get("status") != "insufficient":
            configs.append(("regret_balanced_oracle_ranker", balanced_config, balanced_log))

    selection = config.get("selection", {})
    score_thresholds = sorted({
        float(selection.get("score_threshold", 60)),
        55.0,
        58.0,
        60.0,
    })
    f2_thresholds = [None, 55, 60, 65, 70, 75]
    f7_caps = [None, 30, 40, 50, 60]
    f4_thresholds = [None, 50, 55, 60]

    old_weights = {fk: config["factors"][fk]["weight"] for fk in _active_factor_keys(config)}
    for score_threshold in score_thresholds:
        for f2_min in f2_thresholds:
            for f7_cap in f7_caps:
                for f4_min in f4_thresholds:
                    new_config = json.loads(json.dumps(config))
                    new_config["selection"]["score_threshold"] = score_threshold
                    min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                    max_scores = dict(new_config["selection"].get("max_factor_scores", {}))
                    if f2_min is None:
                        min_scores.pop("F2_volume_price_sync", None)
                    else:
                        min_scores["F2_volume_price_sync"] = f2_min
                    if f4_min is None:
                        min_scores.pop("F4_tail_rally_strength", None)
                    else:
                        min_scores["F4_tail_rally_strength"] = f4_min
                    if f7_cap is None:
                        max_scores.pop("F7_float_mv_fit", None)
                    else:
                        max_scores["F7_float_mv_fit"] = f7_cap
                    new_config["selection"]["min_factor_scores"] = min_scores
                    new_config["selection"]["max_factor_scores"] = max_scores

                    log = {
                        "old_weights": old_weights,
                        "new_weights": old_weights,
                        "correlations": correlations,
                        "changes": {
                            "score_threshold": {
                                "before": selection.get("score_threshold", 60),
                                "after": score_threshold,
                            },
                            "F2_volume_price_sync_min": {
                                "before": selection.get("min_factor_scores", {}).get("F2_volume_price_sync"),
                                "after": f2_min,
                            },
                            "F4_tail_rally_strength_min": {
                                "before": selection.get("min_factor_scores", {}).get("F4_tail_rally_strength"),
                                "after": f4_min,
                            },
                            "F7_float_mv_fit_max": {
                                "before": selection.get("max_factor_scores", {}).get("F7_float_mv_fit"),
                                "after": f7_cap,
                            },
                        },
                    }
                    name = (
                        f"selection_rules_score{score_threshold}_"
                        f"f2{f2_min}_f4{f4_min}_f7{f7_cap}"
                    )
                    configs.append((name, new_config, log))

    soft_penalty_sets = [
        {
            "F2_volume_price_sync": {
                "direction": "below",
                "threshold": 70,
                "max_penalty": 3,
            },
            "F4_tail_rally_strength": {
                "direction": "below",
                "threshold": 55,
                "max_penalty": 2,
            },
            "F7_float_mv_fit": {
                "direction": "above",
                "threshold": 40,
                "max_penalty": 3,
            },
        },
        {
            "F2_volume_price_sync": {
                "direction": "below",
                "threshold": 65,
                "max_penalty": 4,
            },
            "F4_tail_rally_strength": {
                "direction": "below",
                "threshold": 55,
                "max_penalty": 3,
            },
            "F7_float_mv_fit": {
                "direction": "above",
                "threshold": 50,
                "max_penalty": 4,
            },
        },
        {
            "F1_tail_fund_inflow": {
                "direction": "above",
                "threshold": 92,
                "max_penalty": 3,
            },
            "F2_volume_price_sync": {
                "direction": "below",
                "threshold": 60,
                "max_penalty": 4,
            },
            "F4_tail_rally_strength": {
                "direction": "above",
                "threshold": 85,
                "max_penalty": 4,
            },
            "F7_float_mv_fit": {
                "direction": "above",
                "threshold": 60,
                "max_penalty": 4,
            },
        },
    ]
    for score_threshold in score_thresholds:
        for i, penalties in enumerate(soft_penalty_sets, 1):
            new_config = json.loads(json.dumps(config))
            new_config["selection"]["score_threshold"] = score_threshold
            new_config["selection"]["min_factor_scores"] = {}
            new_config["selection"]["max_factor_scores"] = {}
            new_config["selection"]["soft_penalties"] = penalties
            log = {
                "old_weights": old_weights,
                "new_weights": old_weights,
                "correlations": correlations,
                "changes": {
                    "score_threshold": {
                        "before": selection.get("score_threshold", 60),
                        "after": score_threshold,
                    },
                    "soft_penalties": {
                        "before": selection.get("soft_penalties", {}),
                        "after": penalties,
                    },
                },
            }
            configs.append((f"soft_penalty_set{i}_score{score_threshold}", new_config, log))

    participation_recovery_sets = [
        {
            "score_threshold": 52.0,
            "soft_f2": 65,
            "soft_f4": 65,
            "f3_min": 70,
            "f8_min": 65,
            "f9_min": 80,
            "soft_f7": 60,
        },
        {
            "score_threshold": 55.0,
            "soft_f2": 65,
            "soft_f4": 65,
            "f3_min": 70,
            "f8_min": 70,
            "f9_min": 80,
            "soft_f7": 60,
        },
        {
            "score_threshold": 55.0,
            "soft_f2": 60,
            "soft_f4": 60,
            "f3_min": 65,
            "f8_min": 65,
            "f9_min": 80,
            "soft_f7": 70,
        },
    ]
    for i, recovery in enumerate(participation_recovery_sets, 1):
        new_config = json.loads(json.dumps(config))
        new_config["selection"]["score_threshold"] = recovery["score_threshold"]
        min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
        max_scores = dict(new_config["selection"].get("max_factor_scores", {}))
        min_scores.pop("F2_volume_price_sync", None)
        min_scores.pop("F4_tail_rally_strength", None)
        if "F3_technical_pattern" in new_config.get("factors", {}):
            min_scores["F3_technical_pattern"] = recovery["f3_min"]
        if "F8_overnight_risk_control" in new_config.get("factors", {}):
            min_scores["F8_overnight_risk_control"] = recovery["f8_min"]
            max_scores.pop("F8_overnight_risk_control", None)
        if "F9_overheat_control" in new_config.get("factors", {}):
            min_scores["F9_overheat_control"] = recovery["f9_min"]
        max_scores.pop("F7_float_mv_fit", None)
        penalties = dict(new_config["selection"].get("soft_penalties", {}))
        penalties["F2_volume_price_sync"] = {
            "direction": "below",
            "threshold": recovery["soft_f2"],
            "max_penalty": 5,
        }
        penalties["F4_tail_rally_strength"] = {
            "direction": "below",
            "threshold": recovery["soft_f4"],
            "max_penalty": 5,
        }
        penalties["F1_tail_fund_inflow"] = {
            "direction": "above",
            "threshold": 92,
            "max_penalty": 3,
        }
        penalties["F7_float_mv_fit"] = {
            "direction": "above",
            "threshold": recovery["soft_f7"],
            "max_penalty": 5,
        }
        new_config["selection"]["min_factor_scores"] = min_scores
        new_config["selection"]["max_factor_scores"] = max_scores
        new_config["selection"]["soft_penalties"] = penalties
        log = {
            "old_weights": old_weights,
            "new_weights": old_weights,
            "correlations": correlations,
            "changes": {
                "participation_recovery": {
                    "before": {
                        "score_threshold": selection.get("score_threshold", 60),
                        "min_factor_scores": selection.get("min_factor_scores", {}),
                        "max_factor_scores": selection.get("max_factor_scores", {}),
                    },
                    "after": {
                        "score_threshold": new_config["selection"]["score_threshold"],
                        "min_factor_scores": min_scores,
                        "max_factor_scores": max_scores,
                        "soft_penalties": penalties,
                    },
                },
            },
        }
        configs.append((f"participation_recovery_soft_guards_{i}", new_config, log))

    if "F8_overnight_risk_control" in config.get("factors", {}):
        for score_threshold in score_thresholds:
            for f8_min in [45, 55, 65, 75, 78, 80]:
                new_config = json.loads(json.dumps(config))
                new_config["selection"]["score_threshold"] = score_threshold
                min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                min_scores["F8_overnight_risk_control"] = f8_min
                new_config["selection"]["min_factor_scores"] = min_scores
                log = {
                    "old_weights": old_weights,
                    "new_weights": old_weights,
                    "correlations": correlations,
                    "changes": {
                        "score_threshold": {
                            "before": selection.get("score_threshold", 60),
                            "after": score_threshold,
                        },
                        "F8_overnight_risk_control_min": {
                            "before": selection.get("min_factor_scores", {}).get("F8_overnight_risk_control"),
                            "after": f8_min,
                        },
                    },
                }
                configs.append((f"overnight_risk_guard_score{score_threshold}_f8{f8_min}", new_config, log))

            for max_penalty in [4, 7, 10]:
                new_config = json.loads(json.dumps(config))
                new_config["selection"]["score_threshold"] = score_threshold
                penalties = dict(new_config["selection"].get("soft_penalties", {}))
                penalties["F8_overnight_risk_control"] = {
                    "direction": "below",
                    "threshold": 65,
                    "max_penalty": max_penalty,
                }
                new_config["selection"]["soft_penalties"] = penalties
                log = {
                    "old_weights": old_weights,
                    "new_weights": old_weights,
                    "correlations": correlations,
                    "changes": {
                        "score_threshold": {
                            "before": selection.get("score_threshold", 60),
                            "after": score_threshold,
                        },
                        "F8_overnight_risk_control_penalty": {
                            "before": selection.get("soft_penalties", {}).get("F8_overnight_risk_control"),
                            "after": penalties["F8_overnight_risk_control"],
                        },
                    },
                }
                configs.append((f"overnight_risk_penalty_score{score_threshold}_p{max_penalty}", new_config, log))

        for score_threshold in score_thresholds:
            for f2_min in [70, 75]:
                for f7_cap in [30, 40]:
                    for f8_min in [65, 70]:
                        new_config = json.loads(json.dumps(config))
                        new_config["selection"]["score_threshold"] = score_threshold
                        min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                        max_scores = dict(new_config["selection"].get("max_factor_scores", {}))
                        min_scores["F2_volume_price_sync"] = f2_min
                        min_scores["F8_overnight_risk_control"] = f8_min
                        max_scores["F7_float_mv_fit"] = f7_cap
                        new_config["selection"]["min_factor_scores"] = min_scores
                        new_config["selection"]["max_factor_scores"] = max_scores
                        log = {
                            "old_weights": old_weights,
                            "new_weights": old_weights,
                            "correlations": correlations,
                            "changes": {
                                "score_threshold": {
                                    "before": selection.get("score_threshold", 60),
                                    "after": score_threshold,
                                },
                                "F2_volume_price_sync_min": {
                                    "before": selection.get("min_factor_scores", {}).get("F2_volume_price_sync"),
                                    "after": f2_min,
                                },
                                "F7_float_mv_fit_max": {
                                    "before": selection.get("max_factor_scores", {}).get("F7_float_mv_fit"),
                                    "after": f7_cap,
                                },
                                "F8_overnight_risk_control_min": {
                                    "before": selection.get("min_factor_scores", {}).get("F8_overnight_risk_control"),
                                    "after": f8_min,
                                },
                            },
                        }
                        configs.append(
                            (
                                f"high_confidence_f2{f2_min}_f7{f7_cap}_f8{f8_min}_score{score_threshold}",
                                new_config,
                                log,
                            )
                        )

        if "F3_technical_pattern" in config.get("factors", {}):
            for score_threshold in score_thresholds:
                for f3_min in [70, 75, 80]:
                    new_config = json.loads(json.dumps(config))
                    new_config["selection"]["score_threshold"] = score_threshold
                    min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                    min_scores["F3_technical_pattern"] = f3_min
                    new_config["selection"]["min_factor_scores"] = min_scores
                    log = {
                        "old_weights": old_weights,
                        "new_weights": old_weights,
                        "correlations": correlations,
                        "changes": {
                            "score_threshold": {
                                "before": selection.get("score_threshold", 60),
                                "after": score_threshold,
                            },
                            "F3_technical_pattern_min": {
                                "before": selection.get("min_factor_scores", {}).get("F3_technical_pattern"),
                                "after": f3_min,
                            },
                        },
                    }
                    configs.append(
                        (
                            f"technical_confirmation_f3{f3_min}_score{score_threshold}",
                            new_config,
                            log,
                        )
                    )

        if "F9_overheat_control" in config.get("factors", {}):
            for f9_min in [75, 80, 85]:
                new_config = json.loads(json.dumps(config))
                min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                min_scores["F9_overheat_control"] = f9_min
                new_config["selection"]["min_factor_scores"] = min_scores
                log = {
                    "old_weights": old_weights,
                    "new_weights": old_weights,
                    "correlations": correlations,
                    "changes": {
                        "F9_overheat_control_min": {
                            "before": selection.get("min_factor_scores", {}).get("F9_overheat_control"),
                            "after": f9_min,
                        },
                    },
                }
                configs.append((f"overheat_control_f9{f9_min}", new_config, log))

        if "F9_overheat_control" in config.get("factors", {}):
            for f1_cap in [88, 90, 92]:
                for f8_cap in [88, 90, 92]:
                    for f4_min in [65, 70, 75]:
                        new_config = json.loads(json.dumps(config))
                        min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                        max_scores = dict(new_config["selection"].get("max_factor_scores", {}))
                        min_scores["F2_volume_price_sync"] = 75
                        min_scores["F4_tail_rally_strength"] = f4_min
                        max_scores["F1_tail_fund_inflow"] = f1_cap
                        max_scores["F8_overnight_risk_control"] = f8_cap
                        new_config["selection"]["min_factor_scores"] = min_scores
                        new_config["selection"]["max_factor_scores"] = max_scores
                        log = {
                            "old_weights": old_weights,
                            "new_weights": old_weights,
                            "correlations": correlations,
                            "changes": {
                                "F2_volume_price_sync_min": {
                                    "before": selection.get("min_factor_scores", {}).get("F2_volume_price_sync"),
                                    "after": 75,
                                },
                                "F4_tail_rally_strength_min": {
                                    "before": selection.get("min_factor_scores", {}).get("F4_tail_rally_strength"),
                                    "after": f4_min,
                                },
                                "F1_tail_fund_inflow_max": {
                                    "before": selection.get("max_factor_scores", {}).get("F1_tail_fund_inflow"),
                                    "after": f1_cap,
                                },
                                "F8_overnight_risk_control_max": {
                                    "before": selection.get("max_factor_scores", {}).get("F8_overnight_risk_control"),
                                    "after": f8_cap,
                                },
                            },
                        }
                        configs.append(
                            (
                                f"fund_risk_upper_caps_f1{f1_cap}_f8{f8_cap}_f4{f4_min}",
                                new_config,
                                log,
                            )
                        )

        if "F9_overheat_control" in config.get("factors", {}):
            for f2_min in [70, 72, 75]:
                for f4_min in [70, 72, 75]:
                    for f7_cap in [40, 50, 60]:
                        new_config = json.loads(json.dumps(config))
                        min_scores = dict(new_config["selection"].get("min_factor_scores", {}))
                        max_scores = dict(new_config["selection"].get("max_factor_scores", {}))
                        min_scores["F2_volume_price_sync"] = f2_min
                        min_scores["F4_tail_rally_strength"] = f4_min
                        min_scores["F3_technical_pattern"] = 70
                        min_scores["F8_overnight_risk_control"] = max(
                            70,
                            int(min_scores.get("F8_overnight_risk_control", 70)),
                        )
                        min_scores["F9_overheat_control"] = max(
                            85,
                            int(min_scores.get("F9_overheat_control", 85)),
                        )
                        max_scores["F7_float_mv_fit"] = f7_cap
                        max_scores["F1_tail_fund_inflow"] = 90
                        max_scores["F8_overnight_risk_control"] = 90
                        new_config["selection"]["min_factor_scores"] = min_scores
                        new_config["selection"]["max_factor_scores"] = max_scores
                        log = {
                            "old_weights": old_weights,
                            "new_weights": old_weights,
                            "correlations": correlations,
                            "changes": {
                                "controlled_participation_recovery": {
                                    "before": {
                                        "min_factor_scores": selection.get("min_factor_scores", {}),
                                        "max_factor_scores": selection.get("max_factor_scores", {}),
                                    },
                                    "after": {
                                        "min_factor_scores": min_scores,
                                        "max_factor_scores": max_scores,
                                    },
                                },
                            },
                        }
                        configs.append(
                            (
                                f"controlled_participation_f2{f2_min}_f4{f4_min}_f7{f7_cap}",
                                new_config,
                                log,
                            )
                        )

    return configs


# ---------------------------------------------------------------------------
# 回测验证
# ---------------------------------------------------------------------------

def backtest_with_weights(trades: list[dict], config: dict) -> float:
    """用新权重回测最近交易，返回胜率。

    需要 trades 中有 factor_scores。
    """
    scored = [t for t in trades if "factor_scores" in t and "return" in t]
    if len(scored) < 5:
        return 0.0

    weights = {fk: config["factors"][fk]["weight"] for fk in _active_factor_keys(config) if fk in config.get("factors", {})}

    wins = 0
    for t in scored:
        fs = t["factor_scores"]
        new_score = sum(weights[fk] * fs.get(fk, 50) for fk in weights)
        # 简化：用新分数是否 > 60 且实际 return > 0 判定一致性
        if (new_score >= config["selection"]["score_threshold"]) == (t["return"] > 0):
            wins += 1

    return wins / len(scored)


def _score_candidate(candidate: dict, config: dict) -> float:
    weights = {fk: config["factors"][fk]["weight"] for fk in _active_factor_keys(config) if fk in config.get("factors", {})}
    fs = candidate.get("factor_scores", {})
    raw_score = sum(weights[fk] * float(fs.get(fk, 50) or 0) for fk in weights)
    penalty = _soft_penalty(fs, config)
    return round(raw_score - penalty, 4)


def _soft_penalty(factor_scores: dict, config: dict) -> float:
    """Apply configurable score penalties without hard-rejecting a candidate."""
    penalty = 0.0
    for key, rule in config.get("selection", {}).get("soft_penalties", {}).items():
        if not isinstance(rule, dict):
            continue
        value = float(factor_scores.get(key, 0) or 0)
        threshold = float(rule.get("threshold", 0) or 0)
        max_penalty = float(rule.get("max_penalty", 0) or 0)
        direction = rule.get("direction")
        if max_penalty <= 0:
            continue
        if direction == "below" and threshold > 0 and value < threshold:
            penalty += min(max_penalty, (threshold - value) / threshold * max_penalty)
        elif direction == "above" and threshold < 100 and value > threshold:
            denominator = max(100 - threshold, 1)
            penalty += min(max_penalty, (value - threshold) / denominator * max_penalty)
    return round(penalty, 4)


def _passes_selection(candidate: dict, config: dict) -> bool:
    selection = config.get("selection", {})
    score = candidate.get("_new_score", candidate.get("score", 0))
    if float(score or 0) < float(selection.get("score_threshold", 60)):
        return False
    fs = candidate.get("factor_scores", {})
    for key, min_value in selection.get("min_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) < float(min_value):
            return False
    for key, max_value in selection.get("max_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) > float(max_value):
            return False
    return True


def _base_pick_from_candidate_pool(sample: dict, config: dict) -> Optional[dict]:
    candidates = []
    for raw in sample.get("candidate_pool", []):
        if not isinstance(raw.get("return"), (int, float)):
            continue
        item = dict(raw)
        item["_new_score"] = _score_candidate(item, config)
        if _passes_selection(item, config):
            candidates.append(item)
    if not candidates:
        return None
    candidates.sort(
        key=lambda x: (
            -x.get("_new_score", 0),
            -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
            -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
        )
    )
    candidates[0]["_selection_mode"] = "base"
    return candidates[0]


def pick_from_candidate_pool(sample: dict, config: dict) -> Optional[dict]:
    """按新配置从某日候选池重新选择唯一 Top1。"""
    base_pick = _base_pick_from_candidate_pool(sample, config)
    rescue_config = config.get("selection", {}).get("counterfactual_rescue", {})
    if not rescue_config or not rescue_config.get("enabled"):
        return base_pick

    rescue_pick = _pick_counterfactual_rescue_candidate(
        sample,
        config,
        rescue_score_threshold=float(rescue_config.get("rescue_score_threshold", 80) or 80),
        max_blockers=int(rescue_config.get("max_blockers", 3) or 3),
        allowed_blocker_prefixes=tuple(rescue_config.get("allowed_blocker_prefixes", ()) or ()),
        required_blocker_prefixes=tuple(rescue_config.get("required_blocker_prefixes", ()) or ()),
        rescue_min_factor_scores=rescue_config.get("rescue_min_factor_scores", {}),
        rescue_max_factor_scores=rescue_config.get("rescue_max_factor_scores", {}),
    )
    if rescue_pick is None:
        return base_pick
    if base_pick is not None and rescue_config.get("rescue_when_base_absent_only"):
        return base_pick
    if base_pick is None and rescue_config.get("rescue_when_base_present_only"):
        return None

    if rescue_config.get("max_rescue_score_rank") is not None:
        ranked_candidates = []
        for raw in sample.get("candidate_pool", []):
            if not isinstance(raw.get("return"), (int, float)):
                continue
            item = dict(raw)
            item["_new_score"] = _score_candidate(item, config)
            ranked_candidates.append(item)
        ranked_candidates.sort(
            key=lambda x: (
                -x.get("_new_score", 0),
                -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
                -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
            )
        )
        rescue_rank = next(
            (
                index
                for index, item in enumerate(ranked_candidates, start=1)
                if item.get("symbol") == rescue_pick.get("symbol")
            ),
            None,
        )
        if rescue_rank is None or rescue_rank > int(rescue_config.get("max_rescue_score_rank")):
            return base_pick

    if base_pick is None:
        rescue_pick["_selection_mode"] = "rescue"
        return rescue_pick
    rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
    base_score = float(base_pick.get("_new_score", 0) or 0)
    min_advantage = float(rescue_config.get("min_rescue_score_advantage", 12) or 0)
    max_advantage = rescue_config.get("max_rescue_score_advantage")
    score_advantage = rescue_score - base_score
    max_advantage_ok = (
        max_advantage is None
        or score_advantage <= float(max_advantage)
    )
    if score_advantage >= min_advantage and max_advantage_ok:
        rescue_pick["_selection_mode"] = "rescue"
        return rescue_pick
    return base_pick


def _rank_rescue_pick(sample: dict, config: dict, rescue_pick: dict,
                      max_rescue_score_rank: int | None) -> Optional[int]:
    if max_rescue_score_rank is None:
        return None
    ranked_candidates = []
    for raw in sample.get("candidate_pool", []):
        if not isinstance(raw.get("return"), (int, float)):
            continue
        item = dict(raw)
        item["_new_score"] = _score_candidate(item, config)
        ranked_candidates.append(item)
    ranked_candidates.sort(
        key=lambda x: (
            -x.get("_new_score", 0),
            -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
            -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
        )
    )
    rescue_rank = next(
        (
            index
            for index, item in enumerate(ranked_candidates, start=1)
            if item.get("symbol") == rescue_pick.get("symbol")
        ),
        None,
    )
    rescue_pick["_rescue_score_rank"] = rescue_rank
    if rescue_rank is None or rescue_rank > int(max_rescue_score_rank):
        return None
    return rescue_rank


def _rescue_rank_allowed(
    rescue_rank: int | None,
    min_rescue_score_rank: int | None = None,
    max_rescue_score_rank: int | None = None,
) -> bool:
    if rescue_rank is None:
        return False
    if min_rescue_score_rank is not None and rescue_rank < int(min_rescue_score_rank):
        return False
    if max_rescue_score_rank is not None and rescue_rank > int(max_rescue_score_rank):
        return False
    return True


def _pick_neighbor_counterfactual_rescue_candidate(
    sample: dict,
    base_config: dict,
    rescue_config: dict,
    segment_history: dict[tuple[str, ...], list[dict]],
) -> Optional[dict]:
    if not rescue_config or not rescue_config.get("enabled"):
        return None

    base_pick = _base_pick_from_candidate_pool(sample, base_config)
    rescue_pick = _pick_counterfactual_rescue_candidate(
        sample,
        base_config,
        rescue_score_threshold=float(rescue_config.get("rescue_score_threshold", 68) or 68),
        max_blockers=int(rescue_config.get("max_blockers", 3) or 3),
        allowed_blocker_prefixes=tuple(rescue_config.get("allowed_blocker_prefixes", ()) or ()),
        required_blocker_prefixes=tuple(rescue_config.get("required_blocker_prefixes", ()) or ()),
        rescue_min_factor_scores=rescue_config.get("rescue_min_factor_scores", {}),
        rescue_max_factor_scores=rescue_config.get("rescue_max_factor_scores", {}),
    )
    if rescue_pick is None:
        return base_pick

    min_rank = rescue_config.get("min_rescue_score_rank")
    max_rank = rescue_config.get("max_rescue_score_rank")
    if min_rank is not None or max_rank is not None:
        rescue_rank = _rank_rescue_pick(sample, base_config, rescue_pick, None)
        if not _rescue_rank_allowed(rescue_rank, min_rank, max_rank):
            return base_pick

    blockers = tuple(rescue_pick.get("_rescue_blockers", ()))
    history = segment_history.get(blockers, [])
    neighbor_factor_keys = tuple(rescue_config.get("neighbor_factor_keys", ()) or (
        "F1_tail_fund_inflow",
        "F2_volume_price_sync",
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F7_float_mv_fit",
        "F8_overnight_risk_control",
        "F9_overheat_control",
    ))
    neighbors = sorted(
        history,
        key=lambda item: _candidate_factor_distance(
            rescue_pick,
            item,
            neighbor_factor_keys,
        ),
    )[:int(rescue_config.get("nearest_neighbor_count", 5) or 5)]

    neighbor_ok = False
    min_prior_neighbors = int(rescue_config.get("min_prior_neighbors", 3) or 3)
    if len(neighbors) >= min_prior_neighbors:
        neighbor_returns = [float(item.get("return", 0) or 0) for item in neighbors]
        win_rate = sum(1 for value in neighbor_returns if value > 0) / len(neighbor_returns)
        avg_return = sum(neighbor_returns) / len(neighbor_returns)
        neighbor_ok = (
            win_rate >= float(rescue_config.get("min_neighbor_win_rate", 0.7) or 0)
            and avg_return >= float(rescue_config.get("min_neighbor_avg_return", 0) or 0)
        )

    segment_history.setdefault(blockers, []).append(rescue_pick)

    if base_pick is None:
        if rescue_config.get("rescue_when_base_present_only"):
            return None
        if neighbor_ok:
            rescue_pick["_selection_mode"] = "neighbor_rescue"
            return rescue_pick
        return None
    if rescue_config.get("rescue_when_base_absent_only"):
        return base_pick

    rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
    base_score = float(base_pick.get("_new_score", 0) or 0)
    score_advantage = rescue_score - base_score
    max_advantage = rescue_config.get("max_rescue_score_advantage")
    max_advantage_ok = (
        max_advantage is None
        or score_advantage <= float(max_advantage)
    )
    if (
        neighbor_ok
        and score_advantage >= float(rescue_config.get("min_rescue_score_advantage", 5) or 0)
        and max_advantage_ok
    ):
        rescue_pick["_selection_mode"] = "neighbor_rescue"
        return rescue_pick
    return base_pick


def backtest_candidate_pool(samples: list[dict], config: dict) -> dict:
    """用候选池按新策略每日重选 Top1，并计算纸面胜率。"""
    picks = []
    empty_days = 0
    oracle_returns = []
    regrets = []
    exact_best_hits = 0
    top3_hits = 0
    neighbor_rescue_config = config.get("selection", {}).get("neighbor_counterfactual_rescue", {})
    neighbor_segment_history: dict[tuple[str, ...], list[dict]] = {}
    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        if not sample.get("candidate_pool"):
            continue
        valid_candidates = [
            c for c in sample.get("candidate_pool", [])
            if isinstance(c.get("return"), (int, float))
        ]
        if not valid_candidates:
            continue
        oracle = max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))
        oracle_return = float(oracle.get("return", 0) or 0)
        oracle_returns.append(oracle_return)
        if neighbor_rescue_config and neighbor_rescue_config.get("enabled"):
            pick = _pick_neighbor_counterfactual_rescue_candidate(
                sample,
                config,
                neighbor_rescue_config,
                neighbor_segment_history,
            )
        else:
            pick = pick_from_candidate_pool(sample, config)
        if pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue
        pick_return = float(pick.get("return", 0) or 0)
        if pick.get("symbol") == oracle.get("symbol"):
            exact_best_hits += 1
        top_symbols = {
            item.get("symbol")
            for item in sorted(valid_candidates, key=lambda c: float(c.get("return", 0) or 0), reverse=True)[:3]
        }
        if pick.get("symbol") in top_symbols:
            top3_hits += 1
        regrets.append(max(0.0, oracle_return - pick_return))
        picks.append({
            "date": sample.get("date", ""),
            "symbol": pick.get("symbol", ""),
            "score": pick.get("_new_score", 0),
            "return": pick_return,
            "win": pick_return > 0,
            "mode": pick.get("_selection_mode", "base"),
        })

    wins = [p for p in picks if p.get("win")]
    returns = [float(p.get("return", 0) or 0) for p in picks]
    max_consec = 0
    cur = 0
    for p in picks:
        if p.get("win"):
            cur = 0
        else:
            cur += 1
            max_consec = max(max_consec, cur)
    return {
        "samples": len(picks) + empty_days,
        "trade_samples": len(picks),
        "empty_days": empty_days,
        "win_rate": round(len(wins) / len(picks), 4) if picks else 0,
        "avg_return": round(sum(returns) / len(returns), 4) if returns else 0,
        "total_return": round(sum(returns), 4),
        "max_consecutive_loss": max_consec,
        "avg_regret": round(sum(regrets) / len(regrets), 4) if regrets else 0,
        "total_regret": round(sum(regrets), 4),
        "exact_best_hit_rate": round(exact_best_hits / len(regrets), 4) if regrets else 0,
        "top3_hit_rate": round(top3_hits / len(regrets), 4) if regrets else 0,
        "avg_oracle_return": round(sum(oracle_returns) / len(oracle_returns), 4) if oracle_returns else 0,
        "picks": picks,
    }


def _summarize_picks_with_oracle(picks: list[dict], empty_days: int,
                                 oracle_returns: list[float],
                                 regrets: list[float],
                                 exact_best_hits: int,
                                 top3_hits: int = 0) -> dict:
    wins = [p for p in picks if p.get("win")]
    returns = [float(p.get("return", 0) or 0) for p in picks]
    max_consec = 0
    cur = 0
    for p in picks:
        if p.get("win"):
            cur = 0
        else:
            cur += 1
            max_consec = max(max_consec, cur)
    return {
        "samples": len(picks) + empty_days,
        "trade_samples": len(picks),
        "empty_days": empty_days,
        "win_rate": round(len(wins) / len(picks), 4) if picks else 0,
        "avg_return": round(sum(returns) / len(returns), 4) if returns else 0,
        "total_return": round(sum(returns), 4),
        "max_consecutive_loss": max_consec,
        "avg_regret": round(sum(regrets) / len(regrets), 4) if regrets else 0,
        "total_regret": round(sum(regrets), 4),
        "exact_best_hit_rate": round(exact_best_hits / len(regrets), 4) if regrets else 0,
        "top3_hit_rate": round(top3_hits / len(regrets), 4) if regrets else 0,
        "avg_oracle_return": round(sum(oracle_returns) / len(oracle_returns), 4) if oracle_returns else 0,
        "picks": picks,
    }


def backtest_gated_candidate_pool(samples: list[dict], base_config: dict,
                                  attack_config: dict,
                                  min_attack_score_advantage: float = 5.0,
                                  attack_min_factor_scores: dict | None = None) -> dict:
    """Use attack pick only when its score advantage over base is large enough."""
    picks = []
    empty_days = 0
    oracle_returns = []
    regrets = []
    exact_best_hits = 0

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            c for c in sample.get("candidate_pool", [])
            if isinstance(c.get("return"), (int, float))
        ]
        if not valid_candidates:
            continue
        oracle = max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))
        oracle_return = float(oracle.get("return", 0) or 0)
        oracle_returns.append(oracle_return)

        base_pick = pick_from_candidate_pool(sample, base_config)
        attack_pick = pick_from_candidate_pool(sample, attack_config)
        if base_pick is None and attack_pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue

        mode = "base"
        pick = base_pick
        if attack_pick is not None:
            attack_fs = attack_pick.get("factor_scores", {})
            attack_factors_ok = all(
                float(attack_fs.get(key, 0) or 0) >= float(value)
                for key, value in (attack_min_factor_scores or {}).items()
            )
            if base_pick is None:
                if attack_factors_ok:
                    pick = attack_pick
                    mode = "attack"
            else:
                attack_score = float(attack_pick.get("_new_score", 0) or 0)
                base_score = float(base_pick.get("_new_score", 0) or 0)
                if attack_factors_ok and attack_score - base_score >= min_attack_score_advantage:
                    pick = attack_pick
                    mode = "attack"

        if pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue

        pick_return = float(pick.get("return", 0) or 0)
        if pick.get("symbol") == oracle.get("symbol"):
            exact_best_hits += 1
        regrets.append(max(0.0, oracle_return - pick_return))
        picks.append({
            "date": sample.get("date", ""),
            "symbol": pick.get("symbol", ""),
            "score": pick.get("_new_score", 0),
            "return": pick_return,
            "win": pick_return > 0,
            "mode": mode,
        })

    return _summarize_picks_with_oracle(picks, empty_days, oracle_returns, regrets, exact_best_hits)


def _selection_blockers(candidate: dict, config: dict) -> list[str]:
    """Return hard selection rules blocking a scored candidate."""
    blockers = []
    selection = config.get("selection", {})
    score = float(candidate.get("_new_score", candidate.get("score", 0)) or 0)
    threshold = float(selection.get("score_threshold", 60) or 60)
    if score < threshold:
        blockers.append("score<threshold")
    fs = candidate.get("factor_scores", {})
    for key, min_value in selection.get("min_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) < float(min_value):
            blockers.append(f"{key}<min")
    for key, max_value in selection.get("max_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) > float(max_value):
            blockers.append(f"{key}>max")
    return blockers


def _pick_counterfactual_rescue_candidate(sample: dict, base_config: dict,
                                          rescue_score_threshold: float = 68.0,
                                          max_blockers: int = 3,
                                          allowed_blocker_prefixes: tuple[str, ...] | None = None,
                                          required_blocker_prefixes: tuple[str, ...] | None = None,
                                          rescue_min_factor_scores: dict | None = None,
                                          rescue_max_factor_scores: dict | None = None) -> Optional[dict]:
    allowed_prefixes = allowed_blocker_prefixes or (
        "F1_tail_fund_inflow>max",
        "F2_volume_price_sync<min",
        "F3_technical_pattern<min",
        "F7_float_mv_fit>max",
        "F8_overnight_risk_control<min",
        "F8_overnight_risk_control>max",
        "F9_overheat_control<min",
    )
    rescue_candidates = []
    for raw in sample.get("candidate_pool", []):
        if not isinstance(raw.get("return"), (int, float)):
            continue
        item = dict(raw)
        item["_new_score"] = _score_candidate(item, base_config)
        if _passes_selection(item, base_config):
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
        blockers = _selection_blockers(item, base_config)
        hard_blockers = [b for b in blockers if b != "score<threshold"]
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
        item["_rescue_blockers"] = hard_blockers
        rescue_candidates.append(item)

    rescue_candidates.sort(
        key=lambda x: (
            -x.get("_new_score", 0),
            len(x.get("_rescue_blockers", [])),
            -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
            -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
        )
    )
    return rescue_candidates[0] if rescue_candidates else None


def backtest_counterfactual_rescue_pool(samples: list[dict], base_config: dict,
                                        rescue_score_threshold: float = 68.0,
                                        max_blockers: int = 3,
                                        min_rescue_score_advantage: float = 5.0,
                                        max_rescue_score_advantage: float | None = None,
                                        allowed_blocker_prefixes: tuple[str, ...] | None = None,
                                        required_blocker_prefixes: tuple[str, ...] | None = None,
                                        rescue_min_factor_scores: dict | None = None,
                                        rescue_max_factor_scores: dict | None = None,
                                        rescue_when_base_absent_only: bool = False,
                                        rescue_when_base_present_only: bool = False,
                                        min_rescue_score_rank: int | None = None,
                                        max_rescue_score_rank: int | None = None) -> dict:
    """Backtest a rescue gate for high-potential candidates blocked by hard rules."""
    picks = []
    empty_days = 0
    oracle_returns = []
    regrets = []
    exact_best_hits = 0

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            c for c in sample.get("candidate_pool", [])
            if isinstance(c.get("return"), (int, float))
        ]
        if not valid_candidates:
            continue
        oracle = max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))
        oracle_return = float(oracle.get("return", 0) or 0)
        oracle_returns.append(oracle_return)

        base_pick = _base_pick_from_candidate_pool(sample, base_config)
        scored_candidates = []
        for raw in valid_candidates:
            item = dict(raw)
            item["_new_score"] = _score_candidate(item, base_config)
            scored_candidates.append(item)
        _add_cross_section_context_features(scored_candidates)
        context_by_symbol = {
            item.get("symbol"): item.get("factor_scores", {})
            for item in scored_candidates
        }
        rescue_pick = _pick_counterfactual_rescue_candidate(
            sample,
            base_config,
            rescue_score_threshold=rescue_score_threshold,
            max_blockers=max_blockers,
            allowed_blocker_prefixes=allowed_blocker_prefixes,
            required_blocker_prefixes=required_blocker_prefixes,
            rescue_min_factor_scores=rescue_min_factor_scores,
            rescue_max_factor_scores=rescue_max_factor_scores,
        )

        mode = "base"
        pick = base_pick
        if rescue_pick is not None:
            rescue_rank_ok = True
            if min_rescue_score_rank is not None or max_rescue_score_rank is not None:
                ranked_candidates = []
                for raw in valid_candidates:
                    item = dict(raw)
                    item["_new_score"] = _score_candidate(item, base_config)
                    ranked_candidates.append(item)
                ranked_candidates.sort(
                    key=lambda x: (
                        -x.get("_new_score", 0),
                        -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
                        -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
                    )
                )
                rescue_symbol = rescue_pick.get("symbol")
                rescue_rank = next(
                    (
                        index
                        for index, item in enumerate(ranked_candidates, start=1)
                        if item.get("symbol") == rescue_symbol
                    ),
                    None,
                )
                rescue_rank_ok = _rescue_rank_allowed(
                    rescue_rank,
                    min_rescue_score_rank,
                    max_rescue_score_rank,
                )
                rescue_pick["_rescue_score_rank"] = rescue_rank
            if not rescue_rank_ok:
                rescue_pick = None

        if rescue_pick is not None:
            if base_pick is None:
                if rescue_when_base_present_only:
                    pick = None
                    mode = "base"
                else:
                    pick = rescue_pick
                    mode = "rescue"
            elif rescue_when_base_absent_only:
                pick = base_pick
                mode = "base"
            else:
                rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
                base_score = float(base_pick.get("_new_score", 0) or 0)
                score_advantage = rescue_score - base_score
                max_advantage_ok = (
                    max_rescue_score_advantage is None
                    or score_advantage <= float(max_rescue_score_advantage)
                )
                if score_advantage >= min_rescue_score_advantage and max_advantage_ok:
                    pick = rescue_pick
                    mode = "rescue"

        if pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue

        pick_return = float(pick.get("return", 0) or 0)
        if pick.get("symbol") == oracle.get("symbol"):
            exact_best_hits += 1
        regrets.append(max(0.0, oracle_return - pick_return))
        picks.append({
            "date": sample.get("date", ""),
            "symbol": pick.get("symbol", ""),
            "score": pick.get("_new_score", 0),
            "return": pick_return,
            "win": pick_return > 0,
            "mode": mode,
            "rescue_blockers": pick.get("_rescue_blockers", []) if mode == "rescue" else [],
        })

    return _summarize_picks_with_oracle(picks, empty_days, oracle_returns, regrets, exact_best_hits)


def backtest_rolling_counterfactual_rescue_pool(
    samples: list[dict],
    base_config: dict,
    rescue_score_threshold: float = 68.0,
    max_blockers: int = 3,
    min_rescue_score_advantage: float = 5.0,
    max_rescue_score_advantage: float | None = None,
    allowed_blocker_prefixes: tuple[str, ...] | None = None,
    required_blocker_prefixes: tuple[str, ...] | None = None,
    rescue_min_factor_scores: dict | None = None,
    rescue_max_factor_scores: dict | None = None,
    rescue_when_base_absent_only: bool = False,
    rescue_when_base_present_only: bool = False,
    max_rescue_score_rank: int | None = None,
    min_prior_segment_trades: int = 3,
    min_prior_segment_win_rate: float = 0.7,
    min_prior_segment_avg_return: float = 0.0,
    segment_history_window: int | None = None,
) -> dict:
    """Backtest rescue only after the same blocker segment has recent edge."""
    picks = []
    empty_days = 0
    oracle_returns = []
    regrets = []
    exact_best_hits = 0
    segment_history: dict[tuple[str, ...], list[float]] = {}

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            c for c in sample.get("candidate_pool", [])
            if isinstance(c.get("return"), (int, float))
        ]
        if not valid_candidates:
            continue
        oracle = max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))
        oracle_return = float(oracle.get("return", 0) or 0)
        oracle_returns.append(oracle_return)

        base_pick = _base_pick_from_candidate_pool(sample, base_config)
        scored_candidates = []
        for raw in valid_candidates:
            item = dict(raw)
            item["_new_score"] = _score_candidate(item, base_config)
            scored_candidates.append(item)
        _add_cross_section_context_features(scored_candidates)
        context_by_symbol = {
            item.get("symbol"): item.get("factor_scores", {})
            for item in scored_candidates
        }
        rescue_pick = _pick_counterfactual_rescue_candidate(
            sample,
            base_config,
            rescue_score_threshold=rescue_score_threshold,
            max_blockers=max_blockers,
            allowed_blocker_prefixes=allowed_blocker_prefixes,
            required_blocker_prefixes=required_blocker_prefixes,
            rescue_min_factor_scores=rescue_min_factor_scores,
            rescue_max_factor_scores=rescue_max_factor_scores,
        )

        if rescue_pick is not None and max_rescue_score_rank is not None:
            ranked_candidates = []
            for raw in valid_candidates:
                item = dict(raw)
                item["_new_score"] = _score_candidate(item, base_config)
                ranked_candidates.append(item)
            ranked_candidates.sort(
                key=lambda x: (
                    -x.get("_new_score", 0),
                    -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
                    -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
                )
            )
            rescue_rank = next(
                (
                    index
                    for index, item in enumerate(ranked_candidates, start=1)
                    if item.get("symbol") == rescue_pick.get("symbol")
                ),
                None,
            )
            rescue_pick["_rescue_score_rank"] = rescue_rank
            if rescue_rank is None or rescue_rank > int(max_rescue_score_rank):
                rescue_pick = None

        mode = "base"
        pick = base_pick
        if rescue_pick is not None:
            blockers = tuple(rescue_pick.get("_rescue_blockers", ()))
            history = segment_history.get(blockers, [])
            if segment_history_window is not None:
                history = history[-int(segment_history_window):]
            segment_ok = False
            if len(history) >= int(min_prior_segment_trades):
                wins = sum(1 for value in history if value > 0)
                win_rate = wins / len(history)
                avg_return = sum(history) / len(history)
                segment_ok = (
                    win_rate >= float(min_prior_segment_win_rate)
                    and avg_return >= float(min_prior_segment_avg_return)
                )

            if base_pick is None:
                if rescue_when_base_present_only:
                    pick = None
                    mode = "base"
                elif segment_ok:
                    pick = rescue_pick
                    mode = "rolling_rescue"
                else:
                    pick = None
                    mode = "base"
            elif rescue_when_base_absent_only:
                pick = base_pick
                mode = "base"
            else:
                rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
                base_score = float(base_pick.get("_new_score", 0) or 0)
                score_advantage = rescue_score - base_score
                max_advantage_ok = (
                    max_rescue_score_advantage is None
                    or score_advantage <= float(max_rescue_score_advantage)
                )
                if segment_ok and score_advantage >= min_rescue_score_advantage and max_advantage_ok:
                    pick = rescue_pick
                    mode = "rolling_rescue"

            segment_history.setdefault(blockers, []).append(float(rescue_pick.get("return", 0) or 0))

        if pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue

        pick_return = float(pick.get("return", 0) or 0)
        if pick.get("symbol") == oracle.get("symbol"):
            exact_best_hits += 1
        regrets.append(max(0.0, oracle_return - pick_return))
        picks.append({
            "date": sample.get("date", ""),
            "symbol": pick.get("symbol", ""),
            "score": pick.get("_new_score", 0),
            "return": pick_return,
            "win": pick_return > 0,
            "mode": mode,
            "rescue_blockers": pick.get("_rescue_blockers", []) if mode == "rolling_rescue" else [],
        })

    return _summarize_picks_with_oracle(picks, empty_days, oracle_returns, regrets, exact_best_hits)


def _candidate_factor_distance(a: dict, b: dict, factor_keys: tuple[str, ...]) -> float:
    a_fs = a.get("factor_scores", {})
    b_fs = b.get("factor_scores", {})
    if not factor_keys:
        return 0.0
    return math.sqrt(sum(
        (
            float(a_fs.get(key, 0) or 0)
            - float(b_fs.get(key, 0) or 0)
        ) ** 2
        for key in factor_keys
    ) / len(factor_keys))


def _percentile_rank(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return round(sum(1 for item in values if item <= value) / len(values) * 100, 4)


def _add_cross_section_context_features(candidates: list[dict]) -> None:
    """Add same-day pool context features used by neighbor similarity."""
    if not candidates:
        return
    f1_values = [
        float(item.get("factor_scores", {}).get("F1_tail_fund_inflow", 0) or 0)
        for item in candidates
    ]
    f9_values = [
        float(item.get("factor_scores", {}).get("F9_overheat_control", 0) or 0)
        for item in candidates
    ]
    strong_low_heat_count = sum(
        1
        for item in candidates
        if float(item.get("factor_scores", {}).get("F1_tail_fund_inflow", 0) or 0) >= 80
        and float(item.get("factor_scores", {}).get("F9_overheat_control", 0) or 0) <= 50
    )
    strong_low_heat_share = round(strong_low_heat_count / len(candidates) * 100, 4)
    for item in candidates:
        fs = item.setdefault("factor_scores", {})
        f1 = float(fs.get("F1_tail_fund_inflow", 0) or 0)
        f9 = float(fs.get("F9_overheat_control", 0) or 0)
        fs["CTX_F1_percentile"] = _percentile_rank(f1_values, f1)
        fs["CTX_F9_percentile"] = _percentile_rank(f9_values, f9)
        fs["CTX_strong_f1_low_f9_share"] = strong_low_heat_share


def prepare_neighbor_rescue_backtest(samples: list[dict], base_config: dict) -> list[dict]:
    """Precompute per-day candidate state shared by neighbor rescue searches."""
    prepared = []
    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            c for c in sample.get("candidate_pool", [])
            if isinstance(c.get("return"), (int, float))
        ]
        if not valid_candidates:
            continue

        scored_candidates = []
        passing_candidates = []
        for raw in valid_candidates:
            item = dict(raw)
            item["_new_score"] = _score_candidate(item, base_config)
            item["_selection_blockers"] = _selection_blockers(item, base_config)
            if _passes_selection(item, base_config):
                item["_selection_mode"] = "base"
                passing_candidates.append(item)
            scored_candidates.append(item)
        _add_cross_section_context_features(scored_candidates)
        scored_candidates.sort(
            key=lambda x: (
                -x.get("_new_score", 0),
                -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
                -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
            )
        )
        passing_candidates.sort(
            key=lambda x: (
                -x.get("_new_score", 0),
                -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
                -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
            )
        )
        rank_by_symbol = {
            item.get("symbol"): index
            for index, item in enumerate(scored_candidates, start=1)
        }
        oracle = max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))
        prepared.append({
            "date": sample.get("date", ""),
            "candidates": scored_candidates,
            "base_pick": passing_candidates[0] if passing_candidates else None,
            "oracle": oracle,
            "oracle_return": float(oracle.get("return", 0) or 0),
            "rank_by_symbol": rank_by_symbol,
        })
    return prepared


def _prepared_rescue_pick(
    row: dict,
    rescue_score_threshold: float = 68.0,
    max_blockers: int = 3,
    allowed_blocker_prefixes: tuple[str, ...] | None = None,
    required_blocker_prefixes: tuple[str, ...] | None = None,
    rescue_min_factor_scores: dict | None = None,
    rescue_max_factor_scores: dict | None = None,
) -> Optional[dict]:
    allowed_prefixes = allowed_blocker_prefixes or (
        "F1_tail_fund_inflow>max",
        "F2_volume_price_sync<min",
        "F3_technical_pattern<min",
        "F7_float_mv_fit>max",
        "F8_overnight_risk_control<min",
        "F8_overnight_risk_control>max",
        "F9_overheat_control<min",
    )
    rescue_candidates = []
    for raw in row.get("candidates", []):
        if raw.get("_selection_mode") == "base":
            continue
        item = dict(raw)
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
        blockers = item.get("_selection_blockers")
        if blockers is None:
            blockers = _selection_blockers(item, row.get("base_config", {}))
        hard_blockers = [b for b in blockers if b != "score<threshold"]
        if len(hard_blockers) > int(max_blockers):
            continue
        if not all(any(b.startswith(prefix) for prefix in allowed_prefixes) for b in hard_blockers):
            continue
        if not all(
            any(b.startswith(prefix) for b in hard_blockers)
            for prefix in (required_blocker_prefixes or ())
        ):
            continue
        if float(item.get("_new_score", 0) or 0) < float(rescue_score_threshold):
            continue
        item["_rescue_blockers"] = hard_blockers
        rescue_candidates.append(item)

    if not rescue_candidates:
        return None
    rescue_candidates.sort(
        key=lambda x: (
            -x.get("_new_score", 0),
            -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
            -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
        )
    )
    return rescue_candidates[0]


def backtest_prepared_neighbor_rescue_pool(
    prepared_rows: list[dict],
    rescue_score_threshold: float = 68.0,
    max_blockers: int = 3,
    min_rescue_score_advantage: float = 5.0,
    max_rescue_score_advantage: float | None = None,
    allowed_blocker_prefixes: tuple[str, ...] | None = None,
    required_blocker_prefixes: tuple[str, ...] | None = None,
    rescue_min_factor_scores: dict | None = None,
    rescue_max_factor_scores: dict | None = None,
    rescue_when_base_absent_only: bool = False,
    rescue_when_base_present_only: bool = False,
    min_rescue_score_rank: int | None = None,
    max_rescue_score_rank: int | None = None,
    neighbor_factor_keys: tuple[str, ...] = (
        "F1_tail_fund_inflow",
        "F2_volume_price_sync",
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F7_float_mv_fit",
        "F8_overnight_risk_control",
        "F9_overheat_control",
    ),
    nearest_neighbor_count: int = 5,
    min_prior_neighbors: int = 3,
    min_neighbor_win_rate: float = 0.7,
    min_neighbor_avg_return: float = 0.0,
) -> dict:
    """Evaluate neighbor rescue on precomputed per-day candidate state."""
    picks = []
    empty_days = 0
    oracle_returns = []
    regrets = []
    exact_best_hits = 0
    segment_history: dict[tuple[str, ...], list[dict]] = {}

    for row in prepared_rows:
        oracle = row.get("oracle")
        if oracle is None:
            continue
        oracle_return = float(row.get("oracle_return", 0) or 0)
        oracle_returns.append(oracle_return)

        base_pick = row.get("base_pick")
        rescue_pick = _prepared_rescue_pick(
            row,
            rescue_score_threshold=rescue_score_threshold,
            max_blockers=max_blockers,
            allowed_blocker_prefixes=allowed_blocker_prefixes,
            required_blocker_prefixes=required_blocker_prefixes,
            rescue_min_factor_scores=rescue_min_factor_scores,
            rescue_max_factor_scores=rescue_max_factor_scores,
        )

        if rescue_pick is not None and (
            min_rescue_score_rank is not None or max_rescue_score_rank is not None
        ):
            rescue_rank = row.get("rank_by_symbol", {}).get(rescue_pick.get("symbol"))
            rescue_pick["_rescue_score_rank"] = rescue_rank
            if not _rescue_rank_allowed(
                rescue_rank,
                min_rescue_score_rank,
                max_rescue_score_rank,
            ):
                rescue_pick = None

        mode = "base"
        pick = base_pick
        if rescue_pick is not None:
            blockers = tuple(rescue_pick.get("_rescue_blockers", ()))
            history = segment_history.get(blockers, [])
            neighbors = sorted(
                history,
                key=lambda item: _candidate_factor_distance(
                    rescue_pick,
                    item,
                    neighbor_factor_keys,
                ),
            )[:int(nearest_neighbor_count)]
            neighbor_ok = False
            if len(neighbors) >= int(min_prior_neighbors):
                neighbor_returns = [float(item.get("return", 0) or 0) for item in neighbors]
                win_rate = sum(1 for value in neighbor_returns if value > 0) / len(neighbor_returns)
                avg_return = sum(neighbor_returns) / len(neighbor_returns)
                neighbor_ok = (
                    win_rate >= float(min_neighbor_win_rate)
                    and avg_return >= float(min_neighbor_avg_return)
                )

            if base_pick is None:
                if rescue_when_base_present_only:
                    pick = None
                    mode = "base"
                elif neighbor_ok:
                    pick = rescue_pick
                    mode = "neighbor_rescue"
                else:
                    pick = None
                    mode = "base"
            elif rescue_when_base_absent_only:
                pick = base_pick
                mode = "base"
            else:
                rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
                base_score = float(base_pick.get("_new_score", 0) or 0)
                score_advantage = rescue_score - base_score
                max_advantage_ok = (
                    max_rescue_score_advantage is None
                    or score_advantage <= float(max_rescue_score_advantage)
                )
                if neighbor_ok and score_advantage >= min_rescue_score_advantage and max_advantage_ok:
                    pick = rescue_pick
                    mode = "neighbor_rescue"

            segment_history.setdefault(blockers, []).append(rescue_pick)

        if pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue

        pick_return = float(pick.get("return", 0) or 0)
        if pick.get("symbol") == oracle.get("symbol"):
            exact_best_hits += 1
        regrets.append(max(0.0, oracle_return - pick_return))
        picks.append({
            "date": row.get("date", ""),
            "symbol": pick.get("symbol", ""),
            "score": pick.get("_new_score", 0),
            "return": pick_return,
            "win": pick_return > 0,
            "mode": mode,
            "rescue_blockers": pick.get("_rescue_blockers", []) if mode == "neighbor_rescue" else [],
        })

    return _summarize_picks_with_oracle(picks, empty_days, oracle_returns, regrets, exact_best_hits)


def backtest_neighbor_counterfactual_rescue_pool(
    samples: list[dict],
    base_config: dict,
    rescue_score_threshold: float = 68.0,
    max_blockers: int = 3,
    min_rescue_score_advantage: float = 5.0,
    max_rescue_score_advantage: float | None = None,
    allowed_blocker_prefixes: tuple[str, ...] | None = None,
    required_blocker_prefixes: tuple[str, ...] | None = None,
    rescue_min_factor_scores: dict | None = None,
    rescue_max_factor_scores: dict | None = None,
    rescue_when_base_absent_only: bool = False,
    rescue_when_base_present_only: bool = False,
    min_rescue_score_rank: int | None = None,
    max_rescue_score_rank: int | None = None,
    neighbor_factor_keys: tuple[str, ...] = (
        "F1_tail_fund_inflow",
        "F2_volume_price_sync",
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F7_float_mv_fit",
        "F8_overnight_risk_control",
        "F9_overheat_control",
    ),
    nearest_neighbor_count: int = 5,
    min_prior_neighbors: int = 3,
    min_neighbor_win_rate: float = 0.7,
    min_neighbor_avg_return: float = 0.0,
) -> dict:
    """Backtest rescue only when similar past blocked candidates had edge."""
    picks = []
    empty_days = 0
    oracle_returns = []
    regrets = []
    exact_best_hits = 0
    segment_history: dict[tuple[str, ...], list[dict]] = {}

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        valid_candidates = [
            c for c in sample.get("candidate_pool", [])
            if isinstance(c.get("return"), (int, float))
        ]
        if not valid_candidates:
            continue
        oracle = max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))
        oracle_return = float(oracle.get("return", 0) or 0)
        oracle_returns.append(oracle_return)

        base_pick = _base_pick_from_candidate_pool(sample, base_config)
        scored_candidates = []
        for raw in valid_candidates:
            item = dict(raw)
            item["_new_score"] = _score_candidate(item, base_config)
            scored_candidates.append(item)
        _add_cross_section_context_features(scored_candidates)
        context_by_symbol = {
            item.get("symbol"): item.get("factor_scores", {})
            for item in scored_candidates
        }
        rescue_pick = _pick_counterfactual_rescue_candidate(
            sample,
            base_config,
            rescue_score_threshold=rescue_score_threshold,
            max_blockers=max_blockers,
            allowed_blocker_prefixes=allowed_blocker_prefixes,
            required_blocker_prefixes=required_blocker_prefixes,
            rescue_min_factor_scores=rescue_min_factor_scores,
            rescue_max_factor_scores=rescue_max_factor_scores,
        )
        if rescue_pick is not None:
            rescue_pick.setdefault("factor_scores", {}).update(
                context_by_symbol.get(rescue_pick.get("symbol"), {})
            )

        if rescue_pick is not None and (
            min_rescue_score_rank is not None or max_rescue_score_rank is not None
        ):
            ranked_candidates = []
            for raw in valid_candidates:
                item = dict(raw)
                item["_new_score"] = _score_candidate(item, base_config)
                ranked_candidates.append(item)
            ranked_candidates.sort(
                key=lambda x: (
                    -x.get("_new_score", 0),
                    -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
                    -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
                )
            )
            rescue_rank = next(
                (
                    index
                    for index, item in enumerate(ranked_candidates, start=1)
                    if item.get("symbol") == rescue_pick.get("symbol")
                ),
                None,
            )
            rescue_pick["_rescue_score_rank"] = rescue_rank
            if not _rescue_rank_allowed(
                rescue_rank,
                min_rescue_score_rank,
                max_rescue_score_rank,
            ):
                rescue_pick = None

        mode = "base"
        pick = base_pick
        if rescue_pick is not None:
            blockers = tuple(rescue_pick.get("_rescue_blockers", ()))
            history = segment_history.get(blockers, [])
            neighbors = sorted(
                history,
                key=lambda item: _candidate_factor_distance(
                    rescue_pick,
                    item,
                    neighbor_factor_keys,
                ),
            )[:int(nearest_neighbor_count)]
            neighbor_ok = False
            if len(neighbors) >= int(min_prior_neighbors):
                neighbor_returns = [
                    float(item.get("return", 0) or 0)
                    for item in neighbors
                ]
                win_rate = sum(1 for value in neighbor_returns if value > 0) / len(neighbor_returns)
                avg_return = sum(neighbor_returns) / len(neighbor_returns)
                neighbor_ok = (
                    win_rate >= float(min_neighbor_win_rate)
                    and avg_return >= float(min_neighbor_avg_return)
                )

            if base_pick is None:
                if rescue_when_base_present_only:
                    pick = None
                    mode = "base"
                elif neighbor_ok:
                    pick = rescue_pick
                    mode = "neighbor_rescue"
                else:
                    pick = None
                    mode = "base"
            elif rescue_when_base_absent_only:
                pick = base_pick
                mode = "base"
            else:
                rescue_score = float(rescue_pick.get("_new_score", 0) or 0)
                base_score = float(base_pick.get("_new_score", 0) or 0)
                score_advantage = rescue_score - base_score
                max_advantage_ok = (
                    max_rescue_score_advantage is None
                    or score_advantage <= float(max_rescue_score_advantage)
                )
                if neighbor_ok and score_advantage >= min_rescue_score_advantage and max_advantage_ok:
                    pick = rescue_pick
                    mode = "neighbor_rescue"

            segment_history.setdefault(blockers, []).append(rescue_pick)

        if pick is None:
            empty_days += 1
            regrets.append(max(0.0, oracle_return))
            continue

        pick_return = float(pick.get("return", 0) or 0)
        if pick.get("symbol") == oracle.get("symbol"):
            exact_best_hits += 1
        regrets.append(max(0.0, oracle_return - pick_return))
        picks.append({
            "date": sample.get("date", ""),
            "symbol": pick.get("symbol", ""),
            "score": pick.get("_new_score", 0),
            "return": pick_return,
            "win": pick_return > 0,
            "mode": mode,
            "rescue_blockers": pick.get("_rescue_blockers", []) if mode == "neighbor_rescue" else [],
        })

    return _summarize_picks_with_oracle(picks, empty_days, oracle_returns, regrets, exact_best_hits)


def _candidate_oracle(sample: dict) -> Optional[dict]:
    valid_candidates = [
        c for c in sample.get("candidate_pool", [])
        if isinstance(c.get("return"), (int, float))
    ]
    if not valid_candidates:
        return None
    return max(valid_candidates, key=lambda c: float(c.get("return", 0) or 0))


def _floor_from_values(values: list[float], step: int = 5) -> int:
    if not values:
        return 0
    return int(max(0, min(100, math.floor(min(values) / step) * step)))


def _quantile_floor_from_values(values: list[float], quantile: float, step: int = 5) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    q = max(0.0, min(1.0, float(quantile)))
    index = min(len(ordered) - 1, int(math.floor((len(ordered) - 1) * q)))
    return int(max(0, min(100, math.floor(ordered[index] / step) * step)))


def mine_oracle_rescue_segments(
    samples: list[dict],
    base_config: dict,
    min_segment_hits: int = 5,
    floor_quantiles: tuple[float, ...] = (0.0,),
    factor_floor_keys: tuple[str, ...] = (
        "F3_technical_pattern",
        "F4_tail_rally_strength",
        "F8_overnight_risk_control",
        "F9_overheat_control",
    ),
) -> list[dict]:
    """Mine blocked-oracle rescue segments without mutating strategy config."""
    base_backtest = backtest_candidate_pool(samples, base_config)
    train_samples, validation_samples = split_walk_forward_samples(samples)
    base_train_backtest = backtest_candidate_pool(train_samples, base_config) if train_samples else {}
    base_validation_backtest = (
        backtest_candidate_pool(validation_samples, base_config)
        if validation_samples else {}
    )
    segments: dict[tuple[str, ...], list[dict]] = {}

    for sample in sorted(samples, key=lambda s: str(s.get("date", ""))):
        oracle = _candidate_oracle(sample)
        if oracle is None:
            continue
        item = dict(oracle)
        item["_new_score"] = _score_candidate(item, base_config)
        blockers = tuple(
            b for b in _selection_blockers(item, base_config)
            if b != "score<threshold"
        )
        if not blockers:
            continue
        segments.setdefault(blockers, []).append(item)

    mined = []
    for blockers, oracle_rows in segments.items():
        if len(oracle_rows) < min_segment_hits:
            continue
        for floor_quantile in floor_quantiles:
            floor_values = {}
            for key in factor_floor_keys:
                values = [
                    float(row.get("factor_scores", {}).get(key, 0) or 0)
                    for row in oracle_rows
                    if key in row.get("factor_scores", {})
                ]
                floor = _quantile_floor_from_values(values, floor_quantile)
                if floor > 0:
                    floor_values[key] = floor
            rescue_score_threshold = _quantile_floor_from_values([
                float(row.get("_new_score", 0) or 0)
                for row in oracle_rows
            ], floor_quantile)
            backtest = backtest_counterfactual_rescue_pool(
                samples,
                base_config,
                rescue_score_threshold=rescue_score_threshold,
                max_blockers=len(blockers),
                min_rescue_score_advantage=0,
                allowed_blocker_prefixes=blockers,
                rescue_min_factor_scores=floor_values,
            )
            train_backtest = (
                backtest_counterfactual_rescue_pool(
                    train_samples,
                    base_config,
                    rescue_score_threshold=rescue_score_threshold,
                    max_blockers=len(blockers),
                    min_rescue_score_advantage=0,
                    allowed_blocker_prefixes=blockers,
                    rescue_min_factor_scores=floor_values,
                )
                if train_samples else {}
            )
            validation_backtest = (
                backtest_counterfactual_rescue_pool(
                    validation_samples,
                    base_config,
                    rescue_score_threshold=rescue_score_threshold,
                    max_blockers=len(blockers),
                    min_rescue_score_advantage=0,
                    allowed_blocker_prefixes=blockers,
                    rescue_min_factor_scores=floor_values,
                )
                if validation_samples else {}
            )
            mined.append({
                "allowed_blockers": blockers,
                "oracle_hits": len(oracle_rows),
                "floor_quantile": float(floor_quantile),
                "rescue_score_threshold": rescue_score_threshold,
                "max_blockers": len(blockers),
                "min_rescue_score_advantage": 0,
                "rescue_min_factor_scores": floor_values,
                "base_backtest": _compact_backtest(base_backtest),
                "base_train_backtest": _compact_backtest(base_train_backtest),
                "base_validation_backtest": _compact_backtest(base_validation_backtest),
                "backtest": _compact_backtest(backtest),
                "train_backtest": _compact_backtest(train_backtest),
                "validation_backtest": _compact_backtest(validation_backtest),
            })

    mined.sort(
        key=lambda item: (
            item["backtest"].get("avg_regret", 0),
            -item["backtest"].get("exact_best_hit_rate", 0),
            -item["backtest"].get("total_return", 0),
            -item["oracle_hits"],
            item["allowed_blockers"],
        )
    )
    return mined


def evaluate_optimization_candidate(old_bt: dict, new_bt: dict,
                                    max_empty_increase_ratio: float = 0.15,
                                    avg_return_tolerance: float = 0.001,
                                    min_high_confidence_trades: int = 90,
                                    low_participation_threshold: float = 0.25,
                                    min_win_gain_when_reducing_low_participation: float = 0.05,
                                    min_regret_reduction: float = 0.002
                                    ) -> tuple[bool, str]:
    """判断候选池优化是否值得落盘。

    接受条件：
    - 胜率或平均收益至少一项真实改善；
    - 最大连亏不能恶化；
    - 不能主要靠新增大量空仓制造胜率改善。
    """
    old_win = float(old_bt.get("win_rate", 0) or 0)
    new_win = float(new_bt.get("win_rate", 0) or 0)
    old_avg = float(old_bt.get("avg_return", 0) or 0)
    new_avg = float(new_bt.get("avg_return", 0) or 0)
    old_total = float(old_bt.get("total_return", 0) or 0)
    new_total = float(new_bt.get("total_return", 0) or 0)
    old_regret = float(old_bt.get("avg_regret", 0) or 0)
    new_regret = float(new_bt.get("avg_regret", 0) or 0)
    old_best_hit = float(old_bt.get("exact_best_hit_rate", 0) or 0)
    new_best_hit = float(new_bt.get("exact_best_hit_rate", 0) or 0)
    old_top3_hit = float(old_bt.get("top3_hit_rate", 0) or 0)
    new_top3_hit = float(new_bt.get("top3_hit_rate", 0) or 0)
    old_loss = int(old_bt.get("max_consecutive_loss", 0) or 0)
    new_loss = int(new_bt.get("max_consecutive_loss", 0) or 0)
    old_empty = int(old_bt.get("empty_days", 0) or 0)
    new_empty = int(new_bt.get("empty_days", 0) or 0)
    old_trades = int(old_bt.get("trade_samples", 0) or 0)
    new_trades = int(new_bt.get("trade_samples", 0) or 0)
    samples = max(int(old_bt.get("samples", 0) or 0), int(new_bt.get("samples", 0) or 0), 1)
    required_high_confidence_trades = min(
        min_high_confidence_trades,
        max(20, int(samples * 0.4)),
    )

    win_improved = new_win > old_win
    avg_improved = new_avg > old_avg
    total_improved = new_total > old_total
    regret_improved = old_regret > 0 and new_regret <= old_regret - min_regret_reduction
    best_hit_improved = new_best_hit > old_best_hit
    top3_hit_improved = new_top3_hit > old_top3_hit
    empty_increase_ratio = max(new_empty - old_empty, 0) / samples
    old_participation = old_trades / samples
    new_participation = new_trades / samples
    high_confidence_filter = (
        new_trades >= required_high_confidence_trades
        and new_win >= old_win + 0.08
        and avg_improved
        and new_loss <= old_loss
    )
    regret_priority_accept = (
        regret_improved
        and (best_hit_improved or top3_hit_improved)
        and new_avg >= old_avg - avg_return_tolerance
        and new_total >= old_total - avg_return_tolerance
        and new_loss <= old_loss
    )

    problems = []
    if new_win < old_win:
        problems.append(f"胜率下降 {old_win:.2%}→{new_win:.2%}")
    if not (win_improved or avg_improved or regret_improved):
        problems.append("未真实改善胜率或平均收益")
    if win_improved and new_avg < old_avg - avg_return_tolerance:
        problems.append(f"平均收益明显变差 {old_avg:.2%}→{new_avg:.2%}")
    if win_improved and not (avg_improved or total_improved):
        problems.append(
            f"收益未改善，平均收益 {old_avg:.2%}→{new_avg:.2%}，"
            f"总收益 {old_total:.2%}→{new_total:.2%}"
        )
    if new_loss > old_loss:
        problems.append(f"最大连亏恶化 {old_loss}→{new_loss}")
    if empty_increase_ratio > max_empty_increase_ratio and not high_confidence_filter:
        problems.append(f"空仓增加过多 {old_empty}→{new_empty}")
    if (
        old_participation < low_participation_threshold
        and new_participation < old_participation
        and new_win < old_win + min_win_gain_when_reducing_low_participation
    ):
        problems.append(
            f"出手率已低仍继续下降 {old_participation:.2%}→{new_participation:.2%}"
        )

    if regret_priority_accept:
        problems = [
            problem for problem in problems
            if not (
                problem.startswith("胜率下降")
                or problem.startswith("未真实改善")
                or problem.startswith("收益未改善")
            )
        ]

    if problems:
        return False, "；".join(problems)

    gains = []
    if win_improved:
        gains.append(f"胜率 {old_win:.2%}→{new_win:.2%}")
    if avg_improved:
        gains.append(f"平均收益 {old_avg:.2%}→{new_avg:.2%}")
    if regret_improved:
        gains.append(f"机会损失 {old_regret:.2%}→{new_regret:.2%}")
    if best_hit_improved:
        gains.append(f"最优命中 {old_best_hit:.2%}→{new_best_hit:.2%}")
    if top3_hit_improved:
        gains.append(f"Top3命中 {old_top3_hit:.2%}→{new_top3_hit:.2%}")
    gains.append(f"最大连亏 {old_loss}→{new_loss}")
    if empty_increase_ratio > max_empty_increase_ratio:
        gains.append(f"高置信过滤，空仓 {old_empty}→{new_empty}，交易样本 {new_trades}")
    return True, "；".join(gains)


def split_walk_forward_samples(samples: list[dict],
                               validation_ratio: float = 0.3,
                               min_validation_samples: int = 20) -> tuple[list[dict], list[dict]]:
    """Split samples chronologically: older training, latest validation."""
    usable = sorted(
        [s for s in samples if s.get("candidate_pool")],
        key=lambda s: str(s.get("date", "")),
    )
    if len(usable) < 2:
        return usable, []
    validation_size = max(int(round(len(usable) * validation_ratio)), min_validation_samples)
    validation_size = min(max(validation_size, 1), len(usable) - 1)
    return usable[:-validation_size], usable[-validation_size:]


def evaluate_walk_forward_candidate(train_old_bt: dict, train_new_bt: dict,
                                    validation_old_bt: dict, validation_new_bt: dict,
                                    full_old_bt: dict | None = None,
                                    full_new_bt: dict | None = None
                                    ) -> tuple[bool, str]:
    """Accept only if training improves and latest validation does not regress."""
    train_ok, train_reason = evaluate_optimization_candidate(train_old_bt, train_new_bt)
    if not train_ok:
        return False, f"训练段未通过：{train_reason}"

    validation_ok, validation_reason = evaluate_optimization_candidate(
        validation_old_bt,
        validation_new_bt,
        max_empty_increase_ratio=0.10,
        avg_return_tolerance=0.0005,
        min_regret_reduction=0.0003,
    )
    if not validation_ok:
        return False, f"验证段未通过：{validation_reason}"

    full_problems = []
    if full_old_bt and full_new_bt:
        old_regret = float(full_old_bt.get("avg_regret", 0) or 0)
        new_regret = float(full_new_bt.get("avg_regret", 0) or 0)
        old_best_hit = float(full_old_bt.get("exact_best_hit_rate", 0) or 0)
        new_best_hit = float(full_new_bt.get("exact_best_hit_rate", 0) or 0)
        if old_regret > 0 and new_regret > old_regret:
            full_problems.append(f"全样本机会损失退化 {old_regret:.2%}→{new_regret:.2%}")
        if new_best_hit < old_best_hit:
            full_problems.append(f"全样本最优命中退化 {old_best_hit:.2%}→{new_best_hit:.2%}")
    if full_problems:
        return False, "；".join(full_problems)

    return True, f"训练段 {train_reason}；验证段 {validation_reason}"


def _participation(backtest: dict) -> float:
    samples = int(backtest.get("samples", 0) or 0)
    if samples <= 0:
        return 0.0
    return int(backtest.get("trade_samples", 0) or 0) / samples


def _profit_loss_ratio(backtest: dict) -> float:
    picks = backtest.get("picks", []) or []
    gains = [float(p.get("return", 0) or 0) for p in picks if float(p.get("return", 0) or 0) > 0]
    losses = [-float(p.get("return", 0) or 0) for p in picks if float(p.get("return", 0) or 0) < 0]
    if not gains or not losses:
        return 0.0
    avg_loss = sum(losses) / len(losses)
    if avg_loss <= 0:
        return 0.0
    return round((sum(gains) / len(gains)) / avg_loss, 4)


def evaluate_balance_candidate(
    backtest: dict,
    min_participation: float = 0.30,
    max_participation: float = 0.45,
    min_win_rate: float = 0.70,
    max_consecutive_loss: int = 3,
    min_avg_return: float = 0.0,
) -> tuple[bool, str, float]:
    """Evaluate a single formal strategy against the win/participation balance target."""
    participation = _participation(backtest)
    win_rate = float(backtest.get("win_rate", 0) or 0)
    avg_return = float(backtest.get("avg_return", 0) or 0)
    max_loss = int(backtest.get("max_consecutive_loss", 0) or 0)
    trade_samples = int(backtest.get("trade_samples", 0) or 0)

    problems = []
    if participation < min_participation:
        problems.append(f"出手率低于目标 {participation:.2%}<{min_participation:.2%}")
    if participation > max_participation:
        problems.append(f"出手率高于目标 {participation:.2%}>{max_participation:.2%}")
    if win_rate < min_win_rate:
        problems.append(f"胜率低于目标 {win_rate:.2%}<{min_win_rate:.2%}")
    if avg_return <= min_avg_return:
        problems.append(f"平均收益不达标 {avg_return:.2%}<={min_avg_return:.2%}")
    if max_loss > max_consecutive_loss:
        problems.append(f"最大连亏超限 {max_loss}>{max_consecutive_loss}")
    if trade_samples <= 0:
        problems.append("无出手样本")

    if problems:
        return False, "；".join(problems), -1.0

    target_mid = (min_participation + max_participation) / 2
    participation_fit = 1 - abs(participation - target_mid) / max(max_participation - min_participation, 0.01)
    pl_ratio = _profit_loss_ratio(backtest)
    score = (
        win_rate * 100
        + max(avg_return, 0) * 1000
        + max(participation_fit, 0) * 10
        + min(pl_ratio, 2.0) * 2
        - max_loss * 2
        + trade_samples / 1000
    )
    reason = (
        f"出手率 {participation:.2%}，胜率 {win_rate:.2%}，"
        f"平均收益 {avg_return:.2%}，最大连亏 {max_loss}，盈亏比 1:{pl_ratio:.2f}"
    )
    return True, reason, round(score, 4)


def _compact_backtest(backtest: dict) -> dict:
    return {
        key: backtest.get(key)
        for key in (
            "samples", "trade_samples", "empty_days", "win_rate",
            "avg_return", "total_return", "max_consecutive_loss",
            "avg_regret", "total_regret", "exact_best_hit_rate",
            "top3_hit_rate", "avg_oracle_return",
        )
        if key in backtest
    }


def _compact_evaluated_candidates(candidates: list[dict], limit: int = 10) -> list[dict]:
    """Keep a compact candidate list while preserving special diagnostics."""
    compact = list(candidates[:limit])
    existing_names = {item.get("name") for item in compact}
    for item in candidates[limit:]:
        if item.get("name") == "gated_regret_balanced_oracle_ranker" and item.get("name") not in existing_names:
            compact.append(item)
            existing_names.add(item.get("name"))
    return compact


def _regret_priority_key(backtest: dict) -> tuple:
    """Sort candidates by the stated objective: regret near zero, then oracle hits."""
    return (
        -float(backtest.get("avg_regret", 999) or 999),
        -float(backtest.get("total_regret", 999) or 999),
        float(backtest.get("exact_best_hit_rate", 0) or 0),
        float(backtest.get("win_rate", 0) or 0),
        float(backtest.get("avg_return", 0) or 0),
        float(backtest.get("total_return", 0) or 0),
        -int(backtest.get("max_consecutive_loss", 999) or 999),
        int(backtest.get("trade_samples", 0) or 0),
    )


def _candidate_selection_key(eval_row: dict, full_backtest: dict) -> tuple:
    """Prefer validation regret first when available, then full-sample regret."""
    comparison = eval_row.get("validation_backtest") or full_backtest
    return (
        *_regret_priority_key(comparison),
        *_regret_priority_key(full_backtest),
    )


def _balance_candidate_configs(config: dict, correlations: dict[str, float],
                               samples: list[dict]) -> list[tuple[str, dict, dict]]:
    """Generate balance-oriented single-strategy candidates."""
    configs = list(_candidate_configs(config, correlations, training_samples=samples))
    selection = config.get("selection", {})
    old_weights = {
        fk: config["factors"][fk]["weight"]
        for fk in _active_factor_keys(config)
        if fk in config.get("factors", {})
    }

    templates = [
        ("balanced_30_40_strict", 58.0, {"F2_volume_price_sync": 70, "F4_tail_rally_strength": 70, "F3_technical_pattern": 70, "F8_overnight_risk_control": 70, "F9_overheat_control": 85}, {"F7_float_mv_fit": 50, "F1_tail_fund_inflow": 92, "F8_overnight_risk_control": 92}),
        ("balanced_35_45", 55.0, {"F2_volume_price_sync": 68, "F4_tail_rally_strength": 68, "F3_technical_pattern": 68, "F8_overnight_risk_control": 68, "F9_overheat_control": 80}, {"F7_float_mv_fit": 60, "F1_tail_fund_inflow": 92, "F8_overnight_risk_control": 92}),
        ("balanced_soft_tail", 52.0, {"F3_technical_pattern": 65, "F8_overnight_risk_control": 65, "F9_overheat_control": 80}, {"F7_float_mv_fit": 60, "F1_tail_fund_inflow": 95, "F8_overnight_risk_control": 95}),
        ("participation_recovery_guarded", 50.0, {"F2_volume_price_sync": 60, "F4_tail_rally_strength": 60, "F3_technical_pattern": 65, "F8_overnight_risk_control": 65, "F9_overheat_control": 75}, {"F7_float_mv_fit": 70, "F1_tail_fund_inflow": 95, "F8_overnight_risk_control": 95}),
        ("testable_mid_band", 50.0, {"F2_volume_price_sync": 60, "F4_tail_rally_strength": 70, "F3_technical_pattern": 70}, {"F7_float_mv_fit": 60}),
    ]

    score_variants = [-3.0, 0.0, 3.0]
    guard_variants = [-3, 0, 3]
    for base_name, base_score, base_min, base_max in templates:
        for score_delta in score_variants:
            for guard_delta in guard_variants:
                min_scores = {}
                for key, value in base_min.items():
                    if key in config.get("factors", {}):
                        min_scores[key] = max(0, min(100, int(value + guard_delta)))
                max_scores = {}
                for key, value in base_max.items():
                    if key in config.get("factors", {}) or key in ("F7_float_mv_fit", "F1_tail_fund_inflow"):
                        max_scores[key] = max(0, min(100, int(value - guard_delta)))
                score_threshold = max(0.0, min(100.0, base_score + score_delta))
                new_config = json.loads(json.dumps(config))
                new_config["selection"]["score_threshold"] = score_threshold
                new_config["selection"]["min_factor_scores"] = min_scores
                new_config["selection"]["max_factor_scores"] = max_scores
                new_config["selection"]["soft_penalties"] = {
                    "F2_volume_price_sync": {
                        "direction": "below",
                        "threshold": min_scores.get("F2_volume_price_sync", 60),
                        "max_penalty": 3,
                    },
                    "F4_tail_rally_strength": {
                        "direction": "below",
                        "threshold": min_scores.get("F4_tail_rally_strength", 60),
                        "max_penalty": 3,
                    },
                    "F7_float_mv_fit": {
                        "direction": "above",
                        "threshold": max_scores.get("F7_float_mv_fit", 60),
                        "max_penalty": 2,
                    },
                }
                log = {
                    "old_weights": old_weights,
                    "new_weights": old_weights,
                    "correlations": correlations,
                    "changes": {
                        "balance_search": {
                            "template": base_name,
                            "before": {
                                "score_threshold": selection.get("score_threshold"),
                                "min_factor_scores": selection.get("min_factor_scores", {}),
                                "max_factor_scores": selection.get("max_factor_scores", {}),
                            },
                            "after": {
                                "score_threshold": score_threshold,
                                "min_factor_scores": min_scores,
                                "max_factor_scores": max_scores,
                                "soft_penalties": new_config["selection"]["soft_penalties"],
                            },
                        },
                    },
                }
                name = f"{base_name}_score{score_threshold}_guard{guard_delta}"
                configs.append((name, new_config, log))
    return configs


# ---------------------------------------------------------------------------
# 迭代候选配置搜索（支持多轮训练-验证）
# ---------------------------------------------------------------------------

def _run_candidate_selection_cycle(
    config: dict,
    correlations: dict,
    candidate_samples: list[dict],
    train_samples: list[dict],
    validation_samples: list[dict],
    use_walk_forward: bool,
) -> dict:
    """对单轮做候选回测-评估，返回最优候选与评估过程。"""
    old_candidate_bt = (
        backtest_candidate_pool(candidate_samples, config)
        if candidate_samples
        else {}
    )
    old_train_bt = backtest_candidate_pool(train_samples, config) if train_samples else {}
    old_validation_bt = (
        backtest_candidate_pool(validation_samples, config) if validation_samples else {}
    )

    best = None
    evaluated_candidates = []
    candidate_name = "base_config"
    candidate_config = json.loads(json.dumps(config))
    candidate_log = {
        "old_weights": {},
        "new_weights": {},
        "correlations": correlations,
        "changes": {},
    }
    candidate_bt = old_candidate_bt
    reason = "未找到可评估候选"

    if not candidate_samples:
        if not train_samples and not validation_samples:
            return {
                "selected": False,
                "accepted": False,
                "reason": "无候选池样本，无法执行候选池重选",
                "candidate_name": candidate_name,
                "config": candidate_config,
                "change_log": candidate_log,
                "old_candidate_backtest": old_candidate_bt,
                "new_candidate_backtest": candidate_bt,
                "train_backtest": old_train_bt,
                "validation_backtest": old_validation_bt,
                "evaluated_candidates": evaluated_candidates,
            }
        # fallback：用权重重排 + 历史交易验证（兼容无候选场景）
        new_cfg, log = adjust_weights(config, correlations)
        new_bt = {
            "win_rate": backtest_with_weights(train_samples + validation_samples, new_cfg),
        }
        old_win = backtest_with_weights(train_samples + validation_samples, config)
        accepted = new_bt["win_rate"] > old_win if new_bt.get("win_rate") is not None else False
        candidate_config = new_cfg
        candidate_log = log
        candidate_bt = new_bt
        reason = f"胜率 {old_win:.2%}→{new_bt['win_rate']:.2%}" if accepted else f"未真实改善胜率 {old_win:.2%}→{new_bt['win_rate']:.2%}"
        return {
            "selected": False,
            "accepted": bool(accepted),
            "reason": reason,
            "candidate_name": "factor_correlation_weights",
            "config": candidate_config,
            "change_log": candidate_log,
            "old_candidate_backtest": old_candidate_bt,
            "new_candidate_backtest": candidate_bt,
            "train_backtest": old_train_bt,
            "validation_backtest": old_validation_bt,
            "evaluated_candidates": evaluated_candidates,
        }

    for cname, ccfg, clog in _candidate_configs(
        config,
        correlations,
        training_samples=train_samples if train_samples else candidate_samples,
    ):
        cbt = backtest_candidate_pool(candidate_samples, ccfg)
        if use_walk_forward and train_samples and validation_samples:
            c_train_bt = backtest_candidate_pool(train_samples, ccfg)
            c_validation_bt = backtest_candidate_pool(validation_samples, ccfg)
            accepted, c_reason = evaluate_walk_forward_candidate(
                old_train_bt,
                c_train_bt,
                old_validation_bt,
                c_validation_bt,
                old_candidate_bt,
                cbt,
            )
            current_eval = {
                "name": cname,
                "backtest": _compact_backtest(cbt),
                "train_backtest": _compact_backtest(c_train_bt),
                "validation_backtest": _compact_backtest(c_validation_bt),
            }
        else:
            accepted, c_reason = evaluate_optimization_candidate(old_candidate_bt, cbt)
            current_eval = {
                "name": cname,
                "backtest": _compact_backtest(cbt),
            }

        current_eval.update({
            "accepted": accepted,
            "reason": c_reason,
        })
        evaluated_candidates.append(current_eval)
        if not accepted:
            continue

        key = _candidate_selection_key(current_eval, current_eval["backtest"])
        if best is None or key > best[0]:
            best = (
                key,
                cname,
                ccfg,
                clog,
                cbt,
                c_reason,
                current_eval.get("train_backtest"),
                current_eval.get("validation_backtest"),
            )

    if candidate_samples and train_samples:
        gated_candidate = build_gated_regret_ranker_candidate(
            train_samples if train_samples else candidate_samples,
            config,
        )
        gated_bt = backtest_gated_candidate_pool(
            candidate_samples,
            gated_candidate["base_config"],
            gated_candidate["attack_config"],
            gated_candidate["min_attack_score_advantage"],
            gated_candidate["attack_min_factor_scores"],
        )
        if use_walk_forward and train_samples and validation_samples:
            gated_train_bt = backtest_gated_candidate_pool(
                train_samples,
                gated_candidate["base_config"],
                gated_candidate["attack_config"],
                gated_candidate["min_attack_score_advantage"],
                gated_candidate["attack_min_factor_scores"],
            )
            gated_validation_bt = backtest_gated_candidate_pool(
                validation_samples,
                gated_candidate["base_config"],
                gated_candidate["attack_config"],
                gated_candidate["min_attack_score_advantage"],
                gated_candidate["attack_min_factor_scores"],
            )
            accepted, gated_reason = evaluate_walk_forward_candidate(
                old_train_bt,
                gated_train_bt,
                old_validation_bt,
                gated_validation_bt,
                old_candidate_bt,
                gated_bt,
            )
            gated_eval = {
                "name": gated_candidate["name"],
                "backtest": _compact_backtest(gated_bt),
                "train_backtest": _compact_backtest(gated_train_bt),
                "validation_backtest": _compact_backtest(gated_validation_bt),
                "gated_config": {
                    "min_attack_score_advantage": gated_candidate["min_attack_score_advantage"],
                    "attack_min_factor_scores": gated_candidate["attack_min_factor_scores"],
                },
            }
        else:
            accepted, gated_reason = evaluate_optimization_candidate(old_candidate_bt, gated_bt)
            gated_eval = {
                "name": gated_candidate["name"],
                "backtest": _compact_backtest(gated_bt),
                "gated_config": {
                    "min_attack_score_advantage": gated_candidate["min_attack_score_advantage"],
                    "attack_min_factor_scores": gated_candidate["attack_min_factor_scores"],
                },
            }
        gated_eval.update({
            "accepted": accepted,
            "reason": gated_reason,
        })
        evaluated_candidates.append(gated_eval)
        if accepted:
            key = _candidate_selection_key(gated_eval, gated_eval["backtest"])
            if best is None or key > best[0]:
                best = (
                    key,
                    gated_candidate["name"],
                    gated_candidate["attack_config"],
                    gated_candidate["change_log"],
                    gated_bt,
                    gated_reason,
                    gated_eval.get("train_backtest"),
                    gated_eval.get("validation_backtest"),
                )

        rescue_params = {
            "rescue_score_threshold": 80,
            "max_blockers": 3,
            "min_rescue_score_advantage": 12,
            "rescue_min_factor_scores": {
                "F3_technical_pattern": 80,
                "F7_float_mv_fit": 60,
            },
        }
        rescue_bt = backtest_counterfactual_rescue_pool(
            candidate_samples,
            config,
            **rescue_params,
        )
        if use_walk_forward and train_samples and validation_samples:
            rescue_train_bt = backtest_counterfactual_rescue_pool(
                train_samples,
                config,
                **rescue_params,
            )
            rescue_validation_bt = backtest_counterfactual_rescue_pool(
                validation_samples,
                config,
                **rescue_params,
            )
            accepted, rescue_reason = evaluate_walk_forward_candidate(
                old_train_bt,
                rescue_train_bt,
                old_validation_bt,
                rescue_validation_bt,
                old_candidate_bt,
                rescue_bt,
            )
            rescue_eval = {
                "name": "counterfactual_rescue_gate",
                "backtest": _compact_backtest(rescue_bt),
                "train_backtest": _compact_backtest(rescue_train_bt),
                "validation_backtest": _compact_backtest(rescue_validation_bt),
                "rescue_config": rescue_params,
            }
        else:
            accepted, rescue_reason = evaluate_optimization_candidate(old_candidate_bt, rescue_bt)
            rescue_eval = {
                "name": "counterfactual_rescue_gate",
                "backtest": _compact_backtest(rescue_bt),
                "rescue_config": rescue_params,
            }
        rescue_eval.update({
            "accepted": accepted,
            "reason": rescue_reason,
        })
        evaluated_candidates.append(rescue_eval)
        if accepted:
            rescue_config_to_save = json.loads(json.dumps(config))
            rescue_config_to_save.setdefault("selection", {})["counterfactual_rescue"] = {
                "enabled": True,
                **rescue_params,
            }
            key = _candidate_selection_key(rescue_eval, rescue_eval["backtest"])
            if best is None or key > best[0]:
                best = (
                    key,
                    "counterfactual_rescue_gate",
                    rescue_config_to_save,
                    {
                        "old_weights": {
                            fk: config["factors"][fk]["weight"]
                            for fk in _active_factor_keys(config)
                            if fk in config.get("factors", {})
                        },
                        "new_weights": {
                            fk: config["factors"][fk]["weight"]
                            for fk in _active_factor_keys(config)
                            if fk in config.get("factors", {})
                        },
                        "correlations": correlations,
                        "changes": {
                            "counterfactual_rescue_gate": {
                                "method": "rescue_high_score_candidates_blocked_by_limited_hard_rules",
                                **rescue_params,
                            }
                        },
                    },
                    rescue_bt,
                    rescue_reason,
                    rescue_eval.get("train_backtest"),
                    rescue_eval.get("validation_backtest"),
                )

        neighbor_rescue_params = {
            "rescue_score_threshold": 65,
            "max_blockers": 1,
            "min_rescue_score_advantage": 0,
            "allowed_blocker_prefixes": ("F2_volume_price_sync<min",),
            "required_blocker_prefixes": ("F2_volume_price_sync<min",),
            "rescue_min_factor_scores": {
                "F3_technical_pattern": 75,
                "F4_tail_rally_strength": 65,
                "F8_overnight_risk_control": 70,
                "F9_overheat_control": 85,
            },
            "rescue_when_base_absent_only": True,
            "neighbor_factor_keys": (
                "F1_tail_fund_inflow",
                "F3_technical_pattern",
                "F4_tail_rally_strength",
                "F7_float_mv_fit",
                "F8_overnight_risk_control",
                "F9_overheat_control",
            ),
            "nearest_neighbor_count": 3,
            "min_prior_neighbors": 2,
            "min_neighbor_win_rate": 0.6,
            "min_neighbor_avg_return": 0,
        }
        rank_floor_neighbor_rescue_params = {
            **neighbor_rescue_params,
            "rescue_score_threshold": 60,
            "max_blockers": 2,
            "allowed_blocker_prefixes": (
                "F2_volume_price_sync<min",
                "F9_overheat_control<min",
            ),
            "required_blocker_prefixes": (
                "F2_volume_price_sync<min",
                "F9_overheat_control<min",
            ),
            "rescue_min_factor_scores": {
                "F1_tail_fund_inflow": 80,
                "F3_technical_pattern": 75,
                "F4_tail_rally_strength": 70,
                "F8_overnight_risk_control": 70,
            },
            "rescue_max_factor_scores": {
                "F9_overheat_control": 85,
            },
            "min_rescue_score_rank": 6,
            "nearest_neighbor_count": 1,
            "min_prior_neighbors": 1,
            "min_neighbor_win_rate": 1.0,
        }
        f7_empty_only_neighbor_rescue_params = {
            **neighbor_rescue_params,
            "rescue_score_threshold": 65,
            "max_blockers": 1,
            "allowed_blocker_prefixes": ("F7_float_mv_fit>max",),
            "required_blocker_prefixes": ("F7_float_mv_fit>max",),
            "rescue_min_factor_scores": {
                "F3_technical_pattern": 75,
                "F4_tail_rally_strength": 60,
                "F8_overnight_risk_control": 75,
                "F9_overheat_control": 80,
            },
            "rescue_when_base_absent_only": True,
            "neighbor_factor_keys": (
                "F1_tail_fund_inflow",
                "F3_technical_pattern",
                "F4_tail_rally_strength",
                "F7_float_mv_fit",
                "F8_overnight_risk_control",
                "F9_overheat_control",
            ),
            "nearest_neighbor_count": 3,
            "min_prior_neighbors": 2,
            "min_neighbor_win_rate": 0.6,
            "min_neighbor_avg_return": 0,
        }
        f7_empty_only_guarded_neighbor_rescue_params = {
            **f7_empty_only_neighbor_rescue_params,
            "rescue_max_factor_scores": {
                "F1_tail_fund_inflow": 80,
                "F7_float_mv_fit": 90,
            },
        }
        neighbor_param_sets = [
            (
                "neighbor_counterfactual_rescue_gate",
                "audit_similar_prior_blocked_candidates_before_rescue",
                neighbor_rescue_params,
            ),
            (
                "neighbor_counterfactual_rescue_rank_floor_gate",
                "rescue_late_rank_f2_f9_blockers_only_after_prior_win",
                rank_floor_neighbor_rescue_params,
            ),
            (
                "neighbor_counterfactual_rescue_f7_empty_only_gate",
                "rescue_f7_cap_blocked_empty_days_after_prior_neighbor_edge",
                f7_empty_only_neighbor_rescue_params,
            ),
            (
                "neighbor_counterfactual_rescue_f7_empty_only_guarded_gate",
                "rescue_f7_empty_days_with_f1_and_f7_upper_guards",
                f7_empty_only_guarded_neighbor_rescue_params,
            ),
        ]
        for neighbor_name, neighbor_method, active_neighbor_params in neighbor_param_sets:
            neighbor_rescue_bt = backtest_neighbor_counterfactual_rescue_pool(
                candidate_samples,
                config,
                **active_neighbor_params,
            )
            if use_walk_forward and train_samples and validation_samples:
                neighbor_rescue_train_bt = backtest_neighbor_counterfactual_rescue_pool(
                    train_samples,
                    config,
                    **active_neighbor_params,
                )
                neighbor_rescue_validation_bt = backtest_neighbor_counterfactual_rescue_pool(
                    validation_samples,
                    config,
                    **active_neighbor_params,
                )
                accepted, neighbor_rescue_reason = evaluate_walk_forward_candidate(
                    old_train_bt,
                    neighbor_rescue_train_bt,
                    old_validation_bt,
                    neighbor_rescue_validation_bt,
                    old_candidate_bt,
                    neighbor_rescue_bt,
                )
                neighbor_rescue_eval = {
                    "name": neighbor_name,
                    "backtest": _compact_backtest(neighbor_rescue_bt),
                    "train_backtest": _compact_backtest(neighbor_rescue_train_bt),
                    "validation_backtest": _compact_backtest(neighbor_rescue_validation_bt),
                    "neighbor_rescue_config": active_neighbor_params,
                }
            else:
                accepted, neighbor_rescue_reason = evaluate_optimization_candidate(
                    old_candidate_bt,
                    neighbor_rescue_bt,
                )
                neighbor_rescue_eval = {
                    "name": neighbor_name,
                    "backtest": _compact_backtest(neighbor_rescue_bt),
                    "neighbor_rescue_config": active_neighbor_params,
                }
            neighbor_rescue_eval.update({
                "accepted": accepted,
                "reason": neighbor_rescue_reason,
            })
            evaluated_candidates.append(neighbor_rescue_eval)
            if neighbor_name == "neighbor_counterfactual_rescue_f7_empty_only_guarded_gate":
                legacy_eval = dict(neighbor_rescue_eval)
                legacy_eval["name"] = "counterfactual_rescue_f7_empty_only_guarded_gate"
                legacy_eval["rescue_config"] = legacy_eval.get("neighbor_rescue_config", {})
                evaluated_candidates.append(legacy_eval)
            if accepted:
                neighbor_rescue_config_to_save = json.loads(json.dumps(config))
                neighbor_rescue_config_to_save.setdefault("selection", {})["neighbor_counterfactual_rescue"] = {
                    "enabled": True,
                    **active_neighbor_params,
                }
                key = _candidate_selection_key(neighbor_rescue_eval, neighbor_rescue_eval["backtest"])
                if best is None or key > best[0]:
                    best = (
                        key,
                        neighbor_name,
                        neighbor_rescue_config_to_save,
                        {
                            "old_weights": {
                                fk: config["factors"][fk]["weight"]
                                for fk in _active_factor_keys(config)
                                if fk in config.get("factors", {})
                            },
                            "new_weights": {
                                fk: config["factors"][fk]["weight"]
                                for fk in _active_factor_keys(config)
                                if fk in config.get("factors", {})
                            },
                            "correlations": correlations,
                            "changes": {
                                neighbor_name: {
                                    "method": neighbor_method,
                                    **active_neighbor_params,
                                }
                            },
                        },
                        neighbor_rescue_bt,
                        neighbor_rescue_reason,
                        neighbor_rescue_eval.get("train_backtest"),
                        neighbor_rescue_eval.get("validation_backtest"),
                    )

    if best is not None:
        _, candidate_name, candidate_config, candidate_log, candidate_bt, reason, train_bt, validation_bt = best
        return {
            "selected": True,
            "accepted": True,
            "reason": reason,
            "candidate_name": candidate_name,
            "config": candidate_config,
            "change_log": candidate_log,
            "old_candidate_backtest": old_candidate_bt,
            "new_candidate_backtest": candidate_bt,
            "train_backtest": train_bt,
            "validation_backtest": validation_bt,
            "evaluated_candidates": evaluated_candidates,
        }

    # 兜底：没有候选通过
    new_cfg, log = adjust_weights(config, correlations)
    fallback_bt = backtest_candidate_pool(candidate_samples, new_cfg) if candidate_samples else {}
    fallback_accept, fallback_reason = (
        evaluate_optimization_candidate(old_candidate_bt, fallback_bt)
        if candidate_samples else (False, "缺少候选池，无法做候选池候选回测")
    )
    return {
        "selected": True if not candidate_samples else False,
        "accepted": bool(fallback_accept),
        "reason": fallback_reason,
        "candidate_name": "learned_weight_fallback",
        "config": new_cfg,
        "change_log": log,
        "old_candidate_backtest": old_candidate_bt,
        "new_candidate_backtest": fallback_bt,
        "train_backtest": old_train_bt,
        "validation_backtest": old_validation_bt,
        "evaluated_candidates": evaluated_candidates,
    }


# ---------------------------------------------------------------------------
# 版本管理
# ---------------------------------------------------------------------------

def bump_version(current: str) -> str:
    """版本号 +0.0.1。"""
    parts = current.split(".")
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts)
    return current + ".1"


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def optimize_weekly() -> dict:
    """周度优化主流程。"""
    config = _load_json(CONFIG_PATH)
    trades = _load_trades()
    samples = _load_samples()
    opt = config.get("optimization", {})

    # 样本检查
    min_samples = opt.get("min_samples", 20)
    if len(trades) < min_samples:
        return {
            "status": "skipped",
            "reason": f"样本不足: {len(trades)} < {min_samples}",
            "trades_count": len(trades),
        }

    review_window = opt.get("review_window", 30)
    recent_trades = sorted(trades, key=lambda x: x.get("buy_date", ""), reverse=True)[:review_window]

    # 排序损失分析
    correlations = compute_factor_correlations(recent_trades)
    ranking_loss = compute_ranking_loss(recent_trades)

    # 回测验证
    recent_dates = {t.get("buy_date") or t.get("date") for t in recent_trades}
    recent_candidate_samples = [
        s for s in samples
        if s.get("candidate_pool") and (s.get("date") in recent_dates or not recent_dates)
    ]
    all_candidate_samples = [s for s in samples if s.get("candidate_pool")]
    train_samples, validation_samples = split_walk_forward_samples(
        all_candidate_samples,
        validation_ratio=opt.get("walk_forward_validation_ratio", 0.3),
        min_validation_samples=opt.get("walk_forward_min_validation_samples", 20),
    )
    candidate_samples = (
        all_candidate_samples
        if train_samples and validation_samples
        else recent_candidate_samples
    )
    evaluated_candidates = []
    if candidate_samples:
        validation_mode = (
            "walk_forward_candidate_pool"
            if train_samples and validation_samples
            else "candidate_pool_reselect"
        )
        cycle_result = _run_candidate_selection_cycle(
            config,
            correlations,
            candidate_samples,
            train_samples,
            validation_samples,
            bool(train_samples and validation_samples),
        )
        old_candidate_bt = cycle_result.get("old_candidate_backtest", {})
        new_candidate_bt = cycle_result.get("new_candidate_backtest", {})
        old_winrate = old_candidate_bt["win_rate"]
        new_winrate = new_candidate_bt.get("win_rate", 0)
        new_config = cycle_result.get("config", config)
        change_log = cycle_result.get("change_log", {
            "old_weights": {},
            "new_weights": {},
            "correlations": correlations,
            "changes": {},
        })
        evaluated_candidates = cycle_result.get("evaluated_candidates", [])
        accepted = bool(cycle_result.get("accepted"))
        acceptance_reason = cycle_result.get("reason", "没有候选参数通过准入；保留当前策略")
        optimization_method = cycle_result.get("candidate_name", "none_accepted")
    else:
        new_config, change_log = adjust_weights(config, correlations)
        old_candidate_bt = {}
        new_candidate_bt = {}
        old_winrate = backtest_with_weights(recent_trades, config)
        new_winrate = backtest_with_weights(recent_trades, new_config)
        validation_mode = "selected_trade_only"
        optimization_method = "factor_correlation_weights"
        accepted = new_winrate > old_winrate
        acceptance_reason = (
            f"胜率 {old_winrate:.2%}→{new_winrate:.2%}"
            if accepted else f"未真实改善胜率 {old_winrate:.2%}→{new_winrate:.2%}"
        )

    # 恶化则回滚
    if opt.get("rollback_if_worse", True) and not accepted:
        return {
            "status": "rolled_back",
            "reason": acceptance_reason,
            "correlations": correlations,
            "ranking_loss": ranking_loss,
            "change_log": change_log,
            "validation_mode": validation_mode,
            "old_candidate_backtest": old_candidate_bt,
            "new_candidate_backtest": new_candidate_bt,
            "evaluated_candidates": evaluated_candidates,
        }

    # 保存新配置
    new_config["version"] = bump_version(config.get("version", "1.0.0"))
    new_config["updated_at"] = dt.datetime.now().isoformat()
    _save_json(CONFIG_PATH, new_config)

    # 追加版本日志
    version_info = _load_json(VERSION_PATH)
    current_version = new_config["version"]
    next_optimize = (dt.datetime.now() + dt.timedelta(days=7)).strftime("%Y-%m-%d")

    version_entry = {
        "version": current_version,
        "change_date": dt.datetime.now().strftime("%Y-%m-%d"),
        "reason": "周度排序损失优化",
        "factor_rho": correlations,
        "ranking_loss": ranking_loss,
        "old_winrate": round(old_winrate, 4),
        "new_winrate": round(new_winrate, 4),
        "weights_before": change_log["old_weights"],
        "weights_after": change_log["new_weights"],
        "validation_mode": validation_mode,
        "optimization_method": optimization_method,
        "old_candidate_backtest": _compact_backtest(old_candidate_bt),
        "new_candidate_backtest": _compact_backtest(new_candidate_bt),
        "acceptance_reason": acceptance_reason,
        "evaluated_candidates": _compact_evaluated_candidates(evaluated_candidates, limit=10),
    }

    history = version_info.get("history", [])
    history.append(version_entry)
    version_info = {
        "version": current_version,
        "next_optimize_date": next_optimize,
        "history": history,
        "updated_at": dt.datetime.now().isoformat(),
    }
    _save_json(VERSION_PATH, version_info)

    return {
        "status": "optimized",
        "old_version": config.get("version"),
        "new_version": current_version,
        "ranking_loss": ranking_loss,
        "old_winrate": round(old_winrate, 4),
        "new_winrate": round(new_winrate, 4),
        "correlations": correlations,
        "weights_before": change_log["old_weights"],
        "weights_after": change_log["new_weights"],
        "next_optimize_date": next_optimize,
        "validation_mode": validation_mode,
        "optimization_method": optimization_method,
        "old_candidate_backtest": old_candidate_bt,
        "new_candidate_backtest": new_candidate_bt,
        "acceptance_reason": acceptance_reason,
        "evaluated_candidates": evaluated_candidates,
    }


def optimize_iterative(
    rounds: int = 3,
    walk_forward_ratio: float = 0.3,
    min_validation_samples: int = 20,
) -> dict:
    """多轮迭代优化：训练样本回看 + 验证集正向检验。"""
    config = _load_json(CONFIG_PATH)
    baseline_config = json.loads(json.dumps(config))
    trades = _load_trades()
    samples = _load_samples()
    opt = config.get("optimization", {})

    min_samples = opt.get("min_samples", 20)
    if len(trades) < min_samples:
        return {
            "status": "skipped",
            "reason": f"样本不足: {len(trades)} < {min_samples}",
            "trades_count": len(trades),
            "rounds_executed": 0,
        }

    rounds = max(1, int(rounds))
    rounds = min(rounds, 10)

    # 用历史样本切分训练/验证集，确保 latest 是验证
    recent_trades = sorted(trades, key=lambda x: x.get("buy_date", ""), reverse=True)[: max(2, opt.get("review_window", 30))]
    recent_dates = {t.get("buy_date") or t.get("date") for t in recent_trades}
    all_candidate_samples = [s for s in samples if s.get("candidate_pool")]
    train_samples = []
    validation_samples = []
    if all_candidate_samples:
        train_samples, validation_samples = split_walk_forward_samples(
            sorted(all_candidate_samples, key=lambda s: str(s.get("date", ""))),
            validation_ratio=walk_forward_ratio,
            min_validation_samples=min_validation_samples,
        )
    candidate_samples = (
        all_candidate_samples
        if train_samples and validation_samples
        else [s for s in all_candidate_samples if s.get("date") in recent_dates or s.get("candidate_pool")]
    )

    baseline_set = []
    for sid in [
        s for s in candidate_samples
        if s.get("candidate_pool")
    ]:
        if sid.get("candidate_pool"):
            baseline_set.append(sid)
    if not baseline_set:
        return {
            "status": "skipped",
            "reason": "候选池样本不足，无法做迭代重选",
            "trades_count": len(trades),
            "rounds_executed": 0,
        }
    candidate_samples = baseline_set

    # 记录每一轮进展
    rounds_result = []
    current_config = config
    use_walk_forward = bool(train_samples and validation_samples)
    validation_mode = "walk_forward" if use_walk_forward else "candidate_pool_reselect"
    improvement_mode = "iterative"
    accepted_round_count = 0
    last_reason = ""
    next_optimize = (dt.datetime.now() + dt.timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        import feedback_loop
    except Exception:
        feedback_loop = None

    for i in range(1, rounds + 1):
        # 最新训练样本相关性 + 轮次快照
        correlations = compute_factor_correlations([t for t in trades if "return" in t])
        ranking_loss = compute_ranking_loss([t for t in trades if "return" in t])

        pre_sid = None
        if feedback_loop is not None:
            try:
                pre_sid = feedback_loop.collect_metrics(
                    label=f"iter_round{i}_pre",
                )
            except Exception:
                pre_sid = None

        cycle = _run_candidate_selection_cycle(
            current_config,
            correlations,
            candidate_samples,
            train_samples,
            validation_samples,
            use_walk_forward,
        )

        candidate_name = cycle["candidate_name"]
        new_config = cycle["config"]
        change_log = cycle["change_log"]
        cycle_old = cycle["old_candidate_backtest"]
        cycle_new = cycle["new_candidate_backtest"]
        cycle_reason = cycle["reason"]
        cycle_ok = cycle["accepted"]
        if change_log.get("new_weights"):
            weights_changed = change_log.get("new_weights") != change_log.get("old_weights")
        else:
            weights_changed = cycle_old != cycle_new

        candidate_delta = {
            "round": i,
            "method": candidate_name,
            "accepted": cycle_ok,
            "accepted_reason": cycle_reason,
            "old_win_rate": round(cycle_old.get("win_rate", 0), 4) if cycle_old else None,
            "new_win_rate": round(cycle_new.get("win_rate", 0), 4) if cycle_new else None,
            "old_avg_return": round(cycle_old.get("avg_return", 0), 4) if cycle_old else None,
            "new_avg_return": round(cycle_new.get("avg_return", 0), 4) if cycle_new else None,
            "old_max_loss": cycle_old.get("max_consecutive_loss"),
            "new_max_loss": cycle_new.get("max_consecutive_loss"),
            "train_backtest": _compact_backtest(cycle.get("train_backtest", {})),
            "validation_backtest": _compact_backtest(cycle.get("validation_backtest", {})),
            "evaluated_count": len(cycle.get("evaluated_candidates", [])),
            "ranking_loss": ranking_loss,
            "correlations": correlations,
            "pre_snapshot_id": pre_sid,
            "post_snapshot_id": None,
        }

        if cycle_ok and weights_changed:
            accepted_round_count += 1
            current_config = new_config
        else:
            candidate_delta["stop_reason"] = cycle_reason
            rounds_result.append(candidate_delta)
            last_reason = cycle_reason
            if i == 1:
                return {
                    "status": "rolled_back",
                    "reason": f"第一轮无可用改进：{cycle_reason}",
                    "rounds_executed": i,
                    "rounds_requested": rounds,
                    "rounds_result": rounds_result,
                    "validation_mode": validation_mode,
                    "improvement_mode": improvement_mode,
                    "next_optimize_date": next_optimize,
                }
            break

        if feedback_loop is not None:
            try:
                candidate_delta["post_snapshot_id"] = feedback_loop.collect_metrics(
                    label=f"iter_round{i}_post",
                )
            except Exception:
                candidate_delta["post_snapshot_id"] = None

        rounds_result.append(candidate_delta)

        # 连续停滞保护：胜率/平均收益未改善则提前退出
        if cycle_old and cycle_new:
            if (
                cycle_new.get("win_rate", 0) <= cycle_old.get("win_rate", 0)
                and cycle_new.get("avg_return", 0) <= cycle_old.get("avg_return", 0)
            ):
                last_reason = "连续轮次未继续改善，提前结束"
                break

    if accepted_round_count == 0:
        return {
            "status": "rolled_back",
            "reason": f"未通过任何一轮：{last_reason or '无可用提升'}",
            "rounds_executed": len(rounds_result),
            "rounds_requested": rounds,
            "rounds_result": rounds_result,
            "validation_mode": validation_mode,
            "improvement_mode": improvement_mode,
            "next_optimize_date": next_optimize,
        }

    # 持久化最终 config，版本+1
    new_version = bump_version(current_config.get("version", "1.0.0"))
    old_version = config.get("version")
    current_config["version"] = new_version
    current_config["updated_at"] = dt.datetime.now().isoformat()
    _save_json(CONFIG_PATH, current_config)

    # 记录版本历史
    version_info = _load_json(VERSION_PATH)
    history = version_info.get("history", [])
    last_round = rounds_result[-1] if rounds_result else {}
    version_entry = {
        "version": new_version,
        "change_date": dt.datetime.now().strftime("%Y-%m-%d"),
        "reason": "迭代训练-前向验证闭环",
        "strategy_mode": "optimize_iterative",
        "rounds_executed": len(rounds_result),
        "rounds_requested": rounds,
        "validation_mode": validation_mode,
        "improvement_mode": improvement_mode,
        "final_reason": last_round.get("accepted_reason"),
        "ranking_loss": last_round.get("ranking_loss"),
        "weights_before": baseline_config.get("factors", {}),
        "weights_after": current_config.get("factors", {}),
        "rounds_result": rounds_result,
        "last_round": last_round,
    }
    history.append(version_entry)
    version_info = {
        "version": new_version,
        "next_optimize_date": next_optimize,
        "history": history,
        "updated_at": dt.datetime.now().isoformat(),
    }
    _save_json(VERSION_PATH, version_info)

    return {
        "status": "optimized",
        "old_version": old_version,
        "new_version": new_version,
        "rounds_executed": len(rounds_result),
        "rounds_requested": rounds,
        "rounds_result": rounds_result,
        "validation_mode": validation_mode,
        "improvement_mode": improvement_mode,
        "next_optimize_date": next_optimize,
        "ranking_loss": last_round.get("ranking_loss"),
        "last_round": last_round,
        "evaluated_candidates": last_round.get("validated_evaluations", None),
    }


def optimize_balance(
    min_participation: float = 0.30,
    max_participation: float = 0.45,
    min_win_rate: float = 0.70,
    max_consecutive_loss: int = 3,
    min_avg_return: float = 0.0,
    validation_ratio: float = 0.30,
    min_validation_samples: int = 20,
) -> dict:
    """Search and persist one formal strategy balanced for win rate and participation."""
    config = _load_json(CONFIG_PATH)
    samples = [s for s in _load_samples() if s.get("candidate_pool")]
    trades = _load_trades()
    if not samples:
        return {
            "status": "skipped",
            "reason": "候选池样本不足，无法执行平衡优化",
        }

    correlations = compute_factor_correlations([t for t in trades if "return" in t])
    old_bt = backtest_candidate_pool(samples, config)
    train_samples, validation_samples = split_walk_forward_samples(
        samples,
        validation_ratio=validation_ratio,
        min_validation_samples=min_validation_samples,
    )
    old_ok, old_reason, old_score = evaluate_balance_candidate(
        old_bt,
        min_participation=min_participation,
        max_participation=max_participation,
        min_win_rate=min_win_rate,
        max_consecutive_loss=max_consecutive_loss,
        min_avg_return=min_avg_return,
    )

    best = None
    evaluated = []
    for candidate_name, candidate_config, change_log in _balance_candidate_configs(
        config,
        correlations,
        samples,
    ):
        bt = backtest_candidate_pool(samples, candidate_config)
        accepted, reason, score = evaluate_balance_candidate(
            bt,
            min_participation=min_participation,
            max_participation=max_participation,
            min_win_rate=min_win_rate,
            max_consecutive_loss=max_consecutive_loss,
            min_avg_return=min_avg_return,
        )
        item = {
            "name": candidate_name,
            "accepted": accepted,
            "reason": reason,
            "score": score,
            "backtest": _compact_backtest(bt),
        }
        candidate_train_bt = {}
        candidate_validation_bt = {}
        if accepted and train_samples and validation_samples:
            candidate_train_bt = backtest_candidate_pool(train_samples, candidate_config)
            candidate_validation_bt = backtest_candidate_pool(validation_samples, candidate_config)
            validation_ok, validation_reason, validation_score = evaluate_balance_candidate(
                candidate_validation_bt,
                min_participation=0.0,
                max_participation=1.0,
                min_win_rate=min_win_rate,
                max_consecutive_loss=max_consecutive_loss,
                min_avg_return=min_avg_return,
            )
            item["train_backtest"] = _compact_backtest(candidate_train_bt)
            item["validation_backtest"] = _compact_backtest(candidate_validation_bt)
            item["validation_score"] = validation_score
            if not validation_ok:
                item["accepted"] = False
                item["reason"] = f"最近验证段未通过：{validation_reason}"
                evaluated.append(item)
                continue
        evaluated.append(item)
        if not accepted:
            continue
        key = (
            score,
            candidate_validation_bt.get("win_rate", bt.get("win_rate", 0)) if candidate_validation_bt else bt.get("win_rate", 0),
            bt.get("win_rate", 0),
            bt.get("avg_return", 0),
            -bt.get("max_consecutive_loss", 999),
            bt.get("trade_samples", 0),
        )
        if best is None or key > best[0]:
            best = (
                key,
                candidate_name,
                candidate_config,
                change_log,
                bt,
                reason,
                score,
                candidate_train_bt,
                candidate_validation_bt,
            )

    if best is None:
        validation_rejections = [
            item for item in evaluated
            if "最近验证段" in str(item.get("reason", ""))
        ]
        rollback_reason = (
            "最近验证段未通过，拒绝落盘"
            if validation_rejections
            else "没有候选参数同时满足平衡目标"
        )
        return {
            "status": "rolled_back",
            "reason": rollback_reason,
            "target": {
                "min_participation": min_participation,
                "max_participation": max_participation,
                "min_win_rate": min_win_rate,
                "max_consecutive_loss": max_consecutive_loss,
                "min_avg_return": min_avg_return,
            },
            "old_candidate_backtest": old_bt,
            "old_balance_reason": old_reason,
            "evaluated_candidates": evaluated[:20],
        }

    _, method, new_config, change_log, new_bt, reason, balance_score, train_bt, validation_bt = best
    if old_ok and old_score >= balance_score:
        return {
            "status": "rolled_back",
            "reason": f"当前策略已满足目标且评分不低于候选：{old_reason}",
            "old_candidate_backtest": old_bt,
            "new_candidate_backtest": new_bt,
            "evaluated_candidates": evaluated[:20],
        }

    old_version = config.get("version", "1.0.0")
    new_version = bump_version(old_version)
    new_config["version"] = new_version
    new_config["updated_at"] = dt.datetime.now().isoformat()
    new_config["strategy_mode"] = "single_formal_balance"
    new_config["balance_target"] = {
        "min_participation": min_participation,
        "max_participation": max_participation,
        "min_win_rate": min_win_rate,
        "max_consecutive_loss": max_consecutive_loss,
        "min_avg_return": min_avg_return,
        "validation_ratio": validation_ratio,
        "min_validation_samples": min_validation_samples,
    }
    _save_json(CONFIG_PATH, new_config)

    next_optimize = (dt.datetime.now() + dt.timedelta(days=7)).strftime("%Y-%m-%d")
    version_info = _load_json(VERSION_PATH)
    history = version_info.get("history", [])
    history.append({
        "version": new_version,
        "change_date": dt.datetime.now().strftime("%Y-%m-%d"),
        "reason": "胜率与出手率平衡优化",
        "strategy_mode": "single_formal_balance",
        "optimization_method": method,
        "balance_target": new_config["balance_target"],
        "old_candidate_backtest": _compact_backtest(old_bt),
        "new_candidate_backtest": _compact_backtest(new_bt),
        "train_backtest": _compact_backtest(train_bt),
        "validation_backtest": _compact_backtest(validation_bt),
        "acceptance_reason": reason,
        "balance_score": balance_score,
        "weights_before": change_log.get("old_weights", {}),
        "weights_after": change_log.get("new_weights", {}),
        "change_log": change_log,
        "evaluated_candidates": evaluated[:20],
    })
    _save_json(VERSION_PATH, {
        "version": new_version,
        "next_optimize_date": next_optimize,
        "history": history,
        "updated_at": dt.datetime.now().isoformat(),
    })

    return {
        "status": "optimized",
        "old_version": old_version,
        "new_version": new_version,
        "optimization_method": method,
        "old_candidate_backtest": old_bt,
        "new_candidate_backtest": new_bt,
        "train_backtest": train_bt,
        "validation_backtest": validation_bt,
        "acceptance_reason": reason,
        "balance_score": balance_score,
        "target": new_config["balance_target"],
        "evaluated_candidates": evaluated,
        "next_optimize_date": next_optimize,
    }


def optimize_regret_zero(
    validation_ratio: float = 0.30,
    min_validation_samples: int = 20,
) -> dict:
    """Persist the candidate that most directly reduces opportunity regret."""
    config = _load_json(CONFIG_PATH)
    samples = [s for s in _load_samples() if s.get("candidate_pool")]
    trades = _load_trades()
    if not samples:
        return {
            "status": "skipped",
            "reason": "候选池样本不足，无法执行机会损失优化",
        }

    correlations = compute_factor_correlations([t for t in trades if "return" in t])
    old_bt = backtest_candidate_pool(samples, config)
    train_samples, validation_samples = split_walk_forward_samples(
        samples,
        validation_ratio=validation_ratio,
        min_validation_samples=min_validation_samples,
    )
    use_walk_forward = bool(train_samples and validation_samples)
    cycle = _run_candidate_selection_cycle(
        config,
        correlations,
        samples,
        train_samples,
        validation_samples,
        use_walk_forward,
    )

    if not cycle.get("accepted"):
        return {
            "status": "rolled_back",
            "reason": cycle.get("reason", "没有候选参数通过机会损失准入"),
            "validation_mode": "walk_forward_regret_zero" if use_walk_forward else "candidate_pool_regret_zero",
            "old_candidate_backtest": old_bt,
            "new_candidate_backtest": cycle.get("new_candidate_backtest", {}),
            "train_backtest": cycle.get("train_backtest", {}),
            "validation_backtest": cycle.get("validation_backtest", {}),
            "evaluated_candidates": _compact_evaluated_candidates(
                cycle.get("evaluated_candidates", []),
                limit=20,
            ),
        }

    old_version = config.get("version", "1.0.0")
    new_config = cycle.get("config", config)
    new_version = bump_version(old_version)
    new_config["version"] = new_version
    new_config["updated_at"] = dt.datetime.now().isoformat()
    new_config["strategy_mode"] = "regret_zero_oracle_hit"
    new_config["regret_zero_target"] = {
        "objective": "minimize_avg_regret_then_maximize_exact_best_hit_rate",
        "validation_ratio": validation_ratio,
        "min_validation_samples": min_validation_samples,
    }
    _save_json(CONFIG_PATH, new_config)

    next_optimize = (dt.datetime.now() + dt.timedelta(days=7)).strftime("%Y-%m-%d")
    version_info = _load_json(VERSION_PATH)
    history = version_info.get("history", [])
    history.append({
        "version": new_version,
        "change_date": dt.datetime.now().strftime("%Y-%m-%d"),
        "reason": "机会损失趋近0/命中次日最优优化",
        "strategy_mode": "regret_zero_oracle_hit",
        "optimization_method": cycle.get("candidate_name"),
        "regret_zero_target": new_config["regret_zero_target"],
        "old_candidate_backtest": _compact_backtest(old_bt),
        "new_candidate_backtest": _compact_backtest(cycle.get("new_candidate_backtest", {})),
        "train_backtest": _compact_backtest(cycle.get("train_backtest", {})),
        "validation_backtest": _compact_backtest(cycle.get("validation_backtest", {})),
        "acceptance_reason": cycle.get("reason"),
        "weights_before": cycle.get("change_log", {}).get("old_weights", {}),
        "weights_after": cycle.get("change_log", {}).get("new_weights", {}),
        "change_log": cycle.get("change_log", {}),
        "evaluated_candidates": _compact_evaluated_candidates(
            cycle.get("evaluated_candidates", []),
            limit=20,
        ),
    })
    _save_json(VERSION_PATH, {
        "version": new_version,
        "next_optimize_date": next_optimize,
        "history": history,
        "updated_at": dt.datetime.now().isoformat(),
    })

    return {
        "status": "optimized",
        "old_version": old_version,
        "new_version": new_version,
        "optimization_method": cycle.get("candidate_name"),
        "validation_mode": "walk_forward_regret_zero" if use_walk_forward else "candidate_pool_regret_zero",
        "old_candidate_backtest": old_bt,
        "new_candidate_backtest": cycle.get("new_candidate_backtest", {}),
        "train_backtest": cycle.get("train_backtest", {}),
        "validation_backtest": cycle.get("validation_backtest", {}),
        "acceptance_reason": cycle.get("reason"),
        "evaluated_candidates": cycle.get("evaluated_candidates", []),
        "next_optimize_date": next_optimize,
    }


def show_optimization_history() -> str:
    """打印优化历史。"""
    version_info = _load_json(VERSION_PATH)
    history = version_info.get("history", [])

    lines = ["=== 策略优化历史 ===", ""]
    lines.append(f"当前版本: {version_info.get('version', 'v1.0')}")
    lines.append(f"下次优化: {version_info.get('next_optimize_date', '未排期')}")
    lines.append(f"历史优化次数: {len(history)}")
    lines.append("")

    if not history:
        lines.append("暂无优化记录。")
        return "\n".join(lines)

    lines.append("| 版本 | 日期 | 排序损失 | 旧胜率 | 新胜率 |")
    lines.append("|------|------|----------|--------|--------|")
    for h in history[-10:]:
        lines.append(f"| {h.get('version','')} | {h.get('change_date','')} | "
                      f"{h.get('ranking_loss','-')} | {h.get('old_winrate','-')} | "
                      f"{h.get('new_winrate','-')} |")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "history":
        print(show_optimization_history())
    else:
        result = optimize_weekly()
        print(json.dumps(result, ensure_ascii=False, indent=2))
