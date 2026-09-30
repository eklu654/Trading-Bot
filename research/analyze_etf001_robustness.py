"""Analyze local robustness of ETF-001 trend-matrix candidates.

A candidate's neighborhood consists of one-step changes in exactly one matrix
parameter while holding the others fixed. Robustness is computed from training
data only for selection-related metrics. Validation and holdout values are
reported for the same fixed candidates but never used to construct the
training robustness score.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
MATRIX = DATA_DIR / "etf001_trend_matrix.csv"
OUT = DATA_DIR / "etf001_trend_matrix_robustness.csv"

PARAMS = {
    "ma_window": (100, 125, 150, 175, 200, 225, 250),
    "exit_buffer": (0.0, 0.01, 0.02),
    "reentry_buffer": (0.0, 0.01, 0.02),
    "reentry_sessions": (1, 3, 5),
}


def key(row: pd.Series) -> tuple:
    return (
        int(row.ma_window),
        round(float(row.exit_buffer), 10),
        round(float(row.reentry_buffer), 10),
        int(row.reentry_sessions),
    )


def main() -> None:
    frame = pd.read_csv(MATRIX)
    required = set(PARAMS) | {
        "train_annualized_return",
        "train_max_drawdown",
        "train_sharpe_no_risk_free",
        "validation_annualized_return",
        "validation_sharpe_no_risk_free",
        "validation_max_drawdown",
        "holdout_annualized_return",
        "holdout_sharpe_no_risk_free",
        "holdout_max_drawdown",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Matrix is missing required columns: {missing}")

    frame["_key"] = frame.apply(key, axis=1)
    lookup = {r["_key"]: r for _, r in frame.iterrows()}
    rows = []

    for _, row in frame.iterrows():
        neighbors = []
        base = list(row["_key"])
        for i, name in enumerate(PARAMS):
            values = PARAMS[name]
            pos = values.index(base[i])
            for npos in (pos - 1, pos + 1):
                if 0 <= npos < len(values):
                    candidate = base.copy()
                    candidate[i] = values[npos]
                    found = lookup.get(tuple(candidate))
                    if found is not None:
                        neighbors.append(found)

        if not neighbors:
            continue

        ng = pd.DataFrame(neighbors)
        train_ratio = row.train_annualized_return / abs(row.train_max_drawdown) if row.train_max_drawdown else np.nan
        n_ratio = ng.train_annualized_return / ng.train_max_drawdown.abs().replace(0, np.nan)

        rows.append({
            "ma_window": int(row.ma_window),
            "exit_buffer": float(row.exit_buffer),
            "reentry_buffer": float(row.reentry_buffer),
            "reentry_sessions": int(row.reentry_sessions),
            "neighbor_count": len(ng),
            "train_return_drawdown_ratio": train_ratio,
            "train_sharpe_no_risk_free": float(row.train_sharpe_no_risk_free),
            "neighbor_train_ratio_mean": float(n_ratio.mean()),
            "neighbor_train_ratio_std": float(n_ratio.std(ddof=0)),
            "neighbor_train_ratio_min": float(n_ratio.min()),
            "neighbor_train_ratio_max": float(n_ratio.max()),
            "neighbor_positive_ratio_fraction": float((n_ratio > 0).mean()),
            "neighbor_sharpe_mean": float(ng.train_sharpe_no_risk_free.mean()),
            "neighbor_sharpe_std": float(ng.train_sharpe_no_risk_free.std(ddof=0)),
            "train_ratio_minus_neighbor_mean": float(train_ratio - n_ratio.mean()),
            "validation_annualized_return": float(row.validation_annualized_return),
            "validation_sharpe_no_risk_free": float(row.validation_sharpe_no_risk_free),
            "validation_max_drawdown": float(row.validation_max_drawdown),
            "holdout_annualized_return": float(row.holdout_annualized_return),
            "holdout_sharpe_no_risk_free": float(row.holdout_sharpe_no_risk_free),
            "holdout_max_drawdown": float(row.holdout_max_drawdown),
        })

    out = pd.DataFrame(rows)
    # This is intentionally a descriptive robustness score: it uses only
    # training-period quantities and is not a claim of expected live performance.
    out["training_robustness_score"] = (
        out["neighbor_positive_ratio_fraction"] * out["neighbor_train_ratio_mean"]
        - out["neighbor_train_ratio_std"].fillna(0.0) * 0.25
    )
    out = out.sort_values(
        ["training_robustness_score", "train_sharpe_no_risk_free"],
        ascending=False,
    )
    out.to_csv(OUT, index=False)

    print("=== ETF-001 LOCAL ROBUSTNESS ===")
    print(out.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
