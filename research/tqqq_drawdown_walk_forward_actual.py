"""Walk-forward validation for QQQ trailing-drawdown defenses on actual TQQQ.

Signal: QQQ adjusted-close drawdown from prior 252-session rolling high.
Execution: signal at close[t] -> actual TQQQ next session open.
No same-day execution or look-ahead.

The walk-forward procedure selects parameters only from each training interval,
then freezes them for the immediately following test interval. A separately
frozen -25% / -10% / 50% candidate is also reported for chronological
robustness, but is NOT treated as out-of-sample because it was discovered from
the broader research history.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_daily_returns

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-06"
LOOKBACK=252
ENTRIES=(-0.15,-0.20,-0.25,-0.30)
RECOVERIES=(-0.05,-0.10)
EXPOSURES=(0.25,0.50,0.75)

# Train -> immediately following test interval.
WINDOWS=(
    ("2010-2014","2010-01-01","2014-12-31","2015-01-01","2017-12-31"),
    ("2013-2017","2013-01-01","2017-12-31","2018-01-01","2020-12-31"),
    ("2016-2020","2016-01-01","2020-12-31","2021-01-01","2023-12-31"),
    ("2019-2023","2019-01-01","2023-12-31","2024-01-01","2026-10-06"),
)

def dl(ticker):
    x=yf.download(ticker,start=START,end=END,auto_adjust=False,
                  progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def data():
    q=dl("QQQ")
    t=dl("TQQQ")
    x=q[["adj_close"]].rename(columns={"adj_close":"qqq_adj_close"}).join(
        t[["open","close","adj_close"]].rename(
            columns={"open":"tqqq_open","close":"tqqq_close","adj_close":"tqqq_adj_close"}
        ),how="inner").dropna()
    x["tqqq_adj_open"]=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close
    x["overnight"]=x.tqqq_adj_open/x.tqqq_adj_close.shift(1)-1
    x["intraday"]=x.tqqq_adj_close/x.tqqq_adj_open-1
    x[["overnight","intraday"]]=x[["overnight","intraday"]].fillna(0.0)
    x["dd252"]=x.qqq_adj_close/x.qqq_adj_close.rolling(LOOKBACK).max()-1
    return x

def weights(metric,entry,recovery,exposure):
    armed=False
    out=np.ones(len(metric),dtype=float)
    for i,v in enumerate(metric.to_numpy()):
        if not np.isfinite(v):
            out[i]=1.0
            continue
        if not armed and v <= entry:
            armed=True
        elif armed and v >= recovery:
            armed=False
        out[i]=exposure if armed else 1.0
    return out

def daily(frame,w):
    return next_open_daily_returns(w,frame.overnight,frame.intraday)

def compounded(r,mask):
    z=np.asarray(r)[mask]
    return float(np.prod(1+z)-1) if len(z) else np.nan

def final_from(r,mask):
    z=np.asarray(r)[mask]
    return INITIAL*float(np.prod(1+z)) if len(z) else np.nan

def metrics(r,mask):
    z=np.asarray(r)[mask]
    if len(z)==0: return (np.nan,np.nan,np.nan)
    eq=INITIAL*np.cumprod(1+z)
    dd=eq/np.maximum.accumulate(eq)-1
    years=max((len(z)/252),1/252)
    return float(eq[-1]),float((eq[-1]/INITIAL)**(1/years)-1),float(dd.min())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x=data()
    results=[]

    # Precompute the entire causal path for every candidate.
    candidates={}
    for e in ENTRIES:
        for rec in RECOVERIES:
            if rec < e:
                continue
            for exp in EXPOSURES:
                w=weights(x.dd252,e,rec,exp)
                candidates[(e,rec,exp)]=daily(x,w)

    bh_r=daily(x,np.ones(len(x)))

    selected=[]
    for name,train_start,train_end,test_start,test_end in WINDOWS:
        train=(x.index>=train_start)&(x.index<=train_end)
        test=(x.index>=test_start)&(x.index<=test_end)
        # Select only from training history.
        ranked=[]
        for p,r in candidates.items():
            final,cagr,dd=metrics(r,train)
            ranked.append((final,cagr,dd,p))
        ranked.sort(reverse=True,key=lambda z:z[0])
        best=ranked[0]
        p=best[3]
        test_final,test_cagr,test_dd=metrics(candidates[p],test)
        bh_final,bh_cagr,bh_dd=metrics(bh_r,test)
        results.append({
            "window":name,"train_start":train_start,"train_end":train_end,
            "test_start":test_start,"test_end":test_end,
            "selected_entry":p[0],"selected_recovery":p[1],
            "selected_exposure":p[2],
            "train_final":best[0],"train_cagr":best[1],"train_dd":best[2],
            "test_final":test_final,"test_cagr":test_cagr,"test_dd":test_dd,
            "bh_test_final":bh_final,"bh_test_cagr":bh_cagr,"bh_test_dd":bh_dd,
            "test_final_delta":test_final-bh_final,
            "test_cagr_delta":test_cagr-bh_cagr,
        })
        selected.append(p)

    # Frozen candidate is a robustness control, not an OOS-selected result.
    frozen=(-0.25,-0.10,0.50)
    for name,train_start,train_end,test_start,test_end in WINDOWS:
        test=(x.index>=test_start)&(x.index<=test_end)
        ff,fc,fd=metrics(candidates[frozen],test)
        bf,bc,bd=metrics(bh_r,test)
        results.append({
            "window":name,"train_start":train_start,"train_end":train_end,
            "test_start":test_start,"test_end":test_end,
            "selected_entry":frozen[0],"selected_recovery":frozen[1],
            "selected_exposure":frozen[2],
            "train_final":np.nan,"train_cagr":np.nan,"train_dd":np.nan,
            "test_final":ff,"test_cagr":fc,"test_dd":fd,
            "bh_test_final":bf,"bh_test_cagr":bc,"bh_test_dd":bd,
            "test_final_delta":ff-bf,"test_cagr_delta":fc-bc,
        })

    out=pd.DataFrame(results)
    out.to_csv(OUT/"tqqq_drawdown_walk_forward_actual.csv",index=False)
    print(out.to_string(index=False))
    print("\nWalk-forward selected parameters:",selected)
    print("\nOOS-selected windows beating buy-and-hold:",
          int((out.iloc[:len(WINDOWS)].test_cagr_delta>0).sum()),
          "/",len(WINDOWS))
    print("Frozen -25/-10/50 windows beating buy-and-hold:",
          int((out.iloc[len(WINDOWS):].test_cagr_delta>0).sum()),
          "/",len(WINDOWS))

if __name__=="__main__":
    main()
