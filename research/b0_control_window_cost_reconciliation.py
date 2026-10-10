"""Reconcile B0 balances across evaluation windows and cost assumptions.

Uses the canonical frozen-input builder and B0 event builder. Compares:
- inception-start equity at 0/10/25/50 bps;
- post-250-session equity reset to $5,000 at each cost;
- inception-grown equity merely viewed from the warm-up date (no reset).

This is a control accounting audit, not a strategy search.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

try:
    from .causal_execution import next_open_daily_returns, next_open_cost_equity
    from .tqqq_canonical_same_input_reconciliation import (
        INITIAL, make_frozen_input, build_events_and_signal
    )
except ImportError:
    from causal_execution import next_open_daily_returns, next_open_cost_equity
    from tqqq_canonical_same_input_reconciliation import (
        INITIAL, make_frozen_input, build_events_and_signal
    )

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
COSTS = (0, 10, 25, 50)
WARMUP_SESSIONS = 250
COMPARISON_END = pd.Timestamp("2026-10-02")


def make_legs(frame):
    t_close = frame.tqqq_adj_close.to_numpy(dtype=float)
    t_open = frame.tqqq_adj_open.to_numpy(dtype=float)
    overnight = np.zeros(len(frame), dtype=float)
    intraday = np.zeros(len(frame), dtype=float)
    overnight[1:] = t_open[1:] / t_close[:-1] - 1.0
    intraday[:] = t_close / t_open - 1.0
    overnight[0] = intraday[0] = 0.0
    return overnight, intraday


def metric_row(dates, equity, cost_bps, view, start_balance):
    dates = pd.DatetimeIndex(dates)
    equity = np.asarray(equity, dtype=float)
    if len(dates) != len(equity) or len(equity) < 2:
        raise ValueError("dates/equity must align and contain at least two rows")
    peak = np.maximum.accumulate(equity)
    years = (dates[-1] - dates[0]).days / 365.25
    if years <= 0 or equity[-1] <= 0:
        raise ValueError("invalid date span or terminal equity")
    return {
        "view": view,
        "cost_bps": int(cost_bps),
        "start_date": dates[0].date().isoformat(),
        "end_date": dates[-1].date().isoformat(),
        "observations": int(len(dates)),
        "starting_balance": float(start_balance),
        "ending_balance": float(equity[-1]),
        "cagr": float((equity[-1] / start_balance) ** (1.0 / years) - 1.0),
        "max_drawdown": float(np.min(equity / peak - 1.0)),
        "minimum_equity": float(np.min(equity)),
    }


def reconcile(frame):
    frame = frame.sort_index()
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("frozen input dates must be unique and ascending")
    events, signal = build_events_and_signal(frame.qqq_adj_close.astype(float))
    signal = np.asarray(signal, dtype=float)
    overnight, intraday = make_legs(frame)
    warm = WARMUP_SESSIONS - 1
    if len(frame) <= WARMUP_SESSIONS:
        raise ValueError("input too short for requested warm-up")

    rows = []
    paths = []
    for bps in COSTS:
        full = next_open_cost_equity(signal, overnight, intraday, bps, INITIAL)
        if bps == 0:
            plain = INITIAL * np.cumprod(
                1.0 + next_open_daily_returns(signal, overnight, intraday)
            )
            if not np.allclose(full, plain, rtol=1e-11, atol=1e-7):
                raise AssertionError("0-bps cost engine does not match causal return engine")

        # Warm-up reset: evaluate only from the first post-warm-up date with fresh capital.
        w_signal = signal[warm:]
        w_on, w_in = overnight[warm:], intraday[warm:]
        reset = next_open_cost_equity(w_signal, w_on, w_in, bps, INITIAL)

        # Warm-up carried: same dates, but retain the equity accumulated since inception.
        carried = full[warm:].copy()
        views = (
            ("inception_full", frame.index, full, INITIAL),
            ("warmup_reset", frame.index[warm:], reset, INITIAL),
            ("warmup_carried_equity", frame.index[warm:], carried, float(full[warm])),
        )
        for view, dates, eq, start_balance in views:
            rows.append(metric_row(dates, eq, bps, view, start_balance))
            paths.append(pd.DataFrame({
                "date": dates,
                "view": view,
                "cost_bps": bps,
                "signal_at_close": signal if view == "inception_full" else w_signal,
                "equity": eq,
            }))

        # Recompute the same summaries at the hybrid experiments' exclusive-end
        # convention (last observation on or before 2026-10-02), using identical
        # signals/return legs and without refitting or redownloading inputs.
        for view, dates, eq, start_balance in views:
            mask = dates <= COMPARISON_END
            if not np.any(mask):
                continue
            rows.append(metric_row(
                dates[mask], np.asarray(eq)[mask], bps,
                view + "_through_2026-10-02", start_balance
            ))

    summary = pd.DataFrame(rows)
    path = pd.concat(paths, ignore_index=True)
    return summary, path, events


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frame, frozen_path = make_frozen_input()
    summary, paths, events = reconcile(frame)
    summary_path = OUT / "b0_control_window_cost_reconciliation_summary.csv"
    paths_path = OUT / "b0_control_window_cost_reconciliation_paths.csv"
    event_path = OUT / "b0_control_window_cost_reconciliation_events.csv"
    manifest_path = OUT / "b0_control_window_cost_reconciliation_manifest.json"
    summary.to_csv(summary_path, index=False, float_format="%.15g")
    paths.to_csv(paths_path, index=False, float_format="%.15g")
    pd.DataFrame([
        {"shock_date": frame.index[s].date().isoformat(),
         "low_date": frame.index[l].date().isoformat(),
         "recovery_decision_date": frame.index[r].date().isoformat()}
        for s, l, r in events
    ]).to_csv(event_path, index=False)

    manifest = {
        "status": "PASS",
        "frozen_input": frozen_path.name,
        "frozen_input_sha256": hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
        "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        "paths_sha256": hashlib.sha256(paths_path.read_bytes()).hexdigest(),
        "events_sha256": hashlib.sha256(event_path.read_bytes()).hexdigest(),
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "rows": len(frame),
        "initial_balance": INITIAL,
        "event_count": len(events),
        "warmup_sessions": WARMUP_SESSIONS,
        "warmup_date": frame.index[WARMUP_SESSIONS - 1].date().isoformat(),
        "cost_bps": list(COSTS),
        "views": ["inception_full", "warmup_reset", "warmup_carried_equity"],
        "checks": {
            "zero_cost_engine_matches_plain_causal_equity": True,
            "same_signal_and_frozen_input_for_all_views": True,
            "actual_tqqq_only": True,
        },
        "interpretation": "Warm-up-reset and inception-start balances are different experiments; carried-equity view isolates truncation without resetting capital.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nB0 CONTROL RECONCILIATION")
    print(summary.to_string(index=False))
    print("\nPASS: B0 signal and frozen input held fixed across window/cost views.")


if __name__ == "__main__":
    main()
