"""ETF-010 rare-event bear-gate research.

Rather than predicting every next move, this experiment asks whether inverse
exposure is useful only when multiple independent deterioration signals agree.

For each underlying, a bear score is built from:
1. price below 200-DMA,
2. negative 200-DMA slope,
3. negative 20-day momentum,
4. negative 60-day momentum,
5. weak cross-market breadth,
6. elevated VIX percentile.

A sleeve becomes BEAR only after the configured score threshold persists for
the configured confirmation period. Otherwise it is BULL when the underlying
passes the normal 200-DMA trend gate, or CASH when neither condition holds.

All thresholds are fixed research parameters; no holdout tuning is performed.
Same-underlying bull/bear overlap is impossible.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
PAIRS={"QQQ":("TQQQ","SQQQ"),"SPY":("SPXL","SPXS"),"SOXX":("SOXL","SOXS")}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
SCORES=(3,4,5,6)
CONFIRM=(1,3,5,10)
VIX_PCTS=(0.60,0.70,0.80)
BREADTH=(0.33,0.50,0.67)


def load(symbol):
    return pd.read_csv(DATA/f"{symbol.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def build():
    under={x:load(x)["close"] for x in PAIRS}
    raw={x:load(x) for p in PAIRS.values() for x in p}
    vix=load("vix_daily")["vix"]
    close=pd.concat(under,axis=1)
    bull=(close>close.rolling(200).mean()).mean(axis=1)
    vix_pct=vix.rolling(253).apply(lambda x: (x[:-1] <= x[-1]).mean() if len(x)>30 else np.nan,raw=True)
    features={}
    for name,c in under.items():
        ma=c.rolling(200).mean()
        f=pd.DataFrame(index=c.index)
        f["below200"]=c<ma
        f["slope_negative"]=ma.pct_change(20)<0
        f["mom20_negative"]=c.pct_change(20)<0
        f["mom60_negative"]=c.pct_change(60)<0
        f["breadth_weak"]=bull.reindex(c.index)
        f["vix_pct"]=vix_pct.reindex(c.index)
        f["bear_score"]=(
            f["below200"].astype(int)+f["slope_negative"].astype(int)+
            f["mom20_negative"].astype(int)+f["mom60_negative"].astype(int)+
            (f["breadth_weak"]<=0.50).astype(int)
        )
        features[name]=f
    return features,raw


def state_series(f,score_threshold,confirm,vix_pct,breadth):
    score=(f["below200"].astype(int)+f["slope_negative"].astype(int)+
           f["mom20_negative"].astype(int)+f["mom60_negative"].astype(int)+
           (f["breadth_weak"]<=breadth).astype(int)+
           (f["vix_pct"]>=vix_pct).astype(int))
    bear_raw=score>=score_threshold
    bull_raw=(~f["below200"]) & (~f["slope_negative"])
    state=[]; current="CASH"; pending=None; streak=0
    for b,u in zip(bear_raw.fillna(False),bull_raw.fillna(False)):
        candidate="BEAR" if b else "BULL" if u else "CASH"
        if candidate==current:
            pending=None; streak=0
        elif candidate==pending:
            streak+=1
            if streak>=confirm:
                current=candidate; pending=None; streak=0
        else:
            pending=candidate; streak=1
        state.append(current)
    return pd.Series(state,index=f.index).shift(1).fillna("CASH")


def metrics(r):
    r=r.dropna(); eq=(1+r).cumprod()
    years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1
    ann=(1+total)**(1/years)-1
    dd=(eq/eq.cummax()-1).min()
    vol=r.std(ddof=1)*np.sqrt(252)
    sh=r.mean()/r.std(ddof=1)*np.sqrt(252)
    return ann,total,dd,vol,sh,5000*eq.iloc[-1]


def replay(features,raw,score_threshold,confirm,vix_pct,breadth):
    states={n:state_series(f,score_threshold,confirm,vix_pct,breadth) for n,f in features.items()}
    idx=pd.concat([raw[x]["adj_close"] for x in raw],axis=1).index
    daily=pd.Series(0.0,index=idx)
    for n,(bull,bear) in PAIRS.items():
        rb=raw[bull]["adj_close"].reindex(idx).pct_change()
        rs=raw[bear]["adj_close"].reindex(idx).pct_change()
        st=states[n].reindex(idx).ffill().fillna("CASH")
        daily=daily.add(rb.where(st=="BULL",0).add(rs.where(st=="BEAR",0),fill_value=0)*0.25,fill_value=0)
    return daily,states


def main():
    features,raw=build(); rows=[]
    for score in SCORES:
      for confirm in CONFIRM:
       for vp in VIX_PCTS:
        for br in BREADTH:
         daily,_=replay(features,raw,score,confirm,vp,br)
         train=metrics(daily.loc[SPLITS["train"][0]:SPLITS["train"][1]])
         for split,(a,b) in SPLITS.items():
          m=metrics(daily.loc[a:b])
          rows.append({"score":score,"confirm":confirm,"vix_percentile":vp,"breadth_threshold":br,"split":split,
                       "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                       "annualized_volatility":m[3],"sharpe":m[4],"ending_value_5000":m[5],
                       "train_sharpe":train[4]})
    out=pd.DataFrame(rows)
    out.to_csv(DATA/"etf010_bear_gate_results.csv",index=False)
    print("=== ETF-010 VALIDATION TOP 20 ===")
    print(out[out.split=="validation"].sort_values(["sharpe","annualized_return"],ascending=False).head(20).to_string(index=False))
    print("\n=== ETF-010 HOLDOUT FOR VALIDATION TOP 10 ===")
    keys=out[out.split=="validation"].sort_values(["sharpe","annualized_return"],ascending=False).head(10)[["score","confirm","vix_percentile","breadth_threshold"]]
    print(out[out.split=="holdout"].merge(keys,on=["score","confirm","vix_percentile","breadth_threshold"]).sort_values(["sharpe","annualized_return"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
