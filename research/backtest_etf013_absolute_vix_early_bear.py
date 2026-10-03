"""ETF-013 absolute-VIX early bear override research.

ETF-012 found validation improvement from an early bear override but weaker
holdout performance. This experiment removes the rolling VIX percentile and
uses absolute VIX thresholds, making the signal simpler and less dependent
on the historical distribution of volatility.

A confirmed bear gate overrides the normal 200-DMA/5-session bull state.
Only the configured fraction of each 25% sleeve goes to its inverse ETF;
the remainder is cash. Same-underlying bull/bear overlap is impossible.

Validation is used for parameter selection; holdout is reported only for
validation-selected candidates.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
PAIRS={"QQQ":("TQQQ","SQQQ"),"SPY":("SPXL","SPXS"),"SOXX":("SOXL","SOXS")}
SLEEVE=0.25
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}
FRACTIONS=(0.25,0.50,0.75,1.00)
SCORES=(3,4,5)
CONFIRM=(1,3,5)
VIX_LEVELS=(20,22,25,28,30,32)
BREADTH=(0.33,0.50,0.67)


def load(symbol):
    return pd.read_csv(DATA/f"{symbol.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def inputs():
    under={n:load(n)["close"] for n in PAIRS}
    raw={x:load(x) for p in PAIRS.values() for x in p}
    vix=pd.read_csv(DATA/"vix_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["vix"]
    close=pd.concat(under,axis=1)
    breadth=(close>close.rolling(200).mean()).mean(axis=1)
    return under,raw,breadth,vix


def bull_state(close):
    ma=close.rolling(200).mean()
    active=False; above=0; vals=[]
    for p,m in zip(close,ma):
        if pd.isna(m) or p<m:
            active=False; above=0
        elif not active:
            above+=1
            if above>=5: active=True
        vals.append(active)
    return pd.Series(vals,index=close.index).shift(1).fillna(False).astype(bool)


def bear_gate(close,breadth,vix,score_threshold,confirm,vix_level,br):
    ma=close.rolling(200).mean()
    score=(
        (close<ma).astype(int)
        +(ma.pct_change(20)<0).astype(int)
        +(close.pct_change(20)<0).astype(int)
        +(close.pct_change(60)<0).astype(int)
        +(breadth.reindex(close.index)<=br).astype(int)
        +(vix.reindex(close.index)>=vix_level).astype(int)
    )
    raw=(score>=score_threshold).fillna(False).astype(bool)
    runs=raw.astype(int).groupby((~raw).cumsum()).cumsum()
    return (runs>=confirm).shift(1).fillna(False).astype(bool)


def metrics(r):
    r=r.dropna(); eq=(1+r).cumprod()
    years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1
    dd=(eq/eq.cummax()-1).min(); vol=r.std(ddof=1)*np.sqrt(252)
    sh=r.mean()/r.std(ddof=1)*np.sqrt(252) if r.std(ddof=1)>0 else np.nan
    down=r.where(r<0).std(ddof=1)
    so=r.mean()/down*np.sqrt(252) if pd.notna(down) and down>0 else np.nan
    return ann,total,dd,vol,sh,so,5000*eq.iloc[-1]


def main():
    under,raw,breadth,vix=inputs()
    bulls={n:bull_state(c) for n,c in under.items()}
    idx=pd.concat([raw[x]["adj_close"] for x in raw],axis=1).dropna().index
    baseline=pd.Series(0.0,index=idx)
    for n,(b,_) in PAIRS.items():
        rb=raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
        baseline=baseline.add(SLEEVE*rb.where(bulls[n].reindex(idx).fillna(False),0),fill_value=0)

    rows=[]
    for frac in FRACTIONS:
      for score_threshold in SCORES:
       for confirm in CONFIRM:
        for vl in VIX_LEVELS:
         for br in BREADTH:
          gates={n:bear_gate(c,breadth,vix,score_threshold,confirm,vl,br) for n,c in under.items()}
          daily=pd.Series(0.0,index=idx); inv=pd.Series(0,index=idx)
          for n,(b,bear) in PAIRS.items():
            rb=raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
            rs=raw[bear]["adj_close"].reindex(idx).pct_change().fillna(0)
            gate=gates[n].reindex(idx).fillna(False)
            normal_bull=bulls[n].reindex(idx).fillna(False) & ~gate
            daily=daily.add(SLEEVE*rb.where(normal_bull,0),fill_value=0)
            daily=daily.add(SLEEVE*frac*rs.where(gate,0),fill_value=0)
            inv=inv.add(gate.astype(int),fill_value=0)
          for split,(a,z) in SPLITS.items():
            m=metrics(daily.loc[a:z])
            rows.append({"inverse_fraction":frac,"score":score_threshold,"confirm":confirm,
                         "vix_level":vl,"breadth_threshold":br,"split":split,
                         "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                         "annualized_volatility":m[3],"sharpe":m[4],"sortino":m[5],
                         "ending_value_5000":m[6],"mean_inverse_sleeves":inv.loc[a:z].mean()})

    out=pd.DataFrame(rows)
    bases=[]
    for split,(a,z) in SPLITS.items():
        m=metrics(baseline.loc[a:z])
        bases.append({"strategy":"ETF001_BASELINE_CASH","split":split,"annualized_return":m[0],
                      "total_return":m[1],"max_drawdown":m[2],"annualized_volatility":m[3],
                      "sharpe":m[4],"sortino":m[5],"ending_value_5000":m[6]})
    base=pd.DataFrame(bases)
    out.to_csv(DATA/"etf013_absolute_vix_early_bear_results.csv",index=False)
    base.to_csv(DATA/"etf013_baseline_results.csv",index=False)

    val=out[out.split=="validation"].copy(); bval=base.loc[base.split=="validation"].iloc[0]
    val["sharpe_delta_vs_baseline"]=val.sharpe-bval.sharpe
    val["return_delta_vs_baseline"]=val.annualized_return-bval.annualized_return
    top=val.sort_values(["sharpe_delta_vs_baseline","annualized_return"],ascending=False).head(20)
    print("=== ETF-013 BASELINE ==="); print(base.to_string(index=False))
    print("\n=== ETF-013 VALIDATION TOP 20 ==="); print(top.to_string(index=False))
    keys=top.head(10)[["inverse_fraction","score","confirm","vix_level","breadth_threshold"]]
    hold=out[out.split=="holdout"].merge(keys,on=["inverse_fraction","score","confirm","vix_level","breadth_threshold"])
    print("\n=== ETF-013 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(hold.sort_values(["sharpe","annualized_return"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
