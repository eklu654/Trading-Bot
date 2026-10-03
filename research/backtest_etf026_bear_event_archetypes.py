"""ETF-026: bearish-event archetype diagnostics.

Compare successful/failure bearish-transition events without optimizing a trading
strategy. The goal is to determine whether the July 2024 walk-forward ML cluster
shared observable technical characteristics with earlier sustained declines.

Events are defined ex ante as benchmark forward 20-session return <= -4%.
For each event, record six interpretable signal-family scores on the event date
and 5/10 sessions earlier. Also report the 2022-12-28 false-positive date and
the July 2024 cluster explicitly.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
UNDER=("QQQ","SPY","SOXX","DIA","IWM")
EVENT_HORIZON=20
EVENT_THRESHOLD=-.04
DATES_OF_INTEREST=pd.DatetimeIndex(["2022-12-28","2024-07-09","2024-07-10","2024-07-11"])


def load(s):
    return pd.read_csv(DATA/f"{s.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def build():
    frames={s:load(s) for s in UNDER}
    idx=frames["QQQ"].index
    c=pd.concat({s:frames[s]["close"].reindex(idx).ffill() for s in UNDER},axis=1)
    families={k:[] for k in ("trend","macd","channel","momentum")}
    for s in UNDER:
        x=c[s]
        ma200=x.rolling(200,min_periods=200).mean()
        ma50=x.rolling(50,min_periods=50).mean()
        slope=ma200.pct_change(20)
        line=x.ewm(span=12,adjust=False).mean()-x.ewm(span=26,adjust=False).mean()
        sig=line.ewm(span=9,adjust=False).mean()
        hist=line-sig
        families["trend"].append(pd.concat([(x<ma200).astype(float),(slope<0).astype(float),(ma50<ma200).astype(float)],axis=1).mean(axis=1))
        families["macd"].append(pd.concat([(line<sig).astype(float),(hist<0).astype(float),(hist.diff(5)<0).astype(float)],axis=1).mean(axis=1))
        families["channel"].append(pd.concat([(x<x.rolling(20,min_periods=20).min().shift(1)).astype(float),(x<x.rolling(40,min_periods=40).min().shift(1)).astype(float),(x<x.rolling(60,min_periods=60).min().shift(1)).astype(float)],axis=1).mean(axis=1))
        families["momentum"].append(pd.concat([(x.pct_change(20)<0).astype(float),(x.pct_change(60)<0).astype(float)],axis=1).mean(axis=1))
    out=pd.DataFrame({k:pd.concat(v,axis=1).mean(axis=1) for k,v in families.items()})
    v=pd.read_csv(DATA/"vix_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["vix"].reindex(idx).ffill()
    rank=v.rolling(253,min_periods=60).rank(pct=True)
    out["volatility"]=pd.concat([(rank>=.70).astype(float),(v.pct_change(5)>0).astype(float)],axis=1).mean(axis=1)
    breadth=(c<c.rolling(200,min_periods=200).mean()).mean(axis=1)
    macdb=[]
    for s in UNDER:
        line=c[s].ewm(span=12,adjust=False).mean()-c[s].ewm(span=26,adjust=False).mean()
        sig=line.ewm(span=9,adjust=False).mean()
        macdb.append((line<sig).astype(float))
    out["breadth"]=pd.concat([breadth,pd.concat(macdb,axis=1).mean(axis=1)],axis=1).mean(axis=1)
    benchmark=c[["QQQ","SPY","SOXX"]].mean(axis=1)
    fwd=benchmark.shift(-EVENT_HORIZON)/benchmark-1
    return out,benchmark,fwd


def main():
    scores,bench,fwd=build()
    events=fwd<=EVENT_THRESHOLD
    # De-cluster consecutive qualifying dates so one selloff does not dominate
    # the event count. The first qualifying day starts an event.
    starts=events & ~events.shift(1).fillna(False)
    dates=starts[starts].index
    rows=[]
    for d in dates:
        row={"event_date":d,"forward20":float(fwd.loc[d])}
        for lag in (0,5,10):
            base=scores.shift(lag).reindex([d]).iloc[0]
            for fam in scores.columns:
                row[f"{fam}_d{abs(lag)}"]=float(base[fam])
        rows.append(row)
    event_frame=pd.DataFrame(rows)
    event_frame.to_csv(DATA/"etf026_bear_event_archetypes.csv",index=False)

    selected=event_frame[event_frame.event_date.isin(DATES_OF_INTEREST)].copy()
    selected.to_csv(DATA/"etf026_events_of_interest.csv",index=False)

    summary=[]
    for fam in scores.columns:
        for lag in (0,5,10):
            col=f"{fam}_d{lag}"
            x=event_frame[col].dropna()
            summary.append({"family":fam,"days_before":lag,"events":len(x),"mean_score":x.mean(),"median_score":x.median(),"pct_ge_0.67":(x>=.67).mean(),"pct_ge_0.50":(x>=.50).mean()})
    pd.DataFrame(summary).to_csv(DATA/"etf026_event_family_summary.csv",index=False)

    print("=== ETF-026 BEAR EVENT ARCHETYPES ===")
    print(event_frame.to_string(index=False))
    print("\n=== EVENTS OF INTEREST ===")
    print(selected.to_string(index=False))
    print("\n=== FAMILY SUMMARY ===")
    print(pd.DataFrame(summary).to_string(index=False))


if __name__=="__main__":
    main()
