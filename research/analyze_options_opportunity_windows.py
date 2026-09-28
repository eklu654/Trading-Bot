"""Measure OPTIONS-001 opportunity density from the regime dataset.

This is NOT an options P/L backtest. It only answers whether the proposed
regime classifier creates sufficiently frequent and sufficiently long
candidate windows for options trading.

Run from repository root:
    python research/analyze_options_opportunity_windows.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

ELIGIBLE = {"SIDEWAYS_CHOPPY", "TURBULENT_HIGH_VOL"}


def load() -> pd.DataFrame:
    path = DATA_DIR / "historical_regime_dataset.csv"
    return pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()


def build_windows(frame: pd.DataFrame) -> pd.DataFrame:
    eligible = frame["decision_regime"].isin(ELIGIBLE)

    windows = []
    start = None
    previous = None
    regime_values: list[str] = []

    for date, is_eligible in eligible.items():
        if is_eligible and start is None:
            start = date
            regime_values = [frame.loc[date, "decision_regime"]]
        elif is_eligible and start is not None:
            regime_values.append(frame.loc[date, "decision_regime"])
        elif not is_eligible and start is not None:
            end = previous
            dates = frame.loc[start:end].index
            windows.append(
                {
                    "start": start,
                    "end": end,
                    "trading_days": len(dates),
                    "calendar_days": (end - start).days + 1,
                    "regimes_present": ",".join(sorted(set(regime_values))),
                }
            )
            start = None
            regime_values = []

        previous = date

    if start is not None and previous is not None:
        dates = frame.loc[start:previous].index
        windows.append(
            {
                "start": start,
                "end": previous,
                "trading_days": len(dates),
                "calendar_days": (previous - start).days + 1,
                "regimes_present": ",".join(sorted(set(regime_values))),
            }
        )

    return pd.DataFrame(windows)


def main() -> None:
    frame = load()
    windows = build_windows(frame)

    total = len(frame)
    eligible_days = int(
        frame["decision_regime"].isin(ELIGIBLE).sum()
    )

    summary = pd.DataFrame(
        [
            {
                "sample_start": frame.index.min(),
                "sample_end": frame.index.max(),
                "observations": total,
                "eligible_observations": eligible_days,
                "eligible_fraction": eligible_days / total if total else 0.0,
                "candidate_windows": len(windows),
                "mean_trading_days_per_window": (
                    windows["trading_days"].mean() if len(windows) else 0.0
                ),
                "median_trading_days_per_window": (
                    windows["trading_days"].median() if len(windows) else 0.0
                ),
                "windows_at_least_21_sessions": (
                    int((windows["trading_days"] >= 21).sum())
                    if len(windows)
                    else 0
                ),
                "windows_at_least_30_sessions": (
                    int((windows["trading_days"] >= 30).sum())
                    if len(windows)
                    else 0
                ),
                "windows_at_least_45_calendar_days": (
                    int((windows["calendar_days"] >= 45).sum())
                    if len(windows)
                    else 0
                ),
            }
        ]
    )

    regime_counts = (
        frame["decision_regime"]
        .value_counts(dropna=False)
        .rename_axis("regime")
        .reset_index(name="observations")
    )
    regime_counts["fraction"] = regime_counts["observations"] / total

    windows.to_csv(DATA_DIR / "options_opportunity_windows.csv", index=False)
    summary.to_csv(DATA_DIR / "options_opportunity_summary.csv", index=False)
    regime_counts.to_csv(DATA_DIR / "regime_frequency_summary.csv", index=False)

    print("OPTIONS-001 opportunity-density summary")
    print(summary.to_string(index=False))
    print("\\nRegime frequency")
    print(regime_counts.to_string(index=False))


if __name__ == "__main__":
    main()
