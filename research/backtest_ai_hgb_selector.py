"""E4b nonlinear AI baseline using chronological histogram gradient boosting.

All model settings are fixed before evaluation. This is a model-family
comparison against E4 Ridge, not a hyperparameter search.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_ai_action_selector import (
    ACTIONS,
    DATA_DIR,
    SPLITS,
    action_forward_returns,
    backtest,
    build_features,
    feature_columns,
    predict_actions,
    select_action,
    summarize,
)

MODEL_PARAMS = {
    "learning_rate": 0.05,
    "max_iter": 100,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 50,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 42,
}


def make_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(**MODEL_PARAMS)


def fit_action_models(features: pd.DataFrame, targets: pd.DataFrame,
                      cutoff: pd.Timestamp) -> dict[str, HistGradientBoostingRegressor]:
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
        cutoff = pd.Timestamp(f"{year - 1}-12-31")
        models = fit_action_models(features, targets, cutoff)
        for date in features.index[features.index.year == year]:
            row = features.loc[[date], columns]
            predictions = predict_actions(models, row, columns)
            action = select_action(predictions)
            rows.append({
                "Date": date,
                "action": action,
                "predicted_return": float(predictions[action]),
                **{f"pred_{a}": float(v) for a, v in predictions.items()},
            })
    return pd.DataFrame(rows).set_index("Date") if rows else pd.DataFrame()


def main() -> None:
    features = build_features()
    targets = action_forward_returns(features.index)
    predictions = annual_walk_forward(features, targets)
    result = backtest(predictions)

    summaries = []
    for split, (start, end) in SPLITS.items():
        segment = result.loc[start:end]
        if not segment.empty:
            row = summarize(segment, f"AI_HGB_{split}")
            row["split"] = split
            summaries.append(row)

    annual = result["portfolio_return"].groupby(result.index.year).apply(
        lambda x: (1.0 + x).prod() - 1.0
    )
    spy = (
        __import__("research.backtest_ai_action_selector", fromlist=["load"])
        .load("SPY")["adj_close"].reindex(result.index).pct_change().fillna(0.0)
    )
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
    predictions.to_csv(DATA_DIR / "e4b_hgb_predictions.csv")
    result.to_csv(DATA_DIR / "e4b_hgb_backtest.csv")
    pd.DataFrame(summaries).to_csv(DATA_DIR / "e4b_hgb_summary.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(DATA_DIR / "e4b_hgb_annual_returns.csv", index=False)
    result["action"].value_counts(normalize=True).rename("frequency").to_csv(
        DATA_DIR / "e4b_hgb_action_frequency.csv"
    )

    print(pd.DataFrame(summaries).to_string(index=False))
    print("\nAction frequency")
    print(result["action"].value_counts(normalize=True).to_string())


if __name__ == "__main__":
    main()
