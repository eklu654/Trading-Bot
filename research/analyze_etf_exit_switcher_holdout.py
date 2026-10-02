"""Chronological holdout gate for ETF-exit switcher daily paths."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPLITS = {"TRAIN": ("2010-01-01", "2018-12-31"), "VALIDATION": ("2019-01-01", "2022-12-31"), "HOLDOUT": ("2023-01-01", "2099-12-31")}


def split_metrics(frame: pd.DataFrame, capital: float = 5000.0, minimum_option_days: int = 20) -> pd.DataFrame:
    required = {"Date", "portfolio_return", "selector_return", "selector_pnl"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Switcher path missing columns: {sorted(missing)}")
    work = frame.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    work = work.sort_values("Date").set_index("Date")
    rows = []
    for split, (start, end) in SPLITS.items():
        part = work.loc[start:end]
        if part.empty:
            rows.append({"split": split, "observations": 0, "option_realized_days": 0, "option_pnl": 0.0, "selector_ending_equity": capital, "etf_ending_equity": capital, "incremental_vs_etf": 0.0, "sample_status": "NO_DATA"})
            continue
        selector_equity = capital * (1.0 + part["selector_return"]).cumprod()
        etf_equity = capital * (1.0 + part["portfolio_return"]).cumprod()
        source = part.get("selector_source", pd.Series(index=part.index, dtype=str))
        option_days = int((source == "OPTIONS_REALIZED").sum())
        rows.append({"split": split, "observations": int(len(part)), "option_realized_days": option_days, "option_pnl": float(part["selector_pnl"].sum()), "selector_ending_equity": float(selector_equity.iloc[-1]), "etf_ending_equity": float(etf_equity.iloc[-1]), "incremental_vs_etf": float(selector_equity.iloc[-1] - etf_equity.iloc[-1]), "sample_status": "SUFFICIENT_FOR_OBSERVATIONAL_REVIEW" if option_days >= minimum_option_days else "INSUFFICIENT_OPTION_SAMPLE"})
    return pd.DataFrame(rows)


def discover_paths(input_glob: str) -> list[Path]:
    paths = sorted((ROOT / "data" / "research").glob(input_glob))
    paths = [p for p in paths if not p.name.endswith("_summary.csv")]
    if not paths:
        raise FileNotFoundError(f"No switcher daily paths matched {input_glob!r}")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-glob", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--capital", type=float, default=5000.0)
    parser.add_argument("--minimum-option-days", type=int, default=20)
    args = parser.parse_args()
    rows = []
    for path in discover_paths(args.input_glob):
        metrics = split_metrics(pd.read_csv(path), args.capital, args.minimum_option_days)
        metrics.insert(0, "source_file", path.name)
        rows.append(metrics)
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(ROOT / args.output, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
