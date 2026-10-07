"""Predeclared QQQ drawdown/return regime matrix.

No DMA is required for entry. The hypothesis is that the dot-com failure is
primarily a large, persistent QQQ drawdown regime rather than a single moving
average crossing. Signals are QQQ-only and execute at next TQQQ open.

Two trigger families:
1. trailing-252-day drawdown from the prior rolling high
2. trailing-63-day return

Entry threshold and recovery threshold are frozen grids. Defense is sticky
until the QQQ metric recovers above the recovery threshold.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.0
START="1999-03-10"; END="2026-10-06"
ENTRY_DD=(-0.10,-0.15,-0.20,-0.25)
RECOVERY_DD=(-0.05,-0.10,0.0)
ENTRY_RET=(-0.10,-0.15,-0.20,-0.25)
RECOVERY_RET=(-0.05,-0.10,0.0)
EXPOSURES=(0.0,0.25,0.50,0.75)


def dl(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def qqq():
    x=dl("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x=x.dropna(subset=["open","close","adj_close"])
    x["dd252"]=x.adj_close/x.adj_close.rolling(252).max()-1
    x["ret63"]=x.adj_close/x.adj_close.shift(63)-1
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
    x["ret63"]=x.qqq_adj_close/x.qqq_adj_close.shift(63)-1
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["in3"]=(x.adj_close/x.adj_open-1).fillna(0)
    return x


def weights(metric,entry,recovery,exposure):
    armed=False; out=[]
    for x in metric.to_numpy():
        if not np.isfinite(x):
            out.append(1.0); continue
        if not armed and x <= entry: armed=True
        elif armed and x >= recovery: armed=False
        out.append(exposure if armed else 1.0)
    return pd.Series(out,index=metric.index,dtype=float)


def evaluate(frame,source,family,entry,recovery,exposure):
    metric=frame["dd252"] if family=="drawdown" else frame["ret63"]
    w=weights(metric,entry,recovery,exposure)
    eq=next_open_equity(w,frame.on3,frame.in3,INITIAL)
    peak=np.maximum.accumulate(eq); dd=eq/peak-1
    years=(frame.index[-1]-frame.index[0]).days/365.25
    row={"source":source,"family":family,"entry_threshold":entry,
         "recovery_threshold":recovery,"defense_exposure":exposure,
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
    q=qqq()
    for fam,entries,recoveries in [("drawdown",ENTRY_DD,RECOVERY_DD),("return",ENTRY_RET,RECOVERY_RET)]:
        for e in entries:
            for r in recoveries:
                if r < e: continue
                for exp in EXPOSURES:
                    rows.append(evaluate(q,"synthetic_qqq_3x",fam,e,r,exp))
    a=actual()
    for fam,entries,recoveries in [("drawdown",ENTRY_DD,RECOVERY_DD),("return",ENTRY_RET,RECOVERY_RET)]:
        for e in entries:
            for r in recoveries:
                if r < e: continue
                for exp in EXPOSURES:
                    rows.append(evaluate(a,"actual_tqqq_with_qqq_signal",fam,e,r,exp))
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(OUT/"tqqq_qqq_drawdown_return_regime_matrix.csv",index=False)
    print(out.to_string(index=False))


if __name__=="__main__": main()
