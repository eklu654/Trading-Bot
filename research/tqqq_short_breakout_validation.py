"""Strict validation of the short-horizon breakout cluster.
Candidates are frozen before this script runs; no selection occurs inside the OOS periods.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns,next_open_cost_equity
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
PER=[("2010-2013","2010-01-01","2013-12-31"),("2014-2017","2014-01-01","2017-12-31"),("2018-2021","2018-01-01","2021-12-31"),("2022-2026","2022-01-01","2026-10-07")]
CANDS=[(1,15),(1,20),(2,15),(2,20),(3,15),(3,20),(5,20),(7,20),(10,20),(20,20)]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def sig(p,look,hold):
 hi=p.shift(1).rolling(look).max(); on=False; rem=0; out=[]
 for i in range(len(p)):
  if on:
   rem-=1
   if rem<=0:on=False
  if not on and i>=look+1 and p.iloc[i]>hi.iloc[i]:
   on=True;rem=hold
  out.append(float(on))
 return pd.Series(out,index=p.index)
def equity(s,d):
 return INITIAL*np.cumprod(1+d)
def cagr(a,b,days):
 return (b/a)**(365.25/max(days,1))-1
def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx)
 ao=t.open*t.adj_close/t.close;o=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0)
 rows=[]
 for look,hold in CANDS:
  s=sig(q.adj_close,look,hold); d=next_open_daily_returns(s,o,inn); e=equity(s,d)
  for n,a,b in PER:
   mask=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(b));ii=np.flatnonzero(mask);st,en=ii[0],ii[-1]
   base=e[st-1] if st else INITIAL; rows.append({"rule":f"BREAK{look}_H{hold}","period":n,"start":base,"end":e[en],"cagr":cagr(base,e[en],(idx[en]-idx[st]).days),"maxdd":float((pd.Series(e[st:en+1])/pd.Series(e[st:en+1]).cummax()-1).min())})
  for bps in [0,5,10,25]:
   w=next_open_cost_equity(s,o,inn,bps,INITIAL);rows.append({"rule":f"BREAK{look}_H{hold}","period":f"cost_{bps}bps","start":INITIAL,"end":w[-1],"cagr":cagr(INITIAL,w[-1],(idx[-1]-idx[0]).days),"maxdd":np.nan})
 bh=np.ones(len(idx));d=next_open_daily_returns(bh,o,inn);e=equity(bh,d)
 rows.append({"rule":"BUY&HOLD","period":"FULL","start":INITIAL,"end":e[-1],"cagr":cagr(INITIAL,e[-1],(idx[-1]-idx[0]).days),"maxdd":float((pd.Series(e)/pd.Series(e).cummax()-1).min())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_short_breakout_validation.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
