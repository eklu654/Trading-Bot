"""Fast synthetic guardrails for the fixed episode attribution calculations."""
import numpy as np
import pandas as pd
from research.b0_f75_mechanism_repeatability import _max_dd, _equity_path, EPISODES

def test_fixed_episode_set_is_preregistered_and_includes_fast_and_slow_bears():
    names = [x[0] for x in EPISODES]
    assert names == ["dotcom_2000_2002", "gfc_2007_2009", "2011_stress",
                     "2015_2016_stress", "2018_selloff", "covid_2020",
                     "fed_tightening_2022_2024"]

def test_drawdown_uses_running_peak():
    assert np.isclose(_max_dd([100, 120, 90, 110]), -0.25)

def test_zero_exposure_does_not_accrue_market_returns():
    prices = pd.DataFrame({"tqqq_adj_open":[100, 80, 90],
                           "tqqq_adj_close":[100, 90, 100]})
    eq, exposure = _equity_path(prices, np.zeros(3), 25, initial=5000)
    assert np.allclose(eq, [5000, 5000, 5000])
    assert np.allclose(exposure, [0, 0, 0])

def test_full_exposure_path_is_finite():
    prices = pd.DataFrame({"tqqq_adj_open":[100, 101, 99],
                           "tqqq_adj_close":[100, 102, 100]})
    eq, exposure = _equity_path(prices, np.ones(3), 25, initial=5000)
    assert np.isfinite(eq).all()
    assert np.allclose(exposure, [0, 1, 1])
