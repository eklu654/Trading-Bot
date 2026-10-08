"""Causal cost stress for the simple SQQQ crash overlay."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def ret(t):
 ao=t.open*t.adj_close/t.close;return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx);p=q.adj_close;r=p.pct_change();to,ti=ret(t);bo,bi=ret(b);rows=[]
 for shock,n,iv in [(-.05,10,1),(-.05,10,10),(-.045,10,1),(-.05,15,1)]:
  state=np.ones(len(idx));armed=False;until=-1
  for i in range(1,len(idx)):
   if r.iloc[i]<=shock:armed=True;until=i+iv
   if armed:
    if i>=n and p.iloc[i]/p.iloc[i-n]-1>0:armed=False
    elif i<=until:state[i]=-1
    else:state[i]=0
  ex=np.roll(state,1);ex[0]=1
  base=np.where(ex==1,(1+to)*(1+ti),np.where(ex==-1,(1+bo)*(1+bi),1))
  changes=np.r_[True,ex[1:]!=ex[:-1]]
  for bps in [0,5,10,25,50]:
   d=base.copy();d[changes]*=1-bps/10000;e=INITIAL*np.cumprod(d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
   rows.append({"rule":f"S{shock}_M{n}_I{iv}","bps":bps,"final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"switches":int(changes.sum()),"sqqq":float((ex==-1).mean()),"cash":float((ex==0).mean())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_crash_inverse_cost_stress.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
