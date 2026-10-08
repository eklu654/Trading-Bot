"""Targeted validation of SQQQ crash overlay. Includes eras and transaction-cost stress."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
CANDS=[(-.04,5,1),(-.04,5,2),(-.04,10,1),(-.045,10,1),(-.05,10,1),(-.05,10,2),(-.05,15,1)]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def ret(t):
 ao=t.open*t.adj_close/t.close;return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx)
 p=q.adj_close;r=p.pct_change();to,ti=ret(t);bo,bi=ret(b);eras=[("2010-17","2010-01-01","2017-12-31"),("2018-21","2018-01-01","2021-12-31"),("2022-26","2022-01-01","2026-10-07")]
 rows=[]
 for shock,n,invdays in CANDS:
  state=np.ones(len(idx));armed=False;until=-1
  for i in range(1,len(idx)):
   if r.iloc[i]<=shock:armed=True;until=i+invdays
   if armed:
    if i>=n and p.iloc[i]/p.iloc[i-n]-1>0:armed=False
    elif i<=until:state[i]=-1
    else:state[i]=0
  d=np.where(state==1,(1+to)*(1+ti),np.where(state==-1,(1+bo)*(1+bi),1))-1
  for name,a,z in eras:
   m=(idx>=a)&(idx<=z);ii=np.where(m)[0];st,en=ii[0],ii[-1];v=np.prod(1+d[st:en+1]);rows.append({"rule":f"S{shock}_M{n}_I{invdays}","era":name,"growth":v,"cagr":v**(365.25/max((idx[en]-idx[st]).days,1))-1})
  e=INITIAL*np.cumprod(1+d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25;rows.append({"rule":f"S{shock}_M{n}_I{invdays}","era":"FULL","growth":e[-1]/INITIAL,"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"sqqq":float((state==-1).mean()),"cash":float((state==0).mean())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_crash_inverse_validation.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
