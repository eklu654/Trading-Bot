"""Causal QQQ return-persistence matrix for TQQQ.
Entry requires a positive fraction of up days and positive cumulative momentum;
hold is fixed. Designed to test trend persistence rather than raw momentum alone.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);p=q.adj_close;r=p.pct_change()
 ao=t.open*t.adj_close/t.close;o=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0);rows=[]
 for look in [5,10,15,20,30]:
  for frac in [.55,.60,.65,.70,.75]:
   for hold in [5,10,15,20]:
    up=(r>0).rolling(look).mean();mom=p.pct_change(look);on=False;rem=0;vals=[]
    for i in range(len(p)):
     if on:
      rem-=1
      if rem<=0:on=False
     if not on and i>look and up.iloc[i]>=frac and mom.iloc[i]>0:
      on=True;rem=hold
     vals.append(float(on))
    s=pd.Series(vals,index=idx);d=next_open_daily_returns(s,o,inn);e=INITIAL*np.cumprod(1+d);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"strategy":f"PERSIST_L{look}_F{frac}_H{hold}","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":(pd.Series(e,index=idx)/pd.Series(e,index=idx).cummax()-1).min(),"exposure":s.shift(1).fillna(0).mean(),"entries":(s.diff().fillna(0)==1).sum()})
 bh=np.ones(len(idx));d=next_open_daily_returns(pd.Series(bh,index=idx),o,inn);e=INITIAL*np.cumprod(1+d);rows.append({"strategy":"BUY&HOLD","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":(pd.Series(e,index=idx)/pd.Series(e,index=idx).cummax()-1).min(),"exposure":1,"entries":0})
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False);OUT.mkdir(parents=True,exist_ok=True);r.to_csv(OUT/"tqqq_persistence_surface.csv",index=False);print(r.head(40).to_string(index=False))
if __name__=="__main__":main()
