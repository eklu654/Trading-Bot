"""Deterministic dynamic 1x/2x/3x leveraged-ETF research.

This is a research benchmark, not a production strategy. It deliberately uses
a small predeclared universe and no ML. Signals use information available at
the close of day t and affect returns beginning on t+1.

Universe:
    SPY -> SSO -> SPXL
    QQQ -> QLD -> TQQQ
    SOXX -> USD -> SOXL

The benchmark chooses the strongest underlying by trailing relative strength,
then chooses 0x/1x/2x/3x exposure from broad trend and VIX state.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
OUTPUT_DIR = DATA_DIR

FAMILIES = {
    "SPY": {0: None, 1: "SPY", 2: "SSO", 3: "SPXL"},
    "QQQ": {0: None, 1: "QQQ", 2: "QLD", 3: "TQQQ"},
    "SOXX": {0: None, 1: "SOXX", 2: "USD", 3: "SOXL"},
}

# These are fixed benchmark settings, not optimized on the holdout.
MA_WINDOW = 200
RELATIVE_STRENGTH_WINDOW = 60
VIX_MODERATE_PERCENTILE = 0.60
VIX_HIGH_PERCENTILE = 0.80


def load(symbol: str) -> pd.DataFrame:
    path = DATA_DIR / f"{symbol.lower()}_daily.csv"
    return pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    def pct(x: np.ndarray) -> float:
        if len(x) < 30 or not np.isfinite(x[-1]):
            return np.nan
        return float((x[:-1] <= x[-1]).mean())

    return series.rolling(window + 1).apply(pct, raw=True)


def build_features() -> pd.DataFrame:
    spy = load("SPY")
    qqq = load("QQQ")
    soxx = load("SOXX")
    vix = load("^VIX") if (DATA_DIR / "vix_daily.csv").exists() else None

    close = pd.concat(
        {
            "SPY": spy["close"],
            "QQQ": qqq["close"],
            "SOXX": soxx["close"],
        },
        axis=1,
    )
    out = close.dropna().copy()

    out["spy_ma"] = out["SPY"].rolling(MA_WINDOW).mean()
    out["spy_ma_slope20"] = out["spy_ma"].pct_change(20)
    out["vix"] = (
        pd.read_csv(DATA_DIR / "vix_daily.csv", parse_dates=["Date"])
        .set_index("Date")["vix"]
        .reindex(out.index)
        .ffill()
    )
    out["vix_pct"] = rolling_percentile(out["vix"])
    for symbol in ("SPY", "QQQ", "SOXX"):
        out[f"{symbol}_rs"] = out[symbol].pct_change(RELATIVE_STRENGTH_WINDOW)

    return out


def choose_leverage(row: pd.Series) -> int:
    if pd.isna(row["spy_ma"]) or pd.isna(row["vix_pct"]):
        return 0
    if row["SPY"] < row["spy_ma"]:
        return 0
    if row["vix_pct"] >= VIX_HIGH_PERCENTILE:
        return 1
    if row["vix_pct"] >= VIX_MODERATE_PERCENTILE:
        return 2
    return 3


def choose_family(row: pd.Series) -> str:
    scores = {symbol: row[f"{symbol}_rs"] for symbol in FAMILIES}
    valid = {k: v for k, v in scores.items() if pd.notna(v)}
    return max(valid, key=valid.get) if valid else "SPY"


def backtest(features: pd.DataFrame) -> pd.DataFrame:
    prices = {
        symbol: load(symbol)["adj_close"].reindex(features.index)
        for family in FAMILIES.values()
        for symbol in family.values()
        if symbol is not None
    }

    records = []
    equity = 1.0
    for i, date in enumerate(features.index):
        row = features.loc[date]
        leverage = choose_leverage(row)
        family = choose_family(row)

        if i == 0:
            daily_return = 0.0
            selected = None
        else:
            previous_date = features.index[i - 1]
            # Today's signal controls the next session. This intentionally
            # avoids using the current day's return to evaluate its own signal.
            signal_row = features.iloc[i - 1]
            leverage = choose_leverage(signal_row)
            family = choose_family(signal_row)
            selected = FAMILIES[family][leverage]
            if selected is None:
                daily_return = 0.0
            else:
                series = prices[selected]
                prev = series.loc[previous_date]
                cur = series.loc[date]
                daily_return = float(cur / prev - 1.0) if prev and pd.notna(cur) else 0.0

        equity *= 1.0 + daily_return
        records.append(
            {
                "Date": date,
                "portfolio_return": daily_return,
                "portfolio_value": equity,
                "leverage": leverage,
                "family": family,
                "selected": selected,
                "vix": row["vix"],
            }
        )

    out = pd.DataFrame(records).set_index("Date")
    out["running_max"] = out["portfolio_value"].cummax()
    out["drawdown"] = out["portfolio_value"] / out["running_max"] - 1.0
    return out


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"]
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    total = frame["portfolio_value"].iloc[-1] - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    sharpe = daily.mean() / daily.std(ddof=1) * np.sqrt(252) if daily.std(ddof=1) else np.nan
    downside = daily.where(daily < 0).std(ddof=1)
    sortino = daily.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside else np.nan
    return {
        "segment": label,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "total_return": total,
        "annualized_return": (1 + total) ** (1 / years) - 1,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": frame["drawdown"].min(),
        "worst_day": daily.min(),
        "mean_leverage": frame["leverage"].mean(),
        "pct_cash": (frame["leverage"] == 0).mean(),
    }


def main() -> None:
    features = build_features()
    result = backtest(features)

    splits = {
        "full": result,
        "train": result.loc[: "2019-12-31"],
        "validation": result.loc["2020-01-01":"2022-12-31"],
        "holdout": result.loc["2023-01-01":],
    }

    summary = pd.DataFrame(
        [summarize(frame.dropna(subset=["portfolio_value"]), name)
         for name, frame in splits.items()
         if not frame.empty]
    )
    result.to_csv(OUTPUT_DIR / "dynamic_leverage_benchmark.csv")
    summary.to_csv(OUTPUT_DIR / "dynamic_leverage_benchmark_summary.csv", index=False)

    print(summary.to_string(index=False))
    print("\nArtifacts:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
