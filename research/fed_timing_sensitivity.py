"""One-session Fed-state timing sensitivity on identical canonical QQQ/TQQQ inputs.

Compares the existing conservative one-QQQ-session-lag Fed state with a same-session
mapped state. The latter is a diagnostic sensitivity only, not presumed live-safe:
it answers whether a one-session timestamp convention changes overlay signals and
portfolio outcomes. The Fed classifier, DMA, baseline, execution and costs are held
fixed. No parameters are optimized.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
import canonical_shock_recovery_fed_dma_overlay as base

OUT = ROOT / "data" / "research"

def map_state(fed: pd.DataFrame, idx: pd.DatetimeIndex, lag: int) -> pd.Series:
    left = pd.DataFrame({"date": idx}).sort_values("date")
    right = fed[["monetary_state"]].reset_index()
    right.columns = ["date", "monetary_state"]
    right = right.sort_values("date")
    mapped = pd.merge_asof(left, right, on="date", direction="backward")
    s = pd.Series(mapped["monetary_state"].to_numpy(), index=idx)
    if lag:
        s = s.shift(lag)
    return s.fillna("INSUFFICIENT_HISTORY")

def equity_metrics(eq: np.ndarray, dates: pd.DatetimeIndex) -> dict:
    peak = np.maximum.accumulate(eq)
    years = (dates[-1] - dates[0]).days / 365.25
    return {"ending_balance": float(eq[-1]),
            "cagr": float((eq[-1] / base.INITIAL) ** (1 / years) - 1),
            "max_drawdown": float((eq / peak - 1).min())}

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    q = base.download_market("QQQ")
    t = base.download_market("TQQQ")
    q = q.rename(columns={"Open":"qqq_open","High":"qqq_high","Low":"qqq_low",
        "Close":"qqq_close","Adj Close":"qqq_adj_close","Volume":"qqq_volume"})
    t = t.rename(columns={"Open":"tqqq_open","High":"tqqq_high","Low":"tqqq_low",
        "Close":"tqqq_close","Adj Close":"tqqq_adj_close","Volume":"tqqq_volume"})
    common = q.join(t, how="inner").dropna().sort_index()
    if common.empty or common.index.has_duplicates:
        raise RuntimeError("Invalid common QQQ/TQQQ market input")
    fed = base.download_fed()
    states = {lag: map_state(fed, common.index, lag) for lag in (0, 1)}
    events = base.build_shock_recovery_events(common["qqq_adj_close"])
    baseline = base.build_baseline_signal(len(common), events)
    overlay = {}
    for lag in (0, 1):
        overlay[lag], _ = base.build_fed_dma_overlay(common["qqq_adj_close"], states[lag], base.DMA)
    signals = {lag: np.minimum(baseline, overlay[lag]) for lag in (0,1)}
    # Same execution convention and frozen input rows for every comparison.
    adj_open = common["tqqq_open"].to_numpy(float) * common["tqqq_adj_close"].to_numpy(float) / common["tqqq_close"].to_numpy(float)
    adj_close = common["tqqq_adj_close"].to_numpy(float)
    overnight = np.zeros(len(common)); overnight[1:] = adj_open[1:] / adj_close[:-1] - 1
    intraday = adj_close / adj_open - 1
    daily_returns = {lag: base.next_open_daily_returns(signals[lag], overnight, intraday) for lag in (0,1)}
    rows=[]
    for lag in (0,1):
        name = "same_session_mapped_state_DIAGNOSTIC" if lag == 0 else "one_session_lag_CONTROL"
        eq = base.INITIAL * np.cumprod(1 + daily_returns[lag])
        rows.append({"variant":name,"lag_sessions":lag,**equity_metrics(eq,common.index),
          "defensive_signal_days":int((signals[lag] < 1).sum()),
          "fed_state_days_different_from_lag1":int((states[lag] != states[1]).sum())})
    for lag in (0,1):
        name = "same_session_mapped_state_DIAGNOSTIC" if lag == 0 else "one_session_lag_CONTROL"
        for bps in (0,10,25):
            eq = base.next_open_cost_equity(signals[lag],overnight,intraday,bps)
            rows.append({"variant":name,"lag_sessions":lag,"cost_bps":bps,
              **equity_metrics(eq,common.index),"defensive_signal_days":int((signals[lag] < 1).sum()),
              "fed_state_days_different_from_lag1":int((states[lag] != states[1]).sum())})
    pd.DataFrame(rows).to_csv(OUT/"fed_timing_sensitivity_summary.csv",index=False)
    daily = pd.DataFrame({"date":common.index,"fed_state_same_session":states[0].to_numpy(),
      "fed_state_lag1":states[1].to_numpy(),"fed_state_diff":(states[0].to_numpy()!=states[1].to_numpy()),
      "baseline_signal":baseline,"overlay_same_session":overlay[0],"overlay_lag1":overlay[1],
      "candidate_same_session":signals[0],"candidate_lag1":signals[1],
      "signal_diff":signals[0]!=signals[1]})
    daily.to_csv(OUT/"fed_timing_sensitivity_daily.csv",index=False)
    manifest={"status":"COMPLETED_DIAGNOSTIC","start":common.index[0].date().isoformat(),
      "end":common.index[-1].date().isoformat(),"rows":int(len(common)),"initial_balance":base.INITIAL,
      "baseline":"unchanged QQQ <= -4.5% shock / +10% recovery rule",
      "overlay":"QQQ below 200-DMA and Fed state TIGHTENING_PAUSED; sticky until QQQ recovers above 200-DMA",
      "only_change":"Fed state mapping lag: 0 versus 1 QQQ session",
      "warning":"Zero-lag variant is a timing sensitivity, not approved live-safe timing.",
      "market_input_sha256":hashlib.sha256(common.to_csv(float_format="%.12g").encode()).hexdigest(),
      "events":len(events),"state_diff_sessions":int((states[0]!=states[1]).sum()),
      "overlay_diff_sessions":int((overlay[0]!=overlay[1]).sum()),
      "candidate_signal_diff_sessions":int((signals[0]!=signals[1]).sum())}
    (OUT/"fed_timing_sensitivity_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))
    print(pd.DataFrame(rows).to_string(index=False))

if __name__ == "__main__":
    main()
