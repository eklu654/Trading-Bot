"""ETF-027: signal transition/velocity diagnostics.

Use the same six family scores as ETF-026, but examine how they change from
10 to 5 to 0 sessions before de-clustered bearish event starts. This is a
diagnostic only: no portfolio returns are optimized or selected.

The purpose is to distinguish a fast transition into a bearish regime from a
market that is already heavily bearish and therefore vulnerable to reversal.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

from backtest_etf026_bear_event_archetypes import build

DATA=Path(__file__).resolve().parents[1]/"data"/"research"
EVENT_HORIZON=20
EVENT_THRESHOLD=-.04
DATES_OF_INTEREST=pd.DatetimeIndex(["2022-12-28","2024-07-09","2024-07-10","2024-07-11"])
FAMILIES=("trend","macd","channel","momentum","volatility","breadth")


def row(scores, fwd, d, label=None):
    r={"event_date":d,"forward20":float(fwd.loc[d]) if pd.notna(fwd.loc[d]) else np.nan}
    if label:
        r["label"]=label
    for fam in FAMILIES:
        vals=[float(scores.shift(l).reindex([d]).iloc[0][fam]) for l in (10,5,0)]
        r[f"{fam}_d10"],r[f"{fam}_d5"],r[f"{fam}_d0"]=vals
        r[f"{fam}_delta10to5"]=vals[1]-vals[0]
        r[f"{fam}_delta5to0"]=vals[2]-vals[1]
        r[f"{fam}_delta10to0"]=vals[2]-vals[0]
        r[f"{fam}_peak_lag"]=(10,5,0)[int(np.argmax(vals))]
        r[f"{fam}_fade5to0_ge_020"]=float(vals[1]-vals[2]>=.20)
    return r


def main():
    scores,_,fwd=build()
    events=fwd<=EVENT_THRESHOLD
    starts=events & ~events.shift(1).fillna(False)
    dates=starts[starts].index
    frame=pd.DataFrame([row(scores,fwd,d) for d in dates])
    rows=[]
    for fam in FAMILIES:
        for metric in ("d10","d5","d0","delta10to5","delta5to0","delta10to0","fade5to0_ge_020"):
            x=frame[f"{fam}_{metric}"].dropna()
            rows.append({
                "family":fam,
                "metric":metric,
                "events":len(x),
                "mean":x.mean(),
                "median":x.median(),
                "pct_positive":(x>0).mean() if metric.startswith("delta") else np.nan,
                "pct_ge_020":(x>=.20).mean() if metric.startswith("delta") else np.nan,
            })
    pd.DataFrame(rows).to_csv(DATA/"etf027_event_transition_summary.csv",index=False)

    labels={
        pd.Timestamp("2022-12-28"):"2022-12-28 false positive",
        pd.Timestamp("2024-07-09"):"2024-07-09 activation",
        pd.Timestamp("2024-07-10"):"2024-07-10 activation",
        pd.Timestamp("2024-07-11"):"2024-07-11 activation",
    }
    selected=pd.DataFrame([row(scores,fwd,d,labels[d]) for d in DATES_OF_INTEREST if d in scores.index])
    selected["qualifies_as_bear_event"]=selected["forward20"]<=EVENT_THRESHOLD
    selected.to_csv(DATA/"etf027_events_of_interest.csv",index=False)

    print("=== ETF-027 EVENT TRANSITION SUMMARY ===")
    print(pd.DataFrame(rows).to_string(index=False))
    print("\n=== ETF-027 EVENTS OF INTEREST ===")
    print(selected.to_string(index=False))


if __name__=="__main__":
    main()
