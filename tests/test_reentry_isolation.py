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


def test_r1_does_not_reenter_during_consecutive_shock_days():
    q = qqq_path([100.0, 94.0, 89.5, 91.0])
    got = target_exposure(q, "R1").tolist()
    assert got == [1.0, 0.0, 0.0, 1.0]


def test_r2_resets_partial_tranche_on_renewed_shock():
    q = qqq_path([100.0, 94.0, 99.0, 94.0, 90.0, 94.0, 95.0])
    got = target_exposure(q, "R2").tolist()
    # A renewed -4.5% shock resets the low and staged tranche.
    assert got[3:] == [0.0, 0.0, 0.0, 0.5]


def test_r2p_preregistered_tranche_survives_new_low_after_partial_entry():
    # 99 is +5.3% from 94, activating 50%; 94 is a new -5.05% shock.
    # Preregistered R2P retains 50% and resets the full-recovery reference low.
    q = qqq_path([100.0, 94.0, 99.0, 94.0, 98.0, 103.5])
    got = target_exposure(q, "R2P").tolist()
    assert got == [1.0, 0.0, 0.5, 0.5, 0.5, 1.0]


def test_r2_guarded_variant_still_resets_partial_tranche_on_renewed_shock():
    q = qqq_path([100.0, 94.0, 99.0, 94.0, 90.0, 94.0, 95.0])
    got = target_exposure(q, "R2").tolist()
    assert got[3:] == [0.0, 0.0, 0.0, 0.5]
