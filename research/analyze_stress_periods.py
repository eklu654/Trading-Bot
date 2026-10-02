"""Analyze fixed historical stress windows for the research controls.

Windows are predeclared and are not used for parameter tuning. This script is
for diagnosis of how trend filters behave in different kinds of selloffs.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from research.backtest_dynamic_leverage import backtest, build_features, load
from research.backtest_dynamic_etf_selection import add_family_features, backtest as backtest_e2
from research.compare_leverage_benchmarks import dma_cash

DATA_DIR = ROOT / "data" / "research"

WINDOWS = {
    "feb_2018_volatility_shock": ("2018-02-01", "2018-03-02"),
    "oct_dec_2018": ("2018-10-01", "2018-12-31"),
    "covid_crash": ("2020-02-19", "2020-04-30"),
    "2022_rate_hike_bear": ("2022-01-03", "2022-12-30"),
    "2023_2024_recovery": ("2023-01-03", "2024-12-31"),
    "2008_financial_crisis": ("2008-01-02", "2008-12-31"),
}


def summarize(returns: pd.Series) -> dict[str, float]:
    returns = returns.dropna().fillna(0.0)
    if returns.empty:
        return {"return": np.nan, "max_drawdown": np.nan, "worst_day": np.nan}
    equity = (1.0 + returns).cumprod()
    dd = equity / equity.cummax() - 1.0
    return {
        "return": float(equity.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "worst_day": float(returns.min()),
    }


def main() -> None:
    features = build_features()
    dynamic = backtest(features)
    e2_features = add_family_features(features)
    dynamic_e2 = backtest_e2(e2_features, "risk_adjusted_60d")
    spy = load("SPY")["adj_close"].reindex(features.index)
    spxl = load("SPXL")["adj_close"].reindex(features.index)

    strategy_returns = {
        "SPY_1x": spy.pct_change().fillna(0.0),
        "SPXL_3x": spxl.pct_change().fillna(0.0),
        "SPY_200DMA_cash": dma_cash("SPY", features.index)["portfolio_return"],
        "dynamic_family_leverage": dynamic["portfolio_return"],
        "dynamic_e2_risk_adjusted": dynamic_e2["portfolio_return"],
    }

    rows = []
    for window, (start, end) in WINDOWS.items():
        for strategy, returns in strategy_returns.items():
            segment = returns.loc[start:end]
            stats = summarize(segment)
            rows.append({"window": window, "strategy": strategy, **stats})

    result = pd.DataFrame(rows)
    result.to_csv(DATA_DIR / "stress_period_comparison.csv", index=False)

    print(result.to_string(index=False))
    print("\nArtifacts:", DATA_DIR)


if __name__ == "__main__":
    main()
