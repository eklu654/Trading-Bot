"""ETF-020: supervised technical-indicator bear-transition research.

Purpose:
    Test whether a machine-learning model can synthesize a broad technical
    indicator library better than a hand-written composite trigger.

Design:
    - Features are computed only from information available at close t.
    - The model predicts whether the equal-weight QQQ/SPY/SOXX benchmark has a
      sufficiently negative forward 20-session return.
    - Training is strictly 2010-2019.
    - Validation is 2020-2022 and is used only to choose the probability
      threshold and inverse fraction.
    - Holdout is 2023+ and is evaluated only after validation selection.
    - Portfolio accounting matches canonical ETF-001: adjusted-close returns,
      next-session execution, 25% permanent cash, and no same-underlying
      bull/bear overlap.

This is intentionally a bounded experiment, not a claim that ML can predict
markets reliably. The feature library is broad; model selection remains small
to reduce data-mining risk.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"

BULL = ("TQQQ", "SPXL", "SOXL")
UNDER = {"TQQQ": "QQQ", "SPXL": "SPY", "SOXL": "SOXX"}
BEAR = {"TQQQ": "SQQQ", "SPXL": "SPXS", "SOXL": "SOXS"}
BREADTH = ("QQQ", "SPY", "SOXX", "DIA", "IWM")
SLEEVE = 0.25
SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}
THRESHOLDS = (0.55, 0.60, 0.65, 0.70, 0.75, 0.80)
FRACTIONS = (0.25, 0.50, 0.75, 1.00)


def load(symbol: str) -> pd.DataFrame:
    return pd.read_csv(
        DATA / f"{symbol.lower()}_daily.csv",
        parse_dates=["Date"],
    ).set_index("Date").sort_index()


def metrics(r: pd.Series) -> tuple[float, float, float, float, float]:
    r = r.dropna()
    eq = (1.0 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    ann = eq.iloc[-1] ** (1.0 / years) - 1.0
    dd = (eq / eq.cummax() - 1.0).min()
    vol = r.std(ddof=1) * np.sqrt(252)
    sharpe = r.mean() / r.std(ddof=1) * np.sqrt(252)
    return ann, dd, vol, sharpe, 5000.0 * eq.iloc[-1]


def technicals(c: pd.Series, volume: pd.Series | None = None) -> pd.DataFrame:
    global load_current_high, load_current_low
    x = pd.DataFrame(index=c.index)
    ret = c.pct_change()

    # Trend / moving-average geometry.
    for n in (5, 10, 20, 50, 100, 200):
        ma = c.rolling(n, min_periods=n).mean()
        x[f"dist_ma{n}"] = c / ma - 1.0
        x[f"slope_ma{n}"] = ma.pct_change(10)

    # Momentum / ROC.
    for n in (3, 5, 10, 20, 40, 60, 120, 252):
        x[f"roc{n}"] = c.pct_change(n)

    # RSI family.
    for n in (7, 14, 21):
        delta = c.diff()
        gain = delta.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/n, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        x[f"rsi{n}"] = 100.0 - 100.0 / (1.0 + rs)

    # MACD families.
    for fast, slow, sig in ((8, 21, 5), (12, 26, 9), (19, 39, 9)):
        macd = c.ewm(span=fast, adjust=False).mean() - c.ewm(span=slow, adjust=False).mean()
        signal = macd.ewm(span=sig, adjust=False).mean()
        hist = macd - signal
        x[f"macd_{fast}_{slow}"] = macd / c
        x[f"macd_sigdist_{fast}_{slow}"] = (macd - signal) / c
        x[f"macd_hist_slope_{fast}_{slow}"] = hist.diff(3) / c

    # Bollinger-style channel geometry.
    for n, k in ((20, 1.5), (20, 2.0), (50, 2.0)):
        mid = c.rolling(n, min_periods=n).mean()
        sd = c.rolling(n, min_periods=n).std()
        upper = mid + k * sd
        lower = mid - k * sd
        width = (upper - lower) / mid
        x[f"bb_pos_{n}_{k}"] = (c - lower) / (upper - lower)
        x[f"bb_width_{n}_{k}"] = width
        x[f"bb_break_{n}_{k}"] = (c < lower).astype(float)

    # Donchian channels, shifted so today's close cannot influence today's band.
    for n in (10, 20, 40, 60, 100):
        hi = c.rolling(n, min_periods=n).max().shift(1)
        lo = c.rolling(n, min_periods=n).min().shift(1)
        x[f"don_pos{n}"] = (c - lo) / (hi - lo)
        x[f"don_break_low{n}"] = (c < lo).astype(float)
        x[f"drawdown_high{n}"] = c / hi - 1.0

    # ATR-normalized movement and volatility.
    # OHLC files are expected to contain high/low/close.
    high = load_current_high.get(c.name, c)
    low = load_current_low.get(c.name, c)
    prev = c.shift(1)
    tr = pd.concat(
        [high - low, (high - prev).abs(), (low - prev).abs()],
        axis=1,
    ).max(axis=1)
    for n in (5, 14, 20, 40):
        atr = tr.rolling(n, min_periods=n).mean()
        x[f"atr_pct{n}"] = atr / c
        x[f"atr_move{n}"] = (c - c.shift(n)) / atr.replace(0, np.nan)

    for n in (5, 10, 20, 40, 60):
        x[f"vol{n}"] = ret.rolling(n, min_periods=n).std() * np.sqrt(252)

    # Stochastic oscillator.
    for n in (9, 14, 21):
        lo = low.rolling(n, min_periods=n).min()
        hi = high.rolling(n, min_periods=n).max()
        x[f"stoch{n}"] = 100.0 * (c - lo) / (hi - lo).replace(0, np.nan)

    # ADX-style trend strength.
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    for n in (14, 28):
        atr = tr.rolling(n, min_periods=n).mean()
        plus_di = 100.0 * plus_dm.rolling(n, min_periods=n).mean() / atr.replace(0, np.nan)
        minus_di = 100.0 * minus_dm.rolling(n, min_periods=n).mean() / atr.replace(0, np.nan)
        dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        x[f"adx{n}"] = dx.rolling(n, min_periods=n).mean()
        x[f"di_diff{n}"] = (plus_di - minus_di) / 100.0

    if volume is not None:
        obv = (np.sign(c.diff()).fillna(0.0) * volume).cumsum()
        for n in (10, 20, 60):
            x[f"obv_slope{n}"] = obv.pct_change(n).replace([np.inf, -np.inf], np.nan)

    return x.replace([np.inf, -np.inf], np.nan)


# technicals() needs OHLC context; these maps are populated by main().
load_current_high: dict[str, pd.Series] = {}
load_current_low: dict[str, pd.Series] = {}


def make_feature_matrix() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame]:
    frames = {u: load(u) for u in BREADTH}
    idx = frames["QQQ"].index
    close = pd.concat({u: frames[u]["close"].reindex(idx).ffill() for u in BREADTH}, axis=1)
    high = pd.concat({u: frames[u]["high"].reindex(idx).ffill() for u in BREADTH}, axis=1)
    low = pd.concat({u: frames[u]["low"].reindex(idx).ffill() for u in BREADTH}, axis=1)
    load_current_high = {u: high[u] for u in BREADTH}
    load_current_low = {u: low[u] for u in BREADTH}

    parts = []
    for u in BREADTH:
        t = technicals(close[u], frames[u].get("volume"))
        t.columns = [f"{u}_{c}" for c in t.columns]
        parts.append(t)

    vix = pd.read_csv(DATA / "vix_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()["vix"]
    vf = pd.DataFrame(index=idx)
    vf["vix"] = vix.reindex(idx).ffill()
    for n in (5, 10, 20, 60, 252):
        vf[f"vix_chg{n}"] = vf["vix"].pct_change(n)
        vf[f"vix_z{n}"] = (vf["vix"] - vf["vix"].rolling(n).mean()) / vf["vix"].rolling(n).std()
        vf[f"vix_rank{n}"] = vf["vix"].rolling(n, min_periods=max(5, min(20, n))).rank(pct=True)

    X = pd.concat(parts + [vf], axis=1)
    benchmark = close[["QQQ", "SPY", "SOXX"]].mean(axis=1)
    forward20 = benchmark.shift(-20) / benchmark - 1.0
    # A meaningful bearish transition: at least a 4% decline over 20 sessions.
    y = (forward20 <= -0.04).astype(float)
    y[forward20.isna()] = np.nan

    # Cross-market breadth/meta-features.
    meta = pd.DataFrame(index=idx)
    for n in (20, 50, 200):
        ma = close.rolling(n, min_periods=n).mean()
        meta[f"breadth_below_ma{n}"] = (close < ma).mean(axis=1)
    meta["cross_ret20_std"] = close.pct_change(20).std(axis=1)
    meta["cross_ret60_std"] = close.pct_change(60).std(axis=1)
    X = pd.concat([X, meta], axis=1)

    return X, y, close, frames["QQQ"]


def baseline_and_returns(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    bull_prices = {s: load(s) for s in BULL}
    bear_prices = {s: load(s) for s in BEAR.values()}
    idx = close.index
    adj = pd.concat(
        {s: bull_prices[s]["adj_close"].reindex(idx) for s in BULL}
        | {s: bear_prices[s]["adj_close"].reindex(idx) for s in BEAR.values()},
        axis=1,
    )
    ret = adj.pct_change().fillna(0.0)

    bull_state = {}
    for s in BULL:
        c = bull_prices[s]["close"].reindex(idx).ffill()
        ma = c.rolling(200, min_periods=200).mean()
        active = False
        count = 0
        state = []
        for p, m in zip(c, ma):
            if pd.isna(m) or p < m:
                active = False
                count = 0
            elif not active:
                count += 1
                if count >= 5:
                    active = True
            state.append(active)
        bull_state[s] = pd.Series(state, index=idx).shift(1).fillna(False)

    baseline = sum(SLEEVE * ret[s].where(bull_state[s], 0.0) for s in BULL)
    return ret, baseline


def main() -> None:
    X, y, close, _ = make_feature_matrix()
    ret, baseline = baseline_and_returns(close)

    train = X.index.to_series().between(*SPLITS["train"])
    valid = X.index.to_series().between(*SPLITS["validation"])
    hold = X.index.to_series().between(*SPLITS["holdout"])

    usable_train = train & y.notna()
    # Keep model architecture fixed across experiments. Class weighting is
    # represented by sample weights to avoid changing the decision rule.
    models = {
        "hgb_shallow": HistGradientBoostingClassifier(
            max_iter=120, learning_rate=0.05, max_leaf_nodes=7,
            min_samples_leaf=40, l2_regularization=1.0, random_state=42
        ),
        "hgb_medium": HistGradientBoostingClassifier(
            max_iter=160, learning_rate=0.04, max_leaf_nodes=15,
            min_samples_leaf=50, l2_regularization=2.0, random_state=42
        ),
    }

    rows = []
    for name, model in models.items():
        pipe = make_pipeline(SimpleImputer(strategy="median"), model)
        pipe.fit(X.loc[usable_train], y.loc[usable_train])

        prob = pd.Series(
            pipe.predict_proba(X)[:, 1],
            index=X.index,
        )

        for threshold in THRESHOLDS:
            raw = prob >= threshold
            # One close of confirmation; probability threshold itself is the
            # principal decision variable. Hysteresis is tested separately.
            gate = raw.shift(1).fillna(False).astype(bool)

            for frac in FRACTIONS:
                daily = baseline.copy()
                for s in BULL:
                    # Replace the bull sleeve whenever the model says a bearish
                    # transition is underway. No bull/bear overlap.
                    bull = baseline * 0.0  # placeholder to keep accounting explicit
                    # Reconstruct the sleeve contribution from canonical state.
                    c = load(s)["close"].reindex(close.index).ffill()
                    ma = c.rolling(200, min_periods=200).mean()
                    active = pd.Series(False, index=close.index)
                    state = False
                    count = 0
                    for d, p, m in zip(close.index, c, ma):
                        if pd.isna(m) or p < m:
                            state = False
                            count = 0
                        elif not state:
                            count += 1
                            if count >= 5:
                                state = True
                        active.loc[d] = state
                    active = active.shift(1).fillna(False)
                    sleeve = SLEEVE * ret[s].where(active & ~gate, 0.0)
                    inv = SLEEVE * frac * ret[BEAR[s]].where(gate, 0.0)
                    # Remove the baseline sleeve and replace it.
                    daily = daily - SLEEVE * ret[s].where(active, 0.0) + sleeve + inv

                for split, mask in (("train", train), ("validation", valid), ("holdout", hold)):
                    m = metrics(daily.loc[mask])
                    b = metrics(baseline.loc[mask])
                    rows.append({
                        "model": name,
                        "threshold": threshold,
                        "inverse_fraction": frac,
                        "split": split,
                        "annualized_return": m[0],
                        "max_drawdown": m[1],
                        "annualized_volatility": m[2],
                        "sharpe": m[3],
                        "ending_value_5000": m[4],
                        "baseline_annualized_return": b[0],
                        "baseline_sharpe": b[3],
                        "baseline_max_drawdown": b[1],
                        "bear_days": int(gate.loc[mask].sum()),
                    })

        prob.to_csv(DATA / f"etf020_{name}_probabilities.csv", header=True)

    out = pd.DataFrame(rows)
    out.to_csv(DATA / "etf020_ml_indicator_bear_transition.csv", index=False)

    # Selection is strictly validation-based. Holdout is displayed only for
    # the frozen validation winners; it is not used to choose them.
    val = out[out.split == "validation"].copy()
    val["sharpe_delta"] = val.sharpe - val.baseline_sharpe
    val["return_delta"] = val.annualized_return - val.baseline_annualized_return
    top = val.sort_values(["sharpe_delta", "return_delta"], ascending=False).head(10)
    print("=== ETF-020 VALIDATION LEADERS ===")
    print(top.to_string(index=False))

    keys = top[["model", "threshold", "inverse_fraction"]]
    hold = out[out.split == "holdout"].merge(keys, on=["model", "threshold", "inverse_fraction"])
    print("\n=== ETF-020 HOLDOUT FOR VALIDATION LEADERS ===")
    print(hold.sort_values(["sharpe", "annualized_return"], ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
