from __future__ import annotations

import pandas as pd
import pytest

from research.replay_family_rotation_account import (
    STARTING_BALANCE,
    _max_recovery_days,
    summary,
)


def test_recovery_metric_uses_calendar_days_and_dollar_drawdown():
    idx = pd.to_datetime(
        ["2026-01-01", "2026-01-03", "2026-01-06", "2026-01-11", "2026-01-12"]
    )
    frame = pd.DataFrame(
        {
            "equity": [5000.0, 6000.0, 3000.0, 6000.0, 5500.0],
            "cash": [5000.0, 0.0, 0.0, 0.0, 0.0],
            "turnover": [0.0, 1.0, 0.0, 1.0, 0.0],
        },
        index=idx,
    )

    assert _max_recovery_days(frame.equity) == 8.0
    result = summary(frame, "TEST", 25, "prior_close", "full")

    assert result["max_dollar_drawdown"] == -3000.0
    assert result["minimum_equity"] == 3000.0
    assert result["max_recovery_days"] == 8.0
    assert result["current_underwater_days"] == 1
    assert result["ending_equity"] == 5500.0
    assert result["total_return"] == pytest.approx(0.1)
    assert STARTING_BALANCE == 5000.0
