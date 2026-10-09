"""Robustness audit for the canonical QQQ -4.5% shock -> +10% recovery strategy."""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-08"
SHOCK = -0.045
RECOVERY = 0.10


def dl(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna()


def build_events(q):
    p = q["Adj Close"].astype(float)
    r = p.pct_change().fillna(0).to_numpy()
    px = p.to_numpy()
    armed = False
    shock_i = low_i = None
    out = []
    for i in range(1, len(p)):
        if not armed and r[i] <= SHOCK:
            armed = True
            shock_i = i
            low_i = i
        if armed:
            if px[i] < px[low_i]:
                low_i = i
            if px[i] / px[low_i] - 1 >= RECOVERY:
                out.append((shock_i, low_i, i))
                armed = False
    return out


def build_signal(n, events):
    s = np.ones(n)
    for shock_i, low_i, decision_i in events:
        s[shock_i:decision_i] = 0.0
    return s


def daily_returns(t, signal):
    adj_open = (t["Open"] * t["Adj Close"] / t["Close"]).astype(float).to_numpy()
    adj_close = t["Adj Close"].astype(float).to_numpy()
    overnight = np.zeros(len(t))
    intraday = np.zeros(len(t))
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1
    intraday[:] = adj_close / adj_open - 1
    return next_open_daily_returns(signal, overnight, intraday)


def metrics(r):
    eq = INITIAL * np.cumprod(1 + r)
    peak = np.maximum.accumulate(eq)
    years = (pd.Timestamp(END) - pd.Timestamp(START)).days / 365.25
    return {
        "final_balance": float(eq[-1]),
        "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float((eq / peak - 1).min()),
        "avg_exposure": np.nan,
        "equity": eq,
    }


def period_stats(dates, r_strategy, r_bh):
    rows = []
    for label, a, b in [
        ("2010-2014", "2010-01-01", "2014-12-31"),
        ("2015-2019", "2015-01-01", "2019-12-31"),
        ("2020-2021", "2020-01-01", "2021-12-31"),
        ("2022-2024", "2022-01-01", "2024-12-31"),
        ("2025-current", "2025-01-01", END),
    ]:
        m = (dates >= a) & (dates <= b)
        for name, r in [("canonical", r_strategy), ("buy_hold", r_bh)]:
            z = r[m]
            eq = np.cumprod(1 + z)
            peak = np.maximum.accumulate(eq)
            rows.append({
                "period": label,
                "strategy": name,
                "return": float(eq[-1] - 1) if len(eq) else np.nan,
                "max_drawdown": float((eq / peak - 1).min()) if len(eq) else np.nan,
            })
    return pd.DataFrame(rows)


def event_contributions(t, events, full_signal, full_r):
    full_final = INITIAL * np.cumprod(1 + full_r)[-1]
    rows = []
    for j, (shock_i, low_i, decision_i) in enumerate(events, 1):
        s = full_signal.copy()
        s[shock_i:decision_i] = 1.0
        r = daily_returns(t, s)
        final = INITIAL * np.cumprod(1 + r)[-1]
        rows.append({
            "event": j,
            "shock_date": t.index[shock_i].date(),
            "low_date": t.index[low_i].date(),
            "decision_date": t.index[decision_i].date(),
            "defensive_days": decision_i - shock_i,
            "full_final": full_final,
            "counterfactual_no_defense_final": final,
            "terminal_benefit_of_event": full_final - final,
            "terminal_ratio_of_event": full_final / final,
        })
    return pd.DataFrame(rows)


def main():
    q = dl("QQQ")
    t = dl("TQQQ")
    idx = q.index.intersection(t.index)
    q = q.reindex(idx).dropna()
    t = t.reindex(idx).dropna()
    if not q.index.equals(t.index):
        raise RuntimeError("QQQ and TQQQ dates are not aligned after intersection/dropna")
    if len(q) != len(t) or len(idx) == 0:
        raise RuntimeError("QQQ/TQQQ aligned dataset is empty or has unequal lengths")
    events = build_events(q)
    signal = build_signal(len(t), events)
    r = daily_returns(t, signal)
    bh = daily_returns(t, np.ones(len(t)))
    OUT.mkdir(parents=True, exist_ok=True)
    # Persist exact aligned inputs and daily curves for reproducible reconciliation.
    q.to_csv(OUT / "failed_bounce_frozen_qqq.csv", index_label="Date", float_format="%.12g")
    t.to_csv(OUT / "failed_bounce_frozen_tqqq.csv", index_label="Date", float_format="%.12g")
    pd.DataFrame({"Date": t.index, "signal_close": signal, "strategy_daily_return": r, "buy_hold_daily_return": bh,
                  "strategy_equity": INITIAL * np.cumprod(1 + r), "buy_hold_equity": INITIAL * np.cumprod(1 + bh)}).to_csv(OUT / "failed_bounce_daily_equity.csv", index=False, float_format="%.12g")

    years = (t.index[-1] - t.index[0]).days / 365.25
    summary = []
    for name, rr in [("canonical", r), ("buy_hold", bh)]:
        eq = INITIAL * np.cumprod(1 + rr)
        peak = np.maximum.accumulate(eq)
        summary.append({
            "strategy": name,
            "final_balance": float(eq[-1]),
            "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
            "max_drawdown": float((eq / peak - 1).min()),
            "avg_daily_return": float(np.mean(rr)),
        })
    summary_df = pd.DataFrame(summary)

    period_df = period_stats(t.index, r, bh)
    contrib_df = event_contributions(t, events, signal, r)

    cost_rows = []
    for bps in (0, 5, 10, 25, 50):
        # Cost is charged only when next-open exposure changes.
        exec_w = np.roll(signal, 1); exec_w[0] = 0.0
        prev_exec = np.roll(exec_w, 1); prev_exec[0] = 0.0
        cost = np.abs(exec_w - prev_exec) * (bps / 10000.0)
        rr = r - cost
        eq = INITIAL * np.cumprod(1 + rr)
        peak = np.maximum.accumulate(eq)
        cost_rows.append({
            "bps": bps,
            "final_balance": float(eq[-1]),
            "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
            "max_drawdown": float((eq / peak - 1).min()),
            "trades": int(np.sum(np.abs(np.diff(exec_w)) > 0)),
        })
    cost_df = pd.DataFrame(cost_rows)

    summary_df.to_csv(OUT / "failed_bounce_robustness_summary.csv", index=False)
    period_df.to_csv(OUT / "failed_bounce_robustness_periods.csv", index=False)
    contrib_df.to_csv(OUT / "failed_bounce_robustness_event_contributions.csv", index=False)
    cost_df.to_csv(OUT / "failed_bounce_robustness_costs.csv", index=False)

    print("\nSUMMARY")
    print(summary_df.to_string(index=False))
    print("\nPERIODS")
    print(period_df.to_string(index=False))
    print("\nEVENT CONTRIBUTIONS")
    print(contrib_df.to_string(index=False))
    print("\nCOST STRESS")
    print(cost_df.to_string(index=False))


if __name__ == "__main__":
    main()
