"""Causal 1-5 day TQQQ swing matrix."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,kind,l,h):
 r=p.pct_change(l);hi=p.shift(1).rolling(l).max();on=False;rem=0;o=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>l:
   x=(r.iloc[i]>0) if kind=="MOM" else (r.iloc[i]<0 and p.iloc[i]>p.iloc[i-1]) if kind=="REV" else (p.iloc[i]>hi.iloc[i])
   if x:on=True;rem=h
  o.append(float(on))
 return pd.Series(o,index=p.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx)
 ao=t.open*t.adj_close/t.close;o=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0);rows=[]
 for k in ["MOM","REV","BREAK"]:
  for l in [1,2,3,5,7,10]:
   for h in [1,2,3,4,5]:
    s=sig(q.adj_close,k,l,h);d=next_open_daily_returns(s,o,inn);e=INITIAL*np.cumprod(1+d);yrs=(idx[-1]-idx[0]).days/365.25
    dd=(pd.Series(e,index=idx)/pd.Series(e,index=idx).cummax()-1).min()
    rows.append({"strategy":f"{k}_L{l}_H{h}","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":dd,"exposure":s.shift(1).fillna(0).mean(),"entries":(s.diff().fillna(0)==1).sum()})
 bh=np.ones(len(idx));d=next_open_daily_returns(bh,o,inn);e=INITIAL*np.cumprod(1+d);rows.append({"strategy":"BUY&HOLD","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":(pd.Series(e)/pd.Series(e).cummax()-1).min(),"exposure":1,"entries":0})
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False);OUT.mkdir(parents=True,exist_ok=True);r.to_csv(OUT/"tqqq_1to5day_surface.csv",index=False);print(r.head(30).to_string(index=False))
if __name__=="__main__":main()
