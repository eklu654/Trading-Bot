#!/usr/bin/env python3
"""Attribute the frozen 0DTE control set to fixed VIX regimes.

This is descriptive attribution, not a strategy optimizer. The VIX buckets are
predeclared and the control set is frozen to the four controls from the
chronological validation document.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

CONTROLS = {
    "IC_16D_6D_1555": "Iron condor 16D/6D, 15:55",
    "IC_16D_6D_1500": "Iron condor 16D/6D, 15:00",
    "PUT_16D_6D_1555": "Put credit 16D/6D, 15:55",
    "CALL_16D_6D_1555": "Call credit 16D/6D, 15:55",
}
VIX_BINS = [-1.0, 15.0, 20.0, 25.0, 30.0, float("inf")]
VIX_LABELS = ["<15", "15-20", "20-25", "25-30", ">=30"]
SPLITS = {
    "TRAIN": ("2022-06-16", "2024-12-31"),
    "VALIDATION": ("2025-01-01", "2025-12-31"),
    "HOLDOUT": ("2026-01-01", "2026-09-28"),
}


def load_days(path: Path) -> dict[str, pd.DataFrame]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, pd.DataFrame] = {}
    for cfg in data["configs"]:
        if cfg["name"] not in CONTROLS:
            continue
        frame = pd.DataFrame(cfg["result"]["results"]["days"])
        frame["date"] = pd.to_datetime(frame["date"])
        frame["net_pnl"] = pd.to_numeric(frame["net_pnl"])
        out[cfg["name"]] = frame[["date", "net_pnl"]]
    missing = set(CONTROLS) - set(out)
    if missing:
        raise ValueError(f"Missing frozen controls: {sorted(missing)}")
    return out


def load_vix(path: Path) -> pd.Series:
    frame = pd.read_csv(path, parse_dates=["Date"])
    if "vix" not in frame.columns:
        raise ValueError("VIX file must contain Date and vix columns.")
    return frame.set_index("Date")["vix"].sort_index()


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["split"] = "FULL_SAMPLE"
    for label, (start, end) in SPLITS.items():
        mask = frame["date"].between(pd.Timestamp(start), pd.Timestamp(end))
        frame.loc[mask, "split"] = label

    frame["vix_bucket"] = pd.cut(
        frame["vix"], bins=VIX_BINS, labels=VIX_LABELS, right=False
    )
    rows = []
    for (split, bucket), group in frame.dropna(subset=["vix_bucket"]).groupby(
        ["split", "vix_bucket"], observed=True
    ):
        rows.append(
            {
                "split": split,
                "vix_bucket": str(bucket),
                "sessions": len(group),
                "net_pnl": group["net_pnl"].sum(),
                "mean_daily_pnl": group["net_pnl"].mean(),
                "win_rate": (group["net_pnl"] > 0).mean(),
                "worst_day": group["net_pnl"].min(),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("timing_json", type=Path)
    parser.add_argument("vix_csv", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    vix = load_vix(args.vix_csv)
    days = load_days(args.timing_json)
    rows = []
    for control, description in CONTROLS.items():
        frame = days[control].merge(
            vix.rename("vix"), left_on="date", right_index=True, how="left"
        )
        missing = int(frame["vix"].isna().sum())
        result = summarize(frame)
        result.insert(0, "control", control)
        result.insert(1, "description", description)
        result["missing_vix_sessions"] = missing
        rows.append(result)

    out = pd.concat(rows, ignore_index=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.output, index=False)

    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
