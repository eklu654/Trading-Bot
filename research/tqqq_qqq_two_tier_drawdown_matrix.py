"""Predeclared two-tier QQQ drawdown defense matrix.

Normal: 100% TQQQ.
Moderate regime: reduced exposure after a persistent QQQ drawdown.
Severe regime: 0% TQQQ after a deeper QQQ drawdown.
Recovery uses hysteresis so the strategy does not immediately re-enter
full exposure while the market is still materially below its prior high.

Signals are QQQ close -> next session TQQQ open. No look-ahead.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.0
START="1999-03-10"; END="2026-10-06"
MODERATE_ENTRIES=(-0.10,-0.15,-0.20)
SEVERE_ENTRIES=(-0.20,-0.25,-0.30)
SEVERE_RECOVERIES=(-0.10,-0.15)
FULL_RECOVERIES=(-0.05,-0.10,0.0)
MODERATE_EXPOSURES=(0.25,0.50,0.75)


def dl(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def qqq():
    x=dl("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).dropna()
    x["dd252"]=x.adj_close/x.adj_close.rolling(252).max()-1
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
    return x


def actual():
    q=dl("QQQ",start="2010-01-01"); t=dl("TQQQ",start="2010-01-01")
    q=q.rename(columns={"Adj Close":"qqq_adj_close"})
    t=t.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x=q[["qqq_adj_close"]].join(t[["open","close","adj_close"]],how="inner").sort_index().dropna()
    x["dd252"]=x.qqq_adj_close/x.qqq_adj_close.rolling(252).max()-1
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["in3"]=(x.adj_close/x.adj_open-1).fillna(0)
    return x


def weights(metric,moderate_entry,severe_entry,severe_recovery,full_recovery,moderate_exposure):
    state="normal"; out=[]
    for x in metric.to_numpy():
        if not np.isfinite(x):
            out.append(1.0); continue
        if state=="normal" and x <= severe_entry:
            state="severe"
        elif state=="normal" and x <= moderate_entry:
            state="moderate"
        elif state=="moderate":
            if x <= severe_entry: state="severe"
            elif x >= full_recovery: state="normal"
        elif state=="severe":
            if x >= full_recovery: state="normal"
            elif x >= severe_recovery: state="moderate"
        out.append(0.0 if state=="severe" else (moderate_exposure if state=="moderate" else 1.0))
    return pd.Series(out,index=metric.index,dtype=float)


def evaluate(frame,source,me,se,sr,fr,exp):
    w=weights(frame.dd252,me,se,sr,fr,exp)
    eq=next_open_equity(w,frame.on3,frame.in3,INITIAL)
    peak=np.maximum.accumulate(eq); dd=eq/peak-1
    years=(frame.index[-1]-frame.index[0]).days/365.25
    row={"source":source,"moderate_entry":me,"severe_entry":se,
         "severe_recovery":sr,"full_recovery":fr,"moderate_exposure":exp,
         "final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
         "max_drawdown":float(dd.min()),"minimum_equity":float(eq.min()),
         "avg_exposure":float(w.mean()),"defensive_days":int((w<1).sum())}
    for label,a,b in [("dotcom","2000-01-01","2002-12-31"),("gfc","2007-10-01","2009-12-31"),
                      ("covid","2020-01-01","2020-12-31"),("inflation_2022","2022-01-01","2022-12-31")]:
        z=pd.Series(eq,index=frame.index).loc[a:b]
        if len(z): row[label+"_max_dd"]=float((z/z.cummax()-1).min())
    return row


def main():
    OUT.mkdir(parents=True,exist_ok=True); rows=[]
    q=qqq(); a=actual()
    for me in MODERATE_ENTRIES:
        for se in SEVERE_ENTRIES:
            if se >= me: continue
            for sr in SEVERE_RECOVERIES:
                for fr in FULL_RECOVERIES:
                    if fr < sr: continue
                    for exp in MODERATE_EXPOSURES:
                        rows.append(evaluate(q,"synthetic_qqq_3x",me,se,sr,fr,exp))
                        rows.append(evaluate(a,"actual_tqqq_with_qqq_signal",me,se,sr,fr,exp))
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(OUT/"tqqq_qqq_two_tier_drawdown_matrix.csv",index=False)
    print(out.to_string(index=False))


if __name__=="__main__": main()
