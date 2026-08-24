"""Shared paper-trade execution accounting for overnight strategy outcomes."""

from typing import Any, Mapping


DEFAULT_EXECUTION_MODEL = {
    "entry_slippage_bps": 0.0,
    "exit_slippage_bps": 0.0,
    "commission_rate": 0.0,
    "stamp_duty_rate": 0.0,
    "require_valid_ohlcv": True,
    "skip_limit_entry": True,
    "skip_limit_exit": True,
}


def normalize_execution_model(model: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Merge caller configuration over backward-compatible paper defaults."""
    normalized = dict(DEFAULT_EXECUTION_MODEL)
    normalized.update(model or {})
    for key in ("entry_slippage_bps", "exit_slippage_bps", "commission_rate", "stamp_duty_rate"):
        normalized[key] = float(normalized.get(key, 0) or 0)
    return normalized


def _valid_bar(row: Mapping[str, Any] | None, require_ohlcv: bool) -> bool:
    if row is None:
        return False
    try:
        values = {key: float(row.get(key, 0) or 0) for key in ("open", "high", "low", "close")}
        if min(values.values()) <= 0:
            return False
        if values["high"] < max(values["open"], values["close"], values["low"]):
            return False
        if values["low"] > min(values["open"], values["close"], values["high"]):
            return False
        if require_ohlcv:
            return float(row.get("volume", 0) or 0) > 0 and float(row.get("amount", 0) or 0) > 0
        return True
    except (TypeError, ValueError):
        return False


def _skip(reason: str) -> dict[str, Any]:
    return {"execution_status": "skipped", "skip_reason": reason}


def evaluate_overnight_trade(
    t_row: Mapping[str, Any] | None,
    t1_row: Mapping[str, Any] | None,
    model: Mapping[str, Any] | None = None,
    *,
    entry_price: float | None = None,
    entry_source: str = "T_close",
    exit_price: float | None = None,
    exit_source: str = "T1_open",
) -> dict[str, Any]:
    """Evaluate T entry to T+1 exit under adverse slippage and transaction costs."""
    cfg = normalize_execution_model(model)
    if not _valid_bar(t_row, cfg["require_valid_ohlcv"]):
        return _skip("invalid_t_row")
    if not _valid_bar(t1_row, cfg["require_valid_ohlcv"]):
        return _skip("invalid_t1_row")
    if cfg["skip_limit_entry"] and bool(t_row.get("entry_unfillable")):
        return _skip("entry_unfillable_limit")
    if cfg["skip_limit_exit"] and bool(t1_row.get("exit_unfillable")):
        return _skip("exit_unfillable_limit")

    raw_entry = float(entry_price if entry_price is not None else t_row["close"])
    raw_exit = float(exit_price if exit_price is not None else t1_row["open"])
    if raw_entry <= 0:
        return _skip("invalid_entry_price")
    if raw_exit <= 0:
        return _skip("invalid_exit_price")

    adjusted_entry = raw_entry * (1 + cfg["entry_slippage_bps"] / 10000)
    adjusted_exit = raw_exit * (1 - cfg["exit_slippage_bps"] / 10000)
    gross_return = raw_exit / raw_entry - 1
    slippage_adjusted_return = adjusted_exit / adjusted_entry - 1
    total_cost_rate = (2 * cfg["commission_rate"]) + cfg["stamp_duty_rate"]
    net_return = slippage_adjusted_return - total_cost_rate
    return {
        "execution_status": "filled",
        "skip_reason": "",
        "raw_entry_price": round(raw_entry, 4),
        "raw_exit_price": round(raw_exit, 4),
        "buy_price": round(raw_entry, 3),
        "sell_price": round(raw_exit, 3),
        "adjusted_entry_price": round(adjusted_entry, 4),
        "adjusted_exit_price": round(adjusted_exit, 4),
        "buy_price_source": entry_source,
        "sell_price_source": exit_source,
        "gross_return": round(gross_return, 4),
        "net_return": round(net_return, 4),
        "return": round(net_return, 4),
        "win": net_return > 0,
        "entry_slippage_bps": cfg["entry_slippage_bps"],
        "exit_slippage_bps": cfg["exit_slippage_bps"],
        "commission_rate": cfg["commission_rate"],
        "stamp_duty_rate": cfg["stamp_duty_rate"],
    }
