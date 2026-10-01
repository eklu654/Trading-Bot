"""Common-date comparison of OPTIONS-002 candidates against ETF-001.

This comparison is descriptive and does not select a winner. It rebuilds ETF-001
from raw price data instead of trusting a potentially stale scaffold artifact.

Run from repository root:
    python research/compare_options002_etf001_common_dates.py

Inputs:
  data/research/{tqqq,spxl,soxl,vix}_daily.csv
  data/research/options002_delta20_*_all_days_{conservative,mid}.csv

The 2023-onward period is the existing chronological holdout and is reported
without parameter optimization.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
OUT = DATA

ETF_SYMBOLS = ("TQQQ", "SPXL", "SOXL")
CASH = 0.25
MA_WINDOW = 200
REENTRY_SESSIONS = 5


def load_inputs():
    prices = {}
    for symbol in ETF_SYMBOLS:
        prices[symbol] = (
            pd.read_csv(DATA / f"{symbol.lower()}_daily.csv", parse_dates=["Date"])
            .set_index("Date")
            .sort_index()
        )
    vix = (
        pd.read_csv(DATA / "vix_daily.csv", parse_dates=["Date"])
        .set_index("Date")["vix"]
        .sort_index()
    )
    return prices, vix


def signal(close: pd.Series) -> pd.Series:
    ma = close.rolling(MA_WINDOW, min_periods=MA_WINDOW).mean()
    active = False
    above = 0
    out = []
    for date in close.index:
        value = close.loc[date]
        mean = ma.loc[date]
        if pd.isna(mean) or value < mean:
            active = False
            above = 0
        elif not active:
            above += 1
            if above >= REENTRY_SESSIONS:
                active = True
        out.append(active)
    return pd.Series(out, index=close.index, dtype=bool)


def rebuild_etf_prices(prices, vix, vix_overlay=False) -> pd.DataFrame:
    close = pd.concat({s: prices[s]["close"] for s in ETF_SYMBOLS}, axis=1)
    close["vix"] = vix
    close = close.dropna(subset=list(ETF_SYMBOLS)).ffill()

    adjusted = pd.concat(
        {s: prices[s]["adj_close"] for s in ETF_SYMBOLS}, axis=1
    ).reindex(close.index)
    returns = adjusted.pct_change().fillna(0.0)

    signals = {s: signal(close[s]) for s in ETF_SYMBOLS}
    if vix_overlay:
        overlay = False
        vix_hold = []
        for date in close.index:
            value = close.loc[date, "vix"]
            if value >= 28.0:
                overlay = True
            elif overlay and value < 20.0:
                overlay = False
            vix_hold.append(not overlay)
        vix_hold = pd.Series(vix_hold, index=close.index, dtype=bool)
        signals = {s: signals[s] & vix_hold for s in ETF_SYMBOLS}

    holdings = pd.DataFrame(
        {s: signals[s].shift(1).fillna(False) for s in ETF_SYMBOLS},
        index=close.index,
    )
    sleeve = (1.0 - CASH) / len(ETF_SYMBOLS)
    portfolio_return = sum(
        sleeve * returns[s] * holdings[s].astype(float) for s in ETF_SYMBOLS
    )
    value = (1.0 + portfolio_return).cumprod()

    result = pd.DataFrame(
        {"portfolio_return": portfolio_return, "portfolio_value": value},
        index=close.index,
    )
    if not np.isfinite(result["portfolio_value"]).all():
        raise ValueError("Rebuilt ETF-001 contains non-finite portfolio values.")
    return result


def compare(candidate_path: Path, etf: pd.DataFrame) -> pd.DataFrame:
    candidates = pd.read_csv(
        candidate_path, parse_dates=["entry_date", "exit_date"]
    )
    candidates = candidates[
        candidates["entry_date"] >= pd.Timestamp("2023-01-01")
    ].copy()

    rows = []
    for row in candidates.itertuples(index=False):
        if row.entry_date not in etf.index or row.exit_date not in etf.index:
            continue
        start = etf.loc[row.entry_date, "portfolio_value"]
        end = etf.loc[row.exit_date, "portfolio_value"]
        etf_return = end / start - 1.0
        risk_return = (
            row.pnl / row.max_defined_loss
            if row.max_defined_loss not in (0, None) and pd.notna(row.max_defined_loss)
            else np.nan
        )
        rows.append(
            {
                "candidate_file": candidate_path.name,
                "entry_date": row.entry_date,
                "exit_date": row.exit_date,
                "option_pnl": row.pnl,
                "max_defined_loss": row.max_defined_loss,
                "option_pnl_per_defined_loss": risk_return,
                "etf_dma_return_same_window": etf_return,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    prices, vix = load_inputs()
    dma = rebuild_etf_prices(prices, vix, vix_overlay=False)
    vix_dma = rebuild_etf_prices(prices, vix, vix_overlay=True)

    files = [
        DATA / f"options002_delta20_{wing}_all_days_{fill}.csv"
        for wing in ("long10d", "w5", "w10")
        for fill in ("conservative", "mid")
    ]

    frames = []
    for path in files:
        frame = compare(path, dma)
        frame["etf_vix_dma_return_same_window"] = np.nan
        for i, row in frame.iterrows():
            frame.loc[i, "etf_vix_dma_return_same_window"] = (
                vix_dma.loc[row["exit_date"], "portfolio_value"]
                / vix_dma.loc[row["entry_date"], "portfolio_value"]
                - 1.0
            )
        frames.append(frame)

    detail = pd.concat(frames, ignore_index=True)
    detail.to_csv(OUT / "options002_etf001_common_date_holdout_detail.csv", index=False)

    summary = (
        detail.groupby("candidate_file", as_index=False)
        .agg(
            matched_trades=("option_pnl", "size"),
            aggregate_option_pnl=("option_pnl", "sum"),
            mean_option_pnl_per_defined_loss=(
                "option_pnl_per_defined_loss", "mean"
            ),
            median_option_pnl_per_defined_loss=(
                "option_pnl_per_defined_loss", "median"
            ),
            mean_etf_dma_return=("etf_dma_return_same_window", "mean"),
            median_etf_dma_return=("etf_dma_return_same_window", "median"),
            mean_etf_vix_dma_return=("etf_vix_dma_return_same_window", "mean"),
        )
    )
    summary.to_csv(OUT / "options002_etf001_common_date_holdout_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
