"""E4c risk-aware AI baseline.

The learner predicts a forward 20-session return normalized by the realized
volatility of those same future 20 sessions. Future values are used only as
training targets, never as decision-time features.

This tests whether changing the optimization objective is more useful than
increasing model complexity.
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
    ACTIONS,
    DATA_DIR,
    RIDGE_ALPHA,
    SPLITS,
    backtest,
    build_features,
    feature_columns,
    load,
    predict_actions,
    select_action,
    summarize,
)

TARGET_HORIZON = 20


def risk_aware_targets(index: pd.DatetimeIndex) -> pd.DataFrame:
    targets = pd.DataFrame(index=index)
    for action, symbol in ACTIONS.items():
        if symbol is None:
            targets[action] = 0.0
            continue
        prices = load(symbol)["adj_close"].reindex(index)
        forward_return = prices.shift(-TARGET_HORIZON) / prices - 1.0
        daily = prices.pct_change()
        forward_vol = daily.rolling(TARGET_HORIZON).std().shift(-TARGET_HORIZON) * np.sqrt(252)
        targets[action] = forward_return / forward_vol.replace(0.0, np.nan)
    return targets.replace([np.inf, -np.inf], np.nan)


def make_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=RIDGE_ALPHA)),
    ])


def fit_action_models(features: pd.DataFrame, targets: pd.DataFrame,
                      cutoff: pd.Timestamp) -> dict[str, Pipeline]:
    columns = feature_columns(features)
    eligible = (features.index <= cutoff) & targets.notna().all(axis=1)
    x = features.loc[eligible, columns]
    models = {}
    for action in ACTIONS:
        model = make_model()
        model.fit(x, targets.loc[eligible, action])
        models[action] = model
    return models


def annual_walk_forward(features: pd.DataFrame,
                         targets: pd.DataFrame) -> pd.DataFrame:
    columns = feature_columns(features)
    rows = []
    for year in sorted(set(features.index.year)):
        if year < 2020:
            continue
        models = fit_action_models(features, targets, pd.Timestamp(f"{year - 1}-12-31"))
        for date in features.index[features.index.year == year]:
            row = features.loc[[date], columns]
            predictions = predict_actions(models, row, columns)
            action = select_action(predictions)
            rows.append({
                "Date": date,
                "action": action,
                "predicted_score": float(predictions[action]),
                **{f"pred_{a}": float(v) for a, v in predictions.items()},
            })
    return pd.DataFrame(rows).set_index("Date") if rows else pd.DataFrame()



LEVERAGE_CAPS = {
    "cap_2x": {"SPY_3x": "SPY_2x", "QQQ_3x": "QQQ_2x", "SOXX_3x": "SOXX_2x"},
    "cap_1x": {
        "SPY_3x": "SPY_1x", "SPY_2x": "SPY_1x",
        "QQQ_3x": "QQQ_1x", "QQQ_2x": "QQQ_1x",
        "SOXX_3x": "SOXX_1x", "SOXX_2x": "SOXX_1x",
    },
}

def apply_leverage_cap(predictions: pd.DataFrame, cap: str) -> pd.DataFrame:
    out = predictions.copy()
    out["action"] = out["action"].map(lambda x: LEVERAGE_CAPS[cap].get(x, x))
    return out

def main() -> None:
    features = build_features()
    targets = risk_aware_targets(features.index)
    predictions = annual_walk_forward(features, targets)
    predictions_for_backtest = predictions.rename(columns={"predicted_score": "predicted_return"})
    policies = {
        "cap_3x": predictions_for_backtest,
        "cap_2x": apply_leverage_cap(predictions_for_backtest, "cap_2x"),
        "cap_1x": apply_leverage_cap(predictions_for_backtest, "cap_1x"),
    }

    summaries = []
    for policy, policy_predictions in policies.items():
        result = backtest(policy_predictions)
        for split, (start, end) in SPLITS.items():
            segment = result.loc[start:end]
            if not segment.empty:
                row = summarize(segment, f"AI_RiskAware_Ridge_{policy}_{split}")
                row["split"] = split
                row["policy"] = policy
                summaries.append(row)

    cap3_result = backtest(policies["cap_3x"])
    annual = cap3_result["portfolio_return"].groupby(cap3_result.index.year).apply(
        lambda x: (1 + x).prod() - 1
    )
    spy = load("SPY")["adj_close"].reindex(cap3_result.index).pct_change().fillna(0.0)
    spy_annual = spy.groupby(spy.index.year).apply(lambda x: (1 + x).prod() - 1)
    annual_rows = [
        {
            "year": int(year),
            "strategy_return": float(value),
            "spy_return": float(spy_annual.loc[year]),
            "excess_return": float(value - spy_annual.loc[year]),
            "beats_spy": bool(value > spy_annual.loc[year]),
        }
        for year, value in annual.items()
        if year in spy_annual.index
    ]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    targets.to_csv(DATA_DIR / "e4c_risk_aware_targets.csv")
    predictions.to_csv(DATA_DIR / "e4c_risk_aware_predictions.csv")
    cap3_result.to_csv(DATA_DIR / "e4c_risk_aware_backtest.csv")
    backtest(policies["cap_2x"]).to_csv(DATA_DIR / "e4c_risk_aware_cap2x_backtest.csv")
    backtest(policies["cap_1x"]).to_csv(DATA_DIR / "e4c_risk_aware_cap1x_backtest.csv")
    pd.DataFrame(summaries).to_csv(DATA_DIR / "e4c_risk_aware_summary.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(DATA_DIR / "e4c_risk_aware_annual_returns.csv", index=False)
    cap3_result["action"].value_counts(normalize=True).rename("frequency").to_csv(
        DATA_DIR / "e4c_risk_aware_action_frequency.csv"
    )

    print(pd.DataFrame(summaries).to_string(index=False))
    print("\nAction frequency")
    print(cap3_result["action"].value_counts(normalize=True).to_string())


if __name__ == "__main__":
    main()
