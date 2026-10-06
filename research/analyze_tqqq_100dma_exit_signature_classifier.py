"""Outcome-blind classification of initial 100-DMA break signatures.

Purpose: test whether shock/volatility acceleration adds predictive power to the
existing market-state persistence classifier. No threshold optimization is used.

Targets:
- persistence: defensive exit lasts >=20 trading days
- severe: buy-and-hold synthetic 3x QQQ drawdown during the episode reaches <=-50%

Evaluation is chronological TimeSeriesSplit with logistic regression. Feature
groups are fixed before looking at model results.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
INPUT = DATA / "tqqq_100dma_exit_signatures.csv"

MARKET = [
    "dma_gap", "dma_slope20", "ret5", "ret20", "ret60", "vol20",
]
SHOCK = [
    "ret5", "vol20", "vol_change20", "qqq_overnight5", "qqq_intraday5",
    "vix", "vix_change5", "vix_change20",
]
MACRO = [
    "fed_target", "fed_cycle_change", "days_since_fed_move",
    "curve_2s10s", "curve_change20",
]
GROUPS = {
    "market_only": MARKET,
    "shock_only": SHOCK,
    "fed_macro_only": MACRO,
    "market_plus_shock": MARKET + [x for x in SHOCK if x not in MARKET],
    "market_plus_fed_macro": MARKET + [x for x in MACRO if x not in MARKET],
    "all_features": MARKET + [x for x in SHOCK if x not in MARKET] + [x for x in MACRO if x not in MARKET],
}

def evaluate(ep, features, target, label):
    X = ep[features].apply(pd.to_numeric, errors="coerce")
    y = ep[target].astype(int)
    splitter = TimeSeriesSplit(n_splits=5)
    rows = []
    for fold, (train, test) in enumerate(splitter.split(X), 1):
        if y.iloc[train].nunique() < 2 or y.iloc[test].nunique() < 2:
            continue
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=3000),
        )
        model.fit(X.iloc[train], y.iloc[train])
        p = model.predict_proba(X.iloc[test])[:, 1]
        rows.append({
            "target": target, "model": label, "fold": fold,
            "train_episodes": len(train), "test_episodes": len(test),
            "test_positive": int(y.iloc[test].sum()),
            "roc_auc": float(roc_auc_score(y.iloc[test], p)),
            "brier": float(brier_score_loss(y.iloc[test], p)),
        })
    return pd.DataFrame(rows)

def main():
    ep = pd.read_csv(INPUT).sort_values("exit_date").reset_index(drop=True)
    ep["persistent_20d"] = ep["flat_days"] >= 20
    ep["severe_50pct"] = ep["bh_worst_return"] <= -0.5

    results = []
    for target in ("persistent_20d", "severe_50pct"):
        for label, features in GROUPS.items():
            results.append(evaluate(ep, features, target, label))
    results = pd.concat(results, ignore_index=True)

    summary = (
        results.groupby(["target", "model"])
        .agg(
            folds=("fold", "size"),
            mean_roc_auc=("roc_auc", "mean"),
            median_roc_auc=("roc_auc", "median"),
            mean_brier=("brier", "mean"),
            median_brier=("brier", "median"),
        )
        .reset_index()
    )
    summary.to_csv(DATA / "tqqq_100dma_exit_signature_cv_summary.csv", index=False)
    results.to_csv(DATA / "tqqq_100dma_exit_signature_cv_folds.csv", index=False)

    print("\nDATASET")
    print(f"episodes={len(ep)} persistent_20d={int(ep.persistent_20d.sum())} severe_50pct={int(ep.severe_50pct.sum())}")
    print("\nSUMMARY")
    print(summary.to_string(index=False))
    print("\nFOLDS")
    print(results.to_string(index=False))

if __name__ == "__main__":
    main()
