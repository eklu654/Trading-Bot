from pathlib import Path
import numpy as np
import pandas as pd
from backtest_etf001 import SYMBOLS, build_common_frame, load_prices, load_vix, overall_summary
from backtest_etf001_matrix import generate_signal
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"research"
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
CANDIDATES={"baseline_200_0_0_5":(200,0.00,0.00,5),"robust_200_2_1_5":(200,0.02,0.01,5)}
COST_BPS=(0,5,10,20,30,50)
def run(prices,vix,params,cost_bps):
    common=build_common_frame(prices,vix); sleeve=.75/len(SYMBOLS)
    h=pd.DataFrame({s:generate_signal(common[s],*params).shift(1).fillna(False) for s in SYMBOLS},index=common.index)
    p=pd.concat({s:prices[s]["adj_close"] if "adj_close" in prices[s].columns else prices[s]["close"] for s in SYMBOLS},axis=1).reindex(common.index)
    r=p.pct_change().fillna(0); gross=sum(sleeve*r[s]*h[s].astype(float) for s in SYMBOLS)
    turnover=h.astype(float).diff().abs().sum(axis=1)*sleeve
    net=gross-turnover*(cost_bps/10000.0)
    return pd.DataFrame({"portfolio_return":net,"gross_return":gross,"turnover":turnover},index=common.index)
def main():
    prices,vix=load_prices(),load_vix(); rows=[]
    for name,params in CANDIDATES.items():
      for bps in COST_BPS:
        f=run(prices,vix,params,bps)
        for split,(a,b) in SPLITS.items():
          part=f.loc[a:b]; m=overall_summary(part).iloc[0].to_dict()
          rows.append({"candidate":name,"cost_bps":bps,"split":split,"annualized_return":m.get("annualized_return"),"max_drawdown":m.get("max_drawdown"),"sharpe":m.get("sharpe_no_risk_free"),"sortino":m.get("sortino_no_risk_free"),"ending_value_5000":5000*part["portfolio_return"].add(1).prod(),"total_turnover":part["turnover"].sum()})
    out=pd.DataFrame(rows); out.to_csv(DATA/"etf005_cost_sensitivity_summary.csv",index=False); print(out.to_string(index=False))
if __name__=="__main__": main()