"""Unit tests for the E4c risk-aware target baseline."""

import numpy as np
import pandas as pd

from research import backtest_ai_risk_aware_selector as ai


def test_risk_aware_target_uses_future_volatility(monkeypatch):
    dates = pd.date_range("2025-01-01", periods=25, freq="D")
    prices = pd.DataFrame({
        "Date": dates,
        "adj_close": np.arange(100.0, 125.0),
    }).set_index("Date")
    monkeypatch.setattr(ai, "load", lambda symbol: prices)
    targets = ai.risk_aware_targets(dates)

    assert targets.index.equals(dates)
    assert np.isfinite(targets.iloc[0]["SPY_1x"])
    assert pd.isna(targets.iloc[-1]["SPY_1x"])
    assert targets.iloc[0]["cash"] == 0.0

from research import backtest_ai_risk_aware_selector as ai


def test_leverage_caps_only_reduce_leverage():
    predictions = pd.DataFrame(
        {"action": ["SPY_3x", "QQQ_2x", "SOXX_1x", "cash"]},
        index=pd.date_range("2025-01-01", periods=4),
    )
    cap2 = ai.apply_leverage_cap(predictions, "cap_2x")
    cap1 = ai.apply_leverage_cap(predictions, "cap_1x")
    assert list(cap2["action"]) == ["SPY_2x", "QQQ_2x", "SOXX_1x", "cash"]
    assert list(cap1["action"]) == ["SPY_1x", "QQQ_1x", "SOXX_1x", "cash"]
