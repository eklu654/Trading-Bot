"""Clean holdout check for fixed 100-DMA exit + predeclared re-entry rules.

No winner is selected inside the holdout. We report full continuous curves by
fixed calendar periods so a rule's behavior can be inspected without restarting.
Candidate set is frozen to rules already tested:
MOM5, MOM10, MOM20, MOM10_3D, MOM10_CROSS, MOM10_20DMA, 50DMA.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
PERIODS=[("2010_2014","2010-01-01","2014-12-31"),("2015_2019","2015-01-01","2019-12-31"),("2020_2022","2020-01-01","2022-12-31"),("2023_2026","2023-01-01","2026-10-07")]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def make(p,r):
 m100=p.rolling(100).mean(); m50=p.rolling(50).mean(); m20=p.rolling(20).mean(); m5=p.pct_change(5); m10=p.pct_change(10); on=False; out=[]
 for i in range(len(p)):
  if on and i>=99 and p.iloc[i]<m100.iloc[i]: on=False
  elif not on and i>=99:
   x={"MOM5":m5.iloc[i]>0,"MOM10":m10.iloc[i]>0,"MOM20":p.pct_change(20).iloc[i]>0,
      "MOM10_3D":m10.iloc[i]>0 and m10.iloc[i-1]>0 and m10.iloc[i-2]>0,
      "MOM10_CROSS":m10.iloc[i]>0 and m10.iloc[i-1]<=0,
      "MOM10_20DMA":m10.iloc[i]>0 and p.iloc[i]>=m20.iloc[i],
      "50DMA":p.iloc[i]>=m50.iloc[i]}[r]
   if x:on=True
  out.append(float(on))
 return pd.Series(out,index=p.index)
def tr(t):
 ao=t.open*t.adj_close/t.close; return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx); o,ii=tr(t)
 rows=[]
 for tn,p in [("QQQ",q.adj_close),("TQQQ",t.adj_close)]:
  for r in ["MOM5","MOM10","MOM20","MOM10_3D","MOM10_CROSS","MOM10_20DMA","50DMA"]:
   s=make(p,r); d=next_open_daily_returns(s,o,ii); eq=INITIAL*np.cumprod(1+d)
   for pn,a,b in PERIODS:
    mask=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(b)); ids=np.flatnonzero(mask)
    if len(ids)<2:continue
    st,en=ids[0],ids[-1]; base=eq[st-1] if st else INITIAL; end=eq[en]; yrs=(idx[en]-idx[st]).days/365.25
    rows.append({"trigger":tn,"reentry":r,"period":pn,"start_balance":base,"end_balance":end,"period_cagr":(end/base)**(1/max(yrs,1e-9))-1})
 out=pd.DataFrame(rows); OUT.mkdir(parents=True,exist_ok=True); out.to_csv(OUT/"tqqq_100dma_reentry_holdout_periods.csv",index=False); print(out.to_string(index=False))
if __name__=="__main__":main()
