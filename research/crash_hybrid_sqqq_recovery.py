"""Causal hybrid: QQQ shock -> short SQQQ burst -> cash -> reenter after recovery from post-shock low.
No simultaneous TQQQ/SQQQ. The shock/recovery logic uses QQQ closes; all state changes execute next open.
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
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx)
 p=q["Close"].squeeze().astype(float);qr=p.pct_change().fillna(0).to_numpy();tr=ret(t);br=ret(b);rows=[]
 for shock in [-.04,-.045,-.05,-.055]:
  for rec in [.05,.10,.15,.20,.25]:
   for inv in [1,2,3,5]:
    state=np.ones(len(idx));armed=False;low=0.;until=-1
    for i in range(1,len(idx)):
     if qr[i]<=shock:armed=True;low=p.iloc[i];until=i+inv
     if armed:
      low=min(low,p.iloc[i])
      if p.iloc[i]/low-1>=rec:armed=False
      elif i<=until:state[i]=-1
      else:state[i]=0
    ex=np.roll(state,1);ex[0]=1
    d=np.where(ex==1,1+tr,np.where(ex==-1,1+br,1))
    e=INITIAL*np.cumprod(d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"rule":f"S{shock}_R{rec}_I{inv}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"sqqq":float((ex==-1).mean()),"cash":float((ex==0).mean()),"switches":int(np.sum(ex[1:]!=ex[:-1]))})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_hybrid_sqqq_recovery.csv",index=False);print(out.sort_values("final",ascending=False).head(25).to_string(index=False))

# trigger

# trigger
