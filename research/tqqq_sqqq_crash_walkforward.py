"""Causal walk-forward selection of QQQ shock -> SQQQ -> momentum reentry.
Signals use QQQ close; state changes execute next session. No future data in selection.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
CANDS=[(s,m,iv) for s in [-.035,-.04,-.045,-.05,-.055,-.06,-.07] for m in [5,10,15,20] for iv in [1,3,5,10,20]]
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def main():
 q=dl("QQQ");t=dl("TQQQ");b=dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx)
 p=q["Close"].squeeze().astype(float);tc=t["Close"].squeeze().astype(float);bc=b["Close"].squeeze().astype(float);qr=p.pct_change().fillna(0).to_numpy();tr=tc.pct_change().fillna(0).to_numpy();br=bc.pct_change().fillna(0).to_numpy();rows=[]
 for shock,mom,hold in CANDS:
  state=np.ones(len(idx));armed=False;until=-1
  for i in range(1,len(idx)):
   if qr[i]<=shock:armed=True;until=i+hold
   if armed:
    if i>=mom and p.iloc[i]/p.iloc[i-mom]-1>0:armed=False
    elif i<=until:state[i]=-1
    else:state[i]=0
  ex=np.roll(state,1);ex[0]=1
  d=np.where(ex==1,1+tr,np.where(ex==-1,1+br,1))
  for era,a,z in [("TRAIN1","2010-01-01","2017-12-31"),("TEST1","2018-01-01","2021-12-31"),("TRAIN2","2010-01-01","2021-12-31"),("TEST2","2022-01-01","2026-10-07")]:
   ii=np.where((idx>=a)&(idx<=z))[0];v=np.prod(d[ii]);rows.append({"rule":f"S{shock}_M{mom}_I{hold}","era":era,"growth":v,"cagr":v**(365.25/max((idx[ii[-1]]-idx[ii[0]]).days,1))-1})
 df=pd.DataFrame(rows);picks=[]
 for trn,tes in [("TRAIN1","TEST1"),("TRAIN2","TEST2")]:
  best=df[df.era==trn].sort_values("growth",ascending=False).iloc[0].rule;picks.append(df[(df.era.isin([trn,tes]))&(df.rule==best)])
 print(pd.concat(picks).to_string(index=False));print("\nTEST top");print(df[df.era.isin(["TEST1","TEST2"])].sort_values(["era","growth"],ascending=[True,False]).groupby("era").head(10).to_string(index=False))
 OUT.mkdir(parents=True,exist_ok=True);df.to_csv(OUT/"tqqq_sqqq_crash_walkforward.csv",index=False)
if __name__=="__main__":main()

# trigger
