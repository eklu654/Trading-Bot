"""Frozen validation of QQQ trailing-high drawdown defenses.

Primary candidate:
    126-session trailing QQQ high
    enter when QQQ drawdown <= -25%
    exit when drawdown >= -5%
    0% TQQQ while defensive

Controls:
    same rule with -15% and -20% entry thresholds.

This is a validation artifact, not an optimization pass. It reports annual
returns, crash-era drawdowns, transition dates, and execution-cost stress.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_equity, next_open_cost_equity

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.0
START="1999-03-10"; END="2026-10-06"
LOOKBACK=126; RECOVERY=-0.05; ENTRIES=(-0.15,-0.20,-0.25,-0.30,-0.35); COSTS=(0,5,10,25,50)


def dl(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None); return x.sort_index()


def qqq():
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


def signal(px,entry):
    dd=px/px.rolling(LOOKBACK).max()-1
    armed=False; w=[]; changes=[]
    for date,x in dd.items():
        old=armed
        if np.isfinite(x):
            if not armed and x<=entry: armed=True
            elif armed and x>=RECOVERY: armed=False
        w.append(0.0 if armed else 1.0)
        if armed!=old: changes.append((date,x,armed))
    return pd.Series(w,index=px.index),dd,changes


def summary(frame,source,px_col):
    rows=[]; paths=[]; transitions=[]
    for entry in ENTRIES:
        w,dd,changes=signal(frame[px_col],entry)
        for bps in COSTS:
            eq=next_open_cost_equity(w,frame.on3,frame.in3,bps,INITIAL)
            peak=np.maximum.accumulate(eq); pathdd=eq/peak-1
            years=(frame.index[-1]-frame.index[0]).days/365.25
            rows.append({"source":source,"entry":entry,"recovery":RECOVERY,
                         "bps":bps,"final_balance":float(eq[-1]),
                         "cagr":float((eq[-1]/INITIAL)**(1/years)-1),
                         "max_drawdown":float(pathdd.min()),
                         "avg_exposure":float(w.mean()),
                         "defensive_days":int((w<1).sum())})
        # transition ledger and annual return series at zero cost
        eq=next_open_equity(w,frame.on3,frame.in3,INITIAL)
        annual=pd.Series(eq,index=frame.index).resample("YE").last().pct_change()
        annual.iloc[0]=eq[0]/INITIAL-1
        for date,r in annual.items():
            paths.append({"source":source,"entry":entry,"year":date.year,
                          "strategy_return":float(r)})
        for date,x,armed in changes:
            transitions.append({"source":source,"entry":entry,
                                "date":date.date().isoformat(),
                                "qqq_drawdown":float(x),
                                "defensive":bool(armed)})
    # Buy-and-hold control, with same execution engine
    bh=np.ones(len(frame))
    for bps in COSTS:
        eq=next_open_cost_equity(bh,frame.on3,frame.in3,bps,INITIAL)
        peak=np.maximum.accumulate(eq); dd=eq/peak-1
        years=(frame.index[-1]-frame.index[0]).days/365.25
        rows.append({"source":source,"entry":"BUY_HOLD","recovery":"","bps":bps,
                     "final_balance":float(eq[-1]),
                     "cagr":float((eq[-1]/INITIAL)**(1/years)-1),
                     "max_drawdown":float(dd.min()),
                     "avg_exposure":1.0,"defensive_days":0})
    return rows,paths,transitions


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=qqq(); a=actual()
    rows,paths,trans=summary(q,"synthetic_qqq_3x","adj_close")
    r,p,t=summary(a,"actual_tqqq_with_qqq_signal","qqq_adj_close")
    rows+=r; paths+=p; trans+=t
    pd.DataFrame(rows).to_csv(OUT/"tqqq_drawdown_candidate_validation_summary.csv",index=False)
    pd.DataFrame(paths).to_csv(OUT/"tqqq_drawdown_candidate_validation_annual.csv",index=False)
    pd.DataFrame(trans).to_csv(OUT/"tqqq_drawdown_candidate_validation_transitions.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nTRANSITIONS")
    print(pd.DataFrame(trans).to_string(index=False))
    print("\nANNUAL")
    print(pd.DataFrame(paths).to_string(index=False))


if __name__=="__main__": main()
