"""Deterministic E2 research: dynamic ETF family selection plus leverage.

This deliberately tests a small, predeclared set of family-selection rules.
Leverage is inherited from the existing deterministic regime controller so
that the experiment isolates the value of choosing SPY/QQQ/SOXX families.

No parameter search is performed. All signals are shifted one session.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from research.backtest_dynamic_leverage import FAMILIES, build_features, choose_leverage, load

DATA_DIR = ROOT / "data" / "research"

FAMILY_NAMES = tuple(FAMILIES.keys())


def family_score(row: pd.Series, family: str, method: str) -> float:
    if method == "raw_60d":
        return float(row[f"{family}_rs"])

    if method == "trend_confirmed":
        rs = row[f"{family}_rs"]
        ma = row[f"{family}_ma200"]
        price = row[family]
        if pd.isna(rs) or pd.isna(ma) or pd.isna(price):
            return np.nan
        # A family must itself be above its 200-DMA to be eligible. Among
        # eligible families, select the strongest trailing 60-session return.
        return float(rs) if price >= ma else -np.inf

    if method == "risk_adjusted_60d":
        rs = row[f"{family}_rs"]
        vol = row.get(f"{family}_rv20", np.nan)
        if pd.isna(rs) or pd.isna(vol) or vol <= 0:
            return np.nan
        return float(rs / vol)

    raise ValueError(f"Unknown family-selection method: {method}")


def add_family_features(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    for family in FAMILY_NAMES:
        returns = out[family].pct_change()
        out[f"{family}_rv20"] = returns.rolling(20).std() * np.sqrt(252)
        out[f"{family}_ma200"] = out[family].rolling(200).mean()
    return out


def choose_family(row: pd.Series, method: str) -> str:
    scores = {family: family_score(row, family, method) for family in FAMILY_NAMES}
    valid = {k: v for k, v in scores.items() if pd.notna(v)}
    return max(valid, key=valid.get) if valid else "SPY"


def backtest(features: pd.DataFrame, method: str) -> pd.DataFrame:
    prices = {
        symbol: load(symbol)["adj_close"].reindex(features.index)
        for family in FAMILIES.values()
        for symbol in family.values()
        if symbol is not None
    }

    records = []
    equity = 1.0

    for i, date in enumerate(features.index):
        if i == 0:
            daily_return = 0.0
            leverage = 0
            family = "SPY"
            selected = None
        else:
            signal = features.iloc[i - 1]
            leverage = choose_leverage(signal)
            family = choose_family(signal, method)
            selected = FAMILIES[family][leverage]
            if selected is None:
                daily_return = 0.0
            else:
                series = prices[selected]
                prev = series.iloc[i - 1]
                cur = series.iloc[i]
                daily_return = float(cur / prev - 1.0) if pd.notna(prev) and pd.notna(cur) and prev != 0 else 0.0

        equity *= 1.0 + daily_return
        records.append({
            "Date": date,
            "portfolio_return": daily_return,
            "portfolio_value": equity,
            "leverage": leverage,
            "family": family,
            "selected": selected,
        })

    out = pd.DataFrame(records).set_index("Date")
    out["drawdown"] = out["portfolio_value"] / out["portfolio_value"].cummax() - 1.0
    return out


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    total = (1.0 + daily).prod() - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    return {
        "strategy": label,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "total_return": total,
        "annualized_return": (1.0 + total) ** (1.0 / years) - 1.0,
        "annualized_volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252),
        "sortino": daily.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside else np.nan,
        "max_drawdown": frame["drawdown"].min(),
        "worst_day": daily.min(),
        "mean_leverage": frame["leverage"].mean(),
        "pct_cash": float((frame["leverage"] == 0).mean()),
    }


def main() -> None:
    features = add_family_features(build_features())
    methods = ("raw_60d", "trend_confirmed", "risk_adjusted_60d")
    rows = []

    for method in methods:
        result = backtest(features, method)
        result.to_csv(DATA_DIR / f"dynamic_etf_selection_{method}.csv")
        rows.append(summarize(result, method))

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "dynamic_etf_selection_comparison.csv", index=False)

    # Chronological evaluation slices are fixed in advance and are not used
    # to select or tune a method.
    splits = {
        "train": ("2010-01-04", "2019-12-31"),
        "validation": ("2020-01-01", "2022-12-31"),
        "holdout": ("2023-01-01", "2026-09-25"),
    }
    split_rows = []
    annual_rows = []
    rolling_rows = []
    spy_prices = load("SPY")["adj_close"].reindex(features.index)
    spy_returns = spy_prices.pct_change().fillna(0.0)

    for method in methods:
        result = backtest(features, method)
        for split, (start, end) in splits.items():
            segment = result.loc[start:end]
            if segment.empty:
                continue
            stats = summarize(segment, f"{method}_{split}")
            stats["method"] = method
            stats["split"] = split
            split_rows.append(stats)

        annual = result["portfolio_return"].groupby(result.index.year).apply(
            lambda x: (1.0 + x).prod() - 1.0
        )
        spy_annual = spy_returns.groupby(spy_returns.index.year).apply(
            lambda x: (1.0 + x).prod() - 1.0
        )
        for year, value in annual.items():
            if year in spy_annual.index:
                annual_rows.append({
                    "method": method,
                    "year": int(year),
                    "strategy_return": float(value),
                    "spy_return": float(spy_annual.loc[year]),
                    "excess_return": float(value - spy_annual.loc[year]),
                    "beats_spy": bool(value > spy_annual.loc[year]),
                })

        equity = (1.0 + result["portfolio_return"].fillna(0.0)).cumprod()
        spy_equity = (1.0 + spy_returns).cumprod()
        for window in (3, 5, 10):
            years = window
            strategy_roll = equity / equity.shift(window * 252)
            spy_roll = spy_equity / spy_equity.shift(window * 252)
            rolling = (strategy_roll / spy_roll) ** (1.0 / years) - 1.0
            valid = rolling.dropna()
            for date, value in valid.items():
                rolling_rows.append({
                    "method": method,
                    "window_years": window,
                    "date": date,
                    "excess_cagr": float(value),
                })

    split_summary = pd.DataFrame(split_rows)
    annual_summary = pd.DataFrame(annual_rows)
    rolling_summary = pd.DataFrame(rolling_rows)
    split_summary.to_csv(DATA_DIR / "dynamic_etf_selection_split_summary.csv", index=False)
    annual_summary.to_csv(DATA_DIR / "dynamic_etf_selection_annual_returns.csv", index=False)
    rolling_summary.to_csv(DATA_DIR / "dynamic_etf_selection_rolling_relative.csv", index=False)

    print(summary.to_string(index=False))
    print("\nChronological split summary")
    print(split_summary.to_string(index=False))
    print("\nArtifacts:", DATA_DIR)


if __name__ == "__main__":
    main()
