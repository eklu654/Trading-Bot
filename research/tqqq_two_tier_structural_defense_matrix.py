"""Two-tier structural defense: hard macro defense + lighter Fed/DMA defense.

Frozen hierarchy:
1. MACRO_DETERIORATION or MACRO_CRISIS -> 0% TQQQ.
2. Otherwise, QQQ below DMA while Fed is TIGHTENING_ACTIVE or
   TIGHTENING_PAUSED -> reduced TQQQ exposure.
3. Otherwise -> 100%.

Sticky state exits only when QQQ is back above DMA AND macro is structural
expansion. Fed-aware reduced exposures are predeclared at 25/50/75%.

This is intended to separate prolonged structural deterioration (dot-com/GFC)
from monetary-tightening drawdowns (2022), rather than using one exposure for
both regimes.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from research.test_tqqq_macro_regime import download_macro, apply_macro_states, build_synthetic
from research.test_tqqq_fed_paused_dma_sticky import download_fed, build_daily_states as build_fed_states
from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="1999-03-10"
END="2026-10-06"
DMAS=(100,150,200)
FED_EXPOSURES=(0.25,0.50,0.75)


def qqq():
    x=yf.download("QQQ",start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x=x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna(subset=["open","close","adj_close"])


def actual():
    q=yf.download("QQQ",start="2010-01-01",end=END,auto_adjust=False,progress=False,actions=False)
    t=yf.download("TQQQ",start="2010-01-01",end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(q.columns,pd.MultiIndex): q.columns=q.columns.get_level_values(0)
    if isinstance(t.columns,pd.MultiIndex): t.columns=t.columns.get_level_values(0)
    q.index=pd.to_datetime(q.index).tz_localize(None); t.index=pd.to_datetime(t.index).tz_localize(None)
    q=q.rename(columns={"Adj Close":"qqq_adj_close"})
    t=t.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x=q[["qqq_adj_close"]].join(t[["open","close","adj_close"]],how="inner").sort_index().dropna()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["in3"]=(x.adj_close/x.adj_open-1).fillna(0)
    return x


def enrich(x):
    x=x.copy()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
    return x


def state_frame():
    b=qqq()
    fed=build_fed_states(download_fed(),b)[["monetary_state"]]
    macro=apply_macro_states(build_synthetic(b),download_macro())[["macro_state"]]
    return b.join(fed,how="left").join(macro,how="left").ffill()


def signal(frame,dma,fed_exposure):
    close=frame["qqq_adj_close"] if "qqq_adj_close" in frame else frame["adj_close"]
    ma=close.rolling(dma).mean()
    armed=False
    out=[]
    for px,m,fed,macro in zip(close.to_numpy(),ma.to_numpy(),frame.monetary_state,frame.macro_state):
        if not np.isfinite(m):
            out.append(1.0); continue
        macro_hard=macro in {"MACRO_DETERIORATION","MACRO_CRISIS"}
        fed_defense=(px < m and fed in {"TIGHTENING_ACTIVE","TIGHTENING_PAUSED"})
        if not armed and (macro_hard or fed_defense):
            armed=True
        elif armed and px >= m and macro=="STRUCTURAL_EXPANSION":
            armed=False
        if armed:
            out.append(0.0 if macro_hard else fed_exposure)
        else:
            out.append(1.0)
    return pd.Series(out,index=frame.index,dtype=float)


def evaluate(frame,source,dma,exp,states):
    st=states.reindex(frame.index).ffill()
    sig=signal(st,dma,exp)
    eq=next_open_equity(sig,frame.on3,frame.in3,INITIAL)
    peak=np.maximum.accumulate(eq); dd=eq/peak-1
    years=(frame.index[-1]-frame.index[0]).days/365.25
    return {"source":source,"dma":dma,"fed_defense_exposure":exp,
            "final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
            "max_drawdown":float(dd.min()),"minimum_equity":float(eq.min()),
            "avg_exposure":float(sig.mean()),"defensive_days":int((sig<1).sum())}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    st=state_frame(); rows=[]
    syn=enrich(st)
    for dma in DMAS:
        for exp in FED_EXPOSURES:
            rows.append(evaluate(syn,"synthetic_qqq_3x",dma,exp,st))
    a=actual()
    for dma in DMAS:
        for exp in FED_EXPOSURES:
            rows.append(evaluate(a,"actual_tqqq_with_qqq_signal",dma,exp,st))
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(OUT/"tqqq_two_tier_structural_defense_matrix.csv",index=False)
    print(out.to_string(index=False))


if __name__=="__main__":
    main()
