"""Hybrid crash + fast recovery + secular-bear regime tests.
Goal: preserve TQQQ compounding, but remain defensive when a crash occurs inside a persistent secular bear.
All signals from QQQ close, positions execute next session.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s,start,end):
 x=yf.download(s,start=start,end=end,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def test(p, lev, label):
 p=p.astype(float); r=p.pct_change().fillna(0); lev=np.asarray(lev,float); ma={n:p.rolling(n).mean() for n in [50,100,150,200,250]}
 rows=[]
 for shock in [-.04,-.05,-.06]:
  for mom in [10,20]:
   for trend in [100,150,200,250]:
    for slope in [0,20,50]:
     for mode in ["recovery","recovery_or_break"]:
      state=np.ones(len(p));defensive=False
      for i in range(1,len(p)):
       shock_now=r.iloc[i]<=shock
       if shock_now: defensive=True
       if defensive:
        momok=i>=mom and p.iloc[i]/p.iloc[i-mom]-1>0
        trendok=i>=trend and p.iloc[i]>=ma[trend].iloc[i]
        slopeok=(slope==0 or (i>=trend+slope and ma[trend].iloc[i]>=ma[trend].iloc[i-slope]))
        if momok and trendok and slopeok: defensive=False
       elif mode=="recovery_or_break":
        if i>=trend and p.iloc[i]<ma[trend].iloc[i]: defensive=True
       state[i]=0 if defensive else 1
      ex=np.roll(state,1);ex[0]=1;e=INITIAL*np.cumprod(1+lev*ex);w=pd.Series(e,index=p.index);yrs=(p.index[-1]-p.index[0]).days/365.25
      rows.append({"set":label,"rule":f"S{shock}_M{mom}_MA{trend}_SL{slope}_{mode}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"defensive":float((state==0).mean())})
 return rows
def main():
 q=dl("QQQ","2010-01-01","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07");idx=q.index.intersection(t.index);p=q["Close"].squeeze().reindex(idx);ta=t["Close"].squeeze().reindex(idx);rows=test(p,ta.pct_change().fillna(0).to_numpy(),"actual")
 q2=dl("QQQ","1999-03-11","2010-03-11");p2=q2["Close"].squeeze();rows+=test(p2,(1+3*p2.pct_change().fillna(0)).clip(lower=0).to_numpy(),"synthetic")
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_hybrid_secular_regime.csv",index=False)
 for s in ["actual","synthetic"]: print("\n",s);print(out[out['set']==s].sort_values('final',ascending=False).head(20).to_string(index=False))
if __name__=="__main__":main()
