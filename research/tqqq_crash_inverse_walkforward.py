"""Walk-forward selection for crash-triggered SQQQ overlay."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
CANDS=[(s,n,i) for s in [-.03,-.035,-.04,-.045,-.05,-.055,-.06,-.07] for n in [5,10,15,20] for i in [1,2,3,5]]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def ret(t):
 ao=t.open*t.adj_close/t.close;return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx);p=q.adj_close;r=p.pct_change();to,ti=ret(t);bo,bi=ret(b);rows=[]
 for shock,n,iv in CANDS:
  state=np.ones(len(idx));armed=False;until=-1
  for i in range(1,len(idx)):
   if r.iloc[i]<=shock:armed=True;until=i+iv
   if armed:
    if i>=n and p.iloc[i]/p.iloc[i-n]-1>0:armed=False
    elif i<=until:state[i]=-1
    else:state[i]=0
  d=np.where(state==1,(1+to)*(1+ti),np.where(state==-1,(1+bo)*(1+bi),1))-1
  for era,a,z in [("TRAIN1","2010-01-01","2017-12-31"),("TEST1","2018-01-01","2021-12-31"),("TRAIN2","2010-01-01","2021-12-31"),("TEST2","2022-01-01","2026-10-07")]:
   m=(idx>=a)&(idx<=z);ii=np.where(m)[0];st,en=ii[0],ii[-1];v=np.prod(1+d[st:en+1]);rows.append({"rule":f"S{shock}_M{n}_I{iv}","era":era,"growth":v,"cagr":v**(365.25/max((idx[en]-idx[st]).days,1))-1})
 df=pd.DataFrame(rows);picks=[]
 for tr,te in [("TRAIN1","TEST1"),("TRAIN2","TEST2")]:
  best=df[df.era==tr].sort_values("growth",ascending=False).iloc[0].rule;picks.extend([df[(df.era==tr)&(df.rule==best)],df[(df.era==te)&(df.rule==best)]])
 print("\nTOP TRAIN/TEST PICKS\n",pd.concat(picks).to_string(index=False))
 print("\nTEST TOP 15\n",df[df.era.isin(["TEST1","TEST2"])].sort_values(["era","growth"],ascending=[True,False]).groupby("era").head(15).to_string(index=False))
 OUT.mkdir(parents=True,exist_ok=True);df.to_csv(OUT/"tqqq_crash_inverse_walkforward.csv",index=False)
if __name__=="__main__":main()
