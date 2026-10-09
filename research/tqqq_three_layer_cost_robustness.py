"""Fixed transaction-cost stress test using the exact frozen event-attribution inputs.

The upstream event-attribution step writes the data and signals once. This
script must not redownload prices. Zero-cost final balances are asserted
against the event-attribution summary, making data and execution drift fail CI.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from causal_execution import next_open_cost_equity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
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
    frozen=OUT/"tqqq_three_layer_frozen_inputs.csv"
    summary_path=OUT/"tqqq_three_layer_attribution_summary.csv"
    if not frozen.exists() or not summary_path.exists():
        raise FileNotFoundError("Run event attribution first to create frozen inputs and summary")
    x=pd.read_csv(frozen,parse_dates=["date"]).set_index("date")
    expected=pd.read_csv(summary_path)
    expected_finals={
        "base":float(expected.loc[expected.comparison=="conditioned_minus_base","base_final"].iloc[0]),
        "conditioned":float(expected.loc[expected.comparison=="conditioned_minus_base","comparison_final"].iloc[0]),
        "three":float(expected.loc[expected.comparison=="three_layer_minus_conditioned","comparison_final"].iloc[0]),
    }
    rows=[]
    years=(x.index[-1]-x.index[0]).days/365.2425
    for bps in COSTS_BPS:
        for name in ["base","conditioned","three"]:
            final,dd,trades=equity_with_cost(x,x[name],bps)
            rows.append({"cost_bps_per_transition":bps,"strategy":name,
                         "final":final,"cagr":(final/INITIAL)**(1/years)-1,
                         "max_dd":dd,"trades":trades})
    out=pd.DataFrame(rows)
    for name,expected_final in expected_finals.items():
        observed=float(out.loc[(out.cost_bps_per_transition==0)&
                               (out.strategy==name),"final"].iloc[0])
        if not np.isclose(observed,expected_final,rtol=1e-10,atol=1e-6):
            raise AssertionError(f"{name}: zero-cost final {observed} != frozen attribution {expected_final}")
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_three_layer_cost_robustness.csv",index=False)
    print(out.to_string(index=False))
    print("\\nTHREE-LAYER VS BASE AT EACH COST")
    p=out.pivot(index="cost_bps_per_transition",columns="strategy",values="final")
    print(p.assign(three_vs_base_ratio=p["three"]/p["base"]).to_string())
    print("\\nPASS: zero-cost balances match the attribution artifact on identical frozen inputs.")

if __name__=="__main__":
    main()
