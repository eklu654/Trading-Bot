"""Granular ETF-001 cash-allocation sensitivity runner.

This research runner deliberately keeps strategy parameters fixed and varies
only the strategic cash target. It is intended to answer whether conclusions
about ETF-001 depend materially on the coarse 0/10/25/50/100% sweep.

No candidate is selected here. Train/validation/holdout selection belongs in a
separate evaluator. The script writes descriptive metrics for BUY_AND_HOLD,
DMA, and DMA_VIX at each cash level.

Run from repository root:
    python research/analyze_etf001_cash_allocation.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .backtest_etf001 import (
        backtest,
        load_prices,
        load_vix,
        overall_summary,
    )
except ImportError:
    from backtest_etf001 import backtest, load_prices, load_vix, overall_summary


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
OUTPUT_DIR = DATA_DIR

# Deliberately denser around the existing 25% reference point while retaining
# the extreme controls. This is a sensitivity study, not an optimization grid.
CASH_LEVELS = (
    0.00,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
    0.50,
    0.60,
    0.75,
    1.00,
)

SPLITS = {
    "full": ("1900-01-01", "2099-12-31"),
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}


def split_summary(frame: pd.DataFrame, start: str, end: str) -> dict:
    part = frame.loc[start:end]
    if part.empty:
        return {"observations": 0}
    summary = overall_summary(part).iloc[0].to_dict()
    summary["observations"] = len(part)
    # Convert a $5,000 starting account into a descriptive endpoint only.
    # This does not model order sizing, tax, interest, or broker constraints.
    summary["ending_value_5000"] = 5000.0 * float(part["portfolio_value"].iloc[-1])
    return summary


def main() -> None:
    prices = load_prices()
    vix = load_vix()
    rows: list[dict] = []

    for cash in CASH_LEVELS:
        for strategy, overlay, buy_and_hold in (
            ("BUY_AND_HOLD", False, True),
            ("DMA", False, False),
            ("DMA_VIX", True, False),
        ):
            # The all-cash control is represented by the production backtest
            # separately, because BUY_AND_HOLD/DMA otherwise have no sleeves.
            if cash == 1.0:
                frame = pd.DataFrame(
                    {
                        "portfolio_return": 0.0,
                        "portfolio_value": 1.0,
                        "drawdown": 0.0,
                        "invested_weight": 0.0,
                    },
                    index=prices[next(iter(prices))].index,
                )
            else:
                frame = backtest(
                    prices,
                    vix,
                    use_vix_overlay=overlay,
                    cash_allocation=cash,
                    buy_and_hold=buy_and_hold,
                )

            for split, (start, end) in SPLITS.items():
                metrics = split_summary(frame, start, end)
                rows.append(
                    {
                        "strategy": strategy,
                        "cash_allocation": cash,
                        "cash_percent": int(round(cash * 100)),
                        "split": split,
                        **metrics,
                    }
                )

    result = pd.DataFrame(rows)
    result.to_csv(
        OUTPUT_DIR / "etf001_cash_allocation_sensitivity.csv",
        index=False,
    )

    # A compact control table makes it easier to compare the 25% reference
    # against neighboring cash levels without silently ranking candidates.
    controls = result[
        (result["split"] == "holdout")
        & result["cash_allocation"].isin((0.0, 0.25, 0.5, 0.75, 1.0))
    ].copy()
    controls.to_csv(
        OUTPUT_DIR / "etf001_cash_allocation_sensitivity_controls.csv",
        index=False,
    )

    print("=== ETF-001 CASH-ALLOCATION SENSITIVITY ===")
    print(result.to_string(index=False))
    print("\n=== HOLDOUT CONTROLS ===")
    print(
        controls[
            [
                "strategy",
                "cash_percent",
                "total_return",
                "annualized_return",
                "max_drawdown",
                "sharpe_no_risk_free",
                "sortino_no_risk_free",
                "ending_value_5000",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
