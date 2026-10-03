"""ETF-030: temporal stability diagnostics for bearish-event context.

This is a descriptive validation step after ETF-029. It asks whether the
context separation seen in the bearish-event diagnostics persists across
different calendar eras, rather than being concentrated in one historical
period. No cutoff, lag, or strategy is selected from the results.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from backtest_etf026_bear_event_archetypes import build, EVENT_THRESHOLD

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
LAGS = (3, 5, 10, 15, 20)
CUTOFFS = (1 / 3, 0.40, 1 / 2)
ERAS = (
    ("2007-01-01", "2014-12-31", "2007_2014"),
    ("2015-01-01", "2019-12-31", "2015_2019"),
    ("2020-01-01", "2022-12-31", "2020_2022"),
    ("2023-01-01", "2026-12-31", "2023_2026"),
)


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
            for family in scores.columns:
                row[f"{family}_d{lag}"] = (
                    float(base[family]) if pd.notna(base[family]) else np.nan
                )
        rows.append(row)

    frame = pd.DataFrame(rows)
    frame["era"] = "UNMAPPED"
    for start, end, name in ERAS:
        mask = frame["event_date"].between(pd.Timestamp(start), pd.Timestamp(end))
        frame.loc[mask, "era"] = name

    results = []
    for lag in LAGS:
        for cutoff in CUTOFFS:
            usable = frame.dropna(
                subset=[f"trend_d{lag}", f"breadth_d{lag}"]
            ).copy()
            usable["context"] = usable.apply(
                lambda row: classify(row, lag, cutoff), axis=1
            )
            for era, era_frame in usable.groupby("era", dropna=False):
                for context, group in era_frame.groupby("context", dropna=False):
                    results.append(
                        {
                            "era": era,
                            "lag": lag,
                            "cutoff": cutoff,
                            "context": context,
                            "events": len(group),
                            "mean_forward20": group["forward20"].mean(),
                            "median_forward20": group["forward20"].median(),
                            "pct_negative_forward20": (
                                group["forward20"] < 0
                            ).mean(),
                        }
                    )

    out = pd.DataFrame(results)
    out.to_csv(DATA / "etf030_era_stability_summary.csv", index=False)
    frame.to_csv(DATA / "etf030_event_rows.csv", index=False)

    print("=== ETF-030 TEMPORAL STABILITY ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
