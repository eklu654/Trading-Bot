"""ETF-012 early bear override research.

Tests whether the rare-event ETF-010 bear gate can improve timing by
overriding the normal ETF-001 200-DMA bull state before the underlying
actually crosses below its 200-DMA.

When the bear gate is false, the normal 200-DMA/5-session bull state applies.
When the bear gate is confirmed, the configured fraction of the 25% sleeve is
switched to its inverse ETF immediately; the remainder is cash. Thus a sleeve
can never hold its bull and inverse ETFs simultaneously.

Parameters are selected on validation only. Holdout is reported only for the
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
SCORES=(3,4,5,6)
CONFIRM=(1,3,5)
VIX_PCTS=(0.60,0.70,0.80)
BREADTH=(0.33,0.50,0.67)


def load(symbol):
    return pd.read_csv(DATA/f"{symbol.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def inputs():
    under={n:load(n)["close"] for n in PAIRS}
    raw={x:load(x) for p in PAIRS.values() for x in p}
    vix=pd.read_csv(DATA/"vix_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["vix"]
    close=pd.concat(under,axis=1)
    breadth=(close>close.rolling(200).mean()).mean(axis=1)
    vix_pct=vix.rolling(253).apply(lambda x:(x[:-1]<=x[-1]).mean() if len(x)>30 else np.nan,raw=True)
    return under,raw,breadth,vix_pct


def bull_state(close):
    ma=close.rolling(200).mean()
    active=False
    above=0
    vals=[]
    for p,m in zip(close,ma):
        if pd.isna(m) or p<m:
            active=False; above=0
        elif not active:
            above+=1
            if above>=5: active=True
        vals.append(active)
    return pd.Series(vals,index=close.index).shift(1).fillna(False).astype(bool)


def bear_gate(close,breadth,vix_pct,score_threshold,confirm,vp,br):
    ma=close.rolling(200).mean()
    score=(
        (close<ma).astype(int)
        +(ma.pct_change(20)<0).astype(int)
        +(close.pct_change(20)<0).astype(int)
        +(close.pct_change(60)<0).astype(int)
        +(breadth.reindex(close.index)<=br).astype(int)
        +(vix_pct.reindex(close.index)>=vp).astype(int)
    )
    raw=(score>=score_threshold).fillna(False).astype(bool)
    runs=raw.astype(int).groupby((~raw).cumsum()).cumsum()
    return (runs>=confirm).shift(1).fillna(False).astype(bool)


def metrics(r):
    r=r.dropna()
    eq=(1+r).cumprod()
    years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1
    ann=(1+total)**(1/years)-1
    dd=(eq/eq.cummax()-1).min()
    vol=r.std(ddof=1)*np.sqrt(252)
    sh=r.mean()/r.std(ddof=1)*np.sqrt(252) if r.std(ddof=1)>0 else np.nan
    down=r.where(r<0).std(ddof=1)
    sortino=r.mean()/down*np.sqrt(252) if pd.notna(down) and down>0 else np.nan
    return ann,total,dd,vol,sh,sortino,5000*eq.iloc[-1]


def main():
    under,raw,breadth,vix_pct=inputs()
    bulls={n:bull_state(c) for n,c in under.items()}
    idx=pd.concat([raw[x]["adj_close"] for x in raw],axis=1).index

    baseline=pd.Series(0.0,index=idx)
    for n,(b,_) in PAIRS.items():
        rb=raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
        baseline=baseline.add(SLEEVE*rb.where(bulls[n].reindex(idx).fillna(False),0),fill_value=0)

    rows=[]
    for frac in FRACTIONS:
      for score_threshold in SCORES:
       for confirm in CONFIRM:
        for vp in VIX_PCTS:
         for br in BREADTH:
          gates={n:bear_gate(c,breadth,vix_pct,score_threshold,confirm,vp,br) for n,c in under.items()}
          daily=pd.Series(0.0,index=idx)
          inv_sleeves=pd.Series(0,index=idx)
          override_sleeves=pd.Series(0,index=idx)
          for n,(b,bear) in PAIRS.items():
            rb=raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
            rs=raw[bear]["adj_close"].reindex(idx).pct_change().fillna(0)
            bull=bulls[n].reindex(idx).fillna(False)
            gate=gates[n].reindex(idx).fillna(False)
            inv=gate
            normal_bull=bull & ~gate
            daily=daily.add(SLEEVE*rb.where(normal_bull,0),fill_value=0)
            daily=daily.add(SLEEVE*frac*rs.where(inv,0),fill_value=0)
            inv_sleeves=inv_sleeves.add(inv.astype(int),fill_value=0)
            override_sleeves=override_sleeves.add((inv & bull).astype(int),fill_value=0)
          for split,(a,z) in SPLITS.items():
            m=metrics(daily.loc[a:z])
            rows.append({
                "inverse_fraction":frac,"score":score_threshold,"confirm":confirm,
                "vix_percentile":vp,"breadth_threshold":br,"split":split,
                "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                "annualized_volatility":m[3],"sharpe":m[4],"sortino":m[5],
                "ending_value_5000":m[6],
                "mean_inverse_sleeves":inv_sleeves.loc[a:z].mean(),
                "mean_early_override_sleeves":override_sleeves.loc[a:z].mean(),
            })

    out=pd.DataFrame(rows)
    base_rows=[]
    for split,(a,z) in SPLITS.items():
        m=metrics(baseline.loc[a:z])
        base_rows.append({"strategy":"ETF001_BASELINE_CASH","split":split,
                          "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                          "annualized_volatility":m[3],"sharpe":m[4],"sortino":m[5],
                          "ending_value_5000":m[6]})
    base=pd.DataFrame(base_rows)
    out.to_csv(DATA/"etf012_early_bear_override_results.csv",index=False)
    base.to_csv(DATA/"etf012_baseline_results.csv",index=False)

    val=out[out.split=="validation"].copy()
    bval=base.loc[base.split=="validation"].iloc[0]
    val["sharpe_delta_vs_baseline"]=val.sharpe-bval.sharpe
    val["return_delta_vs_baseline"]=val.annualized_return-bval.annualized_return
    top=val.sort_values(["sharpe_delta_vs_baseline","annualized_return"],ascending=False).head(20)
    print("=== ETF-012 BASELINE ===")
    print(base.to_string(index=False))
    print("\n=== ETF-012 VALIDATION TOP 20 ===")
    print(top.to_string(index=False))
    keys=top.head(10)[["inverse_fraction","score","confirm","vix_percentile","breadth_threshold"]]
    hold=out[out.split=="holdout"].merge(keys,on=["inverse_fraction","score","confirm","vix_percentile","breadth_threshold"])
    print("\n=== ETF-012 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(hold.sort_values(["sharpe","annualized_return"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
