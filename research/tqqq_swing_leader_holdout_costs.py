"""Validation of the leading swing hypotheses without re-optimization.

Leaders from the frozen first matrix:
- QQQ MOM10_ACCEL, 20d hold
- QQQ MOM10, 20d hold
- QQQ MOM3, 20d hold
- QQQ BREAK5, 20d hold
Control: TQQQ buy-and-hold

Reports continuous equity by fixed eras and transaction-cost sensitivity.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
PER=[("2010-2013","2010-01-01","2013-12-31"),("2014-2017","2014-01-01","2017-12-31"),("2018-2021","2018-01-01","2021-12-31"),("2022-2026","2022-01-01","2026-10-07")]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,rule):
 m=p.pct_change(10); on=False; rem=0; out=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>=100:
   x={"MOM10_ACCEL":m.iloc[i]>0 and m.iloc[i]>m.iloc[i-1],"MOM10":m.iloc[i]>0,
      "MOM3":p.pct_change(3).iloc[i]>0,"BREAK5":p.iloc[i]>p.shift(1).rolling(5).max().iloc[i]}[rule]
   if x:on=True;rem=20
  out.append(float(on))
 return pd.Series(out,index=p.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx)
 ao=t.open*t.adj_close/t.close; on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 rows=[]
 for rule in ["MOM10_ACCEL","MOM10","MOM3","BREAK5"]:
  s=sig(q.adj_close,rule);d=next_open_daily_returns(s,on,inn);e=INITIAL*np.cumprod(1+d)
  for n,a,b in PER:
   mask=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(b));ii=np.flatnonzero(mask);st,en=ii[0],ii[-1];base=e[st-1] if st else INITIAL
   yrs=(idx[en]-idx[st]).days/365.25;rows.append({"rule":rule,"period":n,"start":base,"end":e[en],"cagr":(e[en]/base)**(1/max(yrs,1e-9))-1})
  for bps in [0,5,10,25]:
   wealth=next_open_cost_equity(s,on,inn,bps,INITIAL)
   rows.append({"rule":rule,"period":f"cost_{bps}bps","start":INITIAL,"end":wealth[-1],"cagr":(wealth[-1]/INITIAL)**(1/((idx[-1]-idx[0]).days/365.25))-1})
 bh=np.ones(len(idx));d=next_open_daily_returns(bh,on,inn);e=INITIAL*np.cumprod(1+d)
 rows.append({"rule":"BUY&HOLD","period":"FULL","start":INITIAL,"end":e[-1],"cagr":(e[-1]/INITIAL)**(1/((idx[-1]-idx[0]).days/365.25))-1})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_swing_leader_holdout_costs.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
