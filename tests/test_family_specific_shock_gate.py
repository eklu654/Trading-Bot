"""Unit tests for family-specific shock gating; no network required."""
import numpy as np
import pandas as pd

from research.family_specific_shock_gate import family_gate_weights


def test_shock_gate_only_exits_the_affected_family_and_reenters_next_session():
    idx = pd.bdate_range("2024-01-02", periods=5)
    base = pd.DataFrame({"A": [0.5] * 5, "B": [0.5] * 5}, index=idx)
    benchmark = pd.DataFrame({
        "A": [100.0, 94.0, 96.0, 104.0, 105.0],
        "B": [100.0, 100.0, 100.0, 100.0, 100.0],
    }, index=idx)
    got, states = family_gate_weights(base, benchmark)
    assert got["A"].tolist() == [0.5, 0.5, 0.0, 0.0, 0.5]
    assert got["B"].tolist() == [0.5] * 5
    assert states["A"].tolist() == [False, False, True, True, False]
    assert got.loc[idx[2], ["A", "B"]].sum() == 0.5  # gated weight stays cash


def test_renewed_shock_resets_only_that_family_recovery_low():
    idx = pd.bdate_range("2024-01-02", periods=7)
    base = pd.DataFrame({"A": [0.5] * 7, "B": [0.5] * 7}, index=idx)
    benchmark = pd.DataFrame({
        "A": [100.0, 94.0, 100.0, 94.0, 98.0, 104.0, 105.0],
        "B": [100.0] * 7,
    }, index=idx)
    got, states = family_gate_weights(base, benchmark)
    assert states["A"].tolist() == [False, False, True, True, True, True, False]
    assert got["B"].tolist() == [0.5] * 7
    assert got["A"].iloc[4] == 0.0
    assert got["A"].iloc[6] == 0.5
