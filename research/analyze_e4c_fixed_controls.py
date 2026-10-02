"""Fixed-control diagnostics for E4c risk-aware Ridge.

No parameters are fitted here. The only controls are the predeclared 1x/2x
leverage caps and the existing SPY 200-DMA / VIX 80th-percentile gates.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_ai_action_selector import DATA_DIR, SPLITS, load
from research.backtest_ai_risk_aware_selector import (
    apply_leverage_cap,
    annual_walk_forward,
    build_features,
    risk_aware_targets,
    summarize,
    backtest,
)

VIX_PERCENTILE = 0.80


def apply_gates(predictions: pd.DataFrame, features: pd.DataFrame, dma: bool, vix: bool) -> pd.DataFrame:
    out = predictions.copy()
    spy = load("SPY")["adj_close"]
    ma200 = spy.rolling(200).mean()
    for date in out.index:
        price = spy.reindex([date]).iloc[0]
        trend = ma200.reindex([date]).iloc[0]
        vix_pct = features["vix_pct"].reindex([date]).iloc[0]
        if (dma and pd.notna(price) and pd.notna(trend) and price < trend) or (
            vix and pd.notna(vix_pct) and vix_pct >= VIX_PERCENTILE
        ):
            out.loc[date, "action"] = "cash"
    return out


def main() -> None:
    features = build_features()
    targets = risk_aware_targets(features.index)
    predictions = annual_walk_forward(features, targets).rename(
        columns={"predicted_score": "predicted_return"}
    )

    policies = {}
    for cap in ("cap_2x", "cap_1x"):
        capped = apply_leverage_cap(predictions, cap)
        policies[f"{cap}_raw"] = capped
        policies[f"{cap}_dma"] = apply_gates(capped, features, True, False)
        policies[f"{cap}_vix"] = apply_gates(capped, features, False, True)
        policies[f"{cap}_both"] = apply_gates(capped, features, True, True)

    rows = []
    for name, policy in policies.items():
        result = backtest(policy)
        for split, (start, end) in SPLITS.items():
            segment = result.loc[start:end]
            if not segment.empty:
                row = summarize(segment, f"E4c_{name}_{split}")
                row["split"] = split
                row["policy"] = name
                rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(DATA_DIR / "e4c_fixed_control_summary.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
