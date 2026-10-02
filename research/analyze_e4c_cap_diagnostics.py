"""Rolling, annual, and stress diagnostics for E4c capped policies."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_ai_action_selector import load

DATA_DIR = ROOT / "data" / "research"
STRESS = {
    "feb_2018": ("2018-02-01", "2018-03-02"),
    "oct_dec_2018": ("2018-10-01", "2018-12-31"),
    "covid": ("2020-02-19", "2020-04-30"),
    "rate_hike_2022": ("2022-01-03", "2022-12-30"),
    "recovery_2023_2024": ("2023-01-03", "2024-12-31"),
}


def cagr(returns: pd.Series) -> float:
    returns = returns.dropna()
    if returns.empty:
        return np.nan
    years = max((returns.index[-1] - returns.index[0]).days / 365.25, 1 / 365.25)
    return float((1 + returns).prod() ** (1 / years) - 1)


def max_dd(returns: pd.Series) -> float:
    equity = (1 + returns.fillna(0.0)).cumprod()
    return float((equity / equity.cummax() - 1).min())


def main() -> None:
    spy = load("SPY")["adj_close"].pct_change().fillna(0.0)
    rows = []
    annual_rows = []
    stress_rows = []

    for cap in ("cap1x", "cap2x"):
        frame = pd.read_csv(
            DATA_DIR / f"e4c_risk_aware_{cap}_backtest.csv",
            parse_dates=["Date"],
        ).set_index("Date")
        common = frame.index.intersection(spy.index)
        returns = frame["portfolio_return"].reindex(common).fillna(0.0)
        spy_common = spy.reindex(common).fillna(0.0)

        for window in (3, 5, 10):
            years = window * 252
            rolling = returns.rolling(years).apply(
                lambda x: (1 + x).prod() ** (252 / len(x)) - 1,
                raw=False,
            )
            rolling_spy = spy_common.rolling(years).apply(
                lambda x: (1 + x).prod() ** (252 / len(x)) - 1,
                raw=False,
            )
            excess = rolling - rolling_spy
            valid = excess.dropna()
            rows.append({
                "policy": cap,
                "rolling_years": window,
                "mean_excess_cagr": valid.mean(),
                "median_excess_cagr": valid.median(),
                "worst_excess_cagr": valid.min(),
                "positive_excess_pct": (valid > 0).mean(),
            })

        for year in sorted(set(returns.index.year)):
            segment = returns[returns.index.year == year]
            spy_segment = spy_common[spy_common.index.year == year]
            if not segment.empty:
                annual_rows.append({
                    "policy": cap,
                    "year": int(year),
                    "strategy_return": (1 + segment).prod() - 1,
                    "spy_return": (1 + spy_segment).prod() - 1,
                })

        for name, (start, end) in STRESS.items():
            segment = returns.loc[start:end]
            if not segment.empty:
                stress_rows.append({
                    "policy": cap,
                    "stress_period": name,
                    "return": (1 + segment).prod() - 1,
                    "max_drawdown": max_dd(segment),
                    "worst_day": segment.min(),
                })

    pd.DataFrame(rows).to_csv(DATA_DIR / "e4c_cap_rolling.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(DATA_DIR / "e4c_cap_annual.csv", index=False)
    pd.DataFrame(stress_rows).to_csv(DATA_DIR / "e4c_cap_stress.csv", index=False)

    print("Rolling")
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nAnnual")
    print(pd.DataFrame(annual_rows).to_string(index=False))
    print("\nStress")
    print(pd.DataFrame(stress_rows).to_string(index=False))


if __name__ == "__main__":
    main()
