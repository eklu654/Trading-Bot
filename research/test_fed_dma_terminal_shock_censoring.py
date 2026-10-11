"""Synthetic guardrail tests for terminal shock/recovery censoring."""
import unittest

import pandas as pd

from fed_dma_chronological_robustness import (
    build_censored_baseline_signal,
    terminal_unrecovered_shock_start,
)


class TerminalShockCensoringTests(unittest.TestCase):
    def test_unrecovered_terminal_shock_stays_defensive_through_last_session(self):
        prices = pd.Series(
            [100.0, 100.0, 94.0, 92.0, 90.0, 91.0],
            index=pd.date_range("2025-01-01", periods=6, freq="B"),
        )
        shock_i = terminal_unrecovered_shock_start(prices)
        self.assertEqual(shock_i, 2)
        signal = build_censored_baseline_signal(len(prices), [], shock_i)
        self.assertTrue((signal[:2] == 1.0).all())
        self.assertTrue((signal[2:] == 0.0).all())

    def test_completed_recovery_does_not_leave_terminal_episode_armed(self):
        prices = pd.Series(
            [100.0, 100.0, 94.0, 90.0, 95.0, 100.0],
            index=pd.date_range("2025-01-01", periods=6, freq="B"),
        )
        self.assertIsNone(terminal_unrecovered_shock_start(prices))

    def test_terminal_censor_index_is_validated(self):
        with self.assertRaises(ValueError):
            build_censored_baseline_signal(4, [], 4)


if __name__ == "__main__":
    unittest.main()
