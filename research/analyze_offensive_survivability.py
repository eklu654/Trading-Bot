"""Common rolling survivability audit for frozen Tier-A offensive controls."""
from pathlib import Path
import pandas as pd
import numpy as np
from research.backtest_dynamic_leverage import load
from research.test_dma_family_rotation import backtest as family_rotation_backtest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
START=pd.Timestamp("2010-03-11"); END=pd.Timestamp("2026-10-02")
WINDOWS={"1y":252,"3y":756,"5y":1260,"10y":2520}
THRESHOLDS=(-.50,-.60,-.70,-.80)

def buy_hold_returns(price,cost_bps=0):
    ret=price.pct_change().fillna(0.0)
    if len(ret): ret.iloc[0]-=cost_bps/10000.0
    return ret

def dma_next_open_returns(frame,cost_bps=0):
    adj_open=frame["open"].astype(float)*(frame["adj_close"].astype(float)/frame["close"].astype(float))
    adj_close=frame["adj_close"].astype(float)
    ma=adj_close.rolling(200).mean()
    held=(adj_close.shift(1)>=ma.shift(1)).fillna(False)
    prev=held.shift(1).fillna(False)
    entry=held & ~prev; holding=held & prev; exit_=~held & prev
    out=pd.Series(0.0,index=frame.index)
    out.loc[entry]=adj_close.loc[entry]/adj_open.loc[entry]-1
    out.loc[holding]=adj_close.loc[holding]/adj_close.shift(1).loc[holding]-1
    out.loc[exit_]=adj_open.loc[exit_]/adj_close.shift(1).loc[exit_]-1
    turnover=held.astype(float).diff().abs().fillna(held.astype(float))
    return out-turnover*(cost_bps/10000.0)


def cagr(eq):
    years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    return float(eq.iloc[-1]**(1/years)-1)

def max_dd(eq):
    return float((eq/eq.cummax()-1).min())

def rolling(ret,label):
    ret=ret.fillna(0).astype(float); details=[]; summaries=[]
    for name,w in WINDOWS.items():
        if len(ret)<w: continue
        for i in range(w-1,len(ret)):
            seg=ret.iloc[i-w+1:i+1]; eq=(1+seg).cumprod()
            details.append({"strategy":label,"window":name,"start":seg.index[0],"end":seg.index[-1],"cagr":cagr(eq),"max_drawdown":max_dd(eq)})
        d=pd.DataFrame([x for x in details if x["window"]==name])
        row={"strategy":label,"window":name,"observed_windows":len(d),
             "worst_rolling_cagr":d.cagr.min(),"best_rolling_cagr":d.cagr.max(),
             "worst_rolling_drawdown":d.max_drawdown.min(),"best_rolling_drawdown":d.max_drawdown.max(),
             "negative_cagr_rate":(d.cagr<0).mean(),"cagr_below_10pct_rate":(d.cagr<.10).mean()}
        for t in THRESHOLDS: row[f"dd_breach_{abs(int(t*100))}pct"]=(d.max_drawdown<=t).mean()
        summaries.append(row)
    return pd.DataFrame(details),pd.DataFrame(summaries)

def main():
    prices={s:load(s) for s in ("TQQQ","SOXL","SPXL")}
    idx=prices["TQQQ"].index
    for p in prices.values(): idx=idx.intersection(p.index)
    idx=idx[(idx>=START)&(idx<=END)]
    frame=pd.read_csv(DATA/"tqqq_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index().loc[START:END]
    controls={
      "TQQQ_buy_and_hold":buy_hold_returns(prices["TQQQ"]["adj_close"].loc[idx],0),
      "SOXL_buy_and_hold":buy_hold_returns(prices["SOXL"]["adj_close"].loc[idx],0),
      "SPXL_buy_and_hold":buy_hold_returns(prices["SPXL"]["adj_close"].loc[idx],0),
      "TQQQ_200DMA_next_open":dma_next_open_returns(frame,0),
      "BASE_ROTATE_DMA250_TOP2_C5":family_rotation_backtest(250,2,5)["portfolio_return"].loc[START:END],
    }
    ds=[]; ss=[]
    for label,ret in controls.items():
        d,s=rolling(ret,label)
        ds.append(d); ss.append(s)
    summary=pd.concat(ss,ignore_index=True); detail=pd.concat(ds,ignore_index=True)
    summary["common_period_start"]=START; summary["common_period_end"]=END
    summary.to_csv(DATA/"offensive_tier_a_rolling_summary.csv",index=False)
    detail.to_csv(DATA/"offensive_tier_a_rolling_detail.csv",index=False)
    print(summary.to_string(index=False))

if __name__=="__main__": main()
