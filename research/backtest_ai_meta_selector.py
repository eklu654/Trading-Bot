"""E5 meta-regime selector: choose among proven strategy sleeves.

The learner does not directly select a leveraged ETF. It selects among:
- deterministic E2 risk-adjusted family/leverage selector;
- deterministic E3 square-root volatility sizing;
- SPY 1x;
- cash.

Targets are forward 20-session sleeve returns normalized by each sleeve's
future realized volatility. Training remains strictly chronological.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_ai_action_selector import (
    DATA_DIR,
    SPLITS,
    feature_columns,
    load,
    summarize,
)
from research.backtest_dynamic_leverage import build_features
from research.backtest_dynamic_etf_selection import (
    add_family_features,
    backtest as e2_backtest,
)
from research.backtest_dynamic_sizing import (
    backtest as e3_backtest,
    build_volatility_features,
)

HORIZON = 20
ALPHA = 1.0
SLEEVES = ("E2", "E3_sqrt", "SPY", "cash")


def make_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=ALPHA)),
    ])


def sleeve_returns() -> pd.DataFrame:
    e2_features = add_family_features(build_features())
    e2 = e2_backtest(e2_features, "risk_adjusted_60d")["portfolio_return"]

    e3_features = build_volatility_features(e2_features)
    e3 = e3_backtest(e3_features, "sqrt_ratio")["portfolio_return"]

    spy = load("SPY")["adj_close"].reindex(e2.index).pct_change().fillna(0.0)
    out = pd.DataFrame({"E2": e2, "E3_sqrt": e3, "SPY": spy}, index=e2.index)
    out["cash"] = 0.0
    return out


def risk_aware_targets(returns: pd.DataFrame) -> pd.DataFrame:
    targets = pd.DataFrame(index=returns.index)
    for sleeve in SLEEVES:
        series = returns[sleeve]
        future_return = (1.0 + series).rolling(HORIZON).apply(np.prod).shift(-HORIZON) - 1.0
        future_vol = series.rolling(HORIZON).std().shift(-HORIZON) * np.sqrt(252)
        targets[sleeve] = future_return / future_vol.replace(0.0, np.nan)
    return targets.replace([np.inf, -np.inf], np.nan)


def fit_models(features: pd.DataFrame, targets: pd.DataFrame,
                cutoff: pd.Timestamp) -> dict[str, Pipeline]:
    cols = feature_columns(features)
    eligible = (features.index <= cutoff) & targets.notna().all(axis=1)
    models = {}
    for sleeve in SLEEVES:
        model = make_model()
        model.fit(features.loc[eligible, cols], targets.loc[eligible, sleeve])
        models[sleeve] = model
    return models


def walk_forward(features: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    cols = feature_columns(features)
    rows = []
    for year in sorted(set(features.index.year)):
        if year < 2020:
            continue
        models = fit_models(features, targets, pd.Timestamp(f"{year - 1}-12-31"))
        for date in features.index[features.index.year == year]:
            x = features.loc[[date], cols]
            scores = {s: float(m.predict(x)[0]) for s, m in models.items()}
            action = max(scores, key=scores.get)
            rows.append({
                "Date": date,
                "sleeve": action,
                "predicted_score": scores[action],
                **{f"pred_{s}": v for s, v in scores.items()},
            })
    return pd.DataFrame(rows).set_index("Date")


def backtest(predictions: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    equity = 1.0
    rows = []
    previous = "cash"
    for date, row in predictions.iterrows():
        next_date = returns.index[returns.index > date]
        if len(next_date) == 0:
            continue
        trade_date = next_date[0]
        sleeve = row["sleeve"]
        daily = float(returns.loc[trade_date, sleeve])
        equity *= 1.0 + daily
        rows.append({
            "Date": trade_date,
            "decision_date": date,
            "sleeve": sleeve,
            "portfolio_return": daily,
            "portfolio_value": equity,
            "changed_sleeve": sleeve != previous,
            "predicted_score": row["predicted_score"],
        })
        previous = sleeve
    out = pd.DataFrame(rows).set_index("Date")
    out["drawdown"] = out["portfolio_value"] / out["portfolio_value"].cummax() - 1.0
    return out


def main() -> None:
    features = add_family_features(build_features())
    returns = sleeve_returns().reindex(features.index)
    targets = risk_aware_targets(returns)
    predictions = walk_forward(features, targets)
    result = backtest(predictions, returns)

    rows = []
    for split, (start, end) in SPLITS.items():
        segment = result.loc[start:end]
        if not segment.empty:
            row = summarize(segment, f"E5_{split}")
            row["split"] = split
            rows.append(row)

    annual = result["portfolio_return"].groupby(result.index.year).apply(
        lambda x: (1.0 + x).prod() - 1.0
    )
    spy = returns["SPY"].reindex(result.index).fillna(0.0)
    spy_annual = spy.groupby(spy.index.year).apply(lambda x: (1.0 + x).prod() - 1.0)
    annual_rows = []
    for year, value in annual.items():
        if year in spy_annual.index:
            annual_rows.append({
                "year": int(year),
                "strategy_return": float(value),
                "spy_return": float(spy_annual.loc[year]),
                "excess_return": float(value - spy_annual.loc[year]),
                "beats_spy": bool(value > spy_annual.loc[year]),
            })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    returns.to_csv(DATA_DIR / "e5_sleeve_returns.csv")
    targets.to_csv(DATA_DIR / "e5_sleeve_targets.csv")
    predictions.to_csv(DATA_DIR / "e5_predictions.csv")
    result.to_csv(DATA_DIR / "e5_backtest.csv")
    pd.DataFrame(rows).to_csv(DATA_DIR / "e5_summary.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(DATA_DIR / "e5_annual_returns.csv", index=False)
    result["sleeve"].value_counts(normalize=True).rename("frequency").to_csv(
        DATA_DIR / "e5_sleeve_frequency.csv"
    )

    print(pd.DataFrame(rows).to_string(index=False))
    print("\nSleeve frequency")
    print(result["sleeve"].value_counts(normalize=True).to_string())


if __name__ == "__main__":
    main()
