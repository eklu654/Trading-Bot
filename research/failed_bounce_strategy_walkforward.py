"""Causal failed-bounce classifier integration test.

QQQ supplies all signals; TQQQ supplies traded returns.  At the first
+10% QQQ recovery after a >=4.5% daily shock, a simple classifier can
either allow immediate TQQQ re-entry or delay it to 15/20/30%.

Classifier rules are fixed ex ante and are evaluated walk-forward.
A separate broad 3% shock event sample is used only as a training-data
diagnostic; the trading strategy itself remains the canonical 4.5% shock.
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
NORMAL=0.10
TARGETS=(0.15,0.20,0.25,0.30,0.40)
SPEED_THRESHOLDS=(10,12,15,18,20,22,25,30)

def dl(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def feature_arrays(p):
    sma20=p.rolling(20).mean()
    sma50=p.rolling(50).mean()
    sma100=p.rolling(100).mean()
    sma200=p.rolling(200).mean()
    ema12=p.ewm(span=12,adjust=False).mean()
    ema26=p.ewm(span=26,adjust=False).mean()
    macd=ema12-ema26
    sig=macd.ewm(span=9,adjust=False).mean()
    hist=macd-sig
    cross=(macd>sig).astype(int).diff()
    bbstd=p.rolling(20).std()
    bb=(p-(sma20-2*bbstd))/(4*bbstd)
    hi=p.rolling(20).max()
    lo=p.rolling(20).min()
    don=(p-lo)/(hi-lo)
    tr=p.diff().abs()
    atr=tr.rolling(14).mean()
    kmid=p.ewm(span=20,adjust=False).mean()
    kel=(p-(kmid-2*atr))/(4*atr)
    return {
        "ret60":p/p.shift(60)-1,
        "ma20_50":sma20/sma50-1,
        "ma50_100":sma50/sma100-1,
        "ma100_200":sma100/sma200-1,
        "macd_hist":hist,
        "macd_bull_cross":(cross==1).astype(int),
        "bb_pct":bb,
        "donchian_pct":don,
        "keltner_pct":kel,
    }

def rule_flag(name, f, days):
    # These are deliberately simple, interpretable hypotheses.
    if name.startswith("slow_"):
        threshold=int(name.split("_")[1])
        return days>=threshold
    if name=="slow15":
        return days>=15
    if name=="slow20":
        return days>=20
    if name=="slow20_ma50":
        return days>=20 and f["ma50_100"]<0
    if name=="slow20_ma100":
        return days>=20 and f["ma100_200"]<0
    if name=="slow20_channels":
        return days>=20 and f["donchian_pct"]>=0.99 and f["keltner_pct"]>1.0
    if name=="slow20_no_macd_cross":
        return days>=20 and f["macd_bull_cross"]==0
    if name=="slow20_structural":
        return (days>=20 and f["ma50_100"]<0 and
                f["ma100_200"]<0 and f["macd_bull_cross"]==0)
    if name=="slow20_structural_or_channels":
        structural=(f["ma50_100"]<0 and f["ma100_200"]<0 and f["macd_bull_cross"]==0)
        channels=(f["donchian_pct"]>=0.99 and f["keltner_pct"]>1.0)
        return days>=20 and (structural or channels)
    if name=="slow15_60neg":
        return days>=15 and f["ret60"]<0
    if name=="slow15_60neg_ma":
        return days>=15 and f["ret60"]<0 and f["ma50_100"]<0
    if name=="slow15_60neg_macd":
        return days>=15 and f["ret60"]<0 and f["macd_bull_cross"]==0
    if name=="slow15_60neg_structure":
        return days>=15 and f["ret60"]<0 and f["ma50_100"]<0 and f["ma100_200"]<0
    if name=="slow15_60neg_structure_macd":
        return (days>=15 and f["ret60"]<0 and f["ma50_100"]<0 and
                f["ma100_200"]<0 and f["macd_bull_cross"]==0)
    if name=="slow15_60neg_channels":
        return days>=15 and f["ret60"]<0 and f["donchian_pct"]>=0.99 and f["keltner_pct"]>1.0
    return False

RULES=tuple([f"slow_{x}" for x in SPEED_THRESHOLDS])+("slow20_ma50","slow20_ma100",
       "slow20_channels","slow20_no_macd_cross","slow20_structural",
       "slow20_structural_or_channels","slow15_60neg","slow15_60neg_ma",
       "slow15_60neg_macd","slow15_60neg_structure",
       "slow15_60neg_structure_macd","slow15_60neg_channels")

def equity(p,asset_returns,rule=None,target=NORMAL):
    qret=p.pct_change().fillna(0).to_numpy()
    px=p.to_numpy()
    ar=asset_returns.to_numpy()
    f={k:v.to_numpy() for k,v in feature_arrays(p).items()}
    invested=np.ones(len(p))
    armed=False
    low=np.nan
    low_i=None
    required_target=NORMAL
    for i in range(1,len(p)):
        if not armed and qret[i]<=SHOCK:
            armed=True
            low=px[i]
            low_i=i
        if armed:
            if px[i]<low:
                low=px[i]
                low_i=i
            gain=px[i]/low-1
            if gain>=NORMAL and required_target==NORMAL:
                flagged=False
                if rule is not None:
                    days=i-low_i
                    vals={k:f[k][i] for k in f}
                    if all(np.isfinite(v) for v in vals.values()):
                        flagged=rule_flag(rule,vals,days)
                required_target=target if flagged else NORMAL
            required=required_target
            if gain>=required:
                armed=False
                low=np.nan
                low_i=None
                required_target=NORMAL
            else:
                invested[i]=0.0
    exposure=np.roll(invested,1)
    exposure[0]=1.0
    eq=INITIAL*np.cumprod(1+exposure*ar)
    peak=np.maximum.accumulate(eq)
    dd=eq/peak-1
    return pd.Series(eq,index=p.index),float(dd.min())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=dl("QQQ"); t=dl("TQQQ")
    idx=q.index.intersection(t.index)
    q=q.reindex(idx); t=t.reindex(idx)
    p=q["Close"].squeeze().astype(float)
    tp=t["Close"].squeeze().astype(float)
    ar=tp.pct_change().fillna(0)
    bh=INITIAL*np.cumprod(1+ar.to_numpy())

    # Full-period comparison.
    rows=[]
    # canonical-event diagnostic: print every 4.5% shock -> 10% recovery and speed
    qret=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy(); armed=False; low=np.nan; low_i=None
    canonical=[]
    for i in range(1,len(p)):
        if not armed and qret[i] <= SHOCK:
            armed=True; low=px[i]; low_i=i
        if armed:
            if px[i]<low: low=px[i]; low_i=i
            if px[i]/low-1>=NORMAL:
                canonical.append((str(p.index[i].date()), i-low_i, px[i]/low-1))
                armed=False; low=np.nan; low_i=None
    print("\nCANONICAL 4.5% SHOCK -> 10% RECOVERY EVENTS")
    print(canonical)
    configs=[("baseline_10pct",None,NORMAL)]
    for rule in RULES:
        for target in TARGETS:
            configs.append((f"{rule}_target{int(target*100)}",rule,target))
    for name,rule,target in configs:
        eq,dd=equity(p,ar,rule,target)
        years=(eq.index[-1]-eq.index[0]).days/365.25
        rows.append({"scope":"full_2010_2026","name":name,
                     "rule":rule,"target":target,
                     "final_balance":eq.iloc[-1],
                     "cagr":(eq.iloc[-1]/INITIAL)**(1/years)-1,
                     "max_drawdown":dd})
    out=pd.DataFrame(rows)

    # Strict chronological selection: select one rule/target on training,
    # then evaluate that frozen choice on the subsequent test period.
    folds=[
        ("F1","2010-01-01","2017-12-31","2018-01-01","2021-12-31"),
        ("F2","2010-01-01","2021-12-31","2022-01-01","2026-10-07"),
    ]
    wf=[]
    for fold,ta,tb,ea,eb in folds:
        train=[]
        test=[]
        for name,rule,target in configs:
            eq,_=equity(p,ar,rule,target)
            tr=eq.loc[ta:tb]
            te=eq.loc[ea:eb]
            train_growth=tr.iloc[-1]/INITIAL
            test_growth=te.iloc[-1]/tr.iloc[-1]
            train.append((train_growth,name,rule,target,test_growth))
            test.append((name,rule,target,train_growth,test_growth))
        train_sorted=sorted(train,key=lambda x:x[0],reverse=True)
        best=train_sorted[0]
        for name,rule,target,tg,eg in test:
            wf.append({"fold":fold,"name":name,"rule":rule,"target":target,
                       "train_growth":tg,"test_growth":eg,
                       "selected":int(name==best[1])})
        print(f"\n{fold} selected on train: {best[1]} | train growth={best[0]:.6f} | test growth={best[4]:.6f}")
        print(pd.DataFrame(test,columns=["name","rule","target","train_growth","test_growth"])
              .sort_values("test_growth",ascending=False).head(10).to_string(index=False))
    wfdf=pd.DataFrame(wf)

    out.to_csv(OUT/"failed_bounce_strategy_full.csv",index=False)
    wfdf.to_csv(OUT/"failed_bounce_strategy_walkforward.csv",index=False)

    print(f"\nSANITY TQQQ BUY&HOLD: {bh[-1]:,.2f}")
    print("\nFULL-PERIOD RANKING")
    print(out.sort_values("final_balance",ascending=False).head(15).to_string(index=False))
    print("\nWALK-FORWARD SELECTED RESULTS")
    print(wfdf[wfdf.selected==1].to_string(index=False))

if __name__=="__main__":
    main()
