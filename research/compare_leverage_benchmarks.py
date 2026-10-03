"""Compare deterministic leveraged-ETF controls, including technology-heavy 3x baselines.

This research companion uses the same daily dataset and next-session execution.
No parameters are optimized here. The explicit 2018-2025 slice is included
because the technology/semiconductor 3x controls are materially different
benchmarks from broad-market SPXL.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from research.backtest_dynamic_leverage import build_features, backtest, load, MA_WINDOW

OUTPUT_DIR = ROOT / "data" / "research"
STARTING_CAPITAL = 5000.0
COMMON_START = pd.Timestamp("2010-01-01")
COMMON_END = pd.Timestamp("2026-09-25")
COMPARISON_START = pd.Timestamp("2018-01-01")
COMPARISON_END = pd.Timestamp("2025-12-31")


def static_hold(symbol: str, index: pd.DatetimeIndex) -> pd.DataFrame:
    price = load(symbol)["adj_close"].reindex(index)
    daily = price.pct_change().fillna(0.0)
    return pd.DataFrame({"portfolio_return": daily}, index=index)


def dma_cash(symbol: str, index: pd.DatetimeIndex) -> pd.DataFrame:
    price = load(symbol)["adj_close"].reindex(index)
    signal_price = price.shift(1)
    ma = price.rolling(MA_WINDOW).mean().shift(1)
    daily = price.pct_change().fillna(0.0)
    held = (signal_price >= ma).fillna(False)
    return pd.DataFrame(
        {"portfolio_return": daily.where(held, 0.0), "held": held}, index=index
    )


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    equity = (1.0 + daily).cumprod()
    total = equity.iloc[-1] - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    sharpe = daily.mean() / daily.std(ddof=1) * np.sqrt(252) if daily.std(ddof=1) else np.nan
    sortino = daily.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside else np.nan
    drawdown = equity / equity.cummax() - 1.0
    return {
        "strategy": label,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "total_return": total,
        "ending_balance_5000": STARTING_CAPITAL * equity.iloc[-1],
        "annualized_return": (1 + total) ** (1 / years) - 1,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": drawdown.min(),
        "worst_day": daily.min(),
    }


def main() -> None:
    features = build_features()
    dynamic = backtest(features)
    index = features.index

    strategies: dict[str, pd.DataFrame] = {
        "static_spy_1x": static_hold("SPY", index),
        "static_sso_2x": static_hold("SSO", index),
        "static_spxl_3x": static_hold("SPXL", index),
        "static_tqqq_3x": static_hold("TQQQ", index),
        "static_soxl_3x": static_hold("SOXL", index),
        "spy_200dma_cash": dma_cash("SPY", index),
        "sso_200dma_cash": dma_cash("SSO", index),
        "spxl_200dma_cash": dma_cash("SPXL", index),
        "tqqq_200dma_cash": dma_cash("TQQQ", index),
        "soxl_200dma_cash": dma_cash("SOXL", index),
        "dynamic_family_leverage": dynamic,
    }

    def build_summary(frame_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
        rows = [
            summarize(frame.dropna(subset=["portfolio_return"]), label)
            for label, frame in frame_map.items()
        ]
        return pd.DataFrame(rows)

    common_map = {label: frame.loc[COMMON_START:COMMON_END].copy() for label, frame in strategies.items()}
    full = build_summary({label: frame for label, frame in common_map.items() if not frame.empty})
    full.to_csv(OUTPUT_DIR / "leverage_strategy_comparison.csv", index=False)

    start = COMPARISON_START
    end = COMPARISON_END
    slice_map = {
        label: frame.loc[start:end].copy() for label, frame in strategies.items()
    }
    period = build_summary({label: frame for label, frame in slice_map.items() if not frame.empty})
    period.to_csv(OUTPUT_DIR / "leverage_strategy_comparison_2018_2025.csv", index=False)

    print(f"Common-period comparison ({COMMON_START.date()} through {COMMON_END.date()})")
    print(full.to_string(index=False))
    print("\n2018-2025 comparison")
    print(period.to_string(index=False))
    print("\n$5,000 2018-2025 ending balances")
    print(period[["strategy", "ending_balance_5000"]].to_string(index=False))
    print("\nArtifacts:")
    print(OUTPUT_DIR / "leverage_strategy_comparison.csv")
    print(OUTPUT_DIR / "leverage_strategy_comparison_2018_2025.csv")


if __name__ == "__main__":
    main()
