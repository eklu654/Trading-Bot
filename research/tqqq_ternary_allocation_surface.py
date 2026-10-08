"""Causal ternary allocation: QQQ signal chooses TQQQ, QQQ, or cash.
No inverse ETF. This asks whether the missing edge is selecting the *degree* of leverage,
rather than simply entering/exiting TQQQ.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
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
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx)
 qo,qi=ret(q);to,ti=ret(t);p=q.adj_close;r=p.pct_change()
 rows=[]
 for look in [5,10,20,50]:
  mom=p.pct_change(look); ma=p.rolling(look).mean()
  for strong in [.01,.02,.05,.10]:
   for weak in [-.05,-.02,0,.01]:
    if weak>=strong: continue
    s=[]
    for i in range(len(idx)):
     m=mom.iloc[i]
     # strong bullish = TQQQ; middle = QQQ; weak = cash
     s.append(3.0 if m>=strong else (1.0 if m>weak and p.iloc[i]>ma.iloc[i] else 0.0))
    s=np.array(s)
    # build direct asset-return path with next-open execution
    ex=np.roll(s,1);ex[0]=0
    prev=np.roll(ex,1);prev[0]=0
    daily=(1+prev*to)*(1+ex*ti)
    # QQQ middle exposure: use asset-specific weights
    mid=(ex==1)
    daily=np.where(mid,(1+prev[mid]*qo[mid])*(1+ex[mid]*qi[mid]),daily)
    # cash otherwise, TQQQ weight 3 means 3x not valid for a 100% TQQQ allocation; fix encoding below
    # Recompute correctly with states 0=cash, 1=QQQ, 2=TQQQ.
    state=np.where(s>=2,2,np.where(s>=1,1,0)); exs=np.roll(state,1);exs[0]=0;prevs=np.roll(exs,1);prevs[0]=0
    daily=np.ones(len(idx))
    for i in range(len(idx)):
      if prevs[i]==1: daily[i]*=1+qo.iloc[i]
      elif prevs[i]==2: daily[i]*=1+to.iloc[i]
      if exs[i]==1: daily[i]*=1+qi.iloc[i]
      elif exs[i]==2: daily[i]*=1+ti.iloc[i]
    e=INITIAL*np.cumprod(daily);yrs=(idx[-1]-idx[0]).days/365.25;w=pd.Series(e,index=idx)
    rows.append({"strategy":f"L{look}_S{strong}_W{weak}","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":(w/w.cummax()-1).min(),"tqqq_pct":(state==2).mean(),"qqq_pct":(state==1).mean()})
 bh=np.ones(len(idx));e=INITIAL*np.cumprod(1+to);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
 rows.append({"strategy":"TQQQ_BH","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":(w/w.cummax()-1).min(),"tqqq_pct":1,"qqq_pct":0})
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False);OUT.mkdir(parents=True,exist_ok=True);r.to_csv(OUT/"tqqq_ternary_allocation_surface.csv",index=False);print(r.head(40).to_string(index=False))
if __name__=="__main__":main()
