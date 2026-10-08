"""Strict validation for sparse crash brake.
Fixed candidate plus adjacent parameter neighborhood. Reports era compounding and costs.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_cost_equity,next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
PER=[("2010-2013","2010-01-01","2013-12-31"),("2014-2017","2014-01-01","2017-12-31"),("2018-2021","2018-01-01","2021-12-31"),("2022-2026","2022-01-01","2026-10-07")]
CANDS=[(1,x,c) for x in [-.04,-.045,-.05,-.055,-.06,-.07] for c in [3,5,7,10,15]]+[(2,x,c) for x in [-.05,-.07,-.10] for c in [1,3,5,7,10]]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(r,look,shock,c):
 s=np.ones(len(r));until=-1
 for i in range(len(r)):
  if i<=until:s[i]=0
  if i>=look and r.iloc[i-look+1:i+1].sum()<=shock:
   until=i+c;s[i]=0
 return pd.Series(s,index=r.index)
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);p=q.adj_close;r=p.pct_change()
 ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 rows=[]
 for look,shock,c in CANDS:
  s=sig(r,look,shock,c);d=next_open_daily_returns(s,on,inn);e=INITIAL*np.cumprod(1+d);yrs=(idx[-1]-idx[0]).days/365.25
  rows.append({"rule":f"L{look}_S{shock}_C{c}","period":"FULL","start":INITIAL,"end":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((pd.Series(e,index=idx)/pd.Series(e,index=idx).cummax()-1).min()),"cash":float((s==0).mean())})
  for bps in [5,10,25]:
   w=next_open_cost_equity(s,on.to_numpy(),inn.to_numpy(),bps,INITIAL);rows.append({"rule":f"L{look}_S{shock}_C{c}","period":f"COST{bps}","start":INITIAL,"end":w[-1],"cagr":(w[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((pd.Series(w,index=idx)/pd.Series(w,index=idx).cummax()-1).min()),"cash":float((s==0).mean())})
  # sequential era chaining using daily returns
  wealth=INITIAL
  for n,a,b in PER:
   m=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(b));ii=np.where(m)[0]; st,en=ii[0],ii[-1]
   base=wealth;wealth=base*np.prod(1+d[st:en+1]);rows.append({"rule":f"L{look}_S{shock}_C{c}","period":n,"start":base,"end":wealth,"cagr":(wealth/base)**(365.25/max((idx[en]-idx[st]).days,1))-1,"maxdd":np.nan,"cash":float((s.iloc[st:en+1]==0).mean())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_sparse_crash_brake_validation.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
