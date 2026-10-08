"""Delayed escalation recovery: require a modest 10% rebound after the first crash, but if multiple shocks occur before recovery, escalate the rebound requirement sharply.
Variants escalate on 2nd/3rd/4th shock to 25/30/40%, aiming to preserve normal V-shaped recovery while treating persistent bears differently.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s,a,b):
 x=yf.download(s,start=a,end=b,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def run(p,asset,shock,escalate_at,target):
 r=p.pct_change().fillna(0).to_numpy();state=np.ones(len(p));armed=False;low=0.;target_now=.10;count=0
 for i in range(1,len(p)):
  if r[i]<=shock:
   if not armed:armed=True;low=p.iloc[i];count=1;target_now=.10
   else:count+=1;low=min(low,p.iloc[i]);target_now=target if count>=escalate_at else .10
  if armed:
   low=min(low,p.iloc[i])
   if p.iloc[i]/low-1>=target_now:armed=False
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;e=INITIAL*np.cumprod(1+asset*ex);w=pd.Series(e,index=p.index);return e[-1],float((w/w.cummax()-1).min()),float((ex==0).mean())
def main():
 q=dl("QQQ","1999-03-11","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07");idx=q.index.intersection(t.index);pa=q["Close"].squeeze().astype(float).reindex(idx);ta=t["Close"].squeeze().astype(float).reindex(idx);rows=[]
 for shock in [-.045,-.05,-.055]:
  for n in [2,3,4]:
   for target in [.20,.25,.30,.40]:
    f,dd,c=run(pa,ta.pct_change().fillna(0).to_numpy(),shock,n,target);yrs=(idx[-1]-idx[0]).days/365.25;rows.append({"set":"actual","rule":f"S{shock}_N{n}_T{target}","final":f,"cagr":(f/INITIAL)**(1/yrs)-1,"maxdd":dd,"cash":c})
 synp=q["Close"].squeeze().astype(float);synp=synp[(synp.index>="1999-03-11")&(synp.index<="2010-03-11")];sr=synp.pct_change().fillna(0).to_numpy();lev=np.clip(1+3*sr,0,None)-1
 for shock in [-.045,-.05,-.055]:
  for n in [2,3,4]:
   for target in [.20,.25,.30,.40]:
    f,dd,c=run(synp,lev,shock,n,target);yrs=(synp.index[-1]-synp.index[0]).days/365.25;rows.append({"set":"synthetic","rule":f"S{shock}_N{n}_T{target}","final":f,"cagr":(f/INITIAL)**(1/yrs)-1,"maxdd":dd,"cash":c})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"delayed_escalation_recovery.csv",index=False)
 for s in ["actual","synthetic"]:
  x=out[out['set']==s];print("\n"+s+" TOP");print(x.sort_values('final',ascending=False).head(15).to_string(index=False));print("\n"+s+" BEST DD >=5000");print(x[x.final>=5000].sort_values('maxdd',ascending=False).head(10).to_string(index=False))
if __name__=="__main__":main()

# trigger
