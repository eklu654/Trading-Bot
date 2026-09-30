"""Regression tests for ETF-001 matrix validation selection."""

import pandas as pd

from research.evaluate_etf001_matrix import BASELINE, _same


def test_baseline_match_is_exact():
    row = pd.Series({
        "ma_window": 200,
        "exit_buffer": 0.0,
        "reentry_buffer": 0.0,
        "reentry_sessions": 5,
    })
    assert _same(row, BASELINE)


def test_nonbaseline_does_not_match():
    row = pd.Series({
        "ma_window": 225,
        "exit_buffer": 0.0,
        "reentry_buffer": 0.0,
        "reentry_sessions": 5,
    })
    assert not _same(row, BASELINE)
