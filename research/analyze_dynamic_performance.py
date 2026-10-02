"""Analyze dynamic leveraged strategy performance against SPY.

All strategy returns are daily and signals are assumed to be executable on the
next session. This module reports absolute performance and relative-to-SPY
consistency; it does not optimize parameters.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"


def load_prices() -> pd.DataFrame:
    names = ["SPY", "SSO", "SPXL", "QQQ", "QLD", "TQQQ", "SOXX", "USD", "SOXL"]
    series = {}
    for symbol in names:
        frame = pd.read_csv(DATA_DIR / f"{symbol.lower()}_daily.csv", parse_dates=["Date"]).set_index("Date")
        series[symbol] = frame["adj_close"]
    return pd.DataFrame(series).sort_index()


def daily_returns(price: pd.Series) -> pd.Series:
    return price.pct_change().fillna(0.0)


def annual_returns(returns: pd.Series) -> pd.Series:
    return (1.0 + returns).groupby(returns.index.year).prod() - 1.0


def cagr(returns: pd.Series) -> float:
    years = max((returns.index[-1] - returns.index[0]).days / 365.25, 1 / 365.25)
    total = (1.0 + returns).prod() - 1.0
    return (1.0 + total) ** (1.0 / years) - 1.0


def rolling_cagr(returns: pd.Series, years: int) -> pd.Series:
    window = int(round(252 * years))
    equity = (1.0 + returns).cumprod()
    return (equity / equity.shift(window)) ** (252.0 / window) - 1.0


def main() -> None:
    comparison = pd.read_csv(DATA_DIR / "leverage_strategy_comparison.csv").set_index("strategy")
    prices = load_prices()
    spy_returns = daily_returns(prices["SPY"])
    dynamic = pd.read_csv(DATA_DIR / "dynamic_leverage_benchmark.csv", parse_dates=["Date"]).set_index("Date")
    dynamic_returns = dynamic["portfolio_return"].fillna(0.0)

    strategies = {
        "SPY": spy_returns,
        "SSO": daily_returns(prices["SSO"]),
        "SPXL": daily_returns(prices["SPXL"]),
        "dynamic_family_leverage": dynamic_returns,
    }

    annual_rows = []
    for name, returns in strategies.items():
        for year, value in annual_returns(returns).items():
            annual_rows.append({"strategy": name, "year": int(year), "return": float(value)})

    annual = pd.DataFrame(annual_rows)
    annual_wide = annual.pivot(index="year", columns="strategy", values="return")
    annual_wide["dynamic_minus_spy"] = annual_wide["dynamic_family_leverage"] - annual_wide["SPY"]
    annual_wide["dynamic_beats_spy"] = annual_wide["dynamic_minus_spy"] > 0

    relative = {
        "dynamic_vs_spy_years": int(annual_wide["dynamic_beats_spy"].sum()),
        "dynamic_vs_spy_years_observed": int(annual_wide["dynamic_beats_spy"].notna().sum()),
        "dynamic_vs_spy_year_fraction": float(annual_wide["dynamic_beats_spy"].mean()),
        "dynamic_average_annual_excess": float(annual_wide["dynamic_minus_spy"].mean()),
        "dynamic_median_annual_excess": float(annual_wide["dynamic_minus_spy"].median()),
        "dynamic_worst_annual_excess": float(annual_wide["dynamic_minus_spy"].min()),
        "dynamic_best_annual_excess": float(annual_wide["dynamic_minus_spy"].max()),
        "dynamic_cagr": cagr(dynamic_returns),
        "spy_cagr": cagr(spy_returns),
        "dynamic_cagr_minus_spy": cagr(dynamic_returns) - cagr(spy_returns),
    }

    rolling_rows = []
    common = pd.concat([dynamic_returns.rename("dynamic"), spy_returns.rename("spy")], axis=1).dropna()
    for years in (3, 5, 10):
        dyn = rolling_cagr(common["dynamic"], years)
        spy = rolling_cagr(common["spy"], years)
        excess = (dyn - spy).dropna()
        rolling_rows.append({
            "window_years": years,
            "observations": int(excess.size),
            "dynamic_mean_excess_cagr": float(excess.mean()),
            "dynamic_median_excess_cagr": float(excess.median()),
            "dynamic_min_excess_cagr": float(excess.min()),
            "dynamic_max_excess_cagr": float(excess.max()),
            "dynamic_positive_excess_fraction": float((excess > 0).mean()),
        })

    pd.DataFrame([relative]).to_csv(DATA_DIR / "dynamic_relative_summary.csv", index=False)
    annual_wide.to_csv(DATA_DIR / "dynamic_annual_returns.csv")
    pd.DataFrame(rolling_rows).to_csv(DATA_DIR / "dynamic_rolling_relative.csv", index=False)

    print("Annual returns and SPY-relative analysis")
    print(annual_wide.to_string())
    print("\nRelative summary")
    print(pd.DataFrame([relative]).to_string(index=False))
    print("\nRolling relative CAGR")
    print(pd.DataFrame(rolling_rows).to_string(index=False))
    print("\nExisting control comparison")
    print(comparison.to_string())


if __name__ == "__main__":
    main()
