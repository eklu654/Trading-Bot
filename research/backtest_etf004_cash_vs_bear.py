from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
PAIRS={"QQQ":("TQQQ","SQQQ"),"SPY":("SPXL","SPXS"),"SOXX":("SOXL","SOXS")}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
def load(s):
    return pd.read_csv(DATA/(s.lower()+"_daily.csv"),parse_dates=["Date"]).set_index("Date").sort_index()
def metrics(f):
    r=f["return"].dropna(); eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; vol=r.std(ddof=1)*np.sqrt(252); dd=(eq/eq.cummax()-1).min()
    neg=r[r<0].std(ddof=1); sh=r.mean()/r.std(ddof=1)*np.sqrt(252); so=r.mean()/neg*np.sqrt(252) if pd.notna(neg) and neg>0 else np.nan
    return {"observations":len(r),"total_return":total,"annualized_return":ann,"max_drawdown":dd,"annualized_volatility":vol,"sharpe":sh,"sortino":so,"ending_value_5000":5000*eq.iloc[-1]}
def main():
    u={x:load(x)["close"] for x in PAIRS}; common=pd.concat(u,axis=1).dropna()
    etf={t:load(t) for p in PAIRS.values() for t in p}; states={}
    for x,c in u.items():
        ma=c.rolling(200,min_periods=200).mean(); above=(c>=ma).fillna(False); states[x]=above.rolling(5,min_periods=5).sum().fillna(0)>=1
    rows=[]
    for mode in ("CASH","BEAR"):
        daily=[0.0]
        for i in range(1,len(common.index)):
            date=common.index[i]; prev=common.index[i-1]; ret=0.0
            for x,(bull,bear) in PAIRS.items():
                ticker=bull if bool(states[x].loc[prev]) else (bear if mode=="BEAR" else None)
                if ticker:
                    p=etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
                    if prev in p.index and date in p.index: ret += .25*float(p.loc[date]/p.loc[prev]-1)
            daily.append(ret)
        f=pd.DataFrame({"return":daily},index=common.index)
        for split,(a,b) in SPLITS.items(): rows.append({"mode":mode,"split":split,**metrics(f.loc[a:b])})
    out=pd.DataFrame(rows); out.to_csv(DATA/"etf004_cash_vs_bear_summary.csv",index=False); print(out.to_string(index=False))
if __name__=="__main__": main()