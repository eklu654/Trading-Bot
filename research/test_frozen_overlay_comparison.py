"""Synthetic unit tests for frozen-input overlay comparison diagnostics."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

RESEARCH = Path(__file__).resolve().parent
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

from canonical_shock_recovery_frozen_overlay_comparison import (  # noqa: E402
    episode_contributions,
    metrics,
)


def test_episode_counterfactual_only_removes_incremental_overlay_exposure():
    dates = pd.bdate_range("2024-01-02", periods=6)
    frame = pd.DataFrame(
        {
            "tqqq_adj_open": [100.0, 100.0, 110.0, 90.0, 100.0, 105.0],
            "tqqq_adj_close": [100.0, 110.0, 90.0, 100.0, 105.0, 120.0],
        },
        index=dates,
    )
    # Overlay active on indices 1-3; baseline independently defends index 2.
    baseline = np.array([1.0, 1.0, 0.0, 1.0, 1.0, 1.0])
    overlay = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 1.0])

    result = episode_contributions(dates, frame, baseline, overlay, 0.5)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["start_date"] == dates[1].date().isoformat()
    assert row["end_date"] == dates[3].date().isoformat()
    assert row["overlay_sessions"] == 3
    assert row["incremental_defense_sessions"] == 2
    assert row["overlap_with_baseline_defense_sessions"] == 1
    assert row["candidate_final"] != row["counterfactual_final_without_episode"]


def test_metrics_reports_terminal_equity_and_drawdown_from_same_return_path():
    dates = pd.bdate_range("2020-01-02", periods=300)
    returns = np.full(300, 0.001)
    returns[200] = -0.25
    result = metrics(returns, dates, initial=5000.0)

    expected_final = 5000.0 * np.prod(1.0 + returns)
    assert np.isclose(result["final_balance"], expected_final)
    assert result["max_drawdown"] < 0.0
    assert result["worst_rolling_252_session_return"] < 0.0
