"""ETF-001 trend/hysteresis matrix with chronological validation splits.

The sweep is deliberately a candidate generator, not a full-history optimizer.
Every candidate is reported separately on train, validation, and untouched
holdout periods. Holdout performance is not used for selection.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .backtest_etf001 import (
        SYMBOLS,
        build_common_frame,
        load_prices,
        load_vix,
        overall_summary,
    )
except ImportError:
    from backtest_etf001 import (
        SYMBOLS,
        build_common_frame,
        load_prices,
        load_vix,
        overall_summary,
    )

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
OUTPUT_DIR = DATA_DIR

MA_WINDOWS = (100, 125, 150, 175, 200, 225, 250)
EXIT_BUFFERS = (0.0, 0.01, 0.02)
REENTRY_BUFFERS = (0.0, 0.01, 0.02)
REENTRY_SESSIONS = (1, 3, 5)
CASH_ALLOCATION = 0.25

SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}


def generate_signal(close, ma_window, exit_buffer, reentry_buffer, reentry_sessions):
    ma = close.rolling(ma_window, min_periods=ma_window).mean().to_numpy()
    prices = close.to_numpy(dtype=float)
    signal = np.zeros(len(close), dtype=bool)
    active = False
    above = 0
    exit_level = 1.0 - exit_buffer
    entry_level = 1.0 + reentry_buffer

    for i, (price, average) in enumerate(zip(prices, ma)):
        if np.isnan(average) or price < average * exit_level:
            active, above = False, 0
        elif not active:
            if price >= average * entry_level:
                above += 1
                if above >= reentry_sessions:
                    active = True
            else:
                above = 0
        signal[i] = active

    return pd.Series(signal, index=close.index)


def backtest_candidate(prices, vix, ma_window, exit_buffer, reentry_buffer, reentry_sessions):
    common = build_common_frame(prices, vix)
    sleeve = (1.0 - CASH_ALLOCATION) / len(SYMBOLS)
    holdings = pd.DataFrame({
        symbol: generate_signal(
            common[symbol], ma_window, exit_buffer, reentry_buffer, reentry_sessions
        ).shift(1).fillna(False)
        for symbol in SYMBOLS
    }, index=common.index)

    total_return_prices = pd.concat({
        symbol: prices[symbol]["adj_close"] if "adj_close" in prices[symbol].columns
        else prices[symbol]["close"]
        for symbol in SYMBOLS
    }, axis=1).reindex(common.index)
    returns = total_return_prices.pct_change().fillna(0.0)
    daily = sum(sleeve * returns[symbol] * holdings[symbol].astype(float) for symbol in SYMBOLS)
    equity = (1.0 + daily).cumprod()
    out = pd.DataFrame({"portfolio_return": daily, "portfolio_value": equity}, index=common.index)
    out["drawdown"] = equity / equity.cummax() - 1.0
    out["invested_weight"] = holdings.sum(axis=1) * sleeve
    return out


def split_summary(frame, start, end):
    part = frame.loc[start:end]
    if part.empty:
        return {"observations": 0}
    summary = overall_summary(part).iloc[0].to_dict()
    summary["observations"] = len(part)
    return summary


def main():
    prices, vix = load_prices(), load_vix()
    rows = []
    for window in MA_WINDOWS:
        for exit_buffer in EXIT_BUFFERS:
            for reentry_buffer in REENTRY_BUFFERS:
                for sessions in REENTRY_SESSIONS:
                    frame = backtest_candidate(
                        prices, vix, window, exit_buffer, reentry_buffer, sessions
                    )
                    row = {
                        "ma_window": window,
                        "exit_buffer": exit_buffer,
                        "reentry_buffer": reentry_buffer,
                        "reentry_sessions": sessions,
                    }
                    for split, (start, end) in SPLITS.items():
                        metrics = split_summary(frame, start, end)
                        for key in (
                            "total_return", "annualized_return", "max_drawdown",
                            "sharpe_no_risk_free", "sortino_no_risk_free",
                            "annualized_volatility", "mean_invested_weight",
                        ):
                            row[f"{split}_{key}"] = metrics.get(key, np.nan)
                        row[f"{split}_observations"] = metrics.get("observations", 0)
                    dd = abs(row["train_max_drawdown"])
                    row["train_return_drawdown_ratio"] = (
                        row["train_annualized_return"] / dd if dd > 0 else np.nan
                    )
                    rows.append(row)

    result = pd.DataFrame(rows).sort_values(
        ["train_return_drawdown_ratio", "train_sharpe_no_risk_free"],
        ascending=False,
    )
    result.to_csv(OUTPUT_DIR / "etf001_trend_matrix.csv", index=False)
    result.head(25).to_csv(OUTPUT_DIR / "etf001_trend_matrix_top25_train.csv", index=False)
    print(result.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
