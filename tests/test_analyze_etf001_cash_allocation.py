from __future__ import annotations

import numpy as np
import pandas as pd

from research.analyze_etf001_cash_allocation import CASH_LEVELS, split_summary


def test_cash_levels_are_monotonic_and_include_controls():
    assert CASH_LEVELS == tuple(sorted(CASH_LEVELS))
    assert CASH_LEVELS[0] == 0.0
    assert CASH_LEVELS[-1] == 1.0
    assert 0.25 in CASH_LEVELS
    assert len(CASH_LEVELS) == 12


def test_split_summary_reports_5000_capital_equivalent():
    idx = pd.date_range("2023-01-01", periods=3, freq="D")
    frame = pd.DataFrame(
        {
            "portfolio_return": [0.0, 0.1, -0.05],
            "portfolio_value": [1.0, 1.1, 1.045],
            "drawdown": [0.0, 0.0, -0.05],
            "invested_weight": [0.0, 1.0, 1.0],
        },
        index=idx,
    )
    result = split_summary(frame, "2023-01-01", "2023-12-31")
    assert result["observations"] == 3
    assert np.isclose(result["ending_value_5000"], 5225.0)
