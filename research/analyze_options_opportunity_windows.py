"""Measure OPTIONS-001 opportunity density for research regime candidates.

This is NOT an options P/L backtest. It only answers whether candidate
eligibility regimes create sufficiently frequent and sufficiently long windows
for historical option-chain replay.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from evaluate_regime_candidates import candidate_labels

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"


def load() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "historical_regime_dataset.csv", parse_dates=["Date"]).set_index("Date").sort_index()


def build_windows(eligible: pd.Series, frame: pd.DataFrame) -> pd.DataFrame:
    windows, start, previous = [], None, None
    for date, is_eligible in eligible.items():
        if is_eligible and start is None:
            start = date
        elif not is_eligible and start is not None:
            end = previous
            windows.append({"start": start, "end": end, "trading_days": len(frame.loc[start:end]), "calendar_days": (end - start).days + 1})
            start = None
        previous = date
    if start is not None and previous is not None:
        windows.append({"start": start, "end": previous, "trading_days": len(frame.loc[start:previous]), "calendar_days": (previous - start).days + 1})
    return pd.DataFrame(windows)


def summarize(frame: pd.DataFrame, labels: pd.Series, name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = labels.shift(1)
    eligible = labels.isin({"SIDEWAYS_CHOPPY", "TURBULENT_HIGH_VOL"})
    windows = build_windows(eligible, frame)
    total = len(frame)
    eligible_days = int(eligible.sum())
    summary = pd.DataFrame([{
        "candidate": name,
        "sample_start": frame.index.min(),
        "sample_end": frame.index.max(),
        "observations": total,
        "eligible_observations": eligible_days,
        "eligible_fraction": eligible_days / total if total else 0.0,
        "candidate_windows": len(windows),
        "mean_trading_days_per_window": windows["trading_days"].mean() if len(windows) else 0.0,
        "median_trading_days_per_window": windows["trading_days"].median() if len(windows) else 0.0,
        "windows_at_least_21_sessions": int((windows["trading_days"] >= 21).sum()) if len(windows) else 0,
        "windows_at_least_30_sessions": int((windows["trading_days"] >= 30).sum()) if len(windows) else 0,
        "windows_at_least_45_calendar_days": int((windows["calendar_days"] >= 45).sum()) if len(windows) else 0,
    }])
    return summary, windows


def main() -> None:
    frame = load()
    candidates = {
        "CURRENT": candidate_labels(frame, "CURRENT"),
        "BALANCED": candidate_labels(frame, "BALANCED"),
        "BROAD_SIDEWAYS": candidate_labels(frame, "BROAD_SIDEWAYS"),
    }
    candidates["TURBULENT_ONLY"] = pd.Series("TURBULENT_HIGH_VOL", index=frame.index).where(
        frame["vix_percentile252"] >= 0.90, "TRENDING_NORMAL"
    )

    summaries, all_windows = [], []
    for name, labels in candidates.items():
        summary, windows = summarize(frame, labels, name)
        summaries.append(summary)
        if len(windows):
            windows.insert(0, "candidate", name)
            all_windows.append(windows)

        if name == "CURRENT":
            summary.drop(columns=["candidate"]).to_csv(DATA_DIR / "options_opportunity_summary.csv", index=False)
            windows.to_csv(DATA_DIR / "options_opportunity_windows.csv", index=False)
            counts = labels.shift(1).value_counts(dropna=False).rename_axis("regime").reset_index(name="observations")
            counts["fraction"] = counts["observations"] / len(labels)
            counts.to_csv(DATA_DIR / "regime_frequency_summary.csv", index=False)

    summary = pd.concat(summaries, ignore_index=True)
    windows = pd.concat(all_windows, ignore_index=True) if all_windows else pd.DataFrame()

    summary.to_csv(DATA_DIR / "options_opportunity_candidate_summary.csv", index=False)
    windows.to_csv(DATA_DIR / "options_opportunity_candidate_windows.csv", index=False)

    print("=== OPTIONS CANDIDATE OPPORTUNITY DENSITY ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
