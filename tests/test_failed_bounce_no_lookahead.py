import importlib.util
import sys
from pathlib import Path

import pandas as pd


RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))
MODULE_PATH = RESEARCH_DIR / "failed_bounce_structural_matrix.py"
SPEC = importlib.util.spec_from_file_location("failed_bounce_structural_matrix_under_test", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_censored_future_outcome_does_not_skip_live_strategy_event():
    prices = pd.Series([100.0, 90.0, 100.0, 110.0, 120.0])
    events = pd.DataFrame([{
        "decision_i": 2,
        "event_start_i": 1,
        "label": "censored",
        "feature": 1.0,
    }])

    weights = MODULE.signal_for_rule(
        prices,
        events,
        rule=lambda row: bool(row.feature),
        target=0.10,
        exposure=0.50,
    )

    # The event must be traded even though its later diagnostic label is censored.
    # Defensive through the +10% decision close, then reduced exposure until
    # the higher target is met, then full exposure again.
    assert weights.tolist() == [1.0, 0.0, 0.5, 1.0, 1.0]


def test_feature_rule_is_decided_from_event_row_not_future_label():
    prices = pd.Series([100.0, 90.0, 100.0, 105.0, 110.0])
    events = pd.DataFrame([{
        "decision_i": 2,
        "event_start_i": 1,
        "label": "failed",
        "feature": 0.0,
    }])

    weights = MODULE.signal_for_rule(
        prices,
        events,
        rule=lambda row: bool(row.feature),
        target=0.20,
        exposure=0.50,
    )

    # A non-flagged event returns to full exposure at the +10% decision.
    assert weights.tolist() == [1.0, 0.0, 1.0, 1.0, 1.0]
