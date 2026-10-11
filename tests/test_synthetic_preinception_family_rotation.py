"""Pure-function tests for the synthetic pre-inception stress model."""
import numpy as np
import pandas as pd

from research.synthetic_preinception_family_rotation import (
    first_crossing, selector_weights, synthetic_3x_daily_returns
)


def test_daily_reset_model_includes_funding_and_fee_and_absorbs_zero():
    idx = pd.bdate_range("2000-01-03", periods=4)
    benchmark = pd.Series([0.0, -0.40, 0.10, 0.10], index=idx)
    funding = pd.Series([0.0, 0.0, 0.0, 0.0], index=idx)
    returns, wealth = synthetic_3x_daily_returns(benchmark, funding, annual_fee=0.0)
    assert returns.iloc[1] == -1.0
    assert wealth.iloc[1] == 0.0
    assert returns.iloc[2] == 0.0
    assert wealth.iloc[2] == 0.0


def test_first_crossing_reports_first_date_and_blank_when_never_crossed():
    idx = pd.bdate_range("2000-01-03", periods=3)
    equity = pd.Series([5000.0, 40.0, 3.0], index=idx)
    assert first_crossing(equity, 50.0) == idx[1].date().isoformat()
    assert first_crossing(equity, 1.0) == ""
    assert first_crossing(pd.Series([5.0, 4.0], index=idx[:2]), 1.0) == ""


def test_selector_weights_respect_budget_and_rebalance_cadence():
    idx = pd.bdate_range("2000-01-03", periods=6)
    benchmarks = pd.DataFrame({
        "A": [100, 101, 102, 103, 104, 105],
        "B": [100, 101, 102, 103, 104, 105],
        "C": [100, 99, 98, 97, 96, 95],
    }, index=idx, dtype=float)
    wealth = pd.DataFrame(1.0, index=idx, columns=benchmarks.columns)
    got = selector_weights(benchmarks, wealth, dma=2, top_n=2, cadence=5)
    assert (got.to_numpy() >= 0).all()
    assert (got.sum(axis=1) <= 1.0 + 1e-12).all()
    assert got.iloc[0].sum() == 0.0
    assert got.iloc[1].sum() == 0.0
    assert got.iloc[2].sum() <= 1.0
