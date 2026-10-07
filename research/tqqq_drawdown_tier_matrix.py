"""QQQ trailing-high drawdown tier exposure matrix.

Signal: QQQ drawdown from a 126-session trailing high.
Execution: next open using the shared causal execution engine.
No look-ahead and no optimization of individual dates.

Exposure tiers are tested as mappings for progressively deeper QQQ drawdowns.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
INITIAL=5000.0; START="1999-03-10"; END="2026-10-06"; LOOKBACK=126

TIERS={
    "A_100_75_50_0": (1.00,0.75,0.50,0.00),
    "B_100_100_50_0":(1.00,1.00,0.50,0.00),
    "C_100_75_50_25":(1.00,0.75,0.50,0.25),
    "D_100_100_75_25":(1.00,1.00,0.75,0.25),
    "E_100_75_25_0": (1.00,0.75,0.25,0.00),
}
THRESH=(-0.15,-0.20,-0.25)

def dl(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def synthetic():
    x=dl("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).dropna()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
    return x

def actual():
    q=dl("QQQ",start="2010-01-01"); t=dl("TQQQ",start="2010-01-01")
    q=q.rename(columns={"Adj Close":"qqq_adj_close"})
    t=t.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x=q[["qqq_adj_close"]].join(t[["open","close","adj_close"]],how="inner").sort_index().dropna()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["in3"]=(x.adj_close/x.adj_open-1).fillna(0)
    return x

def exposure(dd, tiers):
    e=np.ones(len(dd))
    e[(dd<=THRESH[0])&(dd>THRESH[1])]=tiers[1]
    e[(dd<=THRESH[1])&(dd>THRESH[2])]=tiers[2]
    e[dd<=THRESH[2]]=tiers[3]
    e[~np.isfinite(dd)]=1.0
    return pd.Series(e,index=dd.index)

def run(frame,source,pxcol):
    dd=frame[pxcol]/frame[pxcol].rolling(LOOKBACK).max()-1
    rows=[]
    for name,tiers in TIERS.items():
        w=exposure(dd,tiers)
        eq=next_open_equity(w,frame.on3,frame.in3,INITIAL)
        peak=np.maximum.accumulate(eq)
        years=(frame.index[-1]-frame.index[0]).days/365.25
        rows.append(dict(source=source,tiers=name,final_balance=float(eq[-1]),
            cagr=float((eq[-1]/INITIAL)**(1/years)-1),max_drawdown=float((eq/peak-1).min()),
            avg_exposure=float(w.mean()),days_below_15=int((dd<=-.15).sum()),
            days_below_20=int((dd<=-.20).sum()),days_below_25=int((dd<=-.25).sum())))
    w=np.ones(len(frame)); eq=next_open_equity(w,frame.on3,frame.in3,INITIAL); peak=np.maximum.accumulate(eq)
    years=(frame.index[-1]-frame.index[0]).days/365.25
    rows.append(dict(source=source,tiers="BUY_HOLD",final_balance=float(eq[-1]),
        cagr=float((eq[-1]/INITIAL)**(1/years)-1),max_drawdown=float((eq/peak-1).min()),
        avg_exposure=1.0,days_below_15=0,days_below_20=0,days_below_25=0))
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=run(synthetic(),"synthetic_qqq_3x","adj_close")+run(actual(),"actual_tqqq_with_qqq_signal","qqq_adj_close")
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(OUT/"tqqq_drawdown_tier_matrix.csv",index=False)
    print(out.to_string(index=False))
if __name__=="__main__": main()

# Matrix workflow trigger validation: execute on subsequent source changes.
