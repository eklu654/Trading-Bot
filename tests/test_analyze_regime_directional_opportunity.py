from __future__ import annotations

import pandas as pd

from research.analyze_regime_directional_opportunity import PAIRS, SPLITS, summarize


def test_summarize_preserves_bull_bear_exclusivity_as_separate_sides():
    rows = []
    for regime in ("TRENDING_NORMAL", "SIDEWAYS_CHOPPY", "TURBULENT_HIGH_VOL"):
        for pair in PAIRS:
            rows.append({
                "decision_regime": regime,
                f"{pair}_bull": 0.01,
                f"{pair}_bear": -0.01,
            })
    result = summarize(pd.DataFrame(rows))
    assert set(result["side"]) == {"bull", "bear"}
    assert len(result) == len(SPLITS) * 3 * len(PAIRS) * 2


def test_split_boundaries_are_chronological():
    starts = [pd.Timestamp(v[0]) for v in SPLITS.values()]
    assert starts == sorted(starts)
