from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s,a,b):
 x=yf.download(s,start=a,end=b,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def test(p,signal_ret,asset_ret,shock,r1,r2,mid):
 s=np.ones(len(p));armed=False;low=0.
 for i in range(1,len(p)):
  if signal_ret[i]<=shock:armed=True;low=p.iloc[i]
  if armed:
   low=min(low,p.iloc[i]);rec=p.iloc[i]/low-1
   if rec>=r2:armed=False;s[i]=1
   elif rec>=r1:s[i]=mid
   else:s[i]=0
 ex=np.roll(s,1);ex[0]=1;e=INITIAL*np.cumprod(1+asset_ret*ex);w=pd.Series(e,index=p.index)
 return e[-1],float((w/w.cummax()-1).min()),float((ex==0).mean()),float((ex==mid).mean())
def main():
 q=dl("QQQ","1999-03-11","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07");idx=q.index.intersection(t.index)
 pa,ta=q["Close"].squeeze().astype(float).reindex(idx),t["Close"].squeeze().astype(float).reindex(idx);rows=[]
 for shock in [-.04,-.045,-.05,-.055]:
  for r1 in [.05,.10]:
   for r2 in [.15,.20,.30,.40]:
    for mid in [.25,.50,.75]:
     f,dd,c,m=test(pa,pa.pct_change().fillna(0).to_numpy(),ta.pct_change().fillna(0).to_numpy(),shock,r1,r2,mid);yrs=(idx[-1]-idx[0]).days/365.25
     rows.append({"set":"actual","rule":f"S{shock}_R{r1}_{r2}_M{mid}","final":f,"cagr":(f/INITIAL)**(1/yrs)-1,"maxdd":dd,"cash":c,"partial":m})
 synp=q["Close"].squeeze().astype(float);sr=synp.pct_change().fillna(0).to_numpy();slev=np.clip(1+3*sr,0,None)-1
 for shock in [-.04,-.045,-.05,-.055]:
  for r1 in [.05,.10]:
   for r2 in [.15,.20,.30,.40]:
    for mid in [.25,.50,.75]:
     f,dd,c,m=test(synp,sr,slev,shock,r1,r2,mid);yrs=(synp.index[-1]-synp.index[0]).days/365.25
     rows.append({"set":"synthetic","rule":f"S{shock}_R{r1}_{r2}_M{mid}","final":f,"cagr":(f/INITIAL)**(1/yrs)-1,"maxdd":dd,"cash":c,"partial":m})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"crash_partial_reentry_causal.csv",index=False)
 print(out.sort_values(["set","final"],ascending=[True,False]).groupby("set").head(15).to_string(index=False))
if __name__=="__main__":main()
