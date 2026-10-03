"""ETF-002 directional leveraged-ETF rotation research.

Tests a fixed, transparent rule using only underlying-index proxies for signals:
- QQQ -> TQQQ/SQQQ
- SPY -> SPXL/SPXS
- SOXX -> SOXL/SOXS
- DIA -> UDOW/SDOW
- IWM -> TNA/TZA

At each close, an underlying above its 200-DMA makes its bull ETF eligible;
below its 200-DMA makes its inverse ETF eligible. Eligible pairs are ranked
by the absolute 60-session underlying return in the active direction. The top
N pairs receive equal portions of a 75% invested budget; the remainder stays
cash. A pair can never contribute both its bull and bear ETF.

Signals at t are applied to returns beginning at t+1. Adjusted ETF closes are
used for return accounting; unadjusted underlying closes are used for signals.
Train/validation/holdout are descriptive chronological splits.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"

PAIRS={
    "QQQ":("TQQQ","SQQQ"),
    "SPY":("SPXL","SPXS"),
    "SOXX":("SOXL","SOXS"),
    "DIA":("UDOW","SDOW"),
    "IWM":("TNA","TZA"),
}
CASH=0.25
TOP_N=(1,2,3,5)
LOOKBACK=60
SPLITS={
    "train":("2010-03-01","2019-12-31"),
    "validation":("2020-01-01","2022-12-31"),
    "holdout":("2023-01-01","2099-12-31"),
}

def load(symbol):
    return pd.read_csv(DATA/f"{symbol.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()

def metrics(frame):
    if frame.empty: return {"observations":0}
    r=frame["return"]
    eq=(1+r).cumprod()
    years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1
    ann=(1+total)**(1/years)-1
    vol=r.std(ddof=1)*np.sqrt(252)
    dd=(eq/eq.cummax()-1).min()
    neg=r[r<0].std(ddof=1)
    sharpe=r.mean()/r.std(ddof=1)*np.sqrt(252) if r.std(ddof=1)>0 else np.nan
    sortino=r.mean()/neg*np.sqrt(252) if pd.notna(neg) and neg>0 else np.nan
    return {"observations":len(frame),"total_return":total,"annualized_return":ann,
            "max_drawdown":dd,"annualized_volatility":vol,"sharpe":sharpe,
            "sortino":sortino,"ending_value_5000":5000*eq.iloc[-1]}

def build():
    underlying={s:load(s)["close"] for s in PAIRS}
    etf={}
    for u,(bull,bear) in PAIRS.items():
        etf[bull]=load(bull)
        etf[bear]=load(bear)
    common=pd.concat(underlying,axis=1).dropna()
    # Use a common calendar so ranking never implicitly favors one pair.
    signals={}
    for u in PAIRS:
        c=common[u]
        ma=c.rolling(200,min_periods=200).mean()
        mom=c.pct_change(LOOKBACK)
        direction=np.where(c>=ma,1,-1)
        score=mom.abs()
        signals[u]=pd.DataFrame({"direction":direction,"score":score},index=common.index)

    rows=[]
    for top_n in TOP_N:
        daily=[]
        selections=[]
        for i,date in enumerate(common.index):
            if i==0:
                daily.append(0.0); selections.append([])
                continue
            prev=common.index[i-1]
            candidates=[]
            for u,(bull,bear) in PAIRS.items():
                sig=signals[u].loc[prev]
                if pd.isna(sig["score"]) or pd.isna(sig["direction"]):
                    continue
                ticker=bull if sig["direction"]>0 else bear
                if ticker not in etf or date not in etf[ticker].index or prev not in etf[ticker].index:
                    continue
                candidates.append((float(sig["score"]),u,ticker))
            candidates.sort(reverse=True)
            chosen=candidates[:top_n]
            weight=(1-CASH)/top_n
            ret=0.0
            names=[]
            for _,u,ticker in chosen:
                p=etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
                if prev in p.index and date in p.index:
                    ret += weight*float(p.loc[date]/p.loc[prev]-1)
                    names.append(ticker)
            daily.append(ret); selections.append(names)
        frame=pd.DataFrame({"return":daily},index=common.index)
        frame["equity"]=(1+frame["return"]).cumprod()
        frame["drawdown"]=frame["equity"]/frame["equity"].cummax()-1
        frame["top_n"]=top_n
        frame["selected"]=selections
        rows.append(frame)
    out=[]
    for frame in rows:
        for split,(start,end) in SPLITS.items():
            m=metrics(frame.loc[start:end])
            out.append({"top_n":frame["top_n"].iloc[0],"split":split,**m})
    result=pd.DataFrame(out)
    result.to_csv(DATA/"etf002_directional_rotation_summary.csv",index=False)

    # Also test the simpler fixed 25%-per-pair directional switch without ranking.
    daily=[]
    for i,date in enumerate(common.index):
        if i==0: daily.append(0.0); continue
        prev=common.index[i-1]; ret=0.0
        for u,(bull,bear) in PAIRS.items():
            sig=signals[u].loc[prev]
            ticker=bull if sig["direction"]>0 else bear
            p=etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
            if prev in p.index and date in p.index:
                ret += 0.15*float(p.loc[date]/p.loc[prev]-1)
        daily.append(ret)
    fixed=pd.DataFrame({"return":daily},index=common.index)
    fixed["equity"]=(1+fixed["return"]).cumprod()
    fixed["drawdown"]=fixed["equity"]/fixed["equity"].cummax()-1
    fixed_rows=[]
    for split,(start,end) in SPLITS.items():
        fixed_rows.append({"strategy":"fixed_directional_5x15pct","split":split,**metrics(fixed.loc[start:end])})
    pd.DataFrame(fixed_rows).to_csv(DATA/"etf002_fixed_directional_summary.csv",index=False)
    print("=== ETF-002 ROTATION ===")
    print(result.to_string(index=False))
    print("\n=== ETF-002 FIXED DIRECTIONAL ===")
    print(pd.DataFrame(fixed_rows).to_string(index=False))

if __name__=="__main__":
    build()
