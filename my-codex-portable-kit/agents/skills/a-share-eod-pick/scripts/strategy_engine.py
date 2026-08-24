"""
A股尾盘隔夜策略 - 核心策略引擎

多因子打分模型：
    F1 尾盘资金净流入    0.20
    F2 量价协同          0.15
    F3 技术形态          0.20
    F4 尾盘拉升强度      0.15
    F5 板块热度          0.10
    F6 消息面催化        0.10
    F7 流通市值适配      0.10

综合 Score = Σ(wi × Fi)，归一化到 [0,100]。
"""

import json
import copy
import math
import datetime as dt
from pathlib import Path
from typing import Any
from collections import Counter

import pandas as pd
import numpy as np

import data_loader

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
_ALLOWED_SECTIONS = ("_factor_",)


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def apply_runtime_overrides(config: dict, overrides: dict | None = None) -> dict:
    """Return a copied config with one-off CLI overrides applied."""
    adjusted = copy.deepcopy(config)
    applied = {}
    overrides = overrides or {}
    if "F2_volume_price_sync_min" in overrides:
        value = float(overrides["F2_volume_price_sync_min"])
        min_scores = adjusted.setdefault("selection", {}).setdefault("min_factor_scores", {})
        before = min_scores.get("F2_volume_price_sync")
        min_scores["F2_volume_price_sync"] = value
        applied["F2_volume_price_sync_min"] = {"before": before, "after": value}
    if "score_threshold" in overrides:
        value = float(overrides["score_threshold"])
        selection = adjusted.setdefault("selection", {})
        before = selection.get("score_threshold")
        selection["score_threshold"] = value
        applied["score_threshold"] = {"before": before, "after": value}
    if "F8_overnight_risk_control_min" in overrides:
        value = float(overrides["F8_overnight_risk_control_min"])
        min_scores = adjusted.setdefault("selection", {}).setdefault("min_factor_scores", {})
        before = min_scores.get("F8_overnight_risk_control")
        min_scores["F8_overnight_risk_control"] = value
        applied["F8_overnight_risk_control_min"] = {"before": before, "after": value}
    if "F9_overheat_control_min" in overrides:
        value = float(overrides["F9_overheat_control_min"])
        min_scores = adjusted.setdefault("selection", {}).setdefault("min_factor_scores", {})
        before = min_scores.get("F9_overheat_control")
        min_scores["F9_overheat_control"] = value
        applied["F9_overheat_control_min"] = {"before": before, "after": value}
    if applied:
        adjusted["runtime_overrides"] = applied
    return adjusted


# ---------------------------------------------------------------------------
# 预过滤
# ---------------------------------------------------------------------------

def prefilter(stock_features: dict, config: dict) -> tuple[bool, str]:
    """硬约束预过滤。返回 (是否通过, 原因)。"""
    pf = config["prefilter"]
    rt = stock_features.get("realtime")
    if not rt:
        return False, "无实时行情"

    price = rt.get("price", 0)
    if price <= 0:
        return False, "价格为0"
    if not (pf["price_min"] <= price <= pf["price_max"]):
        return False, f"价格{price}不在[{pf['price_min']},{pf['price_max']}]"

    amount = rt.get("amount", 0)
    if amount < pf["amount_min"]:
        return False, f"成交额{amount/1e4:.0f}万<{pf['amount_min']/1e4:.0f}万"

    # 涨跌停剔除
    if pf["exclude_limit_up_down"]:
        pct = rt.get("pct_change", 0)
        if pct >= 0.097:
            return False, "涨停"
        if pct <= -0.097:
            return False, "跌停"

    # 日K样本不足（仅在已加载 daily_k 时检查，预过滤阶段传 None 跳过）
    daily_k = stock_features.get("daily_k")
    if daily_k is not None and len(daily_k) < pf["listed_days_min"]:
        return False, f"上市不足{pf['listed_days_min']}日"

    # 流通市值范围（仅在已加载 float_mv 时检查，预过滤阶段未加载则跳过）
    float_mv = stock_features.get("float_mv", 0)
    if float_mv > 0:
        if not (pf["float_mv_min"] <= float_mv <= pf["float_mv_max"]):
            return False, f"流通市值{float_mv/1e8:.1f}亿不在[{pf['float_mv_min']/1e8:.0f},{pf['float_mv_max']/1e8:.0f}]亿"

    return True, "ok"


def passes_factor_guardrails(scored_stock: dict, config: dict) -> tuple[bool, str]:
    """综合分之后的因子风控门槛。"""
    selection = config.get("selection", {})
    factors = scored_stock.get("factor_scores", {})
    for key, min_value in selection.get("min_factor_scores", {}).items():
        value = factors.get(key, {}).get("score", scored_stock.get(key, 0))
        if float(value or 0) < float(min_value):
            return False, f"{key}低于{min_value}"
    for key, max_value in selection.get("max_factor_scores", {}).items():
        value = factors.get(key, {}).get("score", scored_stock.get(key, 0))
        if float(value or 0) > float(max_value):
            return False, f"{key}高于{max_value}"
    return True, "ok"


def guardrail_block_reason(scored_stock: dict, config: dict) -> str:
    ok, reason = passes_factor_guardrails(scored_stock, config)
    return "" if ok else reason


def build_selection_diagnostics(
    scored: list[dict],
    errors: list[str],
    config: dict,
    threshold: float,
    watch_limit: int = 10,
) -> tuple[dict, list[dict]]:
    blockers = Counter()
    below_score = 0
    for item in scored:
        if item.get("score", 0) < threshold:
            below_score += 1
        reason = guardrail_block_reason(item, config)
        if reason:
            blockers[reason] += 1

    error_counts = Counter()
    for err in errors:
        if "fund_flow" in err:
            error_counts["fund_flow"] += 1
        elif "tail" in err:
            error_counts["tail_minutes"] += 1
        elif "daily_k" in err:
            error_counts["daily_k"] += 1
        else:
            error_counts["other"] += 1

    watchlist = []
    for item in scored[:watch_limit]:
        reason = guardrail_block_reason(item, config)
        if item.get("score", 0) < threshold and not reason:
            reason = f"score低于{threshold}"
        watchlist.append({
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "score": item.get("score", 0),
            "sector": item.get("sector", ""),
            "block_reason": reason or "已达观察条件",
            "F2_volume_price_sync": item.get("F2_volume_price_sync", 0),
            "F3_technical_pattern": item.get("F3_technical_pattern", 0),
            "F8_overnight_risk_control": item.get("F8_overnight_risk_control", 0),
        })

    return {
        "total_scored": len(scored),
        "below_score_threshold": below_score,
        "guardrail_blockers": dict(blockers),
        "error_counts": dict(error_counts),
    }, watchlist


def _is_strong_market_for_f2_rescue(market_overview: dict, rescue_config: dict) -> bool:
    sh_pct = _safe_float(market_overview.get("sh_pct"))
    up = _safe_float(market_overview.get("limit_up_count"))
    down = _safe_float(market_overview.get("limit_down_count"))
    min_sh_pct = _safe_float(rescue_config.get("min_sh_pct"), 0.003)
    min_up = _safe_float(rescue_config.get("min_limit_up_count"), 50)
    max_down = _safe_float(rescue_config.get("max_limit_down_count"), 15)
    return sh_pct >= min_sh_pct and up >= min_up and down <= max_down


def _guardrail_blockers(scored_stock: dict, config: dict) -> list[str]:
    selection = config.get("selection", {})
    factors = scored_stock.get("factor_scores", {})
    blockers = []
    for key, min_value in selection.get("min_factor_scores", {}).items():
        value = factors.get(key, {}).get("score", scored_stock.get(key, 0))
        if float(value or 0) < float(min_value):
            blockers.append(f"{key}低于{min_value}")
    for key, max_value in selection.get("max_factor_scores", {}).items():
        value = factors.get(key, {}).get("score", scored_stock.get(key, 0))
        if float(value or 0) > float(max_value):
            blockers.append(f"{key}高于{max_value}")
    return blockers


def _strong_market_f2_rescue_candidate(
    opportunity_signals: list[dict],
    config: dict,
    market_overview: dict,
    used_sectors: set[str] | None = None,
) -> dict | None:
    selection = config.get("selection", {}) or {}
    rescue = selection.get("strong_market_f2_rescue", {}) or {}
    if not rescue.get("enabled", True):
        return None
    if not _is_strong_market_for_f2_rescue(market_overview, rescue):
        return None

    allowed_actions = set(rescue.get("allowed_actions") or ["BUY_NOW", "TAIL_CONFIRM"])
    min_opp = _safe_float(rescue.get("min_opportunity_score"), 78.0)
    min_score = _safe_float(rescue.get("min_score"), 40.0)
    max_f2_blockers = int(rescue.get("max_blockers", 1) or 1)
    used_sectors = used_sectors or set()
    for sig in opportunity_signals:
        if sig.get("action") not in allowed_actions:
            continue
        if _safe_float(sig.get("opportunity_score")) < min_opp:
            continue
        if _safe_float(sig.get("score")) < min_score:
            continue
        if sig.get("sector") in used_sectors:
            continue
        blockers = _guardrail_blockers(sig, config)
        if not blockers:
            continue
        if len(blockers) > max_f2_blockers:
            continue
        if any(not blocker.startswith("F2_volume_price_sync低于") for blocker in blockers):
            continue
        rescued = dict(sig)
        rescued["selection_mode"] = "strong_market_f2_rescue"
        risks = list(rescued.get("risks") or [])
        if "F2不足由强市场救援" not in risks:
            risks.append("F2不足由强市场救援")
        rescued["risks"] = risks
        reasons = list(rescued.get("reasons") or [])
        reasons.append("强市场环境下高机会分，允许F2降级为风险提示")
        rescued["reasons"] = reasons
        return rescued
    return None


def select_formal_picks(
    scored: list[dict],
    opportunity_signals: list[dict],
    config: dict,
    market_overview: dict | None = None,
    mode: str | None = "balanced",
) -> list[dict]:
    """Select formal recommendations from score guardrails plus live opportunity rescue."""
    selection = config.get("selection", {}) or {}
    threshold = _safe_float(selection.get("score_threshold"), 60.0)
    top_n = int(selection.get("top_n", 1) or 1)
    max_per_sector = int(selection.get("max_per_sector", 1) or 1)
    picked = []
    used_sectors = set()
    for item in scored:
        if _safe_float(item.get("score")) < threshold:
            continue
        ok, _ = passes_factor_guardrails(item, config)
        if not ok:
            continue
        if item.get("sector") in used_sectors and max_per_sector <= len(
                [p for p in picked if p.get("sector") == item.get("sector")]):
            continue
        picked.append(item)
        used_sectors.add(item.get("sector"))
        if len(picked) >= top_n:
            break

    formal_picks = list(picked)
    normalized_mode = _normalize_strategy_mode(mode)
    if normalized_mode != "tail-only":
        buy_now = [s for s in opportunity_signals if s.get("action") == "BUY_NOW"]
        if buy_now:
            best_buy = buy_now[0]
            if not formal_picks or best_buy.get("symbol") != formal_picks[0].get("symbol"):
                formal_picks = [best_buy]
            else:
                formal_picks[0] = {**formal_picks[0], **best_buy}
        elif not formal_picks:
            rescued = _strong_market_f2_rescue_candidate(
                opportunity_signals,
                config,
                market_overview or {},
                used_sectors,
            )
            if rescued:
                formal_picks = [rescued]
    return formal_picks[:top_n]


def _normalize_strategy_mode(mode: str | None) -> str:
    value = str(mode or "balanced").strip().lower()
    if value in {"tail", "tail_only", "tail-only"}:
        return "tail-only"
    if value == "attack":
        return "attack"
    return "balanced"


def _factor_score(item: dict, key: str, default: float = 50.0) -> float:
    fs = item.get("factor_scores") or {}
    value = fs.get(key)
    if isinstance(value, dict):
        value = value.get("score")
    if value is None:
        value = item.get(key)
    return _safe_float(value, default)


def _action_label(action: str) -> str:
    return {
        "BUY_NOW": "现在可买",
        "WAIT_RECHECK": "等待复核",
        "TAIL_CONFIRM": "尾盘确认",
        "NO_TRADE": "放弃",
    }.get(action, action)


def _case_label(strategy_case: str) -> str:
    return {
        "intraday_attack": "盘中机会",
        "tail_confirm": "尾盘隔夜推荐",
        "watch_only": "观察",
        "no_trade": "不交易",
    }.get(strategy_case, strategy_case)


def _parse_hhmm(value: str | None) -> dt.time | None:
    try:
        hh, mm = str(value or "").split(":")[:2]
        return dt.time(int(hh), int(mm))
    except Exception:
        return None


def _next_recheck_time(config: dict, now: dt.time | None = None) -> str:
    checkpoints = (config.get("execution_revisit", {}) or {}).get("checkpoints") or []
    now = now or dt.datetime.now().time()
    for item in checkpoints:
        checkpoint = _parse_hhmm(str(item))
        if checkpoint is None:
            continue
        if checkpoint > now:
            return str(item)
    return ""


def _format_hhmm(value: dt.time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


def _add_minutes(base: dt.datetime, minutes: int) -> dt.time:
    return (base + dt.timedelta(minutes=max(1, int(minutes)))).time().replace(second=0, microsecond=0)


def _min_future_time(*values: dt.time | None) -> dt.time | None:
    future = [value for value in values if value is not None]
    return min(future) if future else None


def _time_in_window(now: dt.time, start: str | None, end: str | None) -> bool:
    start_time = _parse_hhmm(start)
    end_time = _parse_hhmm(end)
    if start_time is None or end_time is None:
        return False
    return start_time <= now <= end_time


def _time_after_window(now: dt.time, end: str | None) -> bool:
    end_time = _parse_hhmm(end)
    if end_time is None:
        return False
    return now > end_time


def _time_before_market_close(now: dt.time) -> bool:
    return now < dt.time(15, 0)


def _dynamic_recheck_time(
    profile: dict,
    config: dict,
    now_dt: dt.datetime,
    next_checkpoint: str,
    in_tail_window: bool,
    after_tail_window: bool,
    before_market_close: bool,
) -> str:
    """Return a candidate-specific next review time from the current tape state."""
    now = now_dt.time()
    if not before_market_close or in_tail_window or after_tail_window:
        return ""

    revisit = config.get("execution_revisit", {}) or {}
    tail_window = config.get("execution_advice", {}) or {}
    tail_start = _parse_hhmm(tail_window.get("window_start", "14:40"))
    next_checkpoint_time = _parse_hhmm(next_checkpoint)

    pct_change = _safe_float(profile.get("pct_change"))
    position = _safe_float(profile.get("position_in_range"), 0.5)
    drawdown = _safe_float(profile.get("drawdown_from_high"))
    tail_return = _safe_float(profile.get("tail_return"))
    tail_volume_share = _safe_float(profile.get("tail_volume_share"))
    volume_ratio = _safe_float(profile.get("volume_ratio"), 1.0)

    weakening = (
        drawdown >= 0.024
        or tail_return <= -0.002
        or (position < 0.50 and pct_change > 0.012)
    )
    nearly_confirming = (
        0.018 <= pct_change <= 0.075
        and drawdown <= 0.018
        and position >= 0.55
        and (volume_ratio >= 1.1 or tail_volume_share >= 0.07 or tail_return >= 0.002)
    )
    hot_watch = nearly_confirming and (position >= 0.65 or volume_ratio >= 1.2 or tail_volume_share >= 0.10)

    if weakening:
        interval = int(revisit.get("weak_recheck_minutes", 5) or 5)
    elif hot_watch:
        interval = int(revisit.get("hot_recheck_minutes", 5) or 5)
    elif nearly_confirming:
        interval = int(revisit.get("alive_recheck_minutes", 12) or 12)
    else:
        interval = int(revisit.get("default_recheck_minutes", 15) or 15)

    dynamic_time = _add_minutes(now_dt, interval)
    cap_time = tail_start if hot_watch else _min_future_time(next_checkpoint_time, tail_start)
    if cap_time is not None and dynamic_time > cap_time:
        dynamic_time = cap_time
    if dynamic_time <= now:
        return ""
    return _format_hhmm(dynamic_time)


def _candidate_recheck_decision(
    profile: dict,
    opp_score: float,
    next_check: str,
    in_tail_window: bool,
    after_tail_window: bool,
    before_market_close: bool = True,
    dynamic_next_check: str | None = None,
) -> tuple[str, str, str, str, str]:
    """Choose action/recheck from the candidate's live tape state."""
    pct_change = _safe_float(profile.get("pct_change"))
    position = _safe_float(profile.get("position_in_range"), 0.5)
    drawdown = _safe_float(profile.get("drawdown_from_high"))
    tail_return = _safe_float(profile.get("tail_return"))
    tail_volume_share = _safe_float(profile.get("tail_volume_share"))
    volume_ratio = _safe_float(profile.get("volume_ratio"), 1.0)

    strengthening = (
        0.012 <= pct_change <= 0.075
        and 0.48 <= position <= 0.88
        and drawdown <= 0.02
        and (volume_ratio >= 1.2 or tail_volume_share >= 0.10 or tail_return >= 0.004)
    )
    incomplete_but_alive = (
        opp_score >= 52.0
        and drawdown <= 0.028
        and pct_change < 0.085
        and (position >= 0.45 or tail_return >= 0.002)
    )

    if strengthening and (in_tail_window or (after_tail_window and before_market_close) or not next_check):
        return "TAIL_CONFIRM", "tail_confirm", "", "tail_advice_price", "分时承接仍在，当前进入确认窗口"
    candidate_next_check = dynamic_next_check if dynamic_next_check is not None else next_check
    if incomplete_but_alive and candidate_next_check:
        return "WAIT_RECHECK", "watch_only", candidate_next_check, "none", "强度未完整确认，按实时盘面等待下一次复核"
    if in_tail_window:
        return "TAIL_CONFIRM", "tail_confirm", "", "tail_advice_price", "已进入尾盘窗口，按实时承接确认"
    if after_tail_window and before_market_close and incomplete_but_alive:
        return "TAIL_CONFIRM", "tail_confirm", "", "tail_advice_price", "已过建议窗口但仍在收盘前，按实时盘面做最后确认"
    if after_tail_window or not candidate_next_check:
        return "NO_TRADE", "no_trade", "", "none", "已无后续复核窗口，且当前盘面未形成买点"
    return "WAIT_RECHECK", "watch_only", candidate_next_check, "none", "盘面未恶化，等待下一次复核"


def _opportunity_score(item: dict, market_overview: dict, mode: str) -> tuple[float, list[str], list[str]]:
    profile = item.get("intraday_profile") or item.get("timing_profile") or {}
    pct_change = _safe_float(profile.get("pct_change"))
    position = _safe_float(profile.get("position_in_range"), 0.5)
    drawdown = _safe_float(profile.get("drawdown_from_high"))
    tail_return = _safe_float(profile.get("tail_return"))
    tail_volume_share = _safe_float(profile.get("tail_volume_share"))
    volume_ratio = _safe_float(profile.get("volume_ratio"), 1.0)
    score = _safe_float(item.get("score"))
    sector_heat = _factor_score(item, "F5_sector_heat")
    f8 = _factor_score(item, "F8_overnight_risk_control")
    f9 = _factor_score(item, "F9_overheat_control")
    sh_pct = _safe_float(market_overview.get("sh_pct"))
    up = _safe_float(market_overview.get("limit_up_count"))
    down = _safe_float(market_overview.get("limit_down_count"))

    reasons = []
    risks = []
    price_score = 0.0
    if 0.018 <= pct_change <= 0.075:
        price_score = 22.0
        reasons.append(f"当前涨幅{pct_change:.2%}处于进攻区间")
    elif 0.008 <= pct_change < 0.018:
        price_score = 12.0
        reasons.append(f"当前涨幅{pct_change:.2%}仍偏温和")
    elif pct_change > 0.085:
        price_score = 5.0
        risks.append(f"涨幅{pct_change:.2%}接近过热，避免追高")
    else:
        price_score = 6.0
        risks.append(f"涨幅{pct_change:.2%}未形成明确强度")

    position_score = 0.0
    if 0.55 <= position <= 0.86 and drawdown <= 0.018:
        position_score = 20.0
        reasons.append(f"分时位置{position:.0%}且距高点回撤{drawdown:.2%}")
    elif position > 0.90 and pct_change >= 0.04:
        position_score = 7.0
        risks.append(f"接近日内高位，区间位置{position:.0%}")
    elif drawdown >= 0.03:
        position_score = 3.0
        risks.append(f"冲高回落，距高点回撤{drawdown:.2%}")
    else:
        position_score = 10.0

    volume_score = 0.0
    if volume_ratio >= 1.8 or tail_volume_share >= 0.15:
        volume_score = 22.0
        reasons.append(f"量能扩张，量比{volume_ratio:.2f}，尾盘量占比{tail_volume_share:.2%}")
    elif volume_ratio >= 1.2 or tail_volume_share >= 0.10:
        volume_score = 14.0
        reasons.append(f"量能有所放大，量比{volume_ratio:.2f}")
    else:
        volume_score = 5.0
        risks.append("量能确认不足")

    sector_score = 16.0 if sector_heat >= 75 else (10.0 if sector_heat >= 60 else 5.0)
    if sector_heat >= 75:
        reasons.append(f"板块热度较强，F5={sector_heat:.1f}")
    elif sector_heat < 55:
        risks.append(f"板块联动一般，F5={sector_heat:.1f}")

    risk_score = 14.0 if f8 >= 55 and f9 >= 45 else (8.0 if f8 >= 40 and f9 >= 30 else 2.0)
    if f8 < 40 or f9 < 30:
        risks.append(f"隔夜/过热风控偏弱，F8={f8:.1f}，F9={f9:.1f}")

    market_score = 6.0 if sh_pct >= 0.003 and up >= max(down * 1.5, 20) else (3.0 if sh_pct >= -0.008 else 0.0)
    if market_score >= 6:
        reasons.append("市场环境偏强")
    elif sh_pct < -0.008:
        risks.append(f"指数偏弱，上证{sh_pct:.2%}")

    base_score = min(8.0, max(0.0, score - 40.0) * 0.4)
    total = price_score + position_score + volume_score + sector_score + risk_score + market_score + base_score
    if mode == "attack":
        total += 4.0
    return round(max(0.0, min(100.0, total)), 2), reasons[:4], risks[:4]


def build_opportunity_signals(
    scored: list[dict],
    config: dict,
    market_overview: dict | None = None,
    mode: str | None = "balanced",
    limit: int = 5,
    decision_time: dt.datetime | None = None,
) -> list[dict]:
    """Build independent intraday/tail opportunity decisions from scored candidates."""
    normalized_mode = _normalize_strategy_mode(mode)
    market_overview = market_overview or {}
    signals = []
    tail_window = config.get("execution_advice", {}) or {}
    tail_text = f"{tail_window.get('window_start', '14:40')}-{tail_window.get('window_end', '14:55')}"
    decision_dt = decision_time or dt.datetime.now()
    now = decision_dt.time()
    next_check = _next_recheck_time(config, now=now)
    in_tail_window = _time_in_window(now, tail_window.get("window_start", "14:40"), tail_window.get("window_end", "14:55"))
    after_tail_window = _time_after_window(now, tail_window.get("window_end", "14:55"))
    before_market_close = _time_before_market_close(now)

    for item in scored:
        opp_score, reasons, risks = _opportunity_score(item, market_overview, normalized_mode)
        profile = item.get("intraday_profile") or item.get("timing_profile") or {}
        pct_change = _safe_float(profile.get("pct_change"))
        drawdown = _safe_float(profile.get("drawdown_from_high"))
        position = _safe_float(profile.get("position_in_range"), 0.5)
        volume_ratio = _safe_float(profile.get("volume_ratio"), 1.0)
        dynamic_next_check = _dynamic_recheck_time(
            profile,
            config,
            decision_dt,
            next_check,
            in_tail_window,
            after_tail_window,
            before_market_close,
        )
        over_chase = pct_change >= 0.087 or (position >= 0.92 and pct_change >= 0.045)
        reversal = drawdown >= 0.035
        if normalized_mode == "tail-only":
            action = "TAIL_CONFIRM"
            strategy_case = "tail_confirm"
            signal_next_check = "" if in_tail_window or after_tail_window else tail_window.get("window_start", "14:40")
            entry_source = "tail_advice_price"
            reasons = reasons or [f"仅执行尾盘窗口 {tail_text}"]
        elif over_chase or reversal:
            action = "NO_TRADE"
            strategy_case = "no_trade"
            signal_next_check = dynamic_next_check
            entry_source = "none"
            if over_chase:
                risks.append("接近涨停/日内高位，不追高")
            if reversal:
                risks.append("冲高回落超过风控线")
        elif opp_score >= (72.0 if normalized_mode == "balanced" else 68.0) and volume_ratio >= 1.2:
            action = "BUY_NOW"
            strategy_case = "intraday_attack"
            signal_next_check = ""
            entry_source = "current_price"
        elif opp_score >= 52.0:
            action, strategy_case, signal_next_check, entry_source, timing_reason = _candidate_recheck_decision(
                profile,
                opp_score,
                next_check,
                in_tail_window,
                after_tail_window,
                before_market_close,
                dynamic_next_check,
            )
            reasons.append(timing_reason)
            if action == "NO_TRADE":
                risks.append(timing_reason)
        else:
            if after_tail_window and not before_market_close:
                action = "NO_TRADE"
                strategy_case = "no_trade"
                signal_next_check = ""
                entry_source = "none"
                risks.append("已过收盘时间，无法再执行尾盘确认")
            else:
                action = "TAIL_CONFIRM"
                strategy_case = "tail_confirm"
                signal_next_check = "" if in_tail_window or after_tail_window else tail_window.get("window_start", "14:40")
                entry_source = "tail_advice_price"

        signal = {
            **item,
            "opportunity_score": opp_score,
            "action": action,
            "action_label": _action_label(action),
            "strategy_case": strategy_case,
            "case_label": _case_label(strategy_case),
            "entry_price_source": entry_source,
            "next_check_at": signal_next_check,
            "decision_time": decision_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "reasons": reasons or [f"综合机会分{opp_score:.1f}"],
            "risks": risks or ["未触发明显风险"],
        }
        signals.append(signal)

    action_rank = {"BUY_NOW": 0, "WAIT_RECHECK": 1, "TAIL_CONFIRM": 2, "NO_TRADE": 3}
    signals.sort(key=lambda s: (action_rank.get(s.get("action"), 9), -s.get("opportunity_score", 0), -s.get("score", 0)))
    return signals[:limit]


def _ordered_factor_keys(config: dict) -> list[str]:
    """按配置顺序返回因子 keys，忽略非字典配置项。"""
    factors = config.get("factors", {})
    return [k for k, v in factors.items() if isinstance(v, dict)]


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 因子计算
# ---------------------------------------------------------------------------

def calc_F1_tail_fund_inflow(stock_features: dict, config: dict) -> float:
    """F1 尾盘资金净流入。

    主力净额 / 流通市值，归一化到 0-100。
    """
    ff = stock_features.get("fund_flow", {})
    if not ff:
        return 50.0

    main_net = ff.get("main_net", 0)  # 万元
    rt = stock_features.get("realtime", {})
    amount = rt.get("amount", 0)

    if amount <= 0:
        return 50.0

    # 主力净流入占成交额比例
    main_pct = main_net * 1e4 / amount if amount > 0 else 0
    # 映射：[-10%, 10%] → [0, 100]
    score = 50 + main_pct * 500  # 10% → 100, -10% → 0
    return float(np.clip(score, 0, 100))


def calc_F2_volume_price_sync(stock_features: dict, config: dict) -> float:
    """F2 量价协同。

    尾盘量比 × 涨跌幅一致性。
    """
    tail = stock_features.get("tail_minutes")
    rt = stock_features.get("realtime", {})
    daily_k = stock_features.get("daily_k")

    if tail is None or tail.empty or daily_k is None or len(daily_k) < 5:
        return 50.0

    # 尾盘量比 = 尾盘30分钟均量 / 前5日均量
    tail_vol = tail["volume"].sum() if "volume" in tail.columns else 0
    recent_vol = daily_k["volume"].tail(5).mean() if "volume" in daily_k.columns else 0
    if recent_vol <= 0:
        return 50.0
    # 尾盘30分钟占全日比例
    tail_ratio = tail_vol / recent_vol if recent_vol > 0 else 0
    # 量比得分：1.0 → 50, 2.0 → 100, 0.5 → 0
    vol_score = np.clip((tail_ratio - 0.5) / 1.5 * 100, 0, 100)

    # 量价同向：尾盘放量且价格上涨
    if len(tail) >= 2:
        price_change = (tail.iloc[-1]["close"] - tail.iloc[0]["open"]) / tail.iloc[0]["open"]
        # 价涨量增 → 高分
        if tail_vol > recent_vol / 8 and price_change > 0:
            consistency = 70 + min(30, price_change * 1000)
        elif price_change > 0:
            consistency = 60
        else:
            consistency = 40
    else:
        consistency = 50

    score = vol_score * 0.6 + consistency * 0.4
    return float(np.clip(score, 0, 100))


def calc_F3_technical_pattern(stock_features: dict, config: dict) -> float:
    """F3 技术形态。

    MACD 信号 + RSI 区间 + 均线排列。
    """
    daily_k = stock_features.get("daily_k")
    if daily_k is None or len(daily_k) < 30:
        return 50.0

    close = daily_k["close"].astype(float)

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_hist = (dif - dea) * 2

    macd_score = 50
    if len(macd_hist) >= 2:
        # 金叉或柱体转正
        if dif.iloc[-1] > dea.iloc[-1]:
            macd_score = 70
            if dif.iloc[-1] > 0:  # 零轴上方
                macd_score = 90
        elif dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]:
            macd_score = 40  # 死叉
        else:
            macd_score = 55
        # 柱体放大
        if macd_hist.iloc[-1] > macd_hist.iloc[-2]:
            macd_score += 5
        macd_score = np.clip(macd_score, 0, 100)

    # RSI(14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50

    # RSI 区间 [40,60] 为强势整理，最理想
    if 40 <= rsi_val <= 60:
        rsi_score = 90
    elif 50 <= rsi_val <= 70:
        rsi_score = 75
    elif 30 <= rsi_val < 40:
        rsi_score = 60
    elif rsi_val > 70:
        rsi_score = 40  # 超买
    else:
        rsi_score = 30  # 超卖

    # 均线排列
    ma5 = close.rolling(5).mean().iloc[-1]
    ma10 = close.rolling(10).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    last_close = close.iloc[-1]

    ma_score = 50
    if last_close > ma5 > ma10:
        ma_score = 75
        if ma5 > ma20 and ma10 > ma20:
            ma_score = 90  # 多头排列
    elif last_close < ma5 < ma10:
        ma_score = 30
    else:
        ma_score = 55

    # 加权
    score = macd_score * 0.4 + rsi_score * 0.3 + ma_score * 0.3
    return float(np.clip(score, 0, 100))


def calc_F4_tail_rally_strength(stock_features: dict, config: dict) -> float:
    """F4 尾盘拉升强度。

    (15:00价 - 14:30价) / 14:30价 × 尾盘成交占比
    """
    tail = stock_features.get("tail_minutes")
    rt = stock_features.get("realtime", {})

    if tail is None or tail.empty or len(tail) < 2:
        return 50.0

    price_1430 = tail.iloc[0]["open"]
    price_1500 = tail.iloc[-1]["close"]
    if price_1430 <= 0:
        return 50.0

    rally_pct = (price_1500 - price_1430) / price_1430
    # 拉升幅度得分：0% → 50, 1% → 70, 2% → 90, -1% → 30
    rally_score = 50 + rally_pct * 2000
    rally_score = np.clip(rally_score, 0, 100)

    # 尾盘成交占比（占全日）
    tail_amount = tail["amount"].sum() if "amount" in tail.columns else 0
    total_amount = rt.get("amount", 0)
    if total_amount > 0:
        share = tail_amount / total_amount
        # 尾盘放量：>20% 为高，<10% 为低
        share_score = np.clip((share - 0.1) / 0.15 * 100, 0, 100)
    else:
        share_score = 50

    score = rally_score * 0.7 + share_score * 0.3
    return float(np.clip(score, 0, 100))


def calc_F5_sector_heat(stock_features: dict, config: dict, sector_perf: pd.DataFrame) -> float:
    """F5 板块热度。

    所属行业当日涨幅排名 + 龙头联动。
    """
    sector = stock_features.get("sector", "未知")
    if sector_perf is None or sector_perf.empty or sector == "未知":
        return 50.0

    # 行业排名得分
    if "sector" in sector_perf.columns and "pct_change" in sector_perf.columns:
        matched = sector_perf[sector_perf["sector"] == sector]
        if matched.empty:
            return 50.0
        rank = sector_perf["pct_change"].rank(ascending=False)
        idx = matched.index[0]
        rank_pos = rank.loc[idx]  # 1=最好
        total = len(sector_perf)
        # 排名前 10% → 90-100，后 10% → 0-10
        rank_score = (1 - (rank_pos - 1) / total) * 100
    else:
        rank_score = 50

    return float(np.clip(rank_score, 0, 100))


def calc_F6_news_catalyst(stock_features: dict, config: dict) -> float:
    """F6 消息面催化。

    简化版：基于资金流向和涨幅推断。
    完整版可接入巨潮公告/东财研报。
    """
    ff = stock_features.get("fund_flow", {})
    rt = stock_features.get("realtime", {})

    default = config["factors"]["F6_news_catalyst"].get("default_no_news", 50)

    # 主力净流入大且涨幅适中 → 隐含利好
    main_pct = ff.get("main_net_pct", 0)
    pct_change = rt.get("pct_change", 0)

    if main_pct > 0.1 and 0 < pct_change < 0.05:
        return 75  # 资金驱动型利好
    if main_pct > 0.05 and pct_change > 0.03:
        return 70
    if main_pct < -0.1:
        return 35  # 资金流出隐含利空
    return default


def calc_F7_float_mv_fit(stock_features: dict, config: dict) -> float:
    """F7 流通市值适配。

    高斯分布，中位偏好 20 亿（按 SKILL.md 设计 mu=ln(20e8), sigma=0.6）。
    优先用真实流通市值（东财 f117），降级用近20日均成交额近似。
    """
    # 优先真实流通市值
    float_mv = stock_features.get("float_mv", 0)
    if float_mv > 0:
        mu = math.log(20e8)  # 中位 20 亿流通市值
        sigma = 0.6
        x = math.log(float_mv)
        score = math.exp(-0.5 * ((x - mu) / sigma) ** 2) * 100
        return float(np.clip(score, 0, 100))

    # 降级：用近20日均成交额近似
    daily_k = stock_features.get("daily_k")
    if daily_k is None or len(daily_k) < 5:
        return 50.0

    avg_amount = daily_k["amount"].tail(20).mean() if "amount" in daily_k.columns else 0
    if avg_amount <= 0:
        return 50.0

    mu = math.log(2e8)  # 中位 2 亿成交额
    sigma = 0.8
    x = math.log(max(avg_amount, 1))

    score = math.exp(-0.5 * ((x - mu) / sigma) ** 2) * 100
    return float(np.clip(score, 0, 100))


def calc_F10_trend_momentum(stock_features: dict, config: dict) -> float:
    """F10 趋势动能：短中期斜率 + 均线结构。"""
    daily_k = stock_features.get("daily_k")
    if daily_k is None or len(daily_k) < 30:
        return 50.0

    close = daily_k["close"].astype(float)
    if close.empty or close.iloc[-1] <= 0:
        return 50.0

    # 近中期动能斜率（越高越强）
    rt = stock_features.get("realtime", {})
    last = float(rt.get("price", close.iloc[-1]) or 0)
    close_5 = float(close.iloc[-6]) if len(close) >= 6 else float(close.iloc[0])
    close_20 = float(close.iloc[-21]) if len(close) >= 21 else float(close.iloc[0])
    if close_5 > 0 and close_20 > 0:
        mom_5 = (last - close_5) / close_5
        mom_20 = (last - close_20) / close_20
    else:
        mom_5 = 0.0
        mom_20 = 0.0

    ma5 = float(close.rolling(5).mean().iloc[-1])
    ma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else ma5

    trend_score = np.clip((mom_5 / 0.06) * 30, -30, 30)  # 6% 左右映射到 ±30
    long_score = np.clip((mom_20 / 0.12) * 30, -20, 20)   # 12% 左右映射到 ±20
    ma_score = 20.0 if last > ma5 > ma20 else (-20.0 if last < ma5 < ma20 else 0.0)
    score = 50.0 + trend_score + long_score + ma_score
    return float(np.clip(score, 0, 100))


def calc_F11_financial_quality(stock_features: dict, config: dict) -> float:
    """F11 财务质量：优先用财务字段，不可得则基于价格-成交结构中性退化。"""
    financial = stock_features.get("financial", {})
    if financial:
        roe = _safe_float(financial.get("roe"), default=0.0)
        gross_margin = _safe_float(financial.get("gross_margin"), default=0.0)
        debt_ratio = _safe_float(financial.get("debt_to_asset"), default=0.5)
        revenue_growth = _safe_float(financial.get("revenue_growth"), default=0.0)

        # 典型区间兜底映射
        roe_score = np.clip(50 + roe * 2.5, 0, 100)  # 20% -> 100
        margin_score = np.clip(50 + gross_margin * 1.2, 0, 100)  # 40% -> 98
        debt_score = np.clip(100 - debt_ratio * 100, 0, 100)     # 低负债更高分
        growth_score = np.clip(50 + revenue_growth * 80, 0, 100) # 60% -> 98
        score = 0.35 * roe_score + 0.25 * margin_score + 0.2 * debt_score + 0.2 * growth_score
        return float(np.clip(score, 0, 100))

    # 退化为价格-量能代理：高波动/重估值倾向降分，稳定适中偏中性
    rt = stock_features.get("realtime", {})
    k = stock_features.get("daily_k")
    if k is None or len(k) < 10:
        return 50.0

    close = k["close"].astype(float)
    vols = k["volume"].astype(float)
    amt = k["amount"].astype(float)
    ret = close.pct_change().fillna(0.0).tail(10)
    vol_change = (vols.iloc[-1] / max(vols.tail(20).mean(), 1e-6)) if len(vols) >= 20 else 1.0
    stability = max(0.0, 1.0 - min(float(ret.std()), 0.12) / 0.12)  # 12%波动作为坏端
    proxy_score = np.clip(50 + (50 * np.tanh(ret.tail(1).iloc[0] * 8)), 0, 100)
    score = np.clip((proxy_score * 0.4) + (50 * stability * 0.4) + (50 * min(max(2 - vol_change, -1), 1) * 1.2), 0, 100)
    return float(np.clip(score, 0, 100))


def calc_F12_market_sentiment(stock_features: dict, config: dict) -> float:
    """F12 情绪：涨幅与尾盘/量能分歧，结合波动进行打分。"""
    daily_k = stock_features.get("daily_k")
    if daily_k is None or daily_k.empty:
        return 50.0

    close = daily_k["close"].astype(float)
    open_p = daily_k["open"].astype(float)
    high = daily_k["high"].astype(float)
    low = daily_k["low"].astype(float)
    volume = daily_k["volume"].astype(float)
    rt = stock_features.get("realtime", {})

    if close.empty or open_p.empty:
        return 50.0

    if len(daily_k) >= 2:
        ret_1d = (close.iloc[-1] - close.iloc[-2]) / max(close.iloc[-2], 1e-6)
    else:
        ret_1d = _safe_float(rt.get("pct_change"), default=0.0)

    if len(close) >= 10:
        avg_amount = float(volume.tail(10).mean())
    else:
        avg_amount = float(volume.mean())
    amount = float(volume.iloc[-1]) if not volume.empty else avg_amount
    vol_signal = (amount / avg_amount) if avg_amount > 0 else 1.0
    vol_signal = np.clip((vol_signal - 1.0) * 18 + 50, 0, 100)

    if len(daily_k) >= 2:
        intraday_amp = float((high.iloc[-1] - low.iloc[-1]) / max(close.iloc[-1], 1e-6))
    else:
        intraday_amp = 0.0
    range_penalty = np.clip(intraday_amp * 350, 0, 25)
    sentiment = 50 + ret_1d * 250 + (vol_signal - 50) * 0.4 - range_penalty
    return float(np.clip(sentiment, 0, 100))


# ---------------------------------------------------------------------------
# 综合打分
# ---------------------------------------------------------------------------

FACTOR_FUNCS = {
    "F1_tail_fund_inflow": calc_F1_tail_fund_inflow,
    "F2_volume_price_sync": calc_F2_volume_price_sync,
    "F3_technical_pattern": calc_F3_technical_pattern,
    "F4_tail_rally_strength": calc_F4_tail_rally_strength,
    "F5_sector_heat": calc_F5_sector_heat,
    "F6_news_catalyst": calc_F6_news_catalyst,
    "F7_float_mv_fit": calc_F7_float_mv_fit,
    "F10_trend_momentum": calc_F10_trend_momentum,
    "F11_financial_quality": calc_F11_financial_quality,
    "F12_market_sentiment": calc_F12_market_sentiment,
}


def score_stock(stock_features: dict, config: dict, sector_perf: pd.DataFrame) -> dict:
    """计算单只股票的全部因子分与综合得分。

    返回：
        symbol, F1..F7, score, factor_details
    """
    result = {"symbol": stock_features["symbol"]}
    total = 0.0
    factor_details = {}

    for fkey in _ordered_factor_keys(config):
        func = FACTOR_FUNCS.get(fkey)
        if not callable(func):
            result[fkey] = 50.0
            factor_details[fkey] = {"score": 50.0, "weight": config["factors"].get(fkey, {}).get("weight", 0.0), "weighted": 0.0}
            continue

        weight = config["factors"].get(fkey, {}).get("weight", 0.0)
        try:
            if fkey == "F5_sector_heat":
                fscore = func(stock_features, config, sector_perf)
            else:
                fscore = func(stock_features, config)
        except Exception as e:
            print(f"[strategy] {fkey} 计算失败 {stock_features['symbol']}: {e}")
            fscore = 50.0
        result[fkey] = round(fscore, 2)
        factor_details[fkey] = {
            "score": round(fscore, 2),
            "weight": weight,
            "weighted": round(fscore * weight, 2),
        }
        total += fscore * weight

    result["score"] = round(total, 2)
    result["factor_details"] = factor_details
    result["intraday_profile"] = build_intraday_profile(stock_features)
    return result


def build_intraday_profile(stock_features: dict) -> dict:
    """Summarize same-day price action for execution timing advice."""
    realtime = stock_features.get("realtime") or {}
    tail = stock_features.get("tail_minutes")

    price = _safe_float(realtime.get("price"))
    high = _safe_float(realtime.get("high"))
    low = _safe_float(realtime.get("low"))
    pre_close = _safe_float(realtime.get("pre_close"))
    pct_change = _safe_float(realtime.get("pct_change"))
    if pct_change and abs(pct_change) > 1:
        pct_change = pct_change / 100
    if pct_change == 0 and pre_close > 0 and price > 0:
        pct_change = price / pre_close - 1

    position = 0.5
    drawdown = 0.0
    if high > low and price > 0:
        position = max(0.0, min(1.0, (price - low) / (high - low)))
    if high > 0 and price > 0:
        drawdown = max(0.0, (high - price) / high)

    tail_return = 0.0
    tail_volume_share = 0.0
    if tail is not None and not tail.empty and len(tail) >= 2:
        try:
            first = tail.iloc[0]
            last = tail.iloc[-1]
            start_price = _safe_float(first.get("open", first.get("close")))
            end_price = _safe_float(last.get("close"))
            if start_price > 0 and end_price > 0:
                tail_return = end_price / start_price - 1
            if "amount" in tail.columns:
                tail_amount = float(tail["amount"].fillna(0).sum())
                day_amount = _safe_float(realtime.get("amount"))
                if day_amount > 0:
                    tail_volume_share = max(0.0, min(1.0, tail_amount / day_amount))
        except Exception:
            pass

    return {
        "pct_change": round(pct_change, 4),
        "position_in_range": round(position, 4),
        "tail_return": round(tail_return, 4),
        "tail_volume_share": round(tail_volume_share, 4),
        "drawdown_from_high": round(drawdown, 4),
        "volume_ratio": _safe_float(realtime.get("volume_ratio"), 1.0),
    }


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 主流程：选股
# ---------------------------------------------------------------------------

def run_selection(max_universe: int = 200, overrides: dict | None = None, mode: str | None = "balanced") -> dict:
    """执行完整选股流程。

    返回：
        date, recommendations: list[dict], market_overview, config_version,
        data_sources, errors
    """
    config = apply_runtime_overrides(load_config(), overrides)
    mode = _normalize_strategy_mode(mode)
    decision_dt = dt.datetime.now()
    today = decision_dt.strftime("%Y-%m-%d")
    decision_time = decision_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 1. 市场概览
    market_overview = data_loader.get_index_overview()

    # 大盘大跌空仓
    if (config["selection"].get("allow_empty_when_market_drop", True)
            and market_overview.get("sh_pct", 0) < config["selection"]["market_drop_threshold"]):
        return {
            "date": today,
            "recommendations": [],
            "market_overview": market_overview,
            "config_version": config["version"],
            "empty_reason": f"上证跌幅{market_overview['sh_pct']:.2%}超过阈值，空仓",
            "strategy_mode": mode,
            "decision_time": decision_time,
            "opportunity_signals": [],
        }

    # 2. 全市场快照（含流通市值，东财直连）
    snap_df = data_loader.get_market_snapshot()
    if snap_df.empty:
        return {"date": today, "recommendations": [], "error": "无法获取全市场快照",
                "decision_time": decision_time,
                "strategy_mode": mode, "opportunity_signals": []}

    # 3. 行业板块
    sector_perf = data_loader.get_sector_performance()

    # 4. 预过滤（含流通市值范围检查）
    candidates = []
    for _, row in snap_df.iterrows():
        sym = str(row.get("symbol", "")).zfill(6)
        if not sym:
            continue
        mini_features = {
            "symbol": sym,
            "realtime": {
                "price": float(row.get("price", 0)),
                "amount": float(row.get("amount", 0)),
                "pct_change": float(row.get("pct_change", 0)),
            },
            "daily_k": None,  # 预过滤阶段不检查长度
            "float_mv": float(row.get("float_mv", 0)),
        }
        ok, _ = prefilter(mini_features, config)
        if ok:
            candidates.append(sym)

    if not candidates:
        return {"date": today, "recommendations": [], "market_overview": market_overview,
                "empty_reason": "预过滤后无候选股票", "strategy_mode": mode,
                "decision_time": decision_time,
                "opportunity_signals": []}

    # 按成交额降序取 TOP N 深度分析
    snap_candidates = snap_df[snap_df["symbol"].isin(candidates)].sort_values(
        "amount", ascending=False)
    deep_n = config.get("max_deep_analyze", 50)
    candidates = snap_candidates["symbol"].head(deep_n).tolist()

    # 6. 深度打分（复用 snapshot 的 realtime/float_mv，避免重复请求）
    scored = []
    errors = []
    for sym in candidates:
        try:
            snap_row = snap_df[snap_df["symbol"] == sym].iloc[0]
            features = {
                "symbol": sym,
                "realtime": {
                    "price": float(snap_row.get("price", 0)),
                    "open": float(snap_row.get("open", 0)),
                    "high": float(snap_row.get("high", 0)),
                    "low": float(snap_row.get("low", 0)),
                    "pre_close": float(snap_row.get("pre_close", 0)),
                    "volume": float(snap_row.get("volume", 0)),
                    "amount": float(snap_row.get("amount", 0)),
                    "pct_change": float(snap_row.get("pct_change", 0)),
                },
                "float_mv": float(snap_row.get("float_mv", 0)),
            }
            # 补充日K、尾盘分钟、资金流向、所属行业
            try:
                features["daily_k"] = data_loader.get_daily_kline(sym, days=60)
            except Exception as e:
                features["daily_k"] = pd.DataFrame()
                errors.append(f"{sym} daily_k: {e}")
            try:
                features["tail_minutes"] = data_loader.get_tail_minutes(sym)
            except Exception as e:
                features["tail_minutes"] = pd.DataFrame()
                errors.append(f"{sym} tail: {e}")
            try:
                features["fund_flow"] = data_loader.get_fund_flow(sym)
            except Exception as e:
                features["fund_flow"] = {}
                errors.append(f"{sym} fund_flow: {e}")
            try:
                features["sector"] = data_loader.get_stock_sector(sym)
            except Exception:
                features["sector"] = "未知"

            ok, reason = prefilter(features, config)
            if not ok:
                continue
            result = score_stock(features, config, sector_perf)
            result["name"] = snap_row.get("name", "")
            result["sector"] = features.get("sector", "未知")
            scored.append(result)
        except Exception as e:
            errors.append(f"{sym} 打分失败: {e}")

    if not scored:
        return {"date": today, "recommendations": [], "market_overview": market_overview,
                "errors": errors, "empty_reason": "无股票通过深度打分",
                "decision_time": decision_time,
                "strategy_mode": mode, "opportunity_signals": []}

    # 7. 排序
    sel = config["selection"]
    scored.sort(key=lambda x: (-x["score"], -x.get("F1_tail_fund_inflow", 0),
                                -x.get("F4_tail_rally_strength", 0)))

    # 8. 阈值过滤 + 行业去重
    threshold = sel["score_threshold"]
    diagnostics, watchlist = build_selection_diagnostics(scored, errors, config, threshold)
    opportunity_signals = build_opportunity_signals(
        scored, config, market_overview, mode=mode, decision_time=decision_dt
    )
    formal_picks = select_formal_picks(
        scored,
        opportunity_signals,
        config,
        market_overview,
        mode=mode,
    )
    for rec in formal_picks:
        if "strategy_case" not in rec:
            rec["strategy_case"] = "tail_confirm"
            rec["case_label"] = _case_label("tail_confirm")
            rec["action"] = "TAIL_CONFIRM"
            rec["action_label"] = _action_label("TAIL_CONFIRM")
            rec["entry_price_source"] = "tail_advice_price"
            rec["next_check_at"] = (config.get("execution_advice", {}) or {}).get("window_start", "14:40")

    return {
        "date": today,
        "recommendations": formal_picks,
        "market_overview": market_overview,
        "config_version": config["version"],
        "decision_time": decision_time,
        "total_candidates": len(candidates),
        "total_scored": len(scored),
        "errors": errors,
        "runtime_overrides": config.get("runtime_overrides", {}),
        "selection_diagnostics": diagnostics,
        "watchlist": watchlist,
        "opportunity_signals": opportunity_signals,
        "strategy_mode": mode,
    }


if __name__ == "__main__":
    print("=== strategy_engine 选股测试 ===")
    result = run_selection(max_universe=50)
    print(f"日期: {result['date']}")
    print(f"候选: {result.get('total_candidates', 0)} / 打分: {result.get('total_scored', 0)}")
    if result.get("empty_reason"):
        print(f"空仓: {result['empty_reason']}")
    for i, rec in enumerate(result.get("recommendations", []), 1):
        print(f"  推荐{i}: {rec['symbol']} {rec.get('name','')} 得分={rec['score']} 行业={rec.get('sector')}")
        for fk in ["F1_tail_fund_inflow", "F3_technical_pattern", "F4_tail_rally_strength"]:
            print(f"    {fk}: {rec.get(fk)}")
    if result.get("errors"):
        print(f"错误({len(result['errors'])}条): {result['errors'][:3]}")
