"""Crash-triggered persistent-bear filter.
After a QQQ shock, require both positive momentum and a trend-recovery condition before TQQQ reentry.
Tests modern actual TQQQ and synthetic 3x QQQ pre-TQQQ history.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s,start,end):
 x=yf.download(s,start=start,end=end,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def modern():
 q=dl("QQQ","2010-01-01","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07")
 p=q["Close"].squeeze().astype(float);ta=t["Close"].squeeze().astype(float);idx=p.index.intersection(ta.index);p,ta=p.reindex(idx),ta.reindex(idx);r=p.pct_change();tr=ta.pct_change();rows=[]
 for shock in [-.04,-.045,-.05]:
  for mom in [10,20]:
   for ma in [50,100,200]:
    s=np.ones(len(idx));armed=False
    for i in range(1,len(idx)):
     if r.iloc[i]<=shock:armed=True
     if armed:
      ok=i>=mom and p.iloc[i]/p.iloc[i-mom]-1>0 and i>=ma and p.iloc[i]>=p.rolling(ma).mean().iloc[i]
      if ok:armed=False
      else:s[i]=0
    ex=np.roll(s,1);ex[0]=1;e=INITIAL*np.cumprod(1+tr.to_numpy()*ex);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"set":"actual","rule":f"S{shock}_M{mom}_MA{ma}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((s==0).mean())})
 return rows
def synth():
 q=dl("QQQ","1999-03-11","2010-03-11");p=q["Close"].squeeze().astype(float);r=p.pct_change();lev=(1+3*r).clip(lower=0).to_numpy();pv=p.to_numpy();rows=[]
 for shock in [-.04,-.045,-.05]:
  for mom in [10,20]:
   for ma in [50,100,200]:
    s=np.ones(len(p));armed=False
    for i in range(1,len(p)):
     if r.iloc[i]<=shock:armed=True
     if armed:
      ok=i>=mom and pv[i]/pv[i-mom]-1>0 and i>=ma and pv[i]>=p.rolling(ma).mean().iloc[i]
      if ok:armed=False
      else:s[i]=0
    ex=np.roll(s,1);ex[0]=1;e=INITIAL*np.cumprod(np.where(ex,lev,1));w=pd.Series(e,index=p.index);rows.append({"set":"synthetic","rule":f"S{shock}_M{mom}_MA{ma}","final":e[-1],"cagr":(e[-1]/INITIAL)**(365.25/max((p.index[-1]-p.index[0]).days,1))-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((s==0).mean())})
 return rows
out=pd.DataFrame(modern()+synth());OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_persistent_bear_filter.csv",index=False);print(out.sort_values(["set","final"],ascending=[True,False]).to_string(index=False))

# trigger
