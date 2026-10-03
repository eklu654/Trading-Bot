import numpy as np
import pandas as pd

from research.etf031_supplemental_path_stress import (
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


def test_load_tqqq_uses_common_etf031_period(monkeypatch):
    dates = pd.date_range("2010-03-01", periods=20, freq="D")
    frames = {
        "TQQQ": pd.Series(np.arange(20, dtype=float) + 100, index=dates),
        "QQQ": pd.Series(np.arange(18, dtype=float) + 100, index=dates[1:19]),
        "SOXL": pd.Series(np.arange(17, dtype=float) + 100, index=dates[2:19]),
        "SPXL": pd.Series(np.arange(16, dtype=float) + 100, index=dates[3:19]),
    }

    def fake_load(symbol):
        return frames[symbol]

    import research.etf031_supplemental_path_stress as stress

    monkeypatch.setattr(stress, "_load", fake_load)
    price = stress.load_tqqq()

    assert price.index.min() == pd.Timestamp("2010-03-04")
    assert price.index.max() == pd.Timestamp("2010-03-19")
    pd.testing.assert_series_equal(
        price, frames["TQQQ"].loc["2010-03-04":"2010-03-19"]
    )


def test_severe_bear_recovery_has_requested_drawdowns():
    result = severe_bear_recovery_scenarios()
    assert len(result) == 12
    for expected in (-0.50, -0.70, -0.80, -0.90):
        subset = result[np.isclose(result["shock_drawdown"], expected)]
        assert len(subset) == 3
        assert np.allclose(subset["max_drawdown"], expected, atol=1e-10)


def test_severe_bear_recovery_is_fixed_horizon_and_path_sensitive():
    result = severe_bear_recovery_scenarios()
    assert result["calendar_years"].max() - result["calendar_years"].min() < 0.1

    dd90 = result[result["shock_drawdown"] == -0.90].set_index("recovery_years")
    dd50 = result[result["shock_drawdown"] == -0.50].set_index("recovery_years")

    # Deeper shocks must not disappear from terminal wealth merely because
    # the scenario is allowed to run longer.
    assert dd90.loc[2, "ending_balance_5000"] < dd50.loc[2, "ending_balance_5000"]

    # With a fixed horizon, a slower recovery leaves less time for baseline
    # growth after the recovery completes.
    assert dd50.loc[5, "ending_balance_5000"] < dd50.loc[2, "ending_balance_5000"]
