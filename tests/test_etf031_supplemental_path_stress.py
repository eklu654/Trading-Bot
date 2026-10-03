import numpy as np
import pandas as pd

from research.etf031_supplemental_path_stress import (
    load_tqqq,
    remove_observation_stress,
    severe_bear_recovery_scenarios,
)


def test_individual_observation_stress_preserves_baseline_case():
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    price = pd.Series(np.linspace(100, 120, len(dates)), index=dates)
    result = remove_observation_stress(price)
    baseline = result.loc[result["scenario"] == "baseline"].iloc[0]
    assert baseline["ending_balance_5000"] > 5000
    assert np.isfinite(baseline["cagr"])


def test_load_tqqq_uses_common_etf031_period():
    price = load_tqqq()
    assert price.index.min() == pd.Timestamp("2010-03-11")
    assert price.index.max() == min(
        pd.read_csv("data/research/tqqq_daily.csv", parse_dates=["Date"])["Date"].max(),
        pd.read_csv("data/research/qqq_daily.csv", parse_dates=["Date"])["Date"].max(),
        pd.read_csv("data/research/soxl_daily.csv", parse_dates=["Date"])["Date"].max(),
        pd.read_csv("data/research/spxl_daily.csv", parse_dates=["Date"])["Date"].max(),
    )


def test_severe_bear_recovery_has_requested_drawdowns():
    result = severe_bear_recovery_scenarios()
    assert len(result) == 12
    for expected in (-0.50, -0.70, -0.80, -0.90):
        subset = result[np.isclose(result["shock_drawdown"], expected)]
        assert len(subset) == 3
        assert np.allclose(subset["max_drawdown"], expected, atol=1e-10)
