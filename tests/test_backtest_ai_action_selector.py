"""Unit tests for the E4 AI action-selector primitives."""

from __future__ import annotations

import numpy as np
import pandas as pd

from research.backtest_ai_action_selector import (
    ACTIONS,
    RIDGE_ALPHA,
    make_model,
    select_action,
)


def test_action_space_contains_cash_and_three_leverage_levels():
    assert list(ACTIONS) == [
        "cash",
        "SPY_1x", "SPY_2x", "SPY_3x",
        "QQQ_1x", "QQQ_2x", "QQQ_3x",
        "SOXX_1x", "SOXX_2x", "SOXX_3x",
    ]


def test_ridge_alpha_is_fixed():
    assert make_model().named_steps["ridge"].alpha == RIDGE_ALPHA


def test_select_action_prefers_positive_best_forecast():
    predictions = pd.Series({"cash": 0.0, "SPY_1x": 0.02, "SPY_2x": 0.01})
    assert select_action(predictions) == "SPY_1x"


def test_select_action_uses_cash_when_best_forecast_is_nonpositive():
    predictions = pd.Series({"cash": 0.0, "SPY_1x": -0.01, "SPY_2x": 0.0})
    assert select_action(predictions) == "cash"


def test_select_action_falls_back_to_cash_without_predictions():
    predictions = pd.Series({"SPY_1x": np.nan, "SPY_2x": np.nan})
    assert select_action(predictions) == "cash"


def test_select_action_ignores_nan_and_infinite_predictions():
    predictions = pd.Series({
        "cash": 0.0,
        "SPY_1x": np.nan,
        "SPY_2x": np.inf,
        "SPY_3x": 0.03,
    })
    assert select_action(predictions) == "SPY_3x"
