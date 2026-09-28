"""Evaluate candidate SWITCH-001 regime definitions without changing production labels.

This is deliberately a research-only comparison. Candidate thresholds are
predefined, not selected by maximizing total historical return. Results are
split chronologically into training (2010-2018), validation (2019-2022),
and holdout (2023-present).

Run from repository root:
    python research/evaluate_regime_candidates.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"

SPLITS = {
    "TRAIN": ("2010-01-01", "2018-12-31"),
    "VALIDATION": ("2019-01-01", "2022-12-31"),
    "HOLDOUT": ("2023-01-01", "2099-12-31"),
}


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    regime = pd.read_csv(
        DATA_DIR / "historical_regime_dataset.csv",
        parse_dates=["Date"],
    ).set_index("Date").sort_index()
    etf = pd.read_csv(
        DATA_DIR / "etf001_dma_backtest.csv",
        parse_dates=["Date"],
    ).set_index("Date").sort_index()
    return regime, etf


def candidate_labels(frame: pd.DataFrame, name: str) -> pd.Series:
    vix_p = frame["vix_percentile252"]
    rv_p = frame["spy_rv20_percentile252"]

    if name == "CURRENT":
        turbulent = (
            (vix_p >= 0.80)
            | (rv_p >= 0.80)
            | (frame["vix_change5"] >= 0.25)
        )
        trending = (
            (frame["spy_adx14"] >= 25)
            & (frame["spy_er20"] >= 0.35)
            & (frame["spy_sma200_distance"].abs() >= 0.02)
            & (frame["spy_sma200_slope_20"].abs() >= 0.005)
        )
        return pd.Series(
            np.select(
                [turbulent, trending],
                ["TURBULENT_HIGH_VOL", "TRENDING_NORMAL"],
                default="SIDEWAYS_CHOPPY",
            ),
            index=frame.index,
        )

    configs = {
        "BALANCED": {"vix_p": 0.90, "rv_p": 0.90, "adx": 20, "er": 0.30, "return20": 0.08, "slope": 0.003},
        "STRICT_VOL": {"vix_p": 0.95, "rv_p": 0.90, "adx": 20, "er": 0.30, "return20": 0.08, "slope": 0.003},
        "VIX_LEVEL": {"vix_p": 0.90, "rv_p": 0.90, "adx": 20, "er": 0.30, "return20": 0.08, "slope": 0.003},
        "STRICT_SIDEWAYS": {"vix_p": 0.90, "rv_p": 0.90, "adx": 18, "er": 0.25, "return20": 0.06, "slope": 0.003},
    }
    cfg = configs[name]

    if name == "VIX_LEVEL":
        turbulent = (
            (frame["vix"] >= 28)
            | ((vix_p >= cfg["vix_p"]) & (rv_p >= 0.75))
            | (rv_p >= cfg["rv_p"])
        )
    else:
        turbulent = (vix_p >= cfg["vix_p"]) | (rv_p >= cfg["rv_p"])

    sideways = (
        (frame["spy_adx14"] < cfg["adx"])
        & (frame["spy_er20"] < cfg["er"])
        & (frame["spy_return20"].abs() < cfg["return20"])
        & (frame["spy_sma200_slope_20"].abs() < cfg["slope"])
    )

    return pd.Series(
        np.select(
            [turbulent, sideways],
            ["TURBULENT_HIGH_VOL", "SIDEWAYS_CHOPPY"],
            default="TRENDING_NORMAL",
        ),
        index=frame.index,
    )


def stats(etf: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    joined = etf.join(labels.rename("regime"), how="inner").dropna(subset=["regime"])
    rows = []
    for regime, group in joined.groupby("regime"):
        daily = group["portfolio_return"]
        local = (1 + daily).cumprod()
        dd = (local / local.cummax() - 1).min()
        rows.append({
            "regime": regime,
            "observations": len(group),
            "fraction": len(group) / len(joined),
            "mean_daily_return": daily.mean(),
            "annualized_volatility": daily.std(ddof=1) * np.sqrt(252),
            "cumulative_return": (1 + daily).prod() - 1,
            "max_drawdown_within_regime": dd,
            "mean_invested_weight": group["invested_weight"].mean(),
            "worst_day": daily.min(),
        })
    return pd.DataFrame(rows).sort_values("regime")


def main() -> None:
    regime, etf = load()
    outputs = []
    frequency = []

    for name in ["CURRENT", "BALANCED", "STRICT_VOL", "VIX_LEVEL", "STRICT_SIDEWAYS"]:
        labels = candidate_labels(regime, name).shift(1)
        for split, (start, end) in SPLITS.items():
            mask = (labels.index >= start) & (labels.index <= end)
            split_labels = labels.loc[mask]
            split_etf = etf.loc[mask]
            s = stats(split_etf, split_labels)
            s.insert(0, "split", split)
            s.insert(0, "candidate", name)
            outputs.append(s)

            freq = split_labels.value_counts(dropna=False).rename_axis("regime").reset_index(name="observations")
            freq["fraction"] = freq["observations"] / len(split_labels)
            freq.insert(0, "split", split)
            freq.insert(0, "candidate", name)
            frequency.append(freq)

    out = pd.concat(outputs, ignore_index=True)
    freq = pd.concat(frequency, ignore_index=True)
    out.to_csv(DATA_DIR / "regime_candidate_etf_results.csv", index=False)
    freq.to_csv(DATA_DIR / "regime_candidate_frequency.csv", index=False)

    print("=== CANDIDATE ETF RESULTS ===")
    print(out.to_string(index=False))
    print("\n=== CANDIDATE FREQUENCY ===")
    print(freq.to_string(index=False))


if __name__ == "__main__":
    main()
