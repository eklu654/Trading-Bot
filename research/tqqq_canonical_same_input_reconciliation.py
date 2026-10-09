"""One-download, frozen-input reconciliation for canonical QQQ shock/recovery.

Both engines consume the same CSV reloaded from disk:
- shared causal_execution engine
- independently coded day-by-day execution loop

The run fails if event ledgers, daily returns, or equity curves disagree.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "2010-01-01"
END = "2026-10-08"
INITIAL = 5000.0
SHOCK = -0.045
RECOVERY = 0.10


def download(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna()


def make_frozen_input():
    q = download("QQQ")
    t = download("TQQQ")
    idx = q.index.intersection(t.index)
    q = q.reindex(idx).dropna()
    t = t.reindex(idx).dropna()
    idx = q.index.intersection(t.index)
    q, t = q.reindex(idx), t.reindex(idx)
    if len(idx) == 0 or not q.index.equals(t.index):
        raise RuntimeError("No aligned QQQ/TQQQ observations")

    frame = pd.DataFrame(index=idx)
    for col in ("Open", "High", "Low", "Close", "Adj Close", "Volume"):
        frame["qqq_" + col.lower().replace(" ", "_")] = q[col].astype(float)
        frame["tqqq_" + col.lower().replace(" ", "_")] = t[col].astype(float)
    frame["qqq_adj_open"] = frame.qqq_open * frame.qqq_adj_close / frame.qqq_close
    frame["tqqq_adj_open"] = frame.tqqq_open * frame.tqqq_adj_close / frame.tqqq_close
    frame.index.name = "date"
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "tqqq_canonical_frozen_common_input.csv"
    frame.to_csv(path, index_label="date", float_format="%.12g")
    frozen = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    if frozen.index.has_duplicates or not frozen.index.is_monotonic_increasing:
        raise RuntimeError("Frozen date index is invalid")
    return frozen, path


def build_events_and_signal(close):
    ret = close.pct_change().fillna(0.0).to_numpy()
    px = close.to_numpy(dtype=float)
    events = []
    signal = np.ones(len(close), dtype=float)
    armed = False
    shock_i = low_i = None
    for i in range(1, len(close)):
        if not armed and ret[i] <= SHOCK:
            armed = True
            shock_i = i
            low_i = i
        if armed:
            if px[i] < px[low_i]:
                low_i = i
            if px[i] / px[low_i] - 1.0 >= RECOVERY:
                events.append((shock_i, low_i, i))
                signal[shock_i:i] = 0.0
                armed = False
    return events, signal


def independently_rebuild_events(close):
    """Separate event-state implementation used only for reconciliation."""
    px = close.to_numpy(dtype=float)
    daily = close.pct_change().fillna(0.0).to_numpy()
    event_rows = []
    position = 1.0
    trigger = low = None
    signal = np.ones(len(close), dtype=float)
    for i, r in enumerate(daily):
        if i == 0:
            continue
        if position == 1.0 and r <= SHOCK:
            position = 0.0
            trigger = i
            low = i
        if position == 0.0:
            if px[i] < px[low]:
                low = i
            if px[i] / px[low] - 1.0 >= RECOVERY:
                event_rows.append((trigger, low, i))
                position = 1.0
        if position == 0.0:
            signal[trigger:i + 1] = 0.0
    return event_rows, signal


def independent_daily_returns(signal, overnight, intraday):
    """Explicit independent loop: close[t] signal executes at open[t+1]."""
    n = len(signal)
    result = np.zeros(n, dtype=float)
    for i in range(1, n):
        overnight_position = signal[i - 2] if i > 1 else 0.0
        intraday_position = signal[i - 1] if i > 0 else 0.0
        result[i] = ((1.0 + overnight_position * overnight[i]) *
                     (1.0 + intraday_position * intraday[i]) - 1.0)
    return result


def metrics(eq, dates):
    peak = np.maximum.accumulate(eq)
    years = (dates[-1] - dates[0]).days / 365.25
    return {
        "final_balance": float(eq[-1]),
        "cagr": float((eq[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float((eq / peak - 1.0).min()),
    }


def main():
    x, frozen_path = make_frozen_input()
    close = x.qqq_adj_close.astype(float)
    events, signal = build_events_and_signal(close)
    independent_events, independent_signal = independently_rebuild_events(close)
    if events != independent_events:
        raise AssertionError(f"Event ledger mismatch: {events} != {independent_events}")
    if not np.array_equal(signal, independent_signal):
        raise AssertionError("Independent event builders produced different signal arrays")
    t_adj_close = x.tqqq_adj_close.to_numpy(dtype=float)
    t_adj_open = x.tqqq_adj_open.to_numpy(dtype=float)
    overnight = np.zeros(len(x), dtype=float)
    intraday = np.zeros(len(x), dtype=float)
    overnight[1:] = t_adj_open[1:] / t_adj_close[:-1] - 1.0
    intraday[:] = t_adj_close / t_adj_open - 1.0
    overnight[0] = 0.0
    intraday[0] = 0.0

    shared_daily = next_open_daily_returns(signal, overnight, intraday)
    independent_daily = independent_daily_returns(independent_signal, overnight, intraday)
    if not np.allclose(shared_daily, independent_daily, rtol=1e-12, atol=1e-12):
        i = int(np.flatnonzero(~np.isclose(shared_daily, independent_daily,
                                          rtol=1e-12, atol=1e-12))[0])
        raise AssertionError(f"Daily return mismatch at {x.index[i]}: "
                             f"{shared_daily[i]} vs {independent_daily[i]}")

    shared_eq = INITIAL * np.cumprod(1.0 + shared_daily)
    independent_eq = INITIAL * np.cumprod(1.0 + independent_daily)
    if not np.allclose(shared_eq, independent_eq, rtol=1e-12, atol=1e-8):
        i = int(np.flatnonzero(~np.isclose(shared_eq, independent_eq,
                                          rtol=1e-12, atol=1e-8))[0])
        raise AssertionError(f"Equity mismatch at {x.index[i]}: "
                             f"{shared_eq[i]} vs {independent_eq[i]}")

    bh_daily = next_open_daily_returns(np.ones(len(x)), overnight, intraday)
    bh_eq = INITIAL * np.cumprod(1.0 + bh_daily)
    summary = pd.DataFrame([
        {"strategy": "canonical_shock_recovery", "engine": "shared",
         **metrics(shared_eq, x.index)},
        {"strategy": "canonical_shock_recovery", "engine": "independent_loop",
         **metrics(independent_eq, x.index)},
        {"strategy": "tqqq_buy_hold", "engine": "shared",
         **metrics(bh_eq, x.index)},
    ])
    summary.to_csv(OUT / "tqqq_canonical_same_input_summary.csv", index=False)

    ledger = []
    for shock_i, low_i, decision_i in events:
        ledger.append({
            "shock_date": x.index[shock_i].date(),
            "low_date": x.index[low_i].date(),
            "decision_date": x.index[decision_i].date(),
            "shock_signal": signal[shock_i],
            "reentry_signal": signal[decision_i],
            "shock_next_open_position": signal[shock_i],
            "reentry_next_open_position": signal[decision_i],
        })
    pd.DataFrame(ledger).to_csv(OUT / "tqqq_canonical_same_input_events.csv", index=False)
    pd.DataFrame({
        "date": x.index,
        "signal_close": signal,
        "shared_daily_return": shared_daily,
        "independent_daily_return": independent_daily,
        "shared_equity": shared_eq,
        "independent_equity": independent_eq,
        "buy_hold_equity": bh_eq,
    }).to_csv(OUT / "tqqq_canonical_same_input_daily.csv", index=False,
              float_format="%.15g")

    digest = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    manifest = {
        "status": "PASS",
        "start": str(x.index[0].date()),
        "end": str(x.index[-1].date()),
        "rows": int(len(x)),
        "initial_balance": INITIAL,
        "shock_threshold": SHOCK,
        "recovery_threshold": RECOVERY,
        "signal_asset": "QQQ adjusted close",
        "trade_asset": "TQQQ adjusted open/close",
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight, new position earns intraday",
        "frozen_input_file": frozen_path.name,
        "frozen_input_sha256": digest,
        "event_count": len(events),
        "independent_event_builder_match": events == independent_events,
        "independent_signal_match": bool(np.array_equal(signal, independent_signal)),
        "max_abs_daily_return_diff": float(np.max(np.abs(shared_daily-independent_daily))),
        "max_abs_equity_diff": float(np.max(np.abs(shared_eq-independent_eq))),
        "summary": summary.to_dict(orient="records"),
    }
    (OUT / "tqqq_canonical_same_input_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
