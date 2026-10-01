"""Summarize OPTIONS-002 account-feasibility results on the chronological holdout.

This is intentionally descriptive. It does not optimize or select parameters.
It reads the account-feasibility replay outputs and isolates entries on or after
2023-01-01, the project's predefined holdout boundary.

Run from repository root:
    python research/analyze_options002_capital_holdout.py
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
HOLDOUT_START = pd.Timestamp("2023-01-01")


def main() -> None:
    rows = []
    for path in sorted(DATA.glob("options002_*_account_*_risk_*.csv")):
        try:
            df = pd.read_csv(
                path,
                usecols=[
                    "candidate_id",
                    "entry_date",
                    "accepted",
                    "rejection_codes",
                    "pre_trade_nlv",
                    "max_defined_loss",
                    "net_pnl",
                    "post_trade_nlv",
                ],
                parse_dates=["entry_date"],
            )
        except (ValueError, FileNotFoundError):
            continue

        holdout = df[df["entry_date"] >= HOLDOUT_START]
        accepted = holdout[holdout["accepted"] == True]
        rows.append(
            {
                "file": path.name,
                "holdout_candidates": len(holdout),
                "holdout_accepted": len(accepted),
                "holdout_rejected": len(holdout) - len(accepted),
                "holdout_net_pnl": (
                    accepted["net_pnl"].sum() if len(accepted) else 0.0
                ),
                "holdout_ending_nlv": (
                    accepted["post_trade_nlv"].iloc[-1]
                    if len(accepted)
                    else holdout["pre_trade_nlv"].iloc[-1]
                    if len(holdout)
                    else float("nan")
                ),
                "max_defined_loss_seen": (
                    holdout["max_defined_loss"].max()
                    if len(holdout)
                    else float("nan")
                ),
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        raise SystemExit("No account-feasibility replay files were found.")

    out = out.sort_values(
        ["holdout_accepted", "holdout_net_pnl", "file"],
        ascending=[False, False, True],
    )
    output = DATA / "options002_capital_holdout_summary.csv"
    out.to_csv(output, index=False)

    print(out.to_string(index=False))
    print()
    print("2023+ account-feasibility finding:")
    five_k = out[out["file"].str.contains("account_5000_")]
    if len(five_k):
        accepted = int(five_k["holdout_accepted"].sum())
        files = len(five_k)
        print(
            f"$5,000 configurations: {files}; accepted holdout trades across "
            f"all configurations: {accepted}."
        )


if __name__ == "__main__":
    main()
