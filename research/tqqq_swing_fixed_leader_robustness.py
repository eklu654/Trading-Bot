"""Fixed-leader OOS attribution and parameter plateau test for TQQQ swing research."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
FOLDS=[("2010-2013","2010-01-01","2013-12-31","2014-01-01","2015-12-31"),
("2012-2015","2012-01-01","2015-12-31","2016-01-01","2017-12-31"),
("2014-2017","2014-01-01","2017-12-31","2018-01-01","2019-12-31"),
("2016-2019","2016-01-01","2019-12-31","2020-01-01","2021-12-31"),
("2018-2021","2018-01-01","2021-12-31","2022-01-01","2023-12-31"),
("2020-2023","2020-01-01","2023-12-31","2024-01-01","2026-10-07")]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,hold,threshold=0):
 m=p.pct_change(10); on=False; rem=0; out=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>=100 and m.iloc[i]>0 and (m.iloc[i]-m.iloc[i-1])>threshold:
   on=True; rem=hold
  out.append(float(on))
 return pd.Series(out,index=p.index)
def calc(s,d,idx,mask,capital):
 ii=np.flatnonzero(mask); 
 if len(ii)<2:return capital,0
 g=float(np.prod(1+d[ii[0]:ii[-1]+1])); return capital*g,g-1
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx)
 ao=t.open*t.adj_close/t.close; on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 rows=[]
 for hold in [10,15,20,25,30]:
  s=sig(q.adj_close,hold);d=next_open_daily_returns(s,on,inn);cap=INITIAL
  for fold,ta,tb,va,vb in FOLDS:
   mask=(idx>=pd.Timestamp(va))&(idx<=pd.Timestamp(vb));cap,g=calc(s,d,idx,mask,cap)
   rows.append({"type":"fixed_leader_hold","param":hold,"fold":fold,"end":cap,"return":g})
 # threshold sensitivity over full history
 for th in [0,.001,.0025,.005,.01]:
  s=sig(q.adj_close,20,th);d=next_open_daily_returns(s,on,inn);w=INITIAL*np.cumprod(1+d);yrs=(idx[-1]-idx[0]).days/365.25
  wc=next_open_cost_equity(s,on,inn,5,INITIAL)
  rows.append({"type":"threshold_full","param":th,"fold":"FULL","end":float(w[-1]),"return":float(w[-1]/INITIAL-1),"cost5_end":float(wc[-1]),"cagr":float((w[-1]/INITIAL)**(1/yrs)-1)})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_swing_fixed_leader_robustness.csv",index=False)
 print(out.to_string(index=False))
if __name__=="__main__":main()
