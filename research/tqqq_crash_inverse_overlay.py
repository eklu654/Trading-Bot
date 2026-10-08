"""Inverse-ETF overlay test: after QQQ crash trigger, compare cash vs SQQQ.
No simultaneous TQQQ/SQQQ: state is TQQQ or cash or SQQQ only.
Signal is QQQ close; execution next open.
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
def ret(t):
 ao=t.open*t.adj_close/t.close
 return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx)
 p=q.adj_close;r=p.pct_change();to,ti=ret(t);bo,bi=ret(b);rows=[]
 for shock in [-.04,-.045,-.05,-.055,-.06]:
  for n in [5,10,15,20]:
   for invdays in [1,2,3,5,10]:
    state=np.ones(len(idx));armed=False;until=-1
    for i in range(1,len(idx)):
     if r.iloc[i]<=shock: armed=True;until=i+invdays
     if armed:
      if i>=n and p.iloc[i]/p.iloc[i-n]-1>0: armed=False
      elif i<=until: state[i]=-1
      else: state[i]=0
    # -1 SQQQ, 0 cash, 1 TQQQ
    d=np.ones(len(idx))
    for i in range(len(idx)):
     if state[i]==1:d[i]=(1+to.iloc[i])*(1+ti.iloc[i])
     elif state[i]==-1:d[i]=(1+bo.iloc[i])*(1+bi.iloc[i])
    e=INITIAL*np.cumprod(d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"rule":f"S{shock}_M{n}_I{invdays}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"sqqq":float((state==-1).mean()),"cash":float((state==0).mean())})
 out=pd.DataFrame(rows).sort_values("final",ascending=False);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_crash_inverse_overlay.csv",index=False);print(out.head(50).to_string(index=False))
if __name__=="__main__":main()
