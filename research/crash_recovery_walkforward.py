"""Walk-forward validation of QQQ crash recovery-distance reentry.
Selection is made only on the preceding training window; test window is untouched.
No same-day execution: signal at close, position changes next session.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
CANDS=[(s,r) for s in [-.035,-.04,-.045,-.05,-.055] for r in [.10,.15,.20,.25,.30,.40]]
def dl(s,a,b):
 x=yf.download(s,start=a,end=b,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def make(p,tr,shock,rec):
 r=p.pct_change().fillna(0);s=np.ones(len(p));armed=False;low=0.
 for i in range(1,len(p)):
  if r.iloc[i]<=shock:armed=True;low=p.iloc[i]
  if armed:
   low=min(low,p.iloc[i])
   if p.iloc[i]/low-1>=rec:armed=False
   else:s[i]=0
 return s
def eval_asset(p,ret,windows,label):
 rows=[]
 for shock,rec in CANDS:
  s=make(p,None,shock,rec);ex=np.roll(s,1);ex[0]=1
  e=INITIAL*np.cumprod(1+ret*ex)
  for name,a,b in windows:
   m=(p.index>=a)&(p.index<=b);ii=np.where(m)[0]
   if not len(ii):continue
   st,en=ii[0],ii[-1];v=np.prod(1+ret[st:en+1]*ex[st:en+1]);rows.append({"asset":label,"rule":f"S{shock}_R{rec}","window":name,"growth":v,"cagr":v**(365.25/max((p.index[en]-p.index[st]).days,1))-1,"maxdd":float((pd.Series(e[st:en+1],index=p.index[st:en+1])/pd.Series(e[st:en+1],index=p.index[st:en+1]).cummax()-1).min())})
 return pd.DataFrame(rows)
def main():
 q=dl("QQQ","1999-03-11","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07")
 p=q["Close"].squeeze().astype(float);tr=t["Close"].squeeze().astype(float);idx=p.index.intersection(tr.index);pa,ta=p.reindex(idx),tr.reindex(idx)
 actual=eval_asset(pa,ta.pct_change().fillna(0).to_numpy(),[("TRAIN1","2010-01-01","2017-12-31"),("TEST1","2018-01-01","2021-12-31"),("TRAIN2","2010-01-01","2021-12-31"),("TEST2","2022-01-01","2026-10-07")],"actual")
 synp=p[(p.index>="1999-03-11")&(p.index<="2010-03-11")];synret=(1+3*synp.pct_change().fillna(0)).clip(lower=0).to_numpy()-1
 syn=eval_asset(synp,synret,[("TRAIN","1999-03-11","2004-12-31"),("TEST","2005-01-01","2010-03-11")],"synthetic")
 # add untouched buy-and-hold benchmarks for every test/training window\n bench=[]\n for asset,p0,ret0,windows in [("actual",pa,ta.pct_change().fillna(0).to_numpy(),[("TRAIN1","2010-01-01","2017-12-31"),("TEST1","2018-01-01","2021-12-31"),("TRAIN2","2010-01-01","2021-12-31"),("TEST2","2022-01-01","2026-10-07")]),("synthetic",synp,synret,[("TRAIN","1999-03-11","2004-12-31"),("TEST","2005-01-01","2010-03-11")])]:\n  for name,a,b in windows:\n   m=(p0.index>=a)&(p0.index<=b);ii=np.where(m)[0];st,en=ii[0],ii[-1];v=np.prod(1+ret0[st:en+1]);bench.append({"asset":asset,"rule":"B&H","window":name,"growth":v,"cagr":v**(365.25/max((p0.index[en]-p0.index[st]).days,1))-1})\n out=pd.concat([actual,syn,pd.DataFrame(bench)],ignore_index=True);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_recovery_walkforward.csv",index=False)
 for trn,tes in [("TRAIN1","TEST1"),("TRAIN2","TEST2"),("TRAIN","TEST")]:
  d=out[out.window==trn]
  if not len(d):continue
  best=d.sort_values("growth",ascending=False).iloc[0].rule
  print("\n",trn,"=>",tes,"SELECTED",best)
  print(out[(out.window==tes)&(out.rule==best)].to_string(index=False))
  print("TEST TOP",out[out.window==tes].sort_values("growth",ascending=False).head(8).to_string(index=False))
if __name__=="__main__":main()

# trigger

# rerun benchmark
