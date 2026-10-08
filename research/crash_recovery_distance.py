"""Recovery-distance reentry: after a QQQ shock, stay defensive until QQQ recovers X% from the post-trigger low.
Causal next-session execution; evaluates actual TQQQ 2010-2026 and synthetic 3x QQQ 1999-2010.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s,a,b):
 x=yf.download(s,start=a,end=b,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def actual():
 q=dl("QQQ","2010-01-01","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07")
 p=q["Close"].squeeze().astype(float);tr=t["Close"].squeeze().astype(float);idx=p.index.intersection(tr.index);p,tr=p.reindex(idx),tr.reindex(idx);r=p.pct_change();rows=[]
 for shock in [-.035,-.04,-.045,-.05,-.055]:
  for rec in [.05,.10,.15,.20,.25,.30,.40]:
   for hold in [0,5,10]:
    s=np.ones(len(idx));armed=False;low=np.nan;cool=0
    for i in range(1,len(idx)):
     if r.iloc[i]<=shock:armed=True;low=p.iloc[i];cool=hold
     if armed:
      low=min(low,p.iloc[i])
      if cool>0: cool-=1;s[i]=0
      elif p.iloc[i]/low-1>=rec:armed=False
      else:s[i]=0
    ex=np.roll(s,1);ex[0]=1;e=INITIAL*np.cumprod(1+tr.pct_change().fillna(0).to_numpy()*ex);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"set":"actual","rule":f"S{shock}_R{rec}_H{hold}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((s==0).mean())})
 return rows
def synthetic():
 q=dl("QQQ","1999-03-11","2010-03-11");p=q["Close"].squeeze().astype(float);r=p.pct_change().fillna(0);lev=(1+3*r).clip(lower=0).to_numpy();pv=p.to_numpy();rows=[]
 for shock in [-.035,-.04,-.045,-.05,-.055]:
  for rec in [.05,.10,.15,.20,.25,.30,.40]:
   for hold in [0,5,10]:
    s=np.ones(len(p));armed=False;low=0.;cool=0
    for i in range(1,len(p)):
     if r.iloc[i]<=shock:armed=True;low=pv[i];cool=hold
     if armed:
      low=min(low,pv[i])
      if cool>0:cool-=1;s[i]=0
      elif pv[i]/low-1>=rec:armed=False
      else:s[i]=0
    ex=np.roll(s,1);ex[0]=1;e=INITIAL*np.cumprod(np.where(ex,lev,1));w=pd.Series(e,index=p.index)
    rows.append({"set":"synthetic","rule":f"S{shock}_R{rec}_H{hold}","final":e[-1],"cagr":(e[-1]/INITIAL)**(365.25/max((p.index[-1]-p.index[0]).days,1))-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((s==0).mean())})
 return rows
out=pd.DataFrame(actual()+synthetic());OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_recovery_distance.csv",index=False)
print("\nACTUAL TOP\n",out[out['set']=='actual'].sort_values('final',ascending=False).head(20).to_string(index=False))
print("\nSYNTHETIC TOP\n",out[out['set']=='synthetic'].sort_values('final',ascending=False).head(20).to_string(index=False))
print("\nSYNTHETIC LOW-DD\n",out[out['set']=='synthetic'].sort_values('maxdd',ascending=False).head(15).to_string(index=False))

# trigger
