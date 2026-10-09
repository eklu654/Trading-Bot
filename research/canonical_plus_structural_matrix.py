"""Combine the canonical QQQ -4.5% shock / +10% recovery rule with the
structural/fast-shock matrix. The matrix is an overlay only: target exposure is
min(canonical exposure, overlay exposure), so it can never add risk.

Synthetic pre-TQQQ results are explicitly hypothetical, not actual fund returns.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns
from tqqq_canonical_same_input_reconciliation import (
    INITIAL, SHOCK, RECOVERY, make_frozen_input, build_events_and_signal
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START, END = "1999-03-10", "2026-10-08"
STRUCTURAL_DMAS = (100, 150, 200)
FAST_DMAS = (50, 100)
STRUCTURAL_EXPOSURES = (0.25, 0.50, 0.75)
RET_THRESHOLDS = (-0.15, -0.20)
DD_THRESHOLDS = (-0.20, -0.25)
VIX_THRESHOLDS = (28.0, 30.0)


def download(symbol, start=START):
    x = yf.download(symbol, start=start, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def market_signal_frame():
    q = download("QQQ")
    q = q.rename(columns={"Open":"open", "Close":"close", "Adj Close":"adj_close"})
    q = q.dropna(subset=["open", "close", "adj_close"])
    for d in (50, 100, 150, 200):
        q[f"dma{d}"] = q.adj_close.rolling(d, min_periods=d).mean()
    q["ret63"] = q.adj_close / q.adj_close.shift(63) - 1.0
    q["dd252"] = q.adj_close / q.adj_close.rolling(252, min_periods=252).max() - 1.0
    v = download("^VIX")[["Close"]].rename(columns={"Close":"vix"})
    q = q.join(v, how="left")
    q["vix"] = q.vix.ffill()
    return q.dropna(subset=["vix"])


def matrix_signal(q, sd, fd, rt, dt, vt, exposure, fast_only=False):
    ma, fast = q[f"dma{sd}"], q[f"dma{fd}"]
    armed = hard = False
    out = []
    for px, m, f, r, d, v in zip(q.adj_close.to_numpy(), ma.to_numpy(),
                                  fast.to_numpy(), q.ret63.to_numpy(),
                                  q.dd252.to_numpy(), q.vix.to_numpy()):
        if not np.isfinite(m) or not np.isfinite(f):
            out.append(1.0)
            continue
        shock = (px < f and ((np.isfinite(r) and r <= rt) or
                             (np.isfinite(d) and d <= dt) or v >= vt))
        structural = (px < m and f < m)
        enter = shock if fast_only else (structural or shock)
        if not armed and enter:
            armed = True
            hard = bool(shock)
        elif armed:
            if px >= m:
                armed = hard = False
            elif shock:
                hard = True
        out.append(0.0 if hard else (exposure if armed else 1.0))
    return pd.Series(out, index=q.index, dtype=float)


def metrics(name, source, signal, frame, overnight, intraday, dates):
    ret = next_open_daily_returns(signal, overnight, intraday)
    eq = INITIAL * np.cumprod(1.0 + ret)
    dd = eq / np.maximum.accumulate(eq) - 1.0
    years = (dates[-1] - dates[0]).days / 365.25
    roll = pd.Series(np.log1p(ret)).rolling(252, min_periods=252).sum().dropna()
    row = {
        "source": source, "strategy": name, "start": dates[0].date().isoformat(),
        "end": dates[-1].date().isoformat(), "rows": len(dates),
        "initial_balance": INITIAL, "final_balance": float(eq[-1]),
        "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "worst_rolling_252_session_return": float(np.expm1(roll.min())) if len(roll) else np.nan,
        "mean_target_exposure": float(np.mean(signal)),
        "defensive_sessions": int(np.sum(signal < 1.0)),
        "exposure_changes": int(np.sum(np.abs(np.diff(signal, prepend=signal[0])) > 1e-12)),
    }
    for label, a, b in [("dotcom", "2000-01-01", "2002-12-31"),
                         ("gfc", "2007-10-01", "2009-12-31"),
                         ("covid", "2020-02-19", "2020-07-31"),
                         ("inflation_2022", "2022-01-03", "2022-12-30")]:
        mask = (dates >= a) & (dates <= b)
        if mask.any():
            local = eq[mask]
            row[label + "_return"] = float(local[-1] / (eq[np.flatnonzero(mask)[0]-1] if np.flatnonzero(mask)[0] else INITIAL) - 1)
            row[label + "_max_dd"] = float((local / np.maximum.accumulate(local) - 1).min())
    return row, eq


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = market_signal_frame()
    q = q.loc[(q.index >= START) & (q.index < END)].copy()
    # Synthetic daily-reset 3x QQQ proxy, constructed using the same convention
    # as the preceding matrix study; do not call it realized TQQQ performance.
    q["adj_open"] = q.open * q.adj_close / q.close
    q["overnight"] = ((1 + 3 * (q.adj_open / q.adj_close.shift(1) - 1)).clip(lower=0) - 1).fillna(0)
    q["intraday"] = ((1 + 3 * (q.adj_close / q.adj_open - 1)).clip(lower=0) - 1).fillna(0)
    rows = []
    detailed = []
    # Historical synthetic series, 1999 onward.
    ev, b0 = build_events_and_signal(q.adj_close)
    base = b0.astype(float)
    common_on = q.overnight.to_numpy(float); common_in = q.intraday.to_numpy(float)
    r, eq = metrics("B0_canonical_shock_recovery", "synthetic_qqq_3x", base, q, common_on, common_in, q.index)
    rows.append(r)
    for sd in STRUCTURAL_DMAS:
      for fd in FAST_DMAS:
       for rt in RET_THRESHOLDS:
        for dt in DD_THRESHOLDS:
         for vt in VIX_THRESHOLDS:
          for exp in STRUCTURAL_EXPOSURES:
            mat = matrix_signal(q, sd, fd, rt, dt, vt, exp, False).to_numpy(float)
            fast = matrix_signal(q, sd, fd, rt, dt, vt, exp, True).to_numpy(float)
            for kind, overlay in [("structural_plus_fast", mat), ("fast_shock_only", fast)]:
                combined = np.minimum(base, overlay)
                if not np.all(combined <= base + 1e-12):
                    raise AssertionError("Overlay increased canonical exposure")
                r, eq = metrics(kind, "synthetic_qqq_3x", combined, q, common_on, common_in, q.index)
                r.update({"structural_dma":sd,"fast_dma":fd,"ret63_threshold":rt,
                          "dd252_threshold":dt,"vix_threshold":vt,"structural_exposure":exp})
                rows.append(r)
    # Actual TQQQ, exactly the frozen aligned input used by the canonical comparison.
    x, frozen_path = make_frozen_input()
    # Align QQQ signal features onto frozen dates; indicators are computed with prior history.
    # Retain pre-inception QQQ history for rolling lookbacks, but overwrite
    # every live-TQQQ date with the exact frozen QQQ closes used by B0.
    aq = q.reindex(q.index.union(x.index)).sort_index().ffill()
    aq.loc[x.index, "adj_close"] = x.qqq_adj_close.to_numpy(float)
    for d in (50, 100, 150, 200):
        aq[f"dma{d}"] = aq.adj_close.rolling(d, min_periods=d).mean()
    aq["ret63"] = aq.adj_close / aq.adj_close.shift(63) - 1.0
    aq["dd252"] = aq.adj_close / aq.adj_close.rolling(252, min_periods=252).max() - 1.0
    events, b0_actual = build_events_and_signal(x.qqq_adj_close.astype(float))
    base_actual = b0_actual.astype(float)
    on = np.zeros(len(x)); intr = np.zeros(len(x))
    on[1:] = x.tqqq_adj_open.to_numpy(float)[1:] / x.tqqq_adj_close.to_numpy(float)[:-1] - 1
    intr[:] = x.tqqq_adj_close.to_numpy(float) / x.tqqq_adj_open.to_numpy(float) - 1
    on[0] = intr[0] = 0
    r, _ = metrics("B0_canonical_shock_recovery", "actual_tqqq", base_actual, x, on, intr, x.index)
    rows.append(r)
    # Feature series are calculated over long QQQ history, then aligned to TQQQ dates.
    for sd in STRUCTURAL_DMAS:
      for fd in FAST_DMAS:
       for rt in RET_THRESHOLDS:
        for dt in DD_THRESHOLDS:
         for vt in VIX_THRESHOLDS:
          for exp in STRUCTURAL_EXPOSURES:
            # Recreate indicator frame with the full history, align only after calculating features.
            feat = q.reindex(q.index.union(x.index)).sort_index().ffill().reindex(x.index)
            mat = matrix_signal(feat, sd, fd, rt, dt, vt, exp, False).to_numpy(float)
            fast = matrix_signal(feat, sd, fd, rt, dt, vt, exp, True).to_numpy(float)
            for kind, overlay in [("structural_plus_fast", mat), ("fast_shock_only", fast)]:
                combined = np.minimum(base_actual, overlay)
                if not np.all(combined <= base_actual + 1e-12):
                    raise AssertionError("Overlay increased canonical exposure")
                r, _ = metrics(kind, "actual_tqqq", combined, x, on, intr, x.index)
                r.update({"structural_dma":sd,"fast_dma":fd,"ret63_threshold":rt,
                          "dd252_threshold":dt,"vix_threshold":vt,"structural_exposure":exp})
                rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "canonical_plus_structural_matrix_results.csv", index=False)
    digest = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    manifest = {
      "status":"PASS", "start_synthetic":q.index[0].date().isoformat(),
      "end_synthetic":q.index[-1].date().isoformat(), "synthetic_rows":len(q),
      "start_actual":x.index[0].date().isoformat(), "end_actual":x.index[-1].date().isoformat(),
      "actual_rows":len(x), "initial_balance":INITIAL, "shock_threshold":SHOCK,
      "recovery_threshold":RECOVERY, "actual_frozen_input_sha256":digest,
      "actual_event_count":len(events), "rule":"combined_signal=min(B0_signal,matrix_overlay_signal)",
      "matrix_combinations_per_source":len(STRUCTURAL_DMAS)*len(FAST_DMAS)*len(RET_THRESHOLDS)*len(DD_THRESHOLDS)*len(VIX_THRESHOLDS)*len(STRUCTURAL_EXPOSURES),
      "overlay_ablations":["structural_plus_fast","fast_shock_only"],
      "synthetic_caveat":"Hypothetical daily-reset 3x QQQ proxy; not actual TQQQ history or fully financed/fee-calibrated fund simulation."
    }
    (OUT / "canonical_plus_structural_matrix_manifest.json").write_text(json.dumps(manifest, indent=2))
    # Deterministic ranking print for easy audit.
    cols=["source","strategy","final_balance","cagr","max_drawdown","worst_rolling_252_session_return"]
    print(json.dumps(manifest, indent=2))
    print("\nTOP 10 PER SOURCE/OVERLAY")
    print(out.sort_values("final_balance", ascending=False).groupby(["source","strategy"], group_keys=False).head(10)[cols+["structural_dma","fast_dma","ret63_threshold","dd252_threshold","vix_threshold","structural_exposure"]].to_string(index=False))

if __name__ == "__main__":
    main()
