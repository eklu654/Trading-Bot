from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"research"
PAIRS={"QQQ":("TQQQ","SQQQ"),"SPY":("SPXL","SPXS"),"SOXX":("SOXL","SOXS")}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
def load(s): return pd.read_csv(DATA/(s.lower()+"_daily.csv"),parse_dates=["Date"]).set_index("Date").sort_index()["adj_close"]
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25); total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; dd=(eq/eq.cummax()-1).min(); sh=r.mean()/r.std(ddof=1)*np.sqrt(252); return ann,dd,sh,5000*eq.iloc[-1]
def main():
 etf={t:load(t) for p in PAIRS.values() for t in p}; common=pd.concat(etf,axis=1).dropna(); rows=[]
 for mode in ("ORACLE","BULL_ONLY_ORACLE"):
  daily=[]
  for i in range(len(common.index)):
   if i==0: daily.append(0.0); continue
   date=common.index[i]; prev=common.index[i-1]; ret=0.0
   for bull,bear in PAIRS.values():
    br=float(common.loc[date,bull]/common.loc[prev,bull]-1); sr=float(common.loc[date,bear]/common.loc[prev,bear]-1)
    if mode=="ORACLE": ret += .25*max(br,sr,0.0)
    else: ret += .25*max(br,0.0)
   daily.append(ret)
  f=pd.Series(daily,index=common.index)
  for split,(a,b) in SPLITS.items():
   ann,dd,sh,end=metrics(f.loc[a:b]); rows.append({"strategy":mode,"split":split,"annualized_return":ann,"max_drawdown":dd,"sharpe":sh,"ending_value_5000":end})
 out=pd.DataFrame(rows); out.to_csv(DATA/"etf007_oracle_timing_upper_bound.csv",index=False); print(out.to_string(index=False))
if __name__=="__main__": main()