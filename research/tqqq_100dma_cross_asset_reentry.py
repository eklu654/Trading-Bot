"""100-DMA exit with cross-asset recovery confirmation.

Re-entry uses information outside the trigger asset:
- QQQ 10d momentum
- SPY 10d momentum
- HYG 10d momentum
- HYG/LQD relative strength
- QQQ/SPY relative strength
- RSP/SPY breadth proxy
- VIX falling / below its short average

No parameter sweep; fixed hypotheses only. All signals use close data and next-open execution.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
INITIAL=5000.; START="2010-01-01"; END="2026-10-07"

def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def pct(s,n): return s.pct_change(n)
def stat(name,s,d,idx):
 e=INITIAL*np.cumprod(1+d); w=pd.Series(e,index=idx); dd=w/w.cummax()-1; yrs=(idx[-1]-idx[0]).days/365.25
 return {"strategy":name,"final_balance":float(w.iloc[-1]),"cagr":float((w.iloc[-1]/INITIAL)**(1/yrs)-1),"max_drawdown":float(dd.min()),"avg_exposure":float(s.shift(1).fillna(0).mean()),"switches":int(s.diff().abs().fillna(0).sum())}
def signal(q,spy,hyg,lqd,rsp,vix,rule):
 m100=q.rolling(100).mean(); m20=q.rolling(20).mean(); on=False; out=[]
 q5=pct(q,5); q10=pct(q,10); spy10=pct(spy,10); hyg10=pct(hyg,10); lqd10=pct(lqd,10)
 rs=q/spy; rs20=pct(rs,20); credit=hyg/lqd; credit10=pct(credit,10); breadth=rsp/spy; breadth20=pct(breadth,20)
 v10=vix.rolling(10).mean()
 for i in range(len(q)):
  if on and i>=99 and q.iloc[i]<m100.iloc[i]: on=False
  elif not on and i>=99:
   vfall=i>=2 and vix.iloc[i]<vix.iloc[i-1]<vix.iloc[i-2]
   x={
    "QQQ10_SPY10":q10.iloc[i]>0 and spy10.iloc[i]>0,
    "QQQ10_HYG10":q10.iloc[i]>0 and hyg10.iloc[i]>0,
    "QQQ10_CREDIT":q10.iloc[i]>0 and credit10.iloc[i]>0,
    "QQQ10_BREADTH":q10.iloc[i]>0 and breadth20.iloc[i]>0,
    "QQQ10_RELATIVE":q10.iloc[i]>0 and rs20.iloc[i]>0,
    "QQQ5_VIX":q5.iloc[i]>0 and vfall,
    "QQQ10_VIXAVG":q10.iloc[i]>0 and vix.iloc[i]<v10.iloc[i],
    "MULTI3":q10.iloc[i]>0 and spy10.iloc[i]>0 and hyg10.iloc[i]>0,
    "MULTI4":q10.iloc[i]>0 and spy10.iloc[i]>0 and hyg10.iloc[i]>0 and breadth20.iloc[i]>0,
    "RISKON":q10.iloc[i]>0 and credit10.iloc[i]>0 and breadth20.iloc[i]>0,
    "TREND_RISKON":q.iloc[i]>=m20.iloc[i] and q10.iloc[i]>0 and credit10.iloc[i]>0,
   }[rule]
   if bool(x): on=True
  out.append(float(on))
 return pd.Series(out,index=q.index)
def main():
 q,t,spy,hyg,lqd,rsp,v=[dl(x).adj_close for x in ["QQQ","TQQQ","SPY","HYG","LQD","RSP","^VIX"]]
 idx=q.index
 for x in [t,spy,hyg,lqd,rsp,v]: idx=idx.intersection(x.index)
 q,t,spy,hyg,lqd,rsp,v=[x.reindex(idx) for x in [q,t,spy,hyg,lqd,rsp,v]]
 ao=(dl("TQQQ").open.reindex(idx)*t/dl("TQQQ").close.reindex(idx))
 on=(ao/t.shift(1)-1).fillna(0); intr=(t/ao-1).fillna(0)
 rules=["QQQ10_SPY10","QQQ10_HYG10","QQQ10_CREDIT","QQQ10_BREADTH","QQQ10_RELATIVE","QQQ5_VIX","QQQ10_VIXAVG","MULTI3","MULTI4","RISKON","TREND_RISKON"]
 rows=[]
 for tn,tr in [("QQQ",q),("TQQQ",t)]:
  for rule in rules:
   s=signal(tr,spy,hyg,lqd,rsp,v,rule); rows.append(stat(f"TQQQ | {tn} 100DMA exit + {rule}",s,next_open_daily_returns(s,on,intr),idx))
 bh=pd.Series(1.,index=idx); rows.append(stat("TQQQ buy_and_hold",bh,next_open_daily_returns(bh,on,intr),idx))
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False); OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_100dma_cross_asset_reentry.csv",index=False); print(r.to_string(index=False))
if __name__=="__main__": main()
