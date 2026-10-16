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
from fed_dma_chronological_robustness import terminal_unrecovered_shock_start, build_censored_baseline_signal

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

def reconcile_canonical_signal(reconstructed, canonical):
    reconstructed = np.asarray(reconstructed, dtype=float)
    canonical = np.asarray(canonical, dtype=float)
    if reconstructed.shape != canonical.shape:
        raise RuntimeError("B0 canonical signal length mismatch")
    mismatch = np.flatnonzero(reconstructed != canonical)
    if len(mismatch):
        raise RuntimeError(f"B0 canonical historical signal mismatch at index {int(mismatch[0])}")
    return True

def compose_f75_signal(b0, overlay_state, partial_exposure=0.75):
    """Apply the frozen partial-exposure F75 overlay over the B0 baseline."""
    baseline = np.asarray(b0, dtype=float)
    overlay = np.asarray(overlay_state, dtype=float)
    if baseline.shape != overlay.shape:
        raise ValueError("B0 and overlay state must have equal shapes")
    if not np.isfinite(baseline).all() or not np.isin(baseline, [0.0, 1.0]).all():
        raise ValueError("B0 signal must contain only finite binary values")
    if not np.isfinite(overlay).all() or not np.isin(overlay, [0.0, 1.0]).all():
        raise ValueError("overlay state must contain only finite binary values")
    if not np.isfinite(partial_exposure) or not 0.0 <= partial_exposure <= 1.0:
        raise ValueError("partial_exposure must be finite and between 0 and 1")
    overlay_weight = np.where(overlay == 0.0, partial_exposure, 1.0)
    return np.minimum(baseline, overlay_weight)


def validate_existing_ledger(prior, state, ledger_bytes, expected_hash=EXPECTED_HASH):
    """Fail closed if an existing append-only ledger or its state manifest is stale."""
    required = {
        "date", "source_canonical_sha256", "initialization_session",
        "tqqq_adj_open", "tqqq_adj_close", "overnight_return", "intraday_return",
        "b0_signal_close", "f75_overlay_signal_close", "f75_signal_close",
        "b0_exposure", "f75_exposure", "overnight_return", "intraday_return",
        "b0_equity_0bps", "b0_equity_25bps", "b0_equity_50bps",
        "f75_equity_0bps", "f75_equity_25bps", "f75_equity_50bps",
    }
    missing = required - set(prior.columns)
    if missing:
        raise RuntimeError(f"Existing shadow ledger columns missing: {sorted(missing)}")
    dates = pd.to_datetime(prior["date"], errors="coerce", format="mixed")
    if dates.isna().any() or dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise RuntimeError("Existing shadow ledger dates invalid")
    if prior["source_canonical_sha256"].astype(str).ne(expected_hash).any():
        raise RuntimeError("Existing shadow ledger canonical source hash mismatch")
    if state.get("canonical_input_sha256") != expected_hash:
        raise RuntimeError("Shadow state canonical source hash mismatch")
    actual_ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    if state.get("ledger_sha256") != actual_ledger_hash:
        raise RuntimeError("Shadow state ledger SHA-256 mismatch")
    if state.get("last_observation") != dates.iloc[-1].date().isoformat():
        raise RuntimeError("Shadow state tail date does not match ledger")
    if state.get("mode") != "SHADOW_ONLY_NO_ORDERS":
        raise RuntimeError("Shadow state mode is not shadow-only")
    numeric = prior.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise RuntimeError("Existing shadow ledger contains non-finite numeric values")
    if not prior["b0_exposure"].between(0.0, 1.0).all() or not prior["f75_exposure"].between(0.0, 1.0).all():
        raise RuntimeError("Existing shadow ledger contains invalid realized exposure")
    initialized = prior["initialization_session"].astype(bool).to_numpy()
    if len(initialized) == 0 or not initialized[0] or initialized[1:].any():
        raise RuntimeError("Shadow ledger initialization marker is invalid")
    # Reconcile persisted daily return components to adjusted prices, rather
    # than only checking that equity compounds consistently from stored returns.
    # The first row is an explicit zero-return initialization baseline.
    if not np.isclose(float(prior.iloc[0]["overnight_return"]), 0.0, rtol=0, atol=1e-12):
        raise RuntimeError("Shadow ledger initialization overnight return must be zero")
    if not np.isclose(float(prior.iloc[0]["intraday_return"]), 0.0, rtol=0, atol=1e-12):
        raise RuntimeError("Shadow ledger initialization intraday return must be zero")
    adj_open = prior["tqqq_adj_open"].to_numpy(dtype=float)
    adj_close = prior["tqqq_adj_close"].to_numpy(dtype=float)
    if np.any(adj_open <= 0.0) or np.any(adj_close <= 0.0):
        raise RuntimeError("Shadow ledger adjusted TQQQ prices must be positive")
    expected_overnight = np.zeros(len(prior), dtype=float)
    expected_overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    expected_intraday = adj_close / adj_open - 1.0
    expected_intraday[0] = 0.0
    if not np.allclose(prior["overnight_return"].to_numpy(dtype=float), expected_overnight, rtol=1e-9, atol=1e-10):
        raise RuntimeError("Shadow ledger overnight returns do not reconcile to adjusted prices")
    if not np.allclose(prior["intraday_return"].to_numpy(dtype=float), expected_intraday, rtol=1e-9, atol=1e-10):
        raise RuntimeError("Shadow ledger intraday returns do not reconcile to adjusted prices")
    # Treat manifest counters as integrity fields, not merely descriptive metadata.
    # This catches stale or partially migrated state even when the ledger hash matches.
    if type(state.get("sessions_appended_this_run")) is not int or state["sessions_appended_this_run"] < 0:
        raise RuntimeError("Shadow state per-run append counter is invalid")
    if state.get("ledger_rows_total") != len(prior):
        raise RuntimeError("Shadow state total ledger row count mismatch")
    return_bearing_total = int((~prior["initialization_session"].astype(bool)).sum())
    if state.get("return_bearing_sessions_total") != return_bearing_total:
        raise RuntimeError("Shadow state return-bearing session count mismatch")
    if state.get("initialization_date") != dates.iloc[0].date().isoformat():
        raise RuntimeError("Shadow state initialization date mismatch")
    b0_signal = prior["b0_signal_close"].to_numpy(dtype=float)
    overlay_state = prior["f75_overlay_signal_close"].to_numpy(dtype=float)
    f75_signal = prior["f75_signal_close"].to_numpy(dtype=float)
    if not np.isin(b0_signal, [0.0, 1.0]).all() or not np.isin(overlay_state, [0.0, 1.0]).all():
        raise RuntimeError("Existing shadow ledger contains invalid close signals")
    expected_f75 = np.minimum(b0_signal, np.where(overlay_state == 0.0, 0.75, 1.0))
    if not np.array_equal(f75_signal, expected_f75):
        raise RuntimeError("Existing shadow ledger F75 signal violates frozen partial-exposure rule")
    expected_b0_exposure = np.r_[0.0, b0_signal[:-1]]
    expected_f75_exposure = np.r_[0.0, f75_signal[:-1]]
    if not np.allclose(prior["b0_exposure"].to_numpy(dtype=float), expected_b0_exposure, rtol=0, atol=1e-12):
        raise RuntimeError("Existing shadow ledger B0 exposure is not lagged from close signal")
    if not np.allclose(prior["f75_exposure"].to_numpy(dtype=float), expected_f75_exposure, rtol=0, atol=1e-12):
        raise RuntimeError("Existing shadow ledger F75 exposure is not lagged from close signal")
    initialized_equity = prior.iloc[0]
    if not np.isclose(float(initialized_equity["b0_equity_0bps"]), INITIAL) or not np.isclose(float(initialized_equity["f75_equity_0bps"]), INITIAL):
        raise RuntimeError("Shadow ledger initialization equity does not match starting balance")
    for strategy in ("b0", "f75"):
        for cost in COSTS:
            equity = prior[f"{strategy}_equity_{cost}bps"].to_numpy(dtype=float)
            if np.any(equity <= 0.0):
                raise RuntimeError(f"Existing shadow ledger {strategy} equity is non-positive")
            if not np.isclose(equity[0], INITIAL, rtol=0, atol=1e-8):
                raise RuntimeError(f"Shadow ledger {strategy} initialization equity mismatch")
            exposure = prior[f"{strategy}_exposure"].to_numpy(dtype=float)
            overnight = prior["overnight_return"].to_numpy(dtype=float)
            intraday = prior["intraday_return"].to_numpy(dtype=float)
            for i in range(1, len(prior)):
                previous_exposure = exposure[i - 1]
                current_exposure = exposure[i]
                turnover = abs(current_exposure - previous_exposure)
                expected_equity = (
                    equity[i - 1]
                    * (1.0 + previous_exposure * overnight[i])
                    * (1.0 - turnover * cost / 10000.0)
                    * (1.0 + current_exposure * intraday[i])
                )
                if not np.isclose(equity[i], expected_equity, rtol=1e-9, atol=1e-6):
                    raise RuntimeError(f"Existing shadow ledger {strategy} equity accounting mismatch at row {i}, {cost} bp")
    return True


def only_unrecorded_sessions(fresh, prior):
    """Return only sessions newer than the append-only ledger tail."""
    if prior.empty:
        return fresh
    tail = pd.to_datetime(prior["date"], errors="coerce")
    if tail.isna().any():
        raise RuntimeError("Existing shadow ledger contains invalid dates")
    return fresh.loc[fresh.index > tail.max()]


def exclude_current_session(fresh, today=None):
    """Exclude today's possibly incomplete daily bar, including manual intraday runs.

    Use the New York calendar date at call time; a session becomes eligible on
    the following calendar day. This intentionally trades one day of latency
    for avoiding partial-session returns from data vendors.
    """
    if fresh.empty:
        return fresh
    if today is None:
        today = pd.Timestamp.now(tz="America/New_York").date()
    today = pd.Timestamp(today).normalize()
    dates = pd.DatetimeIndex(fresh.index).tz_localize(None).normalize()
    return fresh.loc[dates < today]


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
    # A manual dispatch can occur during market hours; never record today's
    # incomplete daily bar. Today's bar becomes eligible on the next calendar day.
    fresh = exclude_current_session(fresh)
    # Validate the persisted ledger before deciding whether this invocation is a no-op.
    if LEDGER.exists():
        if not STATE.exists():
            raise RuntimeError("Existing shadow ledger has no state manifest")
        prior_bytes = LEDGER.read_bytes()
        prior = pd.read_csv(LEDGER, parse_dates=["date"])
        prior_state = json.loads(STATE.read_text(encoding="utf-8"))
        validate_existing_ledger(prior, prior_state, prior_bytes)
    else:
        if STATE.exists():
            raise RuntimeError("Shadow state exists but its ledger is missing")
        prior = pd.DataFrame()
    # Market feeds overlap the already-recorded tail on every rerun. Keep only
    # strictly newer sessions so scheduled/manual reruns are idempotent.
    fresh = only_unrecorded_sessions(fresh, prior)
    if fresh.empty:
        print("No new completed market sessions after frozen cutoff and ledger tail; no ledger change.")
        return
    if fresh.index.has_duplicates or not fresh.index.is_monotonic_increasing: raise RuntimeError("Fresh market dates invalid")
    old = c.rename(columns={"adj_close":"qqq_adj_close"})[["qqq_adj_close","tqqq_adj_open","tqqq_adj_close"]].copy()
    prices = pd.concat([old, fresh]).sort_index()
    if prices.index.has_duplicates: raise RuntimeError("Frozen/fresh date overlap")
    # Rebuild baseline across the entire combined history and prove frozen values agree.
    events = build_shock_recovery_events(prices["qqq_adj_close"])
    terminal_i = terminal_unrecovered_shock_start(prices["qqq_adj_close"])
    b0 = build_censored_baseline_signal(len(prices), events, terminal_i)
    canonical_signal = c["b0_signal"].to_numpy(float)
    reconcile_canonical_signal(b0[:len(canonical_signal)], canonical_signal)
    fed = download_fed()
    lagged_fed = map_fed_state_to_market(fed, prices.index)
    overlay, _ = build_active_tightening_overlay(prices["qqq_adj_close"], lagged_fed)
    # F75 is a partial-exposure overlay, not a full exit: 75% while active,
    # capped by B0's independent defense. Keep this identical to the frozen audit.
    f75 = compose_f75_signal(b0, overlay, partial_exposure=0.75)
    # Each new session's close signal is recorded today; exposure is the prior close's signal.
    adj_open = prices["tqqq_adj_open"].to_numpy(float)
    adj_close = prices["tqqq_adj_close"].to_numpy(float)
    overnight = np.zeros(len(prices)); overnight[1:] = adj_open[1:] / adj_close[:-1] - 1
    intraday = adj_close / adj_open - 1
    # Existing ledger carries shadow account state forward. Never rewrite past rows.
    if not prior.empty:
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
        initializing = (i == first_new and prior.empty)
        row={"date":d.date().isoformat(),"qqq_adj_close":float(prices.qqq_adj_close.iloc[i]),
             "tqqq_adj_open":float(adj_open[i]),"tqqq_adj_close":float(adj_close[i]),
             "qqq_dma_200":float(prices.qqq_adj_close.rolling(DMA,min_periods=DMA).mean().iloc[i]),
             "lagged_fed_state":str(lagged_fed.iloc[i]),"b0_signal_close":float(b0[i]),
             "f75_overlay_signal_close":float(overlay[i]),"f75_signal_close":float(f75[i]),
             "b0_exposure":0.0 if initializing else (float(b0[i-1]) if i>0 else 0.0),
             "f75_exposure":0.0 if initializing else (float(f75[i-1]) if i>0 else 0.0),
             "overnight_return":0.0 if initializing else float(overnight[i]),
             "intraday_return":0.0 if initializing else float(intraday[i]),
             "source_canonical_sha256":digest,
             "initialization_session":bool(initializing)}
        for strategy, sig in (("B0",b0),("F75",f75)):
            exposure=0.0 if initializing else (float(sig[i-1]) if i>0 else 0.0)
            turnover=0.0 if initializing else abs(exposure-previous_exposure[strategy])
            for b in COSTS:
                if not initializing:
                    # Overnight on prior exposure, charge cost at open, intraday on current exposure.
                    v=eq[(strategy,b)]*(1+previous_exposure[strategy]*overnight[i])*(1-turnover*b/10000)*(1+exposure*intraday[i])
                    eq[(strategy,b)]=v
                row[f"{strategy.lower()}_equity_{b}bps"]=eq[(strategy,b)]
            previous_exposure[strategy]=exposure
        rows.append(row)
    new=pd.DataFrame(rows)
    # A new observation is accepted only if each daily return and balance is finite.
    numeric=new.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all(): raise RuntimeError("Non-finite shadow ledger values")
    if prior.empty: combined=new
    else: combined=pd.concat([prior,new],ignore_index=True)
    if combined["date"].duplicated().any(): raise RuntimeError("Shadow ledger dates duplicated")
    combined.to_csv(LEDGER,index=False,float_format="%.12g")
    # Make the manifest unambiguous: separate this invocation's append count
    # from the cumulative ledger length and usable return-bearing observations.
    initialization_dates = combined.loc[combined["initialization_session"].astype(bool), "date"]
    state={"canonical_input_sha256":digest,"frozen_cutoff":cutoff.date().isoformat(),
           "last_observation":str(combined.date.iloc[-1]),
           "sessions_appended_this_run":len(new),
           "ledger_rows_total":len(combined),
           "return_bearing_sessions_total":int((~combined["initialization_session"].astype(bool)).sum()),
           "initialization_date":str(initialization_dates.iloc[0]) if len(initialization_dates) else None,
           "ledger_sha256":hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
           "mode":"SHADOW_ONLY_NO_ORDERS","cost_sensitivity_bps":list(COSTS)}
    STATE.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(state,indent=2))
if __name__ == "__main__": main()
