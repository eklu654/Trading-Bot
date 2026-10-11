"""Tests for the fixed SOXL family concentration cap."""
import numpy as np
import pandas as pd

from research.soxl_concentration_cap import soxl_cap_weights


def test_soxl_is_capped_and_released_weight_goes_to_next_eligible_family():
    idx = pd.bdate_range("2024-01-02", periods=4)
    cols = ["SP500", "NASDAQ100", "SEMICONDUCTORS"]
    base = pd.DataFrame(0.0, index=idx, columns=cols)
    base.loc[:, ["SEMICONDUCTORS", "SP500"]] = 0.5
    scores = pd.DataFrame({
        "SEMICONDUCTORS": [3.0] * 4,
        "SP500": [2.0] * 4,
        "NASDAQ100": [1.0] * 4,
    }, index=idx)
    eligible = pd.DataFrame(True, index=idx, columns=cols)
    got = soxl_cap_weights(base, scores, eligible, cap=0.25, top_n=2, cadence=2)
    assert got.loc[idx[0], cols].tolist() == [0.5, 0.25, 0.25]
    assert got.loc[idx[1], cols].tolist() == [0.5, 0.25, 0.25]
    assert got.loc[idx[0], cols].sum() == 1.0
    assert got["SEMICONDUCTORS"].max() <= 0.25


def test_soxl_cap_leaves_unfilled_replacement_weight_in_cash():
    idx = pd.bdate_range("2024-01-02", periods=2)
    cols = ["SP500", "NASDAQ100", "SEMICONDUCTORS"]
    base = pd.DataFrame(0.0, index=idx, columns=cols)
    base.loc[:, ["SEMICONDUCTORS", "SP500"]] = 0.5
    scores = pd.DataFrame({
        "SEMICONDUCTORS": [3.0] * 2,
        "SP500": [2.0] * 2,
        "NASDAQ100": [1.0] * 2,
    }, index=idx)
    eligible = pd.DataFrame({
        "SP500": [True] * 2,
        "NASDAQ100": [False] * 2,
        "SEMICONDUCTORS": [True] * 2,
    }, index=idx)
    got = soxl_cap_weights(base, scores, eligible, cap=0.25, top_n=2, cadence=1)
    assert got.loc[idx[0], "SEMICONDUCTORS"] == 0.25
    assert got.loc[idx[0], "SP500"] == 0.5
    assert got.loc[idx[0], "NASDAQ100"] == 0.0
    assert got.loc[idx[0]].sum() == 0.75


def test_soxl_cap_does_not_change_weights_when_semis_not_selected():
    idx = pd.bdate_range("2024-01-02", periods=3)
    cols = ["SP500", "NASDAQ100", "SEMICONDUCTORS"]
    base = pd.DataFrame(0.0, index=idx, columns=cols)
    base.loc[:, ["SP500", "NASDAQ100"]] = 0.5
    scores = pd.DataFrame({
        "SP500": [3.0] * 3,
        "NASDAQ100": [2.0] * 3,
        "SEMICONDUCTORS": [1.0] * 3,
    }, index=idx)
    eligible = pd.DataFrame(True, index=idx, columns=cols)
    got = soxl_cap_weights(base, scores, eligible, cap=0.25, top_n=2, cadence=2)
    assert np.array_equal(got.to_numpy(), base.to_numpy())
