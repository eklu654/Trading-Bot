"""Persistent-bear discriminator walk-forward.
Frozen simple trigger: QQQ daily shock <= -4.5%; defensive until recovery target.
Compare fixed 10%, fixed 20/30/40%, and escalation based on:
- repeated shock count
- lower-low count
- rebound failure
- days without recovery
All use QQQ signal, TQQQ returns, next-session execution.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s,a,b):
 x=yf.download(s,start=a,end=b,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def run(p,asset,mode,param):
 r=p.pct_change().fillna(0).to_numpy();state=np.ones(len(p));armed=False;low=0.;target=.10;shocks=0;days=0;fail=0;peak=0
 for i in range(1,len(p)):
  if not armed and r[i]<=-.045:
   armed=True;low=p.iloc[i];peak=p.iloc[i];shocks=1;days=0;fail=0;target=.10
  if armed:
   days+=1;low=min(low,p.iloc[i]);peak=max(peak,p.iloc[i])
   if r[i]<=-.045: shocks+=1
   rec=p.iloc[i]/low-1
   if mode=="fixed": target=param
   elif mode=="shock": target=min(param[1],.10+param[0]*max(0,shocks-1))
   elif mode=="low": target=param[1] if p.iloc[i] < peak*(1-param[0]) else .10
   elif mode=="time": target=param[1] if days>=param[0] else .10
   elif mode=="fail":
    if rec>=.10 and p.iloc[i]<peak: fail+=1
    target=param[1] if fail>=param[0] else .10
   if rec>=target:armed=False
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;e=INITIAL*np.cumprod(1+asset*ex);w=pd.Series(e,index=p.index)
 return e[-1],float((w/w.cummax()-1).min())
def main():
 q=dl("QQQ","2010-01-01","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07");p=q["Close"].squeeze().astype(float);a=t["Close"].squeeze().astype(float).reindex(p.index).pct_change().fillna(0).to_numpy()
 specs=[("fixed",x) for x in [.10,.15,.20,.30,.40,.50]]
 specs += [("shock",(x,.40)) for x in [.05,.10,.15,.20]]
 specs += [("low",(x,.30)) for x in [.02,.03,.05,.10]]
 specs += [("time",(x,.30)) for x in [10,20,30,40,60]]
 specs += [("fail",(x,.30)) for x in [1,2,3,4]]
 rows=[]
 for mode,param in specs:
  f,dd=run(p,a,mode,param);rows.append({"rule":f"{mode}:{param}","final":f,"cagr":(f/INITIAL)**(365.25/(p.index[-1]-p.index[0]).days)-1,"maxdd":dd})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"bear_discriminator_modern.csv",index=False);print(out.sort_values("final",ascending=False).to_string(index=False))
if __name__=="__main__":main()
