"""Focused re-entry test: immediate 100-DMA versus shock-only re-entry veto.

Mandatory 100-DMA exits are unchanged. On re-entry, compare:
1) immediate re-entry,
2) veto re-entry while either VIX 20-day change or QQQ 20-day realized-vol
   change is >=100%.

Synthetic daily-reset 3x QQQ, $5,000, next-open accounting, no costs.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
START="1999-03-10"; END="2026-10-05"; INITIAL=5000.0

def dl(t):
    x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def main():
    q=dl("QQQ"); v=dl("^VIX")[["close"]].rename(columns={"close":"vix"})
    x=q.join(v,how="left"); x.vix=x.vix.ffill()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
    x["dma"]=x.adj_close.rolling(100).mean()
    x["ret"]=x.adj_close.pct_change()
    x["rv20"]=x.ret.rolling(20).std()*np.sqrt(252)
    x["vix_chg20"]=x.vix/x.vix.shift(20)-1
    x["rv_chg20"]=x.rv20/x.rv20.shift(20)-1
    shock=(x.vix_chg20>=1.0)|(x.rv_chg20>=1.0)
    x["shock"]=shock.fillna(False)

    immediate=np.zeros(len(x)); shock_veto=np.zeros(len(x))
    in_pos=False; in_shock=False; vetoes=[]
    for i in range(100,len(x)):
        if in_pos and x.adj_close.iloc[i] < x.dma.iloc[i]:
            in_pos=False
        elif (not in_pos) and x.adj_close.iloc[i] >= x.dma.iloc[i]:
            in_pos=True
        immediate[i]=float(in_pos)

        if in_shock and x.adj_close.iloc[i] < x.dma.iloc[i]:
            in_shock=False
        elif (not in_shock) and x.adj_close.iloc[i] >= x.dma.iloc[i]:
            if not bool(shock.iloc[i]):
                in_shock=True
            else:
                vetoes.append((x.index[i],x.vix_chg20.iloc[i],x.rv_chg20.iloc[i]))
        shock_veto[i]=float(in_shock)

    def equity(sig):
        w=np.asarray(sig,float); prev=np.roll(w,1); prev[0]=0
        daily=(1+prev*x.on3.to_numpy())*(1+w*x.in3.to_numpy())-1
        eq=INITIAL*np.cumprod(1+daily); dd=eq/np.maximum.accumulate(eq)-1
        return eq,dd

    rows=[]
    for name,sig in [("baseline_100dma",immediate),("shock_reentry_veto",shock_veto)]:
        eq,dd=equity(sig)
        years=(x.index[-1]-x.index[0]).days/365.2425
        rows.append({"strategy":name,"start":x.index[0].date(),"end":x.index[-1].date(),
                     "starting_balance":INITIAL,"final_balance":float(eq[-1]),
                     "cagr":float((eq[-1]/INITIAL)**(1/years)-1),
                     "max_drawdown":float(dd.min()),"avg_exposure":float(np.mean(sig)),
                     "shock_reentry_vetoes":len(vetoes) if name=="shock_reentry_veto" else 0})
    pd.DataFrame(rows).to_csv(OUT/"tqqq_shock_reentry_comparison.csv",index=False)
    pd.DataFrame(vetoes,columns=["date","vix_chg20","rv_chg20"]).to_csv(OUT/"tqqq_shock_reentry_vetoes.csv",index=False)
    x["baseline_signal"]=immediate; x["shock_reentry_signal"]=shock_veto
    x[["adj_close","dma","vix","vix_chg20","rv20","rv_chg20","shock","baseline_signal","shock_reentry_signal"]].to_csv(OUT/"tqqq_shock_reentry_daily.csv")
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"reentry veto events: {len(vetoes)}")

if __name__=="__main__":
    main()
