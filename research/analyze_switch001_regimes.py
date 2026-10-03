"""Analyze SWITCH-001 historical regime labels without look-ahead.

This is an evidence report, not a strategy optimizer. Regime labels are read
from the historical dataset produced by build_historical_regime_dataset.py.
For each label, the report measures next-session returns of the three ETF-001
sleeves and broad benchmarks. No thresholds are selected from these results.

Outputs:
  data/research/switch001_regime_performance.csv
  data/research/switch001_regime_summary.csv
  data/research/switch001_stress_regimes.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

REGIME_FILE = DATA_DIR / "historical_regime_dataset.csv"
SYMBOLS = ("SPY", "QQQ", "SOXX", "TQQQ", "SPXL", "SOXL")

STRESS_WINDOWS = {
    "2018_volatility_shock": ("2018-02-01", "2018-02-28"),
    "2018_q4": ("2018-10-01", "2018-12-31"),
    "covid_crash": ("2020-02-19", "2020-04-30"),
    "2022_rate_hike": ("2022-01-03", "2022-12-30"),
}


def load_prices(symbol: str) -> pd.Series:
    path = DATA_DIR / f"{symbol.lower()}_daily.csv"
    frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    column = "adj_close" if "adj_close" in frame.columns else "close"
    return frame[column]


def load_regime() -> pd.DataFrame:
    if not REGIME_FILE.exists():
        raise FileNotFoundError(
            f"{REGIME_FILE} not found; run build_historical_regime_dataset.py first"
        )
    frame = pd.read_csv(REGIME_FILE, parse_dates=["Date"]).set_index("Date").sort_index()
    required = {"regime", "decision_regime"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"regime dataset missing columns: {sorted(missing)}")
    return frame


def build_forward_returns(regime: pd.DataFrame) -> pd.DataFrame:
    out = regime[["regime", "decision_regime"]].copy()
    for symbol in SYMBOLS:
        prices = load_prices(symbol).reindex(out.index)
        # The decision_regime at t is already shifted by the dataset builder.
        # Return measured from t to t+1 therefore represents the next session
        # after the decision was known at the close of t.
        out[f"{symbol}_fwd1"] = prices.shift(-1) / prices - 1.0
    return out


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for regime, group in frame.groupby("decision_regime", dropna=False):
        if pd.isna(regime):
            continue
        row: dict[str, object] = {
            "decision_regime": regime,
            "observations": int(len(group)),
        }
        for symbol in SYMBOLS:
            x = group[f"{symbol}_fwd1"].dropna()
            row[f"{symbol}_mean_fwd1"] = float(x.mean()) if len(x) else np.nan
            row[f"{symbol}_median_fwd1"] = float(x.median()) if len(x) else np.nan
            row[f"{symbol}_win_rate"] = float((x > 0).mean()) if len(x) else np.nan
            row[f"{symbol}_worst_day"] = float(x.min()) if len(x) else np.nan
            row[f"{symbol}_q05"] = float(x.quantile(0.05)) if len(x) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def stress_report(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for name, (start, end) in STRESS_WINDOWS.items():
        segment = frame.loc[start:end].copy()
        if segment.empty:
            continue
        for regime, group in segment.groupby("decision_regime", dropna=False):
            if pd.isna(regime):
                continue
            row = {
                "stress_window": name,
                "start": start,
                "end": end,
                "decision_regime": regime,
                "observations": int(len(group)),
            }
            for symbol in SYMBOLS:
                x = group[f"{symbol}_fwd1"].dropna()
                row[f"{symbol}_mean_fwd1"] = float(x.mean()) if len(x) else np.nan
                row[f"{symbol}_worst_day"] = float(x.min()) if len(x) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    regime = load_regime()
    frame = build_forward_returns(regime)

    performance = frame.dropna(subset=["decision_regime"])
    summary = summarize(performance)
    stress = stress_report(performance)

    frame.to_csv(DATA_DIR / "switch001_regime_performance.csv")
    summary.to_csv(DATA_DIR / "switch001_regime_summary.csv", index=False)
    stress.to_csv(DATA_DIR / "switch001_stress_regimes.csv", index=False)

    print("SWITCH-001 regime summary")
    print(summary.to_string(index=False))
    print("\nSWITCH-001 stress-period regime observations")
    print(stress.to_string(index=False) if not stress.empty else "No stress-window rows.")


if __name__ == "__main__":
    main()
