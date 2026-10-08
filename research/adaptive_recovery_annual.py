"""Annual decomposition of a pre-specified adaptive crash rule.
Rule is frozen before evaluation: QQQ daily shock <= -5%; base recovery 10%; each additional shock while defensive raises target by 5%, capped at 20%.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def main():
 q=dl("QQQ");t=dl("TQQQ");idx=q.index.intersection(t.index);p=q["Close"].squeeze().astype(float).reindex(idx);r=p.pct_change().fillna(0).to_numpy();tr=t["Close"].squeeze().astype(float).reindex(idx).pct_change().fillna(0).to_numpy()
 state=np.ones(len(idx));armed=False;low=0.;target=.10
 for i in range(1,len(idx)):
  if r[i]<=-.05:
   if not armed:armed=True;low=p.iloc[i];target=.10
   else:target=min(.20,target+.05);low=min(low,p.iloc[i])
  if armed:
   low=min(low,p.iloc[i])
   if p.iloc[i]/low-1>=target:armed=False
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;d=1+tr*ex
 rows=[]
 for y,g in pd.Series(d,index=idx).groupby(idx.year):
  v=g.prod();b=(1+tr[[i.year==y for i in idx]]).prod();rows.append({"year":y,"strategy_growth":v,"strategy_return":v-1,"bh_growth":b,"bh_return":b-1,"strategy_better":v>b,"defensive_days":int((ex[[i.year==y for i in idx]]==0).sum())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"adaptive_recovery_annual.csv",index=False);print(out.to_string(index=False));print("\nCumulative strategy",np.prod(d),"B&H",np.prod(1+tr))
if __name__=="__main__":main()

# trigger
