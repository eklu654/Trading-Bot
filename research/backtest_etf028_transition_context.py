"""ETF-028: bearish-transition context diagnostics.

Stratify the ETF-027 bearish-event population by the pre-event trend/breadth
context and report whether transition magnitude behaves differently when the
market was relatively healthy versus already bearish. This is descriptive:
there is no return-optimized threshold search and no strategy selection.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from backtest_etf026_bear_event_archetypes import build

DATA = Path(__file__).resolve().parents[1] / "data" / "research"
EVENT_THRESHOLD = -0.04
FAMILIES = ("trend", "macd", "channel", "momentum", "volatility", "breadth")

def event_row(scores: pd.DataFrame, fwd: pd.Series, d: pd.Timestamp) -> dict:
    row = {"event_date": d, "forward20": float(fwd.loc[d]) if pd.notna(fwd.loc[d]) else np.nan}
    for fam in FAMILIES:
        vals = [float(scores.shift(l).loc[d, fam]) for l in (10, 5, 0)]
        row[f"{fam}_d10"], row[f"{fam}_d5"], row[f"{fam}_d0"] = vals
        row[f"{fam}_delta10to5"] = vals[1] - vals[0]
        row[f"{fam}_delta5to0"] = vals[2] - vals[1]
        row[f"{fam}_delta10to0"] = vals[2] - vals[0]
    return row

def classify(row: pd.Series) -> str:
    trend5, breadth5 = row["trend_d5"], row["breadth_d5"]
    if trend5 <= 1 / 3 and breadth5 <= 1 / 3:
        return "HEALTHY_TREND_BREADTH"
    if trend5 >= 2 / 3 and breadth5 >= 2 / 3:
        return "ALREADY_BEARISH_TREND_BREADTH"
    return "MIXED_TREND_BREADTH"

def main() -> None:
    scores, _, fwd = build()
    event = fwd <= EVENT_THRESHOLD
    starts = event & ~event.shift(1).fillna(False)
    dates = starts[starts].index
    frame = pd.DataFrame([event_row(scores, fwd, d) for d in dates]).dropna(subset=["forward20"])
    frame["context"] = frame.apply(classify, axis=1)
    delta_cols = [f"{fam}_delta10to0" for fam in FAMILIES]
    frame["mean_abs_family_change"] = frame[delta_cols].abs().mean(axis=1)
    frame["positive_family_changes"] = (frame[delta_cols] > 0).sum(axis=1)
    frame["large_positive_changes"] = (frame[delta_cols] >= 1 / 3).sum(axis=1)
    summary = frame.groupby("context", dropna=False).agg(
        events=("event_date", "size"),
        mean_forward20=("forward20", "mean"),
        median_forward20=("forward20", "median"),
        pct_negative_forward20=("forward20", lambda x: (x < 0).mean()),
        mean_abs_family_change=("mean_abs_family_change", "mean"),
        mean_positive_family_changes=("positive_family_changes", "mean"),
        mean_large_positive_changes=("large_positive_changes", "mean"),
    ).reset_index()
    summary.to_csv(DATA / "etf028_context_summary.csv", index=False)
    frame.to_csv(DATA / "etf028_event_context_rows.csv", index=False)
    print("=== ETF-028 CONTEXT SUMMARY ===")
    print(summary.to_string(index=False))
    print("\n=== ETF-028 EVENT ROWS ===")
    print(frame.to_string(index=False))

if __name__ == "__main__":
    main()