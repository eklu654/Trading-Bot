"""Validation of the strongest crash-triggered momentum reentry family."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
CANDS=[(-.04,5),(-.045,5),(-.05,5),(-.055,5),(-.06,5),(-.05,10),(-.05,15),(-.05,20),(-.045,10),(-.055,10)]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,r,shock,n):
 s=np.ones(len(p));armed=False
 for i in range(1,len(p)):
  if r.iloc[i]<=shock: armed=True
  if armed:
   if i>=n and p.iloc[i]/p.iloc[i-n]-1>0: armed=False
   else:s[i]=0
 return pd.Series(s,index=p.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);p=q.adj_close;r=p.pct_change()
 ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 eras=[("2010-2017","2010-01-01","2017-12-31"),("2018-2021","2018-01-01","2021-12-31"),("2022-2026","2022-01-01","2026-10-07")]
 rows=[]
 for shock,n in CANDS:
  s=sig(p,r,shock,n);d=next_open_daily_returns(s,on,inn)
  for name,a,b in eras:
   m=(idx>=a)&(idx<=b);ii=np.where(m)[0];st,en=ii[0],ii[-1];v=np.prod(1+d[st:en+1]);rows.append({"rule":f"S{shock}_M{n}","era":name,"growth":v,"cagr":v**(365.25/max((idx[en]-idx[st]).days,1))-1,"cash":float((s.iloc[st:en+1]==0).mean())})
  e=INITIAL*np.cumprod(1+d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25;rows.append({"rule":f"S{shock}_M{n}","era":"FULL","growth":e[-1]/INITIAL,"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"cash":float((s==0).mean())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_crash_momentum_validation.csv",index=False);print(out.sort_values(["era","growth"],ascending=[True,False]).to_string(index=False))
if __name__=="__main__":main()
