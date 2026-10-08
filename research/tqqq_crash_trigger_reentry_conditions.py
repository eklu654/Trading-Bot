"""Crash-triggered regime holdout: only enter protection after a QQQ shock.
Compare re-entry conditions designed to distinguish V-shaped crashes from prolonged bears.
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
def run(p,r,shock,cond):
 s=np.ones(len(p));armed=False
 for i in range(1,len(p)):
  if r.iloc[i]<=shock: armed=True
  if armed:
   if cond(i): armed=False
   else: s[i]=0
 return s
def main():
 q,t=dl("QQQ"),dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);p=q.adj_close;r=p.pct_change()
 ao=t.open*t.adj_close/t.close;on=(ao/t.adj_close.shift(1)-1).fillna(0);inn=(t.adj_close/ao-1).fillna(0);rows=[]
 for shock in [-.04,-.05,-.06,-.07]:
  for kind in ["immediate","mom5","mom10","mom20","above20high","above50ma","above100ma","above200ma"]:
   def cond(i,k=kind):
    if k=="immediate": return True
    if k.startswith("mom"): return i>=int(k[3:]) and p.iloc[i]/p.iloc[i-int(k[3:])]-1>0
    if k.endswith("high"): n=int(k[5:-4]); return i>=n and p.iloc[i]>=p.iloc[i-n+1:i+1].max()
    n=int(k[5:-2]); return i>=n and p.iloc[i]>=p.rolling(n).mean().iloc[i]
   s=run(p,r,shock,cond);d=next_open_daily_returns(pd.Series(s,index=idx),on,inn);e=INITIAL*np.cumprod(1+d);w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
   rows.append({"rule":f"S{shock}_{kind}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((s==0).mean())})
 bh=next_open_daily_returns(pd.Series(1.,index=idx),on,inn);e=INITIAL*np.cumprod(1+bh);w=pd.Series(e,index=idx);rows.append({"rule":"TQQQ_BH","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash":0})
 out=pd.DataFrame(rows).sort_values("final",ascending=False);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"tqqq_crash_trigger_reentry_conditions.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()

# validation trigger
