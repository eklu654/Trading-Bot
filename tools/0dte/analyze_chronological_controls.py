#!/usr/bin/env python3
"""Run the frozen 0DTE control set through chronological train/validation/holdout splits.

This tool intentionally evaluates only the four controls frozen in
docs/02-research/0dte-chronological-validation.md. It does not rank the
controls or optimize any parameter.

The source artifact is the sanitized 0DTESPX timing-matrix JSON. Split return
is defined as the sum of daily net P/L divided by the frozen $100,000 platform
preview starting capital, matching the project's existing validation reports.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

STARTING_CAPITAL = 100_000.0

CONTROLS = (
    "IC_16D_6D_1555",
    "IC_16D_6D_1500",
    "PUT_16D_6D_1555",
    "CALL_16D_6D_1555",
)

SPLITS = (
    ("TRAIN", date(2022, 6, 16), date(2024, 12, 31)),
    ("VALIDATION", date(2025, 1, 1), date(2025, 12, 31)),
    ("HOLDOUT", date(2026, 1, 1), date(2026, 9, 28)),
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_days(data: dict, name: str) -> list[tuple[date, float]]:
    configs = {cfg["name"]: cfg for cfg in data["configs"]}
    if name not in configs:
        raise ValueError(f"Missing frozen control: {name}")

    days = configs[name]["result"]["results"]["days"]
    parsed = sorted(
        (date.fromisoformat(row["date"]), float(row["net_pnl"])) for row in days
    )
    if len(parsed) != 1012:
        raise ValueError(f"{name}: expected 1,012 sessions, found {len(parsed)}")
    if len({day for day, _ in parsed}) != len(parsed):
        raise ValueError(f"{name}: duplicate session dates")
    return parsed


def summarize(rows: list[tuple[date, float]]) -> dict[str, float | int]:
    pnl = [value for _, value in rows]
    cumulative = STARTING_CAPITAL
    peak = STARTING_CAPITAL
    max_drawdown = 0.0

    for value in pnl:
        cumulative += value
        peak = max(peak, cumulative)
        max_drawdown = min(max_drawdown, cumulative / peak - 1.0)

    total = sum(pnl)
    return {
        "sessions": len(pnl),
        "net_pnl": total,
        "return_pct": total / STARTING_CAPITAL * 100.0,
        "win_rate_pct": sum(value > 0 for value in pnl) / len(pnl) * 100.0,
        "avg_daily_pnl": total / len(pnl),
        "best_day": max(pnl),
        "worst_day": min(pnl),
        "max_drawdown_pct": max_drawdown * 100.0,
    }


def evaluate(data: dict) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []

    for control in CONTROLS:
        days = parse_days(data, control)
        for split, start, end in SPLITS:
            subset = [(day, pnl) for day, pnl in days if start <= day <= end]
            expected = {"TRAIN": 597, "VALIDATION": 238, "HOLDOUT": 177}[split]
            if len(subset) != expected:
                raise ValueError(
                    f"{control} {split}: expected {expected} sessions, found {len(subset)}"
                )

            summary = summarize(subset)
            rows.append({"control": control, "split": split, **summary})

    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("timing_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = load(args.timing_json)
    rows = evaluate(data)

    fields = [
        "control",
        "split",
        "sessions",
        "net_pnl",
        "return_pct",
        "win_rate_pct",
        "avg_daily_pnl",
        "best_day",
        "worst_day",
        "max_drawdown_pct",
    ]

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    for row in rows:
        print(
            f"{row['control']} {row['split']}: "
            f"sessions={row['sessions']} "
            f"net_pnl={row['net_pnl']:.2f} "
            f"return={row['return_pct']:.4f}% "
            f"win_rate={row['win_rate_pct']:.2f}% "
            f"worst_day={row['worst_day']:.2f} "
            f"max_dd={row['max_drawdown_pct']:.4f}%"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
