"""Fixed transaction-cost stress test for the frozen TQQQ three-layer architecture.

No optimization: evaluates predeclared per-transition costs of 0, 5, 10, 25,
and 50 bps against the same signals/data used by the event attribution test.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from tqqq_three_layer_event_attribution import build, INITIAL

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
COSTS_BPS=[0,5,10,25,50]

def equity_with_cost(x,sig,cost_bps):
    w=np.asarray(sig,float)
    prev=np.roll(w,1); prev[0]=0
    daily=(1+prev*x.on3.to_numpy())*(1+w*x.in3.to_numpy())-1
    turnover=np.abs(w-prev)
    cost=turnover*(cost_bps/10000.0)
    eq=INITIAL*np.cumprod(1+daily-cost)
    dd=eq/np.maximum.accumulate(eq)-1
    trades=int((turnover>0).sum())
    return float(eq[-1]),float(dd.min()),trades

def main():
    x=build()
    rows=[]
    for bps in COSTS_BPS:
        for name in ["base","conditioned","three"]:
            final,dd,trades=equity_with_cost(x,x[name],bps)
            years=(x.index[-1]-x.index[0]).days/365.2425
            cagr=(final/INITIAL)**(1/years)-1
            rows.append({"cost_bps_per_transition":bps,"strategy":name,
                         "final":final,"cagr":cagr,"max_dd":dd,"trades":trades})
    out=pd.DataFrame(rows)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_three_layer_cost_robustness.csv",index=False)
    print(out.to_string(index=False))
    print("\nTHREE-LAYER VS BASE AT EACH COST")
    p=out.pivot(index="cost_bps_per_transition",columns="strategy",values="final")
    print(p.assign(three_vs_base_ratio=p["three"]/p["base"]).to_string())

if __name__=="__main__":
    main()
