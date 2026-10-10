"""Direct QQQ slow-bear exposure audit for the canonical daily-shock exit.

Measures QQQ trailing-252-session drawdowns that cross -10/-15/-20% before
any -4.5% daily QQQ shock, then records how long canonical B0 remains exposed
and the actual TQQQ loss accumulated through the next-open exit. Diagnostic
only: no thresholds or rules are promoted from this audit.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START, END = "2010-01-01", "2026-10-08"
SHOCK, THRESHOLDS = -0.045, (-0.10, -0.15, -0.20)


def download(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna(subset=["Open", "Close", "Adj Close"])


def run_audit(q, t):
    q = q.rename(columns={"Adj Close": "q_adj"})
    t = t.rename(columns={"Open": "t_open", "Close": "t_close", "Adj Close": "t_adj"})
    x = q[["q_adj", "Close"]].join(t[["t_open", "t_close", "t_adj"]], how="inner")
    x = x.dropna().sort_index()
    x["q_ret"] = x.q_adj.pct_change().fillna(0.0)
    x["q_peak252"] = x.q_adj.rolling(252, min_periods=252).max()
    x["q_dd252"] = x.q_adj / x.q_peak252 - 1.0
    x["t_adj_open"] = x.t_open * x.t_adj / x.t_close
    x["t_overnight"] = x.t_adj_open / x.t_adj.shift(1) - 1.0
    x["t_overnight"] = x.t_overnight.fillna(0.0)

    rows = []
    for threshold in THRESHOLDS:
        armed = False
        trigger_i = None
        episode_peak = None
        for i in range(251, len(x)):
            dd = float(x.q_dd252.iloc[i])
            if not np.isfinite(dd):
                continue
            if not armed and dd <= threshold and x.q_dd252.iloc[i-1] > threshold:
                armed, trigger_i = True, i
                episode_peak = float(x.q_peak252.iloc[i])
                # Same-day shock is not a gradual decline missed by the rule.
                if x.q_ret.iloc[i] <= SHOCK:
                    rows.append(make_row(x, threshold, trigger_i, i, "same_day_shock"))
                    armed = False
                    continue
            if armed and i > trigger_i and x.q_ret.iloc[i] <= SHOCK:
                rows.append(make_row(x, threshold, trigger_i, i, "shock_exit_next_open"))
                armed = False
            # Rearm only once QQQ regains the threshold level, to avoid
            # counting every lower close during one continuous bear episode.
            if armed and x.q_dd252.iloc[i] > threshold:
                armed = False
        if armed and trigger_i is not None:
            rows.append(make_row(x, threshold, trigger_i, None, "no_shock_before_data_end"))
    return x, pd.DataFrame(rows)


def make_row(x, threshold, trigger_i, shock_i, status):
    trig = x.iloc[trigger_i]
    if shock_i is None:
        end_i = len(x) - 1
        end_date = x.index[end_i]
        t_exit_return = float(np.prod(1.0 + x.t_overnight.iloc[trigger_i+1:end_i+1].to_numpy()) - 1.0)
        elapsed = end_i - trigger_i
        exit_price = float(x.t_adj_open.iloc[end_i])
        exit_dd = float(exit_price / trig.t_adj - 1.0)
    elif status == "same_day_shock":
        end_i = shock_i
        end_date = x.index[end_i]
        t_exit_return = float(x.t_adj_open.iloc[end_i] / trig.t_adj - 1.0) if end_i > trigger_i else 0.0
        elapsed = 0
        exit_dd = t_exit_return
    else:
        end_i = shock_i
        end_date = x.index[end_i]
        # B0 holds overnight through the shock close's preceding close, then
        # exits at that session's adjusted open. This isolates the return
        # actually experienced before the next-open exit.
        t_exit_return = float(np.prod(1.0 + x.t_overnight.iloc[trigger_i+1:end_i+1].to_numpy()) - 1.0)
        elapsed = end_i - trigger_i
        exit_dd = t_exit_return
    q_ret_to_exit = float(x.q_adj.iloc[end_i] / trig.q_adj - 1.0) if shock_i is not None else float(x.q_adj.iloc[end_i] / trig.q_adj - 1.0)
    peak_loc = x.q_adj.iloc[max(0, trigger_i-251):trigger_i+1].idxmax()
    return {
        "threshold": threshold,
        "trigger_date": x.index[trigger_i].date().isoformat(),
        "qqq_drawdown_at_trigger": float(trig.q_dd252),
        "trigger_daily_return": float(trig.q_ret),
        "prior_252d_peak_date": peak_loc.date().isoformat(),
        "prior_252d_peak_qqq": float(trig.q_peak252),
        "first_shock_date": x.index[shock_i].date().isoformat() if shock_i is not None else None,
        "status": status,
        "sessions_exposed_after_trigger": int(elapsed),
        "qqq_return_trigger_close_to_endpoint_close": q_ret_to_exit,
        "tqqq_return_trigger_close_to_next_open_exit_or_end": t_exit_return,
        "tqqq_dollar_loss_per_5000_at_trigger": float(5000.0 * t_exit_return),
        "endpoint_date": end_date.date().isoformat(),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q, t = download("QQQ"), download("TQQQ")
    x, events = run_audit(q, t)
    events.to_csv(OUT / "qqq_slow_bear_exposure_events.csv", index=False)
    summary = []
    for threshold, z in events.groupby("threshold"):
        summary.append({
            "threshold": float(threshold),
            "episodes": int(len(z)),
            "same_day_shock": int((z.status == "same_day_shock").sum()),
            "later_shock_exit": int((z.status == "shock_exit_next_open").sum()),
            "no_shock_before_end": int((z.status == "no_shock_before_data_end").sum()),
            "median_sessions_until_exit": float(z.loc[z.status == "shock_exit_next_open", "sessions_exposed_after_trigger"].median()) if (z.status == "shock_exit_next_open").any() else None,
            "median_tqqq_return_to_exit": float(z.loc[z.status == "shock_exit_next_open", "tqqq_return_trigger_close_to_next_open_exit_or_end"].median()) if (z.status == "shock_exit_next_open").any() else None,
            "worst_tqqq_return_to_exit": float(z.loc[z.status == "shock_exit_next_open", "tqqq_return_trigger_close_to_next_open_exit_or_end"].min()) if (z.status == "shock_exit_next_open").any() else None,
        })
    manifest = {
        "status": "DIAGNOSTIC_NOT_PROMOTED",
        "instrument_signal": "QQQ adjusted close",
        "instrument_execution": "actual TQQQ adjusted open/close",
        "window": [str(x.index[0].date()), str(x.index[-1].date())],
        "rule": "cross below -10/-15/-20% from trailing 252-session QQQ high; measure until first later QQQ daily return <= -4.5%, with B0 exit at next open",
        "note": "TQQQ return is measured only over overnight segments actually held before next-open exit; intraday movement after the exit open is excluded. No-shock episodes are measured through final available open.",
        "summary": summary,
    }
    (OUT / "qqq_slow_bear_exposure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nEPISODES")
    print(events.to_string(index=False))


if __name__ == "__main__":
    main()
