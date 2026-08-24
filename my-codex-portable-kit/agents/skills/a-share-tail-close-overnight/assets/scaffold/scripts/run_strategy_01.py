#!/usr/bin/env python3
"""
执行 01 尾盘隔夜纸面交易策略。

数据源：
- 同花顺热点：当日强势股和题材归因。
- 东财 clist：热点接口失败时的备选强势股池。
- 百度股市通 K 线：确认短期均线和日线结构。

输出：
- reports/strategy_01/_data/YYYY-MM-DD_candidates.csv
- reports/strategy_01/_data/YYYY-MM-DD_report.md
"""

from __future__ import annotations

import csv
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "strategy_01"
DATA_DIR = OUT_DIR / "_data"
CACHE_DIR = ROOT / "data" / "cache"
KLINE_CACHE_DIR = CACHE_DIR / "kline"
KLINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
KLINE_CACHE: dict[str, list[dict[str, Any]]] = {}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def request_json(url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: int = 15) -> dict[str, Any]:
    response = SESSION.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def to_float(value: Any) -> float:
    if value in (None, "", "-", "--"):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_amount(value: Any, source: str = "") -> float:
    """统一成交额为元。同花顺热点 chengjiaoe 口径为万元。"""
    amount = to_float(value)
    if source == "同花顺热点":
        return amount * 10_000
    return amount


def is_main_board_code(code: str) -> bool:
    """仅保留 A 股主板：沪市主板和深市主板。"""
    code = str(code).zfill(6)
    return code.startswith(("600", "601", "603", "605", "000", "001", "002", "003"))


def ths_hot_reason(trade_date: str | None = None) -> list[dict[str, Any]]:
    if trade_date is None:
        trade_date = date.today().isoformat()
    url = f"http://zx.10jqka.com.cn/event/api/getharden/date/{trade_date}/orderby/date/orderway/desc/charset/GBK/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0 Safari/537.36"}
    data = request_json(url, headers=headers, timeout=10)
    if data.get("errocode", 0) != 0:
        return []
    rows = []
    for item in data.get("data") or []:
        code = str(item.get("code", "")).zfill(6)
        if not is_main_board_code(code):
            continue
        name = str(item.get("name", ""))
        if "ST" in name.upper() or name.startswith("*"):
            continue
        rows.append({
            "code": code,
            "name": name,
            "price": to_float(item.get("close")),
            "change_pct": to_float(item.get("zhangfu")),
            "amount": normalize_amount(item.get("chengjiaoe"), "同花顺热点"),
            "turnover_pct": to_float(item.get("huanshou")),
            "reason": str(item.get("reason", "")),
            "source": "同花顺热点",
        })
    return rows


def eastmoney_strong_pool(limit: int = 160) -> list[dict[str, Any]]:
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": str(limit),
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f2,f3,f6,f7,f8,f12,f14,f15,f16,f17,f18",
    }
    data = request_json(url, params)
    rows = []
    for item in data.get("data", {}).get("diff", []) or []:
        code = str(item.get("f12", "")).zfill(6)
        name = str(item.get("f14", ""))
        if not is_main_board_code(code):
            continue
        if "ST" in name.upper() or name.startswith("*"):
            continue
        rows.append({
            "code": code,
            "name": name,
            "price": to_float(item.get("f2")),
            "change_pct": to_float(item.get("f3")),
            "amount": to_float(item.get("f6")),
            "turnover_pct": to_float(item.get("f8")),
            "amplitude_pct": to_float(item.get("f7")),
            "high": to_float(item.get("f15")),
            "low": to_float(item.get("f16")),
            "open": to_float(item.get("f17")),
            "last_close": to_float(item.get("f18")),
            "reason": "",
            "source": "东财涨幅榜",
        })
    return rows


def baidu_kline_with_ma(code: str) -> list[dict[str, Any]]:
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
        "code": code,
        "start_time": "",
        "ktype": "1",
    }
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    data = request_json(url, params, headers=headers)
    if str(data.get("ResultCode", -1)) != "0":
        return []
    market_data = data.get("Result", {}).get("newMarketData", {})
    keys = market_data.get("keys", []) or []
    raw_rows = [r for r in str(market_data.get("marketData", "")).split(";") if r]
    rows = []
    for raw in raw_rows:
        values = raw.split(",")
        item = dict(zip(keys, values))
        rows.append({
            "date": item.get("time", ""),
            "open": to_float(item.get("open")),
            "close": to_float(item.get("close")),
            "high": to_float(item.get("high")),
            "low": to_float(item.get("low")),
            "amount": to_float(item.get("amount")),
            "ma5": to_float(item.get("ma5avgprice")),
            "ma10": to_float(item.get("ma10avgprice")),
            "ma20": to_float(item.get("ma20avgprice")),
        })
    return rows


def eastmoney_daily_kline(code: str, end: str = "20500101", limit: int = 120) -> list[dict[str, Any]]:
    """东财日 K 线兜底数据源，返回字段与 baidu_kline_with_ma 尽量对齐。"""
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "beg": "20200101",
        "end": end,
        "lmt": str(limit),
    }
    response = SESSION.get(url, params=params, headers={"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"}, timeout=15)
    response.raise_for_status()
    data = response.json()
    rows = []
    closes: list[float] = []
    for raw in data.get("data", {}).get("klines", []) or []:
        parts = raw.split(",")
        if len(parts) < 7:
            continue
        close = to_float(parts[2])
        closes.append(close)
        rows.append({
            "date": parts[0],
            "open": to_float(parts[1]),
            "close": close,
            "high": to_float(parts[3]),
            "low": to_float(parts[4]),
            "amount": to_float(parts[6]),
            "ma5": sum(closes[-5:]) / min(5, len(closes)),
            "ma10": sum(closes[-10:]) / min(10, len(closes)),
            "ma20": sum(closes[-20:]) / min(20, len(closes)),
        })
    return rows


def daily_kline(code: str) -> list[dict[str, Any]]:
    rows = baidu_kline_with_ma(code)
    return rows if rows else eastmoney_daily_kline(code)


def kline_for_date(code: str, trade_date: str) -> list[dict[str, Any]]:
    if code not in KLINE_CACHE:
        path = KLINE_CACHE_DIR / f"{code}.json"
        if path.exists():
            KLINE_CACHE[code] = json.loads(path.read_text(encoding="utf-8"))
        else:
            KLINE_CACHE[code] = []
    cached = KLINE_CACHE[code]
    if any(row.get("date") == trade_date for row in cached):
        return cached
    rows = daily_kline(code)
    if rows:
        KLINE_CACHE[code] = rows
        (KLINE_CACHE_DIR / f"{code}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return KLINE_CACHE[code]


def tencent_quote(codes: list[str]) -> dict[str, dict[str, Any]]:
    if not codes:
        return {}
    prefixed = []
    for code in codes:
        if code.startswith(("6", "9")):
            prefixed.append(f"sh{code}")
        elif code.startswith("8"):
            prefixed.append(f"bj{code}")
        else:
            prefixed.append(f"sz{code}")
    response = SESSION.get("https://qt.gtimg.cn/q=" + ",".join(prefixed), timeout=10)
    response.raise_for_status()
    data = response.content.decode("gbk", errors="ignore")
    result = {}
    for line in data.strip().split(";"):
        if not line.strip() or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 49:
            continue
        code = key[2:]
        result[code] = {
            "name": vals[1],
            "price": to_float(vals[3]),
            "change_pct": to_float(vals[32]),
            "high": to_float(vals[33]),
            "low": to_float(vals[34]),
            "open": to_float(vals[5]),
            "amount": to_float(vals[37]) * 10_000,
            "turnover_pct": to_float(vals[38]),
            "amplitude_pct": to_float(vals[43]),
        }
    return result


@dataclass
class Candidate:
    code: str
    name: str
    score: float
    price: float
    change_pct: float
    close_position_pct: float
    ma5: float
    ma10: float
    ma20: float
    amount_yi: float
    buy_price: float
    stop_price: float
    next_day_plan: str
    reasons: list[str]
    risks: list[str]
    branch: str = "01A"
    buyable_score: float = 0


MAX_DAILY_CANDIDATES = 3
PAPER_TRADE_FIELDS = ["交易日", "代码", "名称", "分支", "评分", "尾盘买入价", "买入时间点", "风险", "来源"]


def risk_penalty(candidate: Candidate) -> float:
    penalty = 0.0
    for risk in candidate.risks:
        if risk == "短期乖离偏大":
            penalty += 8
        elif risk == "放量偏大，需防冲高回落":
            penalty += 6
        elif risk == "换手偏高":
            penalty += 6
        elif risk == "日内振幅偏高":
            penalty += 6
        elif risk == "未接近强封，属于可成交弱封观察票":
            penalty += 15
        elif risk == "量能确认不足":
            penalty += 4
        elif risk == "短线均线支撑不足":
            penalty += 8
        else:
            penalty += 3
    if candidate.amount_yi > 100:
        penalty += 8
    elif candidate.amount_yi > 50:
        penalty += 4
    return penalty


def calculate_buyable_score(candidate: Candidate) -> float:
    return max(0, round(candidate.score - risk_penalty(candidate), 1))


def candidate_sort_key(candidate: Candidate) -> tuple[float, float, float, float]:
    if not candidate.buyable_score:
        candidate.buyable_score = calculate_buyable_score(candidate)
    amount_fit = -abs(candidate.amount_yi - 20)
    return (candidate.buyable_score, candidate.score, candidate.close_position_pct, amount_fit)


def evaluate_candidate(stock: dict[str, Any], kline: list[dict[str, Any]], market_score: float, sector_score: float, branch: str = "01A") -> Candidate | None:
    recent = [r for r in kline[-20:] if r["close"] > 0]
    if len(recent) < 18:
        return None

    quote_price = to_float(stock.get("price"))
    close = quote_price or recent[-1]["close"]
    change_pct = to_float(stock.get("change_pct"))
    high = to_float(stock.get("high")) or recent[-1]["high"]
    low = to_float(stock.get("low")) or recent[-1]["low"]
    open_price = to_float(stock.get("open")) or recent[-1]["open"]
    amount = to_float(stock.get("amount")) or recent[-1]["amount"]
    turnover_pct = to_float(stock.get("turnover_pct"))
    amplitude_pct = to_float(stock.get("amplitude_pct")) or ((high / low - 1) * 100 if low else 0)
    ma5 = recent[-1]["ma5"]
    ma10 = recent[-1]["ma10"]
    ma20 = recent[-1]["ma20"]
    avg_amount = statistics.mean([r["amount"] for r in recent if r["amount"] > 0] or [amount])

    if branch == "01B":
        if change_pct < 7 or change_pct > 10.2:
            return None
    elif change_pct < 2 or change_pct > 7:
        return None
    if amount < 100_000_000:
        return None
    if high <= low:
        return None

    close_position_pct = (close - low) / (high - low) * 100
    if close_position_pct < 65:
        return None
    if branch == "01B" and close_position_pct < 95:
        return None

    trend_score = 0
    risks: list[str] = []
    if ma5 and ma10 and ma20 and close > ma5 > ma10:
        trend_score += 14
    elif ma5 and close > ma5:
        trend_score += 9
    else:
        risks.append("短线均线支撑不足")
    if ma20 and close > ma20:
        trend_score += 6
    if ma5 and close / ma5 - 1 > 0.06:
        trend_score -= 6
        risks.append("短期乖离偏大")

    tail_score = min(20, max(0, (close_position_pct - 55) / 45 * 20))
    if close > open_price:
        tail_score += 3
    tail_score = min(20, tail_score)

    volume_score = 0
    volume_ratio = amount / avg_amount if avg_amount else 1
    if 1.0 <= volume_ratio <= 2.8:
        volume_score += 12
    elif volume_ratio > 2.8:
        volume_score += 7
        risks.append("放量偏大，需防冲高回落")
    else:
        volume_score += 5
        risks.append("量能确认不足")
    if turnover_pct <= 15:
        volume_score += 8
    else:
        volume_score += 3
        risks.append("换手偏高")

    risk_score = 20
    if amplitude_pct > 12:
        risk_score -= 5
        risks.append("日内振幅偏高")
    if turnover_pct > 20:
        risk_score -= 6
    if close_position_pct > 96 and change_pct > 6.5 and branch != "01B":
        risk_score -= 4
        risks.append("接近涨停高位，隔日兑现压力较大")
    if branch == "01B" and close_position_pct >= 99.5:
        risk_score += 4
        reasons_prefix = "涨停/强封板分支"
    elif branch == "01B":
        risk_score -= 15
        risks.append("未接近强封，属于可成交弱封观察票")
        reasons_prefix = "可成交弱封观察分支"
    else:
        reasons_prefix = "尾盘强势非涨停分支"
    risk_score = max(0, risk_score)

    score = market_score + sector_score + trend_score + tail_score + volume_score + risk_score
    score = min(100, round(score, 1))
    if score < 70:
        return None

    reasons = [
        reasons_prefix,
        f"涨幅 {change_pct:.1f}% 处于策略区间",
        f"收盘/现价位于日内 {close_position_pct:.1f}% 位置",
        f"成交额 {amount / 100_000_000:.2f} 亿",
    ]
    if stock.get("reason"):
        reasons.append(f"题材归因：{stock['reason']}")
    if ma5 and ma10 and close > ma5 > ma10:
        reasons.append("价格站上 MA5/MA10")

    stop_price = min(close * 0.97, low * 0.995)
    plan = "次日若高开冲高优先止盈；若低开且 10 分钟内不能修复，模拟防守卖出。"
    candidate = Candidate(
        code=stock["code"],
        name=stock["name"],
        score=score,
        price=close,
        change_pct=change_pct,
        close_position_pct=close_position_pct,
        ma5=ma5,
        ma10=ma10,
        ma20=ma20,
        amount_yi=amount / 100_000_000,
        buy_price=close,
        stop_price=stop_price,
        next_day_plan=plan,
        reasons=reasons,
        risks=risks,
        branch=branch,
    )
    candidate.buyable_score = calculate_buyable_score(candidate)
    return candidate


def market_score() -> tuple[float, list[str]]:
    quotes = tencent_quote(["000001", "000300", "399006"])
    vals = [q.get("change_pct", 0) for q in quotes.values()]
    if not vals:
        return 12, ["指数数据不可用，按中性处理"]
    avg = statistics.mean(vals)
    score = 10 + max(-6, min(8, avg * 4))
    notes = [f"主要指数平均涨跌幅 {avg:.2f}%"]
    if avg <= -1.5:
        notes.append("弱市场环境，隔夜策略空仓")
    return max(0, min(20, round(score, 1))), notes


def collect_pool(trade_date: str | None = None, use_realtime_quote: bool = True) -> list[dict[str, Any]]:
    pool = ths_hot_reason(trade_date)
    if not pool:
        pool = eastmoney_strong_pool()
    if not use_realtime_quote:
        return pool
    codes = [p["code"] for p in pool]
    quotes = tencent_quote(codes)
    merged = []
    for stock in pool:
        quote = quotes.get(stock["code"], {})
        merged_stock = {**stock, **{k: v for k, v in quote.items() if v not in (None, "", 0)}}
        merged.append(merged_stock)
    return merged


def build_candidates_for_date(trade_date: str | None = None) -> tuple[list[Candidate], int, list[str]]:
    if trade_date is None:
        trade_date = date.today().isoformat()
    use_realtime_quote = trade_date == date.today().isoformat()
    m_score, m_notes = market_score()
    if m_score <= 4:
        return [], 0, m_notes
    pool = collect_pool(trade_date, use_realtime_quote=use_realtime_quote)
    candidates: list[Candidate] = []
    for stock in pool:
        try:
            kline = kline_for_date(stock["code"], trade_date)
            hist = [r for r in kline if r.get("date", "") <= trade_date]
            if len(hist) < 18:
                continue
            day = hist[-1]
            stock_for_eval = {
                **stock,
                "price": day["close"],
                "open": day["open"],
                "high": day["high"],
                "low": day["low"],
                "amount": stock.get("amount") or day["amount"],
            }
            for branch in ("01A", "01B"):
                candidate = evaluate_candidate(stock_for_eval, hist, market_score=m_score, sector_score=14, branch=branch)
                if candidate:
                    candidates.append(candidate)
        except Exception as exc:
            print(f"跳过 {stock.get('code')} {stock.get('name')}: {exc}")
        time.sleep(0.08 + random.random() * 0.08)
    candidates.sort(key=candidate_sort_key, reverse=True)
    return candidates[:MAX_DAILY_CANDIDATES], len(pool), m_notes


def write_outputs(candidates: list[Candidate], pool_size: int, market_notes: list[str], trade_date: str | None = None) -> tuple[Path, Path]:
    if trade_date is None:
        trade_date = date.today().isoformat()
    csv_path = DATA_DIR / f"{trade_date}_candidates.csv"
    md_path = DATA_DIR / f"{trade_date}_report.md"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["排名", "分支", "代码", "名称", "评分", "可买入评分", "模拟买入价", "涨幅%", "日内位置%", "成交额(亿)", "MA5", "MA10", "MA20", "止损价", "理由", "风险"])
        for i, c in enumerate(candidates, 1):
            writer.writerow([i, c.branch, c.code, c.name, c.score, c.buyable_score, f"{c.buy_price:.2f}", f"{c.change_pct:.2f}", f"{c.close_position_pct:.2f}", f"{c.amount_yi:.2f}", f"{c.ma5:.2f}", f"{c.ma10:.2f}", f"{c.ma20:.2f}", f"{c.stop_price:.2f}", "；".join(c.reasons), "；".join(c.risks)])

    lines = [
        f"# 第一策略执行报告：{trade_date}",
        "",
        "## 策略规则",
        "",
        "- 范围：只筛 A 股主板。",
        "- 买入时间：尾盘 14:45 到 14:55 附近。",
        "- 每天最多选择 1 只，固定模拟资金 10000 元。",
        "- 01A：尾盘强势非涨停，涨幅 2%-7%。",
        "- 01B：主板涨停/强封板，涨幅 7%-10.2%。",
        "- 今日入选最多 3 只，并按可买入评分排序。",
        "- 最低评分：70 分。",
        "- 本报告只用于纸面交易观察，不构成投资建议。",
        "",
        "## 市场环境",
        "",
        *[f"- {note}" for note in market_notes],
        "",
        "## 执行概况",
        "",
        f"- 初始候选池：{pool_size} 只主板强势股。",
        f"- 入选候选：{len(candidates)} 只。",
        "",
    ]
    if candidates:
        best = candidates[0]
        lines.extend([
            "## 今日最优候选",
            "",
            f"- 股票：{best.code} {best.name}",
            f"- 分支：{best.branch}",
            f"- 评分：{best.score:.1f}",
            f"- 可买入评分：{best.buyable_score:.1f}",
            f"- 模拟买入价：{best.buy_price:.2f}",
            f"- 止损价：{best.stop_price:.2f}",
            f"- 涨幅：{best.change_pct:.2f}%",
            f"- 日内位置：{best.close_position_pct:.1f}%",
            f"- 次日计划：{best.next_day_plan}",
            f"- 理由：{'；'.join(best.reasons)}",
            f"- 风险：{'；'.join(best.risks) if best.risks else '暂无明显规则内风险'}",
        ])
    else:
        lines.extend(["## 今日结论", "", "无合格主板候选，按策略空仓。"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def record_default_top1_paper_trade(trade_date: str, candidates: list[Candidate], report_dir: Path = DATA_DIR) -> Path:
    """记录当天默认纸面交易：候选池按可买入评分排序后的 Top1。"""
    ledger_path = report_dir / "paper_trades.csv"
    report_dir.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, str]] = []
    if ledger_path.exists():
        with ledger_path.open(encoding="utf-8-sig") as f:
            existing = list(csv.DictReader(f))
    kept = [
        row for row in existing
        if not (row.get("交易日") == trade_date and row.get("来源") in {"策略Top1", "默认Top1"})
    ]
    if candidates:
        top = candidates[0]
        kept.append({
            "交易日": trade_date,
            "代码": top.code,
            "名称": top.name,
            "分支": top.branch,
            "评分": f"{top.score:g}",
            "尾盘买入价": f"{top.buy_price:.2f}",
            "买入时间点": "收盘价近似",
            "风险": "；".join(top.risks),
            "来源": "策略Top1",
        })
    with ledger_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=PAPER_TRADE_FIELDS)
        writer.writeheader()
        writer.writerows(kept)
    return ledger_path


def main() -> int:
    trade_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    candidates, pool_size, m_notes = build_candidates_for_date(trade_date)
    csv_path, md_path = write_outputs(candidates, pool_size, m_notes, trade_date)
    ledger_path = record_default_top1_paper_trade(trade_date, candidates)
    print(f"交易日: {trade_date}")
    print(f"主板候选池: {pool_size}")
    print(f"入选候选: {len(candidates)}")
    print(f"CSV: {csv_path}")
    print(f"报告: {md_path}")
    print(f"纸面交易台账: {ledger_path}")
    if candidates:
        best = candidates[0]
        print(f"最优候选: {best.code} {best.name} 评分={best.score:.1f} 模拟买入价={best.buy_price:.2f}")
    else:
        print("今日无合格主板候选，空仓。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
