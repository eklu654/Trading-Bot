"""ETF-018 canonical multi-signal bearish transition research.

Tests whether a *collection* of ex-ante signals can improve the defensive
transition into inverse ETFs versus the canonical ETF-001 cash state.

Signals:
- trend: price/200-DMA, 200-DMA slope, 50-DMA vs 200-DMA
- MACD: bearish line relationship, negative histogram, histogram deterioration
- channels: Donchian 20/40/60 breakdowns (prior-channel values avoid lookahead)
- momentum: 20/60-session returns
- volatility: VIX percentile and 5-session change
- breadth: cross-market 200-DMA weakness and MACD weakness

The experiment deliberately uses ETF-001 accounting:
common bull-ETF calendar, unadjusted closes for signals, adjusted closes for
returns, next-session execution, 25% permanent cash, and independently rebased
train/validation/holdout metrics.

No same-underlying bull/bear overlap is possible: when a sleeve is defensive,
its bull holding is zero before any inverse allocation is applied.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"

BULL = ("TQQQ", "SPXL", "SOXL")
UNDER = {"TQQQ": "QQQ", "SPXL": "SPY", "SOXL": "SOXX"}
BEAR = {"TQQQ": "SQQQ", "SPXL": "SPXS", "SOXL": "SOXS"}

# Additional broad/sector proxies are used only for cross-market breadth.
BREADTH_UNDERLYINGS = ("QQQ", "SPY", "SOXX", "DIA", "IWM")
SLEEVE = 0.25
FRACTIONS = (0.25, 0.50, 0.75, 1.00)
THRESHOLDS = (0.40, 0.50, 0.60, 0.70)
CONFIRM = (1, 2, 3)
RELEASE = (0.20, 0.30, 0.40)

SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}

VARIANTS = {
    "trend_only": ("trend",),
    "trend_macd": ("trend", "macd"),
    "trend_channel": ("trend", "channel"),
    "trend_macd_channel": ("trend", "macd", "channel"),
    "full": ("trend", "macd", "channel", "momentum", "volatility", "breadth"),
}


def load(symbol: str) -> pd.DataFrame:
    return pd.read_csv(
        DATA / f"{symbol.lower()}_daily.csv",
        parse_dates=["Date"],
    ).set_index("Date").sort_index()


def metrics(r: pd.Series) -> tuple[float, float, float, float, float, float, float]:
    r = r.dropna()
    eq = (1.0 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    total = eq.iloc[-1] - 1.0
    ann = (1.0 + total) ** (1.0 / years) - 1.0
    dd = (eq / eq.cummax() - 1.0).min()
    vol = r.std(ddof=1) * np.sqrt(252)
    sharpe = r.mean() / r.std(ddof=1) * np.sqrt(252)
    downside = r.where(r < 0).std(ddof=1)
    sortino = r.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside > 0 else np.nan
    return ann, total, dd, vol, sharpe, sortino, 5000.0 * eq.iloc[-1]


def common_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    bull_prices = {s: load(s) for s in BULL}
    bear_prices = {s: load(s) for s in BEAR.values()}
    under_prices = {s: load(s) for s in BREADTH_UNDERLYINGS}
    vix = pd.read_csv(DATA / "vix_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()["vix"]

    # Exact ETF-001 signal calendar: all three bull ETFs must be present.
    close = pd.concat({s: bull_prices[s]["close"] for s in BULL}, axis=1).dropna()
    close["vix"] = vix.reindex(close.index).ffill()

    adj = pd.concat(
        {**{s: bull_prices[s]["adj_close"] for s in BULL},
         **{s: bear_prices[s]["adj_close"] for s in BEAR.values()}},
        axis=1,
    ).reindex(close.index)

    return close, adj


def make_features(close: pd.DataFrame) -> tuple[dict[str, pd.Series], int]:
    features: dict[str, pd.Series] = {}

    # Per-sleeve features are market-wide averages across the three relevant
    # underlyings, making the trigger a coordinated transition rather than a
    # noisy single-ETF switch.
    under_closes = {u: load(u)["close"].reindex(close.index).ffill() for u in UNDER.values()}
    market = pd.concat(under_closes, axis=1)

    trend_parts = []
    macd_parts = []
    channel_parts = []
    momentum_parts = []
    for u, c in market.items():
        ma200 = c.rolling(200, min_periods=200).mean()
        ma50 = c.rolling(50, min_periods=50).mean()
        slope = ma200.pct_change(20)

        ema12 = c.ewm(span=12, adjust=False).mean()
        ema26 = c.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal

        prior20 = c.rolling(20, min_periods=20).min().shift(1)
        prior40 = c.rolling(40, min_periods=40).min().shift(1)
        prior60 = c.rolling(60, min_periods=60).min().shift(1)

        trend_parts.append(pd.concat([
            (c < ma200).astype(float),
            (slope < 0).astype(float),
            (ma50 < ma200).astype(float),
        ], axis=1).mean(axis=1))
        macd_parts.append(pd.concat([
            (macd < signal).astype(float),
            (hist < 0).astype(float),
            (hist.diff(5) < 0).astype(float),
        ], axis=1).mean(axis=1))
        channel_parts.append(pd.concat([
            (c < prior20).astype(float),
            (c < prior40).astype(float),
            (c < prior60).astype(float),
        ], axis=1).mean(axis=1))
        momentum_parts.append(pd.concat([
            (c.pct_change(20) < 0).astype(float),
            (c.pct_change(60) < 0).astype(float),
        ], axis=1).mean(axis=1))

    # Each family score is normalized to [0,1], so threshold comparisons are
    # comparable across variants with different numbers of component signals.
    features["trend"] = pd.concat(trend_parts, axis=1).mean(axis=1)
    features["macd"] = pd.concat(macd_parts, axis=1).mean(axis=1)
    features["channel"] = pd.concat(channel_parts, axis=1).mean(axis=1)
    features["momentum"] = pd.concat(momentum_parts, axis=1).mean(axis=1)

    vix = close["vix"]
    vix_pct = vix.rolling(253, min_periods=60).apply(
        lambda x: float((x[:-1] <= x[-1]).mean()) if len(x) > 30 else np.nan,
        raw=True,
    )
    features["volatility"] = pd.concat([
        (vix_pct >= 0.70).astype(float),
        (vix.pct_change(5) > 0).astype(float),
    ], axis=1).mean(axis=1)

    broad = pd.concat(
        {u: load(u)["close"].reindex(close.index).ffill() for u in BREADTH_UNDERLYINGS},
        axis=1,
    )
    broad_ma = broad.rolling(200, min_periods=200).mean()
    below_dma = (broad < broad_ma).mean(axis=1)

    broad_macd_negative = []
    for u in BREADTH_UNDERLYINGS:
        c = broad[u]
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        sig = macd.ewm(span=9, adjust=False).mean()
        broad_macd_negative.append((macd < sig).astype(float))
    macd_weak = pd.concat(broad_macd_negative, axis=1).mean(axis=1)
    features["breadth"] = pd.concat([
        below_dma,
        macd_weak,
    ], axis=1).mean(axis=1)

    return features, len(UNDER)


def build_signal(features: dict[str, pd.Series], variant: str, threshold: float,
                  confirm: int, release: float) -> pd.Series:
    families = VARIANTS[variant]
    score = pd.concat([features[f] for f in families], axis=1).mean(axis=1)

    # Enter only after the composite has remained bearish for N closes.
    raw = (score >= threshold).fillna(False)
    runs = raw.astype(int).groupby((~raw).cumsum()).cumsum()
    enter = (runs >= confirm).astype(bool)

    # Hysteresis: once defensive, require a meaningfully improved composite
    # score before releasing the inverse allocation.
    release_raw = (score <= release).fillna(False)
    release_runs = release_raw.astype(int).groupby((~release_raw).cumsum()).cumsum()
    release_ok = (release_runs >= confirm).astype(bool)

    state = False
    out = []
    for e, x in zip(enter, release_ok):
        if state:
            if x:
                state = False
        elif e:
            state = True
        out.append(state)
    return pd.Series(out, index=score.index).shift(1).fillna(False).astype(bool)


def main() -> None:
    close, adj = common_frame()
    features, _ = make_features(close)
    returns = adj.pct_change().fillna(0.0)

    # Canonical ETF-001 baseline: 25% cash and 25% in each bull sleeve whenever
    # its 200-DMA/5-session state is active.
    bulls = {}
    for s in BULL:
        c = close[s]
        ma = c.rolling(200, min_periods=200).mean()
        state = False
        above = 0
        out = []
        for p, m in zip(c, ma):
            if pd.isna(m) or p < m:
                state = False
                above = 0
            elif not state:
                above += 1
                if above >= 5:
                    state = True
            out.append(state)
        bulls[s] = pd.Series(out, index=c.index).shift(1).fillna(False).astype(bool)

    baseline = pd.Series(0.0, index=close.index)
    for s in BULL:
        baseline = baseline.add(SLEEVE * returns[s].where(bulls[s], 0.0), fill_value=0.0)

    rows = []
    for variant in VARIANTS:
        for threshold in THRESHOLDS:
            for confirm in CONFIRM:
                for release in RELEASE:
                    gate = build_signal(features, variant, threshold, confirm, release)
                    for frac in FRACTIONS:
                        daily = pd.Series(0.0, index=close.index)
                        inverse_days = 0
                        early_days = 0
                        for s in BULL:
                            bear = BEAR[s]
                            bull = bulls[s]
                            # The inverse replaces, never coexists with, the
                            # same-underlying bull sleeve.
                            normal = bull & ~gate
                            daily = daily.add(
                                SLEEVE * returns[s].where(normal, 0.0),
                                fill_value=0.0,
                            )
                            daily = daily.add(
                                SLEEVE * frac * returns[bear].where(gate, 0.0),
                                fill_value=0.0,
                            )
                        inverse_days = int(gate.sum())
                        early_days = int((gate & pd.concat(bulls.values(), axis=1).any(axis=1)).sum())

                        for split, (start, end) in SPLITS.items():
                            m = metrics(daily.loc[start:end])
                            b = metrics(baseline.loc[start:end])
                            rows.append({
                                "variant": variant,
                                "threshold": threshold,
                                "confirm": confirm,
                                "release": release,
                                "inverse_fraction": frac,
                                "split": split,
                                "annualized_return": m[0],
                                "total_return": m[1],
                                "max_drawdown": m[2],
                                "annualized_volatility": m[3],
                                "sharpe": m[4],
                                "sortino": m[5],
                                "ending_value_5000": m[6],
                                "inverse_days": inverse_days,
                                "early_override_days": early_days,
                                "baseline_annualized_return": b[0],
                                "baseline_sharpe": b[4],
                                "baseline_max_drawdown": b[2],
                            })

    out = pd.DataFrame(rows)
    out.to_csv(DATA / "etf018_canonical_multisignal_transition.csv", index=False)

    val = out[out["split"] == "validation"].copy()
    val["sharpe_delta"] = val["sharpe"] - val["baseline_sharpe"]
    val["return_delta"] = val["annualized_return"] - val["baseline_annualized_return"]

    # Selection is intentionally conservative: show configurations that improve
    # validation Sharpe, but require holdout inspection before any promotion.
    top = val.sort_values(["sharpe_delta", "return_delta"], ascending=False).head(20)
    print("=== ETF-018 VALIDATION TOP 20 ===")
    print(top.to_string(index=False))

    keys = top.head(10)[
        ["variant", "threshold", "confirm", "release", "inverse_fraction"]
    ]
    hold = out[out["split"] == "holdout"].merge(
        keys,
        on=["variant", "threshold", "confirm", "release", "inverse_fraction"],
    )
    print("\n=== ETF-018 HOLDOUT FOR VALIDATION TOP 10 ===")
    print(
        hold.sort_values(["sharpe", "annualized_return"], ascending=False)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
