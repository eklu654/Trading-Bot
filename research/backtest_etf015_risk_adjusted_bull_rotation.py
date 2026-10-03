"""ETF-015 risk-adjusted bull rotation research.

Bull-only sector/family selection across five broad underlyings:
QQQ/TQQQ, SPY/SPXL, SOXX/SOXL, DIA/UDOW, IWM/TNA.

Every candidate must be above its 200-DMA with configurable consecutive-close
confirmation. The portfolio invests 75% equally across the top 1, 2, or 3
eligible candidates and keeps 25% cash.

Ranking signals:
- 60-day momentum
- 120-day momentum
- 60-day momentum divided by 20-day realized volatility
- 120-day momentum divided by 60-day realized volatility

No inverse ETF is used, and no same-underlying bull/bear overlap is possible.
Validation selects configurations; holdout is only reported for validation
leaders.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
PAIRS={"QQQ":"TQQQ","SPY":"SPXL","SOXX":"SOXL","DIA":"UDOW","IWM":"TNA"}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
SCORES=("MOM60","MOM120","RISK60","RISK120")
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
    return ann,total,dd,vol,sh,so,5000*eq.iloc[-1]


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

    rows=[]
    for score_name in SCORES:
      for confirm in CONFIRM:
       for topn in TOP_N:
        daily=pd.Series(0.0,index=idx)
        chosen_count=pd.Series(0,index=idx)
        eligible_state={}
        for u,f in features.items():
            raw=f["eligible_raw"].fillna(False).astype(bool)
            runs=raw.astype(int).groupby((~raw).cumsum()).cumsum()
            eligible_state[u]=(runs>=confirm).shift(1).fillna(False).astype(bool)

        for i in range(1,len(idx)):
            prev=idx[i-1]; date=idx[i]; candidates=[]
            for u in PAIRS:
                if not bool(eligible_state[u].reindex(idx).loc[prev]): continue
                score=features[u].loc[prev,score_name]
                if pd.notna(score) and prev in etf[u].index and date in etf[u].index:
                    candidates.append((float(score),u))
            candidates.sort(reverse=True)
            chosen=candidates[:topn]
            if chosen:
                w=(1-CASH)/len(chosen)
                for _,u in chosen:
                    daily.loc[date]+=w*float(etf[u].loc[date]/etf[u].loc[prev]-1)
                chosen_count.loc[date]=len(chosen)

        for split,(a,z) in SPLITS.items():
            m=metrics(daily.loc[a:z])
            rows.append({"score":score_name,"confirm":confirm,"top_n":topn,"split":split,
                         "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                         "annualized_volatility":m[3],"sharpe":m[4],"sortino":m[5],
                         "ending_value_5000":m[6],"mean_selected_sleeves":chosen_count.loc[a:z].mean()})

    out=pd.DataFrame(rows)
    out.to_csv(DATA/"etf015_risk_adjusted_bull_rotation.csv",index=False)
    val=out[out.split=="validation"].sort_values(["sharpe","annualized_return"],ascending=False)
    print("=== ETF-015 VALIDATION TOP 20 ==="); print(val.head(20).to_string(index=False))
    keys=val.head(10)[["score","confirm","top_n"]]
    hold=out[out.split=="holdout"].merge(keys,on=["score","confirm","top_n"])
    print("\n=== ETF-015 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(hold.sort_values(["sharpe","annualized_return"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
