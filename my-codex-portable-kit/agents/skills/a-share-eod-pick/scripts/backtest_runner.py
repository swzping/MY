"""
A股尾盘隔夜策略 - 历史回测训练脚本

功能：
1. 基于当前技能策略对历史交易日进行筛选和选取
2. SQLite 缓存日K数据，含版本控制与过期清理
3. 增量累积样本到 data/strategy_samples.json
4. 计算总胜率/分时段胜率/风险回报比等KPI
5. 生成可视化图表

因子近似说明（回测专用）：
    F1 尾盘资金净流入 → 日级代理：日内涨幅 × 量比（强收+放量≈尾盘流入）
    F2 量价协同       → 日级代理：量比 × 量价同向一致性
    F3 技术形态       → 完整计算（MACD/RSI/MA，日K可精确还原）
    F4 尾盘拉升强度   → 日级代理：收盘位置 (close-low)/(high-low) × 量比
    F5 板块热度       → 中性 50（无历史板块分钟数据）
    F6 消息面催化     → 中性 50（无历史公告/研报数据）
    F7 流通市值适配   → 近20日均成交额高斯适配
    F10 趋势动能       → 动量与均线结构（趋势加速）
    F11 财务质量       → 退化到近端波动/量能代理（缺财务时）
    F12 情绪           → 趋势-波动-情绪偏离（日内价量结构）

用法：
    python scripts/backtest_runner.py                    # 全量训练（可验证历史）
    python scripts/backtest_runner.py --days 60          # 指定回测天数
    python scripts/backtest_runner.py --universe 200     # 指定股票池大小
"""

import json
import sys
import math
import sqlite3
import datetime as dt
import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
try:
    from scipy.stats import spearmanr
except Exception:
    spearmanr = None

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_loader
import strategy_engine
import optimizer
import execution_model as paper_execution_model

CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
DATA_DIR = SKILL_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DB = CACHE_DIR / "backtest_kline.db"
TRADES_PATH = DATA_DIR / "trades.json"
PERF_PATH = DATA_DIR / "performance.json"
VERSION_PATH = DATA_DIR / "strategy_version.json"
SAMPLE_POOL_PATH = DATA_DIR / "strategy_samples.json"
BACKTEST_META_PATH = DATA_DIR / "backtest_meta.json"
REPORTS_DIR = SKILL_ROOT / "reports"
DEFAULT_TRAINING_DAYS = None
DEFAULT_HISTORY_FETCH_DAYS = 360

FACTOR_KEYS = [
    "F1_tail_fund_inflow", "F2_volume_price_sync",
    "F3_technical_pattern", "F4_tail_rally_strength",
    "F5_sector_heat", "F6_news_catalyst", "F7_float_mv_fit",
    "F8_overnight_risk_control", "F9_overheat_control",
    "F10_trend_momentum", "F11_financial_quality", "F12_market_sentiment",
]


def _ordered_factor_keys(config: dict) -> list[str]:
    return [
        key
        for key, value in (config.get("factors") or {}).items()
        if isinstance(value, dict)
    ]


def history_fetch_days(trading_days: int | None) -> int:
    """K-line rows needed for factor warmup plus requested validation days."""
    if trading_days is None:
        return DEFAULT_HISTORY_FETCH_DAYS
    return max(130, int(trading_days) + 50)


def history_calendar_limit(trading_days: int | None) -> int:
    """Trading calendar rows needed to cover T days plus T+1 validation."""
    if trading_days is None:
        return DEFAULT_HISTORY_FETCH_DAYS
    return max(80, int(trading_days) + 5)


def select_backtest_dates(all_dates_desc: list[str], trading_days: int | None = DEFAULT_TRAINING_DAYS) -> list[str]:
    """Return trainable T dates in ascending order.

    all_dates_desc must be newest first. The newest date is kept as T+1
    validation data, so the previous trading day can be trained once today's
    open exists.
    """
    trainable = list(all_dates_desc[1:])
    if trading_days is not None:
        trainable = trainable[:max(0, int(trading_days))]
    return sorted(trainable)


# ---------------------------------------------------------------------------
# SQLite 缓存层（版本控制 + 过期清理）
# ---------------------------------------------------------------------------

def init_cache_db():
    """初始化 SQLite 缓存数据库。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kline_cache (
            symbol      TEXT NOT NULL,
            date        TEXT NOT NULL,
            open        REAL,
            high        REAL,
            low         REAL,
            close       REAL,
            volume      REAL,
            amount      REAL,
            cached_at   TEXT NOT NULL,
            cache_version TEXT NOT NULL,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache_meta (
            symbol        TEXT PRIMARY KEY,
            first_date    TEXT,
            last_date     TEXT,
            total_bars    INTEGER,
            cached_at     TEXT,
            cache_version TEXT
        )
    """)
    conn.commit()
    return conn


CACHE_VERSION = "v1.0"


def _is_valid_kline_row(row) -> bool:
    """基础日K质量校验，过滤未完成/异常行情行。"""
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


def cache_kline(conn, symbol: str, df: pd.DataFrame):
    """缓存单只股票的日K数据（增量 upsert）。"""
    if df.empty:
        return
    now = dt.datetime.now().isoformat()
    rows = []
    for _, row in df.iterrows():
        d = str(row.get("date", ""))
        if not d:
            continue
        # 统一日期格式为 YYYY-MM-DD
        d = d[:10]
        if not _is_valid_kline_row(row):
            continue
        rows.append((
            symbol, d,
            float(row.get("open", 0)), float(row.get("high", 0)),
            float(row.get("low", 0)), float(row.get("close", 0)),
            float(row.get("volume", 0)), float(row.get("amount", 0)),
            now, CACHE_VERSION
        ))
    if not rows:
        return
    conn.executemany("""
        INSERT OR REPLACE INTO kline_cache
        (symbol, date, open, high, low, close, volume, amount, cached_at, cache_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.execute("""
        INSERT OR REPLACE INTO cache_meta
        (symbol, first_date, last_date, total_bars, cached_at, cache_version)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        symbol, rows[0][1], rows[-1][1], len(rows), now, CACHE_VERSION
    ))
    conn.commit()


def load_cached_kline(conn, symbol: str, end_date: str,
                      days: int = 120) -> pd.DataFrame:
    """从缓存加载日K（截止 end_date 前 days 个交易日）。"""
    df = pd.read_sql_query("""
        SELECT date, open, high, low, close, volume, amount
        FROM kline_cache
        WHERE symbol = ? AND date <= ?
        ORDER BY date DESC
        LIMIT ?
    """, conn, params=(symbol, end_date, days))
    if df.empty:
        return df
    return df.iloc[::-1].reset_index(drop=True)


def clean_expired_cache(conn, max_age_days: int = 7):
    """清理超过 max_age_days 的旧版本缓存。"""
    cutoff = (dt.datetime.now() - dt.timedelta(days=max_age_days)).isoformat()
    conn.execute("DELETE FROM kline_cache WHERE cached_at < ? AND cache_version < ?",
                 (cutoff, CACHE_VERSION))
    conn.commit()


# ---------------------------------------------------------------------------
# 股票池选取
# ---------------------------------------------------------------------------

def build_universe(size: int = 150) -> list[str]:
    """构建回测股票池：主板、非ST、按流动性取 TOP N。"""
    print(f"[backtest] 构建股票池 (target={size})...")
    snap = data_loader.get_market_snapshot()
    if snap.empty:
        cached = load_cached_universe(size)
        if cached:
            print(f"[backtest] 实时快照不可用，使用缓存股票池: {len(cached)} 只")
            return cached
        raise RuntimeError("无法获取市场快照，且本地缓存股票池为空")

    # 主板前缀过滤
    snap = snap[snap["symbol"].str.match(r"^(60|00|001|002|003)")].copy()
    # 剔除 ST
    snap = snap[~snap["name"].str.contains(r"ST|\*ST|退", na=False, regex=True)]
    # 剔除停牌（价格为0）
    snap = snap[snap["price"] > 0]
    # 按成交额降序
    snap = snap.sort_values("amount", ascending=False)
    symbols = snap["symbol"].head(size).tolist()
    print(f"[backtest] 股票池: {len(symbols)} 只 (source={snap.attrs.get('source','unknown')})")
    return symbols


def load_cached_universe(size: int = 150) -> list[str]:
    """从历史 K 线缓存中恢复股票池，供数据源临时不可用时继续训练。"""
    if not CACHE_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(CACHE_DB))
        rows = conn.execute("""
            SELECT symbol
            FROM cache_meta
            ORDER BY total_bars DESC, symbol ASC
            LIMIT ?
        """, (size,)).fetchall()
        conn.close()
    except Exception:
        return []
    return [str(r[0]).zfill(6) for r in rows]


# ---------------------------------------------------------------------------
# 日级因子计算（回测近似版）
# ---------------------------------------------------------------------------

def calc_F8_overnight_risk_control(kline: pd.DataFrame) -> float:
    """隔夜追高风险控制分：越高越安全，越低越像追高/长上影风险。"""
    if kline is None or len(kline) < 5:
        return 50.0

    df = kline.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    last = df.iloc[-1]
    prev = df.iloc[:-1]
    high = float(last["high"])
    low = float(last["low"])
    open_p = float(last["open"])
    close_p = float(last["close"])
    day_range = max(high - low, 0.01)
    upper_shadow_ratio = max(high - max(open_p, close_p), 0) / day_range
    close_position = (close_p - low) / day_range
    prev_close = float(prev.iloc[-1]["close"])
    day_return = (close_p - prev_close) / prev_close if prev_close > 0 else 0
    rise_3d = close_p / float(prev["close"].tail(3).iloc[0]) - 1 if len(prev) >= 3 else 0
    vol_ma5 = df["volume"].tail(5).mean()
    vol_ratio = float(last["volume"]) / vol_ma5 if vol_ma5 > 0 else 1.0

    risk = 0.0
    risk += min(35, upper_shadow_ratio * 70)
    risk += min(25, max(day_return - 0.03, 0) / 0.06 * 25)
    risk += min(20, max(rise_3d - 0.08, 0) / 0.12 * 20)
    risk += min(20, max(vol_ratio - 1.4, 0) / 1.6 * 20)
    if close_position < 0.55 and day_return > 0:
        risk += 10

    return float(np.clip(100 - risk, 0, 100))


def calc_F9_overheat_control(kline: pd.DataFrame) -> float:
    """过热控制分：越高越温和，越低越像短线涨幅/均线偏离过热。"""
    if kline is None or len(kline) < 10:
        return 50.0

    df = kline.copy()
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)

    last = df.iloc[-1]
    closes = df["close"]
    close_p = float(last["close"])
    prev_close = float(closes.iloc[-2])
    day_return = (close_p - prev_close) / prev_close if prev_close > 0 else 0
    ret3 = close_p / float(closes.iloc[-4]) - 1 if len(closes) >= 4 and closes.iloc[-4] > 0 else 0
    ma5 = closes.tail(5).mean()
    ma10 = closes.tail(10).mean()
    ma5_bias = close_p / ma5 - 1 if ma5 > 0 else 0
    ma10_bias = close_p / ma10 - 1 if ma10 > 0 else 0

    risk = 0.0
    risk += min(30, max(day_return - 0.035, 0) / 0.05 * 30)
    risk += min(25, max(ma5_bias - 0.035, 0) / 0.05 * 25)
    risk += min(25, max(ma10_bias - 0.045, 0) / 0.06 * 25)
    risk += min(20, max(ret3 - 0.06, 0) / 0.08 * 20)
    return float(np.clip(100 - risk, 0, 100))


def calc_factors_daily(kline: pd.DataFrame, config: dict) -> Optional[dict]:
    """基于日K线计算全部因子分（回测近似版）。

    kline: 截止 T 日的日K（至少30条），最后一条为 T 日
    返回: {F1..F7, score} 或 None（数据不足）
    """
    if kline is None or len(kline) < 30:
        return None

    factor_keys = _ordered_factor_keys(config)

    kline = kline.copy()
    kline["close"] = kline["close"].astype(float)
    kline["volume"] = kline["volume"].astype(float)
    kline["amount"] = kline["amount"].astype(float)

    last = kline.iloc[-1]
    close = kline["close"]

    # --- 预过滤检查 ---
    pf = config["prefilter"]
    price = float(last["close"])
    if not (pf["price_min"] <= price <= pf["price_max"]):
        return None
    amount = float(last["amount"])
    if amount < pf["amount_min"]:
        return None
    pct = (float(last["close"]) - float(last["open"])) / float(last["open"]) if float(last["open"]) > 0 else 0
    # 用前复权收盘算涨跌幅更准，但这里用开收差近似
    pre_close = float(kline.iloc[-2]["close"]) if len(kline) >= 2 else float(last["open"])
    pct_change = (float(last["close"]) - pre_close) / pre_close if pre_close > 0 else 0
    if pf["exclude_limit_up_down"]:
        if pct_change >= 0.097 or pct_change <= -0.097:
            return None
    if len(kline) < pf["listed_days_min"]:
        return None

    weights = {fk: config["factors"][fk]["weight"] for fk in FACTOR_KEYS if fk in config.get("factors", {})}

    raw_scores: dict[str, float] = {}
    if "F1_tail_fund_inflow" in factor_keys:
        # 代理逻辑：日内涨幅 × 量比。强收+放量≈尾盘主力流入
        vol_ma5 = kline["volume"].tail(5).mean()
        vol_ratio = float(last["volume"]) / vol_ma5 if vol_ma5 > 0 else 1.0
        daily_ret = (float(last["close"]) - float(last["open"])) / float(last["open"]) if float(last["open"]) > 0 else 0
        main_proxy = daily_ret * vol_ratio  # 涨+放量为正，跌+放量为负
        raw_scores["F1_tail_fund_inflow"] = float(np.clip(50 + main_proxy * 500, 0, 100))

    if "F2_volume_price_sync" in factor_keys:
        # 代理逻辑：量比得分 + 量价同向
        vol_ma5 = kline["volume"].tail(5).mean()
        vol_ratio = float(last["volume"]) / vol_ma5 if vol_ma5 > 0 else 1.0
        daily_ret = (float(last["close"]) - float(last["open"])) / float(last["open"]) if float(last["open"]) > 0 else 0
        vol_score = np.clip((vol_ratio - 0.5) / 1.5 * 100, 0, 100)
        if daily_ret > 0 and vol_ratio > 1.0:
            consistency = 80
        elif daily_ret > 0:
            consistency = 60
        elif daily_ret < 0 and vol_ratio > 1.0:
            consistency = 30
        else:
            consistency = 50
        raw_scores["F2_volume_price_sync"] = float(np.clip(vol_score * 0.6 + consistency * 0.4, 0, 100))

    if "F3_technical_pattern" in factor_keys:
        raw_scores["F3_technical_pattern"] = float(strategy_engine.calc_F3_technical_pattern({"daily_k": kline}, config))

    if "F4_tail_rally_strength" in factor_keys:
        high_d = float(last["high"])
        low_d = float(last["low"])
        close_pos = (float(last["close"]) - low_d) / (high_d - low_d) if (high_d - low_d) > 0 else 0.5
        vol_ma5 = kline["volume"].tail(5).mean()
        vol_ratio = float(last["volume"]) / vol_ma5 if vol_ma5 > 0 else 1.0
        rally_score = close_pos * 100
        share_score = np.clip((vol_ratio - 0.5) / 1.5 * 100, 0, 100)
        raw_scores["F4_tail_rally_strength"] = float(np.clip(rally_score * 0.7 + share_score * 0.3, 0, 100))

    if "F5_sector_heat" in factor_keys:
        raw_scores["F5_sector_heat"] = 50.0

    if "F6_news_catalyst" in factor_keys:
        raw_scores["F6_news_catalyst"] = float(config["factors"]["F6_news_catalyst"].get("default_no_news", 50))

    if "F7_float_mv_fit" in factor_keys:
        avg_amount = kline["amount"].tail(20).mean()
        if avg_amount > 0:
            mu = math.log(2e8)  # 中位 2 亿成交额
            sigma = 0.8
            x = math.log(max(float(avg_amount), 1))
            f7 = math.exp(-0.5 * ((x - mu) / sigma) ** 2) * 100
            raw_scores["F7_float_mv_fit"] = float(np.clip(f7, 0, 100))
        else:
            raw_scores["F7_float_mv_fit"] = 50.0

    if "F8_overnight_risk_control" in factor_keys:
        raw_scores["F8_overnight_risk_control"] = calc_F8_overnight_risk_control(kline)

    if "F9_overheat_control" in factor_keys:
        raw_scores["F9_overheat_control"] = calc_F9_overheat_control(kline)

    if "F10_trend_momentum" in factor_keys:
        raw_scores["F10_trend_momentum"] = float(strategy_engine.calc_F10_trend_momentum({"daily_k": kline}, config))

    if "F11_financial_quality" in factor_keys:
        raw_scores["F11_financial_quality"] = float(strategy_engine.calc_F11_financial_quality({"daily_k": kline}, config))

    if "F12_market_sentiment" in factor_keys:
        raw_scores["F12_market_sentiment"] = float(strategy_engine.calc_F12_market_sentiment({"daily_k": kline}, config))

    scores = {fk: round(float(raw_scores[fk]), 2) for fk in factor_keys if fk in raw_scores}
    total = sum(weights[fk] * scores[fk] for fk in factor_keys if fk in weights and fk in scores)
    scores["score"] = round(total, 2)
    return scores


# ---------------------------------------------------------------------------
# T+1 验证
# ---------------------------------------------------------------------------

def validate_t1(kline: pd.DataFrame, config: dict) -> Optional[dict]:
    """从日K中提取 T+1 验证结果。

    kline: 包含 T 日和 T+1 日的日K
    返回: {buy_price, sell_price, return, win, sell_reason} 或 None
    """
    if kline is None or len(kline) < 2:
        return None

    t1 = kline.iloc[-1]  # T+1 日
    buy_price = float(t1["open"])
    if buy_price <= 0:
        return None

    rc = config.get("validation", {})
    stop_loss = rc.get("stop_loss", -0.03)
    take_profit = rc.get("take_profit", 0.05)

    t1_high = float(t1["high"])
    t1_low = float(t1["low"])
    t1_close = float(t1["close"])

    # 止损/止盈检查（保守：先检查止损）
    sell_price = t1_close
    sell_reason = "close"

    low_ret = (t1_low - buy_price) / buy_price
    high_ret = (t1_high - buy_price) / buy_price

    if low_ret <= stop_loss:
        sell_price = buy_price * (1 + stop_loss)
        sell_reason = "stop_loss"
    elif high_ret >= take_profit:
        sell_price = buy_price * (1 + take_profit)
        sell_reason = "take_profit"

    ret = (sell_price - buy_price) / buy_price
    return {
        "buy_price": round(buy_price, 3),
        "sell_price": round(sell_price, 3),
        "return": round(ret, 4),
        "win": ret > 0,
        "sell_reason": sell_reason,
    }


def _close_position(row: pd.Series) -> float:
    high = float(row["high"])
    low = float(row["low"])
    close = float(row["close"])
    if high <= low:
        return 0.5
    return (close - low) / (high - low)


def _minute_execution_price(tail_minutes: pd.DataFrame | None, buy_time: str) -> tuple[float | None, str]:
    if tail_minutes is None or tail_minutes.empty:
        return None, "T_close_fallback_no_minutes"
    if "time" not in tail_minutes.columns or "close" not in tail_minutes.columns:
        return None, "T_close_fallback_bad_minutes"

    df = tail_minutes.copy()
    df["_time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["_time"]).sort_values("_time")
    if df.empty:
        return None, "T_close_fallback_bad_minutes"

    target = pd.to_datetime(f"{df.iloc[0]['_time'].date()} {buy_time}", errors="coerce")
    if pd.isna(target):
        return None, "T_close_fallback_bad_buy_time"

    eligible = df[df["_time"] <= target]
    row = eligible.iloc[-1] if not eligible.empty else df.iloc[0]
    price = float(row["close"])
    if price <= 0:
        return None, "T_close_fallback_bad_minutes"
    return price, f"T_minute_{buy_time}"


def _tail_advice_proxy_price(t_row: pd.Series) -> tuple[float | None, str]:
    """Approximate a 14:40-14:55 execution price when historical minutes are absent."""
    try:
        open_p = float(t_row["open"])
        high = float(t_row["high"])
        low = float(t_row["low"])
        close = float(t_row["close"])
    except Exception:
        return None, "T_tail_advice_proxy_bad_kline"
    if min(open_p, high, low, close) <= 0 or high < low:
        return None, "T_tail_advice_proxy_bad_kline"

    # Without historical minutes, estimate the late-session executable price from
    # OHLC: bias toward close but temper a high-close chase with the day midpoint.
    midpoint = (high + low) / 2
    proxy = (close * 2 + midpoint) / 3
    return proxy, "T_tail_advice_proxy_no_minutes"


def _open_window_sell_price(open_minutes: pd.DataFrame | None,
                            window_start: str = "09:30",
                            window_end: str = "09:40") -> tuple[float | None, str]:
    if open_minutes is None or open_minutes.empty:
        return None, "T1_open_fallback_no_minutes"
    if "time" not in open_minutes.columns or "close" not in open_minutes.columns:
        return None, "T1_open_fallback_bad_minutes"

    df = open_minutes.copy()
    df["_time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["_time"]).sort_values("_time")
    if df.empty:
        return None, "T1_open_fallback_bad_minutes"

    trade_date = df.iloc[0]["_time"].date()
    start = pd.to_datetime(f"{trade_date} {window_start}", errors="coerce")
    end = pd.to_datetime(f"{trade_date} {window_end}", errors="coerce")
    if pd.isna(start) or pd.isna(end):
        return None, "T1_open_fallback_bad_window"

    window = df[(df["_time"] >= start) & (df["_time"] <= end)]
    if window.empty:
        return None, "T1_open_fallback_no_window_minutes"
    price = float(window["close"].astype(float).mean())
    if price <= 0:
        return None, "T1_open_fallback_bad_minutes"
    return price, f"T1_open_window_avg_{window_start}_{window_end}"


def validate_close_to_next_open(kline: pd.DataFrame, t_date: str = None,
                                t1_date: str = None,
                                execution_model: dict | None = None,
                                tail_minutes: pd.DataFrame | None = None,
                                t1_open_minutes: pd.DataFrame | None = None) -> Optional[dict]:
    """T 日按执行模型买入，T+1 日开盘卖出。"""
    if kline is None or len(kline) < 2:
        return None
    t = kline.iloc[-2]
    t1 = kline.iloc[-1]
    if t_date and str(t.get("date", ""))[:10] != t_date:
        return None
    if t1_date and str(t1.get("date", ""))[:10] != t1_date:
        return None
    if not _is_valid_kline_row(t) or not _is_valid_kline_row(t1):
        return None

    execution_model = execution_model or {}
    buy_mode = execution_model.get("buy_mode", "close")
    if buy_mode == "anti_chase":
        max_close_position = float(execution_model.get("max_close_position", 1.0))
        if _close_position(t) > max_close_position:
            return None

    buy_source = "T_close"
    if buy_mode in ("minute_at", "tail_advice"):
        buy_price, buy_source = _minute_execution_price(
            tail_minutes,
            execution_model.get("buy_time", "14:45"),
        )
        if buy_price is None:
            if buy_mode == "tail_advice":
                proxy_price, proxy_source = _tail_advice_proxy_price(t)
                if proxy_price is not None:
                    buy_price = proxy_price
                    buy_source = proxy_source
                else:
                    buy_price = float(t["close"])
                    buy_source = proxy_source
            else:
                buy_price = float(t["close"])
    else:
        buy_price = float(t["close"])
    sell_mode = execution_model.get("sell_mode", "next_open")
    sell_reason = "next_open"
    sell_source = "T1_open"
    if sell_mode == "open_window_avg":
        sell_price, sell_source = _open_window_sell_price(
            t1_open_minutes,
            execution_model.get("sell_window_start", "09:30"),
            execution_model.get("sell_window_end", "09:40"),
        )
        if sell_price is None:
            sell_price = float(t1["open"])
            sell_reason = "next_open_fallback"
        else:
            sell_reason = "next_open_window"
    else:
        sell_price = float(t1["open"])
    outcome = paper_execution_model.evaluate_overnight_trade(
        t,
        t1,
        execution_model,
        entry_price=buy_price,
        entry_source=buy_source if buy_mode != "anti_chase" else "T_anti_chase",
        exit_price=sell_price,
        exit_source=sell_source,
    )
    outcome["sell_reason"] = sell_reason
    return outcome


def _execution_validation_model(config: dict) -> dict:
    model = dict(config.get("validation", {}))
    model.update(config.get("execution_model", {}))
    model.update(config.get("execution_costs", {}))
    return model


def _passes_selection_rules(stock: dict, config: dict) -> tuple[bool, str]:
    """检查综合分和因子风控门槛。"""
    selection = config.get("selection", {})
    threshold = selection.get("score_threshold", 60)
    score = float(stock.get("score", 0) or 0)
    if score < threshold:
        return False, "无超阈值"

    fs = stock.get("factor_scores", {})
    for key, min_value in selection.get("min_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) < float(min_value):
            return False, f"{key}低于{min_value}"
    for key, max_value in selection.get("max_factor_scores", {}).items():
        if float(fs.get(key, 0) or 0) > float(max_value):
            return False, f"{key}高于{max_value}"
    return True, "ok"


def _candidate_with_validation(stock: dict, validation: dict | None = None) -> dict:
    item = {
        "symbol": stock.get("symbol", ""),
        "name": stock.get("name", ""),
        "score": stock.get("score", 0),
        "factor_scores": stock.get("factor_scores", {}),
    }
    if validation:
        for key in (
            "buy_price", "sell_price", "return", "win", "sell_reason",
            "buy_price_source", "sell_price_source", "execution_status", "skip_reason",
            "gross_return", "net_return", "raw_entry_price", "raw_exit_price",
        ):
            if key in validation:
                item[key] = validation[key]
    return item


def _actual_best(candidate_pool: list[dict]) -> dict:
    valid = [c for c in candidate_pool if isinstance(c.get("return"), (int, float))]
    if not valid:
        return {}
    return max(valid, key=lambda c: c.get("return", -999))


def _missed_best_reason(pick: dict | None, actual_best: dict,
                        config: dict) -> str:
    if not actual_best:
        return "候选池缺少次日验证数据"
    if not pick:
        ok, reason = _passes_selection_rules(actual_best, config)
        if ok:
            return "次日实际最优合格但当日未形成有效选择"
        return f"次日实际最优未过当日规则：{reason}"
    if pick.get("symbol") == actual_best.get("symbol"):
        return "已选中次日实际最优"

    ok, reason = _passes_selection_rules(actual_best, config)
    if not ok:
        return f"次日实际最优未过当日规则：{reason}"

    pick_score = float(pick.get("score", 0) or 0)
    best_score = float(actual_best.get("score", 0) or 0)
    if best_score < pick_score:
        return f"当时综合分 {best_score:.2f} 低于已选 {pick_score:.2f}"
    return "同日排序规则优先选择了已选标的"


def build_daily_sample(t_date: str, t1_date: str, scored_stocks: list[dict],
                       config: dict, next_kline: pd.DataFrame = None,
                       empty_reason: str = "无候选",
                       candidate_validations: dict[str, dict] | None = None,
                       neighbor_rescue_history: dict[tuple[str, ...], list[dict]] | None = None) -> dict:
    """构造单个历史交易日样本：Top1 或空仓。"""
    base = {
        "date": t_date,
        "sample_type": "historical_training",
        "t1_date": t1_date,
        "config_version": config.get("version", ""),
    }
    if not scored_stocks:
        return {**base, "selected": False, "empty_reason": empty_reason}

    candidate_validations = candidate_validations or {}
    ranked = sorted(
        scored_stocks,
        key=lambda x: (
            -x.get("score", 0),
            -x.get("factor_scores", {}).get("F1_tail_fund_inflow", 0),
            -x.get("factor_scores", {}).get("F4_tail_rally_strength", 0),
        ),
    )

    candidate_pool = [
        _candidate_with_validation(s, candidate_validations.get(s.get("symbol", "")))
        for s in ranked[: config.get("optimization", {}).get("candidate_pool_size", 20)]
    ]
    actual_best = _actual_best(candidate_pool)

    pick = None
    reject_reason = "无超阈值"
    selection_mode = "base"
    neighbor_rescue_config = config.get("selection", {}).get("neighbor_counterfactual_rescue", {})
    if (
        neighbor_rescue_history is not None
        and isinstance(neighbor_rescue_config, dict)
        and neighbor_rescue_config.get("enabled")
    ):
        rescue_sample = {"date": t_date, "candidate_pool": candidate_pool}
        rescue_pick = optimizer._pick_neighbor_counterfactual_rescue_candidate(
            rescue_sample,
            config,
            neighbor_rescue_config,
            neighbor_rescue_history,
        )
        if rescue_pick is not None:
            pick = next(
                (
                    stock for stock in ranked
                    if stock.get("symbol") == rescue_pick.get("symbol")
                ),
                rescue_pick,
            )
            selection_mode = rescue_pick.get("_selection_mode", "base")
        else:
            reject_reason = "邻近救援历史未确认"
    else:
        for stock in ranked:
            ok, reason = _passes_selection_rules(stock, config)
            if ok:
                pick = stock
                break
            reject_reason = reason
    if not pick:
        return {
            **base,
            "selected": False,
            "empty_reason": reject_reason,
            "candidate_pool": candidate_pool,
            "actual_best": actual_best,
            "missed_best_reason": _missed_best_reason(None, actual_best, config),
        }

    validation = candidate_validations.get(pick["symbol"])
    if validation is None:
        validation = validate_close_to_next_open(
            next_kline,
            t_date=t_date,
            t1_date=t1_date,
            execution_model=_execution_validation_model(config),
        )
    if validation is None:
        return {
            **base,
            "selected": False,
            "empty_reason": "缺少有效次日开盘验证数据",
            "candidate_pool": candidate_pool,
            "actual_best": actual_best,
            "missed_best_reason": _missed_best_reason(pick, actual_best, config),
        }

    if validation.get("execution_status") == "skipped":
        return {
            **base,
            "selected": True,
            "symbol": pick["symbol"],
            "name": pick.get("name", ""),
            "score": pick.get("score", 0),
            "factor_scores": pick.get("factor_scores", {}),
            "selection_mode": selection_mode,
            "buy_date": t_date,
            "sell_date": t1_date,
            "return": None,
            "win": False,
            "candidate_pool": candidate_pool,
            "actual_best": actual_best,
            "missed_best_reason": _missed_best_reason(pick, actual_best, config),
            **validation,
        }

    return {
        **base,
        "selected": True,
        "symbol": pick["symbol"],
        "name": pick.get("name", ""),
        "score": pick.get("score", 0),
        "factor_scores": pick.get("factor_scores", {}),
        "selection_mode": selection_mode,
        "buy_date": t_date,
        "sell_date": t1_date,
        "buy_price": validation["buy_price"],
        "sell_price": validation["sell_price"],
        "buy_price_source": validation["buy_price_source"],
        "sell_price_source": validation["sell_price_source"],
        "return": validation["return"],
        "win": validation["win"],
        "sell_reason": validation["sell_reason"],
        "candidate_pool": candidate_pool,
        "actual_best": actual_best,
        "missed_best_reason": _missed_best_reason(pick, actual_best, config),
        "execution_status": validation.get("execution_status", "filled"),
        "skip_reason": validation.get("skip_reason", ""),
        "gross_return": validation.get("gross_return", validation["return"]),
        "net_return": validation.get("net_return", validation["return"]),
    }


def fill_sample_names(samples: list[dict]) -> None:
    """补全样本、候选池、次日实际最优的股票名称。"""
    symbols = set()
    for sample in samples:
        for item in [sample, sample.get("actual_best") or {}, *sample.get("candidate_pool", [])]:
            symbol = str(item.get("symbol", "")).zfill(6)
            if symbol and symbol != "000000" and not str(item.get("name", "")).strip():
                symbols.add(symbol)

    if not symbols:
        return

    name_map = {}
    try:
        symbols_df = data_loader.get_a_share_symbols()
        if not symbols_df.empty:
            name_map.update({
                str(row["symbol"]).zfill(6): str(row["name"])
                for _, row in symbols_df.iterrows()
                if row.get("symbol") and row.get("name")
            })
    except Exception:
        pass

    missing = sorted(symbols - set(name_map))
    if missing:
        try:
            quotes = data_loader.tencent_quote(missing)
            for symbol, quote in quotes.items():
                name = str(quote.get("name", "")).strip()
                if name:
                    name_map[str(symbol).zfill(6)] = name
        except Exception:
            pass

    def apply_name(item: dict):
        symbol = str(item.get("symbol", "")).zfill(6)
        if symbol and not str(item.get("name", "")).strip() and name_map.get(symbol):
            item["name"] = name_map[symbol]

    for sample in samples:
        apply_name(sample)
        if isinstance(sample.get("actual_best"), dict):
            apply_name(sample["actual_best"])
        for candidate in sample.get("candidate_pool", []):
            apply_name(candidate)


# ---------------------------------------------------------------------------
# 回测主循环
# ---------------------------------------------------------------------------

def run_backtest(
    trading_days: int | None = DEFAULT_TRAINING_DAYS,
    universe_size: int = 150,
    overrides: dict | None = None,
) -> dict:
    """执行历史回测。

    trading_days: 回测交易日数；None 表示使用可验证全量历史
    universe_size: 股票池大小
    返回: {trades, performance, correlations, ranking_loss, meta}
    """
    config = strategy_engine.apply_runtime_overrides(strategy_engine.load_config(), overrides)
    conn = init_cache_db()
    clean_expired_cache(conn)

    # 1. 构建股票池
    universe = build_universe(universe_size)

    fetch_days = history_fetch_days(trading_days)
    calendar_limit = history_calendar_limit(trading_days)

    # 2. 批量拉取并缓存日K（按训练窗口动态扩展）
    print(f"[backtest] 批量拉取日K数据 ({len(universe)} 只 × {fetch_days} 日)...")
    fetched = 0
    for i, sym in enumerate(universe):
        # 检查缓存是否已有数据
        meta = conn.execute(
            "SELECT total_bars FROM cache_meta WHERE symbol=?", (sym,)
        ).fetchone()
        if meta and meta[0] >= fetch_days:
            fetched += 1
            continue
        try:
            df = data_loader.get_daily_kline(sym, days=fetch_days)
            if not df.empty:
                cache_kline(conn, sym, df)
                fetched += 1
        except Exception as e:
            print(f"  [warn] {sym} K线失败: {e}")
        if (i + 1) % 30 == 0:
            print(f"  进度: {i+1}/{len(universe)} (已缓存 {fetched})")
    print(f"[backtest] 日K拉取完成: {fetched}/{len(universe)}")

    # 3. 确定回测交易日历
    all_dates = pd.read_sql_query(
        "SELECT DISTINCT date FROM kline_cache ORDER BY date DESC LIMIT ?",
        conn,
        params=(calendar_limit,),
    )["date"].tolist()
    requested_days = trading_days
    if requested_days is not None and len(all_dates) < requested_days + 5:
        print(f"[backtest] 警告: 仅 {len(all_dates)} 个交易日可用")
        trading_days = max(10, len(all_dates) - 5)

    # 排除最后1天（T+1 验证需要次日数据，最后一天无 T+1）
    backtest_dates = select_backtest_dates(all_dates, trading_days)
    if not backtest_dates:
        raise RuntimeError("没有可回测的交易日；至少需要 2 个交易日的日K数据。")
    print(f"[backtest] 回测区间: {backtest_dates[0]} → {backtest_dates[-1]} ({len(backtest_dates)} 日)")

    # 4. 逐日训练：每个历史交易日生成 1 条 Top1/空仓样本
    all_samples = []
    daily_picks_log = []
    neighbor_rescue_history: dict[tuple[str, ...], list[dict]] = {}

    for t_idx, t_date in enumerate(backtest_dates):
        # T+1 日期 = 回测日历中 T 的下一个交易日
        if t_idx + 1 >= len(all_dates):
            continue
        # all_dates 是降序的，backtest_dates 是升序的
        # 需要找到 t_date 在 all_dates 中的位置，然后取前一个（更晚的）
        # all_dates[0] = 最新, all_dates[-1] = 最旧
        # backtest_dates 是 all_dates[1:trading_days+1] 的升序
        # t_date 在 all_dates 中的索引 = all_dates.index(t_date)
        # T+1 = all_dates[idx - 1]（更晚的一天）
        t_idx_in_all = all_dates.index(t_date)
        t1_date = all_dates[t_idx_in_all - 1]  # 前一天 = 更晚 = T+1

        # 收集当日候选
        scored_stocks = []
        for sym in universe:
            # 加载截止 T 日的 K线（含足够技术指标 warmup）
            kline_t = load_cached_kline(conn, sym, t_date, days=fetch_days)
            if kline_t is None or len(kline_t) < 30:
                continue
            # 确保 K线最后一天是 t_date
            if kline_t.iloc[-1]["date"][:10] != t_date[:10]:
                continue

            factors = calc_factors_daily(kline_t, config)
            if factors is None:
                continue

            scored_stocks.append({
                "symbol": sym,
                "score": factors["score"],
                "factor_scores": factors,
            })

        candidate_validations = {}
        if scored_stocks:
            ranked_for_validation = sorted(scored_stocks, key=lambda x: -x.get("score", 0))
            pool_size = config.get("optimization", {}).get("candidate_pool_size", 20)
            for candidate in ranked_for_validation[:pool_size]:
                sym = candidate["symbol"]
                candidate_kline = load_cached_kline(conn, sym, t1_date, days=fetch_days)
                validation = validate_close_to_next_open(
                    candidate_kline,
                    t_date=t_date,
                    t1_date=t1_date,
                    execution_model=_execution_validation_model(config),
                )
                if validation is not None:
                    candidate_validations[sym] = validation

        sample = build_daily_sample(
            t_date=t_date,
            t1_date=t1_date,
            scored_stocks=scored_stocks,
            config=config,
            candidate_validations=candidate_validations,
            neighbor_rescue_history=neighbor_rescue_history,
        )
        all_samples.append(sample)

        if sample.get("selected"):
            daily_picks_log.append({"date": t_date, "t1_date": t1_date, "picks": [sample]})
            win_text = "胜" if sample.get("win") else "负"
            print(f"  {t_date} → {t1_date}: {sample['symbol']} {sample['return']:.2%} {win_text}")
        else:
            daily_picks_log.append({"date": t_date, "t1_date": t1_date,
                                    "picks": [], "reason": sample.get("empty_reason")})
            print(f"  {t_date} → {t1_date}: 空仓 ({sample.get('empty_reason')})")

    conn.close()

    # 补充股票名称
    print("[backtest] 补充股票名称...")
    fill_sample_names(all_samples)

    # 5. 计算绩效
    selected_samples = [s for s in all_samples if s.get("selected")]
    performance = recompute_performance_full(selected_samples)
    correlations = compute_factor_correlations(selected_samples)
    ranking_loss = compute_ranking_loss(selected_samples)

    # 6. 保存
    save_strategy_samples(all_samples)
    save_trades(selected_samples)
    save_performance(performance)
    save_backtest_meta({
        "backtest_period": {
            "start": backtest_dates[0] if backtest_dates else "",
            "end": backtest_dates[-1] if backtest_dates else "",
            "trading_days": len(backtest_dates),
            "requested_trading_days": requested_days if requested_days is not None else "all",
            "history_fetch_days": fetch_days,
            "universe_size": universe_size,
            "runtime_overrides": config.get("runtime_overrides", {}),
        },
        "total_samples": len(all_samples),
        "selected_samples": len(selected_samples),
        "empty_days": len(all_samples) - len(selected_samples),
        "ranking_loss": ranking_loss,
        "correlations": correlations,
        "run_at": dt.datetime.now().isoformat(),
    })

    print(f"\n[backtest] 回测完成:")
    print(f"  样本日: {len(all_samples)} 日")
    print(f"  出手: {len(selected_samples)} 笔 / 空仓 {len(all_samples) - len(selected_samples)} 日")
    print(f"  总胜率: {performance['total']['win_rate']:.1%}")
    print(f"  盈亏比: 1:{performance['total']['pl_ratio']:.2f}")
    print(f"  排序损失: {ranking_loss}")

    return {
        "samples": all_samples,
        "trades": selected_samples,
        "performance": performance,
        "correlations": correlations,
        "ranking_loss": ranking_loss,
        "daily_picks_log": daily_picks_log,
        "backtest_period": {
            "start": backtest_dates[0] if backtest_dates else "",
            "end": backtest_dates[-1] if backtest_dates else "",
            "trading_days": len(backtest_dates),
            "universe_size": universe_size,
        },
    }


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_training_report(result: dict) -> str:
    """渲染历史训练 Markdown 报告。"""
    samples = result.get("samples", [])
    selected = [s for s in samples if s.get("selected")]
    empty = [s for s in samples if not s.get("selected")]
    wins = [s for s in selected if s.get("win")]
    perf_total = result.get("performance", {}).get("total", {})
    period = result.get("backtest_period", {})

    win_rate = len(wins) / len(selected) if selected else 0
    avg_return = sum(float(s.get("return", 0) or 0) for s in selected) / len(selected) if selected else 0

    lines = [
        f"# A股尾盘隔夜策略历史训练报告 - {dt.datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"> 生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "口径：T 日收盘价买入 → T+1 日开盘价卖出 | 纸面训练，不构成投资建议",
        "",
        "## 一、训练摘要",
        "",
        f"- 回测区间：{period.get('start', '-')} → {period.get('end', '-')}",
        f"- 交易日样本：{len(samples)} 日",
        f"- 出手：{len(selected)} 笔",
        f"- 空仓：{len(empty)} 日",
        f"- 胜：{len(wins)} 笔",
        f"- 胜率：{_pct(win_rate)}",
        f"- 平均收益：{_pct(avg_return)}",
        f"- 累计样本收益：{_pct(perf_total.get('total_return', sum(float(s.get('return', 0) or 0) for s in selected)))}",
        f"- 最大连亏：{perf_total.get('max_consecutive_loss', 0)}",
        f"- 排序损失：{result.get('ranking_loss', 1.0)}",
        "",
        "## 二、分层反馈指标",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 历史训练胜率 | {_pct(win_rate)} |",
        "| 实际执行胜率 | 暂无 live_paper 样本 |",
        f"| 综合胜率 | {_pct(win_rate)} |",
        f"| 空仓率 | {_pct(len(empty) / len(samples) if samples else 0)} |",
        "",
        "## 三、历史逐日样本",
        "",
        "| 日期 | 状态 | 代码 | 名称 | 得分 | 买入价(T收盘) | 卖出价(T+1开盘) | 收益率 | 胜负/原因 | 次日实际最优 | 未选原因 |",
        "|------|------|------|------|------|---------------|-----------------|--------|-----------|--------------|----------|",
    ]

    for s in sorted(samples, key=lambda item: str(item.get("date", "")), reverse=True):
        actual_best = s.get("actual_best") or {}
        best_ret = actual_best.get("return")
        best_text = "-"
        if actual_best.get("symbol") and isinstance(best_ret, (int, float)):
            best_text = (
                f"{actual_best.get('symbol','')} {actual_best.get('name','')} "
                f"({_pct(best_ret)})"
            )
        missed_reason = s.get("missed_best_reason", "-")
        if s.get("selected"):
            lines.append(
                f"| {s.get('date','')} | 出手 | {s.get('symbol','')} | {s.get('name','')} | "
                f"{s.get('score',0):.2f} | {s.get('buy_price',0):.2f} | "
                f"{s.get('sell_price',0):.2f} | {_pct(s.get('return',0))} | "
                f"{'胜' if s.get('win') else '负'} | {best_text} | {missed_reason} |"
            )
        else:
            lines.append(
                f"| {s.get('date','')} | 空仓 | - | - | - | - | - | - | "
                f"{s.get('empty_reason','空仓')} | {best_text} | {missed_reason} |"
            )

    lines.extend([
        "",
        "## 四、初步结论",
        "",
    ])
    if selected and win_rate < 0.55:
        lines.append("- 当前历史训练胜率低于 55% 目标，策略需要先做失败样本归因，再考虑调整参数。")
    if perf_total.get("max_consecutive_loss", 0) >= 3:
        lines.append(f"- 最大连亏 {perf_total.get('max_consecutive_loss')}，已超过风控目标，需要重点检查连续亏损区间。")
    if not selected:
        lines.append("- 当前训练区间未产生出手样本，需要检查阈值、过滤条件或数据完整性。")
    lines.append("- 本报告只用于策略纸面验证，不构成任何投资建议。")
    lines.append("")
    return "\n".join(lines)


def generate_training_report(result: dict, date_str: str = None) -> Path:
    """保存历史训练报告。主流程使用日报生成器，本函数仅保留兼容入口。"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if date_str is None:
        date_str = dt.datetime.now().strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"{date_str}.md"
    path.write_text(render_training_report(result), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 绩效统计
# ---------------------------------------------------------------------------

def recompute_performance_full(trades: list[dict]) -> dict:
    """完整绩效计算：7d/30d/total + 分月 + 分星期 + 分市场环境。"""
    today = dt.datetime.now()
    selected_days = len(trades)
    skipped_executions = sum(1 for trade in trades if trade.get("execution_status") == "skipped")
    trades = [
        trade for trade in trades
        if trade.get("execution_status") != "skipped"
        and isinstance(trade.get("return"), (int, float))
    ]

    def _calc_period(trades_subset: list[dict]) -> dict:
        if not trades_subset:
            return {"win_rate": 0, "pl_ratio": 0, "max_consecutive_loss": 0, "samples": 0}
        wins = [t for t in trades_subset if t.get("return", 0) > 0]
        losses = [t for t in trades_subset if t.get("return", 0) <= 0]
        win_rate = len(wins) / len(trades_subset)
        avg_win = (sum(t["return"] for t in wins) / len(wins)) if wins else 0
        avg_loss = abs(sum(t["return"] for t in losses) / len(losses)) if losses else 0
        pl_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        sorted_t = sorted(trades_subset, key=lambda x: x.get("buy_date", ""))
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
            "samples": len(trades_subset),
            "avg_win": round(avg_win, 4),
            "avg_loss": round(avg_loss, 4),
            "total_return": round(sum(t["return"] for t in trades_subset), 4),
        }

    # 按周期
    result = {
        "7d": _calc_period([t for t in trades
                            if (today - dt.datetime.fromisoformat(t["buy_date"])).days <= 7]),
        "30d": _calc_period([t for t in trades
                             if (today - dt.datetime.fromisoformat(t["buy_date"])).days <= 30]),
        "total": _calc_period(trades),
        "updated_at": today.isoformat(),
    }
    for period in ("7d", "30d", "total"):
        result[period]["selected_days"] = selected_days if period == "total" else result[period]["samples"]
        result[period]["executable_trades"] = result[period]["samples"]
        result[period]["skipped_executions"] = skipped_executions if period == "total" else 0
        result[period]["execution_coverage"] = round(len(trades) / selected_days, 4) if selected_days else 0

    # 按月分组
    by_month = {}
    for t in trades:
        month = t["buy_date"][:7]
        by_month.setdefault(month, []).append(t)
    result["by_month"] = {m: _calc_period(ts) for m, ts in sorted(by_month.items())}

    # 按星期分组
    by_weekday = {}
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    for t in trades:
        wd = dt.datetime.fromisoformat(t["buy_date"]).weekday()
        wd_name = weekday_names[wd]
        by_weekday.setdefault(wd_name, []).append(t)
    result["by_weekday"] = {w: _calc_period(ts) for w, ts in by_weekday.items()}

    # 按市场环境分组（用上证涨跌代理：用 T 日沪深300/上证近似）
    # 简化：按 T+1 日（买入日）的涨跌分组
    by_market = {"大涨": [], "小涨": [], "震荡": [], "小跌": [], "大跌": []}
    for t in trades:
        # 用 T+1 的收益率近似市场环境（个股自身的 buy→sell）
        # 更好：用指数，但回测中我们用个贸收益率分布做代理
        ret = t.get("return", 0)
        if ret >= 0.03:
            by_market["大涨"].append(t)
        elif ret >= 0.01:
            by_market["小涨"].append(t)
        elif ret >= -0.01:
            by_market["震荡"].append(t)
        elif ret >= -0.03:
            by_market["小跌"].append(t)
        else:
            by_market["大跌"].append(t)
    result["by_market_env"] = {k: _calc_period(v) for k, v in by_market.items()}

    # 按卖出原因
    by_reason = {}
    for t in trades:
        r = t.get("sell_reason", "close")
        by_reason.setdefault(r, []).append(t)
    result["by_sell_reason"] = {r: _calc_period(ts) for r, ts in by_reason.items()}

    return result


def compute_factor_correlations(trades: list[dict]) -> dict:
    """计算各因子分与收益率的 Spearman 秩相关。"""
    factor_scores = {fk: [] for fk in FACTOR_KEYS}
    returns = []
    for t in trades:
        fs = t.get("factor_scores", {})
        if not fs:
            continue
        for fk in FACTOR_KEYS:
            if fk in fs:
                factor_scores[fk].append(fs[fk])
        returns.append(t.get("return", 0))

    if len(returns) < 5:
        return {fk: 0.0 for fk in FACTOR_KEYS}

    correlations = {}
    for fk in FACTOR_KEYS:
        scores = factor_scores[fk]
        if len(scores) == len(returns) and len(scores) >= 5:
            try:
                if spearmanr is None:
                    correlations[fk] = 0.0
                    continue
                rho, _ = spearmanr(scores, returns)
                correlations[fk] = round(float(rho) if not np.isnan(rho) else 0, 4)
            except Exception:
                correlations[fk] = 0.0
        else:
            correlations[fk] = 0.0
    return correlations


def compute_ranking_loss(trades: list[dict]) -> float:
    """理想排序(按收益率)与实际排序(按Score)的 Kendall τ 距离。"""
    scored = [t for t in trades if "score" in t and "return" in t]
    if len(scored) < 5:
        return 1.0
    actual = sorted(scored, key=lambda x: -x["score"])
    ideal = sorted(scored, key=lambda x: -x["return"])
    actual_pos = {id(t): i for i, t in enumerate(actual)}
    ideal_pos = {id(t): i for i, t in enumerate(ideal)}
    n = len(scored)
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            a_i, a_j = actual_pos[id(actual[i])], actual_pos[id(actual[j])]
            i_i, i_j = ideal_pos[id(actual[i])], ideal_pos[id(actual[j])]
            if (a_i - a_j) * (i_i - i_j) < 0:
                discordant += 1
    total = n * (n - 1) / 2
    return round(discordant / total, 4) if total > 0 else 1.0


# ---------------------------------------------------------------------------
# 保存
# ---------------------------------------------------------------------------

def save_trades(trades: list[dict]):
    with TRADES_PATH.open("w", encoding="utf-8") as f:
        json.dump({"trades": trades, "updated_at": dt.datetime.now().isoformat()},
                  f, ensure_ascii=False, indent=2)


def save_strategy_samples(samples: list[dict]):
    """刷新历史训练层并保留真实执行层。

    train_history 是当前策略在固定历史窗口上的重新推演，历史训练样本必须整体替换；
    live_paper 是实际执行记录，只能按 date+sample_type 保留或更新。
    """
    SAMPLE_POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SAMPLE_POOL_PATH.exists():
        try:
            existing = json.loads(SAMPLE_POOL_PATH.read_text(encoding="utf-8")).get("samples", [])
        except (json.JSONDecodeError, OSError):
            existing = []
    else:
        existing = []

    incoming_has_historical = any(
        sample.get("sample_type", "historical_training") == "historical_training"
        for sample in samples
    )
    if incoming_has_historical:
        existing = [
            s for s in existing
            if s.get("sample_type", "historical_training") != "historical_training"
        ]

    merged = {
        (s.get("date"), s.get("sample_type", "historical_training")): s
        for s in existing
    }
    for sample in samples:
        key = (sample.get("date"), sample.get("sample_type", "historical_training"))
        merged[key] = sample

    ordered = sorted(
        merged.values(),
        key=lambda s: (str(s.get("date", "")), str(s.get("sample_type", ""))),
    )
    SAMPLE_POOL_PATH.write_text(
        json.dumps({"samples": ordered, "updated_at": dt.datetime.now().isoformat()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_performance(perf: dict):
    with PERF_PATH.open("w", encoding="utf-8") as f:
        json.dump(perf, f, ensure_ascii=False, indent=2)


def save_backtest_meta(meta: dict):
    BACKTEST_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKTEST_META_PATH.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--days" and i + 1 < len(sys.argv):
            args["days"] = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--universe" and i + 1 < len(sys.argv):
            args["universe"] = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    result = run_backtest(
        trading_days=args.get("days", DEFAULT_TRAINING_DAYS),
        universe_size=args.get("universe", 150),
    )
    path = generate_training_report(result)
    print(f"[report] 训练报告已保存到 {path}")


if __name__ == "__main__":
    main()
