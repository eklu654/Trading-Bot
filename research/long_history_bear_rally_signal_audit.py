"""Long-history, signal-only failed-rally audit using S&P 500 index data.

This is not a TQQQ portfolio backtest. It evaluates whether a fixed shock /
recovery event definition and frozen trend features distinguish recoveries
that subsequently fail from those that continue, across historical regimes
including the 1970s, 1987, 2000-2002, 2020, and 2022.

All features are measured at the +10% recovery decision close. Labels use only
subsequent data and never gate event creation or signal construction.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "1970-01-01"
END = "2026-10-08"
SHOCK = -0.045
RECOVERY = 0.10
FAIL = -0.10
SUCCESS = 0.20
HORIZON = 252


def download():
    x = yf.download("^GSPC", start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    x = x.sort_index().dropna()
    if x.empty:
        raise RuntimeError("S&P 500 history download returned no rows")
    # Use the index Close, not a synthetic leveraged series.
    return x, x["Close"].astype(float)


def cross_age(a, b, bullish=True):
    state = (a > b) if bullish else (a < b)
    vals = state.to_numpy(dtype=bool)
    age = np.full(len(vals), np.nan)
    last = None
    for i in range(1, len(vals)):
        if vals[i] and not vals[i - 1]:
            last = i
        if last is not None:
            age[i] = i - last
    return age


def features(p):
    sma = {n: p.rolling(n).mean() for n in (20, 50, 100, 200)}
    ema12 = p.ewm(span=12, adjust=False).mean()
    ema26 = p.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sig = macd.ewm(span=9, adjust=False).mean()
    hist = macd - sig
    f = pd.DataFrame(index=p.index)
    for n in (20, 60, 120, 200):
        f[f"return_{n}"] = p / p.shift(n) - 1
    for n in (50, 100, 200):
        f[f"price_vs_sma{n}"] = p / sma[n] - 1
        f[f"sma{n}_slope20"] = sma[n] / sma[n].shift(20) - 1
        f[f"sma{n}_slope60"] = sma[n] / sma[n].shift(60) - 1
    f["sma50_above_sma100"] = (sma[50] > sma[100]).astype(int)
    f["sma100_above_sma200"] = (sma[100] > sma[200]).astype(int)
    f["sma50_100_bull_cross_age"] = cross_age(sma[50], sma[100], True)
    f["sma50_100_bear_cross_age"] = cross_age(sma[50], sma[100], False)
    f["sma100_200_bull_cross_age"] = cross_age(sma[100], sma[200], True)
    f["sma100_200_bear_cross_age"] = cross_age(sma[100], sma[200], False)
    f["macd"] = macd
    f["macd_signal"] = sig
    f["macd_hist"] = hist
    f["macd_hist_negative"] = (hist < 0).astype(int)
    f["macd_below_signal"] = (macd < sig).astype(int)
    f["macd_hist_slope5"] = hist - hist.shift(5)
    f["macd_bull_cross_age"] = cross_age(macd, sig, True)
    f["macd_bear_cross_age"] = cross_age(macd, sig, False)
    f["vol20"] = p.pct_change().rolling(20).std() * np.sqrt(252)
    return f


def build_events(p, f):
    daily = p.pct_change().fillna(0).to_numpy()
    px = p.to_numpy(dtype=float)
    rows = []
    armed = False
    shock_i = low_i = None
    for i in range(1, len(p)):
        if not armed and daily[i] <= SHOCK:
            armed = True
            shock_i = i
            low_i = i
        if armed:
            if px[i] < px[low_i]:
                low_i = i
            if px[i] / px[low_i] - 1 >= RECOVERY:
                base = float(px[i])
                end = min(len(p) - 1, i + HORIZON)
                future = px[i + 1:end + 1] / base - 1
                fail_hits = np.flatnonzero(future <= FAIL)
                success_hits = np.flatnonzero(future >= SUCCESS)
                if not len(fail_hits) and not len(success_hits):
                    label, label_days, label_return = "censored", None, None
                else:
                    fi = int(fail_hits[0]) if len(fail_hits) else 10**9
                    si = int(success_hits[0]) if len(success_hits) else 10**9
                    if fi < si:
                        label, label_days, label_return = "failed", fi + 1, float(future[fi])
                    else:
                        label, label_days, label_return = "successful", si + 1, float(future[si])
                row = {
                    "shock_date": p.index[shock_i].date().isoformat(),
                    "low_date": p.index[low_i].date().isoformat(),
                    "decision_date": p.index[i].date().isoformat(),
                    "shock_return": float(daily[shock_i]),
                    "recovery_speed_days": i - low_i,
                    "label": label,
                    "label_days": label_days,
                    "label_return": label_return,
                }
                for key, value in f.iloc[i].items():
                    row[key] = float(value) if pd.notna(value) and np.isfinite(value) else None
                rows.append(row)
                armed = False
    return pd.DataFrame(rows)


def period_for(date):
    d = pd.Timestamp(date)
    if 1970 <= d.year <= 1979:
        return "1970s"
    if d.year == 1987:
        return "1987"
    if 2000 <= d.year <= 2002:
        return "2000-2002"
    if 2010 <= d.year <= 2019:
        return "2010-2019"
    if 2020 <= d.year <= 2021:
        return "2020-2021"
    if 2022 <= d.year <= 2026:
        return "2022-2026"
    return "other"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw, p = download()
    f = features(p)
    ev = build_events(p, f)
    if ev.empty:
        raise RuntimeError("No shock/recovery events were found")
    ev["period"] = ev["shock_date"].map(period_for)
    ev.to_csv(OUT / "long_history_bear_rally_events.csv", index=False)
    summary = (ev.groupby(["period", "label"], dropna=False)
                 .size().rename("events").reset_index())
    summary.to_csv(OUT / "long_history_bear_rally_period_summary.csv", index=False)

    resolved = ev[ev.label.isin(["failed", "successful"])]
    feature_cols = [c for c in ev.columns if c not in {
        "shock_date", "low_date", "decision_date", "label", "label_days",
        "label_return", "period"
    }]
    separation = []
    for period in ["all", "1970s", "1987", "2000-2002", "2010-2019",
                   "2020-2021", "2022-2026"]:
        subset = resolved if period == "all" else resolved[resolved.period == period]
        for col in feature_cols:
            for label in ("failed", "successful"):
                vals = subset.loc[subset.label == label, col].dropna()
                separation.append({
                    "period": period, "feature": col, "label": label,
                    "n": int(len(vals)),
                    "mean": float(vals.mean()) if len(vals) else None,
                    "median": float(vals.median()) if len(vals) else None,
                })
    pd.DataFrame(separation).to_csv(
        OUT / "long_history_bear_rally_feature_separation.csv", index=False)

    manifest = {
        "status": "SIGNAL_ONLY_DIAGNOSTIC",
        "instrument": "S&P 500 index (^GSPC), not QQQ or TQQQ",
        "start": str(p.index[0].date()),
        "end": str(p.index[-1].date()),
        "rows": int(len(p)),
        "event_count": int(len(ev)),
        "label_counts": {str(k): int(v) for k, v in ev.label.value_counts(dropna=False).items()},
        "rule": {
            "shock": "daily S&P 500 Close return <= -4.5%",
            "recovery": "first Close >= 10% above the post-shock low",
            "failed": "within next 252 sessions, -10% from decision close before +20%",
            "successful": "+20% from decision close before -10%",
            "censored": "neither barrier hit within 252 sessions",
        },
        "period_counts": summary.to_dict(orient="records"),
        "warning": "No leveraged ETF balance is computed; pre-2010 results are signal-only.",
    }
    (OUT / "long_history_bear_rally_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nEVENT LEDGER")
    print(ev[["shock_date", "low_date", "decision_date", "recovery_speed_days",
              "label", "label_days", "period"]].to_string(index=False))


if __name__ == "__main__":
    main()
