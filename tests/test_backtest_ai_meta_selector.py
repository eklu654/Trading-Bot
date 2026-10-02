"""E5 meta-selector unit tests."""

import pandas as pd

from research import backtest_ai_meta_selector as e5


def test_meta_selector_sleeve_set_is_fixed():
    assert e5.SLEEVES == ("E2", "E3_sqrt", "SPY", "cash")


def test_meta_backtest_uses_next_session():
    dates = pd.date_range("2025-01-01", periods=3)
    returns = pd.DataFrame(
        {"E2": [0.0, 0.10, 0.0], "E3_sqrt": [0.0, 0.0, 0.0],
         "SPY": [0.0, 0.0, 0.0], "cash": [0.0, 0.0, 0.0]},
        index=dates,
    )
    predictions = pd.DataFrame(
        {"sleeve": ["E2"], "predicted_score": [1.0]},
        index=dates[:1],
    )
    result = e5.backtest(predictions, returns)
    assert result.index[0] == dates[1]
    assert result.iloc[0]["portfolio_return"] == 0.10
