#!/usr/bin/env python3
"""Analyze a sanitized 0DTESPX management-timing matrix JSON.

Usage:
    python tools/0dte/analyze_timing_matrix.py path/to/0dte_management_timing_matrix.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    data = load(args.path)
    rows = []

    for cfg in data["configs"]:
        metrics = cfg["result"]["results"]["metrics"]
        rows.append(
            {
                "name": cfg["name"],
                "kind": cfg["kind"],
                "short_delta": cfg["short_delta"],
                "long_delta": cfg["long_delta"],
                "exit": cfg["exit_time"],
                "return_pct": float(metrics["total_return"]) * 100,
                "sharpe": float(metrics["sharpe_annualized"]),
                "sortino": float(metrics["sortino_annualized"]),
                "max_dd_pct": float(metrics["max_drawdown"]) * 100,
                "win_rate_pct": float(metrics["win_rate"]) * 100,
                "profit_factor": float(metrics["profit_factor"]),
                "expectancy": float(metrics["expectancy_per_day"]),
                "worst_day": float(metrics["worst_day"]),
                "fees": float(metrics["fees"]),
                "slippage": float(metrics["slippage"]),
            }
        )

    frame = pd.DataFrame(rows)
    print("\nFULL MATRIX\n")
    print(
        frame.sort_values(["kind", "short_delta", "exit"]).to_string(
            index=False, float_format=lambda x: f"{x:.4f}"
        )
    )

    print("\nBEST BY FULL-SAMPLE RETURN\n")
    print(
        frame.sort_values("return_pct", ascending=False)
        .head(10)
        .to_string(index=False, float_format=lambda x: f"{x:.4f}")
    )

    print("\nAVERAGE BY STRUCTURE / EXIT\n")
    grouped = (
        frame.groupby(["kind", "exit"], as_index=False)[
            ["return_pct", "sharpe", "max_dd_pct", "win_rate_pct", "profit_factor"]
        ]
        .mean()
    )
    print(grouped.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
