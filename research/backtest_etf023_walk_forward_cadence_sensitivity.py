"""ETF-023: walk-forward ML cadence and event attribution.

ETF-022 showed a small validation/holdout portfolio improvement but very few
bear activations. This bounded sensitivity checks whether the effect survives
reasonable predeclared retraining cadences and reports the actual events.

No holdout-based cadence or threshold selection is performed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

from backtest_etf020_ml_indicator_bear_transition import (
    BULL, BEAR, FRACTIONS, SLEEVE, baseline_and_returns, make_feature_matrix, metrics,
)

TRAIN_END = pd.Timestamp("2019-12-31")
TARGET_HORIZON = 20
TARGET_THRESHOLD = -0.04
CADENCES = (21, 63, 126)
THRESHOLDS = (0.55, 0.60, 0.65)


def target(close):
    benchmark = close[["QQQ", "SPY", "SOXX"]].mean(axis=1)
    fwd = benchmark.shift(-TARGET_HORIZON) / benchmark - 1.0
    y = (fwd <= TARGET_THRESHOLD).astype(float)
    y[fwd.isna()] = np.nan
    return y, fwd


def walk(X, y, cadence):
    prob = pd.Series(np.nan, index=X.index, dtype=float)
    model = HistGradientBoostingClassifier(
        max_iter=120, learning_rate=0.05, max_leaf_nodes=7,
        min_samples_leaf=40, l2_regularization=1.0, random_state=42,
    )
    pipe = make_pipeline(SimpleImputer(strategy="median"), model)
    pred = X.index[X.index > TRAIN_END]
    for i, date in enumerate(pred):
        if i % cadence == 0:
            m = (X.index < date) & y.notna()
            pipe.fit(X.loc[m], y.loc[m])
        prob.loc[date] = pipe.predict_proba(X.loc[[date]])[:, 1][0]
    return prob


def bull_states(X):
    out = {}
    root = __import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "research"
    for s in BULL:
        c = pd.read_csv(root / f"{s.lower()}_daily.csv", parse_dates=["Date"]).set_index("Date")["close"]
        c = c.reindex(X.index).ffill()
        ma = c.rolling(200, min_periods=200).mean()
        state = pd.Series(False, index=X.index)
        active = False
        count = 0
        for d, p, m in zip(X.index, c, ma):
            if pd.isna(m) or p < m:
                active, count = False, 0
            elif not active:
                count += 1
                if count >= 5:
                    active = True
            state.loc[d] = active
        out[s] = state.shift(1).fillna(False)
    return out


def portfolio(prob, baseline, ret, states, threshold, fraction):
    gate = (prob >= threshold).shift(1).fillna(False).astype(bool)
    daily = baseline.copy()
    for s in BULL:
        daily = (
            daily
            - SLEEVE * ret[s].where(states[s], 0.0)
            + SLEEVE * ret[s].where(states[s] & ~gate, 0.0)
            + SLEEVE * fraction * ret[BEAR[s]].where(gate, 0.0)
        )
    return daily, gate


def main():
    X, _, close, _ = make_feature_matrix()
    y, fwd = target(close)
    ret, baseline = baseline_and_returns(close)
    states = bull_states(X)
    valid = (X.index >= "2020-01-01") & (X.index <= "2022-12-31")
    hold = X.index >= "2023-01-01"

    rows = []
    predictions = {}
    for cadence in CADENCES:
        prob = walk(X, y, cadence)
        predictions[cadence] = prob
        for threshold in THRESHOLDS:
            daily, gate = portfolio(prob, baseline, ret, states, threshold, 1.0)
            m = metrics(daily.loc[valid])
            b = metrics(baseline.loc[valid])
            rows.append({
                "cadence": cadence, "threshold": threshold,
                "validation_return": m[0], "validation_sharpe": m[3],
                "validation_dd": m[1], "baseline_sharpe": b[3],
                "bear_days": int(gate.loc[valid].sum()),
            })

    out = pd.DataFrame(rows)
    out["sharpe_delta"] = out.validation_sharpe - out.baseline_sharpe
    print("=== ETF-023 VALIDATION CADENCE SENSITIVITY ===")
    print(out.sort_values(["sharpe_delta", "validation_return"], ascending=False).to_string(index=False))

    # Cadence/threshold is selected only from validation.
    winner = out.sort_values(["sharpe_delta", "validation_return"], ascending=False).iloc[0]
    prob = predictions[int(winner.cadence)]
    daily, gate = portfolio(prob, baseline, ret, states, float(winner.threshold), 1.0)
    h = metrics(daily.loc[hold])
    b = metrics(baseline.loc[hold])

    print("\\n=== ETF-023 SELECTED HOLDOUT ===")
    print(pd.DataFrame([{
        "cadence": winner.cadence,
        "threshold": winner.threshold,
        "holdout_return": h[0],
        "holdout_sharpe": h[3],
        "holdout_dd": h[1],
        "baseline_return": b[0],
        "baseline_sharpe": b[3],
        "bear_days": int(gate.loc[hold].sum()),
    }]).to_string(index=False))

    events = pd.DataFrame({
        "trigger_probability": prob.shift(1),
        "gate_for_session": gate,
        "forward20_benchmark_return": fwd,
    })
    events = events.loc[gate & (events.index >= "2020-01-01"), :]
    print("\\n=== ETF-023 BEAR EVENTS ===")
    print(events.to_string())


if __name__ == "__main__":
    main()
