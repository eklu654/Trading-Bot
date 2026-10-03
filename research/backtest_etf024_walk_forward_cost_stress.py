"""ETF-024: transaction-cost stress for the frozen ETF-023 signal.

Uses the already selected walk-forward cadence (63 sessions), probability
threshold (0.60), and 100% inverse sleeve allocation. No re-selection is
performed here. Compares the candidate and canonical baseline under 10/25/50/100
bps per unit one-way turnover.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_etf020_ml_indicator_bear_transition import (
    BULL, BEAR, SLEEVE, baseline_and_returns, make_feature_matrix, metrics,
)
from backtest_etf023_walk_forward_cadence_sensitivity import (
    TARGET_HORIZON, TARGET_THRESHOLD, TRAIN_END, bull_states, target, walk,
)

COSTS_BPS = (10, 25, 50, 100)


def weights(index, prob, states):
    gate = (prob >= 0.60).shift(1).fillna(False).astype(bool)
    w = pd.DataFrame(0.0, index=index, columns=list(BULL) + list(BEAR.values()))
    for s in BULL:
        w.loc[:, s] = SLEEVE * (states[s] & ~gate).astype(float)
        w.loc[:, BEAR[s]] = SLEEVE * gate.astype(float)
    return w


def baseline_weights(index, states):
    w = pd.DataFrame(0.0, index=index, columns=BULL)
    for s in BULL:
        w.loc[:, s] = SLEEVE * states[s].astype(float)
    return w


def net(gross, w, cost_bps):
    turnover = w.diff().abs().sum(axis=1).fillna(0.0)
    return gross - turnover * (cost_bps / 10000.0), turnover


def main():
    X, _, close, _ = make_feature_matrix()
    _, baseline = baseline_and_returns(close)
    ret, _ = baseline_and_returns(close)
    y, _ = target(close)
    prob = walk(X, y, 63)
    states = bull_states(X)

    candidate = baseline.copy()
    gate = (prob >= 0.60).shift(1).fillna(False).astype(bool)
    for s in BULL:
        candidate = (
            candidate
            - SLEEVE * ret[s].where(states[s], 0.0)
            + SLEEVE * ret[s].where(states[s] & ~gate, 0.0)
            + SLEEVE * ret[BEAR[s]].where(gate, 0.0)
        )

    cw = weights(X.index, prob, states)
    bw = baseline_weights(X.index, states)

    masks = {
        "validation": (X.index >= "2020-01-01") & (X.index <= "2022-12-31"),
        "holdout": X.index >= "2023-01-01",
    }

    rows = []
    for split, mask in masks.items():
        for label, gross, w in (
            ("candidate", candidate, cw),
            ("baseline", baseline, bw),
        ):
            for bps in COSTS_BPS:
                nr, turnover = net(gross, w, bps)
                m = metrics(nr.loc[mask])
                rows.append({
                    "split": split, "strategy": label, "cost_bps": bps,
                    "annualized_return": m[0], "max_drawdown": m[1],
                    "sharpe": m[3], "ending_value_5000": m[4],
                    "turnover": turnover.loc[mask].sum(),
                })

    out = pd.DataFrame(rows)
    print("=== ETF-024 TRANSACTION-COST STRESS ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
