"""State-transition ablation for the canonical + structural matrix.

Fixed representative parameters are held constant to isolate the sticky hard
override / sticky structural state behavior. These are diagnostic ablations,
not a new parameter search or a candidate-selection exercise.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns
from tqqq_canonical_same_input_reconciliation import INITIAL, make_frozen_input, build_events_and_signal

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
START,END="1999-03-10","2026-10-08"
# Frozen representative setting from prior combined-grid best terminal-balance row.
SD,FD,RT,DT,VT,EXP=150,100,-0.20,-0.20,30.0,0.25


def download(symbol,start=START):
    x=yf.download(symbol,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def qqq_features():
    q=download("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    q=q.dropna(subset=["open","close","adj_close"])
    for d in (FD,SD): q[f"dma{d}"]=q.adj_close.rolling(d,min_periods=d).mean()
    q["ret63"]=q.adj_close/q.adj_close.shift(63)-1
    q["dd252"]=q.adj_close/q.adj_close.rolling(252,min_periods=252).max()-1
    v=download("^VIX")[["Close"]].rename(columns={"Close":"vix"})
    q=q.join(v,how="left"); q["vix"]=q.vix.ffill()
    return q.dropna(subset=["vix"])


def make_overlay(q,mode):
    ma=q[f"dma{SD}"].to_numpy(); fast=q[f"dma{FD}"].to_numpy()
    px=q.adj_close.to_numpy(); r=q.ret63.to_numpy(); d=q.dd252.to_numpy(); v=q.vix.to_numpy()
    armed=False; hard=False; out=[]
    for i in range(len(q)):
        if not np.isfinite(ma[i]) or not np.isfinite(fast[i]):
            out.append(1.0); continue
        structural=(px[i]<ma[i] and fast[i]<ma[i])
        shock=(px[i]<fast[i] and ((np.isfinite(r[i]) and r[i]<=RT) or
                                  (np.isfinite(d[i]) and d[i]<=DT) or v[i]>=VT))
        if mode=="sticky_original":
            if not armed and (structural or shock): armed=True; hard=bool(shock)
            elif armed:
                if px[i]>=ma[i]: armed=hard=False
                elif shock: hard=True
            target=0.0 if hard else (EXP if armed else 1.0)
        elif mode=="hard_nonsticky":
            # Structural state remains sticky; hard 0% override applies only
            # while the fast-shock condition is true today.
            if not armed and (structural or shock): armed=True
            elif armed and px[i]>=ma[i]: armed=False
            target=0.0 if shock else (EXP if armed else 1.0)
        elif mode=="daily_nonsticky":
            # No state carry: only today's observed structural conjunction or
            # today's fast-shock condition can reduce exposure.
            target=0.0 if shock else (EXP if structural else 1.0)
        else: raise ValueError(mode)
        out.append(target)
    return np.asarray(out,float)


def evaluate(source,name,signal,dates,overnight,intraday):
    daily=next_open_daily_returns(signal,overnight,intraday)
    eq=INITIAL*np.cumprod(1+daily); dd=eq/np.maximum.accumulate(eq)-1
    years=(dates[-1]-dates[0]).days/365.25
    roll=pd.Series(np.log1p(daily)).rolling(252,min_periods=252).sum().dropna()
    row={"source":source,"strategy":name,"start":dates[0].date().isoformat(),
         "end":dates[-1].date().isoformat(),"rows":len(dates),"initial_balance":INITIAL,
         "final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
         "max_drawdown":float(dd.min()),
         "worst_rolling_252_session_return":float(np.expm1(roll.min())) if len(roll) else np.nan,
         "mean_target_exposure":float(np.mean(signal)),"defensive_sessions":int(np.sum(signal<1)),
         "exposure_changes":int(np.sum(np.abs(np.diff(signal,prepend=signal[0]))>1e-12))}
    for label,a,b in [("dotcom","2000-01-01","2002-12-31"),("gfc","2007-10-01","2009-12-31"),
                      ("covid","2020-02-19","2020-07-31"),("inflation_2022","2022-01-03","2022-12-30")]:
        mask=(dates>=a)&(dates<=b)
        if mask.any():
            ix=np.flatnonzero(mask); local=eq[mask]
            prev=eq[ix[0]-1] if ix[0] else INITIAL
            row[label+"_return"]=float(local[-1]/prev-1)
            row[label+"_max_dd"]=float((local/np.maximum.accumulate(local)-1).min())
    return row


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=qqq_features()
    q["adj_open"]=q.open*q.adj_close/q.close
    # Keep prior matrix proxy convention only for diagnostic comparability.
    q["on3"]=((1+3*(q.adj_open/q.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    q["in3"]=((1+3*(q.adj_close/q.adj_open-1)).clip(lower=0)-1).fillna(0)
    events,b0=build_events_and_signal(q.adj_close)
    rows=[]
    for name,overlay in [("B0_canonical",np.ones(len(q))),
                         ("sticky_original",make_overlay(q,"sticky_original")),
                         ("hard_nonsticky",make_overlay(q,"hard_nonsticky")),
                         ("daily_nonsticky",make_overlay(q,"daily_nonsticky"))]:
        sig=np.minimum(b0.astype(float),overlay)
        assert np.all(sig<=b0+1e-12)
        rows.append(evaluate("synthetic_qqq_3x",name,sig,q.index,q.on3.to_numpy(),q.in3.to_numpy()))
    x,path=make_frozen_input()
    feat=q.reindex(q.index.union(x.index)).sort_index().ffill().reindex(x.index)
    # Recompute all QQQ-derived overlay indicators from the same frozen close series as B0.
    feat["adj_close"]=x.qqq_adj_close.to_numpy(float)
    for d in (FD,SD): feat[f"dma{d}"]=feat.adj_close.rolling(d,min_periods=d).mean()
    feat["ret63"]=feat.adj_close/feat.adj_close.shift(63)-1
    feat["dd252"]=feat.adj_close/feat.adj_close.rolling(252,min_periods=252).max()-1
    events_actual,b0_actual=build_events_and_signal(x.qqq_adj_close.astype(float))
    on=np.zeros(len(x)); intr=np.zeros(len(x))
    on[1:]=x.tqqq_adj_open.to_numpy()[1:]/x.tqqq_adj_close.to_numpy()[:-1]-1
    intr[:]=x.tqqq_adj_close.to_numpy()/x.tqqq_adj_open.to_numpy()-1
    for name,overlay in [("B0_canonical",np.ones(len(x))),
                         ("sticky_original",make_overlay(feat,"sticky_original")),
                         ("hard_nonsticky",make_overlay(feat,"hard_nonsticky")),
                         ("daily_nonsticky",make_overlay(feat,"daily_nonsticky"))]:
        sig=np.minimum(b0_actual.astype(float),overlay)
        assert np.all(sig<=b0_actual+1e-12)
        rows.append(evaluate("actual_tqqq",name,sig,x.index,on,intr))
    out=pd.DataFrame(rows)
    out.to_csv(OUT/"canonical_structural_state_ablation_results.csv",index=False)
    manifest={"status":"PASS","parameters":{"structural_dma":SD,"fast_dma":FD,"ret63_threshold":RT,
      "dd252_threshold":DT,"vix_threshold":VT,"structural_exposure":EXP},
      "synthetic_start":q.index[0].date().isoformat(),"synthetic_end":q.index[-1].date().isoformat(),
      "synthetic_rows":len(q),"actual_start":x.index[0].date().isoformat(),
      "actual_end":x.index[-1].date().isoformat(),"actual_rows":len(x),
      "actual_frozen_input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "actual_baseline_event_count":len(events_actual),"combination":"min(B0, overlay)",
      "modes":["sticky_original","hard_nonsticky","daily_nonsticky"],
      "synthetic_warning":"Hypothetical 3x QQQ proxy only, not actual TQQQ or calibrated fund history."}
    (OUT/"canonical_structural_state_ablation_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
    print(out.to_string(index=False))

if __name__=="__main__": main()
