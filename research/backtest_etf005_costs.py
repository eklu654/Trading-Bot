from pathlib import Path
import numpy as np
import pandas as pd
from backtest_etf001 import SYMBOLS, build_common_frame, load_prices, load_vix
from backtest_etf001_matrix import generate_signal
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"research"
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
CANDIDATES={"baseline":(200,0.0,0.0,5),"robust":(200,0.02,0.01,5)}
COSTS=(0,5,10,20,30,50)
def main():
 p,v=load_prices(),load_vix(); rows=[]
 for name,params in CANDIDATES.items():
  common=build_common_frame(p,v); sleeve=.75/len(SYMBOLS)
  h=pd.DataFrame({s:generate_signal(common[s],*params).shift(1).fillna(False) for s in SYMBOLS},index=common.index)
  px=pd.concat({s:p[s]["adj_close"] for s in SYMBOLS},axis=1).reindex(common.index); gross=sum(sleeve*px.pct_change().fillna(0)[s]*h[s].astype(float) for s in SYMBOLS)
  turnover=h.astype(float).diff().abs().sum(axis=1)*sleeve
  for bps in COSTS:
   net=gross-turnover*bps/10000; f=pd.DataFrame({"return":net,"turnover":turnover},index=common.index)
   for split,(a,b) in SPLITS.items():
    x=f.loc[a:b]; r=x["return"]; eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25); total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; vol=r.std(ddof=1)*np.sqrt(252); dd=(eq/eq.cummax()-1).min(); sh=r.mean()/r.std(ddof=1)*np.sqrt(252)
    rows.append({"candidate":name,"cost_bps":bps,"split":split,"annualized_return":ann,"max_drawdown":dd,"sharpe":sh,"ending_value_5000":5000*eq.iloc[-1],"total_turnover":x["turnover"].sum()})
 out=pd.DataFrame(rows); out.to_csv(DATA/"etf005_cost_sensitivity_summary.csv",index=False); print(out.to_string(index=False))
if __name__=="__main__": main()