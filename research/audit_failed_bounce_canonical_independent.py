"""Independent audit of the canonical QQQ -4.5% -> +10% failed-bounce strategy.

This intentionally does NOT import the strategy builder or causal_execution.
It independently reconstructs:
  QQQ close[t] shock -> TQQQ exit at open[t+1]
  QQQ +10% recovery close[t] -> TQQQ re-entry at open[t+1]
and computes wealth with an explicit day-by-day loop.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-08"
SHOCK = -0.045
RECOVERY = 0.10


def download(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna()


def events(q):
    close = q["Adj Close"].astype(float).to_numpy()
    dates = q.index
    daily = q["Adj Close"].pct_change().fillna(0).to_numpy()
    armed = False
    shock_i = low_i = None
    out = []
    for i in range(1, len(q)):
        if not armed and daily[i] <= SHOCK:
            armed = True
            shock_i = i
            low_i = i
        if armed:
            if close[i] < close[low_i]:
                low_i = i
            if close[i] / close[low_i] - 1 >= RECOVERY:
                out.append({
                    "shock_i": shock_i,
                    "shock_date": dates[shock_i].date(),
                    "low_i": low_i,
                    "low_date": dates[low_i].date(),
                    "decision_i": i,
                    "decision_date": dates[i].date(),
                    "speed_days": i - low_i,
                })
                armed = False
    return out


def adjusted_open(x):
    return x["Open"].astype(float) * x["Adj Close"].astype(float) / x["Close"].astype(float)


def explicit_equity(tqqq, signal):
    adj_open = adjusted_open(tqqq).to_numpy()
    adj_close = tqqq["Adj Close"].astype(float).to_numpy()
    value = INITIAL
    curve = []
    for i in range(len(tqqq)):
        # Signal[i-1] is the position established at yesterday's close and
        # therefore held through today's overnight and today's intraday move.
        overnight_position = signal[i - 1] if i > 0 else 0.0
        intraday_position = signal[i - 1] if i > 0 else 0.0
        if i > 0:
            value *= 1.0 + overnight_position * (adj_open[i] / adj_close[i - 1] - 1.0)
            value *= 1.0 + intraday_position * (adj_close[i] / adj_open[i] - 1.0)
        curve.append(value)
    return np.asarray(curve)


def build_signal(n, evs):
    # signal[t] is decided from information at close[t] and is executed
    # at the next session's open.
    s = np.ones(n, dtype=float)
    for e in evs:
        # Exit after the shock close; re-entry after the +10% decision close.
        s[e["shock_i"] : e["decision_i"]] = 0.0
    return s


def stats(eq):
    peak = np.maximum.accumulate(eq)
    years = (len(eq) and (END_DATE - START_DATE).days / 365.25)
    return {
        "final_balance": float(eq[-1]),
        "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float((eq / peak - 1).min()),
    }


START_DATE = pd.Timestamp(START)
END_DATE = pd.Timestamp(END)


def main():
    q = download("QQQ")
    t = download("TQQQ")
    idx = q.index.intersection(t.index)
    q = q.reindex(idx).dropna()
    t = t.reindex(idx).dropna()

    evs = events(q)
    signal = build_signal(len(t), evs)
    audit_eq = explicit_equity(t, signal)
    bh_eq = explicit_equity(t, np.ones(len(t)))

    rows = []
    for name, eq in [("canonical_failed_bounce", audit_eq), ("tqqq_buy_hold", bh_eq)]:
        rows.append({"strategy": name, **stats(eq)})
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "failed_bounce_independent_audit_summary.csv", index=False)

    ledger = []
    for e in evs:
        ledger.append({
            "shock_date": e["shock_date"],
            "low_date": e["low_date"],
            "decision_date": e["decision_date"],
            "speed_days": e["speed_days"],
            "shock_next_open_exposure": signal[e["shock_i"]],
            "reentry_next_open_exposure": signal[e["decision_i"]],
        })
    pd.DataFrame(ledger).to_csv(OUT / "failed_bounce_independent_audit_events.csv", index=False)

    print("\nINDEPENDENT AUDIT SUMMARY")
    print(summary.to_string(index=False))
    print("\nEVENT LEDGER")
    print(pd.DataFrame(ledger).to_string(index=False))
    print("\nEVENT COUNT", len(evs))
    print("SIGNAL/EXECUTION CHECK: shock-day signal=0 means exit next open; +10% decision-day signal=1 means re-enter next open.")
    if not all(signal[e["shock_i"]] == 0 and signal[e["decision_i"]] == 1 for e in evs):
        raise RuntimeError("Signal timing invariant failed.")


if __name__ == "__main__":
    main()
