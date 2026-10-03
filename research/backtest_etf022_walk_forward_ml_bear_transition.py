"""ETF-022: walk-forward ML bear-transition adaptation.

ETF-021 showed that a model frozen on 2010-2019 did not generalize to the
2020-2022 validation regime. ETF-022 tests the narrower question of whether
periodic ex-ante retraining fixes that regime-shift problem.

Rules:
- target: forward 20-session QQQ/SPY/SOXX decline <= -4%;
- model architecture is fixed in advance (no hyperparameter search);
- retrain every 63 trading sessions using only data available before the
  prediction date;
- training window is expanding from the original 2010-2019 seed;
- validation chooses probability threshold and inverse fraction;
- 2023+ is then evaluated with the frozen decision parameters, while the
  model itself continues its predeclared walk-forward retraining schedule;
- canonical ETF-001 accounting and same-underlying bull/bear exclusivity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline

from backtest_etf020_ml_indicator_bear_transition import (
    FRACTIONS,
    BULL,
    BEAR,
    SLEEVE,
    baseline_and_returns,
    make_feature_matrix,
    metrics,
)

TRAIN_END = pd.Timestamp("2019-12-31")
VALID_END = pd.Timestamp("2022-12-31")
RETRAIN_EVERY = 63
TARGET_HORIZON = 20
TARGET_THRESHOLD = -0.04
THRESHOLDS = (0.55, 0.60, 0.65, 0.70)


def make_target(close: pd.DataFrame) -> pd.Series:
    benchmark = close[["QQQ", "SPY", "SOXX"]].mean(axis=1)
    forward = benchmark.shift(-TARGET_HORIZON) / benchmark - 1.0
    y = (forward <= TARGET_THRESHOLD).astype(float)
    y[forward.isna()] = np.nan
    return y


def walk_forward_probabilities(X: pd.DataFrame, y: pd.Series) -> pd.Series:
    pred_idx = X.index[X.index > TRAIN_END]
    prob = pd.Series(np.nan, index=X.index, dtype=float)
    model = HistGradientBoostingClassifier(
        max_iter=120,
        learning_rate=0.05,
        max_leaf_nodes=7,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=42,
    )
    pipe = make_pipeline(SimpleImputer(strategy="median"), model)

    last_train_date = None
    for i, date in enumerate(pred_idx):
        needs_fit = last_train_date is None or i % RETRAIN_EVERY == 0
        if needs_fit:
            train_mask = (X.index <= date) & (X.index < date) & y.notna()
            if train_mask.sum() < 500:
                continue
            pipe.fit(X.loc[train_mask], y.loc[train_mask])
            last_train_date = date
        prob.loc[date] = pipe.predict_proba(X.loc[[date]])[:, 1][0]

    return prob


def portfolio_for_gate(prob: pd.Series, baseline: pd.Series, ret: pd.DataFrame,
                       bull_active: dict[str, pd.Series], threshold: float,
                       fraction: float) -> pd.Series:
    gate = (prob >= threshold).shift(1).fillna(False).astype(bool)
    daily = baseline.copy()

    for s in BULL:
        active = bull_active[s]
        bull = SLEEVE * ret[s].where(active & ~gate, 0.0)
        inv = SLEEVE * fraction * ret[BEAR[s]].where(gate, 0.0)
        daily = daily - SLEEVE * ret[s].where(active, 0.0) + bull + inv

    return daily


def main() -> None:
    X, _, close, _ = make_feature_matrix()
    y = make_target(close)
    ret, baseline = baseline_and_returns(close)

    bull_active: dict[str, pd.Series] = {}
    for s in BULL:
        c = pd.read_csv(
            __import__("pathlib").Path(__file__).resolve().parents[1]
            / "data" / "research" / f"{s.lower()}_daily.csv",
            parse_dates=["Date"],
        ).set_index("Date")["close"].reindex(X.index).ffill()
        ma = c.rolling(200, min_periods=200).mean()
        active = pd.Series(False, index=X.index)
        state = False
        count = 0
        for d, p, m in zip(X.index, c, ma):
            if pd.isna(m) or p < m:
                state = False
                count = 0
            elif not state:
                count += 1
                if count >= 5:
                    state = True
            active.loc[d] = state
        bull_active[s] = active.shift(1).fillna(False)

    prob = walk_forward_probabilities(X, y)
    rows = []

    masks = {
        "validation": (X.index >= "2020-01-01") & (X.index <= VALID_END),
        "holdout": X.index >= "2023-01-01",
    }

    for split, mask in masks.items():
        d = pd.concat([y, prob], axis=1).loc[mask].dropna()
        if len(d) and d.iloc[:, 0].nunique() == 2:
            rows.append({
                "split": split,
                "roc_auc": roc_auc_score(d.iloc[:, 0], d.iloc[:, 1]),
                "average_precision": average_precision_score(d.iloc[:, 0], d.iloc[:, 1]),
                "positive_rate": d.iloc[:, 0].mean(),
                "n": len(d),
            })

    print("=== ETF-022 WALK-FORWARD PREDICTIVE DIAGNOSTICS ===")
    print(pd.DataFrame(rows).to_string(index=False))

    val_rows = []
    for threshold in THRESHOLDS:
        for fraction in FRACTIONS:
            daily = portfolio_for_gate(prob, baseline, ret, bull_active, threshold, fraction)
            m = metrics(daily.loc[masks["validation"]])
            b = metrics(baseline.loc[masks["validation"]])
            val_rows.append({
                "threshold": threshold,
                "inverse_fraction": fraction,
                "annualized_return": m[0],
                "max_drawdown": m[1],
                "sharpe": m[3],
                "ending_value_5000": m[4],
                "baseline_return": b[0],
                "baseline_sharpe": b[3],
                "bear_days": int(((prob >= threshold).shift(1).fillna(False)).loc[masks["validation"]].sum()),
            })

    val = pd.DataFrame(val_rows)
    val["sharpe_delta"] = val["sharpe"] - val["baseline_sharpe"]
    val["return_delta"] = val["annualized_return"] - val["baseline_return"]
    print("\\n=== ETF-022 VALIDATION GRID ===")
    print(val.sort_values(["sharpe_delta", "return_delta"], ascending=False).to_string(index=False))

    winner = val.sort_values(["sharpe_delta", "return_delta"], ascending=False).iloc[0]
    daily = portfolio_for_gate(
        prob, baseline, ret, bull_active,
        float(winner["threshold"]), float(winner["inverse_fraction"]),
    )
    hold = metrics(daily.loc[masks["holdout"]])
    base_hold = metrics(baseline.loc[masks["holdout"]])
    print("\\n=== ETF-022 FROZEN-DECISION HOLDOUT ===")
    print(pd.DataFrame([{
        "threshold": winner["threshold"],
        "inverse_fraction": winner["inverse_fraction"],
        "annualized_return": hold[0],
        "max_drawdown": hold[1],
        "sharpe": hold[3],
        "ending_value_5000": hold[4],
        "baseline_return": base_hold[0],
        "baseline_sharpe": base_hold[3],
        "bear_days": int(((prob >= winner["threshold"]).shift(1).fillna(False)).loc[masks["holdout"]].sum()),
    }]).to_string(index=False))


if __name__ == "__main__":
    main()
