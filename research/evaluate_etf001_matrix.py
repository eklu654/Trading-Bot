"""Evaluate ETF-001 trend-matrix candidates without using holdout data for selection.

The matrix generator ranks candidates only on the training period. This evaluator
reports the corresponding validation and holdout results for fixed top-K cohorts,
plus the current 200-DMA/5-session baseline. It does not select on validation
or holdout performance.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
MATRIX = DATA_DIR / "etf001_trend_matrix.csv"
OUT = DATA_DIR / "etf001_trend_matrix_validation_report.csv"

BASELINE = {
    "ma_window": 200,
    "exit_buffer": 0.0,
    "reentry_buffer": 0.0,
    "reentry_sessions": 5,
}


def _same(row: pd.Series, spec: dict) -> bool:
    return (
        int(row["ma_window"]) == spec["ma_window"]
        and float(row["exit_buffer"]) == spec["exit_buffer"]
        and float(row["reentry_buffer"]) == spec["reentry_buffer"]
        and int(row["reentry_sessions"]) == spec["reentry_sessions"]
    )


def main() -> None:
    frame = pd.read_csv(MATRIX)
    required = {
        "ma_window", "exit_buffer", "reentry_buffer", "reentry_sessions",
        "train_return_drawdown_ratio", "train_annualized_return",
        "train_sharpe_no_risk_free", "validation_annualized_return",
        "validation_sharpe_no_risk_free", "validation_max_drawdown",
        "holdout_annualized_return", "holdout_sharpe_no_risk_free",
        "holdout_max_drawdown",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Matrix is missing required columns: {missing}")

    ranked = frame.sort_values(
        ["train_return_drawdown_ratio", "train_sharpe_no_risk_free"],
        ascending=False,
    ).reset_index(drop=True)

    rows: list[dict] = []

    baseline_matches = ranked[ranked.apply(lambda r: _same(r, BASELINE), axis=1)]
    if not baseline_matches.empty:
        row = baseline_matches.iloc[0].to_dict()
        row["selection"] = "baseline_200dma_5session"
        row["selection_k"] = 1
        row["train_rank"] = int(baseline_matches.index[0]) + 1
        rows.append(row)

    for k in (1, 5, 10, 25):
        cohort = ranked.head(k)
        for rank, (_, row) in enumerate(cohort.iterrows(), start=1):
            item = row.to_dict()
            item["selection"] = f"train_top_{k}"
            item["selection_k"] = k
            item["train_rank"] = rank
            rows.append(item)

    report = pd.DataFrame(rows)
    report.to_csv(OUT, index=False)

    print("=== ETF-001 TREND MATRIX VALIDATION REPORT ===")
    cols = [
        "selection", "selection_k", "train_rank", "ma_window",
        "exit_buffer", "reentry_buffer", "reentry_sessions",
        "train_annualized_return", "train_return_drawdown_ratio",
        "validation_annualized_return", "validation_sharpe_no_risk_free",
        "validation_max_drawdown", "holdout_annualized_return",
        "holdout_sharpe_no_risk_free", "holdout_max_drawdown",
    ]
    print(report[cols].to_string(index=False))


if __name__ == "__main__":
    main()
