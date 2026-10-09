"""Event-level audit: do structural/fast-shock signals at canonical recovery
decisions identify rallies that subsequently fail? QQQ-only diagnostic, no
pre-inception TQQQ return claims, and no parameter search.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START,END="1999-03-10","2026-10-08"
SHOCK,RECOVERY=-0.045,0.10
SD,FD,RT,DT,VT=150,100,-0.20,-0.20,30.0


def download(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=download("QQQ").rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    q=q.dropna(subset=["open","close","adj_close"])
    v=download("^VIX")[["Close"]].rename(columns={"Close":"vix"})
    q=q.join(v,how="left"); q["vix"]=q.vix.ffill()
    for d in (50,100,150,200): q[f"dma{d}"]=q.adj_close.rolling(d,min_periods=d).mean()
    q["ret63"]=q.adj_close/q.adj_close.shift(63)-1
    q["dd252"]=q.adj_close/q.adj_close.rolling(252,min_periods=252).max()-1
    close=q.adj_close.to_numpy(); dates=q.index
    daily=q.adj_close.pct_change().fillna(0).to_numpy()
    events=[]; armed=False; shock_i=low_i=None
    for i in range(1,len(q)):
        if not armed and daily[i] <= SHOCK:
            armed=True; shock_i=low_i=i
        if armed:
            if close[i]<close[low_i]: low_i=i
            if close[i]/close[low_i]-1>=RECOVERY:
                row={"event":len(events)+1,"shock_date":dates[shock_i].date().isoformat(),
                  "low_date":dates[low_i].date().isoformat(),"recovery_date":dates[i].date().isoformat(),
                  "sessions_shock_to_recovery":i-shock_i,"sessions_low_to_recovery":i-low_i,
                  "low_price":float(close[low_i]),"recovery_price":float(close[i]),
                  "recovery_vs_low":float(close[i]/close[low_i]-1)}
                ma150=q.dma150.iloc[i]; ma100=q.dma100.iloc[i]; px=close[i]
                row.update({"qqq_below_dma150":bool(px<ma150) if np.isfinite(ma150) else None,
                  "dma100_below_dma150":bool(ma100<ma150) if np.isfinite(ma100) and np.isfinite(ma150) else None,
                  "structural_condition":bool(px<ma150 and ma100<ma150) if np.isfinite(ma100) and np.isfinite(ma150) else None,
                  "qqq_below_dma100":bool(px<ma100) if np.isfinite(ma100) else None,
                  "ret63":float(q.ret63.iloc[i]) if np.isfinite(q.ret63.iloc[i]) else None,
                  "dd252":float(q.dd252.iloc[i]) if np.isfinite(q.dd252.iloc[i]) else None,
                  "vix":float(q.vix.iloc[i]) if np.isfinite(q.vix.iloc[i]) else None})
                row["fast_shock_condition"]=bool(px<ma100 and ((np.isfinite(q.ret63.iloc[i]) and q.ret63.iloc[i]<=RT) or
                    (np.isfinite(q.dd252.iloc[i]) and q.dd252.iloc[i]<=DT) or q.vix.iloc[i]>=VT)) if np.isfinite(ma100) else None
                for h in (20,60,120,252):
                    end=min(len(q)-1,i+h); future=close[i+1:end+1]
                    if len(future):
                        row[f"forward_{h}s_return"]=float(close[end]/close[i]-1)
                        row[f"forward_{h}s_min_return"]=float(future.min()/close[i]-1)
                        row[f"fall_below_recovery_level_{h}s"]=bool((future < close[low_i]*(1+RECOVERY)).any())
                        row[f"new_low_{h}s"]=bool((future < close[low_i]).any())
                    else:
                        row[f"forward_{h}s_return"]=None; row[f"forward_{h}s_min_return"]=None
                        row[f"fall_below_recovery_level_{h}s"]=None; row[f"new_low_{h}s"]=None
                events.append(row); armed=False
    out=pd.DataFrame(events)
    out.to_csv(OUT/"canonical_recovery_event_quality.csv",index=False)
    # Event-level descriptive scorecard. No claims of statistical significance:
    # events and forward horizons overlap, and the full sample was inspected.
    summaries=[]
    for horizon in (20,60,120,252):
        target=f"fall_below_recovery_level_{horizon}s"
        valid=out[out[target].notna()]
        for feature in ("structural_condition","fast_shock_condition"):
            mask=valid[feature].fillna(False).astype(bool)
            positives=valid[target].astype(bool)
            tp=int((mask&positives).sum()); fp=int((mask&~positives).sum())
            fn=int((~mask&positives).sum()); tn=int((~mask&~positives).sum())
            summaries.append({"horizon_sessions":horizon,"feature":feature,"events":len(valid),
              "flagged":int(mask.sum()),"failed_recoveries":int(positives.sum()),
              "true_positive":tp,"false_positive":fp,"false_negative":fn,"true_negative":tn,
              "precision":tp/(tp+fp) if tp+fp else None,"recall":tp/(tp+fn) if tp+fn else None})
    pd.DataFrame(summaries).to_csv(OUT/"canonical_recovery_event_quality_scorecard.csv",index=False)
    manifest={"status":"PASS","start":dates[0].date().isoformat(),"end":dates[-1].date().isoformat(),
      "rows":len(q),"canonical_event_count":len(out),"shock_threshold":SHOCK,"recovery_threshold":RECOVERY,
      "structural_dma":SD,"fast_dma":FD,"ret63_threshold":RT,"dd252_threshold":DT,"vix_threshold":VT,
      "source":"QQQ adjusted close and VIX close","purpose":"event-level signal diagnostics only",
      "caveat":"Event-level, overlapping forward windows, in-sample and descriptive only; not a trading backtest or TQQQ results."}
    (OUT/"canonical_recovery_event_quality_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
    print("\nEVENTS\n",out.to_string(index=False))
    print("\nSCORECARD\n",pd.DataFrame(summaries).to_string(index=False))

if __name__=="__main__": main()
