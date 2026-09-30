"""Summarize OPTIONS-002 wider-candidate results by regime and chronology.

This is descriptive research only. It does not select a strategy or use holdout
results for optimization. The output is intended to support later common-date
ETF/options comparison.
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

SPLITS = {
    "TRAIN": ("2010-01-01", "2018-12-31"),
    "VALIDATION": ("2019-01-01", "2022-12-31"),
    "HOLDOUT": ("2023-01-01", "2099-12-31"),
}

PATTERN = re.compile(
    r"options002_(?P<label>.+)_(?P<candidate>all_days|broad_sideways|turbulent_only)_"
    r"(?P<fill>conservative|mid)\.csv$"
)


def summarize(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"trades": 0}
    pnl = pd.to_numeric(frame["pnl"], errors="coerce").dropna()
    if pnl.empty:
        return {"trades": 0}
    winners = pnl[pnl > 0]
    losers = pnl[pnl < 0]
    return {
        "trades": int(len(pnl)),
        "total_pnl": float(pnl.sum()),
        "mean_pnl": float(pnl.mean()),
        "win_rate": float((pnl > 0).mean()),
        "worst_trade": float(pnl.min()),
        "best_trade": float(pnl.max()),
        "gross_profit": float(winners.sum()) if not winners.empty else 0.0,
        "gross_loss": float(losers.sum()) if not losers.empty else 0.0,
        "profit_factor": (
            float(winners.sum() / abs(losers.sum()))
            if not losers.empty and losers.sum() != 0
            else None
        ),
    }


def main() -> None:
    rows = []
    files = sorted(DATA_DIR.glob("options002_delta20_*.csv"))
    for path in files:
        match = PATTERN.fullmatch(path.name)
        if not match:
            continue
        frame = pd.read_csv(path, parse_dates=["entry_date"])
        if frame.empty or "pnl" not in frame.columns:
            continue
        base = {
            "source_file": path.name,
            "strategy_label": match.group("label"),
            "candidate": match.group("candidate").upper(),
            "fill_model": match.group("fill"),
        }
        for split, (start, end) in SPLITS.items():
            part = frame[(frame["entry_date"] >= start) & (frame["entry_date"] <= end)]
            rows.append({**base, "split": split, "entry_regime": "ALL", **summarize(part)})
            if "regime" in part.columns:
                for regime, group in part.groupby("regime", dropna=False):
                    rows.append({
                        **base,
                        "split": split,
                        "entry_regime": str(regime),
                        **summarize(group),
                    })

    columns = [
        "source_file", "strategy_label", "candidate", "fill_model", "split",
        "entry_regime", "trades", "total_pnl", "mean_pnl", "win_rate",
        "worst_trade", "best_trade", "gross_profit", "gross_loss", "profit_factor",
    ]
    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in out:
                out[col] = pd.NA
        out = out[columns].sort_values(
            ["strategy_label", "candidate", "fill_model", "split", "entry_regime"]
        )

    out.to_csv(DATA_DIR / "options002_wider_regime_analysis.csv", index=False)
    print("=== OPTIONS-002 WIDER REGIME ANALYSIS ===")
    print(out.to_string(index=False) if not out.empty else "No wider-candidate trade files found.")


if __name__ == "__main__":
    main()
