from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"research"
PAIRS={"QQQ":("TQQQ","SQQQ"),"SPY":("SPXL","SPXS"),"SOXX":("SOXL","SOXS")}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
EXIT_DAYS=(1,3,5,10,20); REENTRY_DAYS=(1,3,5,10); BUFFERS=(0.0,0.01,0.02)
def load(s): return pd.read_csv(DATA/(s.lower()+"_daily.csv"),parse_dates=["Date"]).set_index("Date").sort_index()
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25); total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; vol=r.std(ddof=1)*np.sqrt(252); dd=(eq/eq.cummax()-1).min(); sh=r.mean()/r.std(ddof=1)*np.sqrt(252); return ann,dd,sh,5000*eq.iloc[-1]
def make_state(c,exit_days,reentry_days,buffer):
 ma=c.rolling(200,min_periods=200).mean(); ratio=c/ma; state=[]; mode="BULL"; below=above=0
 for x in ratio:
  if pd.isna(x): state.append("CASH"); continue
  if mode=="BULL":
   below=below+1 if x < 1-buffer else 0
   if below>=exit_days: mode="BEAR"; above=0
  else:
   above=above+1 if x > 1+buffer else 0
   if above>=reentry_days: mode="BULL"; below=0
  state.append(mode)
 return pd.Series(state,index=c.index)
def main():
 u={x:load(x)["close"] for x in PAIRS}; common=pd.concat(u,axis=1).dropna(); etf={t:load(t)["adj_close"] for p in PAIRS.values() for t in p}
 rows=[]
 for ed in EXIT_DAYS:
  for rd in REENTRY_DAYS:
   for buf in BUFFERS:
    states={x:make_state(u[x],ed,rd,buf) for x in PAIRS}; daily=[]; bear_days=0; switches=0
    prev_states={x:None for x in PAIRS}
    for i in range(len(common.index)):
     if i==0: daily.append(0.0); continue
     date=common.index[i]; prev=common.index[i-1]; ret=0.0
     for x,(bull,bear) in PAIRS.items():
      st=states[x].loc[prev]; ticker=bull if st=="BULL" else bear if st=="BEAR" else None
      if st=="BEAR": bear_days+=1
      if prev_states[x] is not None and prev_states[x]!=st: switches+=1
      prev_states[x]=st
      if ticker and prev in etf[ticker].index and date in etf[ticker].index: ret += .25*float(etf[ticker].loc[date]/etf[ticker].loc[prev]-1)
     daily.append(ret)
    f=pd.Series(daily,index=common.index)
    for split,(a,b) in SPLITS.items():
     ann,dd,sh,end=metrics(f.loc[a:b]); rows.append({"exit_days":ed,"reentry_days":rd,"buffer":buf,"split":split,"annualized_return":ann,"max_drawdown":dd,"sharpe":sh,"ending_value_5000":end,"switches_total":switches,"bear_days_total":bear_days})
 out=pd.DataFrame(rows); out.to_csv(DATA/"etf006_inverse_timing_grid.csv",index=False)
 val=out[out.split=="validation"].sort_values("sharpe",ascending=False).head(15); hold=out[out.split=="holdout"].sort_values("sharpe",ascending=False).head(15)
 print("=== ETF-006 VALIDATION TOP 15 ==="); print(val.to_string(index=False)); print("=== ETF-006 HOLDOUT TOP 15 ==="); print(hold.to_string(index=False))
if __name__=="__main__": main()