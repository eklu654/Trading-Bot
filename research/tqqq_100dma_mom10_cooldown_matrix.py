"""Cooldown tests for the strongest observed re-entry signal.

Fixed exit: 100-DMA.
Re-entry: 10-day momentum > 0.
Additional condition: remain defensive for a fixed minimum number of calendar
sessions after each exit (5, 10, 20 trading sessions).

Purpose: determine whether some of the 435 QQQ-trigger switches are costly
whipsaws that can be removed without returning to slow 50/100-DMA re-entry.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def make(p,cool):
 ma=p.rolling(100).mean(); mom=p.pct_change(10); on=False; since_exit=999; out=[]
 for i in range(len(p)):
  if on and i>=99 and p.iloc[i]<ma.iloc[i]: on=False; since_exit=0
  elif not on:
   since_exit+=1
   if i>=99 and since_exit>=cool and mom.iloc[i]>0:on=True
  out.append(float(on))
 return pd.Series(out,index=p.index)
def tr(t):
 ao=t.open*t.adj_close/t.close; return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def stat(name,s,d,idx):
 e=INITIAL*np.cumprod(1+d); w=pd.Series(e,index=idx); dd=w/w.cummax()-1; yrs=(idx[-1]-idx[0]).days/365.25
 return {"strategy":name,"final_balance":w.iloc[-1],"cagr":(w.iloc[-1]/INITIAL)**(1/yrs)-1,"max_drawdown":dd.min(),"avg_exposure":s.shift(1).fillna(0).mean(),"switches":s.diff().abs().fillna(0).sum()}
def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx); o,ii=tr(t); rows=[]
 for tn,p in [("QQQ",q.adj_close),("TQQQ",t.adj_close)]:
  for c in [0,2,5,10,20,30]:
   s=make(p,c); rows.append(stat(f"TQQQ | {tn} 100DMA exit + MOM10 + {c}d cooldown",s,next_open_daily_returns(s,o,ii),idx))
 bh=pd.Series(1.,index=idx); rows.append(stat("TQQQ buy_and_hold",bh,next_open_daily_returns(bh,o,ii),idx))
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False); OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_100dma_mom10_cooldown_matrix.csv",index=False); print(r.to_string(index=False))
if __name__=="__main__":main()
