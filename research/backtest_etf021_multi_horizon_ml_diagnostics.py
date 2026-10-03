"""ETF-021: multi-horizon ML bear-transition diagnostics.

Tests whether the broad ETF-020 indicator library contains stable predictive
information at several bearish horizons before another portfolio grid.
Chronology is fixed: train 2010-2019, validation 2020-2022, holdout 2023+.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline

from backtest_etf020_ml_indicator_bear_transition import make_feature_matrix

SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}

# Fixed event definitions chosen before inspecting validation/holdout.
TARGETS = {
    "5d_-2pct": (5, -0.02),
    "10d_-3pct": (10, -0.03),
    "20d_-4pct": (20, -0.04),
    "40d_-6pct": (40, -0.06),
}

MODELS = {
    "hgb_shallow": HistGradientBoostingClassifier(
        max_iter=120, learning_rate=0.05, max_leaf_nodes=7,
        min_samples_leaf=40, l2_regularization=1.0, random_state=42,
    ),
    "hgb_medium": HistGradientBoostingClassifier(
        max_iter=160, learning_rate=0.04, max_leaf_nodes=15,
        min_samples_leaf=50, l2_regularization=2.0, random_state=42,
    ),
}


def evaluate(y: pd.Series, p: pd.Series, mask: pd.Series) -> dict:
    d = pd.concat([y, p], axis=1).loc[mask].dropna()
    if len(d) == 0 or d.iloc[:, 0].nunique() < 2:
        return {"n": len(d), "positive_rate": np.nan, "roc_auc": np.nan,
                "avg_precision": np.nan, "brier": np.nan,
                "top_decile_precision": np.nan, "p90": np.nan}
    yy = d.iloc[:, 0].astype(int)
    pp = d.iloc[:, 1].astype(float)
    k = max(1, int(np.ceil(len(d) * 0.10)))
    top = pp.nlargest(k).index
    return {
        "n": len(d),
        "positive_rate": yy.mean(),
        "roc_auc": roc_auc_score(yy, pp),
        "avg_precision": average_precision_score(yy, pp),
        "brier": brier_score_loss(yy, pp),
        "top_decile_precision": yy.loc[top].mean(),
        "p90": pp.quantile(0.90),
    }


def main() -> None:
    X, _, close, _ = make_feature_matrix()
    benchmark = close[["QQQ", "SPY", "SOXX"]].mean(axis=1)
    rows = []
    masks = {name: X.index.to_series().between(*bounds)
             for name, bounds in SPLITS.items()}

    for target_name, (horizon, threshold) in TARGETS.items():
        forward = benchmark.shift(-horizon) / benchmark - 1.0
        y = (forward <= threshold).astype(float)
        y[forward.isna()] = np.nan
        train_mask = masks["train"] & y.notna()

        for model_name, model in MODELS.items():
            pipe = make_pipeline(SimpleImputer(strategy="median"), model)
            pipe.fit(X.loc[train_mask], y.loc[train_mask])
            prob = pd.Series(pipe.predict_proba(X)[:, 1], index=X.index)

            for split, mask in masks.items():
                m = evaluate(y, prob, mask & y.notna())
                m.update({
                    "target": target_name,
                    "horizon": horizon,
                    "model": model_name,
                    "split": split,
                    "forward_threshold": threshold,
                })
                rows.append(m)

    out = pd.DataFrame(rows)
    print("=== ETF-021 MULTI-HORIZON ML DIAGNOSTICS ===")
    print(out[[
        "target", "model", "split", "n", "positive_rate", "roc_auc",
        "avg_precision", "brier", "top_decile_precision", "p90",
    ]].to_string(index=False))

    print("\\n=== ETF-021 VALIDATION SUMMARY ===")
    print(out[out["split"] == "validation"]
          .sort_values(["avg_precision", "roc_auc"], ascending=False)
          .to_string(index=False))

    out_path = Path(__file__).resolve().parents[1] / "data" / "research" / "etf021_multi_horizon_ml_diagnostics.csv"\n    out.to_csv(out_path, index=False)


if __name__ == "__main__":
    main()
