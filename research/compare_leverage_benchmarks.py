"""Compare deterministic leveraged-ETF control strategies.

This research companion keeps the comparison on the same daily dataset and
uses next-session execution. It is intentionally transparent: no optimization
is performed here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from research.backtest_dynamic_leverage import (
    FAMILIES,
    build_features,
    backtest,
    load,
    MA_WINDOW,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "research"


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
    result = pd.DataFrame(
        {
            "portfolio_return": daily.where(held, 0.0),
            "held": held,
        },
        index=index,
    )
    return result


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
        "spy_200dma_cash": dma_cash("SPY", index),
        "sso_200dma_cash": dma_cash("SSO", index),
        "spxl_200dma_cash": dma_cash("SPXL", index),
        "dynamic_family_leverage": dynamic,
    }

    rows: list[dict[str, object]] = []
    for label, frame in strategies.items():
        rows.append(summarize(frame.dropna(subset=["portfolio_return"]), label))

    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT_DIR / "leverage_strategy_comparison.csv", index=False)

    print(summary.to_string(index=False))
    print("\nArtifact:", OUTPUT_DIR / "leverage_strategy_comparison.csv")


if __name__ == "__main__":
    main()
