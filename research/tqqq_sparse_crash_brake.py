"""Sparse crash-brake overlay on TQQQ.
Default = TQQQ continuously. Only after an unusually negative QQQ move,
switch to cash for a short fixed cooldown. Signal is known at close; execution next open.
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
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx)
 ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 p=q.adj_close;r=p.pct_change();rows=[]
 for look in [1,2,3,5,10]:
  for shock in [-.02,-.03,-.04,-.05,-.07,-.10]:
   for cooldown in [1,2,3,5,7,10,15,20]:
    s=np.ones(len(idx));until=-1
    for i in range(len(idx)):
      if i<=look: continue
      if i<=until:s[i]=0
      if r.iloc[i-look+1:i+1].sum()<=shock:
        until=i+cooldown; s[i]=0
    d=next_open_daily_returns(pd.Series(s,index=idx),on,inn);e=INITIAL*np.cumprod(1+d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"strategy":f"SHOCK_L{look}_{shock}_C{cooldown}","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash_pct":float((s==0).mean())})
 bh=np.ones(len(idx));d=next_open_daily_returns(pd.Series(bh,index=idx),on,inn);e=INITIAL*np.cumprod(1+d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
 rows.append({"strategy":"TQQQ_BH","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash_pct":0})
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False);OUT.mkdir(parents=True,exist_ok=True);r.to_csv(OUT/"tqqq_sparse_crash_brake.csv",index=False);print(r.head(50).to_string(index=False))
if __name__=="__main__":main()
