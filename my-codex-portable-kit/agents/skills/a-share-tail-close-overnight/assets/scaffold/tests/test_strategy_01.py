import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_strategy_01.py"
spec = importlib.util.spec_from_file_location("run_strategy_01", MODULE_PATH)
strategy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["run_strategy_01"] = strategy
spec.loader.exec_module(strategy)


def test_score_prefers_tail_close_strength():
    stock = {
        "code": "002475",
        "name": "立讯精密",
        "change_pct": 4.2,
        "amount": 1_500_000_000,
        "turnover_pct": 5.0,
        "amplitude_pct": 6.0,
        "price": 42.0,
        "high": 42.5,
        "low": 39.0,
        "open": 40.0,
    }
    kline = [
        {"close": 37 + i * 0.2, "high": 37.5 + i * 0.2, "low": 36.5 + i * 0.2, "open": 36.8 + i * 0.2, "amount": 900_000_000, "ma5": 40, "ma10": 39, "ma20": 38}
        for i in range(20)
    ]
    candidate = strategy.evaluate_candidate(stock, kline, market_score=18, sector_score=16)
    assert candidate is not None
    assert candidate.score >= 70


def test_score_rejects_overheated_or_weak_stock():
    stock = {
        "code": "002475",
        "name": "立讯精密",
        "change_pct": 9.8,
        "amount": 1_500_000_000,
        "turnover_pct": 22.0,
        "amplitude_pct": 15.0,
        "price": 48.0,
        "high": 48.5,
        "low": 39.0,
        "open": 40.0,
    }
    kline = [
        {"close": 40 - i * 0.2, "high": 40.5 - i * 0.2, "low": 39.5 - i * 0.2, "open": 40.2 - i * 0.2, "amount": 300_000_000, "ma5": 35, "ma10": 36, "ma20": 37}
        for i in range(20)
    ]
    candidate = strategy.evaluate_candidate(stock, kline, market_score=8, sector_score=6)
    assert candidate is None


def test_strategy_01_only_allows_main_board_codes():
    assert strategy.is_main_board_code("600519")
    assert strategy.is_main_board_code("002475")
    assert not strategy.is_main_board_code("300750")
    assert not strategy.is_main_board_code("688017")


def test_ths_amount_is_normalized_from_wan_to_yuan():
    assert strategy.normalize_amount(10312, "同花顺热点") == 103_120_000
    assert strategy.normalize_amount(103_120_000, "东财涨幅榜") == 103_120_000


def test_limit_up_branch_accepts_strong_main_board_candidate():
    stock = {
        "code": "002167",
        "name": "东方锆业",
        "change_pct": 9.98,
        "amount": 1_031_200_000,
        "turnover_pct": 8.0,
        "amplitude_pct": 10.0,
        "price": 17.74,
        "high": 17.74,
        "low": 16.3,
        "open": 16.3,
        "reason": "锆材料+产品涨价",
        "source": "同花顺热点",
    }
    kline = [
        {"close": 14 + i * 0.16, "high": 14.2 + i * 0.16, "low": 13.8 + i * 0.16, "open": 13.9 + i * 0.16, "amount": 700_000_000, "ma5": 15.7, "ma10": 14.7, "ma20": 14.1}
        for i in range(20)
    ]
    candidate = strategy.evaluate_candidate(stock, kline, market_score=18, sector_score=16, branch="01B")
    assert candidate is not None
    assert candidate.branch == "01B"


def test_build_candidates_for_date_uses_historical_kline_and_limit_up_branch(monkeypatch, tmp_path):
    stock = {
        "code": "002167",
        "name": "东方锆业",
        "change_pct": 9.98,
        "amount": 1_031_200_000,
        "turnover_pct": 8.0,
        "amplitude_pct": 10.0,
        "reason": "锆材料+产品涨价",
        "source": "同花顺热点",
    }
    kline = [
        {
            "date": f"2026-06-{i + 3:02d}",
            "close": 14 + i * 0.16,
            "high": 14.2 + i * 0.16,
            "low": 13.8 + i * 0.16,
            "open": 13.9 + i * 0.16,
            "amount": 700_000_000,
            "ma5": 15.7,
            "ma10": 14.7,
            "ma20": 14.1,
        }
        for i in range(20)
    ]
    kline[-1].update({"date": "2026-06-22", "close": 17.74, "high": 17.74, "low": 16.3, "open": 16.3})

    monkeypatch.setattr(strategy, "ths_hot_reason", lambda trade_date=None: [stock])
    monkeypatch.setattr(strategy, "daily_kline", lambda code: kline)
    monkeypatch.setattr(strategy, "market_score", lambda: (18, ["测试市场环境"]))
    monkeypatch.setattr(strategy, "KLINE_CACHE_DIR", tmp_path)
    strategy.KLINE_CACHE.clear()

    candidates, pool_size, notes = strategy.build_candidates_for_date("2026-06-22")

    assert pool_size == 1
    assert notes == ["测试市场环境"]
    assert candidates
    assert candidates[0].branch == "01B"
    assert candidates[0].buy_price == 17.74


def test_build_candidates_limits_today_selection_to_three(monkeypatch, tmp_path):
    stocks = [
        {
            "code": f"00210{i}",
            "name": f"测试{i}",
            "change_pct": 9.98,
            "amount": 1_000_000_000 + i,
            "turnover_pct": 8.0,
            "amplitude_pct": 10.0,
            "reason": "测试题材",
            "source": "同花顺热点",
        }
        for i in range(5)
    ]
    kline = [
        {
            "date": f"2026-06-{i + 3:02d}",
            "close": 14 + i * 0.16,
            "high": 14.2 + i * 0.16,
            "low": 13.8 + i * 0.16,
            "open": 13.9 + i * 0.16,
            "amount": 700_000_000,
            "ma5": 15.7,
            "ma10": 14.7,
            "ma20": 14.1,
        }
        for i in range(20)
    ]
    kline[-1].update({"date": "2026-06-22", "close": 17.74, "high": 17.74, "low": 16.3, "open": 16.3})

    monkeypatch.setattr(strategy, "collect_pool", lambda trade_date=None, use_realtime_quote=True: stocks)
    monkeypatch.setattr(strategy, "daily_kline", lambda code: kline)
    monkeypatch.setattr(strategy, "market_score", lambda: (18, ["测试市场环境"]))
    monkeypatch.setattr(strategy, "KLINE_CACHE_DIR", tmp_path)
    strategy.KLINE_CACHE.clear()

    candidates, pool_size, _ = strategy.build_candidates_for_date("2026-06-22")

    assert pool_size == 5
    assert len(candidates) == 3


def test_buyable_score_prefers_lower_risk_candidate_when_strength_ties():
    risky = strategy.Candidate(
        code="603083",
        name="剑桥科技",
        score=100,
        price=262.21,
        change_pct=10.0,
        close_position_pct=100,
        ma5=230.88,
        ma10=208.38,
        ma20=200.72,
        amount_yi=76.28,
        buy_price=262.21,
        stop_price=235.65,
        next_day_plan="",
        reasons=[],
        risks=["短期乖离偏大"],
        branch="01B",
    )
    clean = strategy.Candidate(
        code="002080",
        name="中材科技",
        score=100,
        price=84.48,
        change_pct=10.0,
        close_position_pct=100,
        ma5=81.71,
        ma10=74.02,
        ma20=70.04,
        amount_yi=52.02,
        buy_price=84.48,
        stop_price=76.61,
        next_day_plan="",
        reasons=[],
        risks=[],
        branch="01B",
    )

    ranked = sorted([risky, clean], key=strategy.candidate_sort_key, reverse=True)

    assert clean.buyable_score > risky.buyable_score
    assert ranked[0].code == "002080"


def test_kline_for_date_prefers_cache_when_it_covers_trade_date(monkeypatch, tmp_path):
    cached_rows = [
        {
            "date": "2026-06-22",
            "close": 17.74,
            "high": 17.74,
            "low": 16.3,
            "open": 16.3,
            "amount": 700_000_000,
            "ma5": 15.7,
            "ma10": 14.7,
            "ma20": 14.1,
        }
    ]
    cache_dir = tmp_path / "kline"
    cache_dir.mkdir()
    (cache_dir / "002167.json").write_text(json.dumps(cached_rows), encoding="utf-8")
    monkeypatch.setattr(strategy, "KLINE_CACHE_DIR", cache_dir)
    strategy.KLINE_CACHE.clear()
    monkeypatch.setattr(strategy, "daily_kline", lambda code: (_ for _ in ()).throw(RuntimeError("network should not be used")))

    assert strategy.kline_for_date("002167", "2026-06-22") == cached_rows


def test_build_candidates_blocks_weak_market(monkeypatch):
    monkeypatch.setattr(strategy, "market_score", lambda: (3, ["主要指数平均涨跌幅 -1.81%", "弱市场环境，隔夜策略空仓"]))
    monkeypatch.setattr(strategy, "collect_pool", lambda trade_date=None, use_realtime_quote=True: [{"code": "002167", "name": "东方锆业"}])

    candidates, pool_size, notes = strategy.build_candidates_for_date("2026-06-23")

    assert candidates == []
    assert pool_size == 0
    assert "弱市场环境" in "；".join(notes)


def test_01b_flags_unsealed_limit_candidate_as_risky():
    stock = {
        "code": "002014",
        "name": "永新股份",
        "change_pct": 9.69,
        "amount": 171_000_000,
        "turnover_pct": 3.0,
        "amplitude_pct": 6.0,
        "price": 11.43,
        "high": 11.45,
        "low": 10.80,
        "open": 10.90,
        "reason": "包装材料+新产能投放",
    }
    kline = [
        {"close": 10 + i * 0.05, "high": 10.2 + i * 0.05, "low": 9.8 + i * 0.05, "open": 9.9 + i * 0.05, "amount": 50_000_000, "ma5": 10.7, "ma10": 10.5, "ma20": 10.1}
        for i in range(20)
    ]

    candidate = strategy.evaluate_candidate(stock, kline, market_score=18, sector_score=14, branch="01B")

    assert candidate is not None
    assert "未接近强封" in "；".join(candidate.risks)
    assert candidate.score < 90


def test_record_default_top1_paper_trade_replaces_same_date_default(tmp_path):
    report_dir = tmp_path / "reports" / "strategy_01"
    report_dir.mkdir(parents=True)
    ledger = report_dir / "paper_trades.csv"
    ledger.write_text(
        "\ufeff交易日,代码,名称,分支,评分,尾盘买入价,买入时间点,风险,来源\n"
        "2026-06-24,000001,旧候选,01A,88,10.00,收盘价近似,,策略Top1\n"
        "2026-06-24,000002,用户股,01B,90,12.00,收盘价近似,,用户指定买入\n",
        encoding="utf-8",
    )
    top = strategy.Candidate(
        code="002897",
        name="意华股份",
        score=100,
        price=93.16,
        change_pct=10,
        close_position_pct=100,
        ma5=90,
        ma10=88,
        ma20=84,
        amount_yi=20,
        buy_price=93.16,
        stop_price=90,
        next_day_plan="",
        reasons=[],
        risks=[],
        branch="01B",
        buyable_score=100,
    )

    strategy.record_default_top1_paper_trade("2026-06-24", [top], report_dir=report_dir)

    content = ledger.read_text(encoding="utf-8-sig")
    assert "000001,旧候选" not in content
    assert "002897,意华股份,01B,100,93.16,收盘价近似,,策略Top1" in content
    assert "000002,用户股,01B,90,12.00,收盘价近似,,用户指定买入" in content
