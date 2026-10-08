"""TQQQ swing-trading first-pass matrix with causal next-open execution."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
HORIZONS=[2,3,5,10,20]
def dl(s):
 x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def tr(t):
 ao=t.open*t.adj_close/t.close
 return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)
def signal(q,rule,h):
 p=q; ma20=p.rolling(20).mean(); ma100=p.rolling(100).mean(); m3=p.pct_change(3); m5=p.pct_change(5); m10=p.pct_change(10)
 hi5=p.shift(1).rolling(5).max(); hi10=p.shift(1).rolling(10).max(); hi20=p.shift(1).rolling(20).max()
 on=False; remain=0; out=[]
 for i in range(len(p)):
  if on:
   remain-=1
   if remain<=0:on=False
  if not on and i>=100:
   x={"MOM3":m3.iloc[i]>0,"MOM5":m5.iloc[i]>0,"MOM10":m10.iloc[i]>0,
      "BREAK5":p.iloc[i]>hi5.iloc[i],"BREAK10":p.iloc[i]>hi10.iloc[i],"BREAK20":p.iloc[i]>hi20.iloc[i],
      "PULLBACK5":p.iloc[i]<p.iloc[i-5] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i],
      "PULLBACK10":p.iloc[i]<p.iloc[i-10] and p.iloc[i]>p.iloc[i-1] and p.iloc[i]>ma20.iloc[i],
      "TREND_MOM5":p.iloc[i]>ma100.iloc[i] and m5.iloc[i]>0,"TREND_MOM10":p.iloc[i]>ma100.iloc[i] and m10.iloc[i]>0,
      "TREND_BREAK10":p.iloc[i]>ma100.iloc[i] and p.iloc[i]>hi10.iloc[i],
      "MOM10_ACCEL":m10.iloc[i]>0 and m10.iloc[i]>m10.iloc[i-1],"MOM5_ACCEL":m5.iloc[i]>0 and m5.iloc[i]>m5.iloc[i-1]}[rule]
   if x:on=True; remain=h
  out.append(float(on))
 return pd.Series(out,index=p.index)
def stat(name,s,d,idx):
 e=INITIAL*np.cumprod(1+d); w=pd.Series(e,index=idx); dd=w/w.cummax()-1; yrs=(idx[-1]-idx[0]).days/365.25
 return {"strategy":name,"final_balance":float(w.iloc[-1]),"cagr":float((w.iloc[-1]/INITIAL)**(1/yrs)-1),"max_drawdown":float(dd.min()),"avg_exposure":float(s.shift(1).fillna(0).mean()),"trades":int((s.diff().fillna(0)==1).sum())}
def main():
 q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx); overnight,intraday=tr(t); rows=[]
 for rule in ["MOM3","MOM5","MOM10","BREAK5","BREAK10","BREAK20","PULLBACK5","PULLBACK10","TREND_MOM5","TREND_MOM10","TREND_BREAK10","MOM10_ACCEL","MOM5_ACCEL"]:
  for h in HORIZONS:
   s=signal(q.adj_close,rule,h); rows.append(stat(f"TQQQ swing | QQQ {rule} | {h}d",s,next_open_daily_returns(s,overnight,intraday),idx))
 bh=pd.Series(1.,index=idx); rows.append(stat("TQQQ BUY&HOLD",bh,next_open_daily_returns(bh,overnight,intraday),idx))
 r=pd.DataFrame(rows).sort_values("final_balance",ascending=False); OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_swing_first_matrix.csv",index=False); print(r.to_string(index=False))
if __name__=="__main__":main()
