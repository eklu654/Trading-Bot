"""ETF-016 consistency-gated bull selection.

Replays the ETF-015 bull-only universe but selects candidates using both
training and validation consistency rather than validation Sharpe alone.

Selection objective:
1. require validation Sharpe >= ETF-001 baseline validation Sharpe;
2. require training Sharpe >= ETF-001 baseline training Sharpe;
3. maximize the lower of train/validation Sharpe;
4. break ties with the lower of train/validation annualized return.

This deliberately penalizes configurations that are excellent in only one
historical split. Holdout remains untouched until the candidate is frozen.

Universe and rules match ETF-015:
QQQ/TQQQ, SPY/SPXL, SOXX/SOXL, DIA/UDOW, IWM/TNA; 200-DMA confirmation;
75% invested; top 1/2/3; raw and volatility-adjusted momentum scores.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
PAIRS={"QQQ":"TQQQ","SPY":"SPXL","SOXX":"SOXL","DIA":"UDOW","IWM":"TNA"}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
SCORES=("mom60","mom120","risk60","risk120")
CONFIRM=(1,3,5)
TOP_N=(1,2,3)
CASH=0.25


def load(s):
    return pd.read_csv(DATA/f"{s.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def metrics(r):
    r=r.dropna(); eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; dd=(eq/eq.cummax()-1).min()
    vol=r.std(ddof=1)*np.sqrt(252); sh=r.mean()/r.std(ddof=1)*np.sqrt(252)
    down=r.where(r<0).std(ddof=1); so=r.mean()/down*np.sqrt(252) if pd.notna(down) and down>0 else np.nan
    return {"annualized_return":ann,"total_return":total,"max_drawdown":dd,
            "annualized_volatility":vol,"sharpe":sh,"sortino":so,
            "ending_value_5000":5000*eq.iloc[-1]}


def main():
    under={u:load(u)["close"] for u in PAIRS}
    etf={u:load(t)["adj_close"] for u,t in PAIRS.items()}
    idx=pd.concat(under,axis=1).dropna().index
    features={}
    for u,c in under.items():
        ma=c.rolling(200).mean()
        rv20=c.pct_change().rolling(20).std()*np.sqrt(252)
        rv60=c.pct_change().rolling(60).std()*np.sqrt(252)
        features[u]=pd.DataFrame({
            "eligible_raw":c>=ma,
            "mom60":c.pct_change(60),
            "mom120":c.pct_change(120),
            "risk60":c.pct_change(60)/rv20.replace(0,np.nan),
            "risk120":c.pct_change(120)/rv60.replace(0,np.nan),
        },index=c.index)

    results=[]
    for score_name in SCORES:
      for confirm in CONFIRM:
       for topn in TOP_N:
        daily=pd.Series(0.0,index=idx)
        states={}
        for u,f in features.items():
            raw=f["eligible_raw"].fillna(False).astype(bool)
            runs=raw.astype(int).groupby((~raw).cumsum()).cumsum()
            states[u]=(runs>=confirm).astype(bool).shift(1).fillna(False).astype(bool)
        for i in range(1,len(idx)):
            prev,date=idx[i-1],idx[i]
            candidates=[]
            for u in PAIRS:
                if not bool(states[u].loc[prev]): continue
                s=features[u].loc[prev,score_name]
                if pd.notna(s) and prev in etf[u].index and date in etf[u].index:
                    candidates.append((float(s),u))
            candidates.sort(reverse=True)
            chosen=candidates[:topn]
            if chosen:
                w=(1-CASH)/len(chosen)
                for _,u in chosen:
                    daily.loc[date]+=w*float(etf[u].loc[date]/etf[u].loc[prev]-1)
        row={"score":score_name,"confirm":confirm,"top_n":topn}
        for split,(a,z) in SPLITS.items():
            row.update({f"{k}_{split}":v for k,v in metrics(daily.loc[a:z]).items()})
        results.append(row)

    out=pd.DataFrame(results)
    base_returns=pd.Series(0.0,index=idx)
    # ETF-001-equivalent 3-sleeve bull baseline for consistent comparison.
    for u in ("QQQ","SPY","SOXX"):
        c=under[u]; ma=c.rolling(200).mean(); raw=(c>=ma).fillna(False).astype(bool)
        runs=raw.astype(int).groupby((~raw).cumsum()).cumsum()
        state=(runs>=5).astype(bool).shift(1).fillna(False).astype(bool)
        p=etf[u]
        for i in range(1,len(idx)):
            prev,date=idx[i-1],idx[i]
            if bool(state.reindex(idx).loc[prev]) and prev in p.index and date in p.index:
                base_returns.loc[date]+=0.25*float(p.loc[date]/p.loc[prev]-1)
    base={split:metrics(base_returns.loc[a:z]) for split,(a,z) in SPLITS.items()}
    for split,m in base.items():
        for k,v in m.items(): out[f"baseline_{k}_{split}"]=v

    out["min_train_validation_sharpe"]=out[["sharpe_train","sharpe_validation"]].min(axis=1)
    out["min_train_validation_return"]=out[["annualized_return_train","annualized_return_validation"]].min(axis=1)
    out["validation_sharpe_delta"]=out["sharpe_validation"]-base["validation"]["sharpe"]
    out["train_sharpe_delta"]=out["sharpe_train"]-base["train"]["sharpe"]

    eligible=out[(out.validation_sharpe_delta>=0)&(out.train_sharpe_delta>=0)].copy()
    ranked=eligible.sort_values(["min_train_validation_sharpe","min_train_validation_return"],ascending=False)
    if ranked.empty:
        ranked=out.sort_values(["min_train_validation_sharpe","min_train_validation_return"],ascending=False)
    out.to_csv(DATA/"etf016_consistency_gated_bull_selection.csv",index=False)
    print("=== ETF-016 BASELINES ===")
    print(pd.DataFrame([{"split":s,**base[s]} for s in base]).to_string(index=False))
    print("\n=== ETF-016 CONSISTENCY-GATED CANDIDATES ===")
    print(ranked.head(20)[["score","confirm","top_n","annualized_return_train","sharpe_train","annualized_return_validation","sharpe_validation","max_drawdown_validation","min_train_validation_sharpe","min_train_validation_return","validation_sharpe_delta","train_sharpe_delta"]].to_string(index=False))
    keys=ranked.head(10)[["score","confirm","top_n"]]
    hold=out.merge(keys,on=["score","confirm","top_n"])
    print("\n=== ETF-016 HOLDOUT FOR FROZEN CANDIDATES ===")
    print(hold[["score","confirm","top_n","annualized_return_holdout","sharpe_holdout","max_drawdown_holdout","ending_value_5000_holdout"]].sort_values(["sharpe_holdout","annualized_return_holdout"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
