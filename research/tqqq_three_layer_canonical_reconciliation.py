"""Canonical replay reconciliation for the frozen three-layer TQQQ architecture.

One signal ledger drives both:
1) synthetic daily-reset 3x QQQ execution, and
2) actual TQQQ adjusted open/close execution.

The purpose is to isolate signal differences from instrument-path differences.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_equity
from tqqq_three_layer_event_attribution import FED_EVENTS, RATE_THRESHOLD, SHOCK_THRESHOLD, fed_series

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-05"

def dl(t):
    x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def main():
    q=dl("QQQ"); t=dl("TQQQ"); v=dl("^VIX")[["close"]].rename(columns={"close":"vix"})
    x=q.join(v,how="left").join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="inner")
    x.vix=x.vix.ffill()
    x["dma"]=x.adj_close.rolling(100).mean()
    x["ret60"]=x.adj_close/x.adj_close.shift(60)-1
    x["daily_ret"]=x.adj_close.pct_change()
    x["rv20"]=x.daily_ret.rolling(20).std()*np.sqrt(252)
    x["vix_chg20"]=x.vix/x.vix.shift(20)-1
    x["rv_chg20"]=x.rv20/x.rv20.shift(20)-1
    x["fed"]=fed_series(x.index)
    x["base"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:99],"base"]=0
    x["veto"]=(x.adj_close<x.dma)&(x.fed>RATE_THRESHOLD)&(x.ret60>=0)
    x["shock"]=(x.vix_chg20>=SHOCK_THRESHOLD)|(x.rv_chg20>=SHOCK_THRESHOLD)
    x["conditioned"]=np.where(x.base==1,1.0,np.where(x.veto,1.0,0.0))
    x["three"]=np.where(x.base==1,1.0,np.where(x.veto&~x.shock,1.0,0.0))

    x["q_adj_open"]=x.open*x.adj_close/x.close
    x["q_on"]=(x.q_adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["q_in"]=(x.adj_close/x.q_adj_open-1).fillna(0)
    x["syn_on"]=(1+3*x.q_on).clip(lower=0)-1
    x["syn_in"]=(1+3*x.q_in).clip(lower=0)-1
    x["t_adj_open"]=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close
    x["act_on"]=(x.t_adj_open/x.tqqq_adj_close.shift(1)-1).fillna(0)
    x["act_in"]=(x.tqqq_adj_close/x.t_adj_open-1).fillna(0)

    def path(sig,on,inn):
        daily=next_open_daily_returns(sig,on,inn)
        eq=INITIAL*np.cumprod(1+daily)
        return daily,eq

    rows=[]
    for name in ["base","conditioned","three"]:
        sd,se=path(x[name],x.syn_on,x.syn_in)
        ad,ae=path(x[name],x.act_on,x.act_in)
        x[f"{name}_syn_daily"]=sd; x[f"{name}_act_daily"]=ad
        x[f"{name}_syn_eq"]=se; x[f"{name}_act_eq"]=ae
        rows.append({
            "strategy":name,
            "synthetic_final":float(se[-1]),
            "actual_final":float(ae[-1]),
            "actual_minus_synthetic":float(ae[-1]-se[-1]),
            "actual_over_synthetic":float(ae[-1]/se[-1]-1),
            "signal_days":int(x[name].sum())
        })

    # Event ledger: every day on which the three-layer position changes.
    change=x.three.ne(x.three.shift(1).fillna(0))
    ev=x.loc[change,["base","veto","shock","three","adj_close","dma","ret60","fed","vix_chg20","rv_chg20"]].copy()
    ev["event"]=np.where(ev.three.eq(1),"ENTER","EXIT")
    ev["synthetic_daily"]=x.loc[ev.index,"three_syn_daily"]
    ev["actual_daily"]=x.loc[ev.index,"three_act_daily"]
    ev["synthetic_equity"]=x.loc[ev.index,"three_syn_eq"]
    ev["actual_equity"]=x.loc[ev.index,"three_act_eq"]
    ev["actual_minus_synthetic_daily"]=ev.actual_daily-ev.synthetic_daily
    ev.reset_index(names="date").to_csv(OUT/"tqqq_three_layer_canonical_event_ledger.csv",index=False)

    # Concentration: contribution of actual-vs-synthetic path difference by calendar era.
    z=x[["three","three_syn_daily","three_act_daily"]].copy()
    z["path_gap"]=z.three_act_daily-z.three_syn_daily
    z["era"]=np.select([
        z.index<"2015-01-01",
        z.index<"2020-01-01",
        z.index<"2023-01-01"],
        ["2010-2014","2015-2019","2020-2022"],default="2023-2026")
    era=z.groupby("era").agg(days=("three","size"), invested_days=("three","sum"), mean_daily_gap=("path_gap","mean"), cumulative_gap=("path_gap","sum")).reset_index()
    era.to_csv(OUT/"tqqq_three_layer_canonical_path_gap_by_era.csv",index=False)

    summary=pd.DataFrame(rows)
    summary.to_csv(OUT/"tqqq_three_layer_canonical_reconciliation.csv",index=False)
    print(summary.to_string(index=False))
    print("\nSIGNAL CHANGES",len(ev))
    print(ev.reset_index(names="date").head(30).to_string(index=False))
    print("\nPATH GAP BY ERA")
    print(era.to_string(index=False))
    print("\nSIGNAL CONSISTENCY", bool((x.base==x.base).all()), bool((x.conditioned==np.where(x.base==1,1.0,np.where(x.veto,1.0,0.0))).all()), bool((x.three==np.where(x.base==1,1.0,np.where(x.veto&~x.shock,1.0,0.0))).all()))

if __name__=="__main__":
    main()
