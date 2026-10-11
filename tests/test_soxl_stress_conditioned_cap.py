"""Tests for SOXX drawdown stress hysteresis and conditional SOXL cap."""
import numpy as np
import pandas as pd

from research.soxl_stress_conditioned_cap import stress_conditioned_weights


def _panels(idx):
    cols = ["SP500", "NASDAQ100", "SEMICONDUCTORS"]
    base = pd.DataFrame(0.0, index=idx, columns=cols)
    base.loc[:, ["SP500", "SEMICONDUCTORS"]] = 0.5
    scores = pd.DataFrame({
        "SP500": [2.0] * len(idx),
        "NASDAQ100": [1.0] * len(idx),
        "SEMICONDUCTORS": [3.0] * len(idx),
    }, index=idx)
    eligible = pd.DataFrame(True, index=idx, columns=cols)
    return base, scores, eligible


def test_conditional_cap_activates_at_drawdown_and_releases_with_hysteresis():
    idx = pd.bdate_range("2024-01-02", periods=65)
    base, scores, eligible = _panels(idx)
    closes = pd.Series([100.0] * 60 + [84.0, 85.0, 90.5, 91.0, 92.0], index=idx)
    got, active, dd = stress_conditioned_weights(
        base, scores, eligible, closes, cap=0.25, top_n=2, cadence=1,
        lookback=60, stress_enter=-0.15, stress_exit=-0.10
    )
    assert active.loc[idx[60]] is False or not bool(active.loc[idx[60]])
    assert bool(active.loc[idx[61]]) is True
    assert bool(active.loc[idx[62]]) is True
    assert bool(active.loc[idx[63]]) is False
    assert got.loc[idx[61], ["SP500", "NASDAQ100", "SEMICONDUCTORS"]].tolist() == [0.5, 0.25, 0.25]
    assert got.loc[idx[62], "SEMICONDUCTORS"] == 0.25
    assert np.array_equal(got.loc[~active].to_numpy(), base.loc[~active].to_numpy())


def test_conditional_cap_is_identical_to_base_without_stress():
    idx = pd.bdate_range("2024-01-02", periods=80)
    base, scores, eligible = _panels(idx)
    closes = pd.Series([100.0] * len(idx), index=idx)
    got, active, _ = stress_conditioned_weights(
        base, scores, eligible, closes, cap=0.25, top_n=2, cadence=5,
        lookback=60, stress_enter=-0.15, stress_exit=-0.10
    )
    assert not active.any()
    assert np.array_equal(got.to_numpy(), base.to_numpy())
