"""Regression tests for ETF-001 trend/hysteresis research logic."""

import pandas as pd

from research.backtest_etf001_matrix import generate_signal


def test_reentry_requires_consecutive_sessions():
    index = pd.date_range("2026-01-02", periods=8, freq="D")
    close = pd.Series([9, 11, 11, 9, 11, 11, 11, 11], index=index, dtype=float)

    signal = generate_signal(close, 3, 0.0, 0.0, 3)

    assert not signal.iloc[:6].any()
    assert signal.iloc[6]
    assert signal.iloc[7]


def test_exit_buffer_prevents_small_dip_from_triggering_exit():
    index = pd.date_range("2026-01-02", periods=7, freq="D")
    close = pd.Series([10, 10, 10, 9.95, 10.1, 10.2, 10.3], index=index, dtype=float)

    no_buffer = generate_signal(close, 3, 0.0, 0.0, 1)
    buffered = generate_signal(close, 3, 0.01, 0.0, 1)

    assert not no_buffer.iloc[3]
    assert buffered.iloc[3]
