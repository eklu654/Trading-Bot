"""Episode attribution for combined B0 + structural state overlays.

Reports intervals where the structural overlay reduces exposure after B0 has
returned to 100%, then computes conditional leave-one-interval-out effects.
This is diagnostic, not a parameter search.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns
from tqqq_canonical_same_input_reconciliation import INITIAL, make_frozen_input, build_events_and_signal

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START,END="1999-03-10","2026-10-08"
SD,FD,RT,DT,VT,EXP=150,100,-0.20,-0.20,30.0,0.25


def download(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def features():
    q=download("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    q=q.dropna(subset=["open","close","adj_close"])
    for d in (FD,SD): q[f"dma{d}"]=q.adj_close.rolling(d,min_periods=d).mean()
    q["ret63"]=q.adj_close/q.adj_close.shift(63)-1
    q["dd252"]=q.adj_close/q.adj_close.rolling(252,min_periods=252).max()-1
    v=download("^VIX")[["Close"]].rename(columns={"Close":"vix"})
    q=q.join(v,how="left"); q["vix"]=q.vix.ffill()
    return q.dropna(subset=["vix"])


def overlay_signal(q,mode):
    ma=q[f"dma{SD}"].to_numpy(); fast=q[f"dma{FD}"].to_numpy()
    px=q.adj_close.to_numpy(); r=q.ret63.to_numpy(); d=q.dd252.to_numpy(); v=q.vix.to_numpy()
    armed=False; hard=False; out=[]
    for i in range(len(q)):
        if not np.isfinite(ma[i]) or not np.isfinite(fast[i]): out.append(1.0); continue
        structural=px[i]<ma[i] and fast[i]<ma[i]
        shock=px[i]<fast[i] and ((np.isfinite(r[i]) and r[i]<=RT) or
            (np.isfinite(d[i]) and d[i]<=DT) or v[i]>=VT)
        if mode=="sticky_original":
            if not armed and (structural or shock): armed=True; hard=bool(shock)
            elif armed:
                if px[i]>=ma[i]: armed=hard=False
                elif shock: hard=True
            w=0.0 if hard else (EXP if armed else 1.0)
        elif mode=="hard_nonsticky":
            if not armed and (structural or shock): armed=True
            elif armed and px[i]>=ma[i]: armed=False
            w=0.0 if shock else (EXP if armed else 1.0)
        elif mode=="daily_nonsticky":
            w=0.0 if shock else (EXP if structural else 1.0)
        else: raise ValueError(mode)
        out.append(w)
    return np.asarray(out,float)


def runs(mask):
    starts=np.flatnonzero(mask & ~np.r_[False,mask[:-1]])
    ends=np.flatnonzero(mask & ~np.r_[mask[1:],False])
    return list(zip(starts,ends))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x,path=make_frozen_input()
    q=features()
    feat=q.reindex(q.index.union(x.index)).sort_index().ffill().reindex(x.index)
    # Recompute QQQ indicators from the frozen close series used by B0.
    feat["adj_close"]=x.qqq_adj_close.to_numpy(float)
    for d in (FD,SD): feat[f"dma{d}"]=feat.adj_close.rolling(d,min_periods=d).mean()
    feat["ret63"]=feat.adj_close/feat.adj_close.shift(63)-1
    feat["dd252"]=feat.adj_close/feat.adj_close.rolling(252,min_periods=252).max()-1
    events,b0=build_events_and_signal(x.qqq_adj_close.astype(float)); b0=b0.astype(float)
    on=np.zeros(len(x)); intr=np.zeros(len(x))
    on[1:]=x.tqqq_adj_open.to_numpy()[1:]/x.tqqq_adj_close.to_numpy()[:-1]-1
    intr[:]=x.tqqq_adj_close.to_numpy()/x.tqqq_adj_open.to_numpy()-1
    dates=x.index
    event_rows=[]
    for si,li,ri in events:
        event_rows.append({"shock_date":dates[si].date().isoformat(),"low_date":dates[li].date().isoformat(),
          "recovery_decision_date":dates[ri].date().isoformat(),
          "baseline_reentry_execution_date":dates[min(ri+1,len(dates)-1)].date().isoformat()})
    pd.DataFrame(event_rows).to_csv(OUT/"canonical_structural_attribution_b0_events.csv",index=False)
    intervals=[]; summary=[]
    for mode in ("sticky_original","hard_nonsticky","daily_nonsticky"):
        ov=overlay_signal(feat,mode)
        combined=np.minimum(b0,ov)
        assert np.all(combined<=b0+1e-12)
        ret=next_open_daily_returns(combined,on,intr)
        full_final=float(INITIAL*np.cumprod(1+ret)[-1])
        # Overlay only matters on sessions B0 itself targets full exposure.
        active=(ov<1.0)&(b0>=1.0)
        starts_ends=runs(active)
        for n,(s,e) in enumerate(starts_ends,1):
            cf=ov.copy(); cf[s:e+1]=1.0
            cf_signal=np.minimum(b0,cf)
            cf_ret=next_open_daily_returns(cf_signal,on,intr)
            cf_final=float(INITIAL*np.cumprod(1+cf_ret)[-1])
            prior_recoveries=[ev for ev in event_rows if pd.Timestamp(ev["recovery_decision_date"])<=dates[s]]
            last_prior_recovery=prior_recoveries[-1]["recovery_decision_date"] if prior_recoveries else ""
            labels=[]
            for label,a,b in [("COVID","2020-02-19","2020-07-31"),("2022","2022-01-03","2022-12-30"),
                              ("2018-2019","2018-10-01","2019-12-31")]:
                if dates[s]<=pd.Timestamp(b) and dates[e]>=pd.Timestamp(a): labels.append(label)
            intervals.append({"mode":mode,"episode":n,"start":dates[s].date().isoformat(),
              "end":dates[e].date().isoformat(),"sessions":e-s+1,
              "mean_overlay_exposure":float(ov[s:e+1].mean()),"minimum_overlay_exposure":float(ov[s:e+1].min()),
              "intersects":",".join(labels),"latest_b0_recovery_decision_on_or_before_interval":last_prior_recovery,
              "full_candidate_final":full_final,"counterfactual_final_without_interval":cf_final,
              "conditional_terminal_contribution":full_final-cf_final})
        summary.append({"source":"actual_tqqq","mode":mode,"final_balance":full_final,
          "baseline_final_balance":float(INITIAL*np.cumprod(1+next_open_daily_returns(b0,on,intr))[-1]),
          "incremental_overlay_intervals":len(starts_ends),"incremental_defense_sessions":int(active.sum()),
          "sessions_reduced_after_b0_reentry":int(active.sum()),
          "sum_conditional_contributions_not_additive":float(sum(r["conditional_terminal_contribution"] for r in intervals if r["mode"]==mode))})
    pd.DataFrame(intervals).to_csv(OUT/"canonical_structural_attribution_intervals.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"canonical_structural_attribution_summary.csv",index=False)
    manifest={"status":"PASS","actual_start":dates[0].date().isoformat(),"actual_end":dates[-1].date().isoformat(),
      "rows":len(x),"baseline_events":len(events),"parameters":{"structural_dma":SD,"fast_dma":FD,
      "ret63_threshold":RT,"dd252_threshold":DT,"vix_threshold":VT,"structural_exposure":EXP},
      "frozen_input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "interpretation":"Leave-one-interval-out terminal contributions are conditional and not additive."}
    (OUT/"canonical_structural_attribution_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
    print("\nSUMMARY\n",pd.DataFrame(summary).to_string(index=False))
    print("\nCOVID/2022/2018-19 INTERVALS\n",pd.DataFrame(intervals).query("intersects != ''").to_string(index=False))

if __name__=="__main__": main()
