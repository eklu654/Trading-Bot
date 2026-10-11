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



def test_replacement_rotation_fills_gated_slot_only_at_scheduled_rebalance():
    from research.family_specific_shock_gate import rotating_gate_weights

    idx = pd.bdate_range("2024-01-02", periods=6)
    columns = ["A", "B", "C"]
    base = pd.DataFrame(0.0, index=idx, columns=columns)
    base.loc[:, ["A", "B"]] = 0.5
    scores = pd.DataFrame({"A": [3.0] * 6, "B": [2.0] * 6, "C": [1.0] * 6}, index=idx)
    eligible = pd.DataFrame(True, index=idx, columns=columns)
    gates = pd.DataFrame(False, index=idx, columns=columns)
    gates.loc[idx[1:4], "A"] = True

    got = rotating_gate_weights(base, scores, eligible, gates, top_n=2, cadence=3)
    # Immediate exit on day 1; at day 3 rebalance, B/C replace gated A.
    assert got.loc[idx[1], "A"] == 0.0
    assert got.loc[idx[2], "A"] == 0.0  # recovery before rebalance cannot restore A
    assert got.loc[idx[3], ["A", "B", "C"]].tolist() == [0.0, 0.5, 0.5]
    assert got.loc[idx[4], ["A", "B", "C"]].tolist() == [0.0, 0.5, 0.5]


def test_replacement_rotation_matches_frozen_weights_without_gates():
    from research.family_specific_shock_gate import rotating_gate_weights

    idx = pd.bdate_range("2024-01-02", periods=6)
    columns = ["A", "B", "C"]
    scores = pd.DataFrame({"A": [3.0] * 6, "B": [2.0] * 6, "C": [1.0] * 6}, index=idx)
    eligible = pd.DataFrame(True, index=idx, columns=columns)
    gates = pd.DataFrame(False, index=idx, columns=columns)
    base = pd.DataFrame(0.0, index=idx, columns=columns)
    base.loc[:, ["A", "B"]] = 0.5
    got = rotating_gate_weights(base, scores, eligible, gates, top_n=2, cadence=3)
    assert np.array_equal(got.to_numpy(), base.to_numpy())



def test_replacement_rotation_leaves_unfilled_gated_slot_in_cash():
    from research.family_specific_shock_gate import rotating_gate_weights

    idx = pd.bdate_range("2024-01-02", periods=3)
    columns = ["A", "B", "C"]
    base = pd.DataFrame(0.0, index=idx, columns=columns)
    base.loc[:, ["A", "B"]] = 0.5
    scores = pd.DataFrame({"A": [3.0] * 3, "B": [2.0] * 3, "C": [1.0] * 3}, index=idx)
    eligible = pd.DataFrame({"A": [True] * 3, "B": [True] * 3, "C": [False] * 3}, index=idx)
    gates = pd.DataFrame(False, index=idx, columns=columns)
    gates.loc[:, "A"] = True
    got = rotating_gate_weights(base, scores, eligible, gates, top_n=2, cadence=1)
    assert got["A"].tolist() == [0.0, 0.0, 0.0]
    assert got["B"].tolist() == [0.5, 0.5, 0.5]
    assert got["C"].tolist() == [0.0, 0.0, 0.0]
    assert np.allclose(got.sum(axis=1).to_numpy(), 0.5)
