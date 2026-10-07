"""Focused validation of the best simple re-entry hypotheses.

Candidates:
- QQQ 100DMA exit + 50DMA reentry
- TQQQ 100DMA exit + 50DMA reentry
- QQQ 100DMA exit + 10-day momentum reentry
- TQQQ 100DMA exit + 10-day momentum reentry
- QQQ 100DMA exit + 5-day momentum reentry
- TQQQ 100DMA exit + 5-day momentum reentry
- buy and hold

Continuous signals are evaluated from 2010 onward. Window statistics are calculated
from the same continuous equity curves, avoiding lookahead from restarting each window.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
WINDOWS=[("2010_2013","2010-01-01","2013-12-31"),("2014_2017","2014-01-01","2017-12-31"),("2018_2021","2018-01-01","2021-12-31"),("2022_2026","2022-01-01","2026-10-07")]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,reentry):
 ma100=p.rolling(100).mean(); ma50=p.rolling(50).mean(); m10=p.pct_change(10); m5=p.pct_change(5); on=False; out=[]
 for i in range(len(p)):
  if on and i>=99 and p.iloc[i]<ma100.iloc[i]: on=False
  elif not on and i>=99:
   x={"50DMA":p.iloc[i]>=ma50.iloc[i],"MOM10":m10.iloc[i]>0,"MOM5":m5.iloc[i]>0}[reentry]
   if x:on=True
  out.append(float(on))
 return pd.Series(out,index=p.index)
def tr(t):
 ao=t.open*t.adj_close/t.close
 return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def metrics(eq,idx):
 w=pd.Series(eq,index=idx); dd=w/w.cummax()-1
 return float(w.iloc[-1]),float(dd.min())
def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx); o,ii=tr(t)
 candidates={}
 for tn,p in [("QQQ",q.adj_close),("TQQQ",t.adj_close)]:
  for r in ["50DMA","MOM10","MOM5"]:
   s=sig(p,r); candidates[f"{tn}+{r}"]=next_open_daily_returns(s,o,ii)
 bh=pd.Series(1.,index=idx); candidates["BUY_HOLD"]=next_open_daily_returns(bh,o,ii)
 rows=[]
 for name,d in candidates.items():
  eq=INITIAL*np.cumprod(1+d); final,dd=metrics(eq,idx)
  rows.append({"strategy":name,"full_final":final,"full_max_dd":dd})
  for wn,a,b in WINDOWS:
   mask=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(b)); ids=np.flatnonzero(mask)
   if len(ids)<2: continue
   start=ids[0]; end=ids[-1]
   base=eq[start-1] if start>0 else INITIAL
   endv=eq[end]
   yrs=(idx[end]-idx[start]).days/365.25
   rows.append({"strategy":name,"window":wn,"window_start_balance":base,"window_end_balance":endv,
                "window_return":endv/base-1,"window_cagr":(endv/base)**(1/max(yrs,1e-9))-1})
 out=pd.DataFrame(rows); OUT.mkdir(parents=True,exist_ok=True); out.to_csv(OUT/"tqqq_100dma_reentry_regime_validation.csv",index=False)
 print(out.to_string(index=False))
if __name__=="__main__":main()
