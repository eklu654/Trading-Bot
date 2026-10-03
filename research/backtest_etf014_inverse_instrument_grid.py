"""ETF-014 inverse-instrument leverage research.

Tests whether the poor robustness of inverse overlays is partly caused by using
3x inverse ETFs. The underlying signals use ETF-012's early bear override
framework, while the defensive instrument is varied by leverage.

Profiles:
- 3X: SQQQ / SPXS / SOXS
- 2X: QID / SDS / SSG
- LOW: PSQ / SH / SSG (no -1x semiconductor equivalent in the tested universe)

SSG is -2x the Dow Jones U.S. Semiconductors Index rather than SOXX's exact
benchmark, so LOW is explicitly an approximate semiconductor hedge and is not
treated as equivalent to an exact SOXX inverse.

The same-underlying bull/bear overlap rule is enforced. Parameters are
selected on validation only; holdout is reported for validation-selected
candidates.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
PAIRS={"QQQ":("TQQQ",{"3X":"SQQQ","2X":"QID","LOW":"PSQ"}),
       "SPY":("SPXL",{"3X":"SPXS","2X":"SDS","LOW":"SH"}),
       "SOXX":("SOXL",{"3X":"SOXS","2X":"SSG","LOW":"SSG"})}
SLEEVE=0.25
PROFILES=("3X","2X","LOW")
FRACTIONS=(0.50,1.00)
SCORES=(3,4,5,6)
CONFIRM=(1,3)
VIX_PCTS=(0.70,0.80)
BREADTH=(0.33,0.50)
SPLITS={"train":("2010-03-01","2019-12-31"),"validation":("2020-01-01","2022-12-31"),"holdout":("2023-01-01","2099-12-31")}


def load(s):
    return pd.read_csv(DATA/f"{s.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()


def inputs():
    under={n:load(n)["close"] for n in PAIRS}
    raw={s:load(s) for n,(b,inv) in PAIRS.items() for s in [b,*inv.values()]}
    vix=pd.read_csv(DATA/"vix_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["vix"]
    close=pd.concat(under,axis=1)
    breadth=(close>close.rolling(200).mean()).mean(axis=1)
    vp=vix.rolling(253).apply(lambda x:(x[:-1]<=x[-1]).mean() if len(x)>30 else np.nan,raw=True)
    return under,raw,breadth,vix,vp


def bull_state(c):
    ma=c.rolling(200).mean(); active=False; above=0; out=[]
    for p,m in zip(c,ma):
        if pd.isna(m) or p<m: active=False; above=0
        elif not active:
            above+=1
            if above>=5: active=True
        out.append(active)
    return pd.Series(out,index=c.index).shift(1).fillna(False).astype(bool)


def gate(c,breadth,vp,score,confirm,vixp,br):
    ma=c.rolling(200).mean()
    s=((c<ma).astype(int)+(ma.pct_change(20)<0).astype(int)
       +(c.pct_change(20)<0).astype(int)+(c.pct_change(60)<0).astype(int)
       +(breadth.reindex(c.index)<=br).astype(int)
       +(vp.reindex(c.index)>=vixp).astype(int))
    raw=(s>=score).fillna(False).astype(bool)
    run=raw.astype(int).groupby((~raw).cumsum()).cumsum()
    return (run>=confirm).shift(1).fillna(False).astype(bool)


def metrics(r):
    r=r.dropna(); eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/365.25,1/365.25)
    total=eq.iloc[-1]-1; ann=(1+total)**(1/years)-1; dd=(eq/eq.cummax()-1).min()
    vol=r.std(ddof=1)*np.sqrt(252); sh=r.mean()/r.std(ddof=1)*np.sqrt(252)
    down=r.where(r<0).std(ddof=1); so=r.mean()/down*np.sqrt(252) if pd.notna(down) and down>0 else np.nan
    return ann,total,dd,vol,sh,so,5000*eq.iloc[-1]


def main():
    under,raw,breadth,vix,vp=inputs()
    bulls={n:bull_state(c) for n,c in under.items()}
    idx=pd.concat([raw[s]["adj_close"] for s in raw],axis=1).index
    baseline=pd.Series(0.0,index=idx)
    for n,(b,_) in PAIRS.items():
        rb=raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
        baseline=baseline.add(SLEEVE*rb.where(bulls[n].reindex(idx).fillna(False),0),fill_value=0)

    rows=[]
    for profile in PROFILES:
      for frac in FRACTIONS:
       for score in SCORES:
        for confirm in CONFIRM:
         for vixp in VIX_PCTS:
          for br in BREADTH:
            daily=pd.Series(0.0,index=idx); inv_sleeves=pd.Series(0,index=idx)
            for n,(b,invmap) in PAIRS.items():
                rb=raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
                rs=raw[invmap[profile]]["adj_close"].reindex(idx).pct_change().fillna(0)
                g=gate(under[n],breadth,vp,score,confirm,vixp,br).reindex(idx).fillna(False)
                normal=bulls[n].reindex(idx).fillna(False) & ~g
                daily=daily.add(SLEEVE*rb.where(normal,0),fill_value=0)
                daily=daily.add(SLEEVE*frac*rs.where(g,0),fill_value=0)
                inv_sleeves=inv_sleeves.add(g.astype(int),fill_value=0)
            for split,(a,z) in SPLITS.items():
                m=metrics(daily.loc[a:z])
                rows.append({"profile":profile,"inverse_fraction":frac,"score":score,"confirm":confirm,
                             "vix_percentile":vixp,"breadth_threshold":br,"split":split,
                             "annualized_return":m[0],"total_return":m[1],"max_drawdown":m[2],
                             "annualized_volatility":m[3],"sharpe":m[4],"sortino":m[5],
                             "ending_value_5000":m[6],"mean_inverse_sleeves":inv_sleeves.loc[a:z].mean()})

    out=pd.DataFrame(rows)
    bases=[]
    for split,(a,z) in SPLITS.items():
        m=metrics(baseline.loc[a:z])
        bases.append({"strategy":"ETF001_BASELINE_CASH","split":split,"annualized_return":m[0],
                      "total_return":m[1],"max_drawdown":m[2],"annualized_volatility":m[3],
                      "sharpe":m[4],"sortino":m[5],"ending_value_5000":m[6]})
    base=pd.DataFrame(bases)
    out.to_csv(DATA/"etf014_inverse_instrument_results.csv",index=False)
    base.to_csv(DATA/"etf014_baseline_results.csv",index=False)

    val=out[out.split=="validation"].copy(); bval=base.loc[base.split=="validation"].iloc[0]
    val["sharpe_delta_vs_baseline"]=val.sharpe-bval.sharpe
    val["return_delta_vs_baseline"]=val.annualized_return-bval.annualized_return
    top=val.sort_values(["sharpe_delta_vs_baseline","annualized_return"],ascending=False).head(20)
    print("=== ETF-014 BASELINE ==="); print(base.to_string(index=False))
    print("\n=== ETF-014 VALIDATION TOP 20 ==="); print(top.to_string(index=False))
    keys=top.head(10)[["profile","inverse_fraction","score","confirm","vix_percentile","breadth_threshold"]]
    hold=out[out.split=="holdout"].merge(keys,on=["profile","inverse_fraction","score","confirm","vix_percentile","breadth_threshold"])
    print("\n=== ETF-014 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(hold.sort_values(["sharpe","annualized_return"],ascending=False).to_string(index=False))


if __name__=="__main__":
    main()
