"""Crash-path classification using the prior 60-day structural-instability layer.

Causal research:
- Signal source: QQQ adjusted close.
- Execution: next session open.
- Entry shock: QQQ daily return <= -4.5%.
- Default re-entry: QQQ recovers 10% from post-shock low.
- Structural override: if, on the day a recovery target is reached, QQQ is
  below 100-DMA and its 60-day return is negative, use a slower recovery target.
- No same-day execution and no future-path information in the signal.

This tests whether the old three-layer medium-term signal can protect the
10% fast-recovery rule specifically against failed/V-shaped-vs-secular-bear
confusion, rather than replacing the fast recovery architecture.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="1999-03-10"
END="2026-10-08"
SHOCK=-0.045
DEFAULT_RECOVERY=0.10
SLOW_TARGETS=(0.15,0.20,0.30,0.40)
SIXTY_THRESHOLDS=(0.0,-0.05,-0.10)
DMA=100

def download(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex):
        x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def frame():
    q=download("QQQ")
    t=download("TQQQ",start="2010-01-01")
    v=download("^VIX")[["close"]].rename(columns={"close":"vix"})
    q=q.join(v,how="left").join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="left")
    q.vix=q.vix.ffill()
    q["dma100"]=q.adj_close.rolling(DMA).mean()
    q["ret60"]=q.adj_close/q.adj_close.shift(60)-1
    q["q_daily"]=q.adj_close.pct_change()
    q["t_adj_open"]=q.tqqq_open*q.tqqq_adj_close/q.tqqq_close
    q["t_on"]=(q.t_adj_open/q.tqqq_adj_close.shift(1)-1).fillna(0)
    q["t_in"]=(q.tqqq_adj_close/q.t_adj_open-1).fillna(0)
    return q

def backtest(x, override_target=None, sixty_thr=0.0, require_below_dma=True):
    """Return equity and event ledger. All decisions use current close for next open."""
    pos=False
    low=np.nan
    target=DEFAULT_RECOVERY
    daily=np.zeros(len(x))
    events=[]
    for i,(dt,row) in enumerate(x.iterrows()):
        shock=bool(np.isfinite(row.q_daily) and row.q_daily<=SHOCK)
        if not pos:
            if shock:
                pos=False
                low=float(row.adj_close)
                target=DEFAULT_RECOVERY
                events.append({"date":dt,"event":"SHOCK","price":row.adj_close,
                               "target":target,"ret60":row.ret60,"dma_gap":row.adj_close/row.dma100-1})
        else:
            daily[i]=row.t_in
        if not pos:
            # cash for the day; shock day is excluded from TQQQ return.
            if np.isfinite(low):
                low=min(low,float(row.adj_close))
                recovery=float(row.adj_close)/low-1
                if recovery>=target:
                    override=False
                    if override_target is not None:
                        below=bool(np.isfinite(row.dma100) and row.adj_close<row.dma100)
                        structural=bool(np.isfinite(row.ret60) and row.ret60<sixty_thr)
                        override=(below if require_below_dma else True) and structural
                    chosen=override_target if override else DEFAULT_RECOVERY
                    # If the default target was reached but structural instability
                    # is present, do not enter yet; arm the slower target.
                    if override and chosen>DEFAULT_RECOVERY:
                        target=chosen
                        if recovery<target:
                            events.append({"date":dt,"event":"DEFER_REENTRY","price":row.adj_close,
                                           "target":target,"ret60":row.ret60,
                                           "dma_gap":row.adj_close/row.dma100-1,
                                           "recovery":recovery})
                        else:
                            pos=True; low=np.nan; target=DEFAULT_RECOVERY
                            events.append({"date":dt,"event":"REENTRY","price":row.adj_close,
                                           "target":chosen,"ret60":row.ret60,
                                           "dma_gap":row.adj_close/row.dma100-1,
                                           "recovery":recovery})
                    elif recovery>=target:
                        pos=True; low=np.nan; target=DEFAULT_RECOVERY
                        events.append({"date":dt,"event":"REENTRY","price":row.adj_close,
                                       "target":target,"ret60":row.ret60,
                                       "dma_gap":row.adj_close/row.dma100-1,
                                       "recovery":recovery})
        # If already invested, a new shock starts a new defensive episode only
        # after today's TQQQ return; next iteration handles the new cash state.
        if pos and shock:
            pos=False
            low=float(row.adj_close)
            target=DEFAULT_RECOVERY
            events.append({"date":dt,"event":"SHOCK_EXIT","price":row.adj_close,
                           "target":target,"ret60":row.ret60,
                           "dma_gap":row.adj_close/row.dma100-1})
    # Convert signal state into next-open execution correctly: daily return belongs
    # to prior day's close signal. Rebuild using state-after-close.
    # The loop above intentionally records state changes; replay from events.
    sig=np.ones(len(x))
    state=True
    low=np.nan
    target=DEFAULT_RECOVERY
    for i,row in enumerate(x.itertuples()):
        if i==0:
            sig[i]=1.0; continue
        # state at prior close controls today's open-to-close.
        prev=x.iloc[i-1]
        if state:
            if prev.q_daily<=SHOCK:
                state=False; low=float(prev.adj_close); target=DEFAULT_RECOVERY
        else:
            low=min(low,float(prev.adj_close))
            recovery=float(prev.adj_close)/low-1
            if recovery>=DEFAULT_RECOVERY:
                below=np.isfinite(prev.dma100) and prev.adj_close<prev.dma100
                structural=np.isfinite(prev.ret60) and prev.ret60<sixty_thr
                if override_target is None or not ((below if require_below_dma else True) and structural):
                    state=True; low=np.nan; target=DEFAULT_RECOVERY
                elif recovery>=override_target:
                    state=True; low=np.nan; target=DEFAULT_RECOVERY
        sig[i]=1.0 if state else 0.0
        if state and prev.q_daily<=SHOCK:
            state=False; low=float(prev.adj_close); target=DEFAULT_RECOVERY; sig[i]=0.0
    on=x.t_on.to_numpy(); inn=x.t_in.to_numpy()
    daily=np.where(sig>0,inn,0.0)
    eq=INITIAL*np.cumprod(1+daily)
    dd=eq/np.maximum.accumulate(eq)-1
    return sig,eq,dd,pd.DataFrame(events)

def event_classification(x):
    # For each shock, inspect only the path after the shock to label what the
    # 10% re-entry day looked like and what happened afterward.
    rows=[]
    shock_idx=np.flatnonzero(x.q_daily.to_numpy()<=SHOCK)
    for n,i in enumerate(shock_idx):
        if i+1>=len(x): continue
        end=shock_idx[n+1] if n+1<len(shock_idx) else len(x)
        z=x.iloc[i:end]
        low=float(z.adj_close.cummin().iloc[0])
        lows=z.adj_close.cummin()
        rec=z.adj_close/low-1
        hit=np.flatnonzero(rec.to_numpy()>=DEFAULT_RECOVERY)
        if len(hit)==0:
            first=None
            post10=np.nan
        else:
            j=int(hit[0]); first=z.iloc[j]
            post=z.iloc[j:]
            post10=float(post.adj_close.min()/first.adj_close-1)
        rows.append({
            "shock_date":x.index[i].date(),
            "shock_return":float(x.q_daily.iloc[i]),
            "pre_shock_price":float(x.adj_close.iloc[i-1]) if i>0 else np.nan,
            "shock_price":float(x.adj_close.iloc[i]),
            "lowest_price_before_next_shock":float(z.adj_close.min()),
            "max_rebound_before_next_shock":float(rec.max()),
            "first_10pct_recovery_date":None if first is None else first.name.date(),
            "first_10pct_ret60":np.nan if first is None else float(first.ret60),
            "first_10pct_below_100dma":np.nan if first is None else bool(first.adj_close<first.dma100),
            "first_10pct_dma_gap":np.nan if first is None else float(first.adj_close/first.dma100-1),
            "post_10pct_min_return":post10,
            "event_type":("no_10pct_recovery" if first is None else
                          "failed_bounce" if post10<=-0.15 else "continuing_recovery")
        })
    return pd.DataFrame(rows)

def metrics(eq,dd,start,end):
    z=pd.Series(eq,index=x.index).loc[start:end]
    if len(z)<2: return {}
    years=(z.index[-1]-z.index[0]).days/365.25
    return {"final":float(z.iloc[-1]),"cagr":float((z.iloc[-1]/z.iloc[0])**(1/years)-1) if years>0 else np.nan,
            "max_dd":float((z/z.cummax()-1).min())}

def main():
    global x
    OUT.mkdir(parents=True,exist_ok=True)
    x=frame()
    events=event_classification(x)
    events.to_csv(OUT/"crash_path_event_classification.csv",index=False)
    rows=[]
    variants=[("control_10pct",None,0.0,True)]
    for target in SLOW_TARGETS:
        for thr in SIXTY_THRESHOLDS:
            variants.append((f"override_{int(target*100)}pct_ret60_{int(thr*100)}",target,thr,True))
            variants.append((f"override_{int(target*100)}pct_ret60_{int(thr*100)}_no_dma",target,thr,False))
    for name,target,thr,below in variants:
        sig,eq,dd,_=backtest(x,target,thr,below)
        years=(x.index[-1]-x.index[0]).days/365.25
        rows.append({"variant":name,"final":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
                     "max_dd":float(dd.min()),"avg_exposure":float(sig.mean()),
                     "defensive_days":int((sig<1).sum())})
        for a,b,label in [("2018-01-01","2021-12-31","test_2018_2021"),("2022-01-01","2026-10-07","test_2022_2026")]:
            m=metrics(eq,dd,a,b)
            rows[-1].update({f"{label}_{k}":v for k,v in m.items()})
    pd.DataFrame(rows).to_csv(OUT/"crash_path_override_matrix.csv",index=False)
    # Event summary: how often the old 60d structural condition would have
    # overridden the fast 10% entry, and how often those events subsequently
    # experienced a material failed bounce.
    valid=events[events.first_10pct_recovery_date.notna()].copy()
    valid["override_signal"]=(valid.first_10pct_below_100dma.astype(bool) & (valid.first_10pct_ret60<0))
    valid["failed_15pct"]=(valid.post_10pct_min_return<=-0.15)
    summary=valid.groupby("override_signal").agg(events=("shock_date","count"),
        failed_bounces=("failed_15pct","sum"),mean_post10_min=("post_10pct_min_return","mean"),
        median_post10_min=("post_10pct_min_return","median")).reset_index()
    summary.to_csv(OUT/"crash_path_override_event_summary.csv",index=False)
    print("\nSTRATEGY MATRIX\n",pd.DataFrame(rows).to_string(index=False))
    print("\nEVENT CLASSIFICATION\n",events.to_string(index=False))
    print("\nOVERRIDE EVENT SUMMARY\n",summary.to_string(index=False))

if __name__=="__main__": main()

# CI trigger: crash-path structural override research.
