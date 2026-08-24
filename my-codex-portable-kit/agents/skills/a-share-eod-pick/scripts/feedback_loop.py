"""
A股尾盘隔夜策略 - 反馈闭环引擎

针对策略重大调整建立逆向反馈机制，覆盖 5 步：
    1) 调整记录（record_adjustment）
    2) 指标采集（collect_metrics）
    3) 影响分析（analyze_feedback）
    4) 优化方案（plan_optimization / implement_action）
    5) 闭环验证（verify_action / close_loop）

数据存储：data/strategy_samples.json + data/feedback/{adjustments,metrics_snapshots,feedback_actions}.json
"""

import json
import time
import socket
import datetime as dt
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_ROOT / "data"
FEEDBACK_DIR = DATA_DIR / "feedback"
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
TRADES_PATH = DATA_DIR / "trades.json"
SAMPLE_POOL_PATH = DATA_DIR / "strategy_samples.json"

ADJUSTMENTS_PATH = FEEDBACK_DIR / "adjustments.json"
SNAPSHOTS_PATH = FEEDBACK_DIR / "metrics_snapshots.json"
ACTIONS_PATH = FEEDBACK_DIR / "feedback_actions.json"

# 触发规则阈值
WIN_RATE_DELTA_NEG = -0.05     # 30日胜率下降5%
WIN_RATE_DELTA_POS = +0.05
RANKING_LOSS_DELTA_NEG = +0.10  # 排序损失上升10%
RANKING_LOSS_DELTA_POS = -0.10

CATEGORY_ENUM = {"data_source", "factor", "prefilter", "risk_control", "report"}
ADJ_STATUS_ENUM = {"open", "analyzing", "optimized", "closed", "rolled_back"}
ACTION_STATUS_ENUM = {"proposed", "in_progress", "implemented", "verified", "rejected"}
PRIORITY_ENUM = {"P0", "P1", "P2"}
FEEDBACK_TYPE_ENUM = {"positive", "negative", "neutral"}
SAMPLE_TYPES = ("historical_training", "live_paper")


def _empty_metric() -> dict:
    return {
        "samples": 0,
        "trade_samples": 0,
        "selected_days": 0,
        "executable_trades": 0,
        "skipped_executions": 0,
        "legacy_filled_trades": 0,
        "execution_coverage": 0,
        "gross_avg_return": 0,
        "net_avg_return": 0,
        "net_total_return": 0,
        "max_drawdown": 0,
        "empty_days": 0,
        "win_rate": 0,
        "avg_return": 0,
        "total_return": 0,
        "empty_rate": 0,
        "max_consecutive_loss": 0,
        "last_7d": {"samples": 0, "trade_samples": 0, "win_rate": 0, "avg_return": 0},
        "last_30d": {"samples": 0, "trade_samples": 0, "win_rate": 0, "avg_return": 0},
        "insufficient": True,
    }


# ---------------------------------------------------------------------------
# JSON 读写（自包含，避免与 optimizer/validator 循环依赖）
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _gen_id(prefix: str, existing_ids: list) -> str:
    """生成形如 PREFIX-YYYY-MM-DD-NNN 的 ID，NNN 自增。"""
    today = dt.datetime.now().strftime("%Y-%m-%d")
    base = f"{prefix}-{today}"
    n = 1
    while f"{base}-{n:03d}" in existing_ids:
        n += 1
    return f"{base}-{n:03d}"


# ---------------------------------------------------------------------------
# 统一样本池指标
# ---------------------------------------------------------------------------

def load_strategy_samples() -> list[dict]:
    """读取统一策略样本池。

    优先读取 data/strategy_samples.json；若尚未建立样本池，则将旧 trades.json
    兼容转换为 historical_training 交易样本，避免历史数据突然不可见。
    """
    doc = _load_json(SAMPLE_POOL_PATH)
    samples = doc.get("samples", [])
    if samples:
        return samples

    trades = _load_json(TRADES_PATH).get("trades", [])
    converted = []
    for t in trades:
        date = t.get("recommend_date") or t.get("buy_date")
        converted.append({
            "date": date,
            "sample_type": t.get("sample_type", "historical_training"),
            "selected": True,
            "symbol": t.get("symbol", ""),
            "name": t.get("name", ""),
            "score": t.get("score", 0),
            "buy_price": t.get("buy_price", 0),
            "sell_price": t.get("sell_price", 0),
            "return": t.get("return", 0),
            "win": bool(t.get("win", t.get("return", 0) > 0)),
            "factor_scores": t.get("factor_scores", {}),
            "source": "legacy_trades",
        })
    return converted


def _parse_sample_date(sample: dict):
    raw = sample.get("date") or sample.get("recommend_date") or sample.get("buy_date")
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _calc_sample_subset(samples: list[dict]) -> dict:
    if not samples:
        return _empty_metric()

    ordered = sorted(samples, key=lambda s: str(s.get("date") or s.get("buy_date") or ""))
    selected_samples = [s for s in ordered if s.get("selected", True)]
    empty_days = len(ordered) - len(selected_samples)
    skipped = [s for s in selected_samples if s.get("execution_status") == "skipped"]
    executable = [s for s in selected_samples if s.get("execution_status") != "skipped"]
    legacy = [s for s in executable if "execution_status" not in s]
    returns = [float(s.get("net_return", s.get("return", 0)) or 0) for s in executable]
    gross_returns = [float(s.get("gross_return", s.get("return", 0)) or 0) for s in executable]
    wins = [s for s, ret in zip(executable, returns) if ret > 0]

    max_consec = 0
    cur = 0
    for ret in returns:
        if ret > 0:
            cur = 0
        else:
            cur += 1
            max_consec = max(max_consec, cur)

    def _recent(days: int) -> dict:
        dated = [(s, _parse_sample_date(s)) for s in ordered]
        valid_dates = [d for _, d in dated if d is not None]
        if not valid_dates:
            return {"samples": 0, "trade_samples": 0, "win_rate": 0, "avg_return": 0}
        cutoff = max(valid_dates) - dt.timedelta(days=days)
        recent = [s for s, d in dated if d is not None and d >= cutoff]
        recent_trades = [s for s in recent if s.get("selected", True) and s.get("execution_status") != "skipped"]
        recent_returns = [float(s.get("net_return", s.get("return", 0)) or 0) for s in recent_trades]
        recent_wins = [s for s, ret in zip(recent_trades, recent_returns) if ret > 0]
        return {
            "samples": len(recent),
            "trade_samples": len(recent_trades),
            "win_rate": round(len(recent_wins) / len(recent_trades), 4) if recent_trades else 0,
            "avg_return": round(sum(recent_returns) / len(recent_returns), 4) if recent_returns else 0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for ret in returns:
        equity *= 1 + ret
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak if peak else 0)

    return {
        "samples": len(ordered),
        "trade_samples": len(executable),
        "selected_days": len(selected_samples),
        "executable_trades": len(executable),
        "skipped_executions": len(skipped),
        "legacy_filled_trades": len(legacy),
        "execution_coverage": round(len(executable) / len(selected_samples), 4) if selected_samples else 0,
        "empty_days": empty_days,
        "win_rate": round(len(wins) / len(executable), 4) if executable else 0,
        "avg_return": round(sum(returns) / len(returns), 4) if returns else 0,
        "total_return": round(sum(returns), 4),
        "gross_avg_return": round(sum(gross_returns) / len(gross_returns), 4) if gross_returns else 0,
        "net_avg_return": round(sum(returns) / len(returns), 4) if returns else 0,
        "net_total_return": round(sum(returns), 4),
        "empty_rate": round(empty_days / len(ordered), 4) if ordered else 0,
        "max_consecutive_loss": max_consec,
        "max_drawdown": round(max_drawdown, 4),
        "last_7d": _recent(7),
        "last_30d": _recent(30),
        "insufficient": len(executable) < 20,
    }


def compute_sample_metrics(samples: list[dict] | None = None) -> dict:
    """按历史训练、实际执行、综合三层统计统一样本池。"""
    if samples is None:
        samples = load_strategy_samples()

    normalized = []
    for s in samples:
        item = dict(s)
        item["sample_type"] = item.get("sample_type") or "historical_training"
        item["selected"] = bool(item.get("selected", True))
        normalized.append(item)

    result = {}
    for st in SAMPLE_TYPES:
        result[st] = _calc_sample_subset([s for s in normalized if s.get("sample_type") == st])
    result["combined"] = _calc_sample_subset(normalized)
    return result


# ---------------------------------------------------------------------------
# 数据源探针
# ---------------------------------------------------------------------------

def _probe_data_sources() -> dict:
    """探测各数据源可用性，返回 {source: status}。status ∈ ok|blocked|unavailable"""
    status = {}

    # 腾讯
    try:
        import data_loader
        q = data_loader.tencent_quote(["600519"])
        status["tencent"] = "ok" if q and q.get("600519", {}).get("price", 0) > 0 else "blocked"
    except Exception:
        status["tencent"] = "unavailable"

    # 东财 push2
    try:
        import data_loader
        if hasattr(data_loader, "em_get"):
            r = data_loader.em_get(
                "http://push2.eastmoney.com/api/qt/stock/get",
                params={"secid": "1.600519", "fields": "f117"},
                headers={"Referer": "https://quote.eastmoney.com/"},
                timeout=8,
            )
            data = r.json().get("data", {})
            status["eastmoney_push2"] = "ok" if data.get("f117") else "blocked"
        else:
            status["eastmoney_push2"] = "unavailable"
    except Exception:
        status["eastmoney_push2"] = "blocked"

    # mootdx
    try:
        import data_loader
        if hasattr(data_loader, "tdx_client"):
            client = data_loader.tdx_client()
            client.index(frequency=9, market=1, start=0, offset=1)
            status["mootdx"] = "ok"
        else:
            status["mootdx"] = "unavailable"
    except Exception:
        status["mootdx"] = "blocked"

    # akshare
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        status["akshare"] = "ok" if df is not None and not df.empty else "blocked"
    except Exception:
        status["akshare"] = "blocked"

    return status


# ---------------------------------------------------------------------------
# 指标采集
# ---------------------------------------------------------------------------

def collect_metrics(label: str, adjustment_id=None) -> str:
    """采集当前指标快照，写入 metrics_snapshots.json。返回 snapshot_id。"""
    samples = load_strategy_samples()
    sample_metrics = compute_sample_metrics(samples)

    # 旧 performance 字段保留为 combined 摘要，兼容现有状态展示和历史快照。
    combined = sample_metrics["combined"]
    perf = {
        "7d": combined["last_7d"],
        "30d": combined["last_30d"],
        "total": {
            "win_rate": combined["win_rate"],
            "avg_return": combined["avg_return"],
            "max_consecutive_loss": combined["max_consecutive_loss"],
            "samples": combined["trade_samples"],
            "empty_rate": combined["empty_rate"],
        },
        "updated_at": _now_iso(),
    }

    trade_samples = [s for s in samples if s.get("selected", True)]

    # 复用 optimizer 计算因子相关性 + 排序损失；失败时不阻断反馈快照。
    factor_corr = {}
    ranking_loss = 1.0
    try:
        import optimizer
        factor_corr = optimizer.compute_factor_correlations(trade_samples)
        ranking_loss = optimizer.compute_ranking_loss(trade_samples)
    except Exception as e:
        factor_corr = {"_error": str(e)}

    # 数据源探针
    try:
        sources = _probe_data_sources()
    except Exception as e:
        sources = {"_error": str(e)}

    # 配置版本
    config = _load_json(CONFIG_PATH)
    config_version = config.get("version", "unknown")

    snapshots_doc = _load_json(SNAPSHOTS_PATH)
    snapshots = snapshots_doc.get("snapshots", [])
    existing_ids = [s.get("id", "") for s in snapshots]
    sid = _gen_id("MS", existing_ids)

    snapshot = {
        "id": sid,
        "ts": _now_iso(),
        "label": label,
        "adjustment_id": adjustment_id,
        "sample_metrics": sample_metrics,
        "performance": perf,
        "factor_correlations": factor_corr,
        "ranking_loss": ranking_loss,
        "data_sources_status": sources,
        "trades_count": len(samples) if isinstance(samples, list) else 0,
        "config_version": config_version,
    }
    snapshots.append(snapshot)
    _save_json(SNAPSHOTS_PATH, {"snapshots": snapshots})
    return sid


# ---------------------------------------------------------------------------
# 调整记录
# ---------------------------------------------------------------------------

def record_adjustment(title: str, content: str, scope, goal: str,
                       category: str, expected_horizon_days: int = 30) -> str:
    """记录重大调整，自动采集 baseline 快照。返回 adjustment_id。

    Args:
        title: 调整标题（简短）
        content: 调整内容描述
        scope: 影响范围（list[str] 或逗号分隔字符串）
        goal: 调整目标
        category: data_source | factor | prefilter | risk_control | report
        expected_horizon_days: 预期观察周期（默认30天）
    """
    if category not in CATEGORY_ENUM:
        raise ValueError(f"category 必须是 {CATEGORY_ENUM} 之一")
    if isinstance(scope, str):
        scope = [s.strip() for s in scope.split(",") if s.strip()]

    doc = _load_json(ADJUSTMENTS_PATH)
    adjustments = doc.get("adjustments", [])
    existing_ids = [a.get("id", "") for a in adjustments]
    aid = _gen_id("ADJ", existing_ids)

    now = dt.datetime.now()
    first_analysis_due = (now + dt.timedelta(days=7)).strftime("%Y-%m-%d")
    closure_due = (now + dt.timedelta(days=expected_horizon_days)).strftime("%Y-%m-%d")

    # 自动采集 baseline
    baseline_sid = collect_metrics(
        label=f"baseline_pre_adjustment",
        adjustment_id=aid,
    )

    adjustment = {
        "id": aid,
        "title": title,
        "content": content,
        "scope": scope,
        "goal": goal,
        "category": category,
        "created_at": _now_iso(),
        "baseline_snapshot_id": baseline_sid,
        "post_snapshot_ids": [],
        "status": "open",
        "expected_horizon_days": expected_horizon_days,
        "timeline": {
            "baseline_collected_at": _now_iso(),
            "first_analysis_due": first_analysis_due,
            "closure_due": closure_due,
            "first_analysis_at": None,
            "closed_at": None,
        },
    }
    adjustments.append(adjustment)
    _save_json(ADJUSTMENTS_PATH, {"adjustments": adjustments})
    return aid


# ---------------------------------------------------------------------------
# 影响分析（自动识别正负反馈）
# ---------------------------------------------------------------------------

def analyze_feedback(adjustment_id: str) -> dict:
    """对比 baseline 与最新 snapshot，自动生成 findings 写入 feedback_actions.json。"""
    doc = _load_json(ADJUSTMENTS_PATH)
    adjustments = doc.get("adjustments", [])
    adj = next((a for a in adjustments if a["id"] == adjustment_id), None)
    if not adj:
        return {"error": f"adjustment {adjustment_id} 不存在"}

    snapshots_doc = _load_json(SNAPSHOTS_PATH)
    snapshots = snapshots_doc.get("snapshots", [])

    baseline_id = adj.get("baseline_snapshot_id")
    baseline = next((s for s in snapshots if s["id"] == baseline_id), None)
    if not baseline:
        return {"error": "未找到 baseline snapshot"}

    # 采集当前快照
    post_sid = collect_metrics(label=f"post_check_{dt.datetime.now().strftime('%Y%m%d')}",
                                adjustment_id=adjustment_id)
    post = next((s for s in snapshots if s["id"] == post_sid), None)
    if not post:
        post = _load_json(SNAPSHOTS_PATH).get("snapshots", [])[-1]

    # 追加 post_snapshot_ids
    post_ids = adj.get("post_snapshot_ids", [])
    if post_sid not in post_ids:
        post_ids.append(post_sid)
        adj["post_snapshot_ids"] = post_ids

    # 更新状态
    if adj["status"] == "open":
        adj["status"] = "analyzing"
    adj["timeline"]["first_analysis_at"] = _now_iso()
    _save_json(ADJUSTMENTS_PATH, {"adjustments": adjustments})

    # 对比生成 findings
    findings = _compare_snapshots(baseline, post)

    # 写入 feedback_actions.json
    actions_doc = _load_json(ACTIONS_PATH)
    actions = actions_doc.get("actions", [])
    existing_ids = [a.get("id", "") for a in actions]
    new_actions = []
    for f in findings:
        fa_id = _gen_id("FA", existing_ids + [a["id"] for a in new_actions])
        action = {
            "id": fa_id,
            "adjustment_id": adjustment_id,
            "finding": f["finding"],
            "feedback_type": f["feedback_type"],
            "impact": f["impact"],
            "proposed_optimization": f.get("proposed_optimization", ""),
            "priority": f["priority"],
            "status": "proposed",
            "metric_baseline": f.get("baseline"),
            "metric_post": f.get("post"),
            "metric_delta": f.get("delta"),
            "created_at": _now_iso(),
            "resolved_at": None,
            "verification": None,
        }
        new_actions.append(action)
        actions.append(action)

    _save_json(ACTIONS_PATH, {"actions": actions})

    return {
        "adjustment_id": adjustment_id,
        "baseline_snapshot_id": baseline_id,
        "post_snapshot_id": post_sid,
        "new_findings_count": len(new_actions),
        "findings": findings,
    }


def _compare_snapshots(baseline: dict, post: dict) -> list:
    """对比两个 snapshot，返回 findings 列表。"""
    findings = []

    b_sm = baseline.get("sample_metrics", {})
    p_sm = post.get("sample_metrics", {})
    if b_sm or p_sm:
        findings.extend(_compare_sample_metrics(b_sm, p_sm))

    # 1. 胜率对比（30d）
    b_perf = baseline.get("performance", {})
    p_perf = post.get("performance", {})
    b_wr_30 = b_perf.get("30d", {}).get("win_rate", 0)
    p_wr_30 = p_perf.get("30d", {}).get("win_rate", 0)
    wr_delta = p_wr_30 - b_wr_30
    if abs(wr_delta) >= abs(WIN_RATE_DELTA_NEG):
        if wr_delta <= WIN_RATE_DELTA_NEG:
            findings.append({
                "finding": f"30日胜率下降 {wr_delta:+.2%}",
                "feedback_type": "negative",
                "impact": "策略整体表现恶化，需检查调整是否引入回归",
                "priority": "P0",
                "baseline": b_wr_30, "post": p_wr_30, "delta": wr_delta,
                "proposed_optimization": "回滚调整或下调相关因子权重",
            })
        elif wr_delta >= WIN_RATE_DELTA_POS:
            findings.append({
                "finding": f"30日胜率提升 {wr_delta:+.2%}",
                "feedback_type": "positive",
                "impact": "调整带来正向收益，可作为后续优化基线",
                "priority": "P2",
                "baseline": b_wr_30, "post": p_wr_30, "delta": wr_delta,
            })

    # 2. 排序损失对比
    b_rl = baseline.get("ranking_loss", 1.0)
    p_rl = post.get("ranking_loss", 1.0)
    rl_delta = p_rl - b_rl
    if rl_delta >= RANKING_LOSS_DELTA_NEG:
        findings.append({
            "finding": f"排序损失上升 {rl_delta:+.4f}（{b_rl:.4f} → {p_rl:.4f}）",
            "feedback_type": "negative",
            "impact": "因子打分排序与实际收益率一致性下降",
            "priority": "P1",
            "baseline": b_rl, "post": p_rl, "delta": rl_delta,
            "proposed_optimization": "触发 optimize_weekly 重新校准权重",
        })
    elif rl_delta <= RANKING_LOSS_DELTA_POS:
        findings.append({
            "finding": f"排序损失下降 {rl_delta:+.4f}（{b_rl:.4f} → {p_rl:.4f}）",
            "feedback_type": "positive",
            "impact": "因子打分排序与实际收益率一致性提升",
            "priority": "P2",
            "baseline": b_rl, "post": p_rl, "delta": rl_delta,
        })

    # 3. 数据源可用性对比
    b_src = baseline.get("data_sources_status", {})
    p_src = post.get("data_sources_status", {})
    for src in set(b_src.keys()) | set(p_src.keys()):
        b_st = b_src.get(src, "unknown")
        p_st = p_src.get(src, "unknown")
        if b_st == "ok" and p_st in ("blocked", "unavailable"):
            prio = "P0" if src in ("tencent", "mootdx") else "P1"
            findings.append({
                "finding": f"数据源 {src} 从 ok 变为 {p_st}",
                "feedback_type": "negative",
                "impact": f"{src} 不可用，相关因子降级或失效",
                "priority": prio,
                "baseline": b_st, "post": p_st, "delta": None,
                "proposed_optimization": f"检查 {src} 网络/IP 或启用备选源",
            })
        elif b_st in ("blocked", "unavailable") and p_st == "ok":
            findings.append({
                "finding": f"数据源 {src} 从 {b_st} 恢复为 ok",
                "feedback_type": "positive",
                "impact": f"{src} 恢复可用，相关因子可正常计算",
                "priority": "P2",
                "baseline": b_st, "post": p_st, "delta": None,
            })

    # 4. 触发风控阈值
    config = _load_json(CONFIG_PATH)
    rc = config.get("risk_control", {})
    for period, alert_key in [("7d", "win_rate_7d_alert"), ("30d", "win_rate_30d_alert")]:
        threshold = rc.get(alert_key, 0)
        p_wr = p_perf.get(period, {}).get("win_rate", 0)
        if threshold > 0 and p_wr < threshold and p_perf.get(period, {}).get("samples", 0) >= 5:
            findings.append({
                "finding": f"{period}胜率 {p_wr:.2%} 低于告警阈值 {threshold:.2%}",
                "feedback_type": "negative",
                "impact": "触发策略告警，需考虑空仓或参数调整",
                "priority": "P0",
                "baseline": b_perf.get(period, {}).get("win_rate", 0),
                "post": p_wr, "delta": None,
                "proposed_optimization": "检查是否需要 cooldown_days_after_max_loss 或降仓",
            })

    return findings


def _finding(finding: str, feedback_type: str, impact: str, priority: str,
             baseline=None, post=None, delta=None, proposed_optimization="") -> dict:
    return {
        "finding": finding,
        "feedback_type": feedback_type,
        "impact": impact,
        "priority": priority,
        "baseline": baseline,
        "post": post,
        "delta": delta,
        "proposed_optimization": proposed_optimization,
        "status_hint": "suggestion_only",
    }


def _compare_sample_metrics(baseline: dict, post: dict) -> list[dict]:
    """按样本分层对比调整前后表现，只生成建议，不修改参数。"""
    findings = []

    labels = {
        "historical_training": "历史训练",
        "live_paper": "实际执行",
        "combined": "综合",
    }

    for key, label in labels.items():
        b = baseline.get(key, _empty_metric())
        p = post.get(key, _empty_metric())

        b_wr = b.get("win_rate", 0)
        p_wr = p.get("win_rate", 0)
        wr_delta = p_wr - b_wr
        if p.get("trade_samples", 0) >= 5 and wr_delta <= WIN_RATE_DELTA_NEG:
            findings.append(_finding(
                f"{label}胜率下降 {wr_delta:+.2%}",
                "negative",
                f"{label}样本显示策略表现转弱，需要复核最近调整和样本分布",
                "P0" if key in ("combined", "live_paper") else "P1",
                b_wr,
                p_wr,
                wr_delta,
                "保持参数不自动修改，建议人工检查因子权重、阈值与近期失败样本",
            ))
        elif p.get("trade_samples", 0) >= 5 and wr_delta >= WIN_RATE_DELTA_POS:
            findings.append(_finding(
                f"{label}胜率提升 {wr_delta:+.2%}",
                "positive",
                f"{label}样本显示调整方向可能有效，可作为后续观察基线",
                "P2",
                b_wr,
                p_wr,
                wr_delta,
                "暂不自动调参，建议继续累计样本验证稳定性",
            ))

        b_empty = b.get("empty_rate", 0)
        p_empty = p.get("empty_rate", 0)
        empty_delta = p_empty - b_empty
        sample_count = p.get("samples", 0) or p.get("trade_samples", 0)
        if sample_count >= 5 and empty_delta >= 0.10:
            findings.append(_finding(
                f"{label}空仓率上升 {empty_delta:+.2%}",
                "negative",
                "策略出手机会减少，可能由阈值过高、数据缺失或过滤条件过严导致",
                "P1",
                b_empty,
                p_empty,
                empty_delta,
                "建议检查分数阈值、预过滤条件和数据源完整性",
            ))

        b_loss = b.get("max_consecutive_loss", 0)
        p_loss = p.get("max_consecutive_loss", 0)
        if p_loss - b_loss >= 2 and p_loss >= 3:
            findings.append(_finding(
                f"{label}最大连亏扩大 {b_loss} → {p_loss}",
                "negative",
                "连续亏损风险升高，需检查是否触发冷却或空仓机制",
                "P0" if key in ("combined", "live_paper") else "P1",
                b_loss,
                p_loss,
                p_loss - b_loss,
                "建议人工评估 cooldown 和风险阈值，不自动修改参数",
            ))

    hist = post.get("historical_training", _empty_metric())
    live = post.get("live_paper", _empty_metric())
    if hist.get("trade_samples", 0) >= 5 and live.get("trade_samples", 0) >= 5:
        gap = live.get("win_rate", 0) - hist.get("win_rate", 0)
        if gap <= -0.10:
            findings.append(_finding(
                f"实际执行胜率低于历史训练 {gap:+.2%}",
                "negative",
                "真实纸面执行明显弱于历史训练，可能存在数据时点、滑点或样本漂移",
                "P0",
                hist.get("win_rate", 0),
                live.get("win_rate", 0),
                gap,
                "建议单独复盘实际执行样本，暂不依据历史样本继续强化参数",
            ))

    return findings


# ---------------------------------------------------------------------------
# 优化方案制定 / 实施 / 验证
# ---------------------------------------------------------------------------

def plan_optimization(action_id: str, proposed_solution: str, priority: str) -> bool:
    """为指定 finding 制定优化方案。"""
    if priority not in PRIORITY_ENUM:
        raise ValueError(f"priority 必须是 {PRIORITY_ENUM} 之一")
    doc = _load_json(ACTIONS_PATH)
    actions = doc.get("actions", [])
    action = next((a for a in actions if a["id"] == action_id), None)
    if not action:
        return False
    action["proposed_optimization"] = proposed_solution
    action["priority"] = priority
    action["status"] = "in_progress"
    _save_json(ACTIONS_PATH, {"actions": actions})
    return True


def implement_action(action_id: str, implementation_notes: str) -> bool:
    """标记行动项已实施。"""
    doc = _load_json(ACTIONS_PATH)
    actions = doc.get("actions", [])
    action = next((a for a in actions if a["id"] == action_id), None)
    if not action:
        return False
    action["status"] = "implemented"
    action["implementation_notes"] = implementation_notes
    action["implemented_at"] = _now_iso()
    _save_json(ACTIONS_PATH, {"actions": actions})

    # 同步更新 adjustment 状态
    _sync_adjustment_status(action["adjustment_id"])
    return True


def verify_action(action_id: str, verification_result: str, improved: bool) -> bool:
    """验证行动项效果。improved=True 表示验证为改善。"""
    doc = _load_json(ACTIONS_PATH)
    actions = doc.get("actions", [])
    action = next((a for a in actions if a["id"] == action_id), None)
    if not action:
        return False
    action["status"] = "verified"
    action["verification"] = {"result": verification_result, "improved": improved}
    action["resolved_at"] = _now_iso()
    _save_json(ACTIONS_PATH, {"actions": actions})
    return True


def reject_action(action_id: str, reason: str) -> bool:
    """拒绝行动项（不实施）。"""
    doc = _load_json(ACTIONS_PATH)
    actions = doc.get("actions", [])
    action = next((a for a in actions if a["id"] == action_id), None)
    if not action:
        return False
    action["status"] = "rejected"
    action["verification"] = {"result": reason, "improved": False}
    action["resolved_at"] = _now_iso()
    _save_json(ACTIONS_PATH, {"actions": actions})
    return True


def _sync_adjustment_status(adjustment_id: str):
    """根据关联 action 状态同步 adjustment 状态。"""
    doc = _load_json(ADJUSTMENTS_PATH)
    adjustments = doc.get("adjustments", [])
    adj = next((a for a in adjustments if a["id"] == adjustment_id), None)
    if not adj:
        return
    actions_doc = _load_json(ACTIONS_PATH)
    actions = [a for a in actions_doc.get("actions", [])
               if a.get("adjustment_id") == adjustment_id]
    if not actions:
        return
    implemented_count = sum(1 for a in actions if a["status"] in ("implemented", "verified"))
    if implemented_count > 0 and adj["status"] == "analyzing":
        adj["status"] = "optimized"
        _save_json(ADJUSTMENTS_PATH, {"adjustments": adjustments})


# ---------------------------------------------------------------------------
# 闭环关闭
# ---------------------------------------------------------------------------

def close_loop(adjustment_id: str, summary: str) -> dict:
    """关闭闭环。要求所有 action ∈ {verified, rejected}。"""
    doc = _load_json(ADJUSTMENTS_PATH)
    adjustments = doc.get("adjustments", [])
    adj = next((a for a in adjustments if a["id"] == adjustment_id), None)
    if not adj:
        return {"error": f"adjustment {adjustment_id} 不存在"}

    actions_doc = _load_json(ACTIONS_PATH)
    actions = [a for a in actions_doc.get("actions", [])
               if a.get("adjustment_id") == adjustment_id]
    pending = [a for a in actions if a["status"] not in ("verified", "rejected")]
    if pending:
        return {
            "error": "存在未关闭的 action",
            "pending_ids": [a["id"] for a in pending],
        }

    adj["status"] = "closed"
    adj["timeline"]["closed_at"] = _now_iso()
    adj["closure_summary"] = summary
    _save_json(ADJUSTMENTS_PATH, {"adjustments": adjustments})
    return {"adjustment_id": adjustment_id, "status": "closed", "summary": summary}


# ---------------------------------------------------------------------------
# 质量指标仪表板
# ---------------------------------------------------------------------------

def _compute_quality_metrics() -> dict:
    """计算 5 项质量评估指标（本月）。"""
    adj_doc = _load_json(ADJUSTMENTS_PATH)
    act_doc = _load_json(ACTIONS_PATH)
    adjustments = adj_doc.get("adjustments", [])
    actions = act_doc.get("actions", [])

    now = dt.datetime.now()
    month_prefix = now.strftime("%Y-%m")
    month_adjs = [a for a in adjustments if a.get("created_at", "").startswith(month_prefix)]
    month_acts = [a for a in actions if a.get("created_at", "").startswith(month_prefix)]

    # 1. 数据完整度：必填字段填写率
    required_adj_fields = ["id", "title", "content", "scope", "goal", "category",
                           "created_at", "baseline_snapshot_id", "status"]
    filled = 0
    total = 0
    for a in month_adjs:
        for f in required_adj_fields:
            total += 1
            if a.get(f) not in (None, "", []):
                filled += 1
    completeness = filled / total if total > 0 else 1.0

    # 2. 时效达成率：按时完成阶段数 / 应完成阶段数
    today_str = now.strftime("%Y-%m-%d")
    due_stages = 0
    on_time_stages = 0
    for a in month_adjs:
        # baseline 阶段
        due_stages += 1
        if a.get("baseline_snapshot_id"):
            on_time_stages += 1
        # 首次分析阶段
        if a.get("timeline", {}).get("first_analysis_due", "") <= today_str:
            due_stages += 1
            if a.get("timeline", {}).get("first_analysis_at"):
                on_time_stages += 1
        # 闭环阶段
        closure_due = a.get("timeline", {}).get("closure_due", "")
        if closure_due <= today_str:
            due_stages += 1
            if a.get("status") == "closed":
                on_time_stages += 1
    timeliness = on_time_stages / due_stages if due_stages > 0 else 1.0

    # 3. 反馈转化率：(verified + implemented) / 总 findings
    resolved = sum(1 for a in month_acts if a["status"] in ("verified", "implemented"))
    conversion = resolved / len(month_acts) if month_acts else 0.0

    # 4. 闭环完成率：closed / opened（本月）
    closed = sum(1 for a in month_adjs if a["status"] == "closed")
    closure_rate = closed / len(month_adjs) if month_adjs else 0.0

    # 5. 优化有效率：verified 为改善 / closed
    verified_improved = sum(1 for a in month_acts
                             if a["status"] == "verified"
                             and a.get("verification", {}).get("improved"))
    closed_count = sum(1 for a in month_adjs if a["status"] == "closed")
    effectiveness = verified_improved / closed_count if closed_count > 0 else 0.0

    return {
        "period": month_prefix,
        "data_completeness": round(completeness, 4),
        "timeliness": round(timeliness, 4),
        "feedback_conversion": round(conversion, 4),
        "closure_rate": round(closure_rate, 4),
        "optimization_effectiveness": round(effectiveness, 4),
        "targets": {
            "data_completeness": 0.95,
            "timeliness": 0.90,
            "feedback_conversion": 0.70,
            "closure_rate": 0.80,
            "optimization_effectiveness": 0.60,
        },
        "samples": {
            "adjustments_opened": len(month_adjs),
            "adjustments_closed": closed,
            "actions_total": len(month_acts),
            "actions_verified_improved": verified_improved,
        },
    }


# ---------------------------------------------------------------------------
# 状态展示
# ---------------------------------------------------------------------------

def show_feedback_status(adjustment_id=None) -> str:
    """展示调整列表 + 行动项 + 质量仪表板。"""
    adj_doc = _load_json(ADJUSTMENTS_PATH)
    act_doc = _load_json(ACTIONS_PATH)
    snap_doc = _load_json(SNAPSHOTS_PATH)
    adjustments = adj_doc.get("adjustments", [])
    actions = act_doc.get("actions", [])
    snapshots = snap_doc.get("snapshots", [])

    lines = ["=" * 60, "反馈闭环状态", "=" * 60, ""]

    if not adjustments:
        lines.append("暂无调整记录。使用 record_adjustment 录入首次调整。")
        lines.append("")
    else:
        target_adjs = [a for a in adjustments if not adjustment_id or a["id"] == adjustment_id]
        for a in target_adjs:
            lines.append(f"[{a['id']}] {a['title']}  ({a['status']})")
            lines.append(f"  分类: {a['category']} | 目标: {a['goal']}")
            lines.append(f"  范围: {', '.join(a['scope'])}")
            tl = a.get("timeline", {})
            lines.append(f"  创建: {a.get('created_at', '-')}")
            lines.append(f"  Baseline: {a.get('baseline_snapshot_id', '-')}")
            lines.append(f"  首次分析 due: {tl.get('first_analysis_due', '-')} "
                         f"(完成: {tl.get('first_analysis_at', '待执行')})")
            lines.append(f"  闭环 due: {tl.get('closure_due', '-')} "
                         f"(关闭: {tl.get('closed_at', '待关闭')})")
            # 关联 actions
            rel_acts = [ac for ac in actions if ac.get("adjustment_id") == a["id"]]
            if rel_acts:
                lines.append(f"  行动项 ({len(rel_acts)}):")
                for ac in rel_acts:
                    flag = {"P0": "⚠️", "P1": "!", "P2": "·"}.get(ac["priority"], "·")
                    lines.append(f"    {flag} [{ac['status']}] {ac['id']}: {ac['finding']}")
                    if ac.get("proposed_optimization"):
                        lines.append(f"        方案: {ac['proposed_optimization']}")
            lines.append("")

    # 质量仪表板
    qm = _compute_quality_metrics()
    lines.append("-" * 60)
    lines.append(f"质量指标仪表板（{qm['period']}）")
    lines.append("-" * 60)
    lines.append(f"数据完整度: {qm['data_completeness']:.1%}  (目标 ≥{qm['targets']['data_completeness']:.0%})")
    lines.append(f"时效达成率: {qm['timeliness']:.1%}  (目标 ≥{qm['targets']['timeliness']:.0%})")
    lines.append(f"反馈转化率: {qm['feedback_conversion']:.1%}  (目标 ≥{qm['targets']['feedback_conversion']:.0%})")
    lines.append(f"闭环完成率: {qm['closure_rate']:.1%}  (目标 ≥{qm['targets']['closure_rate']:.0%})")
    lines.append(f"优化有效率: {qm['optimization_effectiveness']:.1%}  (目标 ≥{qm['targets']['optimization_effectiveness']:.0%})")
    lines.append("")
    lines.append(f"快照总数: {len(snapshots)} | 调整总数: {len(adjustments)} | 行动项总数: {len(actions)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def cli_record_adjustment(args):
    aid = record_adjustment(
        title=args.title,
        content=args.content,
        scope=args.scope,
        goal=args.goal,
        category=args.category,
        expected_horizon_days=args.horizon,
    )
    print(f"已记录调整: {aid}")
    print(f"Baseline 快照已采集")
    print(show_feedback_status(aid))


def cli_collect_metrics(args):
    sid = collect_metrics(label=args.label, adjustment_id=args.adjustment_id)
    print(f"已采集快照: {sid}")


def cli_analyze_feedback(args):
    result = analyze_feedback(args.adjustment_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    print(show_feedback_status(args.adjustment_id))


def cli_feedback_status(args):
    print(show_feedback_status(args.adjustment_id))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="反馈闭环引擎")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("record", help="记录重大调整")
    p1.add_argument("--title", required=True)
    p1.add_argument("--content", required=True)
    p1.add_argument("--scope", required=True, help="逗号分隔的文件列表")
    p1.add_argument("--goal", required=True)
    p1.add_argument("--category", required=True,
                    choices=list(CATEGORY_ENUM))
    p1.add_argument("--horizon", type=int, default=30)
    p1.set_defaults(func=cli_record_adjustment)

    p2 = sub.add_parser("collect", help="采集指标快照")
    p2.add_argument("--label", required=True)
    p2.add_argument("--adjustment-id", default=None)
    p2.set_defaults(func=cli_collect_metrics)

    p3 = sub.add_parser("analyze", help="分析反馈")
    p3.add_argument("--adjustment-id", required=True)
    p3.set_defaults(func=cli_analyze_feedback)

    p4 = sub.add_parser("status", help="展示反馈状态")
    p4.add_argument("--adjustment-id", default=None)
    p4.set_defaults(func=cli_feedback_status)

    args = parser.parse_args()
    args.func(args)
