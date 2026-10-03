"""ETF-019 diagnostic: measure bearish-signal lead time and false triggers.

This is a diagnostic, not a trading strategy. It asks which signal families
actually arrive before sustained weakness, so future composite rules can be
constructed from causal sequence rather than another blind total-return grid.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
UNDER=("QQQ","SPY","SOXX","DIA","IWM")
FAMILIES=("trend","macd","channel","momentum","volatility","breadth")


def load(s):
    return pd.read_csv(DATA/f"{s.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def features():
    prices={s:load(s)["close"] for s in UNDER}
    idx=pd.concat(prices,axis=1).dropna().index
    m=pd.concat({s:prices[s].reindex(idx) for s in UNDER},axis=1)
    out={}
    trend=[]; macd=[]; channel=[]; momentum=[]
    for _,c in m.items():
        ma200=c.rolling(200,min_periods=200).mean()
        ma50=c.rolling(50,min_periods=50).mean()
        slope=ma200.pct_change(20)
        ema12=c.ewm(span=12,adjust=False).mean()
        ema26=c.ewm(span=26,adjust=False).mean()
        line=ema12-ema26
        sig=line.ewm(span=9,adjust=False).mean()
        hist=line-sig
        trend.append(pd.concat([(c<ma200).astype(float),(slope<0).astype(float),(ma50<ma200).astype(float)],axis=1).mean(axis=1))
        macd.append(pd.concat([(line<sig).astype(float),(hist<0).astype(float),(hist.diff(5)<0).astype(float)],axis=1).mean(axis=1))
        channel.append(pd.concat([(c<c.rolling(20,min_periods=20).min().shift(1)).astype(float),(c<c.rolling(40,min_periods=40).min().shift(1)).astype(float),(c<c.rolling(60,min_periods=60).min().shift(1)).astype(float)],axis=1).mean(axis=1))
        momentum.append(pd.concat([(c.pct_change(20)<0).astype(float),(c.pct_change(60)<0).astype(float)],axis=1).mean(axis=1))
    out["trend"]=pd.concat(trend,axis=1).mean(axis=1)
    out["macd"]=pd.concat(macd,axis=1).mean(axis=1)
    out["channel"]=pd.concat(channel,axis=1).mean(axis=1)
    out["momentum"]=pd.concat(momentum,axis=1).mean(axis=1)

    v=load("^VIX")["close"].reindex(idx).ffill() if (DATA/"^vix_daily.csv").exists() else pd.read_csv(DATA/"vix_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["vix"].reindex(idx).ffill()
    pct=v.rolling(253,min_periods=60).apply(lambda x: float((x[:-1]<=x[-1]).mean()) if len(x)>30 else np.nan,raw=True)
    out["volatility"]=pd.concat([(pct>=.70).astype(float),(v.pct_change(5)>0).astype(float)],axis=1).mean(axis=1)

    below=(m<m.rolling(200,min_periods=200).mean()).mean(axis=1)
    weak=[]
    for _,c in m.items():
        line=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
        sig=line.ewm(span=9,adjust=False).mean()
        weak.append((line<sig).astype(float))
    out["breadth"]=pd.concat([below,pd.concat(weak,axis=1).mean(axis=1)],axis=1).mean(axis=1)
    return out,m


def main():
    f,m=features()
    bench=m.pct_change().mean(axis=1)
    rows=[]
    for family,s in f.items():
        for threshold in (.4,.5,.6,.7):
            raw=(s>=threshold).fillna(False)
            event=raw & ~raw.shift(1).fillna(False)
            for horizon in (5,10,20,40):
                forward=bench.shift(-horizon)/bench-1
                sample=forward[event].dropna()
                if len(sample)==0: continue
                rows.append({
                    "family":family,"threshold":threshold,"horizon":horizon,
                    "events":len(sample),
                    "mean_forward_return":sample.mean(),
                    "median_forward_return":sample.median(),
                    "pct_negative":(sample<0).mean(),
                    "p10":sample.quantile(.10),
                    "p90":sample.quantile(.90),
                })
    out=pd.DataFrame(rows)
    out.to_csv(DATA/"etf019_signal_lead_diagnostics.csv",index=False)
    print("=== ETF-019 SIGNAL LEAD DIAGNOSTICS ===")
    print(out.to_string(index=False))


if __name__=="__main__":
    main()
