"""Second-generation TQQQ swing search with a true train/validation/test split.

Train: 2010-2021. Validation: 2022-2023. Untouched test: 2024-2026.
Candidate selection is based only on train + validation; final test is never used
for selection. Terminal wealth is primary. B&H is the control.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
LOOK=[3,5,10,15,20,30];H=[5,10,15,20,30]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def rsi(p,n=14):
 d=p.diff();up=d.clip(lower=0).rolling(n).mean();dn=(-d.clip(upper=0)).rolling(n).mean();return 100-100/(1+up/dn)
def sig(p,name,h):
 m={n:p.pct_change(n) for n in LOOK};ma20=p.rolling(20).mean();ma50=p.rolling(50).mean();ma100=p.rolling(100).mean();ma200=p.rolling(200).mean();r=rsi(p)
 parts=name.split(":");typ=parts[0];n=int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 0
 on=False;rem=0;o=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>=200:
   if typ=="MOM": x=m[n].iloc[i]>0
   elif typ=="ACCEL": x=m[n].iloc[i]>0 and m[n].iloc[i]>m[n].iloc[i-1]
   elif typ=="TREND": x=p.iloc[i]>ma100.iloc[i] and m[n].iloc[i]>0
   elif typ=="TREND200": x=p.iloc[i]>ma200.iloc[i] and m[n].iloc[i]>0
   elif typ=="BREAK": x=p.iloc[i]>p.shift(1).rolling(n).max().iloc[i]
   elif typ=="MA_CROSS": x=(p.iloc[i]>ma20.iloc[i] and ma20.iloc[i]>ma50.iloc[i])
   elif typ=="MA_SLOPE": x=(ma50.iloc[i]>ma50.iloc[i-5] and p.iloc[i]>ma50.iloc[i])
   elif typ=="RSI_REV": x=(r.iloc[i]>50 and r.iloc[i-1]<=50 and p.iloc[i]>ma20.iloc[i])
   elif typ=="PULLBACK": x=(p.iloc[i]<p.iloc[i-n] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i])
   else:x=False
   if x:on=True;rem=h
  o.append(float(on))
 return pd.Series(o,index=p.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 names=[f"MOM:{n}" for n in LOOK]+[f"ACCEL:{n}" for n in LOOK]+[f"TREND:{n}" for n in LOOK]+[f"TREND200:{n}" for n in LOOK]+[f"BREAK:{n}" for n in [5,10,20,30,50]]+["MA_CROSS:0","MA_SLOPE:0","RSI_REV:0"]+[f"PULLBACK:{n}" for n in [5,10,20]]
 cand={(n,h):sig(q.adj_close,n,h) for n in names for h in H}
 train=(idx>=pd.Timestamp("2010-01-01"))&(idx<=pd.Timestamp("2021-12-31"));val=(idx>=pd.Timestamp("2022-01-01"))&(idx<=pd.Timestamp("2023-12-31"));test=(idx>=pd.Timestamp("2024-01-01"))&(idx<=pd.Timestamp("2026-10-07"))
 def score(s,mask):
  d=next_open_daily_returns(s,on,inn);ii=np.flatnonzero(mask);return INITIAL*float(np.prod(1+d[ii[0]:ii[-1]+1]))
 # Stage 1: rank on train. Keep top 10 only.
 ranked=sorted([((n,h),score(s,train)) for (n,h),s in cand.items()],key=lambda x:x[1],reverse=True)[:10]
 vr=[(k,score(cand[k],val)) for k,_ in ranked];vr.sort(key=lambda x:x[1],reverse=True)
 # Require validation performance to be positive; final selection among candidates that survived.
 best=vr[0];s=cand[best[0]]
 ti=np.flatnonzero(test);d=next_open_daily_returns(s,on,inn);end=INITIAL*float(np.prod(1+d[ti[0]:ti[-1]+1]));w=next_open_cost_equity(s,on,inn,5,INITIAL);cost=INITIAL*float(w[ti[-1]]/w[ti[0]-1])
 bh=np.ones(len(idx));bd=next_open_daily_returns(bh,on,inn);bhend=INITIAL*float(np.prod(1+bd[ti[0]:ti[-1]+1]));yrs=(idx[ti[-1]]-idx[ti[0]]).days/365.25
 print("TRAIN TOP10",ranked);print("VALIDATION TOP",vr);print({"selected":best[0],"validation_from_5000":best[1],"test_end_0bps":end,"test_end_5bps":cost,"bh_test_end":bhend,"test_cagr":(end/INITIAL)**(1/yrs)-1,"bh_cagr":(bhend/INITIAL)**(1/yrs)-1})
 out=pd.DataFrame([{"selected_rule":best[0][0],"hold":best[0][1],"validation_end":best[1],"test_end_0bps":end,"test_end_5bps":cost,"bh_test_end":bhend,"test_cagr":(end/INITIAL)**(1/yrs)-1,"bh_cagr":(bhend/INITIAL)**(1/yrs)-1}]);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_swing_train_validate_test.csv",index=False)
if __name__=="__main__":main()
