"""Deterministic unit checks for gradual-decline research mechanics."""
import datetime as dt
import unittest

from research.backtests.gradual_decline_overlay_comparison import run_variant, sma


class GradualDeclineOverlayTests(unittest.TestCase):
    def test_sma_requires_full_window_and_uses_trailing_values(self):
        values = [float(i) for i in range(1, 201)]
        self.assertIsNone(sma(values, 98, 100))
        self.assertAlmostEqual(sma(values, 99, 100), 50.5)
        self.assertAlmostEqual(sma(values, 199, 100), 150.5)

    def test_trend_indicators_can_use_pretrade_warmup_history(self):
        all_dates = [
            (dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat()
            for i in range(260)
        ]
        qqq = {
            day: {"open": 100.0 + i, "close": 100.0 + i}
            for i, day in enumerate(all_dates)
        }
        tqqq = {
            day: {"open": 50.0 + i, "close": 50.0 + i}
            for i, day in enumerate(all_dates[220:], start=220)
        }
        trading_days = all_dates[220:]
        result = run_variant(trading_days, qqq, tqqq, "B0 + QQQ 200-DMA")
        self.assertEqual(result["start"], trading_days[0])
        self.assertEqual(result["position_changes"], 0)
        self.assertGreater(result["final_equity"], 0)
        self.assertIn("estimated_cost_bps_per_transaction", result)


if __name__ == "__main__":
    unittest.main()
