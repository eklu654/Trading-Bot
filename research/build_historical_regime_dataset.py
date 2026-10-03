"""Build the historical SWITCH-001 research dataset.

This script intentionally separates data acquisition, feature construction,
regime labeling, and ETF-001 evaluation. It is a research tool, not a
production trading component.

Run from the repository root:
    python research/build_historical_regime_dataset.py

Dependencies:
    pip install pandas numpy
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
DATA_DIR.mkdir(parents=True, exist_ok=True)

START = "2010-01-01"
END = "2026-09-27"

# Stooq provides daily OHLCV history for these U.S. symbols.
PRICE_SYMBOLS = [
    "TQQQ",
    "SQQQ",
    "PSQ",
    "QID",
    "SPXL",
    "SPXS",
    "SH",
    "SDS",
    "SOXL",
    "SOXS",
    "SSG",
    "UDOW",
    "SDOW",
    "DIA",
    "TNA",
    "TZA",
    "IWM",
    "SPY",
    "QQQ",
    "SOXX",
    "QLD",
    "SSO",
    "USD",
]


def read_price(symbol: str) -> pd.DataFrame:
    frame = yf.download(
        symbol,
        start=START,
        end="2026-09-28",
        auto_adjust=False,
        progress=False,
        actions=False,
    )

    if frame.empty:
        raise RuntimeError(f"No price history returned for {symbol}")

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    frame = frame.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    frame["symbol"] = symbol
    return frame.sort_index()


def read_vix() -> pd.DataFrame:
    frame = read_price("^VIX")
    return frame[["close"]].rename(columns={"close": "vix"})


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def adx(frame: pd.DataFrame, window: int = 14) -> pd.Series:
    high = frame["high"]
    low = frame["low"]
    close = frame["close"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=frame.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=frame.index,
    )

    true_range = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.ewm(alpha=1 / window, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / window, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / window, adjust=False).mean() / atr

    denominator = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / denominator
    return dx.ewm(alpha=1 / window, adjust=False).mean()


def efficiency_ratio(close: pd.Series, window: int = 20) -> pd.Series:
    direction = (close - close.shift(window)).abs()
    noise = close.diff().abs().rolling(window).sum()
    return direction / noise.replace(0, np.nan)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    close = out["close"]

    out["sma200"] = sma(close, 200)
    out["sma200_distance"] = close / out["sma200"] - 1
    out["sma200_slope_20"] = out["sma200"].pct_change(20)
    out["adx14"] = adx(out, 14)
    out["er20"] = efficiency_ratio(close, 20)

    returns = close.pct_change()
    out["rv10"] = returns.rolling(10).std() * np.sqrt(252)
    out["rv20"] = returns.rolling(20).std() * np.sqrt(252)
    out["rv60"] = returns.rolling(60).std() * np.sqrt(252)

    out["return20"] = close.pct_change(20)
    out["return60"] = close.pct_change(60)
    out["range20"] = close.rolling(20).max() / close.rolling(20).min() - 1
    out["drawdown252"] = close / close.rolling(252).max() - 1

    return out


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    def pct(x: np.ndarray) -> float:
        if len(x) < 30 or np.isnan(x[-1]):
            return np.nan
        return float((x[:-1] <= x[-1]).mean())

    return series.rolling(window + 1).apply(pct, raw=True)


def build_regime_dataset(
    spy: pd.DataFrame,
    vix: pd.DataFrame,
    qqq: pd.DataFrame,
    soxx: pd.DataFrame,
) -> pd.DataFrame:
    broad = add_features(spy).add_prefix("spy_")
    broad["Date"] = broad.index

    q = add_features(qqq).add_prefix("qqq_")
    q["Date"] = q.index

    s = add_features(soxx).add_prefix("soxx_")
    s["Date"] = s.index

    out = broad.join(q.drop(columns=["Date"]), how="left")
    out = out.join(s.drop(columns=["Date"]), how="left")
    out = out.join(vix, how="left")

    out["vix_percentile252"] = rolling_percentile(out["vix"], 252)
    out["vix_change5"] = out["vix"].pct_change(5)
    out["vix_sma20"] = out["vix"].rolling(20).mean()
    out["vix_above_sma20"] = out["vix"] > out["vix_sma20"]

    # These are candidate research thresholds only. They must be optimized
    # on training data and validated chronologically before production use.
    turbulence = (
        (out["vix_percentile252"] >= 0.80)
        | (out["spy_rv20"] >= out["spy_rv20"].rolling(252).quantile(0.80))
        | (out["vix_change5"] >= 0.25)
    )

    trending = (
        (out["spy_adx14"] >= 25)
        & (out["spy_er20"] >= 0.35)
        & (out["spy_sma200_distance"].abs() >= 0.02)
        & (out["spy_sma200_slope_20"].abs() >= 0.005)
    )

    out["regime"] = np.select(
        [turbulence, trending],
        ["TURBULENT_HIGH_VOL", "TRENDING_NORMAL"],
        default="SIDEWAYS_CHOPPY",
    )

    # One-bar lag for next-session execution.
    out["decision_regime"] = out["regime"].shift(1)

    return out


def simulate_etf(
    prices: dict[str, pd.DataFrame],
    vix: pd.DataFrame,
    use_vix_overlay: bool,
) -> pd.DataFrame:
    merged = pd.concat(
        {
            symbol: prices[symbol]["close"]
            for symbol in ["TQQQ", "SPXL", "SOXL"]
        },
        axis=1,
    ).dropna()

    v = vix.reindex(merged.index)["vix"].ffill()

    states: dict[str, bool] = {}
    above_count: dict[str, int] = {}
    for symbol in merged.columns:
        states[symbol] = True
        above_count[symbol] = 0

    daily = []
    previous_value = 1.0

    for date, row in merged.iterrows():
        for symbol in merged.columns:
            history = prices[symbol]["close"].loc[:date]
            if len(history) < 200:
                states[symbol] = False
                above_count[symbol] = 0
                continue

            ma200 = history.iloc[-200:].mean()
            close = row[symbol]

            if close < ma200:
                states[symbol] = False
                above_count[symbol] = 0
            elif not states[symbol]:
                above_count[symbol] += 1
                if above_count[symbol] >= 5:
                    states[symbol] = True

        # The VIX overlay is measured separately and is intentionally simple:
        # if VIX closes at/above 28, all ETF sleeves are considered ineligible
        # for the next session until their individual rules permit re-entry.
        if use_vix_overlay and v.loc[date] >= 28:
            active = 0
        else:
            active = sum(states.values())

        # Equal 25% sleeve weights plus 25% permanent cash.
        # This is a simplified research accounting model. Execution-level
        # cash, fills, slippage, and dividends must be implemented later.
        if active == 0:
            portfolio_return = 0.0
        else:
            sleeve_returns = row.pct_change()
            # Replace this placeholder with prior-day holdings once the
            # execution simulator is implemented.
            portfolio_return = float(sleeve_returns.mean()) * 0.75

        previous_value *= 1 + (portfolio_return if np.isfinite(portfolio_return) else 0)
        daily.append(
            {
                "Date": date,
                "portfolio_value": previous_value,
                "active_sleeves": active,
                "vix": v.loc[date],
            }
        )

    return pd.DataFrame(daily).set_index("Date")


def main() -> None:
    prices = {symbol: read_price(symbol) for symbol in PRICE_SYMBOLS}
    vix = read_vix()

    for symbol, frame in prices.items():
        frame.to_csv(DATA_DIR / f"{symbol.lower()}_daily.csv")
    vix.to_csv(DATA_DIR / "vix_daily.csv")

    regime = build_regime_dataset(
        prices["SPY"],
        vix,
        prices["QQQ"],
        prices["SOXX"],
    )
    regime.to_csv(DATA_DIR / "historical_regime_dataset.csv")

    # Produce ETF-001 comparison artifacts. This initial function is
    # deliberately marked as a research scaffold because exact execution
    # accounting still needs to be implemented before performance claims
    # are made.
    dma = simulate_etf(prices, vix, use_vix_overlay=False)
    dma_vix = simulate_etf(prices, vix, use_vix_overlay=True)

    dma.to_csv(DATA_DIR / "etf001_dma_scaffold.csv")
    dma_vix.to_csv(DATA_DIR / "etf001_dma_vix_scaffold.csv")

    summary = (
        regime.groupby("decision_regime")
        .agg(
            observations=("regime", "size"),
            first_date=("regime", "first"),
            last_date=("regime", "last"),
        )
        .reset_index()
    )
    summary.to_csv(DATA_DIR / "regime_summary_scaffold.csv", index=False)

    print("Historical regime dataset generated.")
    print(f"Output directory: {DATA_DIR}")


if __name__ == "__main__":
    main()
