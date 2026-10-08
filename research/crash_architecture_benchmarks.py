"""Benchmark the causal QQQ-shock architecture: TQQQ B&H, cash defense, SQQQ defense.
Uses the two walk-forward-selected rules plus fixed -5%/10d/1d.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
RULES=[(-.045,10,1),(-.045,15,1),(-.05,10,1),(-.05,10,10)]
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def main():
 q=dl("QQQ");t=dl("TQQQ");b=dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx);p=q["Close"].squeeze().astype(float);tr=t["Close"].squeeze().astype(float).pct_change().fillna(0).to_numpy();br=b["Close"].squeeze().astype(float).pct_change().fillna(0).to_numpy();qr=p.pct_change().fillna(0).to_numpy();rows=[]
 specs=[("TQQQ_BH",np.ones(len(idx)),tr)]
 for shock,mom,hold in RULES:
  state=np.ones(len(idx));armed=False;until=-1
  for i in range(1,len(idx)):
   if qr[i]<=shock:armed=True;until=i+hold
   if armed:
    if i>=mom and p.iloc[i]/p.iloc[i-mom]-1>0:armed=False
    elif i<=until:state[i]=-1
    else:state[i]=0
  ex=np.roll(state,1);ex[0]=1;specs += [(f"S{shock}_M{mom}_I{hold}_CASH",ex,np.zeros(len(idx))), (f"S{shock}_M{mom}_I{hold}_SQQQ",ex,br)]
 for name,state,inv in specs:
  if name=="TQQQ_BH":d=1+tr
  else:d=np.where(state==1,1+tr,np.where(state==-1,1+inv,1))
  e=INITIAL*np.cumprod(d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25;rows.append({"rule":name,"final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min())})
 out=pd.DataFrame(rows).sort_values("final",ascending=False);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_architecture_benchmarks.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
