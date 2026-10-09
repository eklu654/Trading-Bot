"""Predeclared structural + fast-shock defense matrix.

Purpose: test whether a regime detector can solve the core failure:
buy-and-hold survives growth but is unacceptable through the dot-com crash,
while fixed-DMA defenses either react too late or sacrifice too much upside.

Causal rule:
- QQQ close is the signal source.
- Signal executes at next session open.
- Defense is sticky until QQQ closes back above the structural DMA.
- Structural entry requires QQQ below structural DMA AND 50-DMA below
  200-DMA (trend deterioration).
- Fast-shock override requires QQQ below the fast DMA AND at least one of:
  63-day QQQ return <= threshold,
  252-day drawdown <= threshold,
  VIX >= threshold.
- Shock override is hard defense (0% TQQQ).
- Structural-only defense uses a predeclared 25/50/75% exposure family.

This is a research matrix, not a tuned production strategy.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="1999-03-10"
END="2026-10-06"

STRUCTURAL_DMAS=(100,150,200)
FAST_DMAS=(50,100)
STRUCTURAL_EXPOSURES=(0.25,0.50,0.75)
RET_THRESHOLDS=(-0.15,-0.20)
DD_THRESHOLDS=(-0.20,-0.25)
VIX_THRESHOLDS=(28.0,30.0)


def download(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def qqq_frame():
    q=download("QQQ")
    q=q.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    q=q.dropna(subset=["open","close","adj_close"])
    q["dma50"]=q.adj_close.rolling(50).mean()
    q["dma100"]=q.adj_close.rolling(100).mean()
    q["dma150"]=q.adj_close.rolling(150).mean()
    q["dma200"]=q.adj_close.rolling(200).mean()
    q["ret63"]=q.adj_close/q.adj_close.shift(63)-1
    q["dd252"]=q.adj_close/q.adj_close.rolling(252).max()-1
    q["adj_open"]=q.open*q.adj_close/q.close
    q["on3"]=((1+3*(q.adj_open/q.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    q["in3"]=((1+3*(q.adj_close/q.adj_open-1)).clip(lower=0)-1).fillna(0)
    v=download("^VIX")[["Close"]].rename(columns={"Close":"vix"})
    q=q.join(v,how="left")
    q.vix=q.vix.ffill()
    return q.dropna(subset=["vix"])


def actual_tqqq():
    q=download("QQQ",start="2010-01-01")
    t=download("TQQQ",start="2010-01-01")
    q=q.rename(columns={"Adj Close":"qqq_adj_close"})
    t=t.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x=q[["qqq_adj_close"]].join(t[["open","close","adj_close"]],how="inner").sort_index().dropna()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["in3"]=(x.adj_close/x.adj_open-1).fillna(0)
    return x


def signal(q,struct_dma,fast_dma,ret_thr,dd_thr,vix_thr,exposure):
    ma=q[f"dma{struct_dma}"]
    fast=q[f"dma{fast_dma}"]
    armed=False
    hard=False
    out=[]
    for px,m,f,r,d,v in zip(q.adj_close.to_numpy(),ma.to_numpy(),fast.to_numpy(),
                            q.ret63.to_numpy(),q.dd252.to_numpy(),q.vix.to_numpy()):
        if not np.isfinite(m) or not np.isfinite(f):
            out.append(1.0)
            continue
        structural=(px < m and f < m)
        shock=(px < f and ((r <= ret_thr) or (d <= dd_thr) or (v >= vix_thr)))
        if not armed and (structural or shock):
            armed=True
            hard=shock
        elif armed:
            if px >= m:
                armed=False
                hard=False
            elif shock:
                hard=True
        out.append(0.0 if hard else (exposure if armed else 1.0))
    return pd.Series(out,index=q.index,dtype=float)


def eval_frame(frame,source,signal_index,signal_series,struct_dma,fast_dma,ret_thr,dd_thr,vix_thr,exposure):
    s=signal_series.reindex(frame.index).ffill()
    eq=next_open_equity(s,frame.on3,frame.in3,INITIAL)
    peak=np.maximum.accumulate(eq); dd=eq/peak-1
    years=(frame.index[-1]-frame.index[0]).days/365.25
    row={
        "source":source,"structural_dma":struct_dma,"fast_dma":fast_dma,
        "ret63_threshold":ret_thr,"dd252_threshold":dd_thr,
        "vix_threshold":vix_thr,"structural_exposure":exposure,
        "final_balance":float(eq[-1]),
        "cagr":float((eq[-1]/INITIAL)**(1/years)-1),
        "max_drawdown":float(dd.min()),
        "minimum_equity":float(eq.min()),
        "avg_exposure":float(s.mean()),
        "defensive_days":int((s<1).sum()),
    }
    for label,a,b in [("dotcom","2000-01-01","2002-12-31"),
                      ("gfc","2007-10-01","2009-12-31"),
                      ("covid","2020-01-01","2020-12-31"),
                      ("inflation_2022","2022-01-01","2022-12-31")]:
        z=pd.Series(eq,index=frame.index).loc[a:b]
        if len(z):
            row[label+"_max_dd"]=float((z/z.cummax()-1).min())
    return row


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=qqq_frame()
    rows=[]
    for sd in STRUCTURAL_DMAS:
        for fd in FAST_DMAS:
            for rt in RET_THRESHOLDS:
                for dt in DD_THRESHOLDS:
                    for vt in VIX_THRESHOLDS:
                        for exp in STRUCTURAL_EXPOSURES:
                            sig=signal(q,sd,fd,rt,dt,vt,exp)
                            rows.append(eval_frame(q,"synthetic_qqq_3x",q.index,sig,sd,fd,rt,dt,vt,exp))
    a=actual_tqqq()
    aq=q.reindex(a.index).ffill()
    for sd in STRUCTURAL_DMAS:
        for fd in FAST_DMAS:
            for rt in RET_THRESHOLDS:
                for dt in DD_THRESHOLDS:
                    for vt in VIX_THRESHOLDS:
                        for exp in STRUCTURAL_EXPOSURES:
                            sig=signal(aq,sd,fd,rt,dt,vt,exp)
                            rows.append(eval_frame(a,"actual_tqqq_with_qqq_signal",a.index,sig,sd,fd,rt,dt,vt,exp))
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(OUT/"tqqq_structural_shock_defense_matrix.csv",index=False)
    print(out.to_string(index=False))


if __name__=="__main__":
    main()


# Re-run audit checkpoint: 2026-10-09; no strategy logic changed.
