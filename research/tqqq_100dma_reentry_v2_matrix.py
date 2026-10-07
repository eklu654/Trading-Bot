"""Focused second-generation 100-DMA exit / predictive re-entry matrix.

The exit remains fixed: trigger close < trigger 100-DMA => next-open exit.
Only re-entry logic changes. All rules are predeclared; no threshold optimization.

Families:
1) momentum positive
2) momentum crossover
3) momentum persistence
4) momentum acceleration
5) recovery from post-exit trough
6) recovery + momentum
7) short-term trend reversal
8) RSI recovery
9) MACD crossover
10) 20-day breakout
11) combinations deliberately kept simple.

Also records re-entry latency and post-trough rebound missed, so performance can
be explained rather than treated as a black-box ranking.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_daily_returns

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0; START="2010-01-01"; END="2026-10-07"

def dl(s):
    x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[
        ["open","close","adj_close"]].sort_index().dropna()

def indicators(p):
    ma20=p.rolling(20).mean(); ma50=p.rolling(50).mean(); ma100=p.rolling(100).mean()
    m5=p.pct_change(5); m10=p.pct_change(10); m20=p.pct_change(20)
    e12=p.ewm(span=12,adjust=False).mean(); e26=p.ewm(span=26,adjust=False).mean()
    macd=e12-e26; ms=macd.ewm(span=9,adjust=False).mean()
    d=p.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean()
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    return locals()

def make_signal(p,rule):
    f=indicators(p); ma20=f["ma20"]; ma50=f["ma50"]; ma100=f["ma100"]
    m5=f["m5"]; m10=f["m10"]; m20=f["m20"]; rsi=f["rsi"]
    on=False; out=[]; trough=np.nan; days=0
    for i in range(len(p)):
        if on and i>=99 and p.iloc[i] < ma100.iloc[i]:
            on=False; trough=np.nan; days=0
        elif not on and i>=99:
            days += 1
            if np.isnan(trough): trough=p.iloc[i]
            trough=min(trough,p.iloc[i])
            recovery=p.iloc[i]/trough-1 if trough>0 else 0
            x=False
            if rule=="MOM5": x=m5.iloc[i]>0
            elif rule=="MOM10": x=m10.iloc[i]>0
            elif rule=="MOM20": x=m20.iloc[i]>0
            elif rule=="MOM10_CROSS": x=m10.iloc[i]>0 and m10.iloc[i-1]<=0
            elif rule=="MOM10_2D": x=m10.iloc[i]>0 and m10.iloc[i-1]>0
            elif rule=="MOM10_3D": x=m10.iloc[i]>0 and m10.iloc[i-1]>0 and m10.iloc[i-2]>0
            elif rule=="MOM_ACCEL": x=m10.iloc[i]>0 and m10.iloc[i]>m10.iloc[i-1]
            elif rule=="MOM5_ACCEL": x=m5.iloc[i]>0 and m5.iloc[i]>m5.iloc[i-1]
            elif rule=="RECOVERY5": x=recovery>=0.05
            elif rule=="RECOVERY10": x=recovery>=0.10
            elif rule=="RECOVERY5_MOM10": x=recovery>=0.05 and m10.iloc[i]>0
            elif rule=="RECOVERY10_MOM10": x=recovery>=0.10 and m10.iloc[i]>0
            elif rule=="MOM10_20DMA": x=m10.iloc[i]>0 and p.iloc[i]>=ma20.iloc[i]
            elif rule=="MOM10_50TREND": x=m10.iloc[i]>0 and p.iloc[i]>=ma20.iloc[i] and ma20.iloc[i]>=ma50.iloc[i]
            elif rule=="RSI50": x=rsi.iloc[i]>=50
            elif rule=="RSI50_MOM10": x=rsi.iloc[i]>=50 and m10.iloc[i]>0
            elif rule=="MACD_CROSS":
                x=f["macd"].iloc[i]>f["ms"].iloc[i] and f["macd"].iloc[i-1]<=f["ms"].iloc[i-1]
            elif rule=="HIGH20": x=p.iloc[i]>=f["ma20"].iloc[i] and p.iloc[i]>=p.iloc[max(0,i-20):i].max()
            elif rule=="MOM5_10": x=m5.iloc[i]>0 and m10.iloc[i]>0
            if x: on=True
        out.append(float(on))
    return pd.Series(out,index=p.index)

def treturns(t):
    ao=t.open*t.adj_close/t.close
    return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)

def stat(name,sig,daily,idx):
    eq=INITIAL*np.cumprod(1+daily); w=pd.Series(eq,index=idx); yrs=(idx[-1]-idx[0]).days/365.25
    dd=w/w.cummax()-1
    return {"strategy":name,"final_balance":float(w.iloc[-1]),
            "cagr":float((w.iloc[-1]/INITIAL)**(1/yrs)-1),
            "max_drawdown":float(dd.min()),
            "avg_exposure":float(sig.shift(1).fillna(0).mean()),
            "switches":int(sig.diff().abs().fillna(0).sum())}

def main():
    q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx)
    o,inn=treturns(t)
    rules=["MOM5","MOM10","MOM20","MOM10_CROSS","MOM10_2D","MOM10_3D",
           "MOM_ACCEL","MOM5_ACCEL","RECOVERY5","RECOVERY10","RECOVERY5_MOM10",
           "RECOVERY10_MOM10","MOM10_20DMA","MOM10_50TREND","RSI50","RSI50_MOM10",
           "MACD_CROSS","HIGH20","MOM5_10"]
    rows=[]
    for tn,p in [("QQQ",q.adj_close),("TQQQ",t.adj_close)]:
        for rule in rules:
            s=make_signal(p,rule); d=next_open_daily_returns(s,o,inn)
            rows.append(stat(f"TQQQ | {tn} 100DMA exit + {rule}",s,d,idx))
    bh=pd.Series(1.,index=idx); rows.append(stat("TQQQ buy_and_hold",bh,next_open_daily_returns(bh,o,inn),idx))
    r=pd.DataFrame(rows).sort_values("final_balance",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_100dma_reentry_v2_matrix.csv",index=False)
    print(r.to_string(index=False))

if __name__=="__main__": main()
