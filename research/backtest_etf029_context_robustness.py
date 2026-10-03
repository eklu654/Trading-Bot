"""ETF-029: robustness diagnostics for ETF-028 context classification.

This is a descriptive robustness check, not a strategy-selection sweep. It
repeats the ETF-028 healthy/mixed/already-bearish classification at several
pre-event lags and measures the same fixed 20-session event outcome. The
purpose is to determine whether any context separation is an artifact of
choosing exactly five sessions before the event.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from backtest_etf026_bear_event_archetypes import build, EVENT_THRESHOLD

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
FAMILIES = ("trend", "macd", "channel", "momentum", "volatility", "breadth")
LAGS = (3, 5, 10, 15, 20)
CUTOFFS = (1 / 3, 0.40, 1 / 2)


def classify(row: pd.Series, lag: int, cutoff: float) -> str:
    trend = row[f"trend_d{lag}"]
    breadth = row[f"breadth_d{lag}"]
    if trend <= cutoff and breadth <= cutoff:
        return "HEALTHY_TREND_BREADTH"
    if trend >= 1 - cutoff and breadth >= 1 - cutoff:
        return "ALREADY_BEARISH_TREND_BREADTH"
    return "MIXED_TREND_BREADTH"


def main() -> None:
    scores, _, fwd = build()
    events = fwd <= EVENT_THRESHOLD
    starts = events & ~events.shift(1).fillna(False)
    dates = starts[starts].index

    rows = []
    for d in dates:
        if pd.isna(fwd.loc[d]):
            continue
        row = {"event_date": d, "forward20": float(fwd.loc[d])}
        for lag in LAGS:
            base = scores.shift(lag).reindex([d]).iloc[0]
            for fam in FAMILIES:
                row[f"{fam}_d{lag}"] = float(base[fam]) if pd.notna(base[fam]) else np.nan
        rows.append(row)

    frame = pd.DataFrame(rows)
    results = []
    for lag in LAGS:
        for cutoff in CUTOFFS:
            x = frame.dropna(subset=[f"trend_d{lag}", f"breadth_d{lag}"]).copy()
            x["context"] = x.apply(lambda r: classify(r, lag, cutoff), axis=1)
            for context, g in x.groupby("context", dropna=False):
                results.append({
                    "lag": lag,
                    "cutoff": cutoff,
                    "context": context,
                    "events": len(g),
                    "mean_forward20": g["forward20"].mean(),
                    "median_forward20": g["forward20"].median(),
                    "pct_negative_forward20": (g["forward20"] < 0).mean(),
                })

    out = pd.DataFrame(results)
    out.to_csv(DATA / "etf029_context_robustness_summary.csv", index=False)
    frame.to_csv(DATA / "etf029_event_rows.csv", index=False)

    print("=== ETF-029 CONTEXT ROBUSTNESS ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
