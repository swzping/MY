"""
A股尾盘隔夜策略 - 次日验证模块

验证口径：T 日尾盘建议价买入，T+1 日开盘价卖出。
run_today_report 会先执行轻量昨日同步，只处理最近一个可验证交易日，
不触发历史训练或全市场股票池构建。
"""

import json
import datetime as dt
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

import data_loader
import execution_model as paper_execution_model

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = SKILL_ROOT / "reports"
DATA_DIR = SKILL_ROOT / "data"
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
TRADES_PATH = DATA_DIR / "trades.json"
PERF_PATH = DATA_DIR / "performance.json"
SAMPLE_POOL_PATH = DATA_DIR / "strategy_samples.json"
CACHE_DB = DATA_DIR / "cache" / "backtest_kline.db"


def _now() -> dt.datetime:
    return dt.datetime.now()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_config() -> dict:
    return _load_json(CONFIG_PATH)


def _load_trades() -> list[dict]:
    return _load_json(TRADES_PATH).get("trades", [])


def _save_trades(trades: list[dict]):
    _save_json(TRADES_PATH, {"trades": trades, "updated_at": _now().isoformat()})


def _save_live_samples(trades: list[dict]):
    """将真实纸面验证结果写入统一样本池，按 date+sample_type upsert。"""
    doc = _load_json(SAMPLE_POOL_PATH)
    samples = doc.get("samples", [])
    merged = {
        (s.get("date"), s.get("sample_type", "historical_training")): s
        for s in samples
    }
    for t in trades:
        selected = bool(t.get("selected", True))
        sample = {
            "date": t.get("recommend_date") or t.get("buy_date"),
            "sample_type": "live_paper",
            "selected": selected,
            "symbol": t.get("symbol", ""),
            "name": _resolve_stock_name(t.get("symbol", ""), t.get("name", "")),
            "buy_date": t.get("buy_date", ""),
            "sell_date": t.get("sell_date", ""),
            "buy_price": t.get("buy_price", 0),
            "sell_price": t.get("sell_price", 0),
            "return": t.get("return", 0),
            "win": t.get("return", 0) > 0,
            "sell_reason": t.get("sell_reason", ""),
        }
        for key in (
            "selected_at", "selection_date", "score", "sector", "factor_scores",
            "buy_price_source", "sell_price_source", "strategy_case", "action",
            "entry_price_source", "next_check_at", "opportunity_score",
            "execution_status", "skip_reason", "gross_return", "net_return",
            "raw_entry_price", "raw_exit_price", "entry_slippage_bps",
            "exit_slippage_bps", "commission_rate", "stamp_duty_rate",
        ):
            if key in t:
                sample[key] = t[key]
        if not selected:
            sample["empty_reason"] = t.get("empty_reason", "空仓")
        key = (sample["date"], "live_paper")
        merged[key] = sample

    ordered = sorted(
        merged.values(),
        key=lambda s: (str(s.get("date", "")), str(s.get("sample_type", ""))),
    )
    _save_json(SAMPLE_POOL_PATH, {"samples": ordered, "updated_at": _now().isoformat()})


def _resolve_stock_name(symbol: str, current_name: str = "") -> str:
    """补全股票名称，优先保留当时快照，其次腾讯行情、A股清单、历史样本。"""
    if current_name:
        return current_name
    if not symbol:
        return ""
    try:
        quote = data_loader.tencent_quote([symbol])
        name = quote.get(symbol, {}).get("name", "")
        if name:
            return str(name)
    except Exception:
        pass
    try:
        symbols_df = data_loader.get_a_share_symbols()
        if not symbols_df.empty:
            row = symbols_df[symbols_df["symbol"].astype(str).str.zfill(6) == symbol]
            if not row.empty:
                name = row.iloc[0].get("name", "")
                if name:
                    return str(name)
    except Exception:
        pass
    for sample in _load_json(SAMPLE_POOL_PATH).get("samples", []):
        if sample.get("symbol") == symbol and sample.get("name"):
            return str(sample["name"])
    return ""


# ---------------------------------------------------------------------------
# 价格获取
# ---------------------------------------------------------------------------

def get_buy_price(symbol: str, date_str: str) -> Optional[float]:
    """旧版盘中验证 helper：获取 T+1 日 9:30-9:40 开盘段均价。

    date_str: T+1 日，格式 YYYY-MM-DD
    """
    # 优先分钟数据
    try:
        df = data_loader.get_daily_kline(symbol, days=5)
        if not df.empty and "date" in df.columns:
            # 日K只给收盘，分钟数据需另外拉
            pass
    except Exception:
        pass

    # 用 akshare 分钟数据
    try:
        import akshare as ak
        start = date_str.replace("-", "") + " 09:30:00"
        end = date_str.replace("-", "") + " 09:40:00"
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1",
                                        start_date=start, end_date=end)
        if df is not None and not df.empty:
            return float(df["收盘"].mean())
    except Exception as e:
        print(f"[validator] 分钟数据获取失败 {symbol}: {e}")

    # 降级：用当日开盘价
    try:
        rt = data_loader.get_realtime_quotes([symbol])
        if not rt.empty:
            return float(rt.iloc[0].get("open", 0))
    except Exception:
        pass

    return None


def get_sell_price(symbol: str, date_str: str, buy_price: float,
                    config: dict) -> tuple[float, str]:
    """旧版盘中验证 helper：获取卖出价及卖出原因。

    返回 (sell_price, reason)
    reason: 'close' | 'stop_loss' | 'take_profit'
    """
    rc = config.get("validation", {})
    stop_loss = rc.get("stop_loss", -0.03)
    take_profit = rc.get("take_profit", 0.05)

    # 尝试获取全日分钟数据判断是否触发止损/止盈
    try:
        import akshare as ak
        start = date_str.replace("-", "") + " 09:30:00"
        end = date_str.replace("-", "") + " 15:00:00"
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1",
                                        start_date=start, end_date=end)
        if df is not None and not df.empty:
            df = df.rename(columns={"收盘": "close", "时间": "time"})
            df["time"] = pd.to_datetime(df["time"])
            # 检查止损
            for _, row in df.iterrows():
                ret = (row["close"] - buy_price) / buy_price
                if ret <= stop_loss:
                    return float(row["close"]), "stop_loss"
                if ret >= take_profit:
                    return float(row["close"]), "take_profit"
            # 未触发，用收盘价
            return float(df.iloc[-1]["close"]), "close"
    except Exception as e:
        print(f"[validator] 分钟数据获取失败 {symbol}: {e}")

    # 降级：用日K收盘价
    try:
        df = data_loader.get_daily_kline(symbol, days=5)
        if not df.empty:
            return float(df.iloc[-1]["close"]), "close"
    except Exception:
        pass

    # 再降级：实时价格
    try:
        rt = data_loader.get_realtime_quotes([symbol])
        if not rt.empty:
            return float(rt.iloc[0].get("price", 0)), "close"
    except Exception:
        pass

    return buy_price, "no_data"  # 无法获取，按平价处理


# ---------------------------------------------------------------------------
# 单笔验证
# ---------------------------------------------------------------------------

def _is_valid_kline_row(row) -> bool:
    """基础日K质量校验，避免异常/占位行情进入验证收益。"""
    try:
        open_p = float(row.get("open", 0))
        high = float(row.get("high", 0))
        low = float(row.get("low", 0))
        close = float(row.get("close", 0))
        volume = float(row.get("volume", 0))
        amount = float(row.get("amount", 0))
    except Exception:
        return False
    if min(open_p, high, low, close) <= 0:
        return False
    if high < max(open_p, close, low) or low > min(open_p, close, high):
        return False
    if volume <= 0 or amount <= 0:
        return False
    return True


def _tail_advice_proxy_price(t_row: pd.Series) -> tuple[float | None, str]:
    try:
        open_p = float(t_row["open"])
        high = float(t_row["high"])
        low = float(t_row["low"])
        close = float(t_row["close"])
    except Exception:
        return None, "T_tail_advice_proxy_bad_kline"
    if min(open_p, high, low, close) <= 0 or high < low:
        return None, "T_tail_advice_proxy_bad_kline"
    midpoint = (high + low) / 2
    return (close * 2 + midpoint) / 3, "T_tail_advice_proxy_no_minutes"


def validate_close_to_next_open(symbol: str, name: str, recommend_date: str,
                                validate_date: str, recommendation: dict = None) -> dict:
    """按 T 尾盘建议执行价 → T+1 开盘口径轻量验证单只推荐。"""
    recommendation = recommendation or {}
    name = _resolve_stock_name(symbol, name or recommendation.get("name", ""))
    base_meta = {
        "selected_at": recommendation.get("selected_at", ""),
        "selection_date": recommendation.get("selection_date", recommend_date),
        "score": recommendation.get("score", 0),
        "sector": recommendation.get("sector", ""),
        "factor_scores": recommendation.get("factor_scores", {}),
        "strategy_case": recommendation.get("strategy_case", "tail_confirm"),
        "action": recommendation.get("action", "TAIL_CONFIRM"),
        "entry_price_source": recommendation.get("entry_price_source", "tail_advice_price"),
        "next_check_at": recommendation.get("next_check_at", ""),
        "opportunity_score": recommendation.get("opportunity_score", 0),
    }
    try:
        df = _load_cached_validation_kline(symbol, recommend_date, validate_date)
        if df.empty:
            df = data_loader.get_daily_kline(symbol, days=10)
    except Exception as e:
        return {
            **base_meta,
            "symbol": symbol, "name": name,
            "recommend_date": recommend_date,
            "buy_date": recommend_date,
            "sell_date": validate_date,
            "selected": False,
            "empty_reason": f"数据不足以验证: {e}",
            "buy_price": 0, "sell_price": 0, "return": 0,
            "win": False, "sell_reason": "no_valid_kline",
        }

    if df is None or df.empty or "date" not in df.columns:
        return {
            **base_meta,
            "symbol": symbol, "name": name,
            "recommend_date": recommend_date,
            "buy_date": recommend_date,
            "sell_date": validate_date,
            "selected": False,
            "empty_reason": "数据不足以验证: 日K缺失",
            "buy_price": 0, "sell_price": 0, "return": 0,
            "win": False, "sell_reason": "no_valid_kline",
        }

    df = df.copy()
    df["date"] = df["date"].astype(str).str[:10]
    t_rows = df[df["date"] == recommend_date]
    t1_rows = df[df["date"] == validate_date]
    if t_rows.empty or t1_rows.empty:
        return {
            **base_meta,
            "symbol": symbol, "name": name,
            "recommend_date": recommend_date,
            "buy_date": recommend_date,
            "sell_date": validate_date,
            "selected": False,
            "empty_reason": "数据不足以验证: 缺少T或T+1日K",
            "buy_price": 0, "sell_price": 0, "return": 0,
            "win": False, "sell_reason": "no_valid_kline",
        }

    t = t_rows.iloc[-1]
    t1 = t1_rows.iloc[-1]
    if not _is_valid_kline_row(t) or not _is_valid_kline_row(t1):
        return {
            **base_meta,
            "symbol": symbol, "name": name,
            "recommend_date": recommend_date,
            "buy_date": recommend_date,
            "sell_date": validate_date,
            "selected": False,
            "empty_reason": "数据不足以验证: K线异常",
            "buy_price": 0, "sell_price": 0, "return": 0,
            "win": False, "sell_reason": "invalid_kline",
        }

    try:
        config = data_loader.load_config()
    except Exception:
        config = _load_config()
    execution_model = config.get("execution_model", {})
    buy_source = "T_close"
    if recommendation.get("strategy_case") == "intraday_attack" and recommendation.get("action") == "BUY_NOW":
        buy_price = float(recommendation.get("entry_price") or recommendation.get("price") or 0)
        if buy_price <= 0:
            buy_price = float(t["close"])
            buy_source = "T_intraday_current_fallback_close"
        else:
            buy_source = recommendation.get("entry_price_source", "current_price")
    elif execution_model.get("buy_mode") == "tail_advice":
        proxy_price, proxy_source = _tail_advice_proxy_price(t)
        if proxy_price and proxy_price > 0:
            buy_price = proxy_price
            buy_source = proxy_source
        else:
            buy_price = float(t["close"])
            buy_source = proxy_source
    else:
        buy_price = float(t["close"])
    sell_price = float(t1["open"])
    sell_source = "T1_open"
    sell_reason = "next_open"
    validation_model = config.get("validation", {})
    if validation_model.get("sell_mode") == "open_window_avg":
        window_price, window_source = _get_open_window_average_sell_price(
            symbol,
            validate_date,
            validation_model.get("sell_window_start", "09:30"),
            validation_model.get("sell_window_end", "09:40"),
        )
        if window_price and window_price > 0:
            sell_price = window_price
            sell_source = window_source
            sell_reason = "next_open_window"
        else:
            sell_source = window_source
            sell_reason = "next_open_fallback"
    execution_config = dict(config.get("validation", {}))
    execution_config.update(config.get("execution_model", {}))
    execution_config.update(config.get("execution_costs", {}))
    outcome = paper_execution_model.evaluate_overnight_trade(
        t,
        t1,
        execution_config,
        entry_price=buy_price,
        entry_source=buy_source,
        exit_price=sell_price,
        exit_source=sell_source,
    )
    outcome["sell_reason"] = sell_reason
    return {
        **base_meta,
        "symbol": symbol,
        "name": name,
        "recommend_date": recommend_date,
        "buy_date": recommend_date,
        "sell_date": validate_date,
        "selected": True,
        **outcome,
    }


def _get_open_window_average_sell_price(symbol: str, date_str: str,
                                        window_start: str = "09:30",
                                        window_end: str = "09:40") -> tuple[float | None, str]:
    try:
        import akshare as ak
        start = date_str.replace("-", "") + f" {window_start}:00"
        end = date_str.replace("-", "") + f" {window_end}:00"
        df = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period="1",
            start_date=start,
            end_date=end,
        )
        if df is not None and not df.empty and "收盘" in df.columns:
            price = float(df["收盘"].astype(float).mean())
            if price > 0:
                return price, f"T1_open_window_avg_{window_start}_{window_end}"
        return None, "T1_open_fallback_no_window_minutes"
    except Exception:
        return None, "T1_open_fallback_no_minutes"


def _load_cached_validation_kline(symbol: str, recommend_date: str,
                                  validate_date: str) -> pd.DataFrame:
    """从历史训练 SQLite 缓存读取验证所需 T/T+1 日K。"""
    if not CACHE_DB.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(str(CACHE_DB))
        df = pd.read_sql_query(
            """
            SELECT date, open, high, low, close, volume, amount
            FROM kline_cache
            WHERE symbol = ? AND date IN (?, ?)
            ORDER BY date ASC
            """,
            conn,
            params=(symbol, recommend_date, validate_date),
        )
        conn.close()
    except Exception:
        return pd.DataFrame()
    dates = set(df["date"].astype(str).str[:10]) if not df.empty else set()
    if {recommend_date, validate_date}.issubset(dates):
        return df
    return pd.DataFrame()

def validate_one(symbol: str, name: str, recommend_date: str,
                  config: dict) -> dict:
    """旧版盘中验证单只推荐股票。

    返回交易记录 dict。
    """
    validate_date = dt.datetime.now().strftime("%Y-%m-%d")

    buy_price = get_buy_price(symbol, validate_date)
    if buy_price is None or buy_price <= 0:
        return {
            "symbol": symbol, "name": name,
            "recommend_date": recommend_date,
            "buy_date": validate_date,
            "buy_price": 0, "sell_price": 0, "return": 0,
            "win": False, "sell_reason": "no_buy_data",
        }

    sell_price, reason = get_sell_price(symbol, validate_date, buy_price, config)
    ret = (sell_price - buy_price) / buy_price if buy_price > 0 else 0

    return {
        "symbol": symbol, "name": name,
        "recommend_date": recommend_date,
        "selected": True,
        "buy_date": validate_date,
        "buy_price": round(buy_price, 3),
        "sell_price": round(sell_price, 3),
        "return": round(ret, 4),
        "win": ret > 0,
        "sell_reason": reason,
    }


# ---------------------------------------------------------------------------
# 性能统计
# ---------------------------------------------------------------------------

def recompute_performance(trades: list[dict]) -> dict:
    """重算 7d/30d/total 胜率、盈亏比、最大连亏。"""
    today = dt.datetime.now()

    def _calc(period_days: int | None) -> dict:
        if period_days is not None:
            cutoff = today - dt.timedelta(days=period_days)
            subset = [t for t in trades
                      if dt.datetime.fromisoformat(t["buy_date"]) >= cutoff]
        else:
            subset = trades

        if not subset:
            return {"win_rate": 0, "pl_ratio": 0,
                    "max_consecutive_loss": 0, "samples": 0}

        wins = [t for t in subset if t.get("return", 0) > 0]
        losses = [t for t in subset if t.get("return", 0) <= 0]

        win_rate = len(wins) / len(subset)

        avg_win = (sum(t["return"] for t in wins) / len(wins)) if wins else 0
        avg_loss = abs(sum(t["return"] for t in losses) / len(losses)) if losses else 0
        pl_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # 最大连亏
        sorted_t = sorted(subset, key=lambda x: x["buy_date"])
        max_consec = 0
        cur = 0
        for t in sorted_t:
            if t.get("return", 0) <= 0:
                cur += 1
                max_consec = max(max_consec, cur)
            else:
                cur = 0

        return {
            "win_rate": round(win_rate, 4),
            "pl_ratio": round(pl_ratio, 4),
            "max_consecutive_loss": max_consec,
            "samples": len(subset),
        }

    return {
        "7d": _calc(7),
        "30d": _calc(30),
        "total": _calc(None),
        "updated_at": today.isoformat(),
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def validate_yesterday() -> dict:
    """验证昨日推荐，写入 trades + performance。"""
    config = _load_config()
    yesterday = (dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    report_path = REPORTS_DIR / f"{yesterday}.md"

    # 从报告解析推荐（简单版：报告生成时也写 json 更稳）
    # 这里用 data/pending_recommendations.json 更可靠
    pending_path = DATA_DIR / "pending_recommendations.json"
    pending = _load_json(pending_path)
    recs = pending.get(yesterday, [])

    if not recs:
        return {"date": yesterday, "validated": 0, "message": "昨日无推荐记录"}

    trades = _load_trades()
    results = []
    for rec in recs:
        trade = validate_one(rec["symbol"], rec.get("name", ""), yesterday, config)
        trades.append(trade)
        results.append(trade)
        print(f"[validator] {trade['symbol']} {trade['name']} "
              f"买{trade['buy_price']} 卖{trade['sell_price']} "
              f"收益{trade['return']:.2%} {trade['sell_reason']}")

    # 保存
    _save_trades(trades)
    _save_live_samples(results)
    perf = recompute_performance(trades)
    _save_json(PERF_PATH, perf)

    # 清理 pending
    pending.pop(yesterday, None)
    _save_json(pending_path, pending)

    return {
        "date": yesterday,
        "validated": len(results),
        "results": results,
        "performance": perf,
    }


def _has_live_sample(date_str: str) -> bool:
    samples = _load_json(SAMPLE_POOL_PATH).get("samples", [])
    return any(
        s.get("sample_type") == "live_paper" and s.get("date") == date_str
        for s in samples
    )


def _get_live_sample(date_str: str) -> dict:
    samples = _load_json(SAMPLE_POOL_PATH).get("samples", [])
    for s in samples:
        if s.get("sample_type") == "live_paper" and s.get("date") == date_str:
            return s
    return {}


def _is_retryable_unverifiable_sample(sample: dict) -> bool:
    if not sample:
        return False
    if sample.get("selected", True):
        return False
    if not sample.get("symbol"):
        return False
    return sample.get("sell_reason") in {"no_valid_kline", "invalid_kline"}


def _latest_live_sample_date_before(today: str) -> str:
    samples = _load_json(SAMPLE_POOL_PATH).get("samples", [])
    dates = sorted(
        str(s.get("date", ""))
        for s in samples
        if s.get("sample_type") == "live_paper" and str(s.get("date", "")) < today
    )
    return dates[-1] if dates else ""


def _previous_pending_date(pending: dict, today: str) -> str:
    dates = sorted(d for d in pending.keys() if str(d) < today)
    return dates[-1] if dates else ""


def _normalize_pending_entry(entry, target_date: str) -> tuple[list[dict], dict]:
    """兼容旧 list 格式与新元数据格式的 pending。"""
    if isinstance(entry, dict) and not entry.get("selected", True):
        return [], {
            "selected_at": entry.get("selected_at", ""),
            "selection_date": entry.get("selection_date", target_date),
            "empty_reason": entry.get("empty_reason", "当日空仓"),
        }
    if isinstance(entry, dict):
        recs = entry.get("recommendations", [])
        meta = {
            "selected_at": entry.get("selected_at", ""),
            "selection_date": entry.get("selection_date", target_date),
            "empty_reason": entry.get("empty_reason", ""),
        }
        return recs, meta
    return list(entry or []), {"selected_at": "", "selection_date": target_date, "empty_reason": "当日空仓"}


def sync_previous_live_paper(today: str = None) -> dict:
    """轻量同步最近一个可验证交易日的实际执行/空仓样本。

    只读取 pending_recommendations 中 today 之前最近一日；如果已存在同日
    live_paper 样本则跳过，保证 run_today_report 可安全重复执行。
    """
    if today is None:
        today = dt.datetime.now().strftime("%Y-%m-%d")
    pending_path = DATA_DIR / "pending_recommendations.json"
    pending = _load_json(pending_path)
    target_date = _previous_pending_date(pending, today)
    if not target_date:
        retry_date = _latest_live_sample_date_before(today)
        retry_sample = _get_live_sample(retry_date) if retry_date else {}
        if _is_retryable_unverifiable_sample(retry_sample):
            result = validate_close_to_next_open(
                retry_sample["symbol"],
                retry_sample.get("name", ""),
                retry_date,
                today,
                retry_sample,
            )
            _save_live_samples([result])
            if result.get("selected", True):
                trades = _load_trades()
                existing_keys = {
                    (t.get("recommend_date"), t.get("symbol"))
                    for t in trades
                }
                key = (result.get("recommend_date"), result.get("symbol"))
                if key not in existing_keys:
                    trades.append(result)
                    _save_trades(trades)
                perf = recompute_performance(trades)
                _save_json(PERF_PATH, perf)
                return {"date": retry_date, "status": "validated", "validated": 1, "results": [result]}
            return {"date": retry_date, "status": "unverifiable", "validated": 0, "results": [result]}
        synced_date = _latest_live_sample_date_before(today)
        if synced_date:
            return {"date": synced_date, "status": "already_synced", "validated": 0, "results": []}
        return {"date": "", "status": "no_pending", "validated": 0, "results": []}
    live_sample = _get_live_sample(target_date)
    if live_sample and not _is_retryable_unverifiable_sample(live_sample):
        return {"date": target_date, "status": "already_synced", "validated": 0, "results": []}
    if live_sample and _is_retryable_unverifiable_sample(live_sample):
        result = validate_close_to_next_open(
            live_sample["symbol"],
            live_sample.get("name", ""),
            target_date,
            today,
            live_sample,
        )
        _save_live_samples([result])
        if result.get("selected", True):
            trades = _load_trades()
            existing_keys = {
                (t.get("recommend_date"), t.get("symbol"))
                for t in trades
            }
            key = (result.get("recommend_date"), result.get("symbol"))
            if key not in existing_keys:
                trades.append(result)
                _save_trades(trades)
            perf = recompute_performance(trades)
            _save_json(PERF_PATH, perf)
            return {"date": target_date, "status": "validated", "validated": 1, "results": [result]}
        return {"date": target_date, "status": "unverifiable", "validated": 0, "results": [result]}

    recs, pending_meta = _normalize_pending_entry(pending.get(target_date, []), target_date)
    if not recs:
        sample = {
            "recommend_date": target_date,
            "buy_date": target_date,
            "sell_date": today,
            "selected": False,
            "selected_at": pending_meta.get("selected_at", ""),
            "selection_date": pending_meta.get("selection_date", target_date),
            "empty_reason": pending_meta.get("empty_reason") or "当日空仓",
            "sell_reason": "empty_position",
            "return": 0,
        }
        _save_live_samples([sample])
        pending.pop(target_date, None)
        _save_json(pending_path, pending)
        return {"date": target_date, "status": "empty", "validated": 0, "results": [sample]}

    trades = _load_trades()
    results = [
        validate_close_to_next_open(
            rec["symbol"],
            rec.get("name", ""),
            target_date,
            today,
            rec,
        )
        for rec in recs[:1]
    ]
    selected_results = [r for r in results if r.get("selected", True)]
    if selected_results:
        existing_keys = {
            (t.get("recommend_date"), t.get("symbol"))
            for t in trades
        }
        for trade in selected_results:
            key = (trade.get("recommend_date"), trade.get("symbol"))
            if key not in existing_keys:
                trades.append(trade)
        _save_trades(trades)
        perf = recompute_performance(trades)
        _save_json(PERF_PATH, perf)

    _save_live_samples(results)
    pending.pop(target_date, None)
    _save_json(pending_path, pending)

    if selected_results:
        status = "validated"
    else:
        status = "unverifiable"
    return {
        "date": target_date,
        "status": status,
        "validated": len(selected_results),
        "results": results,
    }


def save_pending_recommendations(recommendations: list[dict]):
    """选股后保存待验证推荐。"""
    pending_path = DATA_DIR / "pending_recommendations.json"
    now = _now()
    today = now.strftime("%Y-%m-%d")
    selected_at = now.strftime("%Y-%m-%d %H:%M:%S")
    pending = _load_json(pending_path)
    pending[today] = [
        {
            "symbol": r["symbol"],
            "name": _resolve_stock_name(r["symbol"], r.get("name", "")),
            "score": r.get("score", 0),
            "sector": r.get("sector", ""),
            "selected_at": selected_at,
            "selection_date": today,
            "strategy_case": r.get("strategy_case", "tail_confirm"),
            "action": r.get("action", "TAIL_CONFIRM"),
            "entry_price_source": r.get("entry_price_source", "tail_advice_price"),
            "next_check_at": r.get("next_check_at", ""),
            "opportunity_score": r.get("opportunity_score", 0),
            "entry_price": (
                r.get("entry_price")
                or (r.get("realtime", {}) or {}).get("price")
                or (r.get("intraday_profile", {}) or {}).get("price")
                or 0
            ),
            "factor_scores": {
                k: r[k]
                for k in [
                    "F1_tail_fund_inflow",
                    "F2_volume_price_sync",
                    "F3_technical_pattern",
                    "F4_tail_rally_strength",
                    "F5_sector_heat",
                    "F6_news_catalyst",
                    "F7_float_mv_fit",
                    "F8_overnight_risk_control",
                    "F9_overheat_control",
                    "F10_trend_momentum",
                    "F11_financial_quality",
                    "F12_market_sentiment",
                ]
                if k in r
            },
        }
        for r in recommendations
    ]
    _save_json(pending_path, pending)


def save_empty_pending(date_str: str = None, reason: str = "当日空仓"):
    """空仓日也覆盖 pending，避免旧推荐残留污染后续验证。"""
    pending_path = DATA_DIR / "pending_recommendations.json"
    if date_str is None:
        date_str = _now().strftime("%Y-%m-%d")
    selected_at = _now().strftime("%Y-%m-%d %H:%M:%S")
    pending = _load_json(pending_path)
    pending[date_str] = {
        "selected": False,
        "selection_date": date_str,
        "selected_at": selected_at,
        "empty_reason": reason,
    }
    _save_json(pending_path, pending)


def show_status() -> str:
    """打印当前策略状态。"""
    trades = _load_trades()
    perf = _load_json(PERF_PATH)
    version = _load_json(DATA_DIR / "strategy_version.json")
    config = _load_config()

    lines = ["=== A股尾盘隔夜策略状态 ===", ""]
    lines.append(f"策略版本: {version.get('version', config.get('version', 'v1.0'))}")
    lines.append(f"下次优化: {version.get('next_optimize_date', '未排期')}")
    lines.append(f"历史交易: {len(trades)} 笔")
    lines.append("")

    for period in ["7d", "30d", "total"]:
        p = perf.get(period, {})
        label = {"7d": "近7日", "30d": "近30日", "total": "总计"}[period]
        lines.append(f"{label}: 胜率 {p.get('win_rate', 0):.1%} | "
                      f"盈亏比 1:{p.get('pl_ratio', 0):.2f} | "
                      f"最大连亏 {p.get('max_consecutive_loss', 0)} | "
                      f"样本 {p.get('samples', 0)}")

    lines.append("")
    if trades:
        lines.append("最近5笔交易:")
        for t in sorted(trades, key=lambda x: x.get("buy_date", ""), reverse=True)[:5]:
            win = "✅" if t.get("return", 0) > 0 else "❌"
            lines.append(f"  {t.get('buy_date','')} {t.get('symbol','')} "
                          f"{t.get('name','')} {t.get('return',0):.2%} {win}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(show_status())
    else:
        result = validate_yesterday()
        print(f"验证完成: {result.get('validated', 0)} 笔")
        print(show_status())
