"""Preregistered paired episode attribution for canonical B0 vs frozen F75.

Uses the same canonical historical input and signal/execution functions as the
prospective shadow monitor. Actual TQQQ history only; pre-inception episodes
are explicitly marked unavailable, never synthetically filled.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

from f75_prospective_shadow_monitor import (
    CANON, EXPECTED_HASH, INITIAL, COSTS, build_shock_recovery_events,
    terminal_unrecovered_shock_start, build_censored_baseline_signal,
    download_fed, map_fed_state_to_market,
)
from canonical_shock_recovery_active_tightening_overlay import build_active_tightening_overlay

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
EPISODES = [
    ("dotcom_2000_2002", "2000-01-01", "2002-12-31"),
    ("gfc_2007_2009", "2007-01-01", "2009-12-31"),
    ("2011_stress", "2011-07-01", "2011-12-31"),
    ("2015_2016_stress", "2015-08-01", "2016-06-30"),
    ("2018_selloff", "2018-09-01", "2018-12-31"),
    ("covid_2020", "2020-02-01", "2020-12-31"),
    ("fed_tightening_2022_2024", "2022-01-01", "2024-12-31"),
]

def _equity_path(prices, signal, cost_bps, initial=INITIAL):
    op = prices["tqqq_adj_open"].to_numpy(float)
    cl = prices["tqqq_adj_close"].to_numpy(float)
    overnight = np.zeros(len(prices)); overnight[1:] = op[1:] / cl[:-1] - 1
    intraday = cl / op - 1
    exposure = np.zeros(len(prices)); exposure[1:] = signal[:-1]
    eq = np.full(len(prices), np.nan); eq[0] = initial
    prior_exp = 0.0
    for i in range(1, len(prices)):
        turnover = abs(exposure[i] - prior_exp)
        eq[i] = eq[i-1] * (1 + prior_exp * overnight[i]) * (1 - turnover * cost_bps / 10000) * (1 + exposure[i] * intraday[i])
        prior_exp = exposure[i]
    return eq, exposure

def _max_dd(eq):
    eq = np.asarray(eq, dtype=float)
    peaks = np.maximum.accumulate(eq)
    return float(np.min(eq / peaks - 1.0))

def _one_episode(name, start, end, dates, prices, b0, f75, costs):
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    available = (dates >= start_ts) & (dates <= end_ts)
    if not available.any():
        return {"episode": name, "start": start, "end": end, "status": "UNAVAILABLE_NO_ACTUAL_TQQQ_HISTORY"}
    ids = np.flatnonzero(available)
    lo, hi = int(ids[0]), int(ids[-1])
    # Include one prior close for causal overnight return calculation, but report
    # the equity path only over the fixed episode rows.
    left = max(0, lo - 1)
    rec = {"episode": name, "start": str(dates[lo].date()), "end": str(dates[hi].date()),
           "status": "MEASURED", "sessions": hi-lo+1}
    for label, sig in (("b0", b0), ("f75", f75)):
        for cost in costs:
            path, exp = _equity_path(prices.iloc[left:hi+1], sig[left:hi+1], cost)
            local = path[lo-left:]
            peak = np.maximum.accumulate(local)
            rec[f"{label}_return_{cost}bps"] = float(local[-1] / local[lo-left] - 1)
            rec[f"{label}_maxdd_{cost}bps"] = _max_dd(local)
            rec[f"{label}_avg_exposure"] = float(np.mean(exp[lo-left:]))
            rec[f"{label}_defensive_sessions"] = int(np.sum(exp[lo-left:] < 0.999))
            rec[f"{label}_terminal_equity_{cost}bps"] = float(local[-1])
    # Recovery participation measured relative to the lowest QQQ close in episode.
    q = prices["qqq_adj_close"].iloc[lo:hi+1].to_numpy(float)
    low_local = int(np.argmin(q)); low_global = lo + low_local
    rec["episode_low_date"] = str(dates[low_global].date())
    for horizon in (20, 60):
        stop = min(hi, low_global + horizon)
        rec[f"b0_exposure_next_{horizon}s"] = float(np.mean(b0[low_global:stop+1]))
        rec[f"f75_exposure_next_{horizon}s"] = float(np.mean(f75[low_global:stop+1]))
    for cost in costs:
        rec[f"incremental_equity_{cost}bps"] = rec[f"f75_terminal_equity_{cost}bps"] - rec[f"b0_terminal_equity_{cost}bps"]
        rec[f"incremental_return_{cost}bps"] = rec[f"f75_return_{cost}bps"] - rec[f"b0_return_{cost}bps"]
        rec[f"incremental_maxdd_{cost}bps"] = rec[f"f75_maxdd_{cost}bps"] - rec[f"b0_maxdd_{cost}bps"]
    return rec

def main():
    if not CANON.exists():
        raise RuntimeError(f"Canonical B0 artifact missing: {CANON}")
    digest = hashlib.sha256(CANON.read_bytes()).hexdigest()
    if digest != EXPECTED_HASH:
        raise RuntimeError(f"Canonical B0 artifact hash mismatch: {digest}")
    c = pd.read_csv(CANON, parse_dates=["date"]).set_index("date").sort_index()
    c.index = pd.DatetimeIndex(c.index).normalize()
    required = {"adj_close", "tqqq_adj_open", "tqqq_adj_close", "b0_signal"}
    if not required.issubset(c.columns):
        raise RuntimeError(f"Required canonical columns missing: {sorted(required-set(c.columns))}")
    prices = pd.DataFrame(index=c.index)
    prices["qqq_adj_close"] = c["adj_close"].astype(float)
    prices["tqqq_adj_open"] = c["tqqq_adj_open"].astype(float)
    prices["tqqq_adj_close"] = c["tqqq_adj_close"].astype(float)
    events = build_shock_recovery_events(prices["qqq_adj_close"])
    terminal_i = terminal_unrecovered_shock_start(prices["qqq_adj_close"])
    b0 = build_censored_baseline_signal(len(prices), events, terminal_i)
    if not np.array_equal(b0, c["b0_signal"].to_numpy(float)):
        raise RuntimeError("Canonical B0 signal failed exact reconciliation")
    fed = download_fed()
    lagged = map_fed_state_to_market(fed, prices.index)
    overlay, _ = build_active_tightening_overlay(prices["qqq_adj_close"], lagged)
    f75 = np.minimum(b0, overlay)
    rows = [_one_episode(n,s,e,prices.index,prices,b0,f75,COSTS) for n,s,e in EPISODES]
    report = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "b0_f75_mechanism_episode_attribution.csv"
    report.to_csv(target, index=False, float_format="%.12g")
    measured = report[report.status.eq("MEASURED")]
    summary = {
        "canonical_sha256": digest,
        "episodes_defined": len(EPISODES),
        "episodes_measured": int(len(measured)),
        "episodes_unavailable": int((report.status != "MEASURED").sum()),
        "frozen_candidate": "F75",
        "control": "B0",
        "threshold_tuning": False,
        "episode_return_wins_f75_25bps": int((measured.get("incremental_return_25bps", pd.Series(dtype=float)) > 0).sum()),
        "episode_drawdown_improvements_f75_25bps": int((measured.get("incremental_maxdd_25bps", pd.Series(dtype=float)) > 0).sum()),
        "median_incremental_return_25bps": float(measured["incremental_return_25bps"].median()) if len(measured) else None,
        "median_incremental_equity_25bps": float(measured["incremental_equity_25bps"].median()) if len(measured) else None,
        "report": str(target.relative_to(ROOT)),
        "interpretation": "Episode attribution only; not a promotion decision."
    }
    (OUT / "b0_f75_mechanism_episode_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not len(measured):
        raise RuntimeError("No fixed episode had actual TQQQ history; refusing to claim repeatability.")

if __name__ == "__main__":
    main()
