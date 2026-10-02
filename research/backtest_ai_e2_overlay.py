"""E6 binary AI overlay: decide whether to run the frozen E2 engine.

The AI has exactly two actions: E2 or cash. It predicts the E2 sleeve's
forward 20-session return/volatility score. E2 itself remains unchanged.
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

from research.backtest_ai_action_selector import DATA_DIR, SPLITS, feature_columns, summarize
from research.backtest_dynamic_etf_selection import add_family_features, backtest as e2_backtest
from research.backtest_dynamic_leverage import build_features

HORIZON = 20
ALPHA = 1.0


def make_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=ALPHA)),
    ])


def e2_returns() -> pd.Series:
    features = add_family_features(build_features())
    return e2_backtest(features, "risk_adjusted_60d")["portfolio_return"]


def target_from_returns(returns: pd.Series) -> pd.Series:
    forward_return = (1.0 + returns).rolling(HORIZON).apply(np.prod).shift(-HORIZON) - 1.0
    forward_vol = returns.rolling(HORIZON).std().shift(-HORIZON) * np.sqrt(252)
    return (forward_return / forward_vol.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)


def walk_forward(features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    cols = feature_columns(features)
    rows = []
    for year in sorted(set(features.index.year)):
        if year < 2020:
            continue
        cutoff = pd.Timestamp(f"{year - 1}-12-31")
        eligible = (features.index <= cutoff) & target.notna()
        model = make_model()
        model.fit(features.loc[eligible, cols], target.loc[eligible])
        for date in features.index[features.index.year == year]:
            score = float(model.predict(features.loc[[date], cols])[0])
            rows.append({
                "Date": date,
                "action": "E2" if score > 0.0 else "cash",
                "predicted_score": score,
            })
    return pd.DataFrame(rows).set_index("Date")


def backtest(predictions: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
    equity = 1.0
    e2_equity = 1.0
    previous = "cash"
    rows = []
    for date, row in predictions.iterrows():
        future = returns.index[returns.index > date]
        if len(future) == 0:
            continue
        trade_date = future[0]
        action = row["action"]
        e2_daily = float(returns.loc[trade_date])
        daily = e2_daily if action == "E2" else 0.0
        equity *= 1.0 + daily
        e2_equity *= 1.0 + e2_daily
        rows.append({
            "Date": trade_date,
            "action": action,
            "decision_date": date,
            "portfolio_return": daily,
            "portfolio_value": equity,
            "e2_baseline_return": e2_daily,
            "e2_baseline_value": e2_equity,
            "changed_action": action != previous,
            "predicted_score": row["predicted_score"],
        })
        previous = action
    out = pd.DataFrame(rows).set_index("Date")
    out["drawdown"] = out["portfolio_value"] / out["portfolio_value"].cummax() - 1.0
    out["e2_baseline_drawdown"] = out["e2_baseline_value"] / out["e2_baseline_value"].cummax() - 1.0
    return out


def main() -> None:
    returns = e2_returns()
    features = add_family_features(build_features()).reindex(returns.index)
    target = target_from_returns(returns)
    predictions = walk_forward(features, target)
    result = backtest(predictions, returns)

    rows = []
    for split, (start, end) in SPLITS.items():
        segment = result.loc[start:end]
        if not segment.empty:
            row = summarize(segment, f"E6_{split}")
            row["split"] = split
            rows.append(row)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    result[["e2_baseline_return", "e2_baseline_value", "e2_baseline_drawdown"]].to_csv(DATA_DIR / "e6_e2_baseline.csv")
    target.to_csv(DATA_DIR / "e6_target.csv")
    predictions.to_csv(DATA_DIR / "e6_predictions.csv")
    result.to_csv(DATA_DIR / "e6_backtest.csv")
    pd.DataFrame(rows).to_csv(DATA_DIR / "e6_summary.csv", index=False)
    result["action"].value_counts(normalize=True).rename("frequency").to_csv(
        DATA_DIR / "e6_action_frequency.csv"
    )

    print(pd.DataFrame(rows).to_string(index=False))
    print("\nAction frequency")
    print(result["action"].value_counts(normalize=True).to_string())


if __name__ == "__main__":
    main()
