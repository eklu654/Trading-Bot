"""Sparse crash switch: default TQQQ; after severe QQQ shock, switch to SQQQ for cooldown.
Causal close signal -> next-session open execution. Tests whether cash can be monetized.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="2010-01-01";END="2026-10-07"
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def main():
 q,t,b=dl("QQQ"),dl("TQQQ"),dl("SQQQ");idx=q.index.intersection(t.index).intersection(b.index);q,t,b=q.reindex(idx),t.reindex(idx),b.reindex(idx)
 def rr(x):
  ao=x.open*x.adj_close/x.close
  return (ao/x.adj_close.shift(1)-1).fillna(0),(x.adj_close/ao-1).fillna(0)
 ton,tin=rr(t);bon,bin=rr(b);r=q.adj_close.pct_change();rows=[]
 for shock in [-.035,-.04,-.045,-.05,-.055,-.06,-.07]:
  for c in [1,3,5,7,10,15,20]:
   state=np.ones(len(idx));until=-1
   for i in range(len(idx)):
    if i<=until: state[i]=-1
    if i>=1 and r.iloc[i]<=shock: until=i+c;state[i]=-1
   # state 1=TQQQ, -1=SQQQ; next open execution
   daily=np.where(np.roll(state,1)==1,(1+ton)*(1+tin),np.where(np.roll(state,1)==-1,(1+bon)*(1+bin),1));daily[0]=1
   e=INITIAL*np.cumprod(daily);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
   rows.append({"rule":f"S{shock}_C{c}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"inverse_pct":float((state==-1).mean())})
   # inverse only first 3 days then cash for rest
   for invdays in [1,3,5]:
    st=np.ones(len(idx));u=-1
    for i in range(len(idx)):
     if i<=u: st[i]=-1
     if i>=1 and r.iloc[i]<=shock: u=i+invdays;st[i]=-1
    daily=np.where(np.roll(st,1)==1,(1+ton)*(1+tin),np.where(np.roll(st,1)==-1,(1+bon)*(1+bin),1));daily[0]=1
    e=INITIAL*np.cumprod(daily);w=pd.Series(e,index=idx)
    rows.append({"rule":f"S{shock}_INV{invdays}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"inverse_pct":float((st==-1).mean())})
 d=INITIAL*np.cumprod((1+ton)*(1+tin));w=pd.Series(d,index=idx);rows.append({"rule":"TQQQ_BH","final":d.iloc[-1],"cagr":(d.iloc[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"inverse_pct":0})
 out=pd.DataFrame(rows).sort_values("final",ascending=False);\n # chronological holdout: evaluate fixed candidate SQQQ shock rules separately by era\n wf=[]\n for shock,cool in [(-.04,10),(-.045,10),(-.05,7),(-.05,10),(-.055,10),(-.06,10)]:\n  st=np.ones(len(idx));u=-1\n  for i in range(len(idx)):\n   if i<=u: st[i]=-1\n   if i>=1 and r.iloc[i]<=shock: u=i+cool;st[i]=-1\n  ex=np.roll(st,1);ex[0]=1;dr=np.where(ex==1,(1+ton)*(1+tin),(1+bon)*(1+bin))-1\n  for era,a,z in [("2010_17","2010-01-01","2017-12-31"),("2018_21","2018-01-01","2021-12-31"),("2022_26","2022-01-01","2026-10-07")]:\n   m=(idx>=pd.Timestamp(a))&(idx<=pd.Timestamp(z));v=np.prod(1+dr[m]);wf.append({"rule":f"S{shock}_C{cool}","era":era,"growth":v})\n OUT.mkdir(parents=True,exist_ok=True)\n pd.DataFrame(wf).to_csv(OUT/"tqqq_sparse_inverse_holdout.csv",index=False)(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_sparse_inverse_switch.csv",index=False);print(out.head(60).to_string(index=False))
if __name__=="__main__":main()
