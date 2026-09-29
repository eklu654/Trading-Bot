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
    cash_allocation: float = 0.25,
    buy_and_hold: bool = False,
) -> pd.DataFrame:
    """Backtest a proportional three-ETF basket with explicit cash.

    Signals are evaluated at close t and applied to close-to-close returns
    beginning at t+1. Buy-and-hold uses initial equal ETF weights and lets
    weights drift; no periodic rebalancing or cash interest is assumed.
    """
    if not 0.0 <= cash_allocation <= 1.0:
        raise ValueError("cash_allocation must be between 0 and 1")

    common = build_common_frame(prices, vix)
    invested_weight = 1.0 - cash_allocation
    sleeve_weight = invested_weight / len(SYMBOLS)

    signals = {
        symbol: generate_signals(
            common[symbol],
            common["vix"],
            use_vix_overlay=use_vix_overlay,
        )
        for symbol in SYMBOLS
    }
    # Use adjusted closes for total-return accounting (dividends/splits), while
    # retaining unadjusted closes for the 200-DMA signal.
    total_return_prices = pd.concat(
        {
            symbol: (
                prices[symbol]["adj_close"]
                if "adj_close" in prices[symbol].columns
                else prices[symbol]["close"]
            )
            for symbol in SYMBOLS
        },
        axis=1,
    ).reindex(common.index)
    returns = total_return_prices.pct_change().fillna(0.0)
    if buy_and_hold:
        holdings = pd.DataFrame(True, index=common.index, columns=SYMBOLS)
    else:
        # Today's close determines tomorrow's holding.
        holdings = pd.DataFrame(
            {
                symbol: signals[symbol]["hold_signal"].shift(1).fillna(False)
                for symbol in SYMBOLS
            },
            index=common.index,
        )

    if buy_and_hold:
        # Buy once at the initial weights; each ETF sleeve then drifts naturally.
        sleeve_growth = (1.0 + returns).cumprod()
        equity = cash_allocation + sleeve_growth.mul(sleeve_weight).sum(axis=1)
        portfolio_returns = equity.pct_change().fillna(0.0)
    else:
        # Rebalance active sleeves to equal target weights at each close.
        portfolio_returns = sum(
            sleeve_weight * returns[symbol] * holdings[symbol].astype(float)
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
    out["invested_weight"] = out["active_sleeves"] * sleeve_weight
    out["cash_weight"] = 1.0 - out["invested_weight"]
    out["cash_allocation_target"] = cash_allocation
    out["strategy_type"] = "BUY_AND_HOLD" if buy_and_hold else (
        "DMA_VIX" if use_vix_overlay else "DMA"
    )
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
    cash_levels = (0.0, 0.10, 0.25, 0.50, 1.0)

    summaries = []
    for cash in cash_levels:
        label = f"{int(cash * 100):02d}cash"
        if cash < 1.0:
            buy_hold = backtest(prices, vix, False, cash, buy_and_hold=True)
            buy_hold.to_csv(OUTPUT_DIR / f"etf001_buyhold_{label}_backtest.csv")
            summaries.append(
                overall_summary(buy_hold).assign(
                    strategy="BUY_AND_HOLD", cash_allocation=cash
                )
            )
            for overlay, strategy in ((False, "DMA"), (True, "DMA_VIX")):
                frame = backtest(prices, vix, overlay, cash)
                frame.to_csv(
                    OUTPUT_DIR / f"etf001_{strategy.lower()}_{label}_backtest.csv"
                )
                if cash == 0.25:
                    legacy_name = (
                        "etf001_dma_backtest.csv" if strategy == "DMA"
                        else "etf001_dma_vix_backtest.csv"
                    )
                    frame.to_csv(OUTPUT_DIR / legacy_name)
                summaries.append(
                    overall_summary(frame).assign(
                        strategy=strategy, cash_allocation=cash
                    )
                )
                if cash == 0.25:
                    regime_summary(frame, regime).to_csv(
                        OUTPUT_DIR / f"etf001_{strategy.lower()}_regime_summary.csv",
                        index=False,
                    )
        else:
            cash_returns = pd.Series(0.0, index=prices[SYMBOLS[0]].index)
            cash_frame = pd.DataFrame(
                {
                    "portfolio_return": cash_returns,
                    "portfolio_value": (1.0 + cash_returns).cumprod(),
                    "drawdown": 0.0,
                    "invested_weight": 0.0,
                },
                index=cash_returns.index,
            )
            summaries.append(
                overall_summary(cash_frame).assign(
                    strategy="CASH_ONLY", cash_allocation=1.0
                )
            )

    combined = pd.concat(summaries, ignore_index=True)
    combined.to_csv(OUTPUT_DIR / "etf001_overall_summary.csv", index=False)
    print(combined.to_string(index=False))
    print("\\nBacktest artifacts written to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
