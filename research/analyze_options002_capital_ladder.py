"""Consolidate OPTIONS-002 capital-ladder feasibility outputs.

This script does not choose a trading configuration. It creates a normalized
comparison across strategy labels, capital checkpoints, regime candidates,
fill assumptions, and risk budgets.

It tolerates missing files so partially completed research remains inspectable.
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
OUT = DATA_DIR / "options002_capital_ladder_analysis.csv"

PATTERN = re.compile(
    r"options002_(?P<label>.+)_(?P<candidate>all_days|broad_sideways|turbulent_only)_"
    r"(?P<fill>conservative|mid)_account_(?P<nlv>\d+)_risk_(?P<risk>[0-9.]+)_summary\.csv$"
)


def main() -> None:
    rows = []
    for path in sorted(DATA_DIR.glob("options002_*_account_*_risk_*_summary.csv")):
        match = PATTERN.fullmatch(path.name)
        if not match:
            continue
        summary = pd.read_csv(path)
        if len(summary) != 1:
            raise RuntimeError(f"Expected exactly one summary row: {path}")
        row = summary.iloc[0].to_dict()
        row.update({
            "source_file": path.name,
            "strategy_label": match.group("label"),
            "candidate": match.group("candidate").upper(),
            "fill_model": match.group("fill"),
            "starting_nlv": float(match.group("nlv")),
            "risk_limit": float(match.group("risk")),
        })
        rows.append(row)

    columns = [
        "source_file", "strategy_label", "candidate", "fill_model",
        "starting_nlv", "risk_limit", "candidate_count", "accepted_count",
        "rejected_count", "ending_nlv", "total_net_pnl", "win_rate",
        "worst_trade", "max_defined_loss", "max_loss_pct", "max_bpr_pct",
    ]
    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in out:
                out[col] = pd.NA
        out = out[columns].sort_values(
            ["strategy_label", "starting_nlv", "candidate", "fill_model", "risk_limit"]
        )

    out.to_csv(OUT, index=False)
    print("=== OPTIONS-002 CAPITAL LADDER ===")
    if out.empty:
        print("No matching feasibility summaries found yet.")
    else:
        print(out.to_string(index=False))
        print(f"rows={len(out)}")


if __name__ == "__main__":
    main()
