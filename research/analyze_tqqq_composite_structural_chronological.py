"""Chronological robustness report for the frozen composite defense rule.

No parameters are changed. The report evaluates the already-frozen composite
family over fixed chronological slices:
- 1999-03-10 through 2009-12-31
- 2010-01-01 through 2019-12-31
- 2020-01-01 through the latest available date

This is a robustness/holdout report, not an optimization.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.test_tqqq_composite_structural_defense import (
    build_composite_frame,
    composite_weights,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
EXPOSURES = (0.0, 0.25, 0.50, 0.75)
PERIODS = {
    "1999_2009": ("1999-03-10", "2009-12-31"),
    "2010_2019": ("2010-01-01", "2019-12-31"),
    "2020_2026": ("2020-01-01", "2026-10-04"),
}


def evaluate(frame: pd.DataFrame, weights: pd.Series) -> dict[str, object]:
    applied = weights.shift(1).fillna(1.0)
    equity = INITIAL * (
        1.0 + frame["synthetic_tqqq_return"] * applied
    ).cumprod()
    period_start = float(equity.iloc[0])
    period_end = float(equity.iloc[-1])
    years = max(
        (frame.index[-1] - frame.index[0]).days / 365.25,
        1 / 365.25,
    )
    relative = period_end / period_start
    dd = equity / equity.cummax() - 1.0
    return {
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "end_over_start": relative,
        "cagr": relative ** (1.0 / years) - 1.0,
        "max_drawdown": float(dd.min()),
        "average_exposure": float(applied.mean()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build_composite_frame()
    rows = []

    for period, (start, end) in PERIODS.items():
        sliced = frame.loc[start:end].copy()
        strategies = {
            "BUY_AND_HOLD": pd.Series(1.0, index=sliced.index)
        }
        for exposure in EXPOSURES:
            strategies[f"COMPOSITE_STRUCTURAL_{int(exposure * 100)}"] = (
                composite_weights(sliced, exposure)
            )

        for strategy, weights in strategies.items():
            row = evaluate(sliced, weights)
            row.update({"period": period, "strategy": strategy})
            rows.append(row)

    result = pd.DataFrame(rows).sort_values(["period", "cagr"], ascending=[True, False])
    result.to_csv(
        OUT / "tqqq_composite_structural_defense_chronological.csv",
        index=False,
    )
    print(result.to_string(index=False))
    print("\nChronological robustness report completed.")


if __name__ == "__main__":
    main()
