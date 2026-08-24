import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from execution_model import evaluate_overnight_trade, normalize_execution_model


def valid_bar(open_price, close_price):
    return {
        "open": open_price,
        "high": max(open_price, close_price) + 0.2,
        "low": min(open_price, close_price) - 0.2,
        "close": close_price,
        "volume": 1000,
        "amount": 10000,
    }


class ExecutionModelTests(unittest.TestCase):
    def test_filled_trade_applies_adverse_slippage_and_costs(self):
        outcome = evaluate_overnight_trade(
            valid_bar(10.0, 10.2),
            valid_bar(10.5, 10.6),
            {
                "entry_slippage_bps": 10,
                "exit_slippage_bps": 10,
                "commission_rate": 0.0003,
                "stamp_duty_rate": 0.0005,
            },
        )

        self.assertEqual(outcome["execution_status"], "filled")
        self.assertEqual(outcome["gross_return"], 0.0294)
        self.assertEqual(outcome["net_return"], 0.0263)
        self.assertEqual(outcome["return"], outcome["net_return"])
        self.assertTrue(outcome["win"])

    def test_invalid_exit_is_skipped_without_a_synthetic_return(self):
        outcome = evaluate_overnight_trade(valid_bar(10.0, 10.2), {"open": 0}, {})

        self.assertEqual(outcome, {
            "execution_status": "skipped",
            "skip_reason": "invalid_t1_row",
        })

    def test_normalization_provides_zero_cost_compatibility_defaults(self):
        self.assertEqual(normalize_execution_model({}), {
            "entry_slippage_bps": 0.0,
            "exit_slippage_bps": 0.0,
            "commission_rate": 0.0,
            "stamp_duty_rate": 0.0,
            "require_valid_ohlcv": True,
            "skip_limit_entry": True,
            "skip_limit_exit": True,
        })


if __name__ == "__main__":
    unittest.main()
