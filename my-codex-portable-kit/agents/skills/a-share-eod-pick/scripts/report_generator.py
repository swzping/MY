"""
A股尾盘隔夜策略 - 报告生成器

生成 reports/YYYY-MM-DD.md，包含：
1. 当日市场概览
2. 策略历史胜率
3. 今日优选
4. 完整历史训练记录
5. 策略告警
"""

import json
import datetime as dt
import html
import re
from pathlib import Path

import pandas as pd

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = SKILL_ROOT / "reports"
DATA_DIR = SKILL_ROOT / "data"
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
_REAL_DATETIME = dt.datetime


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_trades() -> list[dict]:
    data = _load_json(DATA_DIR / "trades.json")
    return data.get("trades", [])


def _load_strategy_samples() -> list[dict]:
    return _load_json(DATA_DIR / "strategy_samples.json").get("samples", [])


def _load_performance() -> dict:
    return _load_json(DATA_DIR / "performance.json")


def _load_config() -> dict:
    return _load_json(CONFIG_PATH)


def _config_for_report(selection_result: dict) -> dict:
    """Apply runtime CLI overrides to the report-only config copy."""
    config = _load_config()
    overrides = selection_result.get("runtime_overrides") or {}
    if not overrides:
        return config

    selection = config.setdefault("selection", {})
    min_scores = selection.setdefault("min_factor_scores", {})
    mapping = {
        "score_threshold": ("selection", "score_threshold"),
        "F2_volume_price_sync_min": ("min", "F2_volume_price_sync"),
        "F8_overnight_risk_control_min": ("min", "F8_overnight_risk_control"),
        "F9_overheat_control_min": ("min", "F9_overheat_control"),
    }
    for override_key, target in mapping.items():
        meta = overrides.get(override_key)
        if not isinstance(meta, dict) or meta.get("after") is None:
            continue
        if target[0] == "selection":
            selection[target[1]] = meta["after"]
        elif target[0] == "min":
            min_scores[target[1]] = meta["after"]
    config["runtime_overrides"] = overrides
    return config


def _load_version() -> dict:
    return _load_json(DATA_DIR / "strategy_version.json")


def _load_latest_feedback_snapshot() -> dict:
    snapshots = _load_json(DATA_DIR / "feedback" / "metrics_snapshots.json").get("snapshots", [])
    if not snapshots:
        return {}
    return snapshots[-1]


def _fmt_pct(x: float) -> str:
    if x is None:
        return "-"
    return f"{x * 100:.2f}%"


def _fmt_amount(x: float) -> str:
    """万元为单位。"""
    if abs(x) >= 1e4:
        return f"{x/1e4:.2f}亿"
    return f"{x:.0f}万"


def _html_escape(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _json_script(value) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _fmt_value(value) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) if value else "-"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return "-"
    return str(value)


def _coerce_float(value, default=0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return default


def _rank_correlation(xs: list[float], ys: list[float]) -> float:
    """Spearman 相关系数（无需 scipy）。"""
    n = len(xs)
    if n < 3 or n != len(ys):
        return 0.0

    def ranks(values):
        ordered = sorted(enumerate(values), key=lambda kv: kv[1])
        res = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and ordered[j + 1][1] == ordered[i][1]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                res[ordered[k][0]] = avg
            i = j + 1
        return res

    rx = ranks(list(xs))
    ry = ranks(list(ys))
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = sum((a - mx) ** 2 for a in rx) ** 0.5
    deny = sum((b - my) ** 2 for b in ry) ** 0.5
    if denx == 0 or deny == 0:
        return 0.0
    return round(num / (denx * deny), 4)


def _get_factor_contrib_cfg(config: dict) -> dict:
    return dict(
        {
            "lookback_days": 30,
            "candidate_scope": "historical_training",
        },
        **(config.get("factor_contrib", {}) or {}),
    )


def _collect_factor_rows(config: dict, scope: str, lookback_days: int) -> list[dict]:
    """基于 historical_training 样本构建因子行。

    scope:
      - historical_training: 用当日实际入选样本作为基底
      - candidate_pool: 用 historical_training 的 candidate_pool（若缺失则退化到 selected）
    """
    samples = _load_strategy_samples()
    by_date = []
    for s in samples:
        if s.get("sample_type") != "historical_training":
            continue
        by_date.append(s)
    by_date = sorted(by_date, key=lambda x: x.get("date") or x.get("buy_date") or "")[-lookback_days:]

    rows: list[dict] = []
    factor_keys = list((config.get("factors") or {}).keys())

    for s in by_date:
        if scope == "candidate_pool":
            candidate_pool = s.get("candidate_pool") or []
            source_rows = candidate_pool if candidate_pool else [s]
            for c in source_rows:
                fs = c.get("factor_scores") or {}
                if not fs:
                    continue
                row = {
                    "factor_scores": fs,
                    "return": _coerce_float(c.get("return", 0)),
                    "win": bool(c.get("win", c.get("return", 0) > 0)),
                    "source": str(s.get("date") or s.get("buy_date", "")),
                    "selected_symbol": s.get("symbol", ""),
                }
                if all(k in fs for k in ["score"]):
                    row["score"] = fs.get("score", c.get("score", 0))
                rows.append(row)
            continue

        fs = s.get("factor_scores")
        if not fs:
            continue
        row = {
            "factor_scores": fs,
            "return": _coerce_float(s.get("return", 0)),
            "win": bool(s.get("win", s.get("return", 0) > 0)),
            "score": _coerce_float(s.get("score", 0)),
            "source": "selected",
            "selected_symbol": s.get("symbol", ""),
        }
        rows.append(row)

    # 保留 factor_scores 中不存在但在配置里声明的因子字段
    # （避免后续过滤时被遗漏）
    if not factor_keys:
        for r in rows:
            factor_keys.extend(k for k in r.get("factor_scores", {}) if k.startswith("F"))
    return rows


def _calc_factor_contrib_rows(
    config: dict,
    period_days: int | None = None,
    scope: str | None = None,
) -> list[dict]:
    cfg = _get_factor_contrib_cfg(config)
    scope = scope or cfg["candidate_scope"]
    days = _coerce_float(cfg.get("lookback_days", 30), 30) if period_days is None else period_days
    rows = _collect_factor_rows(config, scope, int(days))
    factors = list((config.get("factors") or {}).keys())
    weights = {k: _coerce_float((config.get("factors", {}).get(k) or {}).get("weight"), 0) for k in factors}
    selection = config.get("selection", {})
    thresholds = {
        "min": selection.get("min_factor_scores", {}) or {},
        "max": selection.get("max_factor_scores", {}) or {},
    }

    outputs = []
    n = len(rows)
    if n == 0:
        return []

    for fk in factors:
        vals = []
        rets = []
        wins = []
        for r in rows:
            fs = r.get("factor_scores", {})
            if fk not in fs:
                continue
            vals.append(_coerce_float(fs.get(fk)))
            rets.append(_coerce_float(r.get("return", 0)))
            wins.append(1.0 if bool(r.get("win", r.get("return", 0) > 0)) else 0.0)

        if not vals:
            outputs.append({
                "factor": fk,
                "samples": 0,
                "rho_return": 0.0,
                "rho_win": 0.0,
                "top30_return_gap": 0.0,
                "weighted_contrib": 0.0,
                "block_rate": 0.0,
            })
            continue

        # 相关性
        rho_return = _rank_correlation(vals, rets)
        rho_win = _rank_correlation(vals, wins)

        # 前/后30%
        order_idx = sorted(range(len(vals)), key=lambda i: vals[i])
        if len(order_idx) >= 4:
            k = max(1, int(len(order_idx) * 0.3))
            low_idx = order_idx[:k]
            high_idx = order_idx[-k:]
            low_avg = sum(rets[i] for i in low_idx) / len(low_idx)
            high_avg = sum(rets[i] for i in high_idx) / len(high_idx)
            top_gap = high_avg - low_avg
        else:
            top_gap = 0.0

        weighted = weights.get(fk, 0) * (
            sum((_coerce_float(vals[i]) - 50.0) for i in range(len(vals))) / len(vals)
        )

        # 阻挡率：离线上层阈值被打回的比例（candidate scope 下可近似）
        min_t = thresholds["min"].get(fk)
        max_t = thresholds["max"].get(fk)
        block_hits = 0
        for v in vals:
            if min_t is not None and v < _coerce_float(min_t, v):
                block_hits += 1
            if max_t is not None and v > _coerce_float(max_t, v):
                block_hits += 1
        block_rate = block_hits / len(vals) if vals else 0.0

        outputs.append({
            "factor": fk,
            "samples": len(vals),
            "rho_return": rho_return,
            "rho_win": rho_win,
            "top30_return_gap": round(top_gap, 4),
            "weighted_contrib": round(weighted, 4),
            "block_rate": round(block_rate, 4),
        })

    outputs.sort(key=lambda x: abs(x["rho_return"]) + abs(x["weighted_contrib"]) * 0.001, reverse=True)
    return outputs


def _factor_signal_label(row: dict, miss_count: int = 0) -> str:
    """根据候选池相关性与机会损失次数生成结论标签。

    候选池口径下相关性弱但阈值阻挡次数高 → "阈值偏严"，
    提示该因子阈值可能过严，错失了大量次日上涨票。
    """
    rho = row.get("rho_return", 0.0)
    rho_win = row.get("rho_win", 0.0)
    gap = row.get("top30_return_gap", 0.0)
    if miss_count >= 5 and abs(rho) < 0.08:
        return "阈值偏严"
    if abs(rho) >= 0.08 or abs(gap) >= 0.004:
        if rho > 0 or (rho_win > 0.5 and gap > 0):
            return "偏正向"
        if rho < 0 or (rho_win < 0.5 and gap < 0):
            return "偏负向"
    return "中性"


def _fmt_factor_contrib_summary(config: dict, period_days: int, factor_rows: list[dict]) -> str:
    if not factor_rows:
        return "> 当前样本不足，暂不产出因子贡献统计。"
    factor_desc = {fk: _factor_label(fk, config) for fk in config.get("factors", {}).keys()}
    blocker_map = {
        fk: cnt for fk, cnt, _ in _extract_blocker_loss_rows(_load_strategy_samples(), period_days)
    }
    lines = [f"### 因子贡献（最近{period_days}日）", ""]
    lines.append(
        "> 基于候选池全样本统计（含被阈值挡掉的票），避免幸存者偏差；"
        "机会损失次数反映该因子阈值阻挡的次日上涨票数。"
    )
    lines.append("")
    lines.append("| 因子 | 样本 | 与收益相关性 | 与胜负相关性 | 前30%-后30%收益差 | 平均加权贡献 | 阻挡命中率 | 机会损失次数 | 结论 |")
    lines.append("|------|------|--------------|--------------|-------------------|--------------|------------|-------------|------|")
    for r in factor_rows:
        name = factor_desc.get(r['factor'], r['factor'])
        miss_cnt = blocker_map.get(r['factor'], 0)
        signal = _factor_signal_label(r, miss_cnt)
        miss_str = f"{miss_cnt}次" if miss_cnt > 0 else "-"
        lines.append(
            f"| {name}({r['factor']}) | {r['samples']} | {r['rho_return']:.2f} | "
            f"{r['rho_win']:.2f} | {r['top30_return_gap']:.2%} | "
            f"{r['weighted_contrib']:.2f} | {r['block_rate']:.2%} | {miss_str} | {signal} |"
        )
    return "\n".join(lines)


def _extract_blocker_loss_rows(samples: list[dict], lookback_days: int) -> list[tuple[str, int, float]]:
    """统计硬阻挡触发样本中的高频因子及平均收益差。"""
    if not samples:
        return []

    rows: dict[str, list[float]] = {}
    for s in sorted(
        [x for x in samples if x.get("sample_type") == "historical_training" and not x.get("selected", True)],
        key=lambda x: x.get("date", ""),
        reverse=True,
    )[:lookback_days]:
        reason = str(s.get("missed_best_reason") or "")
        if not reason or "F" not in reason:
            continue
        factors = sorted(set(re.findall(r"(F\d+_[a-z_]+)", reason)))
        for fk in factors:
            rows.setdefault(fk, []).append(_coerce_float((s.get("actual_best") or {}).get("return", 0)))

    out: list[tuple[str, int, float]] = []
    for fk, gap_list in rows.items():
        if not gap_list:
            continue
        out.append((fk, len(gap_list), sum(abs(v) for v in gap_list) / len(gap_list)))

    return sorted(out, key=lambda x: (x[1], x[2]), reverse=True)


def _factor_opportunity_snapshot(config: dict, period_days: int) -> str:
    """给出容易错过机会的因子路径。"""
    blocker_rows = _extract_blocker_loss_rows(_load_strategy_samples(), period_days)
    if not blocker_rows:
        return "- 近期未见明确重复阻挡导致的错失机会样本。"

    desc = {fk: _factor_label(fk, config) for fk in config.get("factors", {}).keys()}
    lines = [f"### 机会损失点位（近{period_days}日）", ""]
    lines.append("| 因子 | 错失次数 | 平均错失幅度（样本） | 说明 |")
    lines.append("|------|---------|----------------------|------|")
    for fk, cnt, avg_abs in blocker_rows[:3]:
        lines.append(
            f"| {desc.get(fk, fk)} | {cnt} | {avg_abs:.2%} | "
            f"该因子触发后常见原因是阈值边界或上限约束，建议复核是否可放宽边界。 |"
        )
    return "\n".join(lines)


def _render_factor_contrib_section(config: dict) -> str:
    cfg = _get_factor_contrib_cfg(config)
    lookback = int(_coerce_float(cfg.get("lookback_days", 30), 30))
    if lookback <= 0:
        lookback = 30
    contrib = _calc_factor_contrib_rows(config, lookback, cfg["candidate_scope"])
    return "\n".join([
        _fmt_factor_contrib_summary(config, lookback, contrib),
        "",
        _factor_opportunity_snapshot(config, lookback),
    ])


def _render_factor_contrib_window_summary(config: dict, windows: list[int] | tuple[int, ...]) -> list[str]:
    lines = ["### 最近10/20/30日因子贡献快照"]
    if not windows:
        lines.append("> 未配置有效窗口。")
        return lines

    base_cfg = _get_factor_contrib_cfg(config)
    scope = base_cfg.get("candidate_scope", "historical_training")
    for window in windows:
        period = int(_coerce_float(window, 0))
        if period <= 0:
            continue
        rows = _calc_factor_contrib_rows(config, period, scope)
        if not rows:
            lines.append(f"- 最近{period}日：样本不足")
            continue
        top = rows[:3]
        top_desc = "；".join(
            f"{r['factor']}（rho={r['rho_return']:+.2f}, 差异={r['top30_return_gap']:+.2%}）"
            for r in top
        )
        lines.append(f"- 最近{period}日：{top_desc}")
    return lines


def _eval_early_entry_condition(
    selection_result: dict,
    rec: dict,
    config: dict,
    market: dict,
) -> tuple[str, str]:
    """
    在不改执行逻辑的前提下，输出可执行建议。

    返回：(建议文字, 触发条件)
    """
    rev = config.get("execution_revisit", {}) or {}
    advice = config.get("execution_advice", {}) or {}
    checkpoints = ", ".join((rev.get("checkpoints") or []))
    tail_window = f"{advice.get('window_start', '14:40')}-{advice.get('window_end', '14:55')}"
    score = _coerce_float(rec.get("score", 0))
    score_th = _coerce_float(rev.get("early_entry_threshold_score", 88), 88)
    sh_pct = _coerce_float(market.get("sh_pct", 0))
    up = _coerce_float(market.get("limit_up_count", 0))
    down = _coerce_float(market.get("limit_down_count", 0))

    # 风险因子边界
    min_rules = config.get("selection", {}).get("min_factor_scores", {}) or {}
    max_rules = config.get("selection", {}).get("max_factor_scores", {}) or {}
    fs = rec.get("factor_scores", {}) or {}
    fs.update({k: rec[k] for k in rec if k.startswith("F") and k in config.get("factors", {})})
    near_thresholds = []
    risk_ok = True
    for k, t in (min_rules.items()):
        vk = _coerce_float(fs.get(k))
        if vk < _coerce_float(t, vk) and vk > 0:
            risk_ok = False
            near_thresholds.append(f"{k}低于{t:.2f}（{vk:.2f}）")
    for k, t in (max_rules.items()):
        vk = _coerce_float(fs.get(k))
        if vk > _coerce_float(t, vk) and vk > 0:
            risk_ok = False
            near_thresholds.append(f"{k}高于{t:.2f}（{vk:.2f}）")

    # 近端量价失稳近似：指数波动与涨跌停集中
    market_shock = abs(sh_pct) > 0.025 or (up >= 120 and down >= 60)
    market_strong = sh_pct >= 0.003 and up >= max(down * 1.5, 20)
    market_weak = sh_pct <= -0.012 or down >= max(up * 1.2, 50)
    market_label = "今日行情偏强" if market_strong else ("今日行情偏弱" if market_weak else "今日行情震荡")

    has_explicit_intraday = bool(rec.get("intraday_profile") or rec.get("timing_profile"))
    intraday = _candidate_intraday_profile(rec)
    position = _coerce_float(intraday.get("position_in_range"), 0.5)
    tail_return = _coerce_float(intraday.get("tail_return"), 0.0)
    pct_change = _coerce_float(intraday.get("pct_change"), 0.0)
    drawdown = _coerce_float(intraday.get("drawdown_from_high"), 0.0)
    tail_volume_share = _coerce_float(intraday.get("tail_volume_share"), 0.0)
    volume_ratio = _coerce_float(intraday.get("volume_ratio"), 1.0)
    f1 = _coerce_float(fs.get("F1_tail_fund_inflow"), 50)
    f4 = _coerce_float(fs.get("F4_tail_rally_strength"), 50)
    f8 = _coerce_float(fs.get("F8_overnight_risk_control"), 50)
    f9 = _coerce_float(fs.get("F9_overheat_control"), 50)

    near_high_chase = position >= 0.92 and pct_change >= 0.035
    intraday_reversal = drawdown >= 0.03 or (tail_return <= -0.008 and position >= 0.78)
    weak_tail = tail_return < -0.003 or (tail_volume_share > 0 and tail_volume_share < 0.10 and f1 < 70)
    strong_support = (
        tail_return >= 0.003
        and 0.35 <= position <= 0.82
        and drawdown <= 0.02
        and (tail_volume_share >= 0.12 or volume_ratio >= 1.15 or f1 >= 75)
        and (has_explicit_intraday or f4 >= 65)
    )

    if not rev.get("enabled", True):
        return f"当前仅执行尾盘窗口：{tail_window}", "策略执行参数关闭提前复核"

    if market_shock or market_weak:
        return (
            f"{market_label}，不建议提前介入，保留尾盘窗口 {tail_window} 再确认。",
            f"{market_label}；指数/涨跌停结构偏风险，候选票需等尾盘承接确认",
        )

    if intraday_reversal or near_high_chase:
        reasons = []
        if intraday_reversal:
            reasons.append(f"冲高回落/尾盘转弱，距高点回撤{drawdown:.2%}，尾盘涨跌{tail_return:.2%}")
        if near_high_chase:
            reasons.append(f"接近日内高位，区间位置{position:.0%}，当日涨幅{pct_change:.2%}")
        return (
            f"暂不追高，若14:40后仍冲高回落则放弃买入；只接受回落后重新放量站稳。",
            "；".join(reasons),
        )

    if score >= score_th and risk_ok and strong_support and not market_shock:
        cond = (
            f"{market_label}；分时承接较好，区间位置{position:.0%}，"
            f"尾盘涨跌{tail_return:.2%}，量能占比{tail_volume_share:.2%}"
        )
        return (
            f"可考虑分批提前介入（建议观察时点：{checkpoints}；最终以尾盘执行口径收口）。",
            cond,
        )

    if market_shock and near_thresholds:
        return "当日市场节奏失真，不建议提前介入，建议仅按尾盘窗口执行。", "指数大波动/涨跌停集中分歧，且风控边界触发"
    if not risk_ok:
        return f"当前偏风险触发，建议仅按尾盘窗口执行；观察时点：{checkpoints}。", "关键因子触发风险边界：" + "；".join(near_thresholds[:3])
    if score >= score_th:
        weak_text = "；尾盘承接偏弱" if weak_tail else ""
        return (
            f"高分但尚未形成明确分时买点，等待 {tail_window} 尾盘确认。",
            f"{market_label}{weak_text}；区间位置{position:.0%}，尾盘涨跌{tail_return:.2%}",
        )
    return (
        f"建议继续等尾盘买入（默认窗口 {tail_window}），重点在{checkpoints}复盘。",
        f"{market_label}；分数未满足提前触发条件，当前分数{score:.2f}<{score_th:.2f}",
    )


def _candidate_intraday_profile(rec: dict) -> dict:
    """Normalize optional intraday fields from live selection into timing signals."""
    profile = dict(rec.get("intraday_profile") or rec.get("timing_profile") or {})
    realtime = rec.get("realtime") or {}
    for key in ("pct_change", "high", "low", "price", "open", "pre_close", "volume_ratio"):
        if key not in profile and key in realtime:
            profile[key] = realtime[key]
        if key not in profile and key in rec:
            profile[key] = rec[key]

    price = _coerce_float(profile.get("price") or profile.get("close"), 0)
    high = _coerce_float(profile.get("high"), 0)
    low = _coerce_float(profile.get("low"), 0)
    if "position_in_range" not in profile and high > low and price > 0:
        profile["position_in_range"] = max(0.0, min(1.0, (price - low) / (high - low)))
    if "drawdown_from_high" not in profile and high > 0 and price > 0:
        profile["drawdown_from_high"] = max(0.0, (high - price) / high)

    fs = rec.get("factor_scores") or {}
    f4 = _coerce_float(fs.get("F4_tail_rally_strength", rec.get("F4_tail_rally_strength")), 50)
    f1 = _coerce_float(fs.get("F1_tail_fund_inflow", rec.get("F1_tail_fund_inflow")), 50)
    if "tail_return" not in profile:
        profile["tail_return"] = (f4 - 50.0) / 5000.0
    if "tail_volume_share" not in profile:
        profile["tail_volume_share"] = max(0.0, min(0.3, (f1 - 40.0) / 250.0))
    if "position_in_range" not in profile:
        profile["position_in_range"] = max(0.0, min(1.0, f4 / 100.0))
    if "drawdown_from_high" not in profile:
        profile["drawdown_from_high"] = max(0.0, (100.0 - f4) / 2500.0)
    return profile


def _recommended_factor_contributions(rec: dict, config: dict, top_n: int = 4) -> list[tuple[str, float, float]]:
    factors = config.get("factors", {})
    weights = {fk: _coerce_float(meta.get("weight"), 0) for fk, meta in factors.items() if isinstance(meta, dict)}
    fs = rec.get("factor_scores") or {}
    out = []
    for fk, meta in factors.items():
        v = fs.get(fk)
        if v is None:
            continue
        v = _coerce_float(v)
        contrib = _coerce_float(weights.get(fk, 0)) * (v - 50.0)
        out.append((fk, v, contrib))
    out.sort(key=lambda x: abs(x[2]), reverse=True)
    return out[:top_n]


def _flag_risky_factors(rec: dict, config: dict) -> list[str]:
    fs = rec.get("factor_scores") or {}
    fs.update({k: rec[k] for k in rec if k.startswith("F") and k in config.get("factors", {})})
    min_rules = config.get("selection", {}).get("min_factor_scores", {}) or {}
    max_rules = config.get("selection", {}).get("max_factor_scores", {}) or {}
    risks = []
    for fk, threshold in min_rules.items():
        score = _coerce_float(fs.get(fk))
        if score < _coerce_float(threshold, score):
            risks.append(f"{fk}({score:.2f})低于阈值{threshold}")
    for fk, threshold in max_rules.items():
        score = _coerce_float(fs.get(fk))
        if score > _coerce_float(threshold, score):
            risks.append(f"{fk}({score:.2f})高于阈值{threshold}")
    return risks


def _build_symbol_name_map() -> dict[str, str]:
    names = {}
    for t in _load_trades():
        symbol = str(t.get("symbol", "")).zfill(6)
        name = str(t.get("name", "")).strip()
        if symbol and name:
            names[symbol] = name
    for s in _load_strategy_samples():
        symbol = str(s.get("symbol", "")).zfill(6)
        name = str(s.get("name", "")).strip()
        if symbol and name:
            names.setdefault(symbol, name)
    return names


def _lookup_symbol_name(symbol: str, name_map: dict[str, str]) -> str:
    symbol = str(symbol or "").zfill(6)
    if not symbol or symbol == "000000":
        return ""
    if name_map.get(symbol):
        return name_map[symbol]
    try:
        import data_loader
        quotes = data_loader.tencent_quote([symbol])
        name = str((quotes.get(symbol) or {}).get("name", "")).strip()
        if name:
            name_map[symbol] = name
            return name
    except Exception:
        pass
    return ""


def _render_market_overview(overview: dict) -> str:
    sh = overview.get("sh_pct")
    sz = overview.get("sz_pct")
    cyb = overview.get("cyb_pct")
    up_count = overview.get("limit_up_count")
    down_count = overview.get("limit_down_count")
    breadth = overview.get("market_bread")
    up = _coerce_float(up_count, 0) if up_count is not None else None
    down = _coerce_float(down_count, 0) if down_count is not None else None

    mt = _market_tone(overview)

    lines = ["## 一、当日市场概览", ""]
    lines.append("### 指数与节奏")
    lines.append(f"- 上证：{_fmt_pct(sh)}；深证：{_fmt_pct(sz)}；创业板：{_fmt_pct(cyb)}")
    lines.append(f"- 节奏判断：{mt.get('tone', '-')}，市场偏离：{mt.get('divergence', '-')}")

    lines.append("### 情绪与风控边界")
    lines.append(
        f"- 涨停：{up if up_count is not None else '不可用'}；跌停：{down if down_count is not None else '不可用'}；"
        f"偏离度：{(up - down if up is not None and down is not None else '不可用')}"
    )
    if breadth is not None:
        lines.append(f"- 市场宽度（上证净涨跌数比例）：{breadth if breadth == 0 else f'{breadth:.2f}'}")

    lines.append("### 执行数据源")
    lines.append(
        f"- 市场快照：{overview.get('source', 'unknown')} | 涨跌停口径：{overview.get('limit_source', 'unavailable')}"
    )
    lines.append(
        f"- 指数口径代码：{overview.get('quote_code', '000001/399001/399006')} | "
        f"采样时间：{overview.get('quote_time', '-') }"
    )
    if overview.get("market_bread_raw"):
        lines.append(f"- 原始宽度值：{overview.get('market_bread_raw')}")
    if overview.get("notes"):
        lines.append(f"- 补充说明：{overview.get('notes')}")
    lines.append("")
    return "\n".join(lines)


def _market_tone(overview: dict) -> dict[str, str]:
    sh = _coerce_float(overview.get("sh_pct"), 0)
    sz = _coerce_float(overview.get("sz_pct"), 0)
    cyb = _coerce_float(overview.get("cyb_pct"), 0)
    up = _coerce_float(overview.get("limit_up_count", 0), 0)
    down = _coerce_float(overview.get("limit_down_count", 0), 0)

    avg = (sh + sz + cyb) / 3
    if avg > 0.006:
        tone = "偏强"
    elif avg < -0.006:
        tone = "偏弱"
    else:
        tone = "震荡"

    divergence = "--"
    if overview.get("limit_up_count") is not None and overview.get("limit_down_count") is not None:
        divergence = f"{up - down:.0f}"

    return {"tone": tone, "divergence": divergence}


def _fmt_market_time(overview: dict) -> str:
    return str(overview.get("quote_time") or "-" )


def _render_performance(perf: dict, version_info: dict) -> str:
    lines = ["## 二、策略历史胜率", ""]
    lines.append("| 周期 | 胜率 | 盈亏比 | 最大连亏 | 样本数 |")
    lines.append("|------|------|--------|----------|--------|")

    for period in ["7d", "30d", "total"]:
        p = perf.get(period, {})
        win_rate = p.get("win_rate", 0)
        pl_ratio = p.get("pl_ratio", 0)
        max_consec = p.get("max_consecutive_loss", 0)
        samples = p.get("samples", 0)
        label = {"7d": "近7日", "30d": "近30日", "total": "总计"}[period]
        pl_str = f"1:{pl_ratio:.2f}" if pl_ratio > 0 else "-"
        lines.append(f"| {label} | {_fmt_pct(win_rate)} | {pl_str} | {max_consec} | {samples} |")

    total = perf.get("total", {})
    if "execution_coverage" in total:
        lines.append("")
        lines.append(
            "执行口径："
            f"入选 {total.get('selected_days', total.get('samples', 0))} 日，"
            f"可成交 {total.get('executable_trades', total.get('samples', 0))} 笔，"
            f"跳过 {total.get('skipped_executions', 0)} 笔，"
            f"覆盖率 {_fmt_pct(total.get('execution_coverage', 0))}。"
        )

    lines.append("")
    ver = version_info.get("version", "v1.0")
    next_opt = version_info.get("next_optimize_date", "未排期")
    lines.append(f"当前策略版本：{ver} | 下次优化日：{next_opt}")
    lines.append("")
    split_summary = _render_walk_forward_summary(version_info)
    if split_summary:
        lines.append(split_summary)
        lines.append("")
    return "\n".join(lines)


def _render_walk_forward_summary(version_info: dict) -> str:
    history = version_info.get("history", [])
    if not history:
        return ""
    latest = history[-1]
    train = latest.get("train_backtest") or {}
    validation = latest.get("validation_backtest") or {}
    if not train and not validation:
        return ""

    def row(label: str, data: dict) -> str:
        samples = int(data.get("samples", 0) or 0)
        trades = int(data.get("trade_samples", 0) or 0)
        win_rate = float(data.get("win_rate", 0) or 0)
        avg_return = float(data.get("avg_return", 0) or 0)
        max_loss = int(data.get("max_consecutive_loss", 0) or 0)
        return (
            f"| {label} | {trades}/{samples} | {_fmt_pct(win_rate)} | "
            f"{_fmt_pct(avg_return)} | {max_loss} |"
        )

    lines = ["### 训练/验证分段", ""]
    lines.append("| 分段 | 出手/样本 | 胜率 | 平均收益 | 最大连亏 |")
    lines.append("|------|-----------|------|----------|----------|")
    if train:
        lines.append(row("训练段", train))
    if validation:
        lines.append(row("最近验证段", validation))
    return "\n".join(lines)


def _append_execution_advice(lines: list[str], advice: dict):
    if not advice:
        return
    window = f"{advice.get('window_start', '14:40')}-{advice.get('window_end', '14:55')}"
    lines.append("- 建议执行窗口：" + window)
    lines.append(f"- 理想买入条件：{advice.get('preferred_price', '靠近尾盘均价，不追全天高位')}")
    lines.append(f"- 触发买入：{advice.get('confirm_condition', '尾盘资金和量价继续确认')}")
    lines.append(f"- 放弃买入：{advice.get('give_up_condition', '尾盘急拉至全天高位附近且承接转弱')}")


def _append_execution_timing_advice(
    lines: list[str],
    selection_result: dict,
    rec: dict,
    config: dict,
) -> None:
    market = selection_result.get("market_overview", {})
    checkpoints = ", ".join((config.get("execution_revisit", {}) or {}).get("checkpoints", []) or [])
    if not rec:
        reason = selection_result.get("empty_reason") or "今日无满足阈值的推荐，空仓观望。"
        lines.append("### 空仓触发原因")
        lines.append("- 动作：不买入，继续观察")
        lines.append(f"- 原因：{reason}")
        lines.append(f"- 建议观察时点：{checkpoints or '未配置'}")
        _append_empty_selection_diagnostics(lines, selection_result)
        lines.append("")
        return

    line, reason = _eval_early_entry_condition(
        selection_result,
        rec,
        config,
        market,
    )
    lines.append("### 执行时机建议")
    lines.append(f"- 建议：{line}")
    lines.append(f"- 触发条件：{reason}")

    risks = _flag_risky_factors(rec, config)
    if risks:
        lines.append(f"- 被淘汰风险因子：{'; '.join(risks)}")

    contrib_rows = _recommended_factor_contributions(rec, config, top_n=4)
    if contrib_rows:
        text = [
            f"{fk}={score:.1f}（{'正向' if contrib >= 0 else '负向'} {contrib:.2f}）"
            for fk, score, contrib in contrib_rows
        ]
        lines.append(f"- 当日Top4因子贡献：{'; '.join(text)}")

    lines.append(f"- 建议观察时点：{checkpoints or '未配置'}")
    lines.append("")


def _fmt_override_value(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _sorted_blockers(selection_result: dict) -> list[tuple[str, int]]:
    diag = selection_result.get("selection_diagnostics") or {}
    blockers = diag.get("guardrail_blockers") or {}
    return sorted(blockers.items(), key=lambda x: (-x[1], x[0]))


def _sorted_error_counts(selection_result: dict) -> list[tuple[str, int]]:
    diag = selection_result.get("selection_diagnostics") or {}
    errors = diag.get("error_counts") or {}
    return sorted(errors.items(), key=lambda x: (-x[1], x[0]))


def _top_blocker_text(selection_result: dict, limit: int = 3) -> str:
    parts = [f"{reason} {count}只" for reason, count in _sorted_blockers(selection_result)[:limit]]
    return "；".join(parts) if parts else "暂无硬门槛阻挡统计"


def _append_empty_selection_diagnostics(lines: list[str], selection_result: dict) -> None:
    overrides = selection_result.get("runtime_overrides") or {}
    if overrides:
        lines.append("- 本次参数覆盖：")
        for key, meta in overrides.items():
            if isinstance(meta, dict):
                before = _fmt_override_value(meta.get("before"))
                after = _fmt_override_value(meta.get("after"))
                lines.append(f"  - {key}：{before} → {after}")

    diag = selection_result.get("selection_diagnostics") or {}
    if diag:
        lines.append("- 空仓诊断：")
        if diag.get("total_scored") is not None:
            lines.append(f"  - 深度打分：{diag.get('total_scored')}只")
        if diag.get("below_score_threshold") is not None:
            lines.append(f"  - 低于综合分阈值：{diag.get('below_score_threshold')}只")
        blockers = diag.get("guardrail_blockers") or {}
        for reason, count in sorted(blockers.items(), key=lambda x: (-x[1], x[0]))[:5]:
            lines.append(f"  - {reason}：{count}只")
        errors = diag.get("error_counts") or {}
        for source, count in sorted(errors.items(), key=lambda x: (-x[1], x[0]))[:5]:
            lines.append(f"  - {source} 数据失败：{count}只")

    watchlist = selection_result.get("watchlist") or []
    if watchlist:
        lines.append("- 观察池 Top：")
        lines.append("")
        lines.append("| 代码 | 名称 | 得分 | 行业 | 阻挡原因 | F2 | F3 | F8 |")
        lines.append("|------|------|------|------|----------|----|----|----|")
        for item in watchlist[:10]:
            lines.append(
                f"| {item.get('symbol','')} | {item.get('name','')} | "
                f"{_coerce_float(item.get('score')):.2f} | {item.get('sector','')} | "
                f"{item.get('block_reason','-')} | "
                f"{_coerce_float(item.get('F2_volume_price_sync')):.2f} | "
                f"{_coerce_float(item.get('F3_technical_pattern')):.2f} | "
                f"{_coerce_float(item.get('F8_overnight_risk_control')):.2f} |"
            )


def _build_recommendation_reason_table(recommendation: dict, config: dict) -> str:
    factors = config.get("factors", {})
    fs = recommendation.get("factor_scores") or {}
    details = recommendation.get("factor_details") or {}
    rows = []
    for fk, meta in factors.items():
        score = fs.get(fk)
        if score is None and fk in recommendation and isinstance(recommendation.get(fk), (int, float, str)):
            score = recommendation.get(fk)
        if score is None:
            score = details.get(fk, {}).get("score")
        if score is None:
            continue
        rows.append((fk, _coerce_float(score), _coerce_float(meta.get("weight", 0))))
    if not rows:
        # 回退兼容旧格式
        for fk in [
            "F1_tail_fund_inflow", "F2_volume_price_sync", "F3_technical_pattern",
            "F4_tail_rally_strength", "F5_sector_heat", "F6_news_catalyst",
            "F7_float_mv_fit", "F8_overnight_risk_control", "F9_overheat_control",
            "F10_trend_momentum", "F11_financial_quality", "F12_market_sentiment",
        ]:
            score = recommendation.get(fk)
            if score is None:
                score = details.get(fk, {}).get("score")
            if isinstance(score, (int, float, str)):
                rows.append(
                    (fk, _coerce_float(score), _coerce_float(config.get("factors", {}).get(fk, {}).get("weight", 0)))
                )

    if not rows:
        return "<p class='muted'>无可用因子分。</p>"

    rows.sort(key=lambda x: abs(x[1] - 50) * 2 + x[2] * 100, reverse=True)
    lines = [
        "<div class='table-wrap compact'>",
        "  <table>",
        "    <thead><tr><th>因子</th><th>得分</th><th>权重</th><th>贡献幅度</th><th>离中性</th></tr></thead>",
        "    <tbody>",
    ]
    for fk, score, weight in rows[:8]:
        desc = _factor_label(fk, config)
        contrib = (score - 50.0) * weight
        delta = score - 50.0
        lines.append(
            f"      <tr><td>{_html_escape(desc)} ({_html_escape(fk)})</td>"
            f"<td>{score:.2f}</td><td>{weight:.4f}</td>"
            f"<td>{contrib:+.2f}</td><td>{delta:+.2f}</td></tr>"
        )
    lines.append("    </tbody>")
    lines.append("  </table>")
    lines.append("</div>")
    return "\n".join(lines)


def _render_recommendations(
    recommendations: list[dict],
    config: dict,
    selection_result: dict | None = None,
) -> str:
    lines = ["## 三、今日优选", ""]
    advice = config.get("execution_advice", {})
    selection_result = selection_result or {}
    signals = selection_result.get("opportunity_signals") or []
    if signals:
        lines.append("### 多时点机会判断")
        for sig in signals[:5]:
            decision_time = _selection_decision_time(selection_result, sig)
            decision_clock = decision_time.time() if decision_time else None
            reasons = "；".join(str(x) for x in (sig.get("reasons") or [])[:3])
            risks = "；".join(str(x) for x in (sig.get("risks") or [])[:2])
            lines.append(
                f"- {sig.get('symbol', '')} {sig.get('name', '')}："
                f"{_display_action_label(sig, config, now=decision_clock)}，"
                f"{_display_case_label(sig, config, now=decision_clock)}，"
                f"机会分 {sig.get('opportunity_score', 0)}/100，"
                f"下次复核 {_display_next_check(sig.get('next_check_at'), now=decision_clock) or '无需等待'}"
            )
            if reasons:
                lines.append(f"  - 触发理由：{reasons}")
            if risks:
                lines.append(f"  - 风险点：{risks}")
        lines.append("")
    _append_near_opportunity_watchlist(lines, selection_result)
    if not recommendations:
        lines.append("> 今日无满足阈值的推荐，空仓观望。")
        if advice:
            lines.append("")
            lines.append("尾盘执行建议（出现达标推荐时适用）：")
            _append_execution_advice(lines, advice)
        _append_execution_timing_advice(lines, selection_result, {}, config)
        lines.append("")
        return "\n".join(lines)

    factor_desc = {fk: fc.get("desc", fk) for fk, fc in config["factors"].items()}

    for i, rec in enumerate(recommendations, 1):
        sym = rec.get("symbol", "")
        name = rec.get("name", "")
        score = rec.get("score", 0)
        label = "盘中机会推荐" if rec.get("strategy_case") == "intraday_attack" else "尾盘隔夜推荐"
        lines.append(f"### {label}{i}：{sym} {name}")
        lines.append(f"- 综合得分：{score}/100")
        decision_time = _selection_decision_time(selection_result, rec)
        decision_clock = decision_time.time() if decision_time else None
        if rec.get("action_label") or rec.get("action"):
            lines.append(f"- 当前动作：{_display_action_label(rec, config, now=decision_clock)}")
        if rec.get("next_check_at"):
            lines.append(f"- 下次复核：{_display_next_check(rec.get('next_check_at'), now=decision_clock) or '无需等待'}")
        lines.append("- 推荐因子明细（Top8）：")
        lines.append(_build_recommendation_reason_table(rec, config))
        lines.append(f"- 所属行业：{rec.get('sector', '未知')}")
        _append_execution_advice(lines, advice)
        if i == 1:
            _append_execution_timing_advice(lines, selection_result, rec, config)
        lines.append("- 风险提示：历史训练默认按 T 日收盘价基准验证；真实纸面执行以当日尾盘窗口记录为准。")
        lines.append("")

    return "\n".join(lines)


def _append_near_opportunity_watchlist(lines: list[str], selection_result: dict) -> None:
    watchlist = (selection_result or {}).get("watchlist") or []
    if not watchlist:
        return
    lines.append("<details>")
    lines.append("<summary>最接近机会的观察池</summary>")
    lines.append("")
    lines.append("| 代码 | 名称 | 综合分 | 行业 | 未推荐原因 | F2 | F8 |")
    lines.append("|------|------|--------|------|------------|----|----|")
    for item in watchlist[:10]:
        lines.append(
            f"| {item.get('symbol', '')} | {item.get('name', '')} | {item.get('score', 0)} | "
            f"{item.get('sector', '未知')} | {item.get('block_reason') or '接近机会'} | "
            f"{item.get('F2_volume_price_sync', '-')} | {item.get('F8_overnight_risk_control', '-')} |"
        )
    lines.append("")
    lines.append("</details>")
    lines.append("")


def _render_strategy_factor_contrib_section(config: dict) -> str:
    lines = []
    lines.extend(_render_factor_contrib_section(config).splitlines())
    lines.append("")
    lines.extend(_render_factor_contrib_window_summary(config, [10, 20, 30]))
    return "\n".join(lines)


def _factor_contrib_snapshot_html(config: dict) -> str:
    cfg = _get_factor_contrib_cfg(config)
    lookback = int(_coerce_float(cfg.get("lookback_days", 30), 30))
    if lookback <= 0:
        lookback = 30
    scope = cfg.get("candidate_scope", "historical_training")
    rows = _calc_factor_contrib_rows(config, lookback, scope)
    if not rows:
        return "<p class=\"muted\">当前样本不足，暂不产出因子贡献统计。</p>"

    factor_desc = {fk: _factor_label(fk, config) for fk in config.get("factors", {}).keys()}
    blocker_map = {
        fk: cnt for fk, cnt, _ in _extract_blocker_loss_rows(_load_strategy_samples(), lookback)
    }
    table_header = (
        "<div class=\"table-wrap compact\">"
        "<table>"
        "<thead><tr>"
        "<th>因子</th><th>样本</th><th>与收益相关性</th>"
        "<th>与胜负相关性</th><th>前30%-后30%收益差</th>"
        "<th>平均加权贡献</th><th>阻挡命中率</th><th>机会损失次数</th><th>结论</th>"
        "</tr></thead><tbody>"
    )
    table_body = []
    for r in rows[:12]:
        name = factor_desc.get(r["factor"], r["factor"])
        miss_cnt = blocker_map.get(r["factor"], 0)
        signal = _factor_signal_label(r, miss_cnt)
        miss_str = f"{miss_cnt}次" if miss_cnt > 0 else "-"
        miss_cls = "status-negative" if miss_cnt >= 5 else ""
        table_body.append(
            "<tr>"
            f"<td>{_html_escape(name)}({_html_escape(r['factor'])})</td>"
            f"<td>{r['samples']}</td>"
            f"<td class=\"{ 'status-positive' if r['rho_return'] >= 0 else 'status-negative'}\">{_html_escape('{0:.2f}'.format(r['rho_return']))}</td>"
            f"<td class=\"{ 'status-positive' if r['rho_win'] >= 0.5 else 'status-negative'}\">{_html_escape('{0:.2f}'.format(r['rho_win']))}</td>"
            f"<td class=\"{ 'status-positive' if r['top30_return_gap'] > 0 else 'status-negative'}\">{_html_escape('{0:.2%}'.format(r['top30_return_gap']))}</td>"
            f"<td class=\"{ 'status-positive' if r['weighted_contrib'] >= 0 else 'status-negative'}\">{_html_escape('{0:.2f}'.format(r['weighted_contrib']))}</td>"
            f"<td>{_html_escape('{0:.2%}'.format(r['block_rate']))}</td>"
            f"<td class=\"{miss_cls}\">{_html_escape(miss_str)}</td>"
            f"<td>{_html_escape(signal)}</td>"
            "</tr>"
        )
    table_footer = "</tbody></table></div>"

    note_html = (
        "<p class='muted' style='margin: 6px 0 10px; font-size: 11px;'>"
        "基于候选池全样本统计（含被阈值挡掉的票），避免幸存者偏差；"
        "机会损失次数反映该因子阈值阻挡的次日上涨票数。"
        "</p>"
    )

    opp_rows = _extract_blocker_loss_rows(_load_strategy_samples(), lookback)
    opp_rows_html = ""
    if opp_rows:
        opp_header = (
            "<div class=\"table-wrap compact\">"
            "<table>"
            "<thead><tr>"
            "<th>因子</th><th>错失次数</th><th>平均错失幅度</th><th>建议</th>"
            "</tr></thead><tbody>"
        )
        opp_body = []
        for fk, cnt, avg_abs in opp_rows[:3]:
            opp_body.append(
                "<tr>"
                f"<td>{_html_escape(factor_desc.get(fk, fk))}（{_html_escape(fk)}）</td>"
                f"<td>{cnt}</td>"
                f"<td>{_html_escape('{0:.2%}'.format(avg_abs))}</td>"
                "<td>常见触发为阈值边界/上限，建议复核是否可放宽阻挡线</td>"
                "</tr>"
            )
        opp_rows_html = "".join([opp_header, "".join(opp_body), "</tbody></table></div>"])
    else:
        opp_rows_html = "<p class='muted'>近期开仓触发样本不足。</p>"

    window_rows = []
    for window in [10, 20, 30]:
        period = int(_coerce_float(window, 0))
        if period <= 0:
            continue
        rows = _calc_factor_contrib_rows(config, period, scope)
        if not rows:
            window_rows.append((f"{period}日", "样本不足", "", ""))
            continue
        top = rows[:3]
        top = [
            f"{r['factor']}（rho={r['rho_return']:+.2f}、差异={r['top30_return_gap']:+.2%}）"
            for r in top
        ]
        window_rows.append((f"{period}日", "近端Top3", "；".join(top[:3]), f"样本{rows[0]['samples']}"))

    window_html = (
        "<div class=\"table-wrap compact\">"
        "<table>"
        "<thead><tr><th>窗口</th><th>状态</th><th>Top3因子</th><th>覆盖</th></tr></thead><tbody>"
        + "".join(
            "<tr>"
            f"<td>{_html_escape(name)}</td><td>{_html_escape(status)}</td>"
            f"<td>{_html_escape(top_desc)}</td><td>{_html_escape(cover)}</td>"
            "</tr>"
            for name, status, top_desc, cover in window_rows
        )
        + "</tbody></table></div>"
    )

    return "".join(
        [
            f"<h3>最近{lookback}日因子贡献（Top12）</h3>",
            note_html,
            table_header,
            "".join(table_body),
            table_footer,
            "<h3>最近10/20/30日因子贡献快照</h3>",
            window_html,
            "<h3>错失机会高风险路径</h3>",
            opp_rows_html,
        ]
    )


def _factor_contrib_compact_snapshot_html(config: dict) -> str:
    cfg = _get_factor_contrib_cfg(config)
    lookback = int(_coerce_float(cfg.get("lookback_days", 30), 30))
    if lookback <= 0:
        lookback = 30
    rows = _calc_factor_contrib_rows(config, lookback, cfg.get("candidate_scope", "historical_training"))
    if not rows:
        return "<p class='muted'>当前样本不足，速览不可用。</p>"

    factor_desc = {fk: _factor_label(fk, config) for fk in config.get("factors", {}).keys()}
    blocker_map = {
        fk: cnt for fk, cnt, _ in _extract_blocker_loss_rows(_load_strategy_samples(), lookback)
    }
    enriched = []
    for r in rows:
        miss_cnt = blocker_map.get(r["factor"], 0)
        signal = _factor_signal_label(r, miss_cnt)
        priority = 0 if signal == "阈值偏严" else 1
        enriched.append((priority, -abs(r["rho_return"]), r, miss_cnt, signal))
    enriched.sort(key=lambda x: (x[0], x[1]))
    cards = []
    for _, _, r, miss_cnt, signal in enriched[:5]:
        rho = r["rho_return"]
        gap = r["top30_return_gap"]
        signal_cls = "status-positive" if signal == "偏正向" else (
            "status-negative" if signal in ("偏负向", "阈值偏严") else ""
        )
        miss_str = f" · 错失{miss_cnt}次" if miss_cnt > 0 else ""
        cards.append(
            '<article class="compact-kpi">'
            f"<small>{_html_escape(factor_desc.get(r['factor'], r['factor']) )}</small>"
            f'<strong class="{signal_cls}">{_html_escape(signal)}</strong>'
            f"<small>ρ(收益)：{_html_escape('{0:.2f}'.format(rho))} · 前后差：{_html_escape('{0:.2%}'.format(gap))}</small>"
            f"<small>阻挡：{_html_escape('{0:.2%}'.format(r['block_rate']))}{miss_str}</small>"
            '</article>'
        )

    return '<div class="compact-kpi-grid">' + "".join(cards) + '</div>'


def _market_compact_snapshot_html(overview: dict) -> str:
    mt = _market_tone(overview)
    sh = overview.get("sh_pct")
    sz = overview.get("sz_pct")
    cyb = overview.get("cyb_pct")
    up = overview.get("limit_up_count")
    down = overview.get("limit_down_count")
    breadth = overview.get("market_bread")
    width_text = "-"
    if breadth is not None:
        width_text = f"{breadth:.2f}" if isinstance(breadth, (int, float)) else str(breadth)

    return (
        '<div class="compact-kpi-grid">'
        '<article class="compact-kpi">'
        "<small>指数走势</small>"
        f"<strong>{_html_escape(_fmt_pct(sh))} / {_html_escape(_fmt_pct(sz))} / {_html_escape(_fmt_pct(cyb))}</strong>"
        "<small>上证 · 深证 · 创业板</small>"
        '</article>'
        '<article class="compact-kpi">'
        "<small>市场节奏</small>"
        f"<strong>{_html_escape(mt.get('tone', '-'))}</strong>"
        f"<small>偏离度 {_html_escape(mt.get('divergence', '-'))} / 宽度 {_html_escape(width_text)}</small>"
        '</article>'
        '<article class="compact-kpi">'
        "<small>涨跌停</small>"
        f"<strong>{_html_escape(up if up is not None else '-')} / {_html_escape(down if down is not None else '-')}</strong>"
        f"<small>行情口径 {_html_escape(overview.get('limit_source', 'unavailable'))}</small>"
        '</article>'
        '<article class="compact-kpi">'
        "<small>数据源/快照</small>"
        f"<strong>{_html_escape(overview.get('source', 'unknown'))}</strong>"
        f"<small>{_html_escape(_fmt_market_time(overview))} · {_html_escape(overview.get('quote_code', '000001/399001/399006'))}</small>"
        '</article>'
        '</div>'
    )


def _render_validation(trades: list[dict], today: str) -> str:
    """渲染昨日实际执行验证结果，只读取 live_paper，避免历史训练样本污染。"""
    lines = ["## 四、昨日推荐验证结果", ""]
    yesterday = (dt.datetime.strptime(today, "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    samples = _load_strategy_samples()
    yesterday_samples = [
        s for s in samples
        if s.get("sample_type") == "live_paper"
        and (s.get("date") == yesterday or s.get("buy_date") == yesterday)
    ]

    if not yesterday_samples:
        lines.append(f"> {yesterday} 无实际执行验证记录。")
        lines.append("")
        return "\n".join(lines)

    empty_samples = [s for s in yesterday_samples if not s.get("selected", True)]
    if empty_samples:
        reason = empty_samples[0].get("empty_reason", "空仓")
        selected_at = empty_samples[0].get("selected_at", "")
        if selected_at:
            lines.append(f"> 昨日选股执行时间：{selected_at}")
            lines.append("")
        lines.append(f"> {yesterday} 空仓：{reason}")
        lines.append("")
        return "\n".join(lines)

    yesterday_trades = [s for s in yesterday_samples if s.get("selected", True)]
    selected_at = yesterday_trades[0].get("selected_at", "")
    if selected_at:
        lines.append(f"> 昨日选股执行时间：{selected_at}")
        lines.append("")
    lines.append("| 代码 | 名称 | 得分 | 买入价 | 卖出价 | 收益率 | 胜负 |")
    lines.append("|------|------|------|--------|--------|--------|------|")
    wins = 0
    for t in yesterday_trades:
        ret = t.get("return", 0)
        win = "✅" if ret > 0 else "❌"
        if ret > 0:
            wins += 1
        lines.append(f"| {t.get('symbol','')} | {t.get('name','')} | "
                      f"{t.get('score',0):.2f} | {t.get('buy_price',0):.2f} | "
                      f"{t.get('sell_price',0):.2f} | "
                      f"{_fmt_pct(ret)} | {win} |")
    lines.append("")
    lines.append(f"昨日策略命中：{wins}/{len(yesterday_trades)}")
    lines.append("")
    return "\n".join(lines)


def _render_history(trades: list[dict]) -> str:
    lines = ["## 四、完整历史训练记录", ""]
    by_date = {}
    for s in _load_strategy_samples():
        sample_type = s.get("sample_type")
        if sample_type != "historical_training":
            continue
        date_key = s.get("date") or s.get("buy_date", "")
        if not date_key:
            continue
        if date_key not in by_date:
            by_date[date_key] = s
    recent = [by_date[d] for d in sorted(by_date.keys(), reverse=True)]
    name_map = _build_symbol_name_map()
    if not recent:
        lines.append("> 暂无历史训练记录。")
        lines.append("")
        return "\n".join(lines)

    lines.append("| 日期 | 行为 | 代码 | 名称 | 买入价 | 买入价来源 | 卖出价 | 收益率 | 结果/原因 | 次日实际最优 | 机会损失 | 命中最优 | 未选原因 |")
    lines.append("|------|------|------|------|--------|------------|--------|--------|-----------|--------------|----------|----------|----------|")
    for t in recent:
        actual_best = t.get("actual_best") or {}
        best_symbol = actual_best.get("symbol", "")
        best_name = str(actual_best.get("name", "")).strip() or _lookup_symbol_name(best_symbol, name_map)
        best_ret = actual_best.get("return")
        best_text = "-"
        if best_symbol and isinstance(best_ret, (int, float)):
            best_text = f"{best_symbol} {best_name} ({_fmt_pct(best_ret)})"
        missed_reason = t.get("missed_best_reason", "-")
        sample_return = t.get("return") if t.get("selected", True) else 0
        opp_loss = _opportunity_loss(sample_return, actual_best)
        hit_best = "命中" if t.get("selected", True) and best_symbol and t.get("symbol") == best_symbol else "未命中"
        if not t.get("selected", True):
            lines.append(f"| {t.get('date','')} | 空仓 | - | - | - | - | - | - | "
                         f"{t.get('empty_reason','空仓')} | {best_text} | {opp_loss} | {hit_best} | {missed_reason} |")
            continue
        ret = t.get("return", 0)
        win = "胜" if ret > 0 else "负"
        symbol = t.get("symbol", "")
        name = str(t.get("name", "")).strip() or _lookup_symbol_name(symbol, name_map)
        buy_source = t.get("buy_price_source", "-")
        lines.append(f"| {t.get('date') or t.get('buy_date','')} | 出手 | {t.get('symbol','')} | "
                      f"{name} | {t.get('buy_price',0):.2f} | "
                      f"{buy_source} | "
                      f"{t.get('sell_price',0):.2f} | {_fmt_pct(ret)} | {win} | "
                      f"{best_text} | {opp_loss} | {hit_best} | {missed_reason} |")
    lines.append("")
    return "\n".join(lines)


def _render_live_execution_history() -> str:
    """渲染真实执行/纸面记录，独立于当前策略历史回放。"""
    lines = ["## 五、实际执行验证记录", ""]
    samples = [
        s for s in _load_strategy_samples()
        if s.get("sample_type") == "live_paper"
    ]
    if not samples:
        lines.append("> 暂无实际执行验证记录。")
        lines.append("")
        return "\n".join(lines)

    name_map = _build_symbol_name_map()
    samples.sort(
        key=lambda s: s.get("date") or s.get("buy_date") or s.get("selection_date", ""),
        reverse=True,
    )
    lines.append("| 日期 | 行为 | 代码 | 名称 | 执行时间 | 买入价 | 卖出价 | 收益率 | 结果/原因 |")
    lines.append("|------|------|------|------|----------|--------|--------|--------|-----------|")
    for s in samples:
        date_key = s.get("date") or s.get("buy_date") or s.get("selection_date", "")
        selected_at = s.get("selected_at", "-") or "-"
        if not s.get("selected", True):
            lines.append(
                f"| {date_key} | 空仓 | - | - | {selected_at} | - | - | - | "
                f"{s.get('empty_reason', '空仓')} |"
            )
            continue

        symbol = s.get("symbol", "")
        name = str(s.get("name", "")).strip() or _lookup_symbol_name(symbol, name_map)
        ret = s.get("return", 0)
        win = "胜" if ret > 0 else "负"
        lines.append(
            f"| {date_key} | 出手 | {symbol} | {name} | {selected_at} | "
            f"{s.get('buy_price', 0):.2f} | {s.get('sell_price', 0):.2f} | "
            f"{_fmt_pct(ret)} | {win} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_coverage_simulation() -> str:
    lines = ["## 六、高出手率模拟", ""]
    try:
        import coverage_simulator
        result = coverage_simulator.simulate_from_files(targets=[0.75, 0.80, 0.85])
    except Exception as e:
        lines.append(f"> 暂无法生成高出手率模拟：{e}")
        lines.append("")
        return "\n".join(lines)

    if not result.get("total_days"):
        lines.append("> 暂无历史候选池，完成历史训练后可展示 75%/80%/85% 出手率模拟。")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        f"> 基于当前历史候选池模拟，不修改正式策略。理论最高出手率："
        f"{result.get('max_possible_coverage', 0):.2%}。"
    )
    lines.append("")
    lines.append("| 目标出手率 | 实际出手率 | 出手/空仓 | 胜率 | 平均收益 | 盈亏比 | 最大连亏 |")
    lines.append("|------------|------------|-----------|------|----------|--------|----------|")
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
    lines.append("")
    return "\n".join(lines)


def _render_alerts(perf: dict, config: dict, trades: list[dict]) -> str:
    rc = config.get("risk_control", {})
    alerts = []

    # 最大连亏
    consec = _calc_consecutive_loss(trades)
    if consec >= rc.get("max_consecutive_loss", 3):
        alerts.append(f"⚠️ 最大连亏已达 {consec} 次（阈值{rc['max_consecutive_loss']}），"
                      f"建议次日空仓观察 {rc.get('cooldown_days_after_max_loss',1)} 天")

    # 7日胜率
    w7 = perf.get("7d", {}).get("win_rate", 1)
    if w7 < rc.get("win_rate_7d_alert", 0.5):
        alerts.append(f"⚠️ 近7日胜率 {_fmt_pct(w7)} 低于阈值 {_fmt_pct(rc['win_rate_7d_alert'])}")

    # 30日胜率
    w30 = perf.get("30d", {}).get("win_rate", 1)
    if w30 < rc.get("win_rate_30d_alert", 0.55):
        alerts.append(f"⚠️ 近30日胜率 {_fmt_pct(w30)} 低于阈值 {_fmt_pct(rc['win_rate_30d_alert'])}")

    # 盈亏比
    pl = perf.get("total", {}).get("pl_ratio", 0)
    if pl < rc.get("min_pl_ratio", 1.5) and perf.get("total", {}).get("samples", 0) >= 10:
        alerts.append(f"⚠️ 总盈亏比 1:{pl:.2f} 低于目标 1:{rc['min_pl_ratio']}")

    lines = ["## 七、策略告警", ""]
    if not alerts:
        lines.append("> 各项指标正常，无告警。")
    else:
        lines.extend(alerts)
    lines.append("")
    return "\n".join(lines)


def _render_feedback_summary() -> str:
    """渲染样本驱动反馈摘要。"""
    snapshot = _load_latest_feedback_snapshot()
    metrics = snapshot.get("sample_metrics", {})
    lines = ["## 八、反馈闭环摘要", ""]

    if not metrics:
        lines.append("> 暂无统一样本池快照，执行 collect_metrics 后可展示历史训练、实际执行与综合胜率。")
        lines.append("")
        return "\n".join(lines)

    lines.append("| 样本层 | 胜率 | 平均收益 | 空仓率 | 最大连亏 | 样本日 | 交易样本 | 判断 |")
    lines.append("|--------|------|----------|--------|----------|--------|----------|------|")
    labels = {
        "historical_training": "历史训练",
        "live_paper": "实际执行",
        "combined": "综合",
    }
    for key in ["historical_training", "live_paper", "combined"]:
        m = metrics.get(key, {})
        judgement = "不足以判断" if m.get("insufficient", True) else "可参考"
        lines.append(
            f"| {labels[key]} | {_fmt_pct(m.get('win_rate', 0))} | "
            f"{_fmt_pct(m.get('avg_return', 0))} | {_fmt_pct(m.get('empty_rate', 0))} | "
            f"{m.get('max_consecutive_loss', 0)} | {m.get('samples', 0)} | "
            f"{m.get('trade_samples', 0)} | {judgement} |"
        )

    lines.append("")
    lines.append("当前策略建议：反馈闭环仅提供建议，不自动修改参数；真实执行样本不足时优先继续累计。")
    lines.append("")
    return "\n".join(lines)


def _render_strategy_diagnostics(config: dict) -> str:
    lines = ["## 九、策略诊断与候选实验", ""]
    samples = [
        sample for sample in _load_strategy_samples()
        if sample.get("sample_type") == "historical_training"
        and sample.get("candidate_pool")
    ]
    if not samples:
        lines.append("> 暂无历史候选池，完成历史训练后可展示机会损失与候选实验。")
        lines.append("")
        return "\n".join(lines)
    try:
        import regret_analyzer
        regret = regret_analyzer.analyze_regret(samples, config)
        combo_rows = regret_analyzer.analyze_blocker_combo_regret(
            samples,
            config,
            top_combo_count=3,
        )
        lines.append(
            f"- 当前累计机会损失：{regret.get('total_regret', 0):.2%}；"
            f"平均机会损失：{regret.get('avg_regret', 0):.2%}；"
            f"命中次日最优：{regret.get('exact_best_hit_rate', 0):.2%}。"
        )
        if combo_rows:
            top = combo_rows[0]
            lines.append(
                f"- 最大 blocker 组合：{'+'.join(top.get('blockers', []))}，"
                f"累计损失 {top.get('total_regret', 0):.2%} / "
                f"{top.get('miss_days', 0)} 天。"
            )
        experiments = [
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
            }
        ]
        experiment_summary = regret_analyzer.analyze_rescue_experiments(
            samples,
            config,
            experiments,
            validation_ratio=0.3,
        )
        lines.append("")
        lines.append(regret_analyzer.format_rescue_experiment_summary(
            "F7 条件救援推广门槛",
            experiment_summary,
        ))
    except Exception as exc:
        lines.append(f"> 暂无法生成策略诊断：{exc}")
    lines.append("")
    return "\n".join(lines)


def _render_strategy_rules(config: dict) -> str:
    """列出当前生效规则与关键参数，便于每次报告追踪调整。"""
    lines = ["## 十、策略规则与参数说明", ""]

    factors = config.get("factors", {})
    if factors:
        lines.append("### 1. 因子与权重")
        lines.append("")
        lines.append("| 因子 | 说明 | 权重 | 计算口径 | 评分区间 |")
        lines.append("|------|------|------|----------|----------|")
        for key, item in factors.items():
            score_range = item.get("score_range", "-")
            if isinstance(score_range, (list, tuple)) and len(score_range) == 2:
                score_range = f"{score_range[0]}-{score_range[1]}"
            lines.append(
                f"| {key} | {item.get('desc', '-')} | {item.get('weight', '-')} | "
                f"{item.get('calc', '-')} | {score_range} |"
            )
        lines.append("")

    def append_params(title: str, params: dict):
        if not params:
            return
        lines.append(f"### {title}")
        lines.append("")
        for key, value in params.items():
            lines.append(f"- `{key}`：{_fmt_value(value)}")
        lines.append("")

    append_params("2. 预过滤硬约束", config.get("prefilter", {}))
    append_params("3. 排序、空仓与救援规则", config.get("selection", {}))
    append_params("4. 执行与验证模型", {
        **(config.get("execution_model", {}) or {}),
        **{f"execution_costs.{k}": v for k, v in (config.get("execution_costs", {}) or {}).items()},
        **{f"validation.{k}": v for k, v in (config.get("validation", {}) or {}).items()},
        **{f"execution_advice.{k}": v for k, v in (config.get("execution_advice", {}) or {}).items()},
        **{f"execution_revisit.{k}": v for k, v in (config.get("execution_revisit", {}) or {}).items()},
        **{f"factor_contrib.{k}": v for k, v in (config.get("factor_contrib", {}) or {}).items()},
    })
    append_params("5. 优化与风控参数", {
        **{f"optimization.{k}": v for k, v in (config.get("optimization", {}) or {}).items()},
        **{f"risk_control.{k}": v for k, v in (config.get("risk_control", {}) or {}).items()},
    })

    if len(lines) == 2:
        lines.append("> 当前配置未提供可展示的规则参数。")
        lines.append("")
    return "\n".join(lines)


def _performance_rows(perf: dict) -> list[dict]:
    rows = []
    for period in ["7d", "30d", "total"]:
        p = perf.get(period, {})
        pl_ratio = p.get("pl_ratio", 0)
        rows.append({
            "label": {"7d": "近7日", "30d": "近30日", "total": "总计"}[period],
            "win_rate": _fmt_pct(p.get("win_rate", 0)),
            "pl_ratio": f"1:{pl_ratio:.2f}" if pl_ratio > 0 else "-",
            "max_consecutive_loss": p.get("max_consecutive_loss", 0),
            "samples": p.get("samples", 0),
        })
    return rows


def _dedupe_historical_samples(samples: list[dict]) -> list[dict]:
    by_date = {}
    for sample in samples:
        if sample.get("sample_type") != "historical_training":
            continue
        date = sample.get("date")
        if not date:
            continue
        by_date[date] = sample
    return [by_date[date] for date in sorted(by_date)]


def _symbol_rank_in_candidate_pool(symbol: str, candidate_pool: list[dict]) -> int | None:
    if not symbol:
        return None
    ranked = sorted(
        candidate_pool or [],
        key=lambda item: float(item.get("return", 0) or 0),
        reverse=True,
    )
    for idx, item in enumerate(ranked, 1):
        if item.get("symbol") == symbol:
            return idx
    return None


def _oracle_metrics(samples: list[dict], last_n: int | None = None) -> dict:
    rows = _dedupe_historical_samples(samples)
    if last_n is not None:
        rows = rows[-last_n:]
    denominators = []
    exact_hits = 0
    top3_hits = 0
    regrets = []
    for sample in rows:
        actual_best = sample.get("actual_best") or {}
        best_symbol = actual_best.get("symbol")
        best_ret = actual_best.get("return")
        if not best_symbol or not isinstance(best_ret, (int, float)):
            continue
        denominators.append(sample)
        selected_symbol = sample.get("symbol") if sample.get("selected") else ""
        selected_return = float(sample.get("return", 0) or 0) if sample.get("selected") else 0.0
        if selected_symbol == best_symbol:
            exact_hits += 1
        rank = _symbol_rank_in_candidate_pool(selected_symbol, sample.get("candidate_pool") or [])
        if rank is not None and rank <= 3:
            top3_hits += 1
        regrets.append(max(0.0, float(best_ret) - selected_return))
    total = len(denominators)
    return {
        "samples": total,
        "exact_best_hit_rate": exact_hits / total if total else 0.0,
        "top3_hit_rate": top3_hits / total if total else 0.0,
        "avg_regret": sum(regrets) / len(regrets) if regrets else 0.0,
        "total_regret": sum(regrets),
    }


def _oracle_kpi_strip_html() -> str:
    samples = _load_strategy_samples()
    metrics = [
        ("近7日命中最优", _oracle_metrics(samples, 7)),
        ("近30日命中最优", _oracle_metrics(samples, 30)),
        ("总计命中最优", _oracle_metrics(samples, None)),
    ]
    cards = []
    for label, metric in metrics:
        cards.append(
            "<article class=\"decision-kpi oracle-kpi\">"
            f"<span>{_html_escape(label)}</span>"
            f"<strong>{_html_escape(_fmt_pct(metric.get('exact_best_hit_rate', 0)))}</strong>"
            f"<small>Top3邻近 {_html_escape(_fmt_pct(metric.get('top3_hit_rate', 0)))} · "
            f"机会损失 {_html_escape(_fmt_pct(metric.get('avg_regret', 0)))} · "
            f"样本 {_html_escape(metric.get('samples', 0))}</small>"
            "</article>"
        )
    return "<div class=\"decision-kpi-strip oracle-kpi-strip\">" + "".join(cards) + "</div>"


def _html_param_list(params: dict, prefix: str = "") -> str:
    items = []
    for key, value in (params or {}).items():
        label = f"{prefix}.{key}" if prefix else str(key)
        items.append(
            f"<li><code>{_html_escape(label)}</code><span>{_html_escape(_fmt_value(value))}</span></li>"
        )
    return "".join(items) or "<li><span>暂无参数</span></li>"


def _strategy_rules_html(config: dict) -> str:
    factor_rows = "".join(
        "<tr>"
        f"<td>{_html_escape(key)}</td>"
        f"<td>{_html_escape(item.get('desc', '-'))}</td>"
        f"<td>{_html_escape(item.get('weight', '-'))}</td>"
        f"<td>{_html_escape(item.get('calc', '-'))}</td>"
        f"<td>{_html_escape(_fmt_value(item.get('score_range', '-')))}</td>"
        "</tr>"
        for key, item in (config.get("factors", {}) or {}).items()
    )
    if not factor_rows:
        factor_rows = '<tr><td colspan="5">暂无因子配置</td></tr>'

    execution_params = {
        **(config.get("execution_model", {}) or {}),
        **{f"validation.{k}": v for k, v in (config.get("validation", {}) or {}).items()},
        **{f"execution_advice.{k}": v for k, v in (config.get("execution_advice", {}) or {}).items()},
        **{f"execution_revisit.{k}": v for k, v in (config.get("execution_revisit", {}) or {}).items()},
        **{f"factor_contrib.{k}": v for k, v in (config.get("factor_contrib", {}) or {}).items()},
    }
    risk_params = {
        **{f"optimization.{k}": v for k, v in (config.get("optimization", {}) or {}).items()},
        **{f"risk_control.{k}": v for k, v in (config.get("risk_control", {}) or {}).items()},
    }
    return f"""
    <section class="panel rules-panel">
      <p class="kicker">规则总览</p>
      <h2>策略规则与参数说明</h2>
      <div class="rules-grid">
        <div class="rule-block wide">
          <h3>因子与权重</h3>
          <div class="table-wrap compact">
            <table aria-label="因子与权重">
              <thead><tr><th>因子</th><th>说明</th><th>权重</th><th>计算口径</th><th>评分区间</th></tr></thead>
              <tbody>{factor_rows}</tbody>
            </table>
          </div>
        </div>
        <div class="rule-block"><h3>预过滤硬约束</h3><ul>{_html_param_list(config.get('prefilter', {}))}</ul></div>
        <div class="rule-block"><h3>排序、空仓与救援</h3><ul>{_html_param_list(config.get('selection', {}))}</ul></div>
        <div class="rule-block"><h3>执行与验证模型</h3><ul>{_html_param_list(execution_params)}</ul></div>
        <div class="rule-block"><h3>优化与风控</h3><ul>{_html_param_list(risk_params)}</ul></div>
      </div>
    </section>
    """


def _strategy_rules_snapshot_html(config: dict) -> str:
    """关键规则快照：用于右侧栏的快速决策参考。"""
    selection = config.get("selection", {}) or {}
    execution_advice = config.get("execution_advice", {}) or {}
    risk_control = config.get("risk_control", {}) or {}

    score_threshold = selection.get("score_threshold")
    market_drop_threshold = selection.get("market_drop_threshold")
    candidate_pool_size = config.get("optimization", {}).get("candidate_pool_size")
    max_consecutive_loss = risk_control.get("max_consecutive_loss")
    give_up_condition = execution_advice.get("give_up_condition")

    snapshot_rows = []
    if score_threshold is not None:
        snapshot_rows.append(("<span>入选阈值</span>", f"score_threshold = {score_threshold}"))
    if market_drop_threshold is not None:
        snapshot_rows.append(("<span>市场跌破阈值</span>", f"market_drop_threshold = {market_drop_threshold}"))
    if candidate_pool_size is not None:
        snapshot_rows.append(("<span>候选池规模</span>", f"candidate_pool_size = {candidate_pool_size}"))
    if max_consecutive_loss is not None:
        snapshot_rows.append(("<span>最大连续亏损</span>", f"max_consecutive_loss = {max_consecutive_loss}"))
    if give_up_condition:
        snapshot_rows.append(("<span>放弃买入触发</span>", _html_escape(give_up_condition)))

    if not snapshot_rows:
        snapshot_rows.append(("<span>参数状态</span>", "默认策略参数"))

    rows = [
        f"<li><strong>{label}</strong><small>{detail}</small></li>"
        for label, detail in snapshot_rows
    ]

    return (
        '<section class="panel rule-snapshot">'
        '<p class="kicker">规则快照</p>'
        '<h2>策略规则与参数说明</h2>'
        '<ul class="snapshot-list">'
        + "".join(rows)
        + "</ul>"
        "</section>"
    )


def _decision_overview_html(selection_result: dict, config: dict, perf: dict, alerts_text: str) -> str:
    overview = selection_result.get("market_overview", {})
    recommendations = selection_result.get("recommendations", [])
    opportunity_signals = selection_result.get("opportunity_signals") or []
    primary_signal = opportunity_signals[0] if opportunity_signals else (recommendations[0] if recommendations else {})
    advice = config.get("execution_advice", {}) or {}
    validation = config.get("validation", {}) or {}
    empty_reason = selection_result.get("empty_reason", "")
    has_pick = bool(recommendations)
    action = primary_signal.get("action", "TAIL_CONFIRM" if has_pick else "NO_TRADE")
    decision_time = _selection_decision_time(selection_result, primary_signal)
    action_label = _display_action_label(primary_signal, config, now=decision_time.time() if decision_time else None)
    if primary_signal:
        decision_title = f"{primary_signal.get('symbol', '')} {primary_signal.get('name', '')}".strip()
        case_label = _display_case_label(primary_signal, config, now=decision_time.time() if decision_time else None)
        decision_detail = (
            f"{case_label} · 机会分 {primary_signal.get('opportunity_score', primary_signal.get('score', 0))}/100，"
            f"综合得分 {primary_signal.get('score', 0)}/100，行业 {primary_signal.get('sector', '未知')}"
        )
    else:
        decision_title = "今日空仓"
        decision_detail = empty_reason or "今日无满足阈值的推荐，空仓观望。"
    alert_lines = [
        line.strip()
        for line in alerts_text.splitlines()
        if line.strip() and not line.startswith("##")
    ]
    alert_summary = "；".join(alert_lines) if alert_lines else "各项指标正常，无告警。"
    has_alert = "⚠" in alerts_text
    execution_window = (
        f"{advice.get('window_start', '14:40')}-{advice.get('window_end', '14:55')}"
    )
    sell_mode = validation.get("sell_mode", "next_open")
    execution_state = action_label if primary_signal else "不买入，继续观察"
    state_class = "ok" if action == "BUY_NOW" and not has_alert else ("warn" if has_alert or action == "NO_TRADE" else "watch")
    primary_class = "execution-ready" if action == "BUY_NOW" and not has_alert else ("execution-paused" if has_alert or action == "NO_TRADE" else "execution-watch")
    next_check = _display_next_check(primary_signal.get("next_check_at", ""), now=decision_time.time() if decision_time else None)
    action_detail = (
        "今日没有达标候选，不进入买入窗口。"
        if not primary_signal
        else f"当前动作：{_html_escape(action_label)} · 下一复核：{_html_escape(next_check or '无需等待')}"
        if action in {"BUY_NOW", "WAIT_RECHECK"}
        else f"当前动作：{_html_escape(action_label)} · 执行窗口 {_html_escape(execution_window)} · 卖出：{_html_escape(sell_mode)}"
    )
    primary_label = "今日交易结论" if primary_signal else "空仓触发原因"
    primary_extra = ""
    if not primary_signal:
        primary_extra = _empty_diagnostics_html(selection_result)
    else:
        primary_extra = _opportunity_detail_html(selection_result, config)
    return f"""
    <section class="panel decision-overview">
      <div class="panel-head">
        <div>
          <p class="kicker">决策总览</p>
          <h2>今日决策</h2>
        </div>
        <strong class="decision-chip">{_html_escape(decision_title)}</strong>
      </div>
      {_performance_kpi_strip_html(perf)}
      {_oracle_kpi_strip_html()}
      <div class="decision-grid">
        <div class="decision-card primary {primary_class}">
          <span>{_html_escape(primary_label)}</span>
          <strong>{_html_escape(decision_title)}</strong>
          <small>{_html_escape(decision_detail)}</small>
          <small>{action_detail}</small>
          <div class="decision-state-band {state_class}">{_html_escape(execution_state)}</div>
          {primary_extra}
        </div>
        <div class="decision-card risk-note">
          <span>今日买入外部影响风险说明</span>
          <strong>{_html_escape(_signal_risk_summary(primary_signal) or advice.get('give_up_condition', '尾盘承接转弱则放弃买入'))}</strong>
          <small>关注指数急跌、板块突发利空、流动性断层、尾盘冲高回落。</small>
          <small>告警：{_html_escape(alert_summary)}</small>
        </div>
      </div>
      <details class="decision-secondary-detail">
        <summary>市场快照与执行口径</summary>
        <div class="decision-market-strip">
          <div class="compact-kpi-grid">
            <article class="compact-kpi"><small>风控</small><strong>{_html_escape(perf.get('total', {}).get('max_consecutive_loss', 0))}天</strong><small>最大连续亏损 · 总样本 {_html_escape(str(perf.get('total', {}).get('samples', 0)))}</small></article>
            <article class="compact-kpi"><small>市场行情</small><strong>{_html_escape(_fmt_pct(overview.get('sh_pct', 0)))}</strong><small>上证 · 数据源 {_html_escape(overview.get('source', 'unknown'))}</small></article>
            <article class="compact-kpi"><small>执行窗口</small><strong>{_html_escape(execution_window)}</strong><small>卖出：{_html_escape(sell_mode)}</small></article>
          </div>
          {_market_compact_snapshot_html(overview)}
        </div>
      </details>
    </section>
    """


def _signal_risk_summary(signal: dict) -> str:
    risks = signal.get("risks") or []
    if risks:
        return "；".join(str(r) for r in risks[:2])
    return ""


def _selection_decision_time(selection_result: dict, signal: dict | None = None) -> dt.datetime | None:
    for source in (signal or {}, selection_result or {}):
        value = source.get("decision_time") or source.get("selected_at")
        if not value:
            continue
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return _REAL_DATETIME.strptime(str(value)[:19], fmt)
            except ValueError:
                continue
    return None


def _tail_window_state(config: dict, now: dt.time | None = None) -> str:
    advice = config.get("execution_advice", {}) or {}
    start = _parse_hhmm(advice.get("window_start", "14:40"))
    end = _parse_hhmm(advice.get("window_end", "14:55"))
    if start is None or end is None:
        return "unknown"
    now = now or dt.datetime.now().time()
    if now < start:
        return "before"
    if start <= now <= end:
        return "inside"
    if now < dt.time(15, 0):
        return "closing"
    return "after"


def _display_action_label(signal: dict, config: dict, now: dt.time | None = None) -> str:
    action = signal.get("action", "")
    if action == "TAIL_CONFIRM":
        state = _tail_window_state(config, now=now)
        if state == "before":
            return "等待尾盘确认"
        if state == "inside":
            return "尾盘可执行"
        if state == "closing":
            return "收盘前确认"
        if state == "after":
            return "尾盘已过"
        return "尾盘确认"
    return signal.get("action_label") or {
        "BUY_NOW": "现在可买",
        "WAIT_RECHECK": "等待复核",
        "NO_TRADE": "不买入，继续观察",
    }.get(action, action)


def _display_case_label(signal: dict, config: dict, now: dt.time | None = None) -> str:
    strategy_case = signal.get("strategy_case", "")
    if strategy_case == "tail_confirm":
        state = _tail_window_state(config, now=now)
        if state == "inside":
            return "尾盘当前确认"
        if state == "closing":
            return "收盘前最后确认"
    return signal.get("case_label") or {
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


def _display_next_check(next_check_at: str | None, now: dt.time | None = None) -> str:
    next_check = str(next_check_at or "").strip()
    if not next_check:
        return ""
    checkpoint = _parse_hhmm(next_check)
    if checkpoint is None:
        return next_check
    now = now or dt.datetime.now().time()
    if checkpoint <= now:
        return f"{next_check} 已过"
    return next_check


def _opportunity_detail_html(selection_result: dict, config: dict) -> str:
    signals = selection_result.get("opportunity_signals") or []
    recommendations = selection_result.get("recommendations") or []
    parts = []
    if signals:
        rows = []
        for sig in signals[:5]:
            decision_time = _selection_decision_time(selection_result, sig)
            decision_clock = decision_time.time() if decision_time else None
            rows.append(
                "<tr>"
                f"<td>{_html_escape(sig.get('symbol', ''))} {_html_escape(sig.get('name', ''))}</td>"
                f"<td>{_html_escape(_display_action_label(sig, config, now=decision_clock))}</td>"
                f"<td>{_html_escape(_display_case_label(sig, config, now=decision_clock))}</td>"
                f"<td>{_html_escape(sig.get('opportunity_score', 0))}</td>"
                f"<td>{_html_escape('; '.join(sig.get('reasons', [])[:2]))}</td>"
                f"<td>{_html_escape(_display_next_check(sig.get('next_check_at'), now=decision_clock) or '-')}</td>"
                "</tr>"
            )
        parts.append(
            "<div class='opportunity-summary'>"
            "<p class='kicker'>多时点机会判断</p>"
            "<div class='table-wrap compact'><table>"
            "<thead><tr><th>标的</th><th>动作</th><th>类型</th><th>机会分</th><th>触发理由</th><th>下次复核</th></tr></thead>"
            "<tbody>" + "".join(rows) + "</tbody></table></div>"
            "</div>"
        )
    if recommendations:
        parts.append("<details class='decision-secondary-detail' open><summary>尾盘隔夜推荐与因子明细</summary>")
        parts.append(_recommendation_detail_html(recommendations, config, selection_result))
        parts.append("</details>")
    parts.append(_near_opportunity_watchlist_html(selection_result))
    return "\n".join(parts)


def _near_opportunity_watchlist_html(selection_result: dict) -> str:
    watchlist = selection_result.get("watchlist") or []
    if not watchlist:
        return ""
    rows = []
    for item in watchlist[:10]:
        rows.append(
            "<tr>"
            f"<td>{_html_escape(item.get('symbol', ''))} {_html_escape(item.get('name', ''))}</td>"
            f"<td>{_html_escape(item.get('score', 0))}</td>"
            f"<td>{_html_escape(item.get('sector', '未知'))}</td>"
            f"<td>{_html_escape(item.get('block_reason') or '接近机会')}</td>"
            f"<td>{_html_escape(item.get('F2_volume_price_sync', '-'))}</td>"
            f"<td>{_html_escape(item.get('F8_overnight_risk_control', '-'))}</td>"
            "</tr>"
        )
    return (
        "<details class='decision-secondary-detail'>"
        "<summary>最接近机会的观察池</summary>"
        "<div class='table-wrap compact'><table>"
        "<thead><tr><th>标的</th><th>综合分</th><th>行业</th><th>未推荐原因</th><th>F2</th><th>F8</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
        "</details>"
    )


def _performance_kpi_strip_html(perf: dict) -> str:
    rows = _performance_rows(perf)
    cards = []
    for row in rows:
        cards.append(
            "<article class=\"decision-kpi\">"
            f"<span>{_html_escape(row['label'])}</span>"
            f"<strong>{_html_escape(row['win_rate'])}</strong>"
            f"<small>盈亏比 {_html_escape(row['pl_ratio'])} · 样本 {_html_escape(row['samples'])}</small>"
            "</article>"
        )
    return "<div class=\"decision-kpi-strip\">" + "".join(cards) + "</div>"


def _quick_status_bar(selection_result: dict, config: dict, perf: dict, alerts_text: str) -> str:
    overview = selection_result.get("market_overview", {})
    recommendations = selection_result.get("recommendations", [])
    if recommendations:
        first = recommendations[0]
        pick_text = f"{first.get('symbol', '-') } {first.get('name', '')}".strip() or first.get('symbol', '未知')
        score_text = f"{_fmt_value(first.get('score', 0))}/100"
    else:
        pick_text = "今日空仓"
        score_text = "-"

    has_alert = "⚠" in alerts_text
    alert_mark = "有告警" if has_alert else "正常"
    mt = _market_tone(overview)
    exec_window = config.get("execution_advice", {}) or {}
    execution_window = f"{exec_window.get('window_start', '14:40')}-{exec_window.get('window_end', '14:55')}"

    return (
        '<section class="quick-metrics decision-side-metrics">'
        '  <article class="quick-card"><small>今日优选</small><strong>' + _html_escape(pick_text) + '</strong><small>得分：' + _html_escape(score_text) + ' · ' + ('可执行' if not has_alert else '风控告警') + '</small></article>'
        '  <article class="quick-card"><small>策略风控</small><strong>' + _html_escape(str(perf.get("total", {}).get("max_consecutive_loss", 0)) + "天") + '</strong><small>连续亏损上限：' + _html_escape(str(perf.get("total", {}).get("samples", 0))) + ' 样本</small></article>'
        '  <article class="quick-card"><small>市场节奏</small><strong>' + _html_escape(mt.get("tone", "-")) + '</strong><small>偏离度：' + _html_escape(mt.get("divergence", "-")) + '</small></article>'
        '  <article class="quick-card"><small>风险状态</small><span class="decision-badge ' + ("ok" if not has_alert else "warn") + '">' + _html_escape(alert_mark) + '</span><small>' + _html_escape("有无告警：" + alert_mark) + '</small></article>'
        '  <article class="quick-card"><small>市场口径</small><strong>' + _html_escape(overview.get("source", "unknown")) + '</strong><small>口径：' + _html_escape(overview.get("limit_source", "unavailable")) + '</small></article>'
        '  <article class="quick-card"><small>执行窗口（今日优化后）</small><strong>' + _html_escape(execution_window) + '</strong><small>' + ('尾盘优先' if execution_window else '暂无优化口径') + '</small></article>'
        '</section>'
    )


def _readable_buy_price_source(source: str) -> str:
    source = str(source or "-")
    labels = {
        "T_close": "T日收盘价",
        "T1_open": "次日开盘价",
        "T_minute_14:45": "14:45分钟价",
        "T_tail_advice_proxy_no_minutes": "尾盘建议价",
        "T1_open_fallback_no_minutes": "次日开盘价",
        "T1_open_window_avg_09:30_09:40": "次日开盘均价",
    }
    if source in labels:
        return labels[source]
    if source.startswith("T_minute_"):
        return source.replace("T_minute_", "") + "分钟价"
    if source.startswith("T1_open_window_avg_"):
        return "次日开盘均价"
    if source.startswith("T1_open_fallback"):
        return "次日开盘价"
    return source if source and source != "-" else "-"


def _factor_label(factor_key: str, config: dict) -> str:
    factors = config.get("factors", {})
    label = factors.get(factor_key, {}).get("desc")
    return label or factor_key


def _readable_factor_reason(reason: str, config: dict) -> str:
    text = str(reason or "-")
    factors = config.get("factors", {})
    for key in factors.keys():
        label = _factor_label(key, config)
        text = text.replace(f"{key}低于", f"{label}低于")
        text = text.replace(f"{key}高于", f"{label}高于")
    return text


def _fmt_signed_pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.2f}%"


def _opportunity_loss(sample_return, actual_best: dict) -> str:
    best_ret = actual_best.get("return")
    if not isinstance(best_ret, (int, float)):
        return "-"
    base_ret = sample_return if isinstance(sample_return, (int, float)) else 0
    return _fmt_signed_pct(best_ret - base_ret)


def _rule_score_details(actual_best: dict, config: dict, fallback_reason: str) -> str:
    factor_scores = actual_best.get("factor_scores") or {}
    selection = config.get("selection", {})
    details = []

    for key, threshold in (selection.get("min_factor_scores") or {}).items():
        score = factor_scores.get(key)
        if isinstance(score, (int, float)) and score < threshold:
            details.append(
                f"{_factor_label(key, config)} {score:.2f} / {float(threshold):.2f}，差 {float(threshold) - score:.2f}"
            )

    for key, threshold in (selection.get("max_factor_scores") or {}).items():
        score = factor_scores.get(key)
        if isinstance(score, (int, float)) and score > threshold:
            details.append(
                f"{_factor_label(key, config)} {score:.2f} / {float(threshold):.2f}，超 {score - float(threshold):.2f}"
            )

    if details:
        return "；".join(details)

    reason = str(fallback_reason or "-")
    if reason.startswith("次日实际最优未过当日规则："):
        return reason.replace("次日实际最优未过当日规则：", "")
    return reason


def _history_records() -> list[dict]:
    by_date = {}
    for s in _load_strategy_samples():
        if s.get("sample_type") != "historical_training":
            continue
        date_key = s.get("date") or s.get("buy_date", "")
        if date_key:
            by_date.setdefault(date_key, s)

    name_map = _build_symbol_name_map()
    config = _load_config()
    records = []
    for date_key in sorted(by_date.keys(), reverse=True):
        s = by_date[date_key]
        actual_best = s.get("actual_best") or {}
        best_symbol = actual_best.get("symbol", "")
        best_name = str(actual_best.get("name", "")).strip() or _lookup_symbol_name(best_symbol, name_map)
        best_ret = actual_best.get("return")
        best_text = "-"
        if best_symbol and isinstance(best_ret, (int, float)):
            best_text = f"{best_symbol} {best_name} ({_fmt_pct(best_ret)})"
        missed_reason = s.get("missed_best_reason", "-")
        rule_details = _rule_score_details(actual_best, config, missed_reason)
        opp_loss = _opportunity_loss(s.get("return"), actual_best)
        hit_best = "命中" if s.get("selected", True) and best_symbol and s.get("symbol") == best_symbol else "未命中"

        if not s.get("selected", True):
            records.append({
                "日期": date_key,
                "行为": "空仓",
                "代码": "-",
                "名称": "-",
                "买入价": "-",
                "买入价来源": "-",
                "卖出价": "-",
                "收益率": "-",
                "结果/原因": _readable_factor_reason(s.get("empty_reason", "空仓"), config),
                "次日实际最优": best_text,
                "机会损失": opp_loss,
                "命中最优": hit_best,
                "未过规则": rule_details,
            })
            continue

        ret = s.get("return", 0)
        symbol = s.get("symbol", "")
        records.append({
            "日期": date_key,
            "行为": "出手",
            "代码": symbol,
            "名称": str(s.get("name", "")).strip() or _lookup_symbol_name(symbol, name_map),
            "买入价": f"{s.get('buy_price', 0):.2f}",
            "买入价来源": _readable_buy_price_source(s.get("buy_price_source", "-")),
            "卖出价": f"{s.get('sell_price', 0):.2f}",
            "收益率": _fmt_pct(ret),
            "结果/原因": "胜" if ret > 0 else "负",
            "次日实际最优": best_text,
            "机会损失": opp_loss,
            "命中最优": hit_best,
            "未过规则": rule_details,
        })
    return records


def _live_records() -> list[dict]:
    samples = [
        s for s in _load_strategy_samples()
        if s.get("sample_type") == "live_paper"
    ]
    samples.sort(
        key=lambda s: s.get("date") or s.get("buy_date") or s.get("selection_date", ""),
        reverse=True,
    )
    name_map = _build_symbol_name_map()
    records = []
    for s in samples:
        date_key = s.get("date") or s.get("buy_date") or s.get("selection_date", "")
        selected_at = s.get("selected_at", "-") or "-"
        if not s.get("selected", True):
            records.append({
                "日期": date_key,
                "行为": "空仓",
                "代码": "-",
                "名称": "-",
                "执行时间": selected_at,
                "买入价": "-",
                "卖出价": "-",
                "收益率": "-",
                "结果/原因": s.get("empty_reason", "空仓"),
            })
            continue

        ret = s.get("return", 0)
        symbol = s.get("symbol", "")
        records.append({
            "日期": date_key,
            "行为": "出手",
            "代码": symbol,
            "名称": str(s.get("name", "")).strip() or _lookup_symbol_name(symbol, name_map),
            "执行时间": selected_at,
            "买入价": f"{s.get('buy_price', 0):.2f}",
            "卖出价": f"{s.get('sell_price', 0):.2f}",
            "收益率": _fmt_pct(ret),
            "结果/原因": "胜" if ret > 0 else "负",
        })
    return records


def _table_shell(
    table_id: str,
    title: str,
    subtitle: str,
    columns: list[str],
    data_table: str = None,
    source_options: list[str] = None,
) -> str:
    data_table = data_table or table_id
    headers = "".join(f"<th>{_html_escape(col)}</th>" for col in columns)
    table_label = _html_escape(title)
    source_filter = ""
    if source_options:
        options = "\n".join(
            f'<option value="{_html_escape(option)}">{_html_escape(option)}</option>'
            for option in source_options
        )
        source_filter = f"""
          <select id="{_html_escape(table_id)}SourceFilter" aria-label="筛选买入价来源">
            <option value="">全部来源</option>
            {options}
          </select>
        """
    return f"""
    <section class="panel table-panel" data-table="{_html_escape(data_table)}">
      <div class="panel-head">
        <div>
          <p class="kicker">{_html_escape(subtitle)}</p>
          <h2>{_html_escape(title)}</h2>
        </div>
        <div class="table-controls">
          <label class="sr-only" for="{_html_escape(table_id)}Search">搜索{table_label}</label>
          <input id="{_html_escape(table_id)}Search" type="search" aria-label="搜索{table_label}" placeholder="搜索日期、代码、名称、原因">
          <select id="{_html_escape(table_id)}PageSize" aria-label="每页条数">
            <option value="10">10/页</option>
            <option value="20" selected>20/页</option>
            <option value="50">50/页</option>
            <option value="100">100/页</option>
          </select>
          {source_filter}
        </div>
      </div>
      <div class="quick-filter" aria-label="{table_label}快速筛选" aria-live="polite">
        <button type="button" data-prefix="{_html_escape(table_id)}" data-filter="all" class="active">全部 <span class="filter-count" data-count-for="all">0</span></button>
        <button type="button" data-prefix="{_html_escape(table_id)}" data-filter="trade">出手 <span class="filter-count" data-count-for="trade">0</span></button>
        <button type="button" data-prefix="{_html_escape(table_id)}" data-filter="empty">空仓 <span class="filter-count" data-count-for="empty">0</span></button>
        <button type="button" data-prefix="{_html_escape(table_id)}" data-filter="win">收益为正 <span class="filter-count" data-count-for="win">0</span></button>
        <button type="button" data-prefix="{_html_escape(table_id)}" data-filter="loss">收益为负 <span class="filter-count" data-count-for="loss">0</span></button>
      </div>
      <div class="table-wrap">
        <table aria-label="{table_label}">
          <thead><tr>{headers}</tr></thead>
          <tbody id="{_html_escape(table_id)}Body"></tbody>
        </table>
      </div>
      <div class="pager">
        <button id="{_html_escape(table_id)}Prev" type="button">上一页</button>
        <span id="{_html_escape(table_id)}Info">第 1 页</span>
        <button id="{_html_escape(table_id)}Next" type="button">下一页</button>
      </div>
    </section>
    """


def _recommendation_html(
    recommendations: list[dict],
    config: dict,
    empty_reason: str = "",
    selection_result: dict | None = None,
) -> str:
    selection_result = selection_result or {}
    market = selection_result.get("market_overview", {})

    if not recommendations:
        reason = empty_reason or "今日无满足阈值的推荐，空仓观望。"
        checkpoints = ", ".join((config.get("execution_revisit", {}) or {}).get("checkpoints", []) or [])
        diagnostics = _empty_diagnostics_html(selection_result)
        return (
            f"<div class=\"empty-decision-card\">"
            f"<span>空仓触发原因</span>"
            f"<strong>不买入，继续观察</strong>"
            f"<small>{_html_escape(reason)}</small>"
            f"<small>观察时点：{_html_escape(checkpoints or '未配置')}</small>"
            f"{diagnostics}"
            "</div>"
        )

    return _recommendation_detail_html(recommendations, config, selection_result)


def _recommendation_detail_html(
    recommendations: list[dict],
    config: dict,
    selection_result: dict | None = None,
) -> str:
    selection_result = selection_result or {}
    market = selection_result.get("market_overview", {})
    first = recommendations[0]
    exec_advice, exec_condition = _eval_early_entry_condition(
        selection_result,
        first,
        config,
        market,
    )
    risks = _flag_risky_factors(first, config)
    contrib_rows = _recommended_factor_contributions(first, config, top_n=4)

    if contrib_rows:
        contrib_tbl = [
            "<div class='table-wrap compact'>",
            "  <table>",
            "    <thead><tr><th>因子</th><th>因子分</th><th>Top4贡献</th></tr></thead><tbody>",
        ]
        for fk, score, contrib in contrib_rows:
            desc = _factor_label(fk, config)
            contrib_tbl.append(
                f"      <tr><td>{_html_escape(desc)}（{_html_escape(fk)}）</td>"
                f"<td>{score:.1f}</td><td>{contrib:+.2f}</td></tr>"
            )
        contrib_tbl.extend(["    </tbody>", "  </table>", "</div>"])
        contrib_html = "\n".join(contrib_tbl)
    else:
        contrib_html = "<p class='muted'>暂无可用因子贡献样本。</p>"

    parts = []
    for rec in recommendations:
        reasons = _build_recommendation_reason_table(rec, config)
        parts.append(f"""
        <article class="pick-card">
          <div>
            <p class="kicker">今日唯一推荐</p>
            <h2>{_html_escape(rec.get('symbol', ''))} {_html_escape(rec.get('name', ''))}</h2>
          </div>
          <strong class="score">{_html_escape(rec.get('score', 0))}/100</strong>
          <p class="kicker">因子明细（Top8）</p>
          {reasons}
          <p>所属行业：{_html_escape(rec.get('sector', '未知'))}</p>
        </article>
        """)

    checkpoints = ", ".join((config.get('execution_revisit', {}) or {}).get('checkpoints', []) or [])
    timing = (
        f"<div class='panel decision-card wide'>\n"
        f"  <span>执行时机建议</span>"
        f"  <strong>{_html_escape(exec_advice)}</strong>"
        f"  <small>触发条件：{_html_escape(exec_condition)}</small>"
        f"  <small>观察时点：{_html_escape(checkpoints or '未配置')}</small>"
        f"  <small>被淘汰风险因子：{_html_escape('; '.join(risks) if risks else '暂无')}</small>"
        "  <div>Top4因子贡献</div>" + contrib_html +
        "</div>"
    )

    return "\n".join(parts) + "\n" + timing


def _empty_diagnostics_html(selection_result: dict) -> str:
    summary_bits = []
    detail_bits = []
    overrides = selection_result.get("runtime_overrides") or {}
    if overrides:
        rows = ["<ul class=\"diagnostic-list\">"]
        for key, meta in overrides.items():
            if isinstance(meta, dict):
                rows.append(
                    "<li>"
                    f"<span>{_html_escape(key)}</span>"
                    f"<strong>{_html_escape(_fmt_override_value(meta.get('before')))}"
                    f" → {_html_escape(_fmt_override_value(meta.get('after')))}</strong>"
                    "</li>"
                )
        rows.append("</ul>")
        if len(rows) > 2:
            detail_bits.append("<div><h4>本次参数覆盖</h4>" + "".join(rows) + "</div>")

    diag = selection_result.get("selection_diagnostics") or {}
    diag_parts = []
    if diag.get("total_scored") is not None:
        diag_parts.append(f"深度打分 {diag.get('total_scored')}只")
    if diag.get("below_score_threshold") is not None:
        diag_parts.append(f"低于综合分 {diag.get('below_score_threshold')}只")
    for reason, count in _sorted_blockers(selection_result)[:3]:
        diag_parts.append(f"{reason} {count}只")
    if diag_parts:
        summary_bits.append(
            "<div class=\"empty-summary-line\"><span>主要阻挡</span><strong>"
            + _html_escape("；".join(diag_parts))
            + "</strong></div>"
        )

    detail_rows = []
    if diag.get("total_scored") is not None:
        detail_rows.append(("深度打分", f"{diag.get('total_scored')}只"))
    if diag.get("below_score_threshold") is not None:
        detail_rows.append(("低于综合分", f"{diag.get('below_score_threshold')}只"))
    for reason, count in _sorted_blockers(selection_result):
        detail_rows.append((reason, f"{count}只"))
    for source, count in _sorted_error_counts(selection_result):
        detail_rows.append((f"{source} 数据失败", f"{count}只"))
    if detail_rows:
        rows = [
            f"<li><span>{_html_escape(label)}</span><strong>{_html_escape(value)}</strong></li>"
            for label, value in detail_rows
        ]
        detail_bits.append(
            "<div><h4>完整空仓诊断</h4><ul class=\"diagnostic-list\">"
            + "".join(rows)
            + "</ul></div>"
        )

    watchlist = selection_result.get("watchlist") or []
    if watchlist:
        summary_rows = []
        for item in watchlist[:5]:
            summary_rows.append(
                "<tr>"
                f"<td>{_html_escape(item.get('symbol',''))}</td>"
                f"<td>{_html_escape(item.get('name',''))}</td>"
                f"<td>{_coerce_float(item.get('score')):.1f}</td>"
                f"<td>{_html_escape(item.get('block_reason','-'))}</td>"
                "</tr>"
            )
        summary_bits.append(
            "<div class=\"empty-watchlist-summary\"><span>观察池 Top5</span>"
            "<div class=\"table-wrap compact watchlist-mini-table\">"
            "<table><thead><tr><th>代码</th><th>名称</th><th>得分</th><th>阻挡原因</th></tr></thead>"
            "<tbody>"
            + "".join(summary_rows)
            + "</tbody></table></div></div>"
        )

        table_rows = []
        for item in watchlist[:10]:
            table_rows.append(
                "<tr>"
                f"<td>{_html_escape(item.get('symbol',''))}</td>"
                f"<td>{_html_escape(item.get('name',''))}</td>"
                f"<td>{_coerce_float(item.get('score')):.2f}</td>"
                f"<td>{_html_escape(item.get('sector',''))}</td>"
                f"<td>{_html_escape(item.get('block_reason','-'))}</td>"
                f"<td>{_coerce_float(item.get('F2_volume_price_sync')):.1f}</td>"
                f"<td>{_coerce_float(item.get('F3_technical_pattern')):.1f}</td>"
                f"<td>{_coerce_float(item.get('F8_overnight_risk_control')):.1f}</td>"
                "</tr>"
            )
        detail_bits.append(
            "<div><h4>观察池 Top10</h4>"
            "<div class=\"table-wrap compact diagnostic-table\">"
            "<table><thead><tr><th>代码</th><th>名称</th><th>得分</th><th>行业</th>"
            "<th>阻挡原因</th><th>F2</th><th>F3</th><th>F8</th></tr></thead>"
            "<tbody>"
            + "".join(table_rows)
            + "</tbody></table></div></div>"
        )

    details = ""
    if detail_bits:
        details = (
            "<details class=\"empty-diagnostics-detail\">"
            "<summary>完整诊断与参数覆盖</summary>"
            "<div class=\"empty-diagnostics-body\">"
            + "".join(detail_bits)
            + "</div></details>"
        )
    return "".join(summary_bits) + details


def render_html_report(selection_result: dict) -> str:
    """渲染可直接打开的 HTML 日报。"""
    today = selection_result.get("date", dt.datetime.now().strftime("%Y-%m-%d"))
    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config = _config_for_report(selection_result)
    perf = _load_performance()
    version_info = _load_version()
    trades = _load_trades()
    overview = selection_result.get("market_overview", {})
    recommendations = selection_result.get("recommendations", [])
    history_rows = _history_records()
    live_rows = _live_records()
    historical_columns = ["日期", "行为", "代码", "名称", "买入价", "买入价来源", "卖出价", "收益率", "结果/原因", "次日实际最优", "机会损失", "命中最优", "未过规则"]
    live_columns = ["日期", "行为", "代码", "名称", "执行时间", "买入价", "卖出价", "收益率", "结果/原因"]
    history_source_options = sorted({
        row.get("买入价来源", "-")
        for row in history_rows
        if row.get("买入价来源") and row.get("买入价来源") != "-"
    })
    alerts_text = _render_alerts(perf, config, trades)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A股尾盘隔夜策略报告 - {_html_escape(today)}</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --paper: #ffffff;
      --ink: #0f172a;
      --muted: #475569;
      --line: #e2e8f0;
      --accent: #1e3a8a;
      --accent-light: #3b82f6;
      --danger: #dc2626;
      --success: #16a34a;
      --warning: #ca8a04;
      --gold: #ca8a04;
      --focus: #2563eb;
      --shadow-soft: 0 16px 34px rgba(15, 23, 42, 0.08);
      --shadow-card: 0 4px 16px rgba(15, 23, 42, 0.06);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
      line-height: 1.5;
    }}
    .page {{ max-width: 1200px; margin: 0 auto; padding: 16px; }}
    .hero {{
      border: 1px solid var(--line);
      background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
      box-shadow: var(--shadow-card);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }}
    h1, h2 {{ margin: 0; letter-spacing: 0; font-weight: 700; }}
    h1 {{ font-size: 24px; line-height: 1.2; }}
    h2 {{ font-size: 16px; line-height: 1.3; }}
    .kicker {{
      margin: 0 0 6px;
      color: var(--accent);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .muted, small {{ color: var(--muted); }}
    .terminal-stamp {{
      font-family: "Fira Code", "SFMono-Regular", Consolas, monospace;
      font-size: 12px;
      background: #0f172a;
      color: #e2e8f0;
      padding: 8px 12px;
      border-radius: 8px;
      text-align: center;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }}
    .panel, .metric {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      box-shadow: var(--shadow-card);
    }}
    .metric {{
      position: relative;
      overflow: hidden;
      min-height: 80px;
    }}
    .metric::before {{
      content: "";
      position: absolute;
      inset: 0 0 auto;
      height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent-light));
    }}
    .metric strong {{ display: block; font-family: "Fira Code", "SFMono-Regular", Consolas, monospace; font-size: 24px; margin-top: 6px; }}
    .quick-metrics {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin: 10px 0;
    }}
    .quick-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      background: #f8fafc;
      min-height: 60px;
    }}
    .quick-card small {{
      color: var(--muted);
      display: block;
      font-size: 11px;
    }}
    .quick-card strong {{
      display: block;
      margin: 3px 0 2px;
      font-size: 15px;
      line-height: 1.2;
    }}
    .decision-shell {{
      display: block;
      margin-top: 12px;
    }}
    .decision-main {{ min-width: 0; }}
    .decision-main > .panel {{ margin-bottom: 0; }}
    .decision-kpi-strip {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-bottom: 10px;
    }}
    .decision-kpi {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      background: #f8fafc;
      min-height: 66px;
    }}
    .decision-kpi span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 2px;
    }}
    .decision-kpi strong {{
      display: block;
      font-family: "Fira Code", "SFMono-Regular", Consolas, monospace;
      font-size: 18px;
      line-height: 1.2;
      margin-bottom: 2px;
    }}
    .decision-kpi small {{ display: block; font-size: 11px; line-height: 1.3; }}
    .compact-kpi-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }}
    .compact-kpi {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8fafc;
      padding: 8px;
      min-height: 70px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 3px;
    }}
    .compact-kpi small {{ display: block; color: var(--muted); font-size: 11px; line-height: 1.3; }}
    .compact-kpi strong {{ font-size: 16px; line-height: 1.2; }}
    .factor-detail {{ margin-top: 8px; }}
    .factor-detail summary {{ cursor: pointer; color: var(--accent); font-weight: 700; padding: 6px 0; font-size: 13px; }}
    .factor-detail summary::marker {{ color: var(--accent); }}
    .factor-detail .detail-body {{ margin-top: 8px; }}
    .pick-card .score {{ color: var(--gold); font-size: 24px; }}
    .empty-state {{ margin: 0; color: var(--muted); border-left: 3px solid var(--focus); padding: 8px 10px; background: #fffbeb; font-size: 13px; }}
    .decision-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border-radius: 6px;
      background: #0f172a;
      color: #e0f2fe;
      font-family: "Fira Code", "SFMono-Regular", Consolas, monospace;
      font-size: 13px;
    }}
    .decision-grid {{
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(260px, 0.9fr);
      gap: 8px;
    }}
    .decision-market-strip {{
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--line);
    }}
    .decision-secondary-detail {{
      margin-top: 10px;
      border-top: 1px solid var(--line);
      padding-top: 8px;
    }}
    .decision-secondary-detail summary {{
      cursor: pointer;
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
    }}
    .decision-card {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #ffffff;
      min-height: 90px;
      transition: border-color .16s ease, box-shadow .16s ease;
    }}
    .decision-card:hover {{
      border-color: #bfdbfe;
      box-shadow: var(--shadow-soft);
    }}
    .decision-card.primary {{ border-color: #93c5fd; background: #eff6ff; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1); }}
    .decision-card.strong {{ background: #f8fafc; }}
    .decision-card.execution-ready {{
      border-color: #22c55e;
      box-shadow: inset 0 0 0 1px #86efac, 0 6px 14px rgba(34, 197, 94, 0.1);
      background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
    }}
    .decision-card.execution-paused {{
      border-color: #f87171;
      box-shadow: inset 0 0 0 1px #fecaca, 0 6px 14px rgba(239, 68, 68, 0.08);
      background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%);
    }}
    .decision-card.execution-watch {{
      border-color: #fbbf24;
      box-shadow: inset 0 0 0 1px #fde68a, 0 6px 14px rgba(202, 138, 4, 0.08);
      background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
    }}
    .decision-card.wide {{ grid-column: span 3; }}
    .decision-card.risk-note {{
      background: #f8fafc;
      min-height: auto;
    }}
    .decision-state-band {{
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      margin-top: 4px;
      font-size: 10px;
      line-height: 1.3;
      border-radius: 999px;
      color: #1f2937;
      background: #eef2ff;
      font-weight: 700;
    }}
    .decision-state-band.ok {{
      color: #166534;
      background: #dcfce7;
    }}
    .decision-state-band.warn {{
      color: #7c2d12;
      background: #fed7aa;
    }}
    .decision-state-band.watch {{
      color: #854d0e;
      background: #fef3c7;
    }}
    .decision-card span {{ display: block; color: var(--muted); font-size: 11px; font-weight: 700; margin-bottom: 4px; }}
    .decision-card strong {{ display: block; font-size: 18px; line-height: 1.2; margin-bottom: 4px; }}
    .decision-card small {{ display: block; line-height: 1.4; font-size: 12px; }}
    .empty-decision-card {{
      border: 1px solid #fde68a;
      border-left: 4px solid #f59e0b;
      border-radius: 8px;
      background: #fffbeb;
      padding: 12px;
    }}
    .empty-decision-card span {{
      display: block;
      color: #854d0e;
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 4px;
    }}
    .empty-decision-card strong {{
      display: block;
      color: #0f172a;
      font-size: 18px;
      line-height: 1.25;
      margin-bottom: 4px;
    }}
    .empty-decision-card small {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .empty-summary-line {{
      margin-top: 8px;
      padding: 8px 10px;
      border: 1px solid #fde68a;
      border-radius: 8px;
      background: rgba(255, 255, 255, .72);
    }}
    .empty-summary-line span {{
      margin-bottom: 3px;
    }}
    .empty-summary-line strong {{
      font-size: 13px;
      line-height: 1.35;
      margin: 0;
      color: #334155;
      font-weight: 700;
    }}
    .empty-watchlist-summary {{
      margin-top: 8px;
      padding: 8px 10px;
      border: 1px solid #fde68a;
      border-radius: 8px;
      background: rgba(255, 255, 255, .76);
    }}
    .empty-watchlist-summary > span {{
      display: block;
      color: #854d0e;
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .watchlist-mini-table {{
      border: 1px solid #fde68a;
      border-radius: 8px;
      background: #fff;
    }}
    .watchlist-mini-table table {{ min-width: 0; }}
    .watchlist-mini-table th,
    .watchlist-mini-table td {{
      padding: 6px 7px;
      font-size: 11px;
      white-space: normal;
    }}
    .empty-diagnostics-detail {{
      margin-top: 10px;
      border-top: 1px solid #fde68a;
      padding-top: 8px;
    }}
    .empty-diagnostics-detail summary {{
      cursor: pointer;
      color: #92400e;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
    }}
    .empty-diagnostics-body {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 8px;
    }}
    .empty-diagnostics-body h4 {{
      margin: 0 0 6px;
      font-size: 12px;
      color: #475569;
    }}
    .diagnostic-list {{
      margin: 0;
      padding: 0;
      list-style: none;
      border: 1px solid #fde68a;
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }}
    .diagnostic-list li {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      padding: 7px 9px;
      border-top: 1px solid #fef3c7;
      font-size: 12px;
    }}
    .diagnostic-list li:first-child {{ border-top: 0; }}
    .diagnostic-list span {{
      margin: 0;
      color: #64748b;
    }}
    .diagnostic-list strong {{
      margin: 0;
      color: #0f172a;
      font-size: 12px;
      text-align: right;
    }}
    .diagnostic-table {{
      border: 1px solid #fde68a;
      border-radius: 8px;
    }}
    .diagnostic-table table {{ min-width: 760px; }}
    .rule-snapshot {{
      margin-top: 0;
      background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
    }}
    .panel-head {{ display: flex; gap: 10px; justify-content: space-between; align-items: end; margin-bottom: 10px; }}
    .table-controls {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }}
    input, select, button {{
      min-height: 36px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 0 10px;
      font: inherit;
      border-radius: 6px;
      transition: border-color .18s ease, box-shadow .18s ease, background-color .18s ease, color .18s ease;
      font-size: 13px;
    }}
    input {{ min-width: 220px; }}
    input:focus-visible, select:focus-visible, button:focus-visible {{
      outline: 2px solid rgba(37, 99, 235, 0.38);
      outline-offset: 1px;
      border-color: var(--focus);
    }}
    button {{ cursor: pointer; color: var(--accent); font-weight: 700; }}
    button:hover:not(:disabled) {{ background: #eff6ff; border-color: #93c5fd; }}
    button:disabled {{ cursor: not-allowed; color: var(--muted); opacity: .6; }}
    .table-panel {{ margin-top: 12px; padding: 0; overflow: hidden; }}
    .table-panel .panel-head {{ padding: 12px 12px 0; }}
    .quick-filter {{ display: flex; gap: 6px; flex-wrap: wrap; padding: 0 12px 10px; }}
    .quick-filter button {{
      min-height: 30px;
      font-size: 12px;
      background: #f8fafc;
      color: #334155;
    }}
    .quick-filter button.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .filter-count {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 20px;
      height: 18px;
      margin-left: 4px;
      padding: 0 5px;
      border-radius: 999px;
      background: #e2e8f0;
      color: #1e293b;
      font-family: "Fira Code", "SFMono-Regular", Consolas, monospace;
      font-size: 11px;
      font-weight: 700;
    }}
    .quick-filter button.active .filter-count {{
      background: rgba(255, 255, 255, .25);
      color: #fff;
    }}
    .table-wrap {{ overflow-x: auto; border-top: 1px solid var(--line); }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1040px; }}
    th, td {{
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      font-size: 12px;
    }}
    .table-wrap.compact th, .table-wrap.compact td {{ font-size: 11px; white-space: nowrap; }}
    th {{
      background: #f1f5ff;
      color: #1e3a8a;
      position: sticky;
      top: 0;
      z-index: 1;
      font-size: 11px;
      letter-spacing: .04em;
      font-weight: 700;
    }}
    td {{ font-family: "Fira Code", "SFMono-Regular", Consolas, monospace; color: #334155; }}
    .status-positive {{ color: var(--success); font-weight: 700; }}
    .status-negative {{ color: var(--danger); font-weight: 700; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    tbody tr:hover td {{ background: #eef6ff; }}
    .return-positive {{ color: var(--success); font-weight: 700; }}
    .return-negative {{ color: var(--danger); font-weight: 700; }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 20px;
      padding: 2px 6px;
      border-radius: 999px;
      background: #eef2ff;
      color: #1e40af;
      font-family: "Fira Sans", "PingFang SC", sans-serif;
      font-weight: 700;
      font-size: 11px;
    }}
    .status-pill.win {{ background: #dcfce7; color: #166534; }}
    .status-pill.loss {{ background: #fee2e2; color: #991b1b; }}
    .status-pill.empty {{ background: #f1f5f9; color: #475569; }}
    .decision-badge {{
      display: inline-flex;
      align-items: center;
      min-height: 20px;
      border-radius: 999px;
      padding: 1px 6px;
      font-size: 11px;
      font-weight: 700;
      font-family: "Fira Sans", "PingFang SC", sans-serif;
      background: #eef2ff;
      color: #1e40af;
    }}
    .decision-badge.ok {{
      background: #dcfce7;
      color: #166534;
    }}
    .decision-badge.warn {{
      background: #fee2e2;
      color: #991b1b;
    }}
    .snapshot-list {{
      margin: 0;
      padding-left: 0;
      list-style: none;
      color: var(--ink);
    }}
    .snapshot-list li {{
      display: grid;
      grid-template-columns: 100px 1fr;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      border-top: 1px solid var(--line);
    }}
    .snapshot-list li:first-child {{
      border-top: 0;
    }}
    .snapshot-list strong {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      line-height: 1.3;
    }}
    .snapshot-list small {{
      color: var(--ink);
      display: block;
      line-height: 1.3;
      font-size: 12px;
    }}
    .pager {{ display: flex; justify-content: flex-end; align-items: center; gap: 8px; padding: 10px 12px 12px; }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      *, *::before, *::after {{ transition: none !important; animation: none !important; }}
    }}
    @media (max-width: 960px) {{
      .hero, .decision-shell, .grid, .decision-grid, .decision-kpi-strip, .compact-kpi-grid, .quick-metrics {{ grid-template-columns: 1fr; }}
      .empty-diagnostics-body {{ grid-template-columns: 1fr; }}
      .panel-head {{ align-items: stretch; flex-direction: column; }}
      .table-controls input, .table-controls select {{ width: 100%; min-width: 0; }}
      .terminal-stamp {{ text-align: center; min-width: 0; }}
      .page {{ padding: 12px 10px 24px; }}
      h1 {{ font-size: 20px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div>
        <p class="kicker">纸面交易，不构成投资建议</p>
        <h1>A股尾盘隔夜策略报告 - {_html_escape(today)}</h1>
        <p class="muted" style="margin-top: 4px; font-size: 12px;">生成时间：{_html_escape(generated_at)} · 策略版本：{_html_escape(version_info.get('version', config.get('version', 'v1.0')))}</p>
      </div>
      <div class="terminal-stamp">NEXT OPT<br>{_html_escape(version_info.get('next_optimize_date', '未排期'))}</div>
    </header>

    <section class="decision-shell">
      <div class="decision-main">
        {_decision_overview_html(selection_result, config, perf, alerts_text)}
      </div>
    </section>

    <section class="panel" style="margin-top: 12px;">
      <div class="panel-head">
        <div>
          <p class="kicker">历史总结</p>
          <h2>近30日因子贡献速览</h2>
        </div>
        <small>候选池口径 · 含被阈值挡掉的票 · 非今日数据</small>
      </div>
      {_factor_contrib_compact_snapshot_html(config)}
    </section>

    {_table_shell('history', '完整历史训练记录', f'共 {len(history_rows)} 条', historical_columns, 'historical', history_source_options)}
    {_table_shell('live', '实际执行验证记录', f'共 {len(live_rows)} 条', live_columns)}
    {_strategy_rules_html(config)}
  </main>

  <script>
    const tableData = {{
      historical: {{
        rows: {_json_script(history_rows)},
        columns: {_json_script(historical_columns)},
        prefix: "history",
        page: 1,
        filter: "all",
        sourceFilter: ""
      }},
      live: {{
        rows: {_json_script(live_rows)},
        columns: {_json_script(live_columns)},
        prefix: "live",
        page: 1,
        filter: "all",
        sourceFilter: ""
      }}
    }};

    function cellText(value) {{
      return String(value ?? "");
    }}

    function renderTable(key) {{
      const state = tableData[key];
      const baseRows = rowsMatchingSearchAndSource(state);
      const pageSize = Number(document.getElementById(state.prefix + "PageSize").value);
      updateFilterCounts(state, baseRows);
      const filtered = baseRows.filter(row => matchesQuickFilter(row, state.filter));
      const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
      state.page = Math.min(Math.max(1, state.page), totalPages);
      const start = (state.page - 1) * pageSize;
      const visible = filtered.slice(start, start + pageSize);
      const body = document.getElementById(state.prefix + "Body");
      body.innerHTML = visible.map(row =>
        "<tr>" + state.columns.map(col => renderCell(col, row[col])).join("") + "</tr>"
      ).join("") || '<tr><td colspan="' + state.columns.length + '">无匹配记录</td></tr>';
      document.getElementById(state.prefix + "Info").textContent =
        "第 " + state.page + " / " + totalPages + " 页，共 " + filtered.length + " 条";
      document.getElementById(state.prefix + "Prev").disabled = state.page <= 1;
      document.getElementById(state.prefix + "Next").disabled = state.page >= totalPages;
    }}

    function rowsMatchingSearchAndSource(state) {{
      const query = document.getElementById(state.prefix + "Search").value.trim().toLowerCase();
      return state.rows.filter(row =>
        state.columns.some(col => cellText(row[col]).toLowerCase().includes(query))
      ).filter(row => matchesSourceFilter(row, state.sourceFilter));
    }}

    function matchesSourceFilter(row, sourceFilter) {{
      return !sourceFilter || cellText(row["买入价来源"]) === sourceFilter;
    }}

    function updateFilterCounts(state, rows) {{
      const counts = {{}};
      ["all", "trade", "empty", "win", "loss"].forEach(filter => {{
        counts[filter] = rows.filter(row => matchesQuickFilter(row, filter)).length;
      }});
      document.querySelectorAll('[data-prefix="' + state.prefix + '"] [data-count-for], [data-prefix="' + state.prefix + '"][data-filter] [data-count-for]').forEach(item => {{
        item.textContent = counts[item.dataset.countFor] ?? 0;
      }});
    }}

    function matchesQuickFilter(row, filter) {{
      const action = cellText(row["行为"]);
      const result = cellText(row["结果/原因"]);
      const returnValue = parseReturn(row["收益率"]);
      if (filter === "trade") return action === "出手";
      if (filter === "empty") return action === "空仓";
      if (filter === "win") return returnValue > 0 || result === "胜";
      if (filter === "loss") return returnValue < 0 || result === "负";
      return true;
    }}

    function parseReturn(value) {{
      const text = cellText(value).replace("%", "");
      const number = Number(text);
      return Number.isFinite(number) ? number : 0;
    }}

    function decorateReturn(value) {{
      const number = parseReturn(value);
      const cls = number > 0 ? "return-positive" : number < 0 ? "return-negative" : "";
      return '<span class="' + cls + '">' + escapeHtml(cellText(value)) + '</span>';
    }}

    function decorateStatus(value) {{
      const text = cellText(value);
      const cls = text === "胜" ? "win" : text === "负" ? "loss" : text.includes("空仓") || text.includes("无") ? "empty" : "";
      return '<span class="status-pill ' + cls + '">' + escapeHtml(text) + '</span>';
    }}

    function renderCell(col, value) {{
      if (col === "收益率") return "<td>" + decorateReturn(value) + "</td>";
      if (col === "结果/原因" || col === "行为") return "<td>" + decorateStatus(value) + "</td>";
      return "<td>" + escapeHtml(cellText(value)) + "</td>";
    }}

    function escapeHtml(text) {{
      return text.replace(/[&<>"']/g, ch => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
      }}[ch]));
    }}

    function bindTable(key) {{
      const state = tableData[key];
      document.getElementById(state.prefix + "Search").addEventListener("input", () => {{
        state.page = 1;
        renderTable(key);
      }});
      document.getElementById(state.prefix + "PageSize").addEventListener("change", () => {{
        state.page = 1;
        renderTable(key);
      }});
      const sourceSelect = document.getElementById(state.prefix + "SourceFilter");
      if (sourceSelect) {{
        sourceSelect.addEventListener("change", () => {{
          state.sourceFilter = sourceSelect.value;
          state.page = 1;
          renderTable(key);
        }});
      }}
      document.getElementById(state.prefix + "Prev").addEventListener("click", () => {{
        state.page -= 1;
        renderTable(key);
      }});
      document.getElementById(state.prefix + "Next").addEventListener("click", () => {{
        state.page += 1;
        renderTable(key);
      }});
      document.querySelectorAll('[data-prefix="' + state.prefix + '"][data-filter]').forEach(button => {{
        button.addEventListener("click", () => {{
          state.filter = button.dataset.filter;
          state.page = 1;
          document.querySelectorAll('[data-prefix="' + state.prefix + '"][data-filter]').forEach(item => {{
            item.classList.toggle("active", item === button);
          }});
          renderTable(key);
        }});
      }});
      renderTable(key);
    }}

    bindTable("historical");
    bindTable("live");
  </script>
</body>
</html>
"""


def _calc_consecutive_loss(trades: list[dict]) -> int:
    """计算当前最大连续亏损次数（从最近一笔往回数）。"""
    sorted_trades = sorted(trades, key=lambda x: x.get("buy_date", ""), reverse=True)
    count = 0
    for t in sorted_trades:
        if t.get("return", 0) < 0:
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# 主生成函数
# ---------------------------------------------------------------------------

def render_report(selection_result: dict) -> str:
    """渲染完整日报。

    selection_result: strategy_engine.run_selection() 的返回值
    """
    today = selection_result.get("date", dt.datetime.now().strftime("%Y-%m-%d"))
    config = _config_for_report(selection_result)
    trades = _load_trades()
    perf = _load_performance()
    version_info = _load_version()

    sections = [
        f"# A股尾盘隔夜策略报告 - {today}",
        "",
        f"> 生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"策略版本：{version_info.get('version', config.get('version', 'v1.0'))} | "
        f"纸面交易，不构成投资建议",
        "",
        _render_market_overview(selection_result.get("market_overview", {})),
        _render_performance(perf, version_info),
        _render_strategy_factor_contrib_section(config),
        _render_recommendations(selection_result.get("recommendations", []), config, selection_result),
        _render_history(trades),
        _render_live_execution_history(),
        _render_coverage_simulation(),
        _render_feedback_summary(),
        _render_strategy_diagnostics(config),
        _render_strategy_rules(config),
    ]

    # 附加降级/错误信息
    if selection_result.get("empty_reason"):
        sections.append(f"> 空仓原因：{selection_result['empty_reason']}")
        sections.append("")
    if selection_result.get("errors"):
        sections.append("## 附录：执行日志")
        sections.append("")
        for e in selection_result["errors"][-5:]:
            sections.append(f"- {e}")
        sections.append("")

    return "\n".join(sections)


def save_report(content: str, date_str: str = None) -> Path:
    """保存报告到 reports/YYYY-MM-DD.md。"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if date_str is None:
        date_str = dt.datetime.now().strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"{date_str}.md"
    with path.open("w", encoding="utf-8") as f:
        f.write(content)
    return path


def save_html_report(content: str, date_str: str = None) -> Path:
    """保存 HTML 报告到 reports/YYYY-MM-DD.html。"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if date_str is None:
        date_str = dt.datetime.now().strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"{date_str}.html"
    with path.open("w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate(selection_result: dict) -> Path:
    """完整生成并保存 Markdown 与 HTML 报告，返回 Markdown 路径。"""
    content = render_report(selection_result)
    html_content = render_html_report(selection_result)
    date_str = selection_result.get("date")
    md_path = save_report(content, date_str)
    save_html_report(html_content, date_str)
    return md_path


if __name__ == "__main__":
    # 模拟测试
    mock = {
        "date": dt.datetime.now().strftime("%Y-%m-%d"),
        "recommendations": [
            {"symbol": "600519", "name": "贵州茅台", "score": 85.5,
             "F1_tail_fund_inflow": 90, "F3_technical_pattern": 88,
             "F4_tail_rally_strength": 82, "sector": "白酒"},
        ],
        "market_overview": {"sh_pct": 0.012, "sz_pct": 0.008,
                             "cyb_pct": -0.003, "limit_up_count": 45,
                             "limit_down_count": 3, "source": "tencent"},
        "empty_reason": None,
        "errors": [],
    }
    path = generate(mock)
    print(f"报告已生成: {path}")
    print(path.read_text(encoding="utf-8")[:500])
