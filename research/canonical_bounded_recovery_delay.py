"""Bounded delay ablation for slow, matrix-flagged B0 recovery attempts.

Fast recovery <= 8 sessions from the current low is exempt. Otherwise, if the
matrix flags the +10% recovery, wait for the matrix to clear but cap that wait
at D sessions. A new low resets the pending attempt and requires a new +10%
rebound. Reentry is never allowed below the +10% recovery level.
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
FAST_EXCEPTION=8
MAX_DELAYS=(3,5,10)


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


def flags(q,i):
    px=q.adj_close.iloc[i]; ma=q.dma150.iloc[i]; fast=q.dma100.iloc[i]
    if not (np.isfinite(ma) and np.isfinite(fast)): return False,False
    structural=bool(px<ma and fast<ma)
    r=q.ret63.iloc[i]; d=q.dd252.iloc[i]; v=q.vix.iloc[i]
    shock=bool(px<fast and ((np.isfinite(r) and r<=RT) or (np.isfinite(d) and d<=DT) or v>=VT))
    return structural,shock


def build(close,q,delay_cap):
    px=close.to_numpy(float); dates=close.index
    daily=close.pct_change().fillna(0).to_numpy()
    sig=np.ones(len(close),float); armed=False; shock_i=low_i=None; pending_i=None
    attempts=[]; releases=[]
    for i in range(1,len(close)):
        if not armed and daily[i]<=SHOCK:
            armed=True; shock_i=low_i=i; pending_i=None
        if not armed: continue
        new_low=px[i]<px[low_i]
        if new_low:
            low_i=i; pending_i=None
        sig[i]=0.0
        if px[i]/px[low_i]-1<RECOVERY: continue
        speed=i-low_i; structural,fast=flags(q,i); flagged=structural or fast
        fast_ok=speed<=FAST_EXCEPTION
        matrix_clear=not flagged
        if fast_ok or matrix_clear:
            reason="fast_recovery_exception" if fast_ok else "matrix_clear"
            release=True
        elif pending_i is None:
            pending_i=i; release=False; reason="start_bounded_wait"
        elif i-pending_i>=delay_cap:
            release=True; reason="delay_cap"
        else:
            release=False; reason="waiting_for_matrix_clear_or_cap"
        attempts.append({"delay_cap_sessions":delay_cap,"shock_date":dates[shock_i].date().isoformat(),
          "running_low_date":dates[low_i].date().isoformat(),"attempt_date":dates[i].date().isoformat(),
          "sessions_from_low":speed,"structural_flag":structural,"fast_shock_flag":fast,
          "fast_recovery_exception":fast_ok,"pending_since":dates[pending_i].date().isoformat() if pending_i is not None else "",
          "new_low_today":new_low,"released":release,"reason":reason})
        if release:
            sig[i]=1.0
            releases.append({"delay_cap_sessions":delay_cap,"shock_date":dates[shock_i].date().isoformat(),
              "low_date":dates[low_i].date().isoformat(),"release_date":dates[i].date().isoformat(),
              "sessions_from_low":speed,"reason":reason})
            armed=False; shock_i=low_i=None; pending_i=None
    return sig,pd.DataFrame(attempts),pd.DataFrame(releases)


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
    return row


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=features()
    q["adj_open"]=q.open*q.adj_close/q.close
    q["on3"]=((1+3*(q.adj_open/q.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    q["in3"]=((1+3*(q.adj_close/q.adj_open-1)).clip(lower=0)-1).fillna(0)
    _,b0=build_events_and_signal(q.adj_close.astype(float))
    rows=[]; attempts=[]; releases=[]
    rows.append(evaluate("synthetic_qqq_3x","B0_canonical",b0.astype(float),q.index,q.on3.to_numpy(),q.in3.to_numpy()))
    for d in MAX_DELAYS:
        sig,a,r=build(q.adj_close,q,d)
        rows.append(evaluate("synthetic_qqq_3x",f"bounded_delay_{d}s_fast_exception_8s",sig,q.index,q.on3.to_numpy(),q.in3.to_numpy()))
        if len(a):
            a["source"]="synthetic_qqq_3x"; attempts.extend(a.to_dict("records"))
        if len(r):
            r["source"]="synthetic_qqq_3x"; releases.extend(r.to_dict("records"))
    x,path=make_frozen_input()
    feat=q.reindex(q.index.union(x.index)).sort_index().ffill().reindex(x.index)
    _,b0a=build_events_and_signal(x.qqq_adj_close.astype(float))
    on=np.zeros(len(x)); intr=np.zeros(len(x))
    on[1:]=x.tqqq_adj_open.to_numpy()[1:]/x.tqqq_adj_close.to_numpy()[:-1]-1
    intr[:]=x.tqqq_adj_close.to_numpy()/x.tqqq_adj_open.to_numpy()-1
    rows.append(evaluate("actual_tqqq","B0_canonical",b0a.astype(float),x.index,on,intr))
    for d in MAX_DELAYS:
        sig,a,r=build(x.qqq_adj_close.astype(float),feat,d)
        rows.append(evaluate("actual_tqqq",f"bounded_delay_{d}s_fast_exception_8s",sig,x.index,on,intr))
        if len(a):
            a["source"]="actual_tqqq"; attempts.extend(a.to_dict("records"))
        if len(r):
            r["source"]="actual_tqqq"; releases.extend(r.to_dict("records"))
    summary=pd.DataFrame(rows)
    summary.to_csv(OUT/"canonical_bounded_recovery_delay_results.csv",index=False)
    pd.DataFrame(attempts).to_csv(OUT/"canonical_bounded_recovery_delay_attempts.csv",index=False)
    pd.DataFrame(releases).to_csv(OUT/"canonical_bounded_recovery_delay_releases.csv",index=False)
    manifest={"status":"PASS","synthetic_start":q.index[0].date().isoformat(),"synthetic_end":q.index[-1].date().isoformat(),
      "synthetic_rows":len(q),"actual_start":x.index[0].date().isoformat(),"actual_end":x.index[-1].date().isoformat(),
      "actual_rows":len(x),"actual_frozen_input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "initial_balance":INITIAL,"shock_threshold":SHOCK,"recovery_threshold":RECOVERY,
      "structural_dma":SD,"fast_dma":FD,"ret63_threshold":RT,"dd252_threshold":DT,"vix_threshold":VT,
      "fast_recovery_exception_sessions":FAST_EXCEPTION,"bounded_wait_caps":list(MAX_DELAYS),
      "rule":"veto slow flagged B0 recovery; release when matrix clears or cap expires while price remains >=10% above running low; new low resets pending wait",
      "synthetic_warning":"Hypothetical 3x QQQ proxy only; not actual TQQQ or calibrated fund simulation."}
    (OUT/"canonical_bounded_recovery_delay_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2)); print("\nSUMMARY\n",summary.to_string(index=False))
    print("\nACTUAL RELEASES\n",pd.DataFrame(releases).query("source == 'actual_tqqq'").to_string(index=False))

if __name__=="__main__": main()
