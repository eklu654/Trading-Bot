"""Fixed transaction-cost stress test for the frozen TQQQ three-layer architecture.

No optimization: evaluates predeclared per-transition costs of 0, 5, 10, 25,
and 50 bps against the exact causal execution convention used by event
attribution. At 0 bps, this script must reproduce event-attribution terminal
equity for each signal; a regression assertion enforces that.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from tqqq_three_layer_event_attribution import build, INITIAL, equity
from causal_execution import next_open_cost_equity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
COSTS_BPS=[0,5,10,25,50]

def equity_with_cost(x, sig, cost_bps):
    wealth=next_open_cost_equity(sig, x.on3.to_numpy(), x.in3.to_numpy(),
                                 cost_bps, INITIAL)
    dd=wealth/np.maximum.accumulate(wealth)-1
    w=np.asarray(sig,float)
    exec_w=np.roll(w,1); exec_w[0]=0.0
    prev_exec=np.roll(exec_w,1); prev_exec[0]=0.0
    trades=int((np.abs(exec_w-prev_exec)>0).sum())
    return float(wealth[-1]),float(dd.min()),trades

def main():
    x=build()
    rows=[]
    years=(x.index[-1]-x.index[0]).days/365.2425
    for bps in COSTS_BPS:
        for name in ["base","conditioned","three"]:
            final,dd,trades=equity_with_cost(x,x[name],bps)
            rows.append({"cost_bps_per_transition":bps,"strategy":name,
                         "final":final,"cagr":(final/INITIAL)**(1/years)-1,
                         "max_dd":dd,"trades":trades})
    out=pd.DataFrame(rows)
    # Exact zero-cost agreement with the independently maintained attribution
    # engine is a hard gate, not a visual comparison.
    for name in ["base","conditioned","three"]:
        expected=float(equity(x,x[name])[-1])
        observed=float(out.loc[(out.cost_bps_per_transition==0)&
                               (out.strategy==name),"final"].iloc[0])
        if not np.isclose(observed,expected,rtol=1e-12,atol=1e-7):
            raise AssertionError(f"{name}: zero-cost final {observed} != causal reference {expected}")
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_three_layer_cost_robustness.csv",index=False)
    print(out.to_string(index=False))
    print("\\nTHREE-LAYER VS BASE AT EACH COST")
    p=out.pivot(index="cost_bps_per_transition",columns="strategy",values="final")
    print(p.assign(three_vs_base_ratio=p["three"]/p["base"]).to_string())
    print("\\nPASS: zero-cost balances match event-attribution engine exactly.")

if __name__=="__main__":
    main()
