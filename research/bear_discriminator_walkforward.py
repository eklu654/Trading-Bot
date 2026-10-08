"""Walk-forward comparison of compact bear discriminators.
Train 2010-2017 -> test 2018-2021; train 2010-2021 -> test 2022-2026.
No parameter chosen from test. All QQQ signal, TQQQ asset, next-session.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def equity(p,a,rule):
 r=p.pct_change().fillna(0).to_numpy();state=np.ones(len(p));armed=False;low=0.;peak=0.;days=0;shocks=0;target=.1
 for i in range(1,len(p)):
  if not armed and r[i]<=-.045: armed=True;low=p.iloc[i];peak=p.iloc[i];days=0;shocks=1
  if armed:
   days+=1;low=min(low,p.iloc[i]);peak=max(peak,p.iloc[i])
   if r[i]<=-.045: shocks+=1
   if rule=="10": target=.10
   elif rule=="30": target=.30
   elif rule=="40": target=.40
   elif rule=="low5": target=.30 if p.iloc[i]<peak*.95 else .10
   elif rule=="low10": target=.30 if p.iloc[i]<peak*.90 else .10
   elif rule=="time30": target=.30 if days>=30 else .10
   elif rule=="shock2": target=.30 if shocks>=2 else .10
   if p.iloc[i]/low-1>=target:armed=False
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;e=INITIAL*np.cumprod(1+a*ex);return pd.Series(e,index=p.index)
def main():
 q=dl("QQQ");t=dl("TQQQ");idx=q.index.intersection(t.index);p=q["Close"].squeeze().astype(float).reindex(idx);a=t["Close"].squeeze().astype(float).reindex(idx).pct_change().fillna(0).to_numpy();rules=["10","30","40","low5","low10","time30","shock2"];sets=[("T1","2010-01-01","2017-12-31","E1","2018-01-01","2021-12-31"),("T2","2010-01-01","2021-12-31","E2","2022-01-01","2026-10-07")];rows=[]
 for tr,ta,tb,te,ea,eb in sets:
  ii=np.where((idx>=ta)&(idx<=tb))[0]; jj=np.where((idx>=ea)&(idx<=eb))[0]
  for rule in rules:
   e=equity(p,a,rule);train_growth=e.iloc[ii[-1]]/(e.iloc[ii[0]-1] if ii[0]>0 else INITIAL);test_growth=e.iloc[jj[-1]]/(e.iloc[jj[0]-1] if jj[0]>0 else INITIAL)
   rows.append({"train":tr,"test":te,"rule":rule,"train_growth":train_growth,"test_growth":test_growth})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"bear_discriminator_walkforward.csv",index=False)
 for tr,te in [("T1","E1"),("T2","E2")]:
  print("\n",tr,"=>",te);print(out[(out.train==tr)&(out.test==te)].sort_values("train_growth",ascending=False).to_string(index=False));print("TEST RANK");print(out[(out.train==tr)&(out.test==te)].sort_values("test_growth",ascending=False).to_string(index=False))
if __name__=="__main__":main()
