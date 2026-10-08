"""Canonical failed-bounce structural classification and partial-exposure matrix.

Signal asset: QQQ adjusted close.
Trade asset: actual TQQQ adjusted OHLC.
Canonical event: QQQ daily shock <= -4.5%, then defensive until QQQ
recovers +10% from the post-shock low.
Classification is evaluated at that +10% decision date using only information
available through that close. TQQQ changes position at the next session open.

Broad shock thresholds are used ONLY for event classification diagnostics.
The strategy matrix is restricted to the canonical -4.5% event set.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_daily_returns, next_open_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-08"
NORMAL = 0.10
FAIL = -0.10
SUCCESS = 0.20
HORIZON = 252
SHOCKS = (-0.03, -0.04, -0.045, -0.05, -0.06)
CANONICAL_SHOCK = -0.045
TARGETS = (0.15, 0.20, 0.30)
EXPOSURES = (0.0, 0.25, 0.50, 0.75)


def dl(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()


def load():
    q = dl("QQQ")
    t = dl("TQQQ")
    q["adj_open"] = q["Open"] * q["Adj Close"] / q["Close"]
    t["adj_open"] = t["Open"] * t["Adj Close"] / t["Close"]
    x = q[["Adj Close", "adj_open"]].rename(columns={"Adj Close": "qqq_adj_close", "adj_open": "qqq_adj_open"})
    x = x.join(
        t[["adj_open", "Adj Close"]].rename(columns={"adj_open": "tqqq_adj_open", "Adj Close": "tqqq_adj_close"}),
        how="inner",
    ).dropna()
    x["tqqq_overnight"] = (x.tqqq_adj_open / x.tqqq_adj_close.shift(1) - 1).fillna(0.0)
    x["tqqq_intraday"] = (x.tqqq_adj_close / x.tqqq_adj_open - 1).fillna(0.0)
    return x


def features(p):
    sma = {n: p.rolling(n).mean() for n in (10, 20, 50, 60, 100, 120, 150, 200)}
    f = {}
    for n in (20, 60, 120):
        f[f"ret{n}"] = p / p.shift(n) - 1
        f[f"slope_sma{n}"] = sma[n] / sma[n].shift(20) - 1
        f[f"price_vs_sma{n}"] = p / sma[n] - 1
    f["state_60_120"] = sma[60] / sma[120] - 1
    f["state_60_200"] = sma[60] / sma[200] - 1
    f["state_120_200"] = sma[120] / sma[200] - 1
    f["sma60_slope60"] = sma[60] / sma[60].shift(60) - 1
    f["sma120_slope60"] = sma[120] / sma[120].shift(60) - 1
    f["sma200_slope60"] = sma[200] / sma[200].shift(60) - 1
    conds = [
        f["ret60"] < 0, f["ret120"] < 0,
        f["slope_sma60"] < 0, f["slope_sma120"] < 0,
        f["price_vs_sma60"] < 0, f["price_vs_sma120"] < 0,
        f["state_60_120"] < 0, f["state_60_200"] < 0,
        f["state_120_200"] < 0, f["sma60_slope60"] < 0,
        f["sma120_slope60"] < 0,
    ]
    f["structural_score"] = sum(c.astype(int) for c in conds)
    f["damage_ge6"] = (f["structural_score"] >= 6).astype(int)
    f["damage_ge7"] = (f["structural_score"] >= 7).astype(int)
    f["damage_ge8"] = (f["structural_score"] >= 8).astype(int)
    f["secular_bear"] = (
        (f["ret120"] < 0)
        & (f["slope_sma60"] < 0)
        & (f["slope_sma120"] < 0)
        & (f["state_60_120"] < 0)
        & (f["state_120_200"] < 0)
        & (f["price_vs_sma120"] < 0)
    ).astype(int)
    f["repair_damage"] = (
        (f["ret20"] > 0)
        & (f["ret60"] < 0)
        & (f["state_60_120"] < 0)
        & (f["state_120_200"] < 0)
    ).astype(int)
    return pd.DataFrame(f, index=p.index)


def event_indices(p, shock):
    r = p.pct_change().fillna(0).to_numpy()
    px = p.to_numpy()
    armed = False
    low = np.nan
    low_i = None
    out = []
    for i in range(1, len(p)):
        if not armed and r[i] <= shock:
            armed = True
            low = px[i]
            low_i = i
        if armed:
            if px[i] < low:
                low = px[i]
                low_i = i
            if px[i] / low - 1 >= NORMAL:
                out.append((i, low_i))
                armed = False
    return out


def label(p, decision_i):
    base = float(p.iloc[decision_i])
    end = min(len(p) - 1, decision_i + HORIZON)
    z = p.iloc[decision_i + 1 : end + 1].to_numpy() / base - 1
    failed = np.where(z <= FAIL)[0]
    successful = np.where(z >= SUCCESS)[0]
    if not len(failed) and not len(successful):
        return "censored", None, None
    fi = int(failed[0]) if len(failed) else 10**9
    si = int(successful[0]) if len(successful) else 10**9
    if fi < si:
        return "failed", fi + 1, float(z[fi])
    return "successful", si + 1, float(z[si])


def rule_defs():
    return {
        "ret60_negative": lambda r: r.ret60 < 0,
        "ret120_negative": lambda r: r.ret120 < 0,
        "sma60_slope_negative": lambda r: r.slope_sma60 < 0,
        "sma120_slope_negative": lambda r: r.slope_sma120 < 0,
        "60_120_bear": lambda r: r.state_60_120 < 0,
        "120_200_bear": lambda r: r.state_120_200 < 0,
        "price_below_120": lambda r: r.price_vs_sma120 < 0,
        "damage_ge6": lambda r: r.structural_score >= 6,
        "damage_ge7": lambda r: r.structural_score >= 7,
        "damage_ge8": lambda r: r.structural_score >= 8,
        "secular_bear": lambda r: r.secular_bear == 1,
        "repair_damage": lambda r: r.repair_damage == 1,
        "repair_and_damage6": lambda r: r.repair_damage == 1 and r.structural_score >= 6,
        "repair_and_damage7": lambda r: r.repair_damage == 1 and r.structural_score >= 7,
        "repair_and_damage8": lambda r: r.repair_damage == 1 and r.structural_score >= 8,
    }


def build_events(p, f, shock):
    rows = []
    for decision_i, low_i in event_indices(p, shock):
        lab, days, ret = label(p, decision_i)
        row = {
            "shock_pct": -shock,
            "decision_i": decision_i,
            "decision_date": p.index[decision_i].date(),
            "low_i": low_i,
            "low_date": p.index[low_i].date(),
            "speed_days": decision_i - low_i,
            "label": lab,
            "label_days": days,
            "label_return": ret,
        }
        for k, v in f.iloc[decision_i].items():
            row[k] = float(v) if np.isfinite(v) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def signal_for_rule(p, events, rule, target, exposure):
    w = np.ones(len(p), dtype=float)
    for row in events.itertuples(index=False):
        if row.label == "censored":
            continue
        decision_i = int(row.decision_i)
        armed_end = decision_i
        # The strategy remains defensive from the original shock until the
        # recovery decision. The only question is how much exposure is allowed
        # after the +10% bounce when the structural rule flags a failed bounce.
        for j in range(int(row.low_i), decision_i + 1):
            w[j] = 0.0
        try:
            flagged = bool(rule(row))
        except Exception:
            flagged = False
        if flagged:
            # Hold reduced exposure until the higher target is reached.
            # If target is never reached, exposure remains reduced through the
            # end of the sample; this is intentional and causal.
            base = float(p.iloc[decision_i])
            future = p.iloc[decision_i + 1 :].to_numpy() / base - 1
            hit = np.where(future >= target)[0]
            resume_i = decision_i + 1 + int(hit[0]) if len(hit) else len(p)
            w[decision_i + 1 : resume_i] = exposure
        else:
            w[decision_i + 1] = 1.0
    return w


def evaluate_weights(x, w):
    daily = next_open_daily_returns(w, x.tqqq_overnight, x.tqqq_intraday)
    eq = INITIAL * np.cumprod(1 + daily)
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1
    years = (x.index[-1] - x.index[0]).days / 365.25
    return {
        "final_balance": float(eq[-1]),
        "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "avg_exposure": float(np.mean(w)),
        "minimum_equity": float(eq.min()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x = load()
    p = x.qqq_adj_close.astype(float)
    f = features(p)

    event_frames = []
    stats = []
    for shock in SHOCKS:
        ev = build_events(p, f, shock)
        event_frames.append(ev)
        resolved = ev[ev.label != "censored"] if len(ev) else ev
        for name, fn in rule_defs().items():
            flagged = []
            for row in resolved.itertuples(index=False):
                try:
                    flagged.append(bool(fn(row)))
                except Exception:
                    flagged.append(False)
            n = int(sum(flagged))
            fail = int(sum(a and b.label == "failed" for a, b in zip(flagged, resolved.itertuples(index=False))))
            stats.append({
                "shock_pct": -shock,
                "rule": name,
                "events": int(len(ev)),
                "resolved": int(len(resolved)),
                "base_fail_rate": float((resolved.label == "failed").mean()) if len(resolved) else np.nan,
                "flagged": n,
                "failed_flagged": fail,
                "success_flagged": n - fail,
                "fail_rate_flagged": float(fail / n) if n else np.nan,
            })

    events_df = pd.concat([e for e in event_frames if len(e)], ignore_index=True)
    events_df.to_csv(OUT / "failed_bounce_structural_events.csv", index=False)
    pd.DataFrame(stats).to_csv(OUT / "failed_bounce_structural_signal_stats.csv", index=False)

    # Strategy matrix is intentionally restricted to the canonical 4.5% event set.
    canonical = build_events(p, f, CANONICAL_SHOCK)
    rules = rule_defs()
    rows = []
    bh = evaluate_weights(x, np.ones(len(x)))
    rows.append({
        "shock_pct": 4.5,
        "strategy": "tqqq_buy_hold",
        "target_pct": np.nan,
        "flagged_exposure": 1.0,
        **bh,
    })

    # Canonical binary defensive control: 0% through the +10% recovery.
    binary_w = np.ones(len(p))
    for row in canonical.itertuples(index=False):
        binary_w[int(row.low_i) : int(row.decision_i) + 1] = 0.0
    rows.append({
        "shock_pct": 4.5,
        "strategy": "canonical_defensive_until_plus10",
        "target_pct": 10.0,
        "flagged_exposure": 0.0,
        **evaluate_weights(x, binary_w),
    })

    for name, fn in rules.items():
        for target in TARGETS:
            for exposure in EXPOSURES:
                w = signal_for_rule(p, canonical, fn, target, exposure)
                rows.append({
                    "shock_pct": 4.5,
                    "strategy": name,
                    "target_pct": target * 100,
                    "flagged_exposure": exposure,
                    **evaluate_weights(x, w),
                })

    matrix = pd.DataFrame(rows).sort_values("final_balance", ascending=False)
    matrix.to_csv(OUT / "failed_bounce_structural_strategy_full.csv", index=False)

    print("\nEVENT COUNTS / FAILURE RATES")
    print(pd.DataFrame(stats).groupby("shock_pct").first().to_string())
    print("\nCANONICAL EVENT SNAPSHOT")
    print(canonical[[
        "decision_date", "low_date", "speed_days", "label", "ret60", "ret120",
        "slope_sma60", "slope_sma120", "state_60_120", "state_120_200",
        "structural_score", "secular_bear", "repair_damage"
    ]].to_string(index=False))
    print("\nTOP CANONICAL STRATEGIES")
    print(matrix.head(40).to_string(index=False))
    print("\nTQQQ BUY-HOLD CONTROL")
    print(bh)


if __name__ == "__main__":
    main()
