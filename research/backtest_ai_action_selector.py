"""E4 AI baseline: chronological Ridge action selector.

Research-only implementation. Features are known at decision close t; the
selected action earns its next-session return. Models predict each action's
forward 20-session return. Annual refits use only rows whose complete forward
target is known by the refit cutoff.

No hyperparameter search is performed: alpha=1.0 is fixed in advance.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

ACTIONS = {
    "cash": None,
    "SPY_1x": "SPY",
    "SPY_2x": "SSO",
    "SPY_3x": "SPXL",
    "QQQ_1x": "QQQ",
    "QQQ_2x": "QLD",
    "QQQ_3x": "TQQQ",
    "SOXX_1x": "SOXX",
    "SOXX_2x": "USD",
    "SOXX_3x": "SOXL",
}

FEATURE_WINDOWS = (20, 50, 100, 150, 200)
MOMENTUM_WINDOWS = (20, 60, 120, 252)
TARGET_HORIZON = 20
RIDGE_ALPHA = 1.0

SPLITS = {
    "train": ("2010-01-04", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-09-25"),
}


def load(symbol: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{symbol.lower()}_daily.csv",
                       parse_dates=["Date"]).set_index("Date").sort_index()


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    def pct(x: np.ndarray) -> float:
        if len(x) < 30 or not np.isfinite(x[-1]):
            return np.nan
        return float((x[:-1] <= x[-1]).mean())
    return series.rolling(window + 1).apply(pct, raw=True)


def build_features() -> pd.DataFrame:
    base = {s: load(s) for s in ("SPY", "QQQ", "SOXX")}
    index = base["SPY"].index.intersection(base["QQQ"].index).intersection(base["SOXX"].index)
    out = pd.DataFrame(index=index)

    for family in ("SPY", "QQQ", "SOXX"):
        close = base[family]["close"].reindex(index)
        ret = close.pct_change()
        ma = {}
        for window in FEATURE_WINDOWS:
            ma[window] = close.rolling(window).mean()
            out[f"{family}_dist_ma{window}"] = close / ma[window] - 1.0
        for window in MOMENTUM_WINDOWS:
            out[f"{family}_mom{window}"] = close.pct_change(window)
        out[f"{family}_rv20"] = ret.rolling(20).std() * np.sqrt(252)
        out[f"{family}_rv60"] = ret.rolling(60).std() * np.sqrt(252)
        out[f"{family}_dd252"] = close / close.rolling(252).max() - 1.0
        out[f"{family}_ma50_slope20"] = ma[50].pct_change(20)
        out[f"{family}_ma200_slope20"] = ma[200].pct_change(20)

    vix = pd.read_csv(DATA_DIR / "vix_daily.csv", parse_dates=["Date"]).set_index("Date")["vix"]
    out["vix"] = vix.reindex(index).ffill()
    out["vix_pct"] = rolling_percentile(out["vix"])
    out["vix_slope20"] = out["vix"].pct_change(20)

    for window in (20, 60, 120):
        out[f"QQQ_minus_SPY_mom{window}"] = out[f"QQQ_mom{window}"] - out[f"SPY_mom{window}"]
        out[f"SOXX_minus_SPY_mom{window}"] = out[f"SOXX_mom{window}"] - out[f"SPY_mom{window}"]
        out[f"SOXX_minus_QQQ_mom{window}"] = out[f"SOXX_mom{window}"] - out[f"QQQ_mom{window}"]
    return out.replace([np.inf, -np.inf], np.nan)


def action_forward_returns(index: pd.DatetimeIndex) -> pd.DataFrame:
    targets = pd.DataFrame(index=index)
    for action, symbol in ACTIONS.items():
        if symbol is None:
            targets[action] = 0.0
        else:
            prices = load(symbol)["adj_close"].reindex(index)
            targets[action] = prices.shift(-TARGET_HORIZON) / prices - 1.0
    return targets


def feature_columns(features: pd.DataFrame) -> list[str]:
    return [c for c in features.columns if features[c].dtype.kind in "fc"]


def make_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=RIDGE_ALPHA)),
    ])


def fit_action_models(features: pd.DataFrame, targets: pd.DataFrame,
                      cutoff: pd.Timestamp) -> dict[str, Pipeline]:
    columns = feature_columns(features)
    eligible = (features.index <= cutoff) & targets.notna().all(axis=1)
    x = features.loc[eligible, columns]
    models = {}
    for action in ACTIONS:
        model = make_model()
        model.fit(x, targets.loc[eligible, action])
        models[action] = model
    return models


def predict_actions(models: dict[str, Pipeline], row: pd.DataFrame,
                    columns: list[str]) -> pd.Series:
    return pd.Series(
        {action: float(model.predict(row[columns])[0])
         for action, model in models.items()}, dtype=float
    )


def select_action(predictions: pd.Series) -> str:
    valid = predictions.replace([np.inf, -np.inf], np.nan).dropna()
    if valid.empty:
        return "cash"
    best = str(valid.idxmax())
    return best if float(valid.loc[best]) > 0.0 else "cash"


def annual_walk_forward(features: pd.DataFrame,
                         targets: pd.DataFrame) -> pd.DataFrame:
    columns = feature_columns(features)
    rows = []
    for year in sorted(set(features.index.year)):
        if year < 2020:
            continue
        cutoff = pd.Timestamp(f"{year - 1}-12-31")
        models = fit_action_models(features, targets, cutoff)
        for date in features.index[features.index.year == year]:
            row = features.loc[[date], columns]
            predictions = predict_actions(models, row, columns)
            action = select_action(predictions)
            rows.append({
                "Date": date,
                "action": action,
                "predicted_return": float(predictions[action]),
                **{f"pred_{a}": float(v) for a, v in predictions.items()},
            })
    return pd.DataFrame(rows).set_index("Date") if rows else pd.DataFrame()


def backtest(predictions: pd.DataFrame) -> pd.DataFrame:
    prices = {a: (load(s)["adj_close"] if s else None)
              for a, s in ACTIONS.items()}
    records = []
    equity = 1.0
    previous_action = "cash"
    for date, row in predictions.iterrows():
        action = str(row["action"])
        series = prices[action]
        if series is None:
            daily_return = 0.0
        else:
            previous = series.shift(1).reindex([date]).iloc[0]
            current = series.reindex([date]).iloc[0]
            daily_return = (float(current / previous - 1.0)
                            if pd.notna(previous) and pd.notna(current) and previous != 0
                            else 0.0)
        equity *= 1.0 + daily_return
        records.append({
            "Date": date,
            "portfolio_return": daily_return,
            "portfolio_value": equity,
            "action": action,
            "changed_action": action != previous_action,
            "predicted_return": row["predicted_return"],
        })
        previous_action = action
    out = pd.DataFrame(records).set_index("Date")
    out["drawdown"] = out["portfolio_value"] / out["portfolio_value"].cummax() - 1.0
    return out


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    total = (1.0 + daily).prod() - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    return {
        "strategy": label,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "total_return": total,
        "annualized_return": (1.0 + total) ** (1.0 / years) - 1.0,
        "annualized_volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252) if daily.std(ddof=1) else np.nan,
        "sortino": daily.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside else np.nan,
        "max_drawdown": frame["drawdown"].min(),
        "worst_day": daily.min(),
        "turnover_events": int(frame["changed_action"].sum()),
        "cash_pct": float((frame["action"] == "cash").mean()),
    }


def main() -> None:
    features = build_features()
    targets = action_forward_returns(features.index)
    predictions = annual_walk_forward(features, targets)
    result = backtest(predictions)

    summaries = []
    for split, (start, end) in SPLITS.items():
        segment = result.loc[start:end]
        if not segment.empty:
            row = summarize(segment, f"AI_Ridge_{split}")
            row["split"] = split
            summaries.append(row)

    annual = result["portfolio_return"].groupby(result.index.year).apply(
        lambda x: (1.0 + x).prod() - 1.0
    )
    spy = load("SPY")["adj_close"].reindex(result.index).pct_change().fillna(0.0)
    spy_annual = spy.groupby(spy.index.year).apply(lambda x: (1.0 + x).prod() - 1.0)
    annual_rows = []
    for year, value in annual.items():
        if year in spy_annual.index:
            annual_rows.append({
                "year": int(year),
                "strategy_return": float(value),
                "spy_return": float(spy_annual.loc[year]),
                "excess_return": float(value - spy_annual.loc[year]),
                "beats_spy": bool(value > spy_annual.loc[year]),
            })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    features.to_csv(DATA_DIR / "e4_ai_features.csv")
    targets.to_csv(DATA_DIR / "e4_ai_action_targets.csv")
    predictions.to_csv(DATA_DIR / "e4_ai_predictions.csv")
    result.to_csv(DATA_DIR / "e4_ai_backtest.csv")
    pd.DataFrame(summaries).to_csv(DATA_DIR / "e4_ai_summary.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(DATA_DIR / "e4_ai_annual_returns.csv", index=False)
    result["action"].value_counts(normalize=True).rename("frequency").to_csv(
        DATA_DIR / "e4_ai_action_frequency.csv"
    )

    print(pd.DataFrame(summaries).to_string(index=False))
    print("\nAction frequency")
    print(result["action"].value_counts(normalize=True).to_string())
    print("\nArtifacts:", DATA_DIR)


if __name__ == "__main__":
    main()
