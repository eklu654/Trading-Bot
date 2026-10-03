"""Measure directional bull/bear ETF opportunity by historical regime.

Evidence only: no parameter optimization and no strategy selection.
Decision regime is lagged by the historical dataset builder. Returns are the
next-session adjusted-close return, so the analysis cannot use the future
session to define the regime.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

PAIRS = {
    "SP500": ("SPXL", "SPXS"),
    "NASDAQ100": ("TQQQ", "SQQQ"),
    "SEMICONDUCTORS": ("SOXL", "SOXS"),
    "DOW30": ("UDOW", "SDOW"),
    "RUSSELL2000": ("TNA", "TZA"),
}

SPLITS = {
    "full": ("2010-01-01", "2026-09-25"),
    "train": ("2010-01-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-09-25"),
}


def load(symbol: str) -> pd.Series:
    path = DATA_DIR / f"{symbol.lower()}_daily.csv"
    frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    column = "adj_close" if "adj_close" in frame.columns else "close"
    return frame[column]


def build_frame() -> pd.DataFrame:
    regime = pd.read_csv(
        DATA_DIR / "historical_regime_dataset.csv", parse_dates=["Date"]
    ).set_index("Date").sort_index()
    out = regime[["decision_regime"]].copy()
    for pair, (bull, bear) in PAIRS.items():
        bull_price = load(bull).reindex(out.index)
        bear_price = load(bear).reindex(out.index)
        out[f"{pair}_bull"] = bull_price.shift(-1) / bull_price - 1.0
        out[f"{pair}_bear"] = bear_price.shift(-1) / bear_price - 1.0
    return out.dropna(subset=["decision_regime"])


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, (start, end) in SPLITS.items():
        segment = frame.loc[start:end]
        for regime, group in segment.groupby("decision_regime"):
            for pair in PAIRS:
                for side in ("bull", "bear"):
                    x = group[f"{pair}_{side}"].dropna()
                    rows.append(
                        {
                            "split": split,
                            "decision_regime": regime,
                            "pair": pair,
                            "side": side,
                            "observations": len(x),
                            "mean_fwd1": float(x.mean()) if len(x) else np.nan,
                            "median_fwd1": float(x.median()) if len(x) else np.nan,
                            "win_rate": float((x > 0).mean()) if len(x) else np.nan,
                            "q05": float(x.quantile(0.05)) if len(x) else np.nan,
                            "worst_day": float(x.min()) if len(x) else np.nan,
                        }
                    )
    return pd.DataFrame(rows)


def main() -> None:
    result = summarize(build_frame())
    path = DATA_DIR / "regime_directional_opportunity.csv"
    result.to_csv(path, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
