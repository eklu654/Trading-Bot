"""Small predeclared counterfactual for short-window QQQ rolling declines.

Uses the canonical frozen QQQ/TQQQ common input and canonical B0 signal. The
short-window rule triggers after X% close-to-trailing-Y-session-high decline.
Overlay is bounded to a fixed number of sessions, then automatically expires;
B0 can always reduce exposure further. No parameter sweep and no promotion.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

try:
    from .tqqq_canonical_same_input_reconciliation import (
        INITIAL, make_frozen_input, build_events_and_signal,
        independently_rebuild_events,
    )
    from .causal_execution import next_open_daily_returns, next_open_cost_equity
except ImportError:
    from tqqq_canonical_same_input_reconciliation import (
        INITIAL, make_frozen_input, build_events_and_signal,
        independently_rebuild_events,
    )
    from causal_execution import next_open_daily_returns, next_open_cost_equity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
CANDIDATES=((0.075,10,0.75,10),(0.10,10,0.75,10),
            (0.075,10,0.75,20),(0.10,10,0.75,20))
COST_BPS=(0.0,10.0,25.0)


def build_bounded_state(close: pd.Series, x_pct: float, y: int, cap: float, duration: int):
    """At close, trigger when close <= rolling Y-session high*(1-X); cap next-open exposure for duration sessions."""
    if not (0 < x_pct < 1 and y > 1 and 0 <= cap <= 1 and duration > 0):
        raise ValueError("Invalid candidate configuration")
    high=close.rolling(y,min_periods=y).max()
    dd=(close/high-1.0).to_numpy(float)
    state=np.ones(len(close),dtype=float)
    until=-1
    for i,v in enumerate(dd):
        if np.isfinite(v) and v <= -x_pct:
            until=max(until,i+duration)
        if i <= until:
            state[i]=cap
    return state,dd


def metrics(returns, dates):
    eq=INITIAL*np.cumprod(1+returns)
    dd=eq/np.maximum.accumulate(eq)-1
    years=(dates[-1]-dates[0]).days/365.25
    logret=np.log1p(returns)
    r252=pd.Series(logret).rolling(252,min_periods=252).sum().dropna()
    return {"final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
            "max_drawdown":float(dd.min()),"worst_rolling_252_session_return":float(np.expm1(r252.min())) if len(r252) else None}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x,frozen_path=make_frozen_input()
    dates=pd.DatetimeIndex(x.index)
    close=x["qqq_adj_close"].astype(float)
    events,base=build_events_and_signal(close)
    events2,base2=independently_rebuild_events(close)
    if events != events2 or not np.array_equal(base,base2):
        raise AssertionError("B0 canonical reconciliation failed")
    peak=close.rolling(252,min_periods=252).max()
    dd=(close/peak-1).to_numpy(float)
    t_open=x["tqqq_adj_open"].to_numpy(float); t_close=x["tqqq_adj_close"].to_numpy(float)
    overnight=np.zeros(len(x)); intraday=np.zeros(len(x))
    overnight[1:]=t_open[1:]/t_close[:-1]-1
    intraday[:]=t_close/t_open-1
    overnight[0]=intraday[0]=0
    bret=next_open_daily_returns(base,overnight,intraday)
    rows=[]; costs=[]; daily=pd.DataFrame({"date":dates,"qqq_adj_close":close.to_numpy(),"b0_signal":base,"b0_return":bret})
    for xp,y,cap,duration in CANDIDATES:
        state,short_dd=build_bounded_state(close,xp,y,cap,duration)
        # Bounded overlay only caps B0; it never increases B0 exposure.
        sig=np.minimum(base,state)
        name=f"DROP{xp*100:g}_IN{y}_CAP{cap*100:g}_DUR{duration}"
        ret=next_open_daily_returns(sig,overnight,intraday)
        rows.append({"strategy":name,"x_decline_pct":xp*100,"y_sessions":y,"warning_exposure_cap_pct":cap*100,
                     "max_duration_sessions":duration,"warning_days":int(np.sum(state<1)),
                     "warning_episodes":int(np.sum((state<1)&~np.r_[False,state[:-1]<1])),
                     "mean_target_exposure":float(sig.mean()),**metrics(ret,dates)})
        daily[name+"_signal"]=sig; daily[name+"_return"]=ret
        for bps in COST_BPS:
            curve=next_open_cost_equity(sig,overnight,intraday,bps,initial=INITIAL)
            costs.append({"strategy":name,"cost_bps_per_full_exposure_change":bps,"final_balance":float(curve[-1]),
                          "max_drawdown":float((curve/np.maximum.accumulate(curve)-1).min())})
    base_metrics=metrics(bret,dates)
    for r in rows:
        r["b0_final_balance"]=base_metrics["final_balance"]
        r["terminal_difference_vs_b0"]=r["final_balance"]-base_metrics["final_balance"]
        r["max_drawdown_improvement_pp"]=(r["max_drawdown"]-base_metrics["max_drawdown"])*100
    summary=pd.DataFrame(rows)
    summary.to_csv(OUT/"qqq_rolling_decline_bounded_overlay_summary.csv",index=False)
    pd.DataFrame(costs).to_csv(OUT/"qqq_rolling_decline_bounded_overlay_costs.csv",index=False)
    daily.to_csv(OUT/"qqq_rolling_decline_bounded_overlay_daily.csv",index=False)
    frozen_hash=hashlib.sha256(Path(frozen_path).read_bytes()).hexdigest()
    metadata={"frozen_input_path":str(frozen_path),"frozen_input_sha256":frozen_hash,
              "rows":len(x),"start":str(dates[0].date()),"end":str(dates[-1].date()),
              "initial_balance":INITIAL,"b0_metrics":base_metrics,
              "candidate_matrix":[{"x_pct":a*100,"y_sessions":b,"exposure_cap_pct":c*100,"duration":d} for a,b,c,d in CANDIDATES],
              "cost_bps":COST_BPS,"execution":"close signal applied from next open via canonical next_open_daily_returns",
              "status":"exploratory retrospective counterfactual; no promotion; no untouched holdout"}
    (OUT/"qqq_rolling_decline_bounded_overlay_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    lines=["# Bounded QQQ Rolling-Decline Overlay Counterfactual","",
           "- Uses canonical frozen QQQ/TQQQ input and independently reconciles the frozen B0 event/signal.",
           f"- Data: {metadata['start']} to {metadata['end']}, {len(x)} rows; input SHA-256: `{frozen_hash}`.",
           "- Rule: a rolling X%-within-Y-session decline caps exposure at 75% for 10 or 20 sessions; repeated triggers extend the cap. B0 can always reduce exposure further.",
           "- Signal uses close data; the exposure state affects returns starting next open. This is an exploratory in-sample counterfactual, not validation.",
           "- No threshold was selected or promoted. Four predeclared candidates are compared against the identical B0 signal.",
           "", "## Baseline", "", pd.DataFrame([{"strategy":"B0",**base_metrics}]).to_markdown(index=False,floatfmt=".4f"),
           "", "## Candidate results (0 bps)", "", summary.to_markdown(index=False,floatfmt=".4f"),
           "", "## Transaction-cost sensitivity", "",pd.DataFrame(costs).to_markdown(index=False,floatfmt=".4f"),
           "", "## Decision guardrails", "",
           "- Compare terminal balance, maximum drawdown, worst rolling 252-session return, and costs together.",
           "- Positive drawdown improvement with severe terminal-wealth loss is not a successful candidate.",
           "- All four candidates are exploratory; no independent holdout is included.",
           "- Verify output artifact and review daily signals around 2000-02, 2007-09, 2018, 2020, 2022, and 2025 before any conclusion."]
    (OUT/"qqq_rolling_decline_bounded_overlay_report.md").write_text("\n".join(lines)+"\n")
    print(summary.to_string(index=False))
    print("B0",base_metrics)
    print("frozen_input_sha256",frozen_hash)

if __name__=="__main__": main()
