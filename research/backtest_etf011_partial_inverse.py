"""ETF-011 partial-inverse overlay research.

Tests whether ETF-010's rare-event bear gate adds value when applied only to
the defensive portion of the ETF-001 200-DMA strategy.

Each sleeve is 25% of the portfolio. When its underlying is in the normal
bull state, the sleeve holds its bull ETF. When the bull state is inactive,
the sleeve is normally cash; if the bear gate is confirmed, only the
configured fraction of that 25% sleeve is placed in the inverse ETF and the
remainder stays in cash.

Same-underlying bull/bear overlap is impossible by construction.
Parameters are selected on validation only; holdout is reported only for
validation-selected candidates.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"

PAIRS = {"QQQ": ("TQQQ", "SQQQ"), "SPY": ("SPXL", "SPXS"), "SOXX": ("SOXL", "SOXS")}
SLEEVE = 0.25
SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}
INVERSE_FRACTIONS = (0.25, 0.50, 0.75, 1.00)
SCORES = (3, 4, 5, 6)
CONFIRM = (1, 3, 5)
VIX_PCTS = (0.60, 0.70, 0.80)
BREADTH = (0.33, 0.50, 0.67)
REENTRY_SESSIONS = 5


def load(symbol):
    return pd.read_csv(DATA / f"{symbol.lower()}_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()


def build_inputs():
    under = {x: load(x)["close"] for x in PAIRS}
    raw = {x: load(x) for pair in PAIRS.values() for x in pair}
    vix = pd.read_csv(DATA / "vix_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()["vix"]
    close = pd.concat(under, axis=1)
    breadth = (close > close.rolling(200).mean()).mean(axis=1)
    vix_pct = vix.rolling(253).apply(
        lambda x: (x[:-1] <= x[-1]).mean() if len(x) > 30 else np.nan, raw=True
    )
    return under, raw, breadth, vix_pct


def bull_state(close, reentry_sessions=REENTRY_SESSIONS):
    ma = close.rolling(200).mean()
    active = False
    above = 0
    out = []
    for price, avg in zip(close, ma):
        if pd.isna(avg) or price < avg:
            active, above = False, 0
        elif not active:
            above += 1
            if above >= reentry_sessions:
                active = True
        out.append(active)
    return pd.Series(out, index=close.index).shift(1).fillna(False)


def bear_score(under, breadth, vix_pct):
    rows = {}
    for name, close in under.items():
        ma = close.rolling(200).mean()
        score = (
            (close < ma).astype(int)
            + (ma.pct_change(20) < 0).astype(int)
            + (close.pct_change(20) < 0).astype(int)
            + (close.pct_change(60) < 0).astype(int)
            + (breadth.reindex(close.index) <= 0.50).astype(int)
            + (vix_pct.reindex(close.index) >= 0.70).astype(int)
        )
        rows[name] = score
    return pd.DataFrame(rows)


def confirmed_bear(score, threshold, confirm, vp, breadth, under_name):
    close = under_name
    # Rebuild exact score with candidate VIX/breadth thresholds.
    ma = close.rolling(200).mean()
    s = (
        (close < ma).astype(int)
        + (ma.pct_change(20) < 0).astype(int)
        + (close.pct_change(20) < 0).astype(int)
        + (close.pct_change(60) < 0).astype(int)
        + (breadth.reindex(close.index) <= vp).astype(int)
        + (vix_pct_global.reindex(close.index) >= vp).astype(int)
    )
    raw = s >= threshold
    # Confirmation is based only on consecutive end-of-day bear signals.
    run = raw.astype(int).groupby((~raw).cumsum()).cumsum()
    return (run >= confirm).shift(1).fillna(False)


def metrics(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    total = eq.iloc[-1] - 1
    ann = (1 + total) ** (1 / years) - 1
    dd = (eq / eq.cummax() - 1).min()
    vol = r.std(ddof=1) * np.sqrt(252)
    sh = r.mean() / r.std(ddof=1) * np.sqrt(252) if r.std(ddof=1) > 0 else np.nan
    down = r.where(r < 0).std(ddof=1)
    sortino = r.mean() / down * np.sqrt(252) if pd.notna(down) and down > 0 else np.nan
    return ann, total, dd, vol, sh, sortino, 5000 * eq.iloc[-1]


def main():
    global vix_pct_global
    under, raw, breadth, vix_pct_global = build_inputs()
    bull = {n: bull_state(c) for n, c in under.items()}
    idx = pd.concat([raw[x]["adj_close"] for x in raw], axis=1).index

    # Precompute every candidate bear gate once per underlying.
    candidates = {}
    for score_threshold in SCORES:
        for confirm in CONFIRM:
            for vp in VIX_PCTS:
                for br in BREADTH:
                    for n, c in under.items():
                        ma = c.rolling(200).mean()
                        score = (
                            (c < ma).astype(int)
                            + (ma.pct_change(20) < 0).astype(int)
                            + (c.pct_change(20) < 0).astype(int)
                            + (c.pct_change(60) < 0).astype(int)
                            + (breadth.reindex(c.index) <= br).astype(int)
                            + (vix_pct_global.reindex(c.index) >= vp).astype(int)
                        )
                        raw_bear = score >= score_threshold
                        run = raw_bear.astype(int).groupby((~raw_bear).cumsum()).cumsum()
                        candidates[(score_threshold, confirm, vp, br, n)] = (run >= confirm).shift(1).fillna(False)

    # Baseline: ETF-001 200-DMA/5-session strategy with 25% permanent cash.
    baseline = pd.Series(0.0, index=idx)
    for n, (b, _) in PAIRS.items():
        ret = raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
        baseline = baseline.add(SLEEVE * ret.where(bull[n].reindex(idx).fillna(False), 0), fill_value=0)

    rows = []
    for frac in INVERSE_FRACTIONS:
        for score_threshold in SCORES:
            for confirm in CONFIRM:
                for vp in VIX_PCTS:
                    for br in BREADTH:
                        daily = pd.Series(0.0, index=idx)
                        inv_days = pd.Series(0, index=idx)
                        for n, (b, bear) in PAIRS.items():
                            rb = raw[b]["adj_close"].reindex(idx).pct_change().fillna(0)
                            rs = raw[bear]["adj_close"].reindex(idx).pct_change().fillna(0)
                            bs = bull[n].reindex(idx).fillna(False)
                            gate = candidates[(score_threshold, confirm, vp, br, n)].reindex(idx).fillna(False)
                            inv = (~bs) & gate
                            # Bull has priority; bear is only possible while bull is inactive.
                            daily = daily.add(SLEEVE * rb.where(bs, 0), fill_value=0)
                            daily = daily.add(SLEEVE * frac * rs.where(inv, 0), fill_value=0)
                            inv_days = inv_days.add(inv.astype(int), fill_value=0)
                        for split, (a, z) in SPLITS.items():
                            m = metrics(daily.loc[a:z])
                            rows.append({
                                "inverse_fraction": frac,
                                "score": score_threshold,
                                "confirm": confirm,
                                "vix_percentile": vp,
                                "breadth_threshold": br,
                                "split": split,
                                "annualized_return": m[0],
                                "total_return": m[1],
                                "max_drawdown": m[2],
                                "annualized_volatility": m[3],
                                "sharpe": m[4],
                                "sortino": m[5],
                                "ending_value_5000": m[6],
                                "mean_inverse_sleeves": inv_days.loc[a:z].mean(),
                            })

    out = pd.DataFrame(rows)
    base_rows = []
    for split, (a, z) in SPLITS.items():
        m = metrics(baseline.loc[a:z])
        base_rows.append({
            "strategy": "ETF001_BASELINE_CASH",
            "split": split,
            "annualized_return": m[0],
            "total_return": m[1],
            "max_drawdown": m[2],
            "annualized_volatility": m[3],
            "sharpe": m[4],
            "sortino": m[5],
            "ending_value_5000": m[6],
        })
    base = pd.DataFrame(base_rows)
    out.to_csv(DATA / "etf011_partial_inverse_results.csv", index=False)
    base.to_csv(DATA / "etf011_baseline_results.csv", index=False)

    val = out[out.split == "validation"].copy()
    val["sharpe_delta_vs_baseline"] = val.sharpe - base.loc[base.split == "validation", "sharpe"].iloc[0]
    val["return_delta_vs_baseline"] = val.annualized_return - base.loc[base.split == "validation", "annualized_return"].iloc[0]
    top = val.sort_values(["sharpe_delta_vs_baseline", "annualized_return"], ascending=False).head(20)
    print("=== ETF-011 BASELINE ===")
    print(base.to_string(index=False))
    print("\n=== ETF-011 VALIDATION TOP 20 ===")
    print(top.to_string(index=False))

    keys = top.head(10)[["inverse_fraction","score","confirm","vix_percentile","breadth_threshold"]]
    hold = out[out.split == "holdout"].merge(keys, on=["inverse_fraction","score","confirm","vix_percentile","breadth_threshold"])
    print("\n=== ETF-011 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(hold.sort_values(["sharpe","annualized_return"], ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
