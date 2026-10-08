"""Persistent-bear inverse overlay: normal first shock goes to cash; only after repeated QQQ shocks does the sleeve switch to SQQQ for a short burst, then returns to cash until the recovery target is met.
No simultaneous TQQQ/SQQQ. Causal next-session execution.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def ret(t):
 c=t["Close"].squeeze().astype(float);return c.pct_change().fillna(0).to_numpy()
def run(p,tr,sr,shock,escalate_at,target,invdays):
 state=np.ones(len(p));armed=False;low=0.;recover=.10;count=0;inv_until=-1
 for i in range(1,len(p)):
  if sr[i]<=shock:
   if not armed:armed=True;low=p.iloc[i];recover=.10;count=1
   else:count+=1;low=min(low,p.iloc[i]);recover=target if count>=escalate_at else .10
   if count>=escalate_at:inv_until=i+invdays
  if armed:
   low=min(low,p.iloc[i])
   if p.iloc[i]/low-1>=recover:armed=False;inv_until=-1
   elif i<=inv_until:state[i]=-1
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;d=np.where(ex==1,1+tr,np.where(ex==-1,1+sr,1));e=INITIAL*np.cumprod(d);w=pd.Series(e,index=p.index);return e[-1],float((w/w.cummax()-1).min()),float((ex==-1).mean()),float((ex==0).mean())
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);p=q["Close"].squeeze().astype(float).reindex(idx);tr=ret(t.reindex(idx));br=ret(b.reindex(idx));rows=[]
 for shock in [-.045,-.05,-.055]:
  for n in [2,3,4]:
   for target in [.20,.30,.40]:
    for inv in [1,2,3,5,10]:
     f,dd,ip,cp=run(p,tr,br,shock,n,target,inv);yrs=(idx[-1]-idx[0]).days/365.25;rows.append({"rule":f"S{shock}_N{n}_T{target}_I{inv}","final":f,"cagr":(f/INITIAL)**(1/yrs)-1,"maxdd":dd,"sqqq":ip,"cash":cp})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"persistent_bear_sqqq.csv",index=False);print(out.sort_values("final",ascending=False).head(25).to_string(index=False))
if __name__=="__main__":main()
