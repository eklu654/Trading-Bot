"""E6 binary AI overlay tests."""

import pandas as pd

from research import backtest_ai_e2_overlay as e6


def test_e6_has_only_two_actions():
    assert e6.HORIZON == 20
    assert e6.ALPHA == 1.0


def test_e6_binary_policy_uses_only_e2_or_cash():
    predictions = pd.DataFrame(
        {"action": ["E2", "cash", "E2"], "predicted_score": [1.0, -0.1, 0.2]},
        index=pd.date_range("2025-01-01", periods=3),
    )
    assert set(predictions["action"]) <= {"E2", "cash"}


def test_e6_backtest_applies_action_to_next_session():
    dates = pd.date_range("2025-01-01", periods=4)
    returns = pd.Series([0.0, 0.10, -0.05, 0.02], index=dates)
    predictions = pd.DataFrame(
        {"action": ["E2", "cash", "E2"], "predicted_score": [1.0, -1.0, 1.0]},
        index=dates[:3],
    )
    result = e6.backtest(predictions, returns)
    assert list(result.index) == list(dates[1:])
    assert result.iloc[0]["portfolio_return"] == 0.10
    assert result.iloc[1]["portfolio_return"] == 0.0
    assert result.iloc[2]["portfolio_return"] == 0.02
