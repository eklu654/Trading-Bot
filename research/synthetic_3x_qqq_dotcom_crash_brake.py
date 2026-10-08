"""Synthetic pre-TQQQ stress test.
Constructs a simple 3x daily QQQ return series before TQQQ existed. This is NOT actual
TQQQ history; it is only a structural test of the crash-brake idea against dot-com.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.;START="1999-03-10";END="2010-03-11"
def dl():
 x=yf.download("QQQ",start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x
def main():
 q=dl();p=q["Adj Close"]; r=p.pct_change().fillna(0)
 # simple daily 3x compounding, no fees/financing; only structural
 lev=(1+3*r).clip(lower=0)
 bh=INITIAL*np.cumprod(lev)
 rows=[]
 for shock in [-.04,-.045,-.05,-.06,-.07]:
  for c in [3,5,7,10,15]:
   s=np.ones(len(p));until=-1
   for i in range(len(p)):
    if i<=until:s[i]=0
    if i>=1 and r.iloc[i]<=shock:
     until=i+c;s[i]=0
   # signal close -> next day's return; synthetic daily series
   ex=np.roll(s,1);ex[0]=0
   daily=np.where(ex,lev,1)
   e=INITIAL*np.cumprod(daily)
   rows.append({"rule":f"S{shock}_C{c}","final":e[-1],"cagr":(e[-1]/INITIAL)**(365.25/max((p.index[-1]-p.index[0]).days,1))-1,"maxdd":float((pd.Series(e)/pd.Series(e).cummax()-1).min()),"cash":float((s==0).mean())})
 rows.append({"rule":"SYNTHETIC_3X_BH","final":bh[-1],"cagr":(bh[-1]/INITIAL)**(365.25/max((p.index[-1]-p.index[0]).days,1))-1,"maxdd":float((pd.Series(bh)/pd.Series(bh).cummax()-1).min()),"cash":0})
 out=pd.DataFrame(rows).sort_values("final",ascending=False);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"synthetic_3x_qqq_dotcom_crash_brake.csv",index=False);print(out.to_string(index=False))
if __name__=="__main__":main()
