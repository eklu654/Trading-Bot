"""Unit tests for the re-entry state machine; no market data or network required."""
import pandas as pd

from research.reentry_isolation import target_exposure


def qqq_path(prices):
    return pd.DataFrame(
        {"Adj Close": prices},
        index=pd.bdate_range("2024-01-02", periods=len(prices)),
    )


def test_b0_waits_for_full_ten_percent_recovery():
    q = qqq_path([100.0, 94.0, 96.0, 99.0, 103.5])
    got = target_exposure(q, "B0").tolist()
    assert got == [1.0, 0.0, 0.0, 0.0, 1.0]


def test_r1_reenters_at_first_close_after_shock():
    q = qqq_path([100.0, 94.0, 96.0, 99.0, 103.5])
    got = target_exposure(q, "R1").tolist()
    assert got == [1.0, 0.0, 1.0, 1.0, 1.0]


def test_r2_stages_half_exposure_at_five_percent_then_full_at_ten():
    q = qqq_path([100.0, 94.0, 96.0, 99.0, 103.5])
    got = target_exposure(q, "R2").tolist()
    assert got == [1.0, 0.0, 0.0, 0.5, 1.0]


def test_r2_updates_running_low_before_partial_reentry():
    q = qqq_path([100.0, 94.0, 90.0, 94.0, 95.0, 99.1])
    got = target_exposure(q, "R2").tolist()
    # New low resets the +5% and +10% levels; 94 is not +5% from 90,
    # 95 is, so partial exposure starts at that close; 99.1 is > +10%.
    assert got == [1.0, 0.0, 0.0, 0.0, 0.5, 1.0]
