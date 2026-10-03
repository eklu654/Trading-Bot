"""ETF-009 multi-horizon directional signal research.

ETF-008 showed that predicting the next single session is too noisy. ETF-009
tests whether the same ex-ante feature set becomes useful when the model
predicts sustained 5/10/20-session direction.

The model is trained only on the chronological training period. Model,
scaler, horizon, threshold, and confirmation settings are then frozen for
validation and holdout. Signals are shifted one session before ETF returns.

No same-underlying bull/bear overlap is possible: each sleeve resolves to
BULL, BEAR, or CASH.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"

PAIRS = {"QQQ": ("TQQQ", "SQQQ"), "SPY": ("SPXL", "SPXS"), "SOXX": ("SOXL", "SOXS")}
SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}
FEATURES = [
    "distance_200", "slope_200_20", "distance_50",
    "momentum_20", "momentum_60", "efficiency_20",
    "vol_20", "drawdown_252", "vix", "vix_change_5",
    "cross_market_bull_fraction",
]
HORIZONS = (5, 10, 20)
THRESHOLDS = ((0.55, 0.45), (0.60, 0.40), (0.65, 0.35))
CONFIRM = (1, 3, 5)


def load_price(symbol: str) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{symbol.lower()}_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()


def features_and_labels() -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    under = {x: load_price(x)["close"] for x in PAIRS}
    raw = {x: load_price(x) for p in PAIRS.values() for x in p}
    vix = pd.read_csv(DATA / "vix_daily.csv", parse_dates=["Date"]).set_index("Date")["vix"].sort_index()
    close = pd.concat(under, axis=1)
    broad = (close > close.rolling(200).mean()).mean(axis=1)
    frames = {}
    for name, c in under.items():
        ma200, ma50 = c.rolling(200).mean(), c.rolling(50).mean()
        f = pd.DataFrame(index=c.index)
        f["distance_200"] = c / ma200 - 1
        f["slope_200_20"] = ma200.pct_change(20)
        f["distance_50"] = c / ma50 - 1
        f["momentum_20"] = c.pct_change(20)
        f["momentum_60"] = c.pct_change(60)
        f["efficiency_20"] = (c - c.shift(20)).abs() / c.diff().abs().rolling(20).sum().replace(0, np.nan)
        f["vol_20"] = c.pct_change().rolling(20).std() * np.sqrt(252)
        f["drawdown_252"] = c / c.rolling(252).max() - 1
        f["vix"] = vix.reindex(c.index).ffill()
        f["vix_change_5"] = f["vix"].pct_change(5)
        f["cross_market_bull_fraction"] = broad.reindex(c.index)
        for h in HORIZONS:
            f[f"target_{h}"] = (c.shift(-h) / c - 1 > 0).astype(float)
        frames[name] = f
    return frames, raw


def model_for(frame: pd.DataFrame, horizon: int) -> Pipeline:
    cols = FEATURES
    train = frame.loc[SPLITS["train"][0]:SPLITS["train"][1], cols + [f"target_{horizon}"]].dropna()
    model = Pipeline([
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(C=0.25, max_iter=2000, random_state=42)),
    ])
    model.fit(train[cols], train[f"target_{horizon}"].astype(int))
    return model


def metrics(r: pd.Series) -> dict[str, float]:
    r = r.dropna()
    eq = (1 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    total = eq.iloc[-1] - 1
    ann = (1 + total) ** (1 / years) - 1
    dd = (eq / eq.cummax() - 1).min()
    vol = r.std(ddof=1) * np.sqrt(252)
    sh = r.mean() / r.std(ddof=1) * np.sqrt(252) if r.std(ddof=1) else np.nan
    return {"annualized_return": ann, "total_return": total, "max_drawdown": dd,
            "annualized_volatility": vol, "sharpe": sh, "ending_value_5000": 5000 * eq.iloc[-1]}


def replay(frames, raw, models, horizon, threshold, confirm):
    states = {}
    idx = pd.concat([raw[x]["adj_close"] for x in raw], axis=1).index
    for name, frame in frames.items():
        usable = frame[FEATURES].notna().all(axis=1)
        p = pd.Series(np.nan, index=frame.index)
        p.loc[usable] = models[name].predict_proba(frame.loc[usable, FEATURES])[:, 1]
        raw_state = p.map(
            lambda x: "BULL" if x >= threshold[0] else "BEAR" if x <= threshold[1] else "CASH"
            if pd.notna(x) else "CASH"
        )
        # Confirmation prevents a single noisy model observation from flipping
        # the sleeve. A new directional state must persist for confirm closes.
        confirmed = []
        current = "CASH"
        pending = None
        streak = 0
        for x in raw_state:
            if x == current:
                pending, streak = None, 0
            elif x == pending:
                streak += 1
                if streak >= confirm:
                    current, pending, streak = x, None, 0
            else:
                pending, streak = x, 1
            confirmed.append(current)
        states[name] = pd.Series(confirmed, index=frame.index).shift(1).fillna("CASH").reindex(idx).ffill().fillna("CASH")

    daily = pd.Series(0.0, index=idx)
    for name, (bull, bear) in PAIRS.items():
        rb = raw[bull]["adj_close"].reindex(idx).pct_change()
        rs = raw[bear]["adj_close"].reindex(idx).pct_change()
        st = states[name]
        daily = daily.add(rb.where(st == "BULL", 0).add(rs.where(st == "BEAR", 0), fill_value=0) * 0.25, fill_value=0)
    return daily


def main():
    frames, raw = features_and_labels()
    rows = []
    for horizon in HORIZONS:
        models = {name: model_for(frame, horizon) for name, frame in frames.items()}
        for threshold in THRESHOLDS:
            for confirm in CONFIRM:
                daily = replay(frames, raw, models, horizon, threshold, confirm)
                train = metrics(daily.loc[SPLITS["train"][0]:SPLITS["train"][1]])
                for split, (a, b) in SPLITS.items():
                    m = metrics(daily.loc[a:b])
                    rows.append({
                        "horizon": horizon, "bull_threshold": threshold[0],
                        "bear_threshold": threshold[1], "confirm": confirm,
                        "split": split, **m,
                        "train_sharpe": train["sharpe"],
                    })
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "etf009_multi_horizon_signal_results.csv", index=False)
    print("=== ETF-009 VALIDATION TOP 20 ===")
    print(out[out.split == "validation"].sort_values(["sharpe", "annualized_return"], ascending=False).head(20).to_string(index=False))
    print("\n=== ETF-009 HOLDOUT FOR VALIDATION TOP 10 CONFIGURATIONS ===")
    keys = out[out.split == "validation"].sort_values(["sharpe", "annualized_return"], ascending=False).head(10)[
        ["horizon", "bull_threshold", "bear_threshold", "confirm"]
    ]
    hold = out[out.split == "holdout"].merge(keys, on=["horizon", "bull_threshold", "bear_threshold", "confirm"])
    print(hold.sort_values(["sharpe", "annualized_return"], ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
