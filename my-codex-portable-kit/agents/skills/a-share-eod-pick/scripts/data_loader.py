"""
A股尾盘隔夜策略 - 数据加载模块

数据源优先级：mootdx > 腾讯 > 新浪（行情/K线）
              东财 > 同花顺 > mootdx（资金流向）
失败降级路径会被记录到返回结果的 source 字段。

依赖：pip install mootdx akshare pandas requests
"""

import json
import time
import math
import random
import socket
import sqlite3
import datetime as dt
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

try:
    from mootdx.quotes import Quotes
    _HAS_MOOTDX = True
except Exception:
    _HAS_MOOTDX = False

try:
    import akshare as ak
    _HAS_AKSHARE = True
except Exception:
    _HAS_AKSHARE = False

try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False


SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "config" / "strategy_params.json"
CACHE_DB = SKILL_ROOT / "data" / "cache" / "backtest_kline.db"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


# ---------------------------------------------------------------------------
# mootdx 配置路径 patch（沙盒/便携环境适配）
# 将 ~/.mootdx/config.json 重定向到技能目录内 .mootdx/config.json，
# 避免沙盒禁止写入 HOME 目录；同时预置默认服务器列表以跳过 bestip 测速。
# ---------------------------------------------------------------------------
if _HAS_MOOTDX:
    import mootdx.config as _mootdx_config
    from mootdx.consts import HQ_HOSTS, EX_HOSTS, GP_HOSTS

    _MOOTDX_DIR = SKILL_ROOT / ".mootdx"
    _MOOTDX_DIR.mkdir(parents=True, exist_ok=True)
    _MOOTDX_CONF = str(_MOOTDX_DIR / "config.json")
    _mootdx_config.CONF = _MOOTDX_CONF

    if not Path(_MOOTDX_CONF).exists():
        # 取第一个 HQ 服务器作为 BESTIP，避免 bestip 测速写文件
        _first_hq = HQ_HOSTS[0]
        _default_cfg = {
            "SERVER": {"HQ": HQ_HOSTS, "EX": EX_HOSTS, "GP": GP_HOSTS},
            "BESTIP": {
                "HQ": [_first_hq[1], _first_hq[2]],
                "EX": "",
                "GP": "",
            },
            "TDXDIR": "C:/new_tdx",
        }
        with open(_MOOTDX_CONF, "w", encoding="utf-8") as _f:
            json.dump(_default_cfg, _f, ensure_ascii=False)

    # 同步 patch get_config_path，供 holiday/adjust 等缓存路径使用
    import mootdx.utils as _mootdx_utils
    _orig_get_config_path = _mootdx_utils.get_config_path

    def _patched_get_config_path(config="config.json"):
        return str(_MOOTDX_DIR / config)

    _mootdx_utils.get_config_path = _patched_get_config_path


# ---------------------------------------------------------------------------
# tdx_client(): 统一 mootdx 客户端创建（规避 0.11.x BESTIP.HQ 空串 bug）
# 显式传 server，顺序探测多台服务器 TCP 可达性，多级 fallback。
# ---------------------------------------------------------------------------
if _HAS_MOOTDX:
    _TDX_SERVERS = [
        ('119.97.185.59', 7709), ('124.70.133.119', 7709), ('116.205.183.150', 7709),
        ('123.60.73.44', 7709),  ('116.205.163.254', 7709), ('121.36.225.169', 7709),
        ('123.60.70.228', 7709), ('124.71.9.153', 7709),    ('110.41.147.114', 7709),
        ('124.71.187.122', 7709),
    ]

    def _tdx_probe(ip, port, timeout=2.0):
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return True
        except Exception:
            return False

    def tdx_client(market='std'):
        """创建 mootdx 客户端。顺序探测多台服务器，全部不可达回退 bestip/bare factory。"""
        for ip, port in _TDX_SERVERS:
            if _tdx_probe(ip, port):
                try:
                    return Quotes.factory(market=market, server=(ip, port))
                except Exception:
                    continue
        try:
            return Quotes.factory(market=market, bestip=True)
        except Exception:
            pass
        try:
            return Quotes.factory(market=market)
        except Exception as e:
            raise RuntimeError(f"所有 mootdx 服务器均不可达: {e}")


# ---------------------------------------------------------------------------
# em_get(): 东财统一请求入口（防封节流 + 会话复用）
# 所有 eastmoney.com 接口走此函数：最小间隔 + 随机抖动 + Keep-Alive。
# ---------------------------------------------------------------------------
if _HAS_REQUESTS:
    EM_SESSION = requests.Session()
    EM_SESSION.headers.update({"User-Agent": UA})
    EM_MIN_INTERVAL = 1.0          # 东财两次请求最小间隔（秒）
    _em_last_call = [0.0]

    def em_get(url, params=None, headers=None, timeout=15, **kwargs):
        """东财统一请求入口：自动节流 + 复用 session + 默认 UA。"""
        wait = EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
        if wait > 0:
            time.sleep(wait + random.uniform(0.1, 0.5))
        try:
            return EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
        finally:
            _em_last_call[0] = time.time()


# ---------------------------------------------------------------------------
# tencent_quote(): 腾讯财经批量行情（一次拿 PE/PB/总市值/流通市值/换手率/涨跌停）
# 不封 IP，GBK 编码，~ 分隔 88 字段。
# ---------------------------------------------------------------------------
def _tencent_prefix(code: str) -> str:
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith("8"):
        return "bj"
    return "sz"


def tencent_quote(codes):
    """批量拉取腾讯财经实时行情。返回 {code: {name, price, pe_ttm, pb, mcap_yi, float_mcap_yi, ...}}"""
    if not codes:
        return {}
    prefixed = [_tencent_prefix(c) + c for c in codes]
    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    try:
        req = __import__('urllib.request', fromlist=['Request']).Request(url)
        req.add_header("User-Agent", UA)
        resp = __import__('urllib.request', fromlist=['urlopen']).urlopen(req, timeout=10)
        data = resp.read().decode("gbk")
    except Exception as e:
        print(f"[data_loader] 腾讯批量行情失败: {e}")
        return {}

    result = {}
    for line in data.strip().split(";"):
        line = line.strip()
        if not line or "=" not in line or '"' not in line:
            continue
        try:
            key = line.split("=")[0].split("_")[-1]
            vals = line.split('"')[1].split("~")
            if len(vals) < 53:
                continue
            code = key[2:]
            def _f(i):
                try:
                    return float(vals[i]) if vals[i] else 0.0
                except (ValueError, IndexError):
                    return 0.0
            result[code] = {
                "name":         vals[1],
                "price":        _f(3),
                "pre_close":    _f(4),
                "open":         _f(5),
                "high":         _f(33),
                "low":          _f(34),
                "change_pct":   _f(32) / 100,   # 涨跌幅（已除100）
                "amount_wan":   _f(37),
                "turnover_pct": _f(38),
                "pe_ttm":       _f(39),
                "amplitude_pct":_f(43),
                "mcap_yi":      _f(44),         # 总市值（亿）
                "float_mcap_yi":_f(45),         # 流通市值（亿）
                "pb":           _f(46),
                "limit_up":     _f(47),
                "limit_down":   _f(48),
                "vol_ratio":    _f(49),
            }
        except Exception:
            continue
    return result


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"策略配置缺失: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. 股票池基础信息
# ---------------------------------------------------------------------------

def get_a_share_symbols() -> pd.DataFrame:
    """获取沪深主板股票清单（含名称），剔除 ST/*ST/退市。

    返回 DataFrame: columns=[symbol, name, market]
        market: 'sh' | 'sz'
    """
    df = pd.DataFrame()
    source = "unknown"

    # 优先 akshare
    if _HAS_AKSHARE:
        try:
            df = ak.stock_info_a_code_name()
            df = df.rename(columns={"code": "symbol", "name": "name"})
            source = "akshare"
        except Exception:
            df = pd.DataFrame()

    # 备选 mootdx
    if df.empty and _HAS_MOOTDX:
        try:
            client = tdx_client()
            sh = client.stocks(market=1)  # 上海
            sz = client.stocks(market=0)  # 深圳
            frames = []
            if isinstance(sh, list):
                frames.append(pd.DataFrame(sh).assign(market="sh"))
            if isinstance(sz, list):
                frames.append(pd.DataFrame(sz).assign(market="sz"))
            if frames:
                df = pd.concat(frames, ignore_index=True)
                df = df.rename(columns={"code": "symbol", "name": "name"})
                source = "mootdx"
        except Exception:
            pass

    # 再兜底：使用历史训练 K 线缓存里的股票池，再用腾讯补名称。
    if df.empty:
        df = _fetch_symbols_from_kline_cache()
        if not df.empty:
            source = "kline_cache_tencent"

    if df.empty:
        raise RuntimeError("无法获取 A 股股票清单，请检查 mootdx/akshare 连接")

    df["symbol"] = df["symbol"].astype(str).str.zfill(6)

    # 主板过滤：60/00/001/002/003 前缀
    prefix_ok = df["symbol"].str.match(r"^(60|00|001|002|003)")
    df = df[prefix_ok].copy()

    # 剔除 ST/*ST/退市
    name_bad = df["name"].str.contains(r"ST|\*ST|退", na=False, regex=True)
    df = df[~name_bad].reset_index(drop=True)

    if "market" not in df.columns:
        df["market"] = df["symbol"].str.startswith("6").map({True: "sh", False: "sz"})

    df.attrs["source"] = source
    return df


def _fetch_symbols_from_kline_cache(limit: int = 500) -> pd.DataFrame:
    """从历史 K 线缓存恢复股票清单，供腾讯行情批量兜底。"""
    if not CACHE_DB.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(str(CACHE_DB))
        rows = conn.execute("""
            SELECT symbol
            FROM cache_meta
            ORDER BY total_bars DESC, symbol ASC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
    except Exception:
        return pd.DataFrame()

    symbols = [str(row[0]).zfill(6) for row in rows]
    symbols = [s for s in symbols if s.startswith(("60", "00", "001", "002", "003"))]
    if not symbols:
        return pd.DataFrame()

    quotes = tencent_quote(symbols)
    data = []
    for symbol in symbols:
        quote = quotes.get(symbol, {})
        name = str(quote.get("name", "")).strip()
        if not name:
            name = symbol
        data.append({
            "symbol": symbol,
            "name": name,
            "market": "sh" if symbol.startswith("6") else "sz",
        })
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# 1.1 全市场实时快照（东财 push2 直连，含流通市值，绕过 akshare 封禁）
# ---------------------------------------------------------------------------

def get_market_snapshot() -> pd.DataFrame:
    """全市场实时快照，含流通市值。

    优先腾讯批量（不封IP，含PE/PB/市值）；降级东财 push2 clist。
    返回列：symbol, name, price, pre_close, open, high, low, volume, amount,
            pct_change, float_mv, timestamp
    """
    # 优先：腾讯批量（不封IP，字段更全）
    try:
        df = _fetch_market_snapshot_tencent()
        if not df.empty:
            df.attrs["source"] = "tencent"
            return df
    except Exception as e:
        print(f"[data_loader] 腾讯快照失败: {e}")

    # 降级：东财 push2 clist
    if _HAS_REQUESTS:
        df = _fetch_market_snapshot_eastmoney()
        if not df.empty:
            df.attrs["source"] = "eastmoney_direct"
            return df

    return pd.DataFrame()


def _fetch_market_snapshot_tencent() -> pd.DataFrame:
    """腾讯批量行情构建全市场快照。每批80只，不封IP。"""
    try:
        symbols_df = get_a_share_symbols()
        all_symbols = symbols_df["symbol"].tolist()
    except Exception as e:
        print(f"[data_loader] 获取股票清单失败: {e}")
        return pd.DataFrame()

    rows = []
    batch_size = 80
    for i in range(0, len(all_symbols), batch_size):
        batch = all_symbols[i:i + batch_size]
        tq = tencent_quote(batch)
        for code, q in tq.items():
            if q.get("price", 0) <= 0:
                continue
            rows.append({
                "symbol":     code,
                "name":       q["name"],
                "price":      q["price"],
                "pct_change": q["change_pct"],
                "volume":     0.0,                     # 腾讯不返回成交量
                "amount":     q["amount_wan"] * 1e4,    # 万元 → 元
                "turnover":   q["turnover_pct"],
                "high":       q["high"],
                "low":        q["low"],
                "open":       q["open"],
                "pre_close":  q["pre_close"],
                "float_mv":   q["float_mcap_yi"] * 1e8, # 亿 → 元
            })
        time.sleep(0.15)  # 腾讯不封IP，但仍加少量间隔避免被限速

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = dt.datetime.now()
    return df.reset_index(drop=True)


def _fetch_market_snapshot_eastmoney() -> pd.DataFrame:
    """东财 push2 全市场实时快照，含流通市值（akshare被封时备用）。"""
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    rows = []

    def _num(value):
        if value in (None, "-", ""):
            raise ValueError("placeholder numeric field")
        return float(value)

    def _optional_num(*values, default=0.0):
        for value in values:
            try:
                return _num(value)
            except (TypeError, ValueError):
                continue
        return default

    for fs in ["m:1 t:2", "m:0 t:6", "m:0 t:13"]:
        params = {
            'pn': 1, 'pz': 2000, 'po': 1, 'np': 1,
            'fltt': 2, 'invt': 2,
            'fs': fs,
            'fields': 'f12,f14,f2,f3,f4,f5,f6,f8,f15,f16,f17,f18,f21,f117',
        }
        headers = {
            'User-Agent': UA,
            'Referer': 'https://quote.eastmoney.com/center/gridlist.html',
        }
        try:
            r = em_get(url, params=params, headers=headers, timeout=15)
            payload = r.json()
            data = payload.get('data') or {}
            items = data.get('diff', []) or []
            for it in items:
                try:
                    price = _num(it.get("f2"))
                    row = {
                        "symbol": str(it.get("f12", "")).zfill(6),
                        "name": it.get("f14", ""),
                        "price": price,
                        "pct_change": _num(it.get("f3")) / 100,
                        "volume": _num(it.get("f5")),
                        "amount": _num(it.get("f6")),
                        "turnover": _num(it.get("f8")),
                        "high": _num(it.get("f15")),
                        "low": _num(it.get("f16")),
                        "open": _num(it.get("f17")),
                        "pre_close": _num(it.get("f18")),
                        "float_mv": _optional_num(it.get("f117"), it.get("f21")),
                    }
                except (TypeError, ValueError):
                    continue
                rows.append(row)
        except Exception as e:
            print(f"[data_loader] 东财快照失败 fs={fs}: {e}")

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # 主板过滤：60/00/001/002/003 前缀
    df = df[df["symbol"].str.match(r"^(60|00|001|002|003)")].copy()
    # 剔除 ST/*ST/退市
    df = df[~df["name"].str.contains(r"ST|\*ST|退", na=False, regex=True)]
    df["timestamp"] = dt.datetime.now()
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. 实时行情
# ---------------------------------------------------------------------------

def get_realtime_quotes(symbols: list[str]) -> pd.DataFrame:
    """批量获取实时行情（收盘价、成交量、成交额等）。

    返回列：
        symbol, name, price, open, high, low, pre_close,
        volume, amount, pct_change, timestamp, source
    """
    if not symbols:
        return pd.DataFrame()

    # 优先 mootdx 批量
    if _HAS_MOOTDX:
        try:
            df = _fetch_realtime_mootdx(symbols)
            if not df.empty:
                df.attrs["source"] = "mootdx"
                return df
        except Exception as e:
            print(f"[data_loader] mootdx 实时行情失败: {e}")

    # 降级腾讯
    if _HAS_REQUESTS:
        try:
            df = _fetch_realtime_tencent(symbols)
            if not df.empty:
                df.attrs["source"] = "tencent"
                return df
        except Exception as e:
            print(f"[data_loader] 腾讯实时行情失败: {e}")

    # 再降级新浪
    if _HAS_REQUESTS:
        try:
            df = _fetch_realtime_sina(symbols)
            if not df.empty:
                df.attrs["source"] = "sina"
                return df
        except Exception as e:
            print(f"[data_loader] 新浪实时行情失败: {e}")

    raise RuntimeError("所有实时行情数据源均不可用")


def _fetch_realtime_mootdx(symbols: list[str]) -> pd.DataFrame:
    client = tdx_client()
    rows = []
    # mootdx 一次最多 80 只
    for i in range(0, len(symbols), 80):
        batch = symbols[i:i + 80]
        result = client.quotes(symbol=batch)
        # mootdx 返回结构可能为 DataFrame 或 list[dict]
        if isinstance(result, pd.DataFrame):
            rows.append(result)
        elif isinstance(result, list):
            rows.append(pd.DataFrame(result))
        time.sleep(0.05)
    if not rows:
        return pd.DataFrame()
    df = pd.concat(rows, ignore_index=True)

    # mootdx 原始列名归一化到统一 schema
    rename_map = {
        "code": "symbol",
        "last_close": "pre_close",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    if "name" not in df.columns:
        df["name"] = ""
    # volume 优先用 volume 列，缺失时回退 vol
    if "volume" not in df.columns and "vol" in df.columns:
        df = df.rename(columns={"vol": "volume"})

    # 计算涨跌幅
    if "pct_change" not in df.columns and "price" in df.columns and "pre_close" in df.columns:
        pre = df["pre_close"].replace(0, np.nan)
        df["pct_change"] = (df["price"] - pre) / pre.fillna(df["price"])

    df["timestamp"] = dt.datetime.now()
    return df


def _fetch_realtime_tencent(symbols: list[str]) -> pd.DataFrame:
    """腾讯实时行情接口。"""
    codes = [f"sh{s}" if s.startswith("6") else f"sz{s}" for s in symbols]
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    resp = requests.get(url, timeout=10)
    resp.encoding = "gbk"
    rows = []
    for line in resp.text.strip().split(";"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        try:
            head, body = line.split("=", 1)
            body = body.strip('"')
            fields = body.split("~")
            if len(fields) < 35:
                continue
            rows.append({
                "symbol": head[-6:],
                "name": fields[1],
                "price": float(fields[3]),
                "pre_close": float(fields[4]),
                "open": float(fields[5]),
                "volume": float(fields[6]),
                "amount": float(fields[37]) if len(fields) > 37 else float(fields[36]),
                "high": float(fields[33]),
                "low": float(fields[34]),
            })
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["pct_change"] = (df["price"] - df["pre_close"]) / df["pre_close"]
    df["timestamp"] = dt.datetime.now()
    return df


def _fetch_realtime_sina(symbols: list[str]) -> pd.DataFrame:
    """新浪实时行情接口。"""
    codes = [f"sh{s}" if s.startswith("6") else f"sz{s}" for s in symbols]
    url = "https://hq.sinajs.cn/list=" + ",".join(codes)
    headers = {"Referer": "https://finance.sina.com.cn"}
    resp = requests.get(url, timeout=10, headers=headers)
    resp.encoding = "gbk"
    rows = []
    for line in resp.text.strip().split("\n"):
        if "=" not in line:
            continue
        try:
            head, body = line.split("=", 1)
            body = body.strip().strip('"').strip(";")
            fields = body.split(",")
            if len(fields) < 10:
                continue
            sym = head.split("=")[0].split("_")[-1][-6:]
            pre_close = float(fields[2])
            price = float(fields[3] or fields[1])
            rows.append({
                "symbol": sym,
                "name": fields[0],
                "open": float(fields[1]),
                "pre_close": pre_close,
                "price": price,
                "high": float(fields[4]),
                "low": float(fields[5]),
                "volume": float(fields[8]),
                "amount": float(fields[9]),
            })
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["pct_change"] = (df["price"] - df["pre_close"]) / df["pre_close"]
    df["timestamp"] = dt.datetime.now()
    return df


# ---------------------------------------------------------------------------
# 3. 日K线（复权）
# ---------------------------------------------------------------------------

def get_daily_kline(symbol: str, days: int = 60) -> pd.DataFrame:
    """获取日K线（前复权）。

    返回列：date, open, high, low, close, volume, amount
    """
    if _HAS_MOOTDX:
        try:
            df = _fetch_kline_mootdx(symbol, days)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[data_loader] mootdx K线失败 {symbol}: {e}")

    if _HAS_AKSHARE:
        try:
            df = _fetch_kline_akshare(symbol, days)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[data_loader] akshare K线失败 {symbol}: {e}")

    if _HAS_REQUESTS:
        try:
            df = _fetch_kline_baidu(symbol, days)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[data_loader] 百度K线失败 {symbol}: {e}")

    try:
        df = _fetch_kline_cache(symbol, days)
        if not df.empty:
            return df
    except Exception as e:
        print(f"[data_loader] 本地K线缓存失败 {symbol}: {e}")

    raise RuntimeError(f"无法获取 {symbol} 的日K线")


def _fetch_kline_mootdx(symbol: str, days: int) -> pd.DataFrame:
    client = tdx_client()
    market = 1 if symbol.startswith("6") else 0
    start = 0
    # mootdx offset 表示从最新往前取
    df = client.bars(symbol=symbol, frequency=9, offset=days)
    if isinstance(df, pd.DataFrame):
        df = df.copy()
        # mootdx 列：datetime, open, close, high, low, vol, amount, ..., volume
        col_map = {
            "datetime": "date",
            "vol": "volume",
        }
        df = df.rename(columns=col_map)
        # mootdx 同时返回 vol 与 volume，rename 后会重复，保留首个
        df = df.loc[:, ~df.columns.duplicated()]
        keep = ["date", "open", "high", "low", "close", "volume", "amount"]
        keep = [c for c in keep if c in df.columns]
        return df[keep].tail(days).reset_index(drop=True)
    return pd.DataFrame()


def _fetch_kline_akshare(symbol: str, days: int) -> pd.DataFrame:
    end = dt.datetime.now().strftime("%Y%m%d")
    start = (dt.datetime.now() - dt.timedelta(days=days * 2)).strftime("%Y%m%d")
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                            start_date=start, end_date=end, adjust="qfq")
    df = df.rename(columns={
        "日期": "date", "开盘": "open", "收盘": "close",
        "最高": "high", "最低": "low", "成交量": "volume",
        "成交额": "amount",
    })
    keep = ["date", "open", "high", "low", "close", "volume", "amount"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].tail(days).reset_index(drop=True)


def _fetch_kline_baidu(symbol: str, days: int) -> pd.DataFrame:
    """百度股市通日K兜底，直连 HTTP，字段自带成交量/成交额。"""
    url = "https://finance.pae.baidu.com/selfselect/getstockquotation"
    params = {
        "all": "1",
        "isIndex": "false",
        "isBk": "false",
        "isBlock": "false",
        "isFutures": "false",
        "isStock": "true",
        "newFormat": "1",
        "group": "quotation_kline_ab",
        "finClientType": "pc",
        "code": symbol,
        "start_time": "",
        "ktype": "1",
    }
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    r = requests.get(url, params=params, headers=headers, timeout=15)
    payload = r.json()
    if str(payload.get("ResultCode", -1)) != "0":
        return pd.DataFrame()
    md = (payload.get("Result") or {}).get("newMarketData") or {}
    keys = md.get("keys") or []
    market_data = md.get("marketData") or ""
    if not keys or not market_data:
        return pd.DataFrame()

    rows = []
    for line in market_data.split(";"):
        if not line:
            continue
        parts = line.split(",")
        row = dict(zip(keys, parts))
        try:
            rows.append({
                "date": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "amount": float(row["amount"]),
            })
        except (KeyError, TypeError, ValueError):
            continue

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).tail(days).reset_index(drop=True)


def _fetch_kline_cache(symbol: str, days: int) -> pd.DataFrame:
    """从历史训练 SQLite K 线缓存兜底，避免实时日K源短暂失败导致无法打分。"""
    if not CACHE_DB.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(CACHE_DB))
    try:
        df = pd.read_sql_query(
            """
            SELECT date, open, high, low, close, volume, amount
            FROM kline_cache
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            conn,
            params=(str(symbol).zfill(6), int(days)),
        )
    finally:
        conn.close()
    if df.empty:
        return df
    df = df.sort_values("date").reset_index(drop=True)
    df.attrs["source"] = "kline_cache"
    return df


# ---------------------------------------------------------------------------
# 4. 尾盘分钟数据（14:30-15:00）
# ---------------------------------------------------------------------------

def get_tail_minutes(symbol: str) -> pd.DataFrame:
    """获取当日尾盘 14:30-15:00 分钟K。

    返回列：time, open, high, low, close, volume, amount
    """
    if _HAS_MOOTDX:
        try:
            df = _fetch_tail_minutes_mootdx(symbol)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[data_loader] mootdx 尾盘分钟失败 {symbol}: {e}")

    if _HAS_AKSHARE:
        try:
            df = _fetch_tail_minutes_akshare(symbol)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[data_loader] akshare 尾盘分钟失败 {symbol}: {e}")

    try:
        df = _fetch_tail_minutes_daily_proxy(symbol)
        if not df.empty:
            return df
    except Exception as e:
        print(f"[data_loader] 日K代理尾盘失败 {symbol}: {e}")

    raise RuntimeError(f"无法获取 {symbol} 的尾盘分钟数据")


def _fetch_tail_minutes_mootdx(symbol: str) -> pd.DataFrame:
    client = tdx_client()
    market = 1 if symbol.startswith("6") else 0
    df = client.bars(symbol=symbol, frequency=8, offset=240)  # 1分钟，取当日全量
    if isinstance(df, pd.DataFrame):
        df = df.copy()
        # 筛选 14:30-15:00
        if "datetime" in df.columns:
            df["time"] = pd.to_datetime(df["datetime"])
        elif "date" in df.columns:
            df["time"] = pd.to_datetime(df["date"])
        else:
            return pd.DataFrame()
        today = dt.datetime.now().date()
        df = df[df["time"].dt.date == today]
        df = df[(df["time"].dt.time >= dt.time(14, 30)) &
                (df["time"].dt.time <= dt.time(15, 0))]
        col_map = {"vol": "volume"}
        df = df.rename(columns=col_map)
        # mootdx 同时返回 vol 与 volume，rename 后去重
        df = df.loc[:, ~df.columns.duplicated()]
        keep = ["time", "open", "high", "low", "close", "volume", "amount"]
        keep = [c for c in keep if c in df.columns]
        return df[keep].reset_index(drop=True)
    return pd.DataFrame()


def _fetch_tail_minutes_akshare(symbol: str) -> pd.DataFrame:
    today = dt.datetime.now().strftime("%Y%m%d")
    df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1",
                                    start_date=today + " 09:30:00",
                                    end_date=today + " 15:00:00")
    df = df.rename(columns={
        "时间": "time", "开盘": "open", "收盘": "close",
        "最高": "high", "最低": "low", "成交量": "volume",
        "成交额": "amount",
    })
    df["time"] = pd.to_datetime(df["time"])
    df = df[(df["time"].dt.time >= dt.time(14, 30)) &
            (df["time"].dt.time <= dt.time(15, 0))]
    keep = ["time", "open", "high", "low", "close", "volume", "amount"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].reset_index(drop=True)


def _fetch_tail_minutes_daily_proxy(symbol: str) -> pd.DataFrame:
    """分钟源不可用时用当日日K构造保守尾盘代理，避免深度打分硬失败。"""
    daily = get_daily_kline(symbol, days=1)
    if daily.empty:
        return pd.DataFrame()
    latest = daily.iloc[-1]
    trade_date = pd.to_datetime(latest.get("date", dt.datetime.now().date()))
    close = float(latest.get("close", 0))
    if close <= 0:
        return pd.DataFrame()
    return pd.DataFrame([
        {
            "time": trade_date.replace(hour=15, minute=0, second=0),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": float(latest.get("volume", 0)) * 0.2,
            "amount": float(latest.get("amount", 0)) * 0.2,
        }
    ])


# ---------------------------------------------------------------------------
# 5. 资金流向
# ---------------------------------------------------------------------------

def get_fund_flow(symbol: str) -> dict:
    """获取个股资金流向（主力净额等）。

    返回 dict：
        main_net: 主力净额（万元）
        super_large_net: 超大单净额
        large_net: 大单净额
        medium_net: 中单净额
        small_net: 小单净额
        main_net_pct: 主力净额占成交额比例
    """
    # 首选东财 push2 直连（akshare 封禁时仍可用）
    if _HAS_REQUESTS:
        try:
            ff = _fetch_fund_flow_eastmoney_direct(symbol)
            if ff:
                return ff
        except Exception as e:
            print(f"[data_loader] 东财直连资金流向失败 {symbol}: {e}")

    if _HAS_AKSHARE:
        try:
            return _fetch_fund_flow_akshare(symbol)
        except Exception as e:
            print(f"[data_loader] akshare 资金流向失败 {symbol}: {e}")

    if _HAS_MOOTDX:
        try:
            return _fetch_fund_flow_mootdx(symbol)
        except Exception as e:
            print(f"[data_loader] mootdx 资金流向失败 {symbol}: {e}")

    raise RuntimeError(f"无法获取 {symbol} 的资金流向")


def _fetch_fund_flow_eastmoney_direct(symbol: str) -> dict:
    """东财 push2 个股资金流向直连接口。

    绕过 akshare 封禁，直接请求 eastmoney push2 API。
    字段：f52 主力净额, f53 小单, f54 中单, f55 大单, f56 超大单, f57 主力净占比
    """
    daily = _fetch_fund_flow_eastmoney_kline(symbol, klt=101, limit=1)
    if daily:
        daily["source"] = "eastmoney_daily"
        return daily
    minute = _fetch_fund_flow_eastmoney_kline(symbol, klt=1, limit=240, aggregate=True)
    if minute:
        minute["source"] = "eastmoney_minute"
        return minute
    return {}


def _fetch_fund_flow_eastmoney_kline(
    symbol: str,
    klt: int,
    limit: int,
    aggregate: bool = False,
) -> dict:
    market = "1" if symbol.startswith("6") else "0"
    secid = f"{market}.{symbol}"
    url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    params = {
        "secid": secid,
        "lmt": int(limit),
        "klt": int(klt),
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
    }
    headers = {
        "User-Agent": UA,
        "Referer": "https://quote.eastmoney.com/",
        "Origin": "https://quote.eastmoney.com",
    }
    r = em_get(url, params=params, headers=headers, timeout=10)
    data = r.json().get("data") or {}
    klines = data.get("klines") or []
    if not klines:
        return {}

    def parse_line(line: str) -> dict:
        fields = str(line).split(",")
        if len(fields) < 6:
            return {}

        def _f(idx):
            try:
                value = fields[idx]
                if value in ("", "-", None):
                    return 0.0
                return float(value)
            except (ValueError, IndexError, TypeError):
                return 0.0

        main_net = _f(1)
        small_net = _f(2)
        medium_net = _f(3)
        large_net = _f(4)
        super_large_net = _f(5)
        main_net_pct = _f(6) / 100 if len(fields) > 6 else 0.0
        return {
            "main_net": main_net,
            "small_net": small_net,
            "medium_net": medium_net,
            "large_net": large_net,
            "super_large_net": super_large_net,
            "main_net_pct": main_net_pct,
        }

    if aggregate:
        totals = {
            "main_net": 0.0,
            "small_net": 0.0,
            "medium_net": 0.0,
            "large_net": 0.0,
            "super_large_net": 0.0,
            "main_net_pct": 0.0,
        }
        for line in klines:
            row = parse_line(line)
            for key in ("main_net", "small_net", "medium_net", "large_net", "super_large_net"):
                totals[key] += row.get(key, 0.0)
        return {key: (value / 1e4 if key != "main_net_pct" else value) for key, value in totals.items()}

    row = parse_line(klines[-1])
    if not row:
        return {}
    return {
        "main_net": row["main_net"] / 1e4,
        "super_large_net": row["super_large_net"] / 1e4,
        "large_net": row["large_net"] / 1e4,
        "medium_net": row["medium_net"] / 1e4,
        "small_net": row["small_net"] / 1e4,
        "main_net_pct": row["main_net_pct"],
    }


def _fetch_fund_flow_akshare(symbol: str) -> dict:
    df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith("6") else "sz")
    if df.empty:
        return {}
    latest = df.iloc[-1]
    return {
        "main_net": float(latest.get("主力净流入-净额", 0)) / 1e4,  # 万元
        "super_large_net": float(latest.get("超大单净流入-净额", 0)) / 1e4,
        "large_net": float(latest.get("大单净流入-净额", 0)) / 1e4,
        "medium_net": float(latest.get("中单净流入-净额", 0)) / 1e4,
        "small_net": float(latest.get("小单净流入-净额", 0)) / 1e4,
        "main_net_pct": float(latest.get("主力净流入-净占比", 0)) / 100,
    }


def _fetch_fund_flow_mootdx(symbol: str) -> dict:
    """mootdx 无直接资金流向接口，降级返回空结构。"""
    return {
        "main_net": 0.0, "super_large_net": 0.0, "large_net": 0.0,
        "medium_net": 0.0, "small_net": 0.0, "main_net_pct": 0.0,
        "_note": "mootdx 无资金流向数据，建议安装 akshare",
    }


# ---------------------------------------------------------------------------
# 5.1 流通市值（东财 push2 直连，绕过 akshare 封禁）
# ---------------------------------------------------------------------------

def get_float_mv(symbol: str) -> float:
    """获取个股流通市值（元）。东财 push2 stock/get，f117 字段。"""
    if not _HAS_REQUESTS:
        return 0.0
    market = '1' if symbol.startswith('6') else '0'
    secid = f"{market}.{symbol}"
    url = "http://push2.eastmoney.com/api/qt/stock/get"
    params = {'secid': secid, 'fields': 'f117'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    }
    try:
        r = em_get(url, params=params, headers=headers, timeout=10)
        data = r.json().get('data', {})
        return float(data.get('f117', 0))
    except Exception as e:
        print(f"[data_loader] 东财流通市值失败 {symbol}: {e}")
        return 0.0


# ---------------------------------------------------------------------------
# 6. 行业/板块涨幅
# ---------------------------------------------------------------------------

def get_sector_performance() -> pd.DataFrame:
    """获取行业板块当日涨跌幅排名。

    返回列：sector, pct_change, leader_code, leader_name, amount
    """
    if _HAS_REQUESTS:
        try:
            df = _fetch_sector_performance_eastmoney_direct()
            if df is not None and not df.empty:
                df.attrs["source"] = "eastmoney_direct"
                return df
        except Exception as e:
            print(f"[data_loader] 东财直连行业板块失败: {e}")

    if _HAS_AKSHARE:
        try:
            df = ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                df = df.rename(columns={
                    "板块名称": "sector", "涨跌幅": "pct_change",
                    "总市值": "amount",
                })
                df = df.sort_values("pct_change", ascending=False).reset_index(drop=True)
                df.attrs["source"] = "akshare_eastmoney"
                return df
        except Exception as e:
            print(f"[data_loader] akshare 行业板块失败: {e}")

    if _HAS_AKSHARE:
        try:
            df = ak.stock_board_industry_name_em()
            return df
        except Exception:
            pass

    return pd.DataFrame()


def _fetch_sector_performance_eastmoney_direct() -> pd.DataFrame:
    """东财 push2 行业板块列表直连。

    接口 clist/get, fs=m:90+t:2 (行业板块),
    字段 f12 代码, f14 板块名, f3 涨跌幅, f20 总市值, f128 领涨股名, f140 领涨股代码
    """
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1, 'pz': 200, 'po': 1, 'np': 1,
        'fltt': 2, 'invt': 2,
        'fs': 'm:90 t:2',
        'fields': 'f12,f14,f3,f20,f128,f140',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/center/boardlist.html',
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    items = r.json().get('data', {}).get('diff', [])
    if not items:
        return pd.DataFrame()
    rows = []
    for it in items:
        rows.append({
            "sector": it.get("f14", ""),
            "pct_change": float(it.get("f3", 0)) / 100,
            "amount": float(it.get("f20", 0)),
            "leader_name": it.get("f128", ""),
            "leader_code": it.get("f140", ""),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("pct_change", ascending=False).reset_index(drop=True)
    return df


def get_stock_sector(symbol: str) -> str:
    """查询个股所属行业板块。优先东财直连，降级 akshare。"""
    if _HAS_REQUESTS:
        try:
            market = '1' if symbol.startswith('6') else '0'
            secid = f"{market}.{symbol}"
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {'secid': secid, 'fields': 'f127'}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/',
            }
            r = em_get(url, params=params, headers=headers, timeout=10)
            sec = r.json().get('data', {}).get('f127', '')
            if sec:
                return str(sec)
        except Exception:
            pass
    if _HAS_AKSHARE:
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            if df is not None and not df.empty:
                row = df[df["item"] == "行业"]
                if not row.empty:
                    return str(row.iloc[0]["value"])
        except Exception:
            pass
    return "未知"


# ---------------------------------------------------------------------------
# 7. 市场指数概览
# ---------------------------------------------------------------------------

def get_index_overview() -> dict:
    """获取上证/深证/创业板当日概览。

    返回：
        sh_pct, sz_pct, cyb_pct,
        limit_up_count, limit_down_count,
        market_bread
    """
    result = {"sh_pct": 0.0, "sz_pct": 0.0, "cyb_pct": 0.0,
              "limit_up_count": 0, "limit_down_count": 0,
              "market_bread": 0.0, "source": "unknown",
              "quote_time": "", "limit_source": "unavailable"}

    # 上证 000001, 深证 399001, 创业板 399006
    idx_codes = {"sh": "sh000001", "sz": "sz399001", "cyb": "sz399006"}
    if _HAS_REQUESTS:
        try:
            url = "https://qt.gtimg.cn/q=" + ",".join(idx_codes.values())
            resp = requests.get(url, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split(";"):
                if "=" not in line:
                    continue
                try:
                    head, body = line.split("=", 1)
                    body = body.strip('"')
                    fields = body.split("~")
                    if len(fields) < 35:
                        continue
                    pct = float(fields[32]) / 100
                    quote_time = fields[30] if len(fields) > 30 else ""
                    if quote_time:
                        result["quote_time"] = quote_time
                    if "000001" in head:
                        result["sh_pct"] = pct
                    elif "399001" in head:
                        result["sz_pct"] = pct
                    elif "399006" in head:
                        result["cyb_pct"] = pct
                except Exception:
                    continue
            result["source"] = "tencent"
        except Exception as e:
            print(f"[data_loader] 指数概览失败: {e}")

    limit_counts = get_limit_pool_counts(dt.datetime.now().strftime("%Y%m%d"))
    result.update(limit_counts)

    return result


def get_limit_pool_counts(date_str: str) -> dict:
    """获取涨停/跌停家数，优先东财专题池 total count。

    date_str: YYYYMMDD
    """
    result = {
        "limit_up_count": None,
        "limit_down_count": None,
        "limit_source": "unavailable",
    }

    if _HAS_REQUESTS:
        headers = {
            "Referer": "https://quote.eastmoney.com/ztb/",
            "User-Agent": UA,
        }
        params = {
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "dpt": "wz.ztzt",
            "Pageindex": 0,
            "pagesize": 1,
            "sort": "fbt:asc",
            "date": date_str,
        }
        try:
            up = em_get("https://push2ex.eastmoney.com/getTopicZTPool",
                        params=params, headers=headers, timeout=10).json()
            down = em_get("https://push2ex.eastmoney.com/getTopicDTPool",
                          params=params, headers=headers, timeout=10).json()
            result["limit_up_count"] = int(up.get("data", {}).get("tc", 0))
            result["limit_down_count"] = int(down.get("data", {}).get("tc", 0))
            result["limit_source"] = "eastmoney"
            return result
        except Exception as e:
            print(f"[data_loader] 东财涨跌停统计失败: {e}")

    if _HAS_AKSHARE:
        try:
            up = ak.stock_zt_pool_em(date=date_str)
            result["limit_up_count"] = len(up) if up is not None else 0
            result["limit_down_count"] = None
            result["limit_source"] = "akshare_partial"
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# 8. 便捷聚合：一次性取齐单只股票全部因子所需数据
# ---------------------------------------------------------------------------

def load_stock_features(symbol: str) -> dict:
    """加载单只股票选股所需的全部数据。

    返回 dict，供 strategy_engine.py 计算因子分。
    任何子项失败返回 None，由上层决定降级。

    优先级：腾讯一次拿齐实时行情+PE/PB+流通市值（不封IP，省HTTP）；
            失败降级 mootdx/新浪/东财。
    """
    features = {"symbol": symbol}

    # 优先用腾讯一次拿齐实时行情+PE/PB+市值（不封IP，省HTTP）
    tencent_data = tencent_quote([symbol])
    tq = tencent_data.get(symbol) if tencent_data else None

    if tq and tq.get("price", 0) > 0:
        features["realtime"] = {
            "price":      float(tq["price"]),
            "open":       float(tq["open"]),
            "high":       float(tq["high"]),
            "low":        float(tq["low"]),
            "pre_close":  float(tq["pre_close"]),
            "volume":     0.0,   # 腾讯不返回成交量，后续由 mootdx/新浪补充
            "amount":     float(tq["amount_wan"]) * 1e4,  # 万元 → 元
            "pct_change": float(tq["change_pct"]),
        }
        features["float_mv"] = float(tq["float_mcap_yi"]) * 1e8  # 亿 → 元
        features["_tencent_extra"] = {
            "pe_ttm":       tq["pe_ttm"],
            "pb":           tq["pb"],
            "mcap_yi":      tq["mcap_yi"],
            "float_mcap_yi":tq["float_mcap_yi"],
            "turnover_pct": tq["turnover_pct"],
            "vol_ratio":    tq["vol_ratio"],
            "limit_up":     tq["limit_up"],
            "limit_down":   tq["limit_down"],
        }
    else:
        # 降级：原有 mootdx/新浪路径
        try:
            rt = get_realtime_quotes([symbol])
            if not rt.empty:
                row = rt.iloc[0]
                features["realtime"] = {
                    "price":      float(row.get("price", 0)),
                    "open":       float(row.get("open", 0)),
                    "high":       float(row.get("high", 0)),
                    "low":        float(row.get("low", 0)),
                    "pre_close":  float(row.get("pre_close", 0)),
                    "volume":     float(row.get("volume", 0)),
                    "amount":     float(row.get("amount", 0)),
                    "pct_change": float(row.get("pct_change", 0)),
                }
        except Exception as e:
            features["realtime"] = None
            features["_errors"] = features.get("_errors", []) + [f"realtime: {e}"]

        # 流通市值（仅当腾讯未提供时才查东财）
        try:
            features["float_mv"] = get_float_mv(symbol)
        except Exception as e:
            features["float_mv"] = 0.0
            features["_errors"] = features.get("_errors", []) + [f"float_mv: {e}"]

    # 日K
    try:
        features["daily_k"] = get_daily_kline(symbol, days=60)
    except Exception as e:
        features["daily_k"] = pd.DataFrame()
        features["_errors"] = features.get("_errors", []) + [f"daily_k: {e}"]

    # 尾盘分钟
    try:
        features["tail_minutes"] = get_tail_minutes(symbol)
    except Exception as e:
        features["tail_minutes"] = pd.DataFrame()
        features["_errors"] = features.get("_errors", []) + [f"tail_minutes: {e}"]

    # 资金流向
    try:
        features["fund_flow"] = get_fund_flow(symbol)
    except Exception as e:
        features["fund_flow"] = {}
        features["_errors"] = features.get("_errors", []) + [f"fund_flow: {e}"]

    # 所属行业
    try:
        features["sector"] = get_stock_sector(symbol)
    except Exception:
        features["sector"] = "未知"

    return features


if __name__ == "__main__":
    # 自检
    print("=== data_loader 自检 ===")
    print(f"mootdx: {_HAS_MOOTDX}, akshare: {_HAS_AKSHARE}, requests: {_HAS_REQUESTS}")
    config = load_config()
    print(f"配置版本: {config['version']}")

    symbols = get_a_share_symbols()
    print(f"主板股票数: {len(symbols)} (source={symbols.attrs.get('source')})")
    print(symbols.head(3))
