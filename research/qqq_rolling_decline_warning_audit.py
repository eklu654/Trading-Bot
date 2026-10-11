"""Pre-registered event-level screening of QQQ rolling peak-to-close declines.

Signal-only diagnostics; does not modify or simulate B0. See
docs/research/QQQ_ROLLING_DECLINE_WARNING_HYPOTHESIS_2026-10-11.md.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import itertools
import json

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
OUT.mkdir(parents=True, exist_ok=True)
START, END = "1999-03-10", "2026-10-09"
X_VALUES = (0.05, 0.075, 0.10, 0.125, 0.15)
Y_VALUES = (10, 20, 40, 60)
EVENT_DD = 0.20


def download():
    raw = yf.download("QQQ", start=START, end=END, auto_adjust=True,
                      progress=False, actions=False)
    if raw.empty:
        raise RuntimeError("QQQ download returned no rows")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    close = raw["Close"].squeeze().astype(float).dropna().sort_index()
    close = close[~close.index.duplicated(keep="last")]
    if len(close) < 1000:
        raise RuntimeError(f"Insufficient QQQ observations: {len(close)}")
    return close


def events_from_close(close, threshold=EVENT_DD):
    """Non-overlapping peak-to-recovery events; peak-to-trough drawdown >= threshold."""
    vals = close.to_numpy()
    dates = close.index
    out = []
    peak_i = 0
    i = 1
    n = len(vals)
    while i < n:
        if vals[i] >= vals[peak_i]:
            peak_i = i
            i += 1
            continue
        dd = vals[i] / vals[peak_i] - 1.0
        if dd > -threshold:
            i += 1
            continue
        start_i = peak_i
        peak_val = vals[start_i]
        trough_i = i
        j = i + 1
        while j < n and vals[j] < peak_val:
            if vals[j] < vals[trough_i]:
                trough_i = j
            j += 1
        recovered = j < n
        end_i = j if recovered else n - 1
        out.append({
            "event_id": len(out) + 1,
            "peak_date": str(pd.Timestamp(dates[start_i]).date()),
            "peak_close": float(peak_val),
            "trough_date": str(pd.Timestamp(dates[trough_i]).date()),
            "trough_close": float(vals[trough_i]),
            "trough_drawdown_pct": float((vals[trough_i] / peak_val - 1) * 100),
            "recovery_date": str(pd.Timestamp(dates[end_i]).date()) if recovered else "",
            "recovered_to_prior_peak": bool(recovered),
            "_peak_i": start_i,
            "_trough_i": trough_i,
            "_end_i": end_i,
        })
        # A completed event ends at prior peak recovery; continue from that point.
        if recovered:
            peak_i = end_i
            i = end_i + 1
        else:
            break
    return out


def main():
    close = download()
    raw = close.to_frame("adj_close")
    data_path = OUT / "qqq_rolling_decline_input.csv"
    raw.to_csv(data_path, index_label="date")
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    px = close.to_numpy()
    dates = close.index
    events = events_from_close(close)

    summary_rows, event_rows = [], []
    all_signals = {}
    for x, y in itertools.product(X_VALUES, Y_VALUES):
        roll_peak = close.rolling(y, min_periods=y).max()
        dd = close / roll_peak - 1.0
        signal = (dd <= -x).fillna(False).to_numpy()
        all_signals[(x, y)] = signal
        # Count distinct warning episodes (false warning cannot be defined
        # without an independently specified outcome horizon, so report episodes).
        starts = np.flatnonzero(signal & ~np.r_[False, signal[:-1]])
        event_detected = 0
        for ev in events:
            pi, ti = ev["_peak_i"], ev["_trough_i"]
            idx = np.flatnonzero(signal[pi:ti + 1])
            hit = len(idx) > 0
            if hit:
                si = pi + int(idx[0])
                event_detected += 1
                loss_avoided = (px[si] - px[ti]) / (px[pi] - px[ti]) if px[pi] != px[ti] else np.nan
                signal_dd = (px[si] / px[pi] - 1) * 100
                delay = si - pi
                sdate = str(pd.Timestamp(dates[si]).date())
            else:
                si, loss_avoided, signal_dd, delay, sdate = (None, np.nan, np.nan, np.nan, "")
            event_rows.append({
                "x_decline_pct": x * 100, "y_sessions": y,
                "event_id": ev["event_id"], "peak_date": ev["peak_date"],
                "trough_date": ev["trough_date"], "trough_drawdown_pct": ev["trough_drawdown_pct"],
                "warning_before_trough": hit, "first_warning_date": sdate,
                "sessions_peak_to_warning": delay, "drawdown_at_warning_pct": signal_dd,
                "estimated_fraction_peak_to_trough_loss_avoided_if_exit_at_close": loss_avoided,
                "recovered_to_prior_peak": ev["recovered_to_prior_peak"],
            })
        summary_rows.append({
            "x_decline_pct": x * 100, "y_sessions": y,
            "event_count": len(events), "events_warned_before_trough": event_detected,
            "event_detection_rate_pct": 100 * event_detected / len(events) if events else np.nan,
            "distinct_warning_episodes": len(starts),
            "warning_days": int(signal.sum()),
            "warning_day_fraction_pct": 100 * float(signal.mean()),
        })

    summary = pd.DataFrame(summary_rows)
    event_df = pd.DataFrame(event_rows)
    summary_path = OUT / "qqq_rolling_decline_summary.csv"
    events_path = OUT / "qqq_rolling_decline_events.csv"
    summary.to_csv(summary_path, index=False)
    event_df.to_csv(events_path, index=False)
    metadata = {
        "symbol": "QQQ", "provider": "Yahoo Finance via yfinance",
        "field": "auto_adjust=True Close", "start": str(dates[0].date()),
        "end_inclusive": str(dates[-1].date()), "rows": int(len(close)),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "input_csv_sha256": digest, "event_definition": "non-overlapping peak-to-prior-peak-recovery drawdown >=20%",
        "x_values_pct": [v * 100 for v in X_VALUES], "y_sessions": list(Y_VALUES),
        "warning_definition": "close <= trailing Y-session maximum adjusted close * (1-X)",
        "note": "Signal-only event diagnostics; no B0/TQQQ performance simulation and no claim that warning episodes are false alarms."
    }
    meta_path = OUT / "qqq_rolling_decline_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    report = [
        "# QQQ Rolling-Decline Warning Audit",
        "",
        f"- Retrieved UTC: {metadata['retrieved_utc']}",
        f"- Data rows: {metadata['rows']}; dates: {metadata['start']} to {metadata['end_inclusive']}",
        f"- Input SHA-256: `{digest}`",
        "- Signal: adjusted close is at least X% below its trailing Y-session closing high.",
        "- Events: non-overlapping peak-to-recovery episodes with at least 20% peak-to-trough loss.",
        "- This is signal-only diagnostics. It does not simulate a defensive portfolio, define false alarms, or modify B0.",
        "",
        "## Threshold matrix",
        "",
        summary.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Interpretation guardrails",
        "",
        "- A warning before an event trough is not automatically an early or useful warning; inspect peak-to-warning delay and loss already incurred.",
        "- Distinct warning episodes are not false alarms. False alarms require a predeclared outcome horizon and independent event definition.",
        "- Thresholds were not optimized. Do not select a winner from this in-sample matrix and report it as validated.",
        "- Actual TQQQ strategy effects and recovery opportunity cost require a separate frozen-control simulation.",
    ]
    report_path = OUT / "qqq_rolling_decline_audit.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"input_sha256={digest}")
    print(f"summary={summary_path}")
    print(f"events={events_path}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
