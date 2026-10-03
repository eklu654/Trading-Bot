"""ETF-017 canonical early-bear override.

This is the corrected version of ETF-012 using the exact ETF-001 accounting
framework: common bull-underlying dates, adjusted-close total-return accounting,
25% sleeves, next-session execution, and 25% permanent cash.

The bear gate can override the normal 200-DMA/5-session bull state before a
DMA exit. A configured fraction of the sleeve goes to the corresponding inverse
ETF; the remainder is cash. Same-underlying bull/bear overlap is impossible.

This experiment exists because earlier ETF-011 through ETF-014 replays used a
different portfolio accounting/alignment implementation. Their headline
numbers are retained as exploratory diagnostics but are not promotion evidence.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
SYMBOLS=("TQQQ","SPXL","SOXL")
UNDER={"TQQQ":"QQQ","SPXL":"SPY","SOXL":"SOXX"}
BEAR={"TQQQ":"SQQQ","SPXL":"SPXS","SOXL":"SOXS"}
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
FRACTIONS=(0.25,0.50,0.75,1.00)
SCORES=(3,4,5,6)
CONFIRM=(1,3,5)
VIX_PCTS=(0.60,0.70,0.80)
BREADTH=(0.33,0.50,0.67)
SLEEVE=0.25


def load(s):
    return pd.read_csv(DATA/f"{s.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def metrics(r):
    r=r.dropna(); eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; dd=(eq/eq.cummax()-1).min()
    vol=r.std(ddof=1)*np.sqrt(252); sh=r.mean()/r.std(ddof=1)*np.sqrt(252)
    down=r.where(r<0).std(ddof=1); so=r.mean()/down*np.sqrt(252) if pd.notna(down) and down>0 else np.nan
    return ann,total,dd,vol,sh,so,5000*eq.iloc[-1]


def bull_state(close):
    ma=close.rolling(200,min_periods=200).mean()
    active=False; above=0; out=[]
    for p,m in zip(close,ma):
        if pd.isna(m) or p<m:
            active=False; above=0
        elif not active:
            above+=1
            if above>=5: active=True
        out.append(active)
    return pd.Series(out,index=close.index).shift(1).fillna(False).astype(bool)


def main():
    bull_prices={s:load(s) for s in SYMBOLS}
    under={u:load(u)["close"] for u in UNDER.values()}
    bear_prices={s:load(s) for s in BEAR.values()}
    vix=load("^VIX")["close"] if (DATA/"^vix_daily.csv").exists() else pd.read_csv(DATA/"vix_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["vix"]

    # Exact ETF-001-style common frame: signal calendar is driven by the
    # three bull ETFs/underlyings, not by the inverse products.
    close=pd.concat({s:bull_prices[s]["close"] for s in SYMBOLS},axis=1)
    common=close.dropna(subset=list(SYMBOLS)).copy()
    common["vix"]=vix.reindex(common.index).ffill()

    total_return_prices=pd.concat(
        {s:bull_prices[s]["adj_close"] for s in SYMBOLS}
        | {s:bear_prices[s]["adj_close"] for s in BEAR.values()},
        axis=1,
    ).reindex(common.index)
    returns=total_return_prices.pct_change().fillna(0)

    bulls={s:bull_state(common[s]) for s in SYMBOLS}
    breadth=pd.concat({u:under[u] for u in under},axis=1).reindex(common.index)
    breadth=(breadth>breadth.rolling(200).mean()).mean(axis=1)
    vix_pct=common["vix"].rolling(253).apply(lambda x:(x[:-1]<=x[-1]).mean() if len(x)>30 else np.nan,raw=True)

    baseline=pd.Series(0.0,index=common.index)
    for s in SYMBOLS:
        baseline=baseline.add(SLEEVE*returns[s].where(bulls[s],0),fill_value=0)

    rows=[]
    for frac in FRACTIONS:
      for score_threshold in SCORES:
       for confirm in CONFIRM:
        for vp in VIX_PCTS:
         for br in BREADTH:
          daily=pd.Series(0.0,index=common.index)
          inv_sleeves=pd.Series(0,index=common.index)
          early=pd.Series(0,index=common.index)
          for s in SYMBOLS:
            u=UNDER[s]
            c=common[s]; ma=c.rolling(200,min_periods=200).mean()
            score=((c<ma).astype(int)+(ma.pct_change(20)<0).astype(int)
                   +(c.pct_change(20)<0).astype(int)+(c.pct_change(60)<0).astype(int)
                   +(breadth<=br).astype(int)+(vix_pct>=vp).astype(int))
            raw=(score>=score_threshold).fillna(False).astype(bool)
            run=raw.astype(int).groupby((~raw).cumsum()).cumsum()
            gate=(run>=confirm).astype(bool).shift(1).fillna(False).astype(bool)
            bull=bulls[s]
            normal=bull & ~gate
            daily=daily.add(SLEEVE*returns[s].where(normal,0),fill_value=0)
            daily=daily.add(SLEEVE*frac*returns[BEAR[s]].where(gate,0),fill_value=0)
            inv_sleeves=inv_sleeves.add(gate.astype(int),fill_value=0)
            early=early.add((gate&bull).astype(int),fill_value=0)
          for split,(a,z) in SPLITS.items():
            m=metrics(daily.loc[a:z]); b=metrics(baseline.loc[a:z])
            rows.append({"inverse_fraction":frac,"score":score_threshold,"confirm":confirm,
                         "vix_percentile":vp,"breadth_threshold":br,"split":split,
                         "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                         "annualized_volatility":m[3],"sharpe":m[4],"sortino":m[5],
                         "ending_value_5000":m[6],"mean_inverse_sleeves":inv_sleeves.loc[a:z].mean(),
                         "mean_early_override_sleeves":early.loc[a:z].mean(),
                         "baseline_annualized_return":b[0],"baseline_sharpe":b[4],
                         "baseline_max_drawdown":b[2]})

    out=pd.DataFrame(rows)
    out.to_csv(DATA/"etf017_canonical_early_bear_override.csv",index=False)
    val=out[out.split=="validation"].copy()
    val["sharpe_delta"]=val.sharpe-val.baseline_sharpe
    val["return_delta"]=val.annualized_return-val.baseline_annualized_return
    top=val.sort_values(["sharpe_delta","annualized_return"],ascending=False).head(20)
    print("=== ETF-017 VALIDATION TOP 20 ==="); print(top.to_string(index=False))
    keys=top.head(10)[["inverse_fraction","score","confirm","vix_percentile","breadth_threshold"]]
    hold=out[out.split=="holdout"].merge(keys,on=["inverse_fraction","score","confirm","vix_percentile","breadth_threshold"])
    print("\n=== ETF-017 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(hold.sort_values(["sharpe","annualized_return"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
