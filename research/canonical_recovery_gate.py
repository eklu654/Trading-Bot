"""Recovery-gated structural confirmation candidate.

Unlike the rejected always-on overlay, this rule uses the structural matrix
only when B0 attempts a +10% recovery. Fast recoveries are explicitly exempt.
If a slow recovery is vetoed, remain defensive, update the running low, and
re-evaluate later recovery attempts. QQQ close signals execute next open.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns
from tqqq_canonical_same_input_reconciliation import INITIAL,SHOCK,RECOVERY,make_frozen_input,build_events_and_signal

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START,END="1999-03-10","2026-10-08"
SD,FD,RT,DT,VT=150,100,-0.20,-0.20,30.0
FAST_RECOVERY_MAX=(5,8,10)


def download(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def features():
    q=download("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    q=q.dropna(subset=["open","close","adj_close"])
    q["dma100"]=q.adj_close.rolling(FD,min_periods=FD).mean()
    q["dma150"]=q.adj_close.rolling(SD,min_periods=SD).mean()
    q["ret63"]=q.adj_close/q.adj_close.shift(63)-1
    q["dd252"]=q.adj_close/q.adj_close.rolling(252,min_periods=252).max()-1
    v=download("^VIX")[["Close"]].rename(columns={"Close":"vix"})
    q=q.join(v,how="left"); q["vix"]=q.vix.ffill()
    return q.dropna(subset=["vix"])


def matrix_flags(q,i):
    px=q.adj_close.iloc[i]; m=q.dma150.iloc[i]; f=q.dma100.iloc[i]
    if not (np.isfinite(m) and np.isfinite(f)): return False,False
    structural=bool(px<m and f<m)
    r=q.ret63.iloc[i]; d=q.dd252.iloc[i]; v=q.vix.iloc[i]
    fast=bool(px<f and ((np.isfinite(r) and r<=RT) or (np.isfinite(d) and d<=DT) or v>=VT))
    return structural,fast


def candidate(close,q,max_speed):
    px=close.to_numpy(float); dates=close.index
    daily=close.pct_change().fillna(0).to_numpy()
    sig=np.ones(len(close),float); armed=False; shock_i=low_i=None
    attempts=[]; events=[]
    for i in range(1,len(close)):
        if not armed and daily[i]<=SHOCK:
            armed=True; shock_i=low_i=i
        if not armed: continue
        if px[i]<px[low_i]: low_i=i
        sig[i]=0.0
        if px[i]/px[low_i]-1>=RECOVERY:
            speed=i-low_i; structural,fast=matrix_flags(q,i); flagged=structural or fast
            allow_fast=speed<=max_speed
            release=allow_fast or not flagged
            attempts.append({"max_fast_recovery_sessions":max_speed,"shock_date":dates[shock_i].date().isoformat(),
              "low_date":dates[low_i].date().isoformat(),"attempt_date":dates[i].date().isoformat(),
              "sessions_low_to_attempt":speed,"structural_flag":structural,"fast_shock_flag":fast,
              "matrix_flag":flagged,"fast_recovery_exception":allow_fast,"released":release,
              "reason":"fast_recovery_exception" if allow_fast else ("matrix_clear" if not flagged else "veto_slow_flagged_recovery")})
            if release:
                sig[i]=1.0
                events.append({"shock_date":dates[shock_i].date().isoformat(),"final_low_date":dates[low_i].date().isoformat(),
                  "release_decision_date":dates[i].date().isoformat(),"sessions_low_to_release":speed})
                armed=False; shock_i=low_i=None
    return sig,pd.DataFrame(attempts),pd.DataFrame(events)


def evaluate(source,name,sig,dates,on,intr):
    ret=next_open_daily_returns(sig,on,intr); eq=INITIAL*np.cumprod(1+ret)
    dd=eq/np.maximum.accumulate(eq)-1; years=(dates[-1]-dates[0]).days/365.25
    roll=pd.Series(np.log1p(ret)).rolling(252,min_periods=252).sum().dropna()
    row={"source":source,"strategy":name,"start":dates[0].date().isoformat(),"end":dates[-1].date().isoformat(),
      "rows":len(dates),"initial_balance":INITIAL,"final_balance":float(eq[-1]),
      "cagr":float((eq[-1]/INITIAL)**(1/years)-1),"max_drawdown":float(dd.min()),
      "worst_rolling_252_session_return":float(np.expm1(roll.min())) if len(roll) else np.nan,
      "mean_signal_exposure":float(sig.mean()),"defensive_sessions":int((sig<1).sum()),
      "exposure_changes":int((np.abs(np.diff(sig,prepend=sig[0]))>1e-12).sum())}
    for label,a,b in [("dotcom","2000-01-01","2002-12-31"),("gfc","2007-10-01","2009-12-31"),
      ("covid","2020-02-19","2020-07-31"),("inflation_2022","2022-01-03","2022-12-30")]:
        mask=(dates>=a)&(dates<=b)
        if mask.any():
            ix=np.flatnonzero(mask); local=eq[mask]; prev=eq[ix[0]-1] if ix[0] else INITIAL
            row[label+"_return"]=float(local[-1]/prev-1)
            row[label+"_max_dd"]=float((local/np.maximum.accumulate(local)-1).min())
    return row,ret


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=features()
    q["adj_open"]=q.open*q.adj_close/q.close
    q["on3"]=((1+3*(q.adj_open/q.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    q["in3"]=((1+3*(q.adj_close/q.adj_open-1)).clip(lower=0)-1).fillna(0)
    rows=[]; all_attempts=[]; all_events=[]
    _,b0=build_events_and_signal(q.adj_close.astype(float))
    r,_=evaluate("synthetic_qqq_3x","B0_canonical",b0.astype(float),q.index,q.on3.to_numpy(),q.in3.to_numpy()); rows.append(r)
    for n in FAST_RECOVERY_MAX:
        sig,attempts,events=candidate(q.adj_close,q,n)
        r,_=evaluate("synthetic_qqq_3x",f"recovery_gate_fast_exception_{n}s",sig,q.index,q.on3.to_numpy(),q.in3.to_numpy()); rows.append(r)
        if len(attempts): all_attempts.extend(attempts.to_dict("records"))
        if len(events):
            for e in events.to_dict("records"): e["max_fast_recovery_sessions"]=n; all_events.append(e)
    x,path=make_frozen_input()
    feat=q.reindex(q.index.union(x.index)).sort_index().ffill().reindex(x.index)
    _,b0a=build_events_and_signal(x.qqq_adj_close.astype(float))
    on=np.zeros(len(x)); intr=np.zeros(len(x))
    on[1:]=x.tqqq_adj_open.to_numpy()[1:]/x.tqqq_adj_close.to_numpy()[:-1]-1
    intr[:]=x.tqqq_adj_close.to_numpy()/x.tqqq_adj_open.to_numpy()-1
    r,_=evaluate("actual_tqqq","B0_canonical",b0a.astype(float),x.index,on,intr); rows.append(r)
    for n in FAST_RECOVERY_MAX:
        sig,attempts,events=candidate(x.qqq_adj_close.astype(float),feat,n)
        r,_=evaluate("actual_tqqq",f"recovery_gate_fast_exception_{n}s",sig,x.index,on,intr); rows.append(r)
        if len(attempts):
            for a in attempts.to_dict("records"): a["source"]="actual_tqqq"; all_attempts.append(a)
        if len(events):
            for e in events.to_dict("records"): e["source"]="actual_tqqq"; all_events.append(e)
    summary=pd.DataFrame(rows); summary.to_csv(OUT/"canonical_recovery_gate_results.csv",index=False)
    pd.DataFrame(all_attempts).to_csv(OUT/"canonical_recovery_gate_attempts.csv",index=False)
    pd.DataFrame(all_events).to_csv(OUT/"canonical_recovery_gate_releases.csv",index=False)
    manifest={"status":"PASS","synthetic_start":q.index[0].date().isoformat(),"synthetic_end":q.index[-1].date().isoformat(),
      "synthetic_rows":len(q),"actual_start":x.index[0].date().isoformat(),"actual_end":x.index[-1].date().isoformat(),
      "actual_rows":len(x),"actual_frozen_input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "initial_balance":INITIAL,"shock_threshold":SHOCK,"recovery_threshold":RECOVERY,
      "structural_dma":SD,"fast_dma":FD,"ret63_threshold":RT,"dd252_threshold":DT,"vix_threshold":VT,
      "fast_recovery_exceptions_tested":list(FAST_RECOVERY_MAX),
      "rule":"only veto a B0 +10% recovery when matrix flag is true and low-to-recovery speed exceeds exception; remain armed, update low, re-evaluate",
      "synthetic_warning":"Hypothetical 3x QQQ proxy only; not actual TQQQ or calibrated fund simulation."}
    (OUT/"canonical_recovery_gate_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
    print("\nSUMMARY\n",summary.to_string(index=False))
    print("\nACTUAL-TQQQ RECOVERY ATTEMPTS\n",pd.DataFrame(all_attempts).query("source == 'actual_tqqq'").to_string(index=False))

if __name__=="__main__": main()
