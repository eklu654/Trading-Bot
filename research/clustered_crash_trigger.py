"""Crash trigger quality test: require either a severe one-day QQQ shock or clustered moderate shocks.
Frozen recovery rule: base 10%, +5% per additional shock, cap 20%.
Compares trigger variants and annual behavior with causal next-session execution.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def run(p,asset,severe,moderate,window):
 r=p.pct_change().fillna(0).to_numpy();state=np.ones(len(p));armed=False;low=0.;target=.10;shockcount=0;recent=[]
 for i in range(1,len(p)):
  recent=[j for j in recent if i-j<=window]
  if r[i]<=severe:
   if not armed:armed=True;low=p.iloc[i];target=.10;shockcount=1
   else:shockcount+=1;target=min(.20,target+.05);low=min(low,p.iloc[i])
   recent.append(i)
  elif r[i]<=moderate:
   recent.append(i)
   if not armed and len(recent)>=2:
    armed=True;low=p.iloc[i];target=.10;shockcount=len(recent)
   elif armed:
    shockcount+=1;target=min(.20,target+.05);low=min(low,p.iloc[i])
  if armed:
   low=min(low,p.iloc[i])
   if p.iloc[i]/low-1>=target:armed=False;recent=[]
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;e=INITIAL*np.cumprod(1+asset*ex);w=pd.Series(e,index=p.index)
 return e,ex,float((w/w.cummax()-1).min())
def main():
 q=dl("QQQ");t=dl("TQQQ");idx=q.index.intersection(t.index);p=q["Close"].squeeze().astype(float).reindex(idx);tr=t["Close"].squeeze().astype(float).reindex(idx).pct_change().fillna(0).to_numpy();rows=[]
 for severe in [-.06,-.07,-.08,-.10]:
  for moderate in [-.045,-.05,-.055]:
   for window in [5,10,20]:
    e,ex,dd=run(p,tr,severe,moderate,window);rows.append({"rule":f"SEV{severe}_MOD{moderate}_W{window}","final":e[-1],"cagr":(e[-1]/INITIAL)**(365.25/(idx[-1]-idx[0]).days)-1,"maxdd":dd,"defensive":int((ex==0).sum())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"clustered_crash_trigger.csv",index=False);print(out.sort_values("final",ascending=False).head(20).to_string(index=False))
if __name__=="__main__":main()
