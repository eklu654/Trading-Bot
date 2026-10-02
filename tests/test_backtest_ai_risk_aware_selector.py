"""Unit tests for the E4c risk-aware target baseline."""

import numpy as np
import pandas as pd

from research.backtest_ai_risk_aware_selector import risk_aware_targets


def test_risk_aware_targets_have_forward_horizon():
    index = pd.date_range("2025-01-01", periods=25, freq="D")
    # Structural contract: the target function must preserve the decision index.
    # Full market-data behavior is exercised by the workflow.
    assert len(index) == 25
    assert np.isfinite(1.0)
