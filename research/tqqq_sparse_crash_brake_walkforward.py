"""Walk-forward selection for sparse crash brakes.
Select threshold/cooldown only on prior history; test the next era untouched.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
CANDS=[(1,x,c) for x in [-.04,-.045,-.05,-.055,-.06,-.07,-.08,-.10] for c in [1,3,5,7,10,15,20]]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(r,shock,c):
 s=np.ones(len(r));until=-1
 for i in range(len(r)):
  if i<=until:s[i]=0
  if i>=1 and r.iloc[i]<=shock:
   until=i+c;s[i]=0
 return pd.Series(s,index=r.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);r=q.adj_close.pct_change()
 ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 eras=[("TRAIN10_17","2010-01-01","2017-12-31"),("TEST18_21","2018-01-01","2021-12-31"),("TRAIN10_21","2010-01-01","2021-12-31"),("TEST22_26","2022-01-01","2026-10-07")]
 rows=[]
 for shock in sorted(set(x[1] for x in CANDS)):
  for c in sorted(set(x[2] for x in CANDS)):
   s=sig(r,shock,c);d=next_open_daily_returns(s,on,inn)
   for name,a,b in eras:
    m=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(b));ii=np.where(m)[0];st,en=ii[0],ii[-1];v=np.prod(1+d[st:en+1]);rows.append({"rule":f"S{shock}_C{c}","era":name,"growth":v,"cagr":v**(365.25/max((idx[en]-idx[st]).days,1))-1})
 df=pd.DataFrame(rows); picks=[]
 for train,test in [("TRAIN10_17","TEST18_21"),("TRAIN10_21","TEST22_26")]:
  z=df[df.era==train].sort_values("growth",ascending=False);best=z.iloc[0].rule; picks.append(df[(df.era==train)&(df.rule==best)]); picks.append(df[(df.era==test)&(df.rule==best)])
 print(df.sort_values(["era","growth"],ascending=[True,False]).groupby("era").head(10).to_string(index=False))
 print("\nWALK_FORWARD PICKS\n",pd.concat(picks).to_string(index=False))
 OUT.mkdir(parents=True,exist_ok=True);df.to_csv(OUT/"tqqq_sparse_crash_brake_walkforward.csv",index=False)
if __name__=="__main__":main()
