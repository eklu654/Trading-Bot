"""Chronological freeze sensitivity: select the same candidate family on an early
training period, then freeze it for the later test period. No test optimization."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
RULES=["MOM3","MOM5","MOM10","BREAK5","BREAK10","BREAK20","PULLBACK5","PULLBACK10","TREND_MOM5","TREND_MOM10","TREND_BREAK10","MOM10_ACCEL","MOM5_ACCEL"];H=[2,3,5,10,15,20,25,30]
SPLITS=[("2010-2013","2010-01-01","2013-12-31","2014-01-01","2026-10-07"),("2010-2015","2010-01-01","2015-12-31","2016-01-01","2026-10-07"),("2010-2017","2010-01-01","2017-12-31","2018-01-01","2026-10-07")]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,r,h):
 ma20=p.rolling(20).mean();ma100=p.rolling(100).mean();m3=p.pct_change(3);m5=p.pct_change(5);m10=p.pct_change(10);hi5=p.shift(1).rolling(5).max();hi10=p.shift(1).rolling(10).max();hi20=p.shift(1).rolling(20).max();on=False;rem=0;o=[]
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
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0);cand={(r,h):sig(q.adj_close,r,h) for r in RULES for h in H};rows=[]
 for name,ta,tb,va,vb in SPLITS:
  tr=(idx>=pd.Timestamp(ta))&(idx<=pd.Timestamp(tb));te=(idx>=pd.Timestamp(va))&(idx<=pd.Timestamp(vb));tri=np.flatnonzero(tr);tei=np.flatnonzero(te);scores=[]
  for k,s in cand.items():
   d=next_open_daily_returns(s,on,inn);scores.append((k,INITIAL*float(np.prod(1+d[tri[0]:tri[-1]+1]))))
  best=max(scores,key=lambda z:z[1]);s=cand[best[0]];d=next_open_daily_returns(s,on,inn);end=INITIAL*float(np.prod(1+d[tei[0]:tei[-1]+1]));bh=np.ones(len(idx));bd=next_open_daily_returns(bh,on,inn);bhend=INITIAL*float(np.prod(1+bd[tei[0]:tei[-1]+1]));w=next_open_cost_equity(s,on,inn,5,INITIAL);cost=INITIAL*float(w[tei[-1]]/w[tei[0]-1]) if tei[0]>0 else float(w[tei[-1]])
  yrs=(idx[tei[-1]]-idx[tei[0]]).days/365.25
  rows.append({"split":name,"selected_rule":best[0][0],"hold":best[0][1],"train_end":best[1],"test_end_0bps":end,"test_end_5bps":cost,"bh_test_end":bhend,"test_cagr":(end/INITIAL)**(1/yrs)-1,"bh_cagr":(bhend/INITIAL)**(1/yrs)-1})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_swing_chronological_freeze_sensitivity.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()

# Workflow trigger validation: frozen methodology, no parameter changes.
