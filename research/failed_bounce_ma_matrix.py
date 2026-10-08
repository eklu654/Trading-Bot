"""Canonical failed-bounce MA-cross matrix research.

Decision point: QQQ has suffered a >=4.5% daily shock, formed a post-shock low,
then recovered +10% from that low.  ONLY information available on the +10%
decision day is used as a predictor.  Forward outcomes are labels.

The goal is to identify failed bounces / prolonged-bear structure without
sacrificing V-shaped recoveries.  QQQ is the signal asset; TQQQ is the traded
asset.  This is research only and does not use AI.
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
FAIL=-0.10
SUCCESS=0.20
HORIZON=252
TARGETS=(0.15,0.20,0.30)

PAIRS=((10,20),(10,50),(20,50),(20,100),(20,200),(50,100),(50,200),(100,200))
CROSS_WINDOWS=(5,10,20,30)

def dl(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def features(p):
    sma={n:p.rolling(n).mean() for n in (10,20,50,100,200)}
    f={}
    for a,b in PAIRS:
        f[f"state_{a}_{b}"]=sma[a]/sma[b]-1
        bull=(sma[a]>sma[b]).astype(int)
        d=bull.diff()
        for w in CROSS_WINDOWS:
            f[f"bull_cross_{a}_{b}_{w}"]=(d.eq(1).rolling(w).max().fillna(0)>0).astype(int)
            f[f"bear_cross_{a}_{b}_{w}"]=(d.eq(-1).rolling(w).max().fillna(0)>0).astype(int)
        # Days since latest cross; capped naturally by available history.
        cross_idx=pd.Series(np.arange(len(p)),index=p.index).where(d.ne(0))
        f[f"days_since_cross_{a}_{b}"]=pd.Series(np.arange(len(p)),index=p.index).subtract(cross_idx.ffill())
        f[f"slope_fast_{a}_{b}"]=sma[a]/sma[a].shift(20)-1
        f[f"slope_slow_{a}_{b}"]=sma[b]/sma[b].shift(20)-1
    # Full hierarchy: the short/medium structure has repaired in order.
    f["hierarchy_bull"]=(
        (sma[10]>sma[20])&(sma[20]>sma[50])&
        (sma[50]>sma[100])&(sma[100]>sma[200])
    ).astype(int)
    f["hierarchy_bear"]=(
        (sma[10]<sma[20])&(sma[20]<sma[50])&
        (sma[50]<sma[100])&(sma[100]<sma[200])
    ).astype(int)
    f["bull_count"]=sum((sma[a]>sma[b]).astype(int) for a,b in PAIRS)
    f["bear_count"]=sum((sma[a]<sma[b]).astype(int) for a,b in PAIRS)
    f["ret20"]=p/p.shift(20)-1
    f["ret60"]=p/p.shift(60)-1
    f["ret120"]=p/p.shift(120)-1
    ema12=p.ewm(span=12,adjust=False).mean(); ema26=p.ewm(span=26,adjust=False).mean()
    macd=ema12-ema26; sig=macd.ewm(span=9,adjust=False).mean()
    f["macd"]=macd; f["macd_signal"]=sig; f["macd_hist"]=macd-sig
    f["macd_bull"]=((macd>sig)&(macd.shift(1)<=sig.shift(1))).astype(int)
    f["macd_bear"]=((macd<sig)&(macd.shift(1)>=sig.shift(1))).astype(int)
    mid=p.rolling(20).mean(); sd=p.rolling(20).std()
    f["bb_pos"]=(p-(mid-2*sd))/(4*sd)
    f["bb_above_mid"]=(p>mid).astype(int)
    f["donch_pos"]=(p-p.rolling(20).min())/(p.rolling(20).max()-p.rolling(20).min())
    atr=(p-p.shift(1)).abs().rolling(20).mean(); kc_mid=p.ewm(span=20,adjust=False).mean()
    f["kc_pos"]=(p-(kc_mid-2*atr))/(4*atr)
    f["vol20"]=p.pct_change().rolling(20).std()*np.sqrt(252)
    return pd.DataFrame(f,index=p.index)

def extra_features(p):
    r=p.pct_change()
    ema12=p.ewm(span=12,adjust=False).mean()
    ema26=p.ewm(span=26,adjust=False).mean()
    macd=ema12-ema26
    sig=macd.ewm(span=9,adjust=False).mean()
    mid=p.rolling(20).mean()
    sd=p.rolling(20).std()
    bb=(p-(mid-2*sd))/(4*sd)
    dc_hi=p.rolling(20).max()
    dc_lo=p.rolling(20).min()
    dc=(p-dc_lo)/(dc_hi-dc_lo)
    atr=(p.diff().abs()).rolling(20).mean()
    kc_mid=mid
    kc=(p-(kc_mid-2*atr))/(4*atr)
    return pd.DataFrame({
        "macd":macd,"macd_signal":sig,"macd_hist":macd-sig,
        "macd_bull":(macd>sig).astype(int),
        "macd_cross_bull":((macd>sig)&(macd.shift(1)<=sig.shift(1))).astype(int),
        "macd_cross_bear":((macd<sig)&(macd.shift(1)>=sig.shift(1))).astype(int),
        "bb_position":bb,"donchian_position":dc,"keltner_position":kc,
        "ret5":p/p.shift(5)-1,"ret10":p/p.shift(10)-1,
        "ret60_extra":p/p.shift(60)-1,
        "ret120":p/p.shift(120)-1,
    },index=p.index)

def canonical_events(p):
    r=p.pct_change().fillna(0).to_numpy()
    px=p.to_numpy()
    armed=False; low=np.nan; low_i=None
    events=[]
    for i in range(1,len(p)):
        if not armed and r[i] <= SHOCK:
            armed=True; low=px[i]; low_i=i
        if armed:
            if px[i] < low:
                low=px[i]; low_i=i
            gain=px[i]/low-1
            if gain >= NORMAL:
                events.append({"decision_i":i,"decision_date":p.index[i].date(),
                                "low_i":low_i,"low_date":p.index[low_i].date(),
                                "speed_days":i-low_i})
                armed=False; low=np.nan; low_i=None
    return events

def label_event(p,e):
    i=e["decision_i"]; base=float(p.iloc[i])
    end=min(len(p)-1,i+HORIZON)
    future=p.iloc[i+1:end+1].to_numpy()/base-1
    hit_fail=np.where(future<=FAIL)[0]
    hit_success=np.where(future>=SUCCESS)[0]
    if len(hit_fail)==0 and len(hit_success)==0:
        return "censored",None,None
    fi=int(hit_fail[0]) if len(hit_fail) else 10**9
    si=int(hit_success[0]) if len(hit_success) else 10**9
    if fi < si:
        return "failed",fi+1,float(future[fi])
    return "successful",si+1,float(future[si])

def event_frame(p,f):
    rows=[]
    for e in canonical_events(p):
        lab,days,out=label_event(p,e)
        i=e["decision_i"]
        row={**e,"label":lab,"label_days":days,"label_return":out}
        for k in f.columns:
            v=f.iloc[i][k]
            row[k]=float(v) if np.isfinite(v) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)

def rule_defs():
    rules={"hierarchy_bull":lambda r:r.hierarchy_bull==1,
           "hierarchy_bear":lambda r:r.hierarchy_bear==1,
           "bull_count_ge6":lambda r:r.bull_count>=6,
           "bull_count_ge4":lambda r:r.bull_count>=4,
           "bear_count_ge6":lambda r:r.bear_count>=6,
           "bear_count_ge4":lambda r:r.bear_count>=4}
    for a,b in PAIRS:
        rules[f"bull_{a}_{b}"]=lambda r,a=a,b=b:getattr(r,f"state_{a}_{b}")>0
        rules[f"bear_{a}_{b}"]=lambda r,a=a,b=b:getattr(r,f"state_{a}_{b}")<0
        for w in CROSS_WINDOWS:
            rules[f"bull_cross_{a}_{b}_{w}"]=lambda r,a=a,b=b,w=w:getattr(r,f"bull_cross_{a}_{b}_{w}")==1
            rules[f"bear_cross_{a}_{b}_{w}"]=lambda r,a=a,b=b,w=w:getattr(r,f"bear_cross_{a}_{b}_{w}")==1
        rules[f"fast_up_slow_down_{a}_{b}"]=lambda r,a=a,b=b:getattr(r,f"slope_fast_{a}_{b}")>0 and getattr(r,f"slope_slow_{a}_{b}")<0
    rules["all_pairs_bull"]=lambda r: r.bull_count==len(PAIRS)
    rules["all_pairs_bear"]=lambda r: r.bear_count==len(PAIRS)
    rules["short_repaired_long_bear"]=lambda r: (
        r.state_10_20>0 and r.state_20_50>0 and r.state_50_100<0 and r.state_100_200<0)
    rules["medium_repaired_long_bear"]=lambda r: (
        r.state_20_50>0 and r.state_50_100>0 and r.state_100_200<0)
    rules["short_bull_long_bear"]=lambda r: (
        r.state_10_20>0 and r.state_20_50>0 and r.state_50_100<0 and r.state_100_200<0)
    return rules

def signal_stats(ev):
    labeled=ev[ev.label!="censored"].copy()
    total=len(labeled)
    base_rate=(labeled.label=="failed").mean() if total else np.nan
    rows=[]
    for name,fn in rule_defs().items():
        flag=labeled.apply(fn,axis=1)
        n=int(flag.sum())
        failed=int(((labeled.label=="failed")&flag).sum())
        success=int(((labeled.label=="successful")&flag).sum())
        rows.append({"rule":name,"events_flagged":n,"failed_flagged":failed,
                      "success_flagged":success,
                      "failed_rate_when_flagged":failed/n if n else np.nan,
                      "failed_rate_when_not_flagged":
                          int(((labeled.label=="failed")&~flag).sum())/int((~flag).sum())
                          if int((~flag).sum()) else np.nan,
                      "base_failed_rate":base_rate})
    return pd.DataFrame(rows).sort_values(["failed_rate_when_flagged","events_flagged"],
                                          ascending=[False,False])

def equity(p,ar,rule_fn=None,target=NORMAL):
    qret=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy(); asset=ar.to_numpy()
    f=features(p)
    invested=np.ones(len(p)); armed=False; low=np.nan; required=NORMAL
    for i in range(1,len(p)):
        if not armed and qret[i] <= SHOCK:
            armed=True; low=px[i]
        if armed:
            low=min(low,px[i]); gain=px[i]/low-1
            if gain>=NORMAL and required==NORMAL:
                if rule_fn is not None:
                    row=f.iloc[i]
                    try: flag=bool(rule_fn(row)) and np.isfinite(row.to_numpy(dtype=float)).all()
                    except Exception: flag=False
                    if flag: required=target
            if gain>=required:
                armed=False; low=np.nan; required=NORMAL
            else:
                invested[i]=0.0
    exposure=np.roll(invested,1); exposure[0]=1
    eq=INITIAL*np.cumprod(1+exposure*asset)
    return eq

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=dl("QQQ"); t=dl("TQQQ"); idx=q.index.intersection(t.index)
    p=q.reindex(idx)["Close"].squeeze().astype(float)
    tp=t.reindex(idx)["Close"].squeeze().astype(float)
    ar=tp.pct_change().fillna(0)

    f=pd.concat([features(p),extra_features(p)],axis=1)
    ev=event_frame(p,f)
    ev.to_csv(OUT/"canonical_failed_bounce_ma_events.csv",index=False)
    stats=signal_stats(ev)
    stats.to_csv(OUT/"canonical_failed_bounce_ma_signal_stats.csv",index=False)

    print("\nCANONICAL EVENTS:",len(ev))
    print(ev[["decision_date","low_date","speed_days","label","label_days","label_return"]].to_string(index=False))
    print("\nEVENT FEATURE SNAPSHOT")
    cols=["decision_date","low_date","speed_days","label","ret20","ret60","ret120","macd","macd_signal","macd_hist","macd_bull","macd_bear","bb_pos","donch_pos","kc_pos","vol20","bull_count","bear_count","hierarchy_bull","hierarchy_bear","state_50_100","state_100_200"]
    print(ev[cols].to_string(index=False))
    print("\n2022 FAILED-BOUNCE FEATURE SNAPSHOT")
    print(ev[ev.label=="failed"].T.to_string())
    print("\nSIGNAL SEPARATION")
    print(stats.to_string(index=False))

    rules=rule_defs()
    configs=[("baseline",None,NORMAL)]
    for n,fn in rules.items():
        for target in TARGETS:
            configs.append((f"{n}_target{int(target*100)}",fn,target))

    rows=[]
    bh=INITIAL*np.cumprod(1+ar.to_numpy())
    for name,fn,target in configs:
        eq=equity(p,ar,fn,target)
        years=(p.index[-1]-p.index[0]).days/365.25
        rows.append({"name":name,"final_balance":float(eq[-1]),
                     "cagr":float((eq[-1]/INITIAL)**(1/years)-1)})
    full=pd.DataFrame(rows).sort_values("final_balance",ascending=False)
    full.to_csv(OUT/"canonical_failed_bounce_ma_strategy_full.csv",index=False)

    folds=[
        ("F1","2010-01-01","2017-12-31","2018-01-01","2021-12-31"),
        ("F2","2010-01-01","2021-12-31","2022-01-01","2026-10-07")]
    wf=[]
    for fold,ta,tb,ea,eb in folds:
        scored=[]
        for name,fn,target in configs:
            eq=equity(p,ar,fn,target)
            tr=pd.Series(eq,index=p.index).loc[ta:tb]
            te=pd.Series(eq,index=p.index).loc[ea:eb]
            tg=tr.iloc[-1]/INITIAL; eg=te.iloc[-1]/tr.iloc[-1]
            scored.append((tg,name,fn,target,eg))
        best=max(scored,key=lambda x:x[0])
        wf.append({"fold":fold,"selected":best[1],"train_growth":best[0],
                    "test_growth":best[4]})
        print(f"\n{fold}: selected {best[1]} | train {best[0]:.6f} | test {best[4]:.6f}")
    pd.DataFrame(wf).to_csv(OUT/"canonical_failed_bounce_ma_walkforward_selected.csv",index=False)

    years=(p.index[-1]-p.index[0]).days/365.25
    print("\nTOP FULL STRATEGIES")
    print(full.head(20).to_string(index=False))
    print(f"\nTQQQ BUY&HOLD: {bh[-1]:,.2f}")
    print("\nWALK-FORWARD SELECTED")
    print(pd.DataFrame(wf).to_string(index=False))

if __name__=="__main__":
    main()
