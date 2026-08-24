import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class DataLoaderMarketOverviewTests(unittest.TestCase):
    def test_symbols_fall_back_to_kline_cache_when_akshare_and_mootdx_fail(self):
        data_loader = importlib.import_module("data_loader")
        with tempfile.TemporaryDirectory() as tmp:
            cache_db = Path(tmp) / "backtest_kline.db"
            import sqlite3
            conn = sqlite3.connect(cache_db)
            conn.execute("""
                CREATE TABLE cache_meta (
                    symbol TEXT PRIMARY KEY,
                    first_date TEXT,
                    last_date TEXT,
                    total_bars INTEGER,
                    cached_at TEXT,
                    cache_version TEXT
                )
            """)
            conn.executemany(
                "INSERT INTO cache_meta(symbol,total_bars) VALUES (?,?)",
                [("600001", 130), ("000001", 130), ("300001", 130)],
            )
            conn.commit()
            conn.close()

            old_cache_db = data_loader.CACHE_DB
            old_has_akshare = data_loader._HAS_AKSHARE
            old_has_mootdx = data_loader._HAS_MOOTDX
            old_quote = data_loader.tencent_quote
            try:
                data_loader.CACHE_DB = cache_db
                data_loader._HAS_AKSHARE = False
                data_loader._HAS_MOOTDX = False
                data_loader.tencent_quote = lambda codes: {
                    "600001": {"name": "缓存沪股"},
                    "000001": {"name": "缓存深股"},
                    "300001": {"name": "创业板"},
                }

                df = data_loader.get_a_share_symbols()
            finally:
                data_loader.CACHE_DB = old_cache_db
                data_loader._HAS_AKSHARE = old_has_akshare
                data_loader._HAS_MOOTDX = old_has_mootdx
                data_loader.tencent_quote = old_quote

        self.assertEqual(df.attrs["source"], "kline_cache_tencent")
        self.assertEqual(set(df["symbol"]), {"600001", "000001"})
        self.assertEqual(set(df["name"]), {"缓存沪股", "缓存深股"})

    def test_market_snapshot_uses_cached_symbols_for_tencent_when_symbol_sources_fail(self):
        data_loader = importlib.import_module("data_loader")
        with tempfile.TemporaryDirectory() as tmp:
            cache_db = Path(tmp) / "backtest_kline.db"
            import sqlite3
            conn = sqlite3.connect(cache_db)
            conn.execute("CREATE TABLE cache_meta (symbol TEXT PRIMARY KEY, total_bars INTEGER)")
            conn.executemany(
                "INSERT INTO cache_meta(symbol,total_bars) VALUES (?,?)",
                [("600001", 130), ("000001", 130)],
            )
            conn.commit()
            conn.close()

            old_cache_db = data_loader.CACHE_DB
            old_has_akshare = data_loader._HAS_AKSHARE
            old_has_mootdx = data_loader._HAS_MOOTDX
            old_quote = data_loader.tencent_quote
            try:
                data_loader.CACHE_DB = cache_db
                data_loader._HAS_AKSHARE = False
                data_loader._HAS_MOOTDX = False
                data_loader.tencent_quote = lambda codes: {
                    code: {
                        "name": f"名称{code}",
                        "price": 10.0,
                        "change_pct": 0.01,
                        "amount_wan": 8000,
                        "turnover_pct": 2.0,
                        "high": 10.2,
                        "low": 9.8,
                        "open": 9.9,
                        "pre_close": 9.9,
                        "float_mcap_yi": 20,
                    }
                    for code in codes
                }

                df = data_loader.get_market_snapshot()
            finally:
                data_loader.CACHE_DB = old_cache_db
                data_loader._HAS_AKSHARE = old_has_akshare
                data_loader._HAS_MOOTDX = old_has_mootdx
                data_loader.tencent_quote = old_quote

        self.assertEqual(df.attrs["source"], "tencent")
        self.assertEqual(set(df["symbol"]), {"600001", "000001"})
        self.assertTrue((df["amount"] >= 80000000).all())

    def test_limit_pool_count_uses_eastmoney_total_count(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def __init__(self, total):
                self.total = total

            def json(self):
                return {"data": {"tc": self.total}}

        calls = []

        def fake_em_get(url, params=None, headers=None, timeout=10, **kwargs):
            calls.append(url)
            if "getTopicZTPool" in url:
                return Resp(39)
            if "getTopicDTPool" in url:
                return Resp(18)
            return Resp(0)

        old_em_get = getattr(data_loader, "em_get", None)
        old_has_requests = data_loader._HAS_REQUESTS
        try:
            data_loader._HAS_REQUESTS = True
            data_loader.em_get = fake_em_get
            counts = data_loader.get_limit_pool_counts("20260626")
        finally:
            data_loader._HAS_REQUESTS = old_has_requests
            if old_em_get is not None:
                data_loader.em_get = old_em_get

        self.assertEqual(counts["limit_up_count"], 39)
        self.assertEqual(counts["limit_down_count"], 18)
        self.assertEqual(counts["limit_source"], "eastmoney")

    def test_eastmoney_snapshot_skips_rows_with_placeholder_numeric_fields(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def json(self):
                return {
                    "data": {
                        "diff": [
                            {
                                "f12": "600001",
                                "f14": "坏字段",
                                "f2": 10.0,
                                "f3": "-",
                                "f5": "-",
                                "f6": "-",
                                "f8": "-",
                                "f15": "-",
                                "f16": "-",
                                "f17": "-",
                                "f18": "-",
                                "f117": "-",
                            },
                            {
                                "f12": "600002",
                                "f14": "正常股",
                                "f2": 10.0,
                                "f3": 1.5,
                                "f5": 100,
                                "f6": 200000000,
                                "f8": 3.2,
                                "f15": 10.5,
                                "f16": 9.8,
                                "f17": 9.9,
                                "f18": 9.85,
                                "f117": 1000000000,
                            },
                        ]
                    }
                }

        old_em_get = getattr(data_loader, "em_get", None)
        try:
            def fake_em_get(*args, **kwargs):
                params = kwargs.get("params") or (args[1] if len(args) > 1 else {})
                return Resp() if params.get("fs") == "m:1 t:2" else type(
                    "EmptyResp",
                    (),
                    {"json": lambda self: {"data": {"diff": []}}},
                )()

            data_loader.em_get = fake_em_get
            df = data_loader._fetch_market_snapshot_eastmoney()
        finally:
            if old_em_get is not None:
                data_loader.em_get = old_em_get

        self.assertFalse(df.empty)
        self.assertIn("600002", df["symbol"].tolist())
        self.assertNotIn("600001", df["symbol"].tolist())

    def test_eastmoney_snapshot_uses_f21_when_f117_is_placeholder(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def json(self):
                return {
                    "data": {
                        "diff": [
                            {
                                "f12": "600003",
                                "f14": "流通市值兜底",
                                "f2": 12.0,
                                "f3": 2.0,
                                "f5": 1000,
                                "f6": 80000000,
                                "f8": 2.1,
                                "f15": 12.4,
                                "f16": 11.8,
                                "f17": 11.9,
                                "f18": 11.76,
                                "f117": "-",
                                "f21": 1200000000,
                            },
                        ]
                    }
                }

        old_em_get = getattr(data_loader, "em_get", None)
        try:
            def fake_em_get(*args, **kwargs):
                params = kwargs.get("params") or (args[1] if len(args) > 1 else {})
                if params.get("fs") == "m:1 t:2":
                    return Resp()
                return type("EmptyResp", (), {"json": lambda self: {"data": {"diff": []}}})()

            data_loader.em_get = fake_em_get
            df = data_loader._fetch_market_snapshot_eastmoney()
        finally:
            if old_em_get is not None:
                data_loader.em_get = old_em_get

        self.assertEqual(df["symbol"].tolist(), ["600003"])
        self.assertEqual(float(df.iloc[0]["float_mv"]), 1200000000)

    def test_eastmoney_snapshot_treats_null_data_as_empty(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def json(self):
                return {"data": None}

        old_em_get = getattr(data_loader, "em_get", None)
        try:
            data_loader.em_get = lambda *args, **kwargs: Resp()
            df = data_loader._fetch_market_snapshot_eastmoney()
        finally:
            if old_em_get is not None:
                data_loader.em_get = old_em_get

        self.assertTrue(df.empty)


class DataLoaderKlineFallbackTests(unittest.TestCase):
    def test_baidu_kline_parses_market_data_rows(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def json(self):
                return {
                    "ResultCode": 0,
                    "Result": {
                        "newMarketData": {
                            "keys": [
                                "timestamp", "time", "open", "close", "volume",
                                "high", "low", "amount",
                            ],
                            "marketData": (
                                "1782230400,2026-06-24,9.26,8.90,107526621,9.27,8.90,969684288.00;"
                                "1782316800,2026-06-25,8.85,8.85,65829690,8.93,8.82,583249750.00"
                            ),
                        }
                    },
                }

        old_requests_get = data_loader.requests.get
        try:
            data_loader.requests.get = lambda *args, **kwargs: Resp()
            df = data_loader._fetch_kline_baidu("600000", days=1)
        finally:
            data_loader.requests.get = old_requests_get

        self.assertEqual(df["date"].tolist(), ["2026-06-25"])
        self.assertEqual(float(df.iloc[0]["open"]), 8.85)
        self.assertEqual(float(df.iloc[0]["close"]), 8.85)
        self.assertEqual(float(df.iloc[0]["amount"]), 583249750.00)

    def test_tail_minutes_falls_back_to_daily_kline_proxy(self):
        data_loader = importlib.import_module("data_loader")

        daily = pd.DataFrame(
            [
                {
                    "date": "2026-06-26",
                    "open": 8.86,
                    "high": 8.89,
                    "low": 8.70,
                    "close": 8.79,
                    "volume": 41111438,
                    "amount": 360563485,
                }
            ]
        )

        old_has_mootdx = data_loader._HAS_MOOTDX
        old_has_akshare = data_loader._HAS_AKSHARE
        old_get_daily_kline = data_loader.get_daily_kline
        try:
            data_loader._HAS_MOOTDX = False
            data_loader._HAS_AKSHARE = False
            data_loader.get_daily_kline = lambda symbol, days=1: daily
            df = data_loader.get_tail_minutes("600000")
        finally:
            data_loader._HAS_MOOTDX = old_has_mootdx
            data_loader._HAS_AKSHARE = old_has_akshare
            data_loader.get_daily_kline = old_get_daily_kline

        self.assertEqual(len(df), 1)
        self.assertEqual(float(df.iloc[0]["close"]), 8.79)
        self.assertEqual(float(df.iloc[0]["volume"]), 41111438 * 0.2)

    def test_daily_kline_falls_back_to_local_kline_cache(self):
        data_loader = importlib.import_module("data_loader")
        with tempfile.TemporaryDirectory() as tmp:
            cache_db = Path(tmp) / "backtest_kline.db"
            import sqlite3
            conn = sqlite3.connect(cache_db)
            conn.execute("""
                CREATE TABLE kline_cache (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    cached_at TEXT,
                    cache_version TEXT,
                    PRIMARY KEY (symbol, date)
                )
            """)
            conn.executemany(
                "INSERT INTO kline_cache VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    ("600867", "2026-06-24", 10, 10.5, 9.8, 10.2, 1000, 100000, "now", "test"),
                    ("600867", "2026-06-25", 10.2, 10.8, 10.1, 10.6, 1200, 130000, "now", "test"),
                ],
            )
            conn.commit()
            conn.close()

            old_cache_db = data_loader.CACHE_DB
            old_has_mootdx = data_loader._HAS_MOOTDX
            old_has_akshare = data_loader._HAS_AKSHARE
            old_has_requests = data_loader._HAS_REQUESTS
            try:
                data_loader.CACHE_DB = cache_db
                data_loader._HAS_MOOTDX = False
                data_loader._HAS_AKSHARE = False
                data_loader._HAS_REQUESTS = False
                df = data_loader.get_daily_kline("600867", days=1)
            finally:
                data_loader.CACHE_DB = old_cache_db
                data_loader._HAS_MOOTDX = old_has_mootdx
                data_loader._HAS_AKSHARE = old_has_akshare
                data_loader._HAS_REQUESTS = old_has_requests

        self.assertEqual(df["date"].tolist(), ["2026-06-25"])
        self.assertEqual(float(df.iloc[0]["close"]), 10.6)
        self.assertEqual(df.attrs.get("source"), "kline_cache")

    def test_eastmoney_fund_flow_uses_limited_em_get_and_parses_daily_row(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def json(self):
                return {"data": {"klines": ["2026-06-25,1200000,100,200000,300000,700000,3.5"]}}

        calls = []
        old_em_get = getattr(data_loader, "em_get", None)
        try:
            def fake_em_get(url, params=None, headers=None, timeout=10, **kwargs):
                calls.append((url, params))
                return Resp()

            data_loader.em_get = fake_em_get
            ff = data_loader._fetch_fund_flow_eastmoney_direct("600867")
        finally:
            if old_em_get is not None:
                data_loader.em_get = old_em_get

        self.assertTrue(calls)
        self.assertEqual(calls[0][1]["klt"], 101)
        self.assertEqual(ff["main_net"], 120)
        self.assertEqual(ff["super_large_net"], 70)
        self.assertEqual(ff["main_net_pct"], 0.035)
        self.assertEqual(ff["source"], "eastmoney_daily")

    def test_eastmoney_fund_flow_falls_back_to_minute_sum(self):
        data_loader = importlib.import_module("data_loader")

        class Resp:
            def __init__(self, payload):
                self._payload = payload

            def json(self):
                return self._payload

        calls = []
        old_em_get = getattr(data_loader, "em_get", None)
        try:
            def fake_em_get(url, params=None, headers=None, timeout=10, **kwargs):
                calls.append(params)
                if params["klt"] == 101:
                    return Resp({"data": {"klines": []}})
                return Resp({
                    "data": {
                        "klines": [
                            "2026-06-25 09:31,100000,50000,10000,20000,70000,1.1",
                            "2026-06-25 09:32,200000,30000,20000,40000,140000,1.2",
                        ]
                    }
                })

            data_loader.em_get = fake_em_get
            ff = data_loader._fetch_fund_flow_eastmoney_direct("600867")
        finally:
            if old_em_get is not None:
                data_loader.em_get = old_em_get

        self.assertEqual([c["klt"] for c in calls], [101, 1])
        self.assertEqual(ff["main_net"], 30)
        self.assertEqual(ff["large_net"], 6)
        self.assertEqual(ff["super_large_net"], 21)
        self.assertEqual(ff["source"], "eastmoney_minute")


if __name__ == "__main__":
    unittest.main()
