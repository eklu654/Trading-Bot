"""E6 post-run diagnostics: compare the binary overlay with frozen E2.

This is deliberately descriptive rather than a parameter search. It consumes the
already-generated E6 artifacts and reports split/stress metrics for the overlay
and the unmodified E2 baseline on identical dates.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

SPLITS = {
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-09-25"),
}

STRESS_WINDOWS = {
    "covid_2020": ("2020-02-19", "2020-04-30"),
    "rate_hike_2022": ("2022-01-03", "2022-12-30"),
}


def stats(returns: pd.Series, values: pd.Series, label: str) -> dict[str, object]:
    returns = returns.fillna(0.0)
    values = values.ffill()
    if values.empty:
        return {}
    total = (1.0 + returns).prod() - 1.0
    years = max((returns.index[-1] - returns.index[0]).days / 365.25, 1 / 365.25)
    vol = returns.std(ddof=1) * np.sqrt(252)
    sharpe = returns.mean() / returns.std(ddof=1) * np.sqrt(252) if returns.std(ddof=1) else np.nan
    drawdown = values / values.cummax() - 1.0
    return {
        "strategy": label,
        "start": returns.index.min(),
        "end": returns.index.max(),
        "total_return": float(total),
        "cagr": float((1.0 + total) ** (1.0 / years) - 1.0),
        "volatility": float(vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(drawdown.min()),
        "worst_day": float(returns.min()),
    }


def main() -> None:
    result = pd.read_csv(DATA_DIR / "e6_backtest.csv", parse_dates=["Date"]).set_index("Date")
    rows = []
    for split, (start, end) in SPLITS.items():
        segment = result.loc[start:end]
        if segment.empty:
            continue
        overlay = stats(segment["portfolio_return"], segment["portfolio_value"], f"E6_{split}")
        baseline = stats(segment["e2_baseline_return"], segment["e2_baseline_value"], f"E2_{split}")
        overlay["split"] = split
        baseline["split"] = split
        rows.extend([overlay, baseline])

    stress_rows = []
    for stress, (start, end) in STRESS_WINDOWS.items():
        segment = result.loc[start:end]
        if segment.empty:
            continue
        for label, ret_col, value_col in (
            ("E6", "portfolio_return", "portfolio_value"),
            ("E2", "e2_baseline_return", "e2_baseline_value"),
        ):
            row = stats(segment[ret_col], segment[value_col], f"{label}_{stress}")
            row["stress"] = stress
            row["cash_pct"] = float((segment["action"] == "cash").mean()) if label == "E6" else 0.0
            stress_rows.append(row)

    split_df = pd.DataFrame(rows)
    stress_df = pd.DataFrame(stress_rows)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    split_df.to_csv(DATA_DIR / "e6_incremental_summary.csv", index=False)
    stress_df.to_csv(DATA_DIR / "e6_incremental_stress.csv", index=False)

    print("E6 vs frozen E2")
    print(split_df.to_string(index=False))
    print("\nStress diagnostics")
    print(stress_df.to_string(index=False))


if __name__ == "__main__":
    main()
