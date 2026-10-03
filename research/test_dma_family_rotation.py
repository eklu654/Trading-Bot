"""Fast deterministic family-rotation research across leveraged ETF families.

This experiment is deliberately simpler than the prior dynamic/meta-selector work:
- five benchmark/leveraged-family pairs;
- bull ETF or cash only;
- rank eligible families by benchmark close / benchmark DMA;
- equal-weight the top N eligible families;
- rebalance only on a fixed cadence;
- no inverse ETFs.

Signals use the prior session close; returns begin on the next session.
Chronological train/validation/holdout splits are preserved.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_dynamic_leverage import load

DATA_DIR = ROOT / "data" / "research"
START = pd.Timestamp("2010-01-01")
END = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

FAMILIES = {
    "SP500": {"benchmark": "SPY", "bull": "SPXL"},
    "NASDAQ100": {"benchmark": "QQQ", "bull": "TQQQ"},
    "SEMICONDUCTORS": {"benchmark": "SOXX", "bull": "SOXL"},
    "DOW30": {"benchmark": "DIA", "bull": "UDOW"},
    "RUSSELL2000": {"benchmark": "IWM", "bull": "TNA"},
}
DMAS = (100, 150, 200, 250)
TOP_NS = (1, 2, 3, 5)
CADENCES = (1, 5, 21)
COST_BPS = (0, 10, 25, 50)


@lru_cache(maxsize=None)
def family_data(name: str) -> tuple[pd.DatetimeIndex, pd.Series, pd.Series]:
    spec = FAMILIES[name]
    b = load(spec["benchmark"])["close"].rename("benchmark")
    r = load(spec["bull"])["adj_close"].pct_change().fillna(0.0).rename("bull_return")
    frame = pd.concat([b, r], axis=1).dropna()
    frame = frame.loc[START:END]
    return frame.index, frame["benchmark"], frame["bull_return"]


def common_index() -> pd.DatetimeIndex:
    indexes = [family_data(name)[0] for name in FAMILIES]
    idx = indexes[0]
    for other in indexes[1:]:
        idx = idx.intersection(other)
    return idx


@lru_cache(maxsize=None)
def aligned_data(name: str) -> tuple[pd.Series, pd.Series]:
    idx = common_index()
    _, benchmark, bull_return = family_data(name)
    return benchmark.reindex(idx), bull_return.reindex(idx)


@lru_cache(maxsize=None)
def score_frame(dma: int) -> pd.DataFrame:
    idx = common_index()
    scores = {}
    eligible = {}
    for name in FAMILIES:
        benchmark, _ = aligned_data(name)
        ma = benchmark.rolling(dma).mean()
        prior_benchmark = benchmark.shift(1)
        prior_ma = ma.shift(1)
        score = (prior_benchmark / prior_ma) - 1.0
        scores[name] = score
        eligible[name] = (prior_benchmark >= prior_ma) & score.notna()
    return pd.DataFrame(scores, index=idx), pd.DataFrame(eligible, index=idx)


def backtest(dma: int, top_n: int, cadence: int) -> pd.DataFrame:
    idx = common_index()
    scores, eligible = score_frame(dma)
    returns = pd.DataFrame(
        {name: aligned_data(name)[1] for name in FAMILIES}, index=idx
    )

    weights = pd.DataFrame(0.0, index=idx, columns=FAMILIES)
    last_rebalance = -cadence
    current = pd.Series(0.0, index=FAMILIES, dtype=float)

    for i, date in enumerate(idx):
        if i - last_rebalance >= cadence:
            candidates = scores.loc[date].where(eligible.loc[date]).dropna()
            if len(candidates):
                selected = candidates.nlargest(min(top_n, len(candidates))).index
                current[:] = 0.0
                current.loc[selected] = 1.0 / len(selected)
            else:
                current[:] = 0.0
            last_rebalance = i
        weights.loc[date] = current

    gross = (weights * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights.iloc[0].abs().sum()
    frame = pd.DataFrame(
        {"portfolio_return": gross, "turnover": turnover}, index=idx
    )
    for name in FAMILIES:
        frame[f"{name}_weight"] = weights[name]
    frame["portfolio_value"] = (1.0 + frame["portfolio_return"]).cumprod()
    frame["running_max"] = frame["portfolio_value"].cummax()
    frame["drawdown"] = frame["portfolio_value"] / frame["running_max"] - 1.0
    return frame


def summarize(frame: pd.DataFrame, label: str, split: str) -> dict[str, object]:
    if frame.empty:
        return {"strategy": label, "split": split, "observations": 0}
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    equity = (1.0 + daily).cumprod()
    dd = equity / equity.cummax() - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    return {
        "strategy": label,
        "split": split,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "observations": len(frame),
        "total_return": equity.iloc[-1] - 1.0,
        "cagr": equity.iloc[-1] ** (1 / years) - 1.0,
        "volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252)
        if daily.std(ddof=1) else np.nan,
        "max_drawdown": dd.min(),
        "average_daily_turnover": frame["turnover"].mean(),
        "annualized_turnover": frame["turnover"].mean() * 252,
        "total_turnover": frame["turnover"].sum(),
    }


def apply_costs(frame: pd.DataFrame, cost_bps: int) -> pd.DataFrame:
    out = frame.copy()
    out["portfolio_return"] = (
        out["portfolio_return"] - out["turnover"] * cost_bps / 10000.0
    )
    out["portfolio_value"] = (1.0 + out["portfolio_return"]).cumprod()
    return out


def main() -> None:
    rows = []
    cost_rows = []
    for dma in DMAS:
        for top_n in TOP_NS:
            for cadence in CADENCES:
                frame = backtest(dma, top_n, cadence)
                label = f"ROTATE_DMA{dma}_TOP{top_n}_C{cadence}"
                splits = {
                    "full": frame.loc["2010-01-01":END.strftime("%Y-%m-%d")],
                    "train": frame.loc["2010-01-01":"2019-12-31"],
                    "validation": frame.loc["2020-01-01":"2022-12-31"],
                    "holdout": frame.loc["2023-01-01":"2026-09-25"],
                }
                for split, segment in splits.items():
                    if not segment.empty:
                        rows.append(summarize(segment, label, split))
                for cost in COST_BPS:
                    stressed = apply_costs(frame, cost)
                    for split, segment in {
                        "train": stressed.loc["2010-01-01":"2019-12-31"],
                        "validation": stressed.loc["2020-01-01":"2022-12-31"],
                        "holdout": stressed.loc["2023-01-01":"2026-09-25"],
                    }.items():
                        if segment.empty:
                            continue
                        row = summarize(segment, label, split)
                        row["cost_bps"] = cost
                        cost_rows.append(row)

    # Controls: equal-weight always-bull across the same five families and
    # single-family always-bull references.
    idx = common_index()
    bull_returns = pd.DataFrame(
        {name: aligned_data(name)[1] for name in FAMILIES}, index=idx
    )
    control = pd.DataFrame(
        {"portfolio_return": bull_returns.mean(axis=1)}, index=idx
    )
    control["turnover"] = 0.0
    for split, segment in {
        "full": control.loc["2010-01-01":"2026-09-25"],
        "train": control.loc["2010-01-01":"2019-12-31"],
        "validation": control.loc["2020-01-01":"2022-12-31"],
        "holdout": control.loc["2023-01-01":"2026-09-25"],
    }.items():
        rows.append(summarize(segment, "ALL_FAMILIES_ALWAYS_BULL", split))

    for name in FAMILIES:
        single = pd.DataFrame(
            {"portfolio_return": bull_returns[name], "turnover": 0.0}, index=idx
        )
        for split, segment in {
            "train": single.loc["2010-01-01":"2019-12-31"],
            "validation": single.loc["2020-01-01":"2022-12-31"],
            "holdout": single.loc["2023-01-01":"2026-09-25"],
        }.items():
            rows.append(summarize(segment, f"ALWAYS_BULL_{name}", split))

    out = pd.DataFrame(rows)
    costs = pd.DataFrame(cost_rows)
    out.to_csv(DATA_DIR / "dma_family_rotation_matrix.csv", index=False)
    costs.to_csv(DATA_DIR / "dma_family_rotation_cost_stress.csv", index=False)

    # A compact selection view for the user: train/validation/holdout for
    # rotation candidates, sorted by training CAGR only. Holdout is never used
    # to choose the candidate.
    candidates = out[
        out["strategy"].str.startswith("ROTATE_")
        & (out["split"] == "train")
    ].sort_values(["cagr", "sharpe"], ascending=False)
    candidates.head(10).to_csv(
        DATA_DIR / "dma_family_rotation_train_top10.csv", index=False
    )

    print("=== FAMILY ROTATION TRAIN TOP 10 ===")
    print(candidates.head(10).to_string(index=False))
    print("\n=== FAMILY ROTATION SPLITS ===")
    print(out.to_string(index=False))
    print("\n=== FAMILY ROTATION COST STRESS ===")
    print(costs.to_string(index=False))


if __name__ == "__main__":
    main()
