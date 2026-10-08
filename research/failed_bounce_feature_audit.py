"""Causal failed-bounce feature audit.

Canonical event:
  QQQ daily shock <= -4.5% -> post-shock low -> QQQ +10% recovery.
Predictors are frozen at the +10% decision close. Outcome labels use only
future data after that decision:
  successful = +20% before -10%
  failed = -10% before +20%
  censored = neither within 252 trading sessions.

This is an audit/diagnostic, not a parameter optimizer.
Walk-forward folds:
  F1 train 2010-2017 / test 2018-2021
  F2 train 2010-2021 / test 2022-2026
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "2010-01-01"
END = "2026-10-08"
SHOCK = -0.045
RECOVERY = 0.10
FAIL = -0.10
SUCCESS = 0.20
HORIZON = 252
PAIRS = ((10,20),(10,50),(20,50),(20,100),(20,200),(50,100),(50,200),(100,200))


def dl(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna()


def events(p):
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


def outcome(p, decision_i):
    base = float(p.iloc[decision_i])
    end = min(len(p)-1, decision_i + HORIZON)
    z = p.iloc[decision_i+1:end+1].to_numpy() / base - 1
    a = np.where(z <= FAIL)[0]
    b = np.where(z >= SUCCESS)[0]
    if not len(a) and not len(b):
        return "censored", None, None
    ai = int(a[0]) if len(a) else 10**9
    bi = int(b[0]) if len(b) else 10**9
    if ai < bi:
        return "failed", ai+1, float(z[ai])
    return "successful", bi+1, float(z[bi])


def recency_of_cross(fast, slow, bullish=True):
    state = fast > slow if bullish else fast < slow
    arr = state.to_numpy()
    out = np.full(len(arr), np.nan)
    last = None
    for i in range(1, len(arr)):
        if bool(arr[i]) and not bool(arr[i-1]):
            last = i
        if last is not None:
            out[i] = i-last
    return out


def feature_frame(p, vix, raw):
    f = pd.DataFrame(index=p.index)
    sma = {n: p.rolling(n).mean() for n in (10,20,50,100,200)}
    ema = {n: p.ewm(span=n, adjust=False).mean() for n in (12,26,20)}
    for n in (5,10,20,40,60,120,200):
        f[f"ret{n}"] = p / p.shift(n) - 1
    f["recovery_speed"] = np.nan

    # MA pair states, separation, and recent cross recency.
    for a,b in PAIRS:
        f[f"ma_{a}_{b}_state"] = (sma[a] > sma[b]).astype(int)
        f[f"ma_{a}_{b}_sep"] = sma[a] / sma[b] - 1
        bull = recency_of_cross(sma[a], sma[b], True)
        bear = recency_of_cross(sma[a], sma[b], False)
        f[f"ma_{a}_{b}_bull_cross_age"] = bull
        f[f"ma_{a}_{b}_bear_cross_age"] = bear

    # Slopes / hierarchy.
    for n in (10,20,50,100,200):
        f[f"sma{n}_slope20"] = sma[n] / sma[n].shift(20) - 1
        f[f"sma{n}_slope60"] = sma[n] / sma[n].shift(60) - 1
        f[f"price_vs_sma{n}"] = p / sma[n] - 1
    f["bear_pair_count"] = sum((sma[a] < sma[b]).astype(int) for a,b in PAIRS)
    f["bull_pair_count"] = sum((sma[a] > sma[b]).astype(int) for a,b in PAIRS)

    # MACD.
    macd = ema[12] - ema[26]
    macd_sig = macd.ewm(span=9, adjust=False).mean()
    hist = macd - macd_sig
    f["macd"] = macd
    f["macd_signal"] = macd_sig
    f["macd_hist"] = hist
    f["macd_below_signal"] = (macd < macd_sig).astype(int)
    f["macd_hist_negative"] = (hist < 0).astype(int)
    f["macd_hist_slope5"] = hist - hist.shift(5)
    f["macd_bull_cross_age"] = recency_of_cross(macd, macd_sig, True)
    f["macd_bear_cross_age"] = recency_of_cross(macd, macd_sig, False)

    # Bollinger 20.
    mid = sma[20]
    std = p.rolling(20).std()
    upper = mid + 2*std
    lower = mid - 2*std
    f["bb_z20"] = (p-mid) / std
    f["bb_pctb20"] = (p-lower) / (upper-lower)
    f["bb_bandwidth20"] = (upper-lower) / mid

    # Donchian positions.
    for n in (20,55):
        hi = p.rolling(n).max()
        lo = p.rolling(n).min()
        f[f"donchian{n}_position"] = (p-lo) / (hi-lo)

    # Keltner-style channel: EMA20 +/- 2 ATR20.
    high = raw["High"].astype(float)
    low = raw["Low"].astype(float)
    close = raw["Close"].astype(float)
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(20).mean()
    ku = ema[20] + 2*atr
    kl = ema[20] - 2*atr
    f["keltner20_position"] = (p-kl) / (ku-kl)
    f["keltner20_upper_distance"] = p/ku - 1
    f["keltner20_lower_distance"] = p/kl - 1

    # Volatility and VIX.
    f["vol20"] = p.pct_change().rolling(20).std() * np.sqrt(252)
    f["vol60"] = p.pct_change().rolling(60).std() * np.sqrt(252)
    f["vix"] = vix.reindex(p.index).ffill()
    f["vix_chg20"] = f.vix / f.vix.shift(20) - 1
    return f


def main():
    q = dl("QQQ")
    vix = dl("^VIX")["Close"].astype(float)
    p = q["Adj Close"].astype(float)
    f = feature_frame(p, vix, q)

    rows = []
    for shock_i, low_i, decision_i in events(p):
        lab, days, ret = outcome(p, decision_i)
        row = {
            "shock_date": p.index[shock_i].date(),
            "low_date": p.index[low_i].date(),
            "decision_date": p.index[decision_i].date(),
            "recovery_speed_days": decision_i-low_i,
            "label": lab,
            "label_days": days,
            "label_return": ret,
        }
        for k,v in f.iloc[decision_i].items():
            row[k] = float(v) if np.isfinite(v) else np.nan
        rows.append(row)

    event_df = pd.DataFrame(rows)
    event_df["decision_date"] = pd.to_datetime(event_df["decision_date"])
    event_df.to_csv(OUT/"failed_bounce_feature_audit_events.csv", index=False)

    # Compact separation table: all events, then each walk-forward train/test fold.
    feature_cols = [c for c in event_df.columns if c not in {
        "shock_date","low_date","decision_date","label","label_days","label_return"
    }]
    groups = [
        ("all","2010-01-01","2026-12-31"),
        ("F1_train","2010-01-01","2017-12-31"),
        ("F1_test","2018-01-01","2021-12-31"),
        ("F2_train","2010-01-01","2021-12-31"),
        ("F2_test","2022-01-01","2026-12-31"),
    ]
    sep = []
    for g,a,b in groups:
        z = event_df[(event_df.decision_date >= a) & (event_df.decision_date <= b)]
        for feat in feature_cols:
            for label in ("failed","successful"):
                vals = z.loc[z.label==label, feat].dropna()
                sep.append({
                    "fold": g, "feature": feat, "label": label,
                    "n": int(len(vals)),
                    "mean": float(vals.mean()) if len(vals) else np.nan,
                    "median": float(vals.median()) if len(vals) else np.nan,
                })
    sep_df = pd.DataFrame(sep)
    sep_df.to_csv(OUT/"failed_bounce_feature_audit_separation.csv", index=False)

    print("\nEVENT TABLE")
    print(event_df.to_string(index=False))
    print("\nLABEL COUNTS")
    print(event_df.label.value_counts(dropna=False).to_string())
    print("\nWALK-FORWARD SAMPLE SIZES")
    for g,a,b in groups[1:]:
        z=event_df[(event_df.decision_date>=a)&(event_df.decision_date<=b)]
        print(g, len(z), z.label.value_counts().to_dict())
    print("\nFEATURE SEPARATION (ALL EVENTS, FAILED VS SUCCESSFUL)")
    allsep=sep_df[sep_df.fold=="all"].pivot(index="feature",columns="label",values=["n","mean","median"])
    print(allsep.to_string())


if __name__=="__main__":
    main()
