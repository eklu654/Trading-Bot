"""Invariant tests for the frozen selector attribution audit."""
import pandas as pd
from research.selector_attribution_audit import make_episode_table


def test_drawdown_episode_finds_trough_and_recovery():
    idx = pd.bdate_range("2024-01-01", periods=5)
    equity = pd.Series([100.0, 90.0, 80.0, 90.0, 100.0], index=idx)
    got = make_episode_table(equity)
    assert len(got) == 1
    assert got.iloc[0]["peak_date"] == idx[0]
    assert got.iloc[0]["trough_date"] == idx[2]
    assert got.iloc[0]["recovery_date"] == idx[4]
    assert abs(got.iloc[0]["max_drawdown"] - (-0.2)) < 1e-12


def test_unrecovered_drawdown_is_marked_open():
    idx = pd.bdate_range("2024-01-01", periods=3)
    equity = pd.Series([100.0, 95.0, 90.0], index=idx)
    got = make_episode_table(equity)
    assert len(got) == 1
    assert pd.isna(got.iloc[0]["recovery_date"])
    assert pd.isna(got.iloc[0]["recovery_sessions"])
