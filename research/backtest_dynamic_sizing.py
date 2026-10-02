"""Deterministic E3 research: E2 family/leverage selection plus volatility sizing.

Sizing is deliberately predeclared and untuned: selected ETF exposure is
capped at 100% and scaled by prior-day SPY realized volatility divided by
prior-day selected-ETF realized volatility. All signals are shifted one
session, so no same-day information is used.
"""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.backtest_dynamic_etf_selection import (
    add_family_features, build_features, choose_family, choose_leverage,
)
from research.backtest_dynamic_leverage import FAMILIES, load

DATA_DIR = ROOT / "data" / "research"
METHOD = "risk_adjusted_60d"
SIZING_METHODS = ("full_ratio", "sqrt_ratio")

def build_volatility_features(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    symbols = {symbol for family in FAMILIES.values() for symbol in family.values() if symbol}
    for symbol in symbols:
        returns = load(symbol)["adj_close"].reindex(out.index).pct_change()
        out[f"{symbol}_rv20"] = returns.rolling(20).std() * np.sqrt(252)
    return out

def choose_allocation(signal: pd.Series, selected: str | None, method: str = "full_ratio") -> float:
    if selected is None:
        return 0.0
    selected_vol = signal.get(f"{selected}_rv20", np.nan)
    spy_vol = signal.get("SPY_rv20", np.nan)
    if pd.isna(selected_vol) or pd.isna(spy_vol) or selected_vol <= 0 or spy_vol < 0:
        return 1.0
    ratio = float(spy_vol / selected_vol)
    if method == "full_ratio":
        return float(min(1.0, ratio))
    if method == "sqrt_ratio":
        return float(min(1.0, np.sqrt(ratio)))
    raise ValueError(f"Unknown sizing method: {method}")

def backtest(features: pd.DataFrame, sizing_method: str = "full_ratio") -> pd.DataFrame:
    prices = {symbol: load(symbol)["adj_close"].reindex(features.index)
              for family in FAMILIES.values() for symbol in family.values() if symbol}
    records, equity = [], 1.0
    for i, date in enumerate(features.index):
        if i == 0:
            daily_return, leverage, family, selected, allocation = 0.0, 0, "SPY", None, 0.0
        else:
            signal = features.iloc[i - 1]
            leverage = choose_leverage(signal)
            family = choose_family(signal, METHOD)
            selected = FAMILIES[family][leverage]
            allocation = choose_allocation(signal, selected, sizing_method)
            if selected is None:
                daily_return = 0.0
            else:
                series = prices[selected]
                prev, cur = series.iloc[i - 1], series.iloc[i]
                raw_return = float(cur / prev - 1.0) if pd.notna(prev) and pd.notna(cur) and prev != 0 else 0.0
                daily_return = allocation * raw_return
        equity *= 1.0 + daily_return
        records.append({"Date": date, "portfolio_return": daily_return,
                        "portfolio_value": equity, "leverage": leverage,
                        "family": family, "selected": selected,
                        "allocation": allocation})
    out = pd.DataFrame(records).set_index("Date")
    out["drawdown"] = out["portfolio_value"] / out["portfolio_value"].cummax() - 1.0
    return out

def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    total = (1 + daily).prod() - 1
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    return {"strategy": label, "start": frame.index.min(), "end": frame.index.max(),
            "total_return": total, "annualized_return": (1 + total) ** (1 / years) - 1,
            "annualized_volatility": vol,
            "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252),
            "sortino": daily.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside else np.nan,
            "max_drawdown": frame["drawdown"].min(), "worst_day": daily.min(),
            "mean_leverage": frame["leverage"].mean(),
            "mean_allocation": frame["allocation"].mean(),
            "pct_cash": float((frame["leverage"] == 0).mean())}

def main() -> None:
    features = build_volatility_features(add_family_features(build_features()))
    all_summary, all_annual = [], []
    for sizing_method in SIZING_METHODS:
        result = backtest(features, sizing_method)
        suffix = "" if sizing_method == "full_ratio" else f"_{sizing_method}"
        result.to_csv(DATA_DIR / f"dynamic_sizing_e3{suffix}.csv")
        splits = {"full": result, "train": result.loc[: "2019-12-31"],
                  "validation": result.loc["2020-01-01":"2022-12-31"],
                  "holdout": result.loc["2023-01-01":]}
        for name, x in splits.items():
            if not x.empty:
                row = summarize(x, name)
                row["sizing_method"] = sizing_method
                all_summary.append(row)
        annual = result["portfolio_return"].groupby(result.index.year).apply(lambda x: (1+x).prod()-1)
        spy = load("SPY")["adj_close"].reindex(result.index).pct_change().fillna(0)
        spy_annual = spy.groupby(spy.index.year).apply(lambda x: (1+x).prod()-1)
        all_annual.extend([{"sizing_method": sizing_method, "year": int(y),
                            "strategy_return": float(v), "spy_return": float(spy_annual.loc[y]),
                            "excess_return": float(v-spy_annual.loc[y]),
                            "beats_spy": bool(v > spy_annual.loc[y])}
                           for y,v in annual.items() if y in spy_annual.index])
    summary = pd.DataFrame(all_summary)
    summary.to_csv(DATA_DIR / "dynamic_sizing_e3_summary.csv", index=False)
    pd.DataFrame(all_annual).to_csv(DATA_DIR / "dynamic_sizing_e3_annual_returns.csv", index=False)
    print(summary.to_string(index=False))
    print("\nArtifacts:", DATA_DIR)

if __name__ == "__main__":
    main()
