"""Causal short-horizon TQQQ swing surface.
QQQ is the signal; TQQQ enters next open. Tests reversal and momentum entries
over short holding periods, with optional 100/200-day trend filters.
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
def ret(t):
 ao=t.open*t.adj_close/t.close
 return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def signal(p,kind,look,hold,trend):
 r=p.pct_change(look); ma=p.rolling(trend).mean() if trend else None
 on=False; rem=0; out=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>=max(look,trend or 0)+1:
   if kind=="REV":
    x=r.iloc[i] < -0.01*look and p.iloc[i]>ma.iloc[i] if trend else r.iloc[i] < -0.01*look
   elif kind=="MOM":
    x=r.iloc[i] > 0.005*look and p.iloc[i]>ma.iloc[i] if trend else r.iloc[i] > 0.005*look
   elif kind=="BREAK":
    hi=p.shift(1).rolling(look).max().iloc[i]
    x=p.iloc[i]>hi and p.iloc[i]>ma.iloc[i] if trend else p.iloc[i]>hi
   else: raise ValueError(kind)
   if x:on=True; rem=hold
  out.append(float(on))
 return pd.Series(out,index=p.index)
def stat(name,s,d,idx):
 e=INITIAL*np.cumprod(1+d); w=pd.Series(e,index=idx); dd=w/w.cummax()-1; yrs=(idx[-1]-idx[0]).days/365.25
 return {"strategy":name,"final_balance":float(w.iloc[-1]),"cagr":float((w.iloc[-1]/INITIAL)**(1/yrs)-1),"max_drawdown":float(dd.min()),"avg_exposure":float(s.shift(1).fillna(0).mean()),"entries":int((s.diff().fillna(0)==1).sum())}
def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx); o,inn=ret(t); rows=[]
 for kind in ["REV","MOM","BREAK"]:
  for look in [1,2,3,5,7,10,15,20]:
   for hold in [2,3,5,7,10,15,20]:
    for trend in [None,100,200]:
     s=signal(q.adj_close,kind,look,hold,trend); d=next_open_daily_returns(s,o,inn)
     rows.append(stat(f"{kind}_L{look}_H{hold}_T{trend or 0}",s,d,idx))
 bh=pd.Series(1.,index=idx); rows.append(stat("BUY&HOLD",bh,next_open_daily_returns(bh,o,inn),idx))
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False)
 OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_short_horizon_surface.csv",index=False); print(r.head(40).to_string(index=False))
if __name__=="__main__": main()
