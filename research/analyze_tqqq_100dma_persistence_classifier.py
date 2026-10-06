"""Chronological persistence classification for frozen 100-DMA exits.

Target is the predeclared existing duration bucket boundary: >=20 defensive
trading days. No parameter search or random train/test split is used.

Compares:
- market-state features only
- Fed/macro features only
- combined features

Uses chronological TimeSeriesSplit and reports ROC-AUC and Brier score.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
INPUT=DATA/"tqqq_100dma_macro_episode_attribution.csv"

MARKET=[
"dma_gap_at_exit","dma_slope_20d_at_exit","qqq_return_5d_at_exit",
"qqq_return_20d_at_exit","qqq_return_60d_at_exit","qqq_realized_vol_20d_at_exit"]
MACRO=[
"fed_target_at_exit","fed_cycle_net_change","days_since_fed_move",
"fed_moves_in_cycle","fed_distance_from_cycle_peak","fed_distance_from_cycle_trough",
"curve_2s10s_at_exit","curve_change_20d_at_exit"]

def evaluate(ep, features, label):
    X=ep[features].apply(pd.to_numeric,errors="coerce")
    y=(ep["flat_trading_days"]>=20).astype(int)
    splitter=TimeSeriesSplit(n_splits=5)
    rows=[]
    for fold,(train,test) in enumerate(splitter.split(X),1):
        if y.iloc[train].nunique()<2 or y.iloc[test].nunique()<2:
            continue
        model=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced"))
        model.fit(X.iloc[train],y.iloc[train])
        p=model.predict_proba(X.iloc[test])[:,1]
        rows.append({"model":label,"fold":fold,"train_episodes":len(train),"test_episodes":len(test),
                     "test_persistent":int(y.iloc[test].sum()),
                     "roc_auc":float(roc_auc_score(y.iloc[test],p)),
                     "brier":float(brier_score_loss(y.iloc[test],p))})
    return pd.DataFrame(rows)

def main():
    ep=pd.read_csv(INPUT).sort_values("exit_date").reset_index(drop=True)
    results=pd.concat([
        evaluate(ep,MARKET,"market_only"),
        evaluate(ep,MACRO,"fed_macro_only"),
        evaluate(ep,MARKET+MACRO,"market_plus_fed_macro"),
    ],ignore_index=True)
    summary=results.groupby("model").agg(
        folds=("fold","size"),mean_roc_auc=("roc_auc","mean"),
        median_roc_auc=("roc_auc","median"),mean_brier=("brier","mean"),
        median_brier=("brier","median")).reset_index()
    results.to_csv(DATA/"tqqq_100dma_persistence_timeseries_cv.csv",index=False)
    summary.to_csv(DATA/"tqqq_100dma_persistence_timeseries_cv_summary.csv",index=False)
    print("\nPERSISTENCE TARGET")
    print(f"episodes={len(ep)} persistent_ge_20_days={int((ep.flat_trading_days>=20).sum())}")
    print("\nFOLD RESULTS")
    print(results.to_string(index=False))
    print("\nMODEL SUMMARY")
    print(summary.to_string(index=False))

if __name__=="__main__":
    main()
