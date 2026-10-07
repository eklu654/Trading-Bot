"""100-DMA fixed exit with non-DMA re-entry signals.

All signals are causal: today's close/data determine tomorrow's execution.
The 100-DMA exit is identical across every strategy. Only re-entry differs.

Predeclared re-entry families:
- 20/50 trend reclaim
- 5-day momentum reversal
- 10-day momentum reversal
- RSI(14) recovery above 50
- MACD(12,26,9) bullish crossover
- 20-day high breakout
- positive 20-day slope + positive 5-day momentum
- VIX falling below 30 (QQQ/TQQQ trigger plus market volatility confirmation)
- combined momentum/trend confirmation

This is intentionally a small hypothesis matrix, not parameter optimization.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-07"


def download(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,
                  progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[
        ["open","close","adj_close"]].sort_index().dropna()


def features(p):
    ma20=p.rolling(20).mean()
    ma50=p.rolling(50).mean()
    ma100=p.rolling(100).mean()
    ema12=p.ewm(span=12,adjust=False).mean()
    ema26=p.ewm(span=26,adjust=False).mean()
    macd=ema12-ema26
    signal=macd.ewm(span=9,adjust=False).mean()
    delta=p.diff()
    gain=delta.clip(lower=0).rolling(14).mean()
    loss=(-delta.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0,np.nan)
    rsi=100-(100/(1+rs))
    return {
        "ma20":ma20,"ma50":ma50,"ma100":ma100,
        "macd":macd,"macd_signal":signal,"rsi":rsi,
        "mom5":p.pct_change(5),"mom10":p.pct_change(10),
        "high20":p.rolling(20).max().shift(1),
        "slope20":ma20.pct_change(5),
    }


def make_signal(p, vix, rule):
    f=features(p)
    ma20,ma50,ma100=f["ma20"],f["ma50"],f["ma100"]
    invested=False
    out=[]
    for i in range(len(p)):
        # Fixed defensive exit: identical 100-DMA exit for every candidate.
        if invested and i>=99 and p.iloc[i] < ma100.iloc[i]:
            invested=False
        elif not invested and i>=99:
            x=False
            if rule=="20DMA":
                x=p.iloc[i]>=ma20.iloc[i]
            elif rule=="20_50":
                x=(p.iloc[i]>=ma20.iloc[i]) and (ma20.iloc[i]>=ma50.iloc[i])
            elif rule=="MOM5":
                x=f["mom5"].iloc[i]>0
            elif rule=="MOM10":
                x=f["mom10"].iloc[i]>0
            elif rule=="RSI50":
                x=f["rsi"].iloc[i]>=50
            elif rule=="MACD_CROSS":
                x=(f["macd"].iloc[i]>f["macd_signal"].iloc[i] and
                   f["macd"].iloc[i-1]<=f["macd_signal"].iloc[i-1])
            elif rule=="HIGH20":
                x=p.iloc[i]>=f["high20"].iloc[i]
            elif rule=="SLOPE_MOM":
                x=(f["slope20"].iloc[i]>0 and f["mom5"].iloc[i]>0)
            elif rule=="VIX30":
                x=(vix.iloc[i]<30 and vix.iloc[i-1]>=30)
            elif rule=="MOM_TREND":
                x=(f["mom5"].iloc[i]>0 and f["mom10"].iloc[i]>0 and
                   p.iloc[i]>ma20.iloc[i] and ma20.iloc[i]>ma50.iloc[i])
            elif rule=="MOM_RSI":
                x=(f["mom5"].iloc[i]>0 and f["rsi"].iloc[i]>50)
            if x:
                invested=True
        out.append(float(invested))
    return pd.Series(out,index=p.index)


def tqqq_returns(t):
    adj_open=t["open"]*t["adj_close"]/t["close"]
    overnight=(adj_open/t["adj_close"].shift(1)-1).fillna(0)
    intraday=(t["adj_close"]/adj_open-1).fillna(0)
    return overnight,intraday


def stats(name,sig,daily,idx):
    eq=INITIAL*np.cumprod(1+daily)
    w=pd.Series(eq,index=idx)
    years=(idx[-1]-idx[0]).days/365.25
    dd=w/w.cummax()-1
    return {
        "strategy":name,"final_balance":float(w.iloc[-1]),
        "cagr":float((w.iloc[-1]/INITIAL)**(1/years)-1),
        "max_drawdown":float(dd.min()),
        "average_exposure":float(sig.shift(1).fillna(0).mean()),
        "switches":int(sig.diff().abs().fillna(0).sum()),
    }


def main():
    q=download("QQQ"); t=download("TQQQ"); v=download("^VIX")
    idx=q.index.intersection(t.index).intersection(v.index)
    q,t,v=q.reindex(idx),t.reindex(idx),v.reindex(idx)
    overnight,intraday=tqqq_returns(t)
    rules=["20DMA","20_50","MOM5","MOM10","RSI50","MACD_CROSS",
           "HIGH20","SLOPE_MOM","VIX30","MOM_TREND","MOM_RSI"]
    rows=[]
    for trigger_name,trigger in [("QQQ",q.adj_close),("TQQQ",t.adj_close)]:
        for rule in rules:
            sig=make_signal(trigger,v.adj_close,rule)
            daily=next_open_daily_returns(sig,overnight,intraday)
            rows.append(stats(f"TQQQ | {trigger_name} 100DMA exit + {rule}",
                              sig,daily,idx))
    bh=pd.Series(1.0,index=idx)
    rows.append(stats("TQQQ buy_and_hold",bh,
                      next_open_daily_returns(bh,overnight,intraday),idx))
    res=pd.DataFrame(rows).sort_values("final_balance",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True)
    res.to_csv(OUT/"tqqq_100dma_non_dma_reentry_matrix.csv",index=False)
    print(res.to_string(index=False))
    print("\nRules are fixed in source; no threshold search is performed.")


if __name__=="__main__":
    main()
