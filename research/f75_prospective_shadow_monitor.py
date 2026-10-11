"""Append-only, shadow-only B0 vs F75 daily monitor.

No broker connectivity or order submission. Frozen historical rows are verified
against the canonical matrix artifact; only observations after its final date
are appended. The ledger is committed by the scheduled workflow.
"""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from canonical_shock_recovery_fed_dma_overlay import (
    download_fed, map_fed_state_to_market, build_shock_recovery_events,
    build_baseline_signal, DMA, SHOCK, RECOVERY,
)
from canonical_shock_recovery_active_tightening_overlay import build_active_tightening_overlay

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
CANON = DATA / "canonical_b0" / "tqqq_actual_partial_dma_frozen_input.csv"
LEDGER = DATA / "f75_shadow_daily_ledger.csv"
STATE = DATA / "f75_shadow_state.json"
EXPECTED_HASH = "6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55"
INITIAL = 5000.0
COSTS = (0, 25, 50)

def market(symbol, start):
    x = yf.download(symbol, start=start, auto_adjust=False, progress=False, actions=False)
    if x.empty: raise RuntimeError(f"No market rows for {symbol}")
    if isinstance(x.columns, pd.MultiIndex): x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None).normalize()
    return x.sort_index()

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    if not CANON.exists(): raise RuntimeError("Canonical frozen input is missing")
    digest = hashlib.sha256(CANON.read_bytes()).hexdigest()
    if digest != EXPECTED_HASH: raise RuntimeError(f"Canonical input hash mismatch: {digest}")
    c = pd.read_csv(CANON, parse_dates=["date"]).set_index("date").sort_index()
    c.index = pd.DatetimeIndex(c.index).normalize()
    required = {"adj_close", "tqqq_adj_open", "tqqq_adj_close", "b0_signal"}
    if not required.issubset(c.columns): raise RuntimeError(f"Canonical columns missing: {sorted(required-set(c.columns))}")
    if c.index.has_duplicates or not c.index.is_monotonic_increasing: raise RuntimeError("Canonical dates invalid")
    cutoff = c.index[-1]
    q = market("QQQ", str(cutoff.date()))
    t = market("TQQQ", str(cutoff.date()))
    if "Adj Close" not in q or "Open" not in t or "Adj Close" not in t or "Close" not in t:
        raise RuntimeError("Market source lacks required adjusted price fields")
    # Include the cutoff row from the frozen file; use fresh data only after cutoff.
    fresh = pd.DataFrame(index=q.index.intersection(t.index))
    fresh["qqq_adj_close"] = q["Adj Close"].reindex(fresh.index).astype(float)
    fresh["tqqq_adj_open"] = (t["Open"] * t["Adj Close"] / t["Close"]).reindex(fresh.index).astype(float)
    fresh["tqqq_adj_close"] = t["Adj Close"].reindex(fresh.index).astype(float)
    fresh = fresh.loc[fresh.index > cutoff].dropna()
    if fresh.empty:
        print("No new completed market sessions after frozen cutoff; no ledger change.")
        return
    if fresh.index.has_duplicates or not fresh.index.is_monotonic_increasing: raise RuntimeError("Fresh market dates invalid")
    old = c.rename(columns={"adj_close":"qqq_adj_close"})[["qqq_adj_close","tqqq_adj_open","tqqq_adj_close"]].copy()
    prices = pd.concat([old, fresh]).sort_index()
    if prices.index.has_duplicates: raise RuntimeError("Frozen/fresh date overlap")
    # Rebuild baseline across the entire combined history and prove frozen values agree.
    events = build_shock_recovery_events(prices["qqq_adj_close"])
    b0 = build_baseline_signal(len(prices), events)
    canonical_signal = c["b0_signal"].to_numpy(float)
    if len(b0[:len(canonical_signal)]) != len(canonical_signal) or not np.array_equal(b0[:len(canonical_signal)], canonical_signal):
        raise RuntimeError("B0 canonical historical signal reconciliation failed")
    fed = download_fed()
    lagged_fed = map_fed_state_to_market(fed, prices.index)
    overlay, _ = build_active_tightening_overlay(prices["qqq_adj_close"], lagged_fed)
    f75 = np.minimum(b0, overlay)
    # Each new session's close signal is recorded today; exposure is the prior close's signal.
    adj_open = prices["tqqq_adj_open"].to_numpy(float)
    adj_close = prices["tqqq_adj_close"].to_numpy(float)
    overnight = np.zeros(len(prices)); overnight[1:] = adj_open[1:] / adj_close[:-1] - 1
    intraday = adj_close / adj_open - 1
    # Existing ledger carries shadow account state forward. Never rewrite past rows.
    prior = pd.read_csv(LEDGER, parse_dates=["date"]) if LEDGER.exists() else pd.DataFrame()
    if not prior.empty:
        if prior["date"].duplicated().any(): raise RuntimeError("Existing ledger has duplicate dates")
        if prior["date"].max() >= fresh.index.min(): raise RuntimeError("New sessions overlap or precede ledger tail")
        last = prior.sort_values("date").iloc[-1]
        eq = {("B0", b): float(last[f"b0_equity_{b}bps"]) for b in COSTS}
        eq.update({("F75", b): float(last[f"f75_equity_{b}bps"]) for b in COSTS})
        previous_exposure = {"B0": float(last["b0_exposure"]), "F75": float(last["f75_exposure"])}
    else:
        eq = {(s,b): INITIAL for s in ("B0","F75") for b in COSTS}
        previous_exposure = {"B0": 0.0, "F75": 0.0}
    rows=[]
    ix = prices.index
    first_new = ix.get_loc(fresh.index[0])
    for i in range(first_new, len(ix)):
        d=ix[i]
        row={"date":d.date().isoformat(),"qqq_adj_close":float(prices.qqq_adj_close.iloc[i]),
             "tqqq_adj_open":float(adj_open[i]),"tqqq_adj_close":float(adj_close[i]),
             "qqq_dma_200":float(prices.qqq_adj_close.rolling(DMA,min_periods=DMA).mean().iloc[i]),
             "lagged_fed_state":str(lagged_fed.iloc[i]),"b0_signal_close":float(b0[i]),
             "f75_overlay_signal_close":float(overlay[i]),"f75_signal_close":float(f75[i]),
             "b0_exposure":float(b0[i-1]) if i>0 else 0.0,
             "f75_exposure":float(f75[i-1]) if i>0 else 0.0,
             "overnight_return":float(overnight[i]),"intraday_return":float(intraday[i]),
             "source_canonical_sha256":digest}
        for s, sig in (("B0",b0),("F75",f75)):
            exposure=float(sig[i-1]) if i>0 else 0.0
            turnover=abs(exposure-previous_exposure[s])
            for b in COSTS:
                # Overnight on prior exposure, charge cost at open, intraday on current exposure.
                v=eq[(s,b)]*(1+previous_exposure[s]*overnight[i])*(1-turnover*b/10000)*(1+exposure*intraday[i])
                eq[(s,b)]=v; row[f"{s.lower()}_equity_{b}bps"]=v
            previous_exposure[s]=exposure
        rows.append(row)
    new=pd.DataFrame(rows)
    # A new observation is accepted only if each daily return and balance is finite.
    numeric=new.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all(): raise RuntimeError("Non-finite shadow ledger values")
    if prior.empty: combined=new
    else: combined=pd.concat([prior,new],ignore_index=True)
    if combined["date"].duplicated().any(): raise RuntimeError("Shadow ledger dates duplicated")
    combined.to_csv(LEDGER,index=False,float_format="%.12g")
    state={"canonical_input_sha256":digest,"frozen_cutoff":cutoff.date().isoformat(),
           "last_observation":new.date.iloc[-1],"sessions_appended":len(new),
           "ledger_sha256":hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
           "mode":"SHADOW_ONLY_NO_ORDERS","cost_sensitivity_bps":list(COSTS)}
    STATE.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(state,indent=2))
if __name__ == "__main__": main()
