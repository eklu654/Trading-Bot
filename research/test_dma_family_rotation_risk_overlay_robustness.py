"""Robustness diagnostics for the family-rotation risk-overlay stage.

The base selector is frozen at DMA-250 / top-2 / 5-session rotation.
This script does not optimize against holdout. It evaluates a small fixed
cluster of risk-overlay settings that survived the initial train/validation
screen across independent calendar eras and transaction-cost stress.

Candidate cluster:
- 30% target, 20-session volatility, DD 20/25/30%
- 30% target, 20-session volatility, DD 15%
- 40% target, 20-session volatility, DD 20/25/30%

The purpose is parameter-neighborhood stability, not another broad search.
"""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.test_dma_family_rotation_risk_overlay import (
    base_weights, build_overlay, apply_costs, summarize
)

DATA_DIR = ROOT / "data" / "research"
CANDIDATES = (
    (30, 20, 15),
    (30, 20, 20),
    (30, 20, 25),
    (30, 20, 30),
    (40, 20, 20),
    (40, 20, 25),
    (40, 20, 30),
)
ERAS = {
    "era_2010_2014": ("2010-03-11", "2014-12-31"),
    "era_2015_2019": ("2015-01-01", "2019-12-31"),
    "era_2020_2022": ("2020-01-01", "2022-12-31"),
    "era_2023_2026": ("2023-01-01", "2026-09-25"),
}
COSTS = (0, 10, 25, 50)  # implementation-friction stress


def main() -> None:
    weights, returns = base_weights()
    rows = []
    for target_pct, lookback, dd_pct in CANDIDATES:
        frame = build_overlay(weights, returns, lookback, target_pct / 100.0, dd_pct / 100.0)
        label = f"RISK_V{target_pct}_L{lookback}_DD{dd_pct}"
        for era, (start, end) in ERAS.items():
            segment = frame.loc[start:end]
            row = summarize(segment, label, era)
            row["cost_bps"] = 0
            rows.append(row)
            for cost in COSTS[1:]:
                stressed = apply_costs(frame, cost).loc[start:end]
                row = summarize(stressed, label, era)
                row["cost_bps"] = cost
                rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(DATA_DIR / "dma_family_rotation_risk_overlay_robustness.csv", index=False)

    # Compact stability report: count eras remaining positive at each cost.
    report = (
        out.groupby(["strategy", "cost_bps"])
        .agg(
            positive_eras=("cagr", lambda s: int((s > 0).sum())),
            min_era_cagr=("cagr", "min"),
            median_era_cagr=("cagr", "median"),
            max_era_cagr=("cagr", "max"),
            worst_drawdown=("max_drawdown", "min"),
        )
        .reset_index()
        .sort_values(["cost_bps", "positive_eras", "median_era_cagr"], ascending=[True, False, False])
    )
    report.to_csv(DATA_DIR / "dma_family_rotation_risk_overlay_robustness_summary.csv", index=False)

    print("=== RISK OVERLAY ERA ROBUSTNESS ===")
    print(out.to_string(index=False))
    print("\n=== RISK OVERLAY ROBUSTNESS SUMMARY ===")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
