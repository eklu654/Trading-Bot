"""Strict early-training freeze for TQQQ swing family.

Select exactly one rule/hold using only 2010-2013, then freeze it and evaluate
the contiguous 2014-2026 period. Also report buy-and-hold and cost sensitivity.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
RULES=["MOM3","MOM5","MOM10","BREAK5","BREAK10","BREAK20","PULLBACK5","PULLBACK10","TREND_MOM5","TREND_MOM10","TREND_BREAK10","MOM10_ACCEL","MOM5_ACCEL"]; H=[2,3,5,10,15,20,25,30]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,r,h):
 ma20=p.rolling(20).mean();ma100=p.rolling(100).mean();m3=p.pct_change(3);m5=p.pct_change(5);m10=p.pct_change(10);hi5=p.shift(1).rolling(5).max();hi10=p.shift(1).rolling(10).max();hi20=p.shift(1).rolling(20).max()
 on=False;rem=0;o=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>=100:
   x={"MOM3":m3.iloc[i]>0,"MOM5":m5.iloc[i]>0,"MOM10":m10.iloc[i]>0,"BREAK5":p.iloc[i]>hi5.iloc[i],"BREAK10":p.iloc[i]>hi10.iloc[i],"BREAK20":p.iloc[i]>hi20.iloc[i],"PULLBACK5":p.iloc[i]<p.iloc[i-5] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i],"PULLBACK10":p.iloc[i]<p.iloc[i-10] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i],"TREND_MOM5":p.iloc[i]>ma100.iloc[i] and m5.iloc[i]>0,"TREND_MOM10":p.iloc[i]>ma100.iloc[i] and m10.iloc[i]>0,"TREND_BREAK10":p.iloc[i]>ma100.iloc[i] and p.iloc[i]>hi10.iloc[i],"MOM10_ACCEL":m10.iloc[i]>0 and m10.iloc[i]>m10.iloc[i-1],"MOM5_ACCEL":m5.iloc[i]>0 and m5.iloc[i]>m5.iloc[i-1]}[r]
   if x:on=True;rem=h
  o.append(float(on))
 return pd.Series(o,index=p.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 cand={(r,h):sig(q.adj_close,r,h) for r in RULES for h in H}
 train=(idx>=pd.Timestamp("2010-01-01"))&(idx<=pd.Timestamp("2013-12-31"));test=(idx>=pd.Timestamp("2014-01-01"))&(idx<=pd.Timestamp("2026-10-07"))
 scores=[]
 for k,s in cand.items():
  d=next_open_daily_returns(s,on,inn);ii=np.flatnonzero(train);scores.append((k,INITIAL*float(np.prod(1+d[ii[0]:ii[-1]+1]))))
 best=max(scores,key=lambda z:z[1]); s=cand[best[0]];d=next_open_daily_returns(s,on,inn);ii=np.flatnonzero(test);oos=INITIAL*float(np.prod(1+d[ii[0]:ii[-1]+1]))
 bh=np.ones(len(idx));bd=next_open_daily_returns(bh,on,inn);bhoos=INITIAL*float(np.prod(1+bd[ii[0]:ii[-1]+1]))
 rows=[{"rule":best[0][0],"hold":best[0][1],"train_end":best[1],"test_end_0bps":oos,"bh_test_end":bhoos}]
 for bps in [2.5,5,10,25]:
  w=next_open_cost_equity(s,on,inn,bps,INITIAL); rows[0][f"test_end_{bps:g}bps"]=float(w[ii[-1]])/float(w[ii[0]-1] if ii[0]>0 else INITIAL)*INITIAL
 yrs=(idx[ii[-1]]-idx[ii[0]]).days/365.25
 rows[0]["test_cagr_0bps"]=(oos/INITIAL)**(1/yrs)-1;rows[0]["bh_test_cagr"]=(bhoos/INITIAL)**(1/yrs)-1
 print("SELECTED_FROM_2010_2013",best);print(pd.DataFrame(rows).to_string(index=False))
 OUT.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(OUT/"tqqq_swing_strict_2013_freeze.csv",index=False)
if __name__=="__main__":main()
