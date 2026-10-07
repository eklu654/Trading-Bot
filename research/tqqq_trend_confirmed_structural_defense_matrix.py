"""Trend-confirmed Fed + macro structural defense.

Entry requires BOTH:
    QQQ below DMA
    AND
    (Fed tightening-active/paused OR macro deterioration/crisis)

Exit:
    QQQ back above DMA.

This deliberately requires market trend confirmation for every defense
activation, preventing macro-only false positives while still distinguishing
tightening regimes from broad structural deterioration.

Grid:
    DMA 100/150/200
    defense 0/25/50/75
    close -> next open
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
EXPOSURES=(0.0,0.25,0.50,0.75)


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


def states():
    b=qqq()
    fed=build_fed_states(download_fed(),b)[["monetary_state"]]
    macro=apply_macro_states(build_synthetic(b),download_macro())[["macro_state"]]
    return b.join(fed,how="left").join(macro,how="left").ffill()


def sig(frame,dma,defense):
    close=frame["qqq_adj_close"] if "qqq_adj_close" in frame else frame["adj_close"]
    ma=close.rolling(dma).mean()
    armed=False; out=[]
    for px,m,fed,macro in zip(close.to_numpy(),ma.to_numpy(),frame.monetary_state,frame.macro_state):
        if not np.isfinite(m):
            out.append(1.0); continue
        confirm=(fed in {"TIGHTENING_ACTIVE","TIGHTENING_PAUSED"} or
                 macro in {"MACRO_DETERIORATION","MACRO_CRISIS"})
        if not armed and px < m and confirm:
            armed=True
        elif armed and px >= m:
            armed=False
        out.append(defense if armed else 1.0)
    return pd.Series(out,index=frame.index,dtype=float)


def evaluate(frame,source,dma,defense,st):
    s=st.reindex(frame.index).ffill()
    w=sig(s,dma,defense)
    eq=next_open_equity(w,frame.on3,frame.in3,INITIAL)
    peak=np.maximum.accumulate(eq); dd=eq/peak-1
    years=(frame.index[-1]-frame.index[0]).days/365.25
    return {"source":source,"dma":dma,"defense_exposure":defense,
            "final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
            "max_drawdown":float(dd.min()),"minimum_equity":float(eq.min()),
            "avg_exposure":float(w.mean()),"defensive_days":int((w<1).sum())}


def main():
    OUT.mkdir(parents=True,exist_ok=True); st=states(); rows=[]
    syn=enrich(st)
    for dma in DMAS:
        for d in EXPOSURES: rows.append(evaluate(syn,"synthetic_qqq_3x",dma,d,st))
    a=actual()
    for dma in DMAS:
        for d in EXPOSURES: rows.append(evaluate(a,"actual_tqqq_with_qqq_signal",dma,d,st))
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(OUT/"tqqq_trend_confirmed_structural_defense_matrix.csv",index=False)
    print(out.to_string(index=False))


if __name__=="__main__": main()
