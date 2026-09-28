"""Historical ETF-001 backtest and regime-conditioned analysis.

This script consumes data produced by build_historical_regime_dataset.py.
It models the strategy at daily close with next-session execution, so a
signal observed on day t affects holdings beginning on day t+1.

Run from repository root:
    python research/backtest_etf001.py

The VIX overlay is parameterized rather than hard-coded as a final rule.
The default exit threshold is 28.0. Re-entry requires VIX to be below the
configured re-entry threshold AND the underlying's normal 200-DMA/5-session
re-entry condition. This prevents the overlay from silently being treated as
validated.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
OUTPUT_DIR = DATA_DIR

SYMBOLS = ("TQQQ", "SPXL", "SOXL")
SLEEVE_WEIGHT = 0.25
VIX_EXIT = 28.0
VIX_REENTRY = 20.0
REENTRY_SESSIONS = 5


def load_prices() -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        path = DATA_DIR / f"{symbol.lower()}_daily.csv"
        frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
        result[symbol] = frame.sort_index()
    return result


def load_regime() -> pd.DataFrame:
    path = DATA_DIR / "historical_regime_dataset.csv"
    return pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()


def load_vix() -> pd.Series:
    path = DATA_DIR / "vix_daily.csv"
    frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    return frame["vix"]


def build_common_frame(
    prices: dict[str, pd.DataFrame], vix: pd.Series
) -> pd.DataFrame:
    closes = pd.concat(
        {symbol: prices[symbol]["close"] for symbol in SYMBOLS}, axis=1
    )
    closes["vix"] = vix
    return closes.dropna(subset=list(SYMBOLS)).ffill()


def generate_signals(
    close: pd.Series,
    vix: pd.Series,
    use_vix_overlay: bool,
    vix_exit: float = VIX_EXIT,
    vix_reentry: float = VIX_REENTRY,
    reentry_sessions: int = REENTRY_SESSIONS,
) -> pd.DataFrame:
    """Create end-of-day signals for one ETF."""

    ma200 = close.rolling(200, min_periods=200).mean()
    normal_hold = pd.Series(False, index=close.index)

    active = False
    above_count = 0
    for date in close.index:
        ma = ma200.loc[date]
        price = close.loc[date]

        if pd.isna(ma) or price < ma:
            active = False
            above_count = 0
        elif not active:
            above_count += 1
            if above_count >= reentry_sessions:
                active = True

        normal_hold.loc[date] = active

    if not use_vix_overlay:
        hold = normal_hold
    else:
        vix_hold = pd.Series(True, index=close.index)
        overlay_active = False

        for date in close.index:
            value = vix.loc[date]
            if pd.isna(value):
                vix_hold.loc[date] = False
                continue

            if value >= vix_exit:
                overlay_active = True
            elif overlay_active and value < vix_reentry:
                overlay_active = False

            vix_hold.loc[date] = not overlay_active

        hold = normal_hold & vix_hold

    return pd.DataFrame(
        {
            "close": close,
            "ma200": ma200,
            "normal_hold": normal_hold,
            "hold_signal": hold,
            "vix": vix,
        }
    )


def backtest(
    prices: dict[str, pd.DataFrame],
    vix: pd.Series,
    use_vix_overlay: bool,
) -> pd.DataFrame:
    common = build_common_frame(prices, vix)

    signals = {
        symbol: generate_signals(
            common[symbol],
            common["vix"],
            use_vix_overlay=use_vix_overlay,
        )
        for symbol in SYMBOLS
    }

    returns = common[list(SYMBOLS)].pct_change().fillna(0.0)

    # Today's close determines tomorrow's holding.
    holdings = pd.DataFrame(
        {
            symbol: signals[symbol]["hold_signal"].shift(1).fillna(False)
            for symbol in SYMBOLS
        },
        index=common.index,
    )

    portfolio_returns = sum(
        0.25 * returns[symbol] * holdings[symbol].astype(float)
        for symbol in SYMBOLS
    )

    equity = (1.0 + portfolio_returns).cumprod()
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0

    out = pd.DataFrame(
        {
            "portfolio_return": portfolio_returns,
            "portfolio_value": equity,
            "drawdown": drawdown,
            "vix": common["vix"],
        },
        index=common.index,
    )

    for symbol in SYMBOLS:
        out[f"{symbol}_hold"] = holdings[symbol]
        out[f"{symbol}_close"] = common[symbol]
        out[f"{symbol}_signal"] = signals[symbol]["hold_signal"]

    out["active_sleeves"] = sum(
        out[f"{symbol}_hold"].astype(int) for symbol in SYMBOLS
    )
    out["invested_weight"] = out["active_sleeves"] * 0.25
    out["cash_weight"] = 1.0 - out["invested_weight"]

    return out


def regime_summary(backtest_frame: pd.DataFrame, regime: pd.DataFrame) -> pd.DataFrame:
    joined = backtest_frame.join(regime[["decision_regime"]], how="left")
    joined = joined.dropna(subset=["decision_regime"])

    rows = []
    for label, group in joined.groupby("decision_regime"):
        daily = group["portfolio_return"]
        cumulative = (1.0 + daily).prod() - 1.0
        volatility = daily.std(ddof=1) * np.sqrt(252)
        downside_std = daily.where(daily < 0).std(ddof=1)

        local_equity = (1.0 + daily).cumprod()
        local_drawdown = local_equity / local_equity.cummax() - 1.0

        rows.append(
            {
                "regime": label,
                "observations": len(group),
                "cumulative_return": cumulative,
                "annualized_volatility": volatility,
                "mean_daily_return": daily.mean(),
                "downside_deviation": (
                    downside_std * np.sqrt(252)
                    if pd.notna(downside_std)
                    else np.nan
                ),
                "worst_day": daily.min(),
                "mean_invested_weight": group["invested_weight"].mean(),
                "max_drawdown_within_regime": local_drawdown.min(),
            }
        )

    return pd.DataFrame(rows).sort_values("regime")


def overall_summary(frame: pd.DataFrame) -> pd.DataFrame:
    daily = frame["portfolio_return"]
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    total = frame["portfolio_value"].iloc[-1] - 1.0
    annualized = (1.0 + total) ** (1.0 / years) - 1.0
    volatility = daily.std(ddof=1) * np.sqrt(252)
    daily_std = daily.std(ddof=1)
    sharpe = daily.mean() / daily_std * np.sqrt(252) if daily_std > 0 else np.nan
    downside_std = daily.where(daily < 0).std(ddof=1)
    sortino = (
        daily.mean() / downside_std * np.sqrt(252)
        if pd.notna(downside_std) and downside_std > 0
        else np.nan
    )

    return pd.DataFrame(
        [
            {
                "start": frame.index.min(),
                "end": frame.index.max(),
                "total_return": total,
                "annualized_return": annualized,
                "max_drawdown": frame["drawdown"].min(),
                "annualized_volatility": volatility,
                "sharpe_no_risk_free": sharpe,
                "sortino_no_risk_free": sortino,
                "profitable_days": (daily > 0).mean(),
                "mean_invested_weight": frame["invested_weight"].mean(),
            }
        ]
    )


def main() -> None:
    prices = load_prices()
    vix = load_vix()
    regime = load_regime()

    dma = backtest(prices, vix, use_vix_overlay=False)
    dma_vix = backtest(prices, vix, use_vix_overlay=True)

    dma.to_csv(OUTPUT_DIR / "etf001_dma_backtest.csv")
    dma_vix.to_csv(OUTPUT_DIR / "etf001_dma_vix_backtest.csv")

    regime_summary(dma, regime).to_csv(
        OUTPUT_DIR / "etf001_dma_regime_summary.csv", index=False
    )
    regime_summary(dma_vix, regime).to_csv(
        OUTPUT_DIR / "etf001_dma_vix_regime_summary.csv", index=False
    )

    combined = pd.concat(
        [
            overall_summary(dma).assign(strategy="ETF-001-DMA"),
            overall_summary(dma_vix).assign(strategy="ETF-001-DMA-VIX"),
        ],
        ignore_index=True,
    )
    combined.to_csv(OUTPUT_DIR / "etf001_overall_summary.csv", index=False)

    print(combined.to_string(index=False))
    print("\\nBacktest artifacts written to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
