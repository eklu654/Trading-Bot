from __future__ import annotations

import pandas as pd

from research.analyze_regime_directional_opportunity import PAIRS, SPLITS, summarize


def test_summarize_preserves_bull_bear_exclusivity_as_separate_sides():
    dates = pd.to_datetime(["2019-01-01", "2020-01-01", "2023-01-01"])
    rows = []
    for date in dates:
        for regime in ("TRENDING_NORMAL", "SIDEWAYS_CHOPPY", "TURBULENT_HIGH_VOL"):
            row = {"Date": date, "decision_regime": regime}
            for pair in PAIRS:
                row[f"{pair}_bull"] = 0.01
                row[f"{pair}_bear"] = -0.01
            rows.append(row)
    frame = pd.DataFrame(rows).set_index("Date")
    result = summarize(frame)
    assert set(result["side"]) == {"bull", "bear"}
    assert len(result) == len(SPLITS) * 3 * len(PAIRS) * 2


def test_split_boundaries_are_chronological():
    starts = [pd.Timestamp(v[0]) for v in SPLITS.values()]
    assert starts == sorted(starts)
