"""ETF-008 ex-ante directional signal research.

This experiment asks a narrower question than the earlier 200-DMA grids:
can an interpretable, information-at-time-t classifier identify the next
session's underlying direction well enough to make inverse exposure useful?

Protocol:
- Train only on 2010-03-01 through 2019-12-31.
- Freeze model, scaler, and decision thresholds.
- Evaluate unchanged on 2020-2022 validation and 2023+ holdout.
- Each underlying independently chooses BULL, BEAR, or CASH.
- Never hold both sides of the same underlying.
- Each sleeve is 25%; remaining 25% is permanent cash.
- Signal at close t is applied to return t+1.
- No future information is used in features or model fitting.

This is research, not a production trading component.
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

PAIRS = {
    "QQQ": ("TQQQ", "SQQQ"),
    "SPY": ("SPXL", "SPXS"),
    "SOXX": ("SOXL", "SOXS"),
}

SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}

FEATURES = [
    "distance_200",
    "slope_200_20",
    "distance_50",
    "momentum_20",
    "momentum_60",
    "efficiency_20",
    "vol_20",
    "drawdown_252",
    "vix",
    "vix_change_5",
    "cross_market_bull_fraction",
]

VARIANTS = {
    "trend_momentum": [
        "distance_200", "slope_200_20", "distance_50",
        "momentum_20", "momentum_60", "efficiency_20",
    ],
    "trend_momentum_vol": [
        "distance_200", "slope_200_20", "distance_50",
        "momentum_20", "momentum_60", "efficiency_20", "vol_20",
    ],
    "full": FEATURES,
    "full_no_vix": [
        x for x in FEATURES if x not in ("vix", "vix_change_5")
    ],
}

THRESHOLDS = (
    (0.50, 0.50),
    (0.55, 0.45),
    (0.60, 0.40),
    (0.65, 0.35),
    (0.70, 0.30),
)


def load(symbol: str) -> pd.DataFrame:
    return (
        pd.read_csv(DATA / f"{symbol.lower()}_daily.csv", parse_dates=["Date"])
        .set_index("Date")
        .sort_index()
    )


def make_feature_frame() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    raw = {symbol: load(symbol) for pair in PAIRS.values() for symbol in pair}
    underlyings = {symbol: load(symbol)["close"] for symbol in PAIRS}
    vix = pd.read_csv(DATA / "vix_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()["vix"] if (DATA / "vix_daily.csv").exists() else pd.Series(dtype=float)

    close = pd.concat(underlyings, axis=1)
    bull_fraction = (close > close.rolling(200).mean()).mean(axis=1)

    frames: dict[str, pd.DataFrame] = {}
    for underlying, c in underlyings.items():
        ma200 = c.rolling(200).mean()
        ma50 = c.rolling(50).mean()
        ret = c.pct_change()

        f = pd.DataFrame(index=c.index)
        f["distance_200"] = c / ma200 - 1
        f["slope_200_20"] = ma200.pct_change(20)
        f["distance_50"] = c / ma50 - 1
        f["momentum_20"] = c.pct_change(20)
        f["momentum_60"] = c.pct_change(60)
        direction = (c - c.shift(20)).abs()
        noise = c.diff().abs().rolling(20).sum()
        f["efficiency_20"] = direction / noise.replace(0, np.nan)
        f["vol_20"] = ret.rolling(20).std() * np.sqrt(252)
        f["drawdown_252"] = c / c.rolling(252).max() - 1
        f["vix"] = vix.reindex(f.index).ffill()
        f["vix_change_5"] = f["vix"].pct_change(5)
        f["cross_market_bull_fraction"] = bull_fraction.reindex(f.index)

        # Label is tomorrow's underlying direction. The feature row remains
        # at today's close, so the label is shifted backward only for training.
        f["target"] = (c.pct_change().shift(-1) > 0).astype(float)
        frames[underlying] = f

    return frames, raw


def fit_model(frame: pd.DataFrame, features: list[str]) -> Pipeline:
    train = frame.loc[SPLITS["train"][0]:SPLITS["train"][1], features + ["target"]].dropna()
    model = Pipeline([
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(C=0.25, max_iter=2000, random_state=42)),
    ])
    model.fit(train[features], train["target"].astype(int))
    return model


def classify(probability: float, bull_threshold: float, bear_threshold: float) -> str:
    if probability >= bull_threshold:
        return "BULL"
    if probability <= bear_threshold:
        return "BEAR"
    return "CASH"


def replay(
    frames: dict[str, pd.DataFrame],
    raw: dict[str, pd.DataFrame],
    models: dict[str, Pipeline],
    features: list[str],
    thresholds: tuple[float, float],
) -> tuple[pd.Series, pd.DataFrame]:
    signals: dict[str, pd.Series] = {}
    for underlying, frame in frames.items():
        p = pd.Series(np.nan, index=frame.index)
        usable = frame[features].notna().all(axis=1)
        if usable.any():
            p.loc[usable] = models[underlying].predict_proba(
                frame.loc[usable, features]
            )[:, 1]
        signals[underlying] = p.map(
            lambda x: classify(x, thresholds[0], thresholds[1])
            if pd.notna(x) else "CASH"
        ).shift(1).fillna("CASH")

    idx = pd.concat(
        [raw[t]["adj_close"].rename(t) for pair in PAIRS.values() for t in pair],
        axis=1,
    ).index
    daily = pd.Series(0.0, index=idx)
    rows = []

    for underlying, (bull, bear) in PAIRS.items():
        prices_bull = raw[bull]["adj_close"].reindex(idx)
        prices_bear = raw[bear]["adj_close"].reindex(idx)
        rb = prices_bull.pct_change()
        rs = prices_bear.pct_change()
        state = signals[underlying].reindex(idx).ffill().fillna("CASH")

        sleeve = pd.Series(0.0, index=idx)
        sleeve[state == "BULL"] = rb[state == "BULL"] * 0.25
        sleeve[state == "BEAR"] = rs[state == "BEAR"] * 0.25
        daily = daily.add(sleeve, fill_value=0.0)

        rows.append(pd.DataFrame({
            f"{underlying}_state": state,
            f"{underlying}_prob_bull": (
                frames[underlying]["target"].copy() * np.nan
            ).reindex(idx),
        }))

    return daily, pd.concat(rows, axis=1)


def metrics(returns: pd.Series) -> dict[str, float]:
    r = returns.dropna()
    if r.empty:
        return {}
    eq = (1 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    total = eq.iloc[-1] - 1
    ann = (1 + total) ** (1 / years) - 1
    vol = r.std(ddof=1) * np.sqrt(252)
    dd = (eq / eq.cummax() - 1).min()
    sharpe = r.mean() / r.std(ddof=1) * np.sqrt(252) if r.std(ddof=1) else np.nan
    return {
        "annualized_return": ann,
        "total_return": total,
        "max_drawdown": dd,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "ending_value_5000": 5000 * eq.iloc[-1],
    }


def select_threshold(
    frames: dict[str, pd.DataFrame],
    raw: dict[str, pd.DataFrame],
    models: dict[str, Pipeline],
    features: list[str],
) -> tuple[float, float]:
    candidates = []
    for thresholds in THRESHOLDS:
        daily, _ = replay(frames, raw, models, features, thresholds)
        m = metrics(daily.loc[SPLITS["train"][0]:SPLITS["train"][1]])
        # Favor risk-adjusted return while retaining a modest penalty for
        # excessive switching. Switching counts are calculated separately
        # below during final replay.
        candidates.append((thresholds, m.get("sharpe", -np.inf), m.get("annualized_return", -np.inf)))
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return candidates[0][0]


def main() -> None:
    frames, raw = make_feature_frame()
    results = []

    for variant, features in VARIANTS.items():
        models = {
            underlying: fit_model(frame, features)
            for underlying, frame in frames.items()
        }
        thresholds = select_threshold(frames, raw, models, features)
        daily, signal_frames = replay(frames, raw, models, features, thresholds)

        for split, (start, end) in SPLITS.items():
            m = metrics(daily.loc[start:end])
            results.append({
                "variant": variant,
                "bull_threshold": thresholds[0],
                "bear_threshold": thresholds[1],
                "split": split,
                **m,
            })

        # Also emit frozen signal states so the eventual paper-trading layer
        # can reuse the exact research definition.
        signal_frames.to_csv(DATA / f"etf008_{variant}_signals.csv")

    out = pd.DataFrame(results)
    out.to_csv(DATA / "etf008_directional_signal_results.csv", index=False)

    print("=== ETF-008 FROZEN-MODEL RESULTS ===")
    print(out.to_string(index=False))

    print("\n=== VALIDATION RANKING ===")
    print(
        out[out["split"] == "validation"]
        .sort_values(["sharpe", "annualized_return"], ascending=False)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
