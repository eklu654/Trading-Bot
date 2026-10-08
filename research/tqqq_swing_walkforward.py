"""Walk-forward validation and local robustness for the frozen TQQQ swing family.

Selection is performed only inside each training window. The selected rule/hold is
then frozen for the following test window. No test-window optimization is used.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
RULES=["MOM3","MOM5","MOM10","BREAK5","BREAK10","BREAK20","PULLBACK5","PULLBACK10","TREND_MOM5","TREND_MOM10","TREND_BREAK10","MOM10_ACCEL","MOM5_ACCEL"]
HORIZONS=[2,3,5,10,15,20,25,30]
# Rolling 4-year train -> 2-year test, with a final partial test through 2026.
FOLDS=[("2010-2013","2010-01-01","2013-12-31","2014-01-01","2015-12-31"),
       ("2012-2015","2012-01-01","2015-12-31","2016-01-01","2017-12-31"),
       ("2014-2017","2014-01-01","2017-12-31","2018-01-01","2019-12-31"),
       ("2016-2019","2016-01-01","2019-12-31","2020-01-01","2021-12-31"),
       ("2018-2021","2018-01-01","2021-12-31","2022-01-01","2023-12-31"),
       ("2020-2023","2020-01-01","2023-12-31","2024-01-01","2026-10-07")]

def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()

def signal(q,rule,h):
 p=q; ma20=p.rolling(20).mean(); ma100=p.rolling(100).mean(); m3=p.pct_change(3); m5=p.pct_change(5); m10=p.pct_change(10)
 hi5=p.shift(1).rolling(5).max(); hi10=p.shift(1).rolling(10).max(); hi20=p.shift(1).rolling(20).max()
 on=False; remain=0; out=[]
 for i in range(len(p)):
  if on:
   remain-=1
   if remain<=0:on=False
  if not on and i>=100:
   x={"MOM3":m3.iloc[i]>0,"MOM5":m5.iloc[i]>0,"MOM10":m10.iloc[i]>0,
      "BREAK5":p.iloc[i]>hi5.iloc[i],"BREAK10":p.iloc[i]>hi10.iloc[i],"BREAK20":p.iloc[i]>hi20.iloc[i],
      "PULLBACK5":p.iloc[i]<p.iloc[i-5] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i],
      "PULLBACK10":p.iloc[i]<p.iloc[i-10] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i],
      "TREND_MOM5":p.iloc[i]>ma100.iloc[i] and m5.iloc[i]>0,"TREND_MOM10":p.iloc[i]>ma100.iloc[i] and m10.iloc[i]>0,
      "TREND_BREAK10":p.iloc[i]>ma100.iloc[i] and p.iloc[i]>hi10.iloc[i],
      "MOM10_ACCEL":m10.iloc[i]>0 and m10.iloc[i]>m10.iloc[i-1],
      "MOM5_ACCEL":m5.iloc[i]>0 and m5.iloc[i]>m5.iloc[i-1]}[rule]
   if x:on=True; remain=h
  out.append(float(on))
 return pd.Series(out,index=p.index)

def wealth_for(s,overnight,intraday,mask,initial):
 idx=np.flatnonzero(mask)
 if len(idx)<2:return initial
 # Return only returns earned inside the requested window, while preserving the
 # actual signal history and causal one-day execution relationship.
 d=next_open_daily_returns(s,overnight,intraday)
 return initial*float(np.prod(1+d[idx[0]:idx[-1]+1]))

def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx)
 ao=t.open*t.adj_close/t.close; overnight=(ao/t.adj_close.shift(1)-1).fillna(0); intraday=(t.adj_close/ao-1).fillna(0)
 candidates={(r,h):signal(q.adj_close,r,h) for r in RULES for h in HORIZONS}
 bh=np.ones(len(idx)); bhd=next_open_daily_returns(bh,overnight,intraday)
 rows=[]; selected=[]; capital=INITIAL
 for fold,ta,tb,va,vb in FOLDS:
  train=(idx>=pd.Timestamp(ta))&(idx<=pd.Timestamp(tb)); test=(idx>=pd.Timestamp(va))&(idx<=pd.Timestamp(vb))
  scores=[]
  for (r,h),s in candidates.items():
   scores.append(((r,h),wealth_for(s,overnight,intraday,train,INITIAL)))
  best=max(scores,key=lambda z:z[1]); selected.append({"fold":fold,"selected_rule":best[0][0],"selected_hold":best[0][1],"train_final_from_5000":best[1]})
  s=candidates[best[0]]
  test_idx=np.flatnonzero(test)
  if len(test_idx):
   d=next_open_daily_returns(s,overnight,intraday)
   capital*=float(np.prod(1+d[test_idx[0]:test_idx[-1]+1]))
   bh_cap=INITIAL*float(np.prod(1+bhd[test_idx[0]:test_idx[-1]+1]))
   rows.append({"fold":fold,"train_start":ta,"train_end":tb,"test_start":va,"test_end":vb,
                "rule":best[0][0],"hold":best[0][1],"oos_start_capital":capital/(np.prod(1+d[test_idx[0]:test_idx[-1]+1])),
                "oos_end_capital":capital,"oos_return":float(np.prod(1+d[test_idx[0]:test_idx[-1]+1])-1),
                "bh_return_same_test":float(np.prod(1+bhd[test_idx[0]:test_idx[-1]+1])-1)})
 # Full chronological OOS chain, plus fixed-leader controls and cost sensitivity.
 oos=pd.DataFrame(rows); sel=pd.DataFrame(selected)
 OUT.mkdir(parents=True,exist_ok=True); oos.to_csv(OUT/"tqqq_swing_walkforward_oos.csv",index=False); sel.to_csv(OUT/"tqqq_swing_walkforward_selections.csv",index=False)
 fixed=candidates[("MOM10_ACCEL",20)]
 for bps in [0,2.5,5,10]:
  w=next_open_cost_equity(fixed,overnight,intraday,bps,INITIAL)
  yrs=(idx[-1]-idx[0]).days/365.25
  print({"fixed_leader_cost_bps":bps,"final":float(w[-1]),"cagr":float((w[-1]/INITIAL)**(1/yrs)-1)})
 print("\nWALK-FORWARD OOS FOLDS"); print(oos.to_string(index=False))
 print("\nSELECTIONS"); print(sel.to_string(index=False))
 print("\nOOS FINAL CAPITAL",capital)
if __name__=="__main__":main()
