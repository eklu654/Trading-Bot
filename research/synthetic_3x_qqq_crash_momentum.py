"""Synthetic 3x QQQ dot-com stress test for crash-triggered momentum reentry."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="1999-03-11";END="2010-03-11"
def main():
 x=yf.download("QQQ",start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 p=x["Close"].squeeze().astype(float);r=p.pct_change().fillna(0);lev=(1+3*r).clip(lower=0);rows=[]
 for shock in [-.04,-.045,-.05,-.055,-.06]:
  for n in [5,10,15,20]:
   s=np.ones(len(p));armed=False
   for i in range(1,len(p)):
    if r.iloc[i]<=shock: armed=True
    if armed:
     if i>=n and p.iloc[i]/p.iloc[i-n]-1>0: armed=False
     else:s[i]=0
   ex=np.roll(s,1);ex[0]=0;e=INITIAL*np.cumprod(np.where(ex,lev,1));w=pd.Series(e,index=p.index)
   rows.append({"rule":f"S{shock}_M{n}","final":e[-1],"cagr":(e[-1]/INITIAL)**(365.25/max((p.index[-1]-p.index[0]).days,1))-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((s==0).mean())})
 bh=INITIAL*np.cumprod(lev);w=pd.Series(bh,index=p.index);rows.append({"rule":"SYNTHETIC_3X_BH","final":bh[-1],"cagr":(bh[-1]/INITIAL)**(365.25/max((p.index[-1]-p.index[0]).days,1))-1,"maxdd":float((w/w.cummax()-1).min()),"cash":0})
 out=pd.DataFrame(rows).sort_values("final",ascending=False);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"synthetic_3x_qqq_crash_momentum.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
