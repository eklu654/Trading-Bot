"""Causal walk-forward test of 10% shock recovery with structural-bear overrides.

Core rule:
- QQQ daily shock <= -4.5% arms a defensive state.
- Normal re-entry: QQQ recovers 10% from the post-shock low.
- Override variants replace the 10% target with a slower target (15/20/30/40%)
  when structural weakness is present at the recovery decision.

Structural conditions tested:
1. QQQ 60-day return < threshold, with NO DMA requirement.
2. QQQ below its 100-DMA AND QQQ 60-day return < threshold.

This is causal: today's signal controls the next session; no same-day execution.
Walk-forward:
- Train 2010-2017 -> Test 2018-2021
- Train 2010-2021 -> Test 2022-2026

No parameter is selected from a test period.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-08"
SHOCK=-0.045
NORMAL_TARGET=0.10
OVERRIDE_TARGETS=(0.15,0.20,0.30,0.40)
RET_THRESHOLDS=(0.0,-0.05,-0.10)


def dl(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def signals(q):
    p=q["Close"].squeeze().astype(float)
    dma100=p.rolling(100).mean()
    ret60=p/p.shift(60)-1
    return p,dma100,ret60


def equity(p,dma100,ret60,asset_returns,override_mode=None,override_target=0.30,threshold=0.0):
    """Return causal equity and event diagnostics.

    override_mode:
      baseline      -> always 10% recovery
      ret60         -> if 60d return is below threshold, use override target
      dma_ret60     -> if below 100DMA AND 60d return below threshold, use override
    """
    r=asset_returns.to_numpy()
    px=p.to_numpy()
    ma=dma100.to_numpy()
    r60=ret60.to_numpy()

    invested=np.ones(len(p),dtype=float)
    armed=False
    low=np.nan
    override_hits=0
    exit_count=0
    shock_count=0

    for i in range(1,len(p)):
        if not armed and r[i] <= SHOCK:
            armed=True
            low=px[i]
            shock_count += 1

        if armed:
            low=min(low,px[i])
            target=NORMAL_TARGET
            structural=False
            if override_mode=="ret60":
                structural=np.isfinite(r60[i]) and r60[i] < threshold
            elif override_mode=="dma_ret60":
                structural=(np.isfinite(ma[i]) and px[i] < ma[i] and
                            np.isfinite(r60[i]) and r60[i] < threshold)
            if structural:
                target=override_target
                override_hits += 1

            if px[i]/low-1 >= target:
                armed=False
                exit_count += 1
            else:
                invested[i]=0.0

    # Signal observed at close i controls session i+1.
    exposure=np.roll(invested,1)
    exposure[0]=1.0
    daily=exposure*r
    eq=INITIAL*np.cumprod(1+daily)
    peak=np.maximum.accumulate(eq)
    dd=eq/peak-1
    return pd.Series(eq,index=p.index), {
        "shock_events":shock_count,
        "reentries":exit_count,
        "override_evaluations":override_hits,
        "max_drawdown":float(dd.min()),
        "minimum_equity":float(eq.min()),
    }


def growth_in_window(eq,start,end):
    z=eq.loc[start:end]
    if len(z)==0:
        return np.nan
    before=eq.loc[:start].iloc[-2] if len(eq.loc[:start])>=2 else INITIAL
    return float(z.iloc[-1]/before)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=dl("QQQ")
    t=dl("TQQQ")
    idx=q.index.intersection(t.index)
    q=q.reindex(idx)
    t=t.reindex(idx)
    p,ma,r60=signals(q)
    asset_returns=t["Adj Close"].squeeze().astype(float).pct_change().fillna(0)

    rows=[]
    configs=[("baseline_10pct","baseline",0.30,0.0)]
    for mode in ("ret60","dma_ret60"):
        for th in RET_THRESHOLDS:
            for target in OVERRIDE_TARGETS:
                name=f"{mode}_ret{int(th*100):+d}_target{int(target*100)}"
                configs.append((name,mode,target,th))

    # Full modern period.
    for name,mode,target,th in configs:
        eq,diag=equity(p,ma,r60,asset_returns,mode,target,th)
        years=(eq.index[-1]-eq.index[0]).days/365.25
        rows.append({
            "scope":"full_2010_2026",
            "name":name,
            "mode":mode,
            "ret60_threshold":th,
            "override_target":target if mode!="baseline" else NORMAL_TARGET,
            "final_balance":float(eq.iloc[-1]),
            "cagr":float((eq.iloc[-1]/INITIAL)**(1/years)-1),
            **diag,
        })

    # Walk-forward: parameters are frozen before each test period.
    folds=[
        ("T1","2010-01-01","2017-12-31","E1","2018-01-01","2021-12-31"),
        ("T2","2010-01-01","2021-12-31","E2","2022-01-01","2026-10-07"),
    ]
    for tr,ta,tb,te,ea,eb in folds:
        train_mask=(eq_index:=p.index)>=ta
        train_mask &= p.index<=tb
        test_mask=(p.index>=ea)&(p.index<=eb)
        for name,mode,target,th in configs:
            eq,_=equity(p,ma,r60,mode,target,th)
            trz=eq.loc[ta:tb]
            tez=eq.loc[ea:eb]
            rows.append({
                "scope":f"{tr}_to_{te}",
                "name":name,
                "mode":mode,
                "ret60_threshold":th,
                "override_target":target if mode!="baseline" else NORMAL_TARGET,
                "train_growth":float(trz.iloc[-1]/INITIAL),
                "test_growth":float(tez.iloc[-1]/trz.iloc[-1]),
                "train_end":float(trz.iloc[-1]),
                "test_end_from_5000":float(INITIAL*(tez.iloc[-1]/trz.iloc[-1])),
            })

    out=pd.DataFrame(rows)
    out.to_csv(OUT/"bear_discriminator_dma_vs_nodma_walkforward.csv",index=False)

    full=out[out.scope=="full_2010_2026"].sort_values("final_balance",ascending=False)
    print("\nFULL MODERN RESULTS")
    print(full[["name","final_balance","cagr","max_drawdown","minimum_equity","shock_events","reentries","override_evaluations"]].to_string(index=False))

    for fold in ["T1_to_E1","T2_to_E2"]:
        z=out[out.scope==fold]
        print(f"\n{fold} — TEST RANK")
        print(z.sort_values("test_growth",ascending=False)[["name","train_growth","test_growth","test_end_from_5000"]].to_string(index=False))
        print(f"\n{fold} — TRAIN RANK")
        print(z.sort_values("train_growth",ascending=False)[["name","train_growth","test_growth"]].to_string(index=False))


if __name__=="__main__":
    main()
