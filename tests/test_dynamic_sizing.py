import numpy as np
import pandas as pd
from research.backtest_dynamic_sizing import choose_allocation

def test_allocation_caps_at_one():
    row = pd.Series({"SPY_rv20": 0.30, "TQQQ_rv20": 0.20})
    assert choose_allocation(row, "TQQQ") == 1.0

def test_higher_selected_vol_reduces_allocation():
    row = pd.Series({"SPY_rv20": 0.20, "TQQQ_rv20": 0.40})
    assert np.isclose(choose_allocation(row, "TQQQ"), 0.5)

def test_missing_volatility_uses_full_allocation_fallback():
    row = pd.Series({"SPY_rv20": np.nan, "TQQQ_rv20": np.nan})
    assert choose_allocation(row, "TQQQ") == 1.0

def test_cash_has_zero_allocation():
    row = pd.Series({"SPY_rv20": 0.20})
    assert choose_allocation(row, None) == 0.0


def test_sqrt_ratio_is_less_aggressive_than_full_ratio():
    row = pd.Series({"SPY_rv20": 0.20, "TQQQ_rv20": 0.80})
    assert np.isclose(choose_allocation(row, "TQQQ", "sqrt_ratio"), 0.5)
    assert choose_allocation(row, "TQQQ", "sqrt_ratio") > choose_allocation(row, "TQQQ", "full_ratio")
