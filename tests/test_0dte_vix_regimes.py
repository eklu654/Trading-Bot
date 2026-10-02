import importlib.util
from pathlib import Path

import pandas as pd
import pytest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "0dte" / "analyze_vix_regimes.py"
SPEC = importlib.util.spec_from_file_location("analyze_vix_regimes", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_vix_bucket_boundaries_are_fixed_and_left_closed():
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=5, freq="D"),
            "vix": [14.99, 15.0, 20.0, 25.0, 30.0],
            "net_pnl": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )

    result = MODULE.summarize(frame)
    full_sample = result[result["split"] == "FULL_SAMPLE"].sort_values("vix_bucket")

    assert full_sample["vix_bucket"].tolist() == [
        "<15",
        "15-20",
        "20-25",
        "25-30",
        ">=30",
    ]
    assert full_sample["sessions"].tolist() == [1, 1, 1, 1, 1]


def test_summarize_keeps_full_sample_and_chronological_splits():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-06-01", "2025-06-01", "2026-06-01", "2026-09-28"]
            ),
            "vix": [12.0, 18.0, 22.0, 31.0],
            "net_pnl": [10.0, -5.0, 7.0, -2.0],
        }
    )

    result = MODULE.summarize(frame)

    assert set(result["split"]) == {"FULL_SAMPLE", "TRAIN", "VALIDATION", "HOLDOUT"}
    assert result.loc[
        (result["split"] == "FULL_SAMPLE") & (result["vix_bucket"] == "<15"),
        "net_pnl",
    ].iloc[0] == pytest.approx(10.0)


def test_summarize_drops_sessions_without_a_vix_bucket():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "vix": [None, 24.0],
            "net_pnl": [100.0, 7.0],
        }
    )

    result = MODULE.summarize(frame)
    full_sample = result[result["split"] == "FULL_SAMPLE"]

    assert full_sample["sessions"].sum() == 1
    assert full_sample.loc[
        full_sample["vix_bucket"] == "20-25", "net_pnl"
    ].iloc[0] == pytest.approx(7.0)
