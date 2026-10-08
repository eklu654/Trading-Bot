from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
CANDS=[(s,b,i,c) for s in [-.04,-.045,-.05,-.055] for b in [.05,.10] for i in [.05,.10] for c in [.20,.30,.40,.50]]
def dl(s,a,b):
 x=yf.download(s,start=a,end=b,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def run(p,signal,asset,shock,base,inc,cap):
 state=np.ones(len(p));armed=False;low=0.;target=base
 for i in range(1,len(p)):
  if signal[i]<=shock:
   if not armed:armed=True;low=p.iloc[i];target=base
   else:target=min(cap,target+inc);low=min(low,p.iloc[i])
  if armed:
   low=min(low,p.iloc[i])
   if p.iloc[i]/low-1>=target:armed=False
   else:state[i]=0
 ex=np.roll(state,1);ex[0]=1;return INITIAL*np.cumprod(1+asset*ex)
def evalset(p,asset,windows,label):
 sig=p.pct_change().fillna(0).to_numpy();ret=asset
 rows=[]
 for shock,b,i,c in CANDS:
  e=run(p,sig,ret,shock,b,i,c)
  for name,a,z in windows:
   ii=np.where((p.index>=a)&(p.index<=z))[0];st,en=ii[0],ii[-1];v=e[en]/e[st-1] if st>0 else e[en]/INITIAL
   rows.append({"asset":label,"rule":f"S{shock}_B{b}_I{i}_C{c}","window":name,"growth":v,"cagr":v**(365.25/max((p.index[en]-p.index[st]).days,1))-1})
 return pd.DataFrame(rows)
def main():
 q=dl("QQQ","1999-03-11","2026-10-07");t=dl("TQQQ","2010-01-01","2026-10-07");idx=q.index.intersection(t.index);pa=q["Close"].squeeze().astype(float).reindex(idx);ta=t["Close"].squeeze().astype(float).reindex(idx)
 aw=[("TRAIN1","2010-01-01","2017-12-31"),("TEST1","2018-01-01","2021-12-31"),("TRAIN2","2010-01-01","2021-12-31"),("TEST2","2022-01-01","2026-10-07")]
 actual=evalset(pa,ta.pct_change().fillna(0).to_numpy(),aw,"actual")
 synp=q["Close"].squeeze().astype(float);synp=synp[(synp.index>="1999-03-11")&(synp.index<="2010-03-11")];synret=np.clip(1+3*synp.pct_change().fillna(0).to_numpy(),0,None)-1
 syn=evalset(synp,synret,[("TRAIN","1999-03-11","2004-12-31"),("TEST","2005-01-01","2010-03-11")],"synthetic")
 out=pd.concat([actual,syn],ignore_index=True);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"adaptive_recovery_walkforward.csv",index=False)
 for tr,te in [("TRAIN1","TEST1"),("TRAIN2","TEST2"),("TRAIN","TEST")]:
  d=out[out.window==tr].sort_values("growth",ascending=False);best=d.iloc[0].rule
  print("\n"+tr+" => "+te+" "+best);print(out[(out.window==te)&(out.rule==best)].to_string(index=False));print("TOP");print(out[out.window==te].sort_values("growth",ascending=False).head(8).to_string(index=False))
if __name__=="__main__":main()

# trigger
