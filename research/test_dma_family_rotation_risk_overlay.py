"""Risk-overlay research for the frozen DMA-250/top-2/5-session family-rotation candidate.

The base strategy is deliberately frozen:
- 250-day benchmark DMA eligibility;
- rank eligible leveraged families by benchmark distance above DMA;
- equal-weight top two;
- rebalance every five sessions;
- bull ETFs or cash only.

This experiment does NOT re-select the base strategy. It tests whether simple,
causal portfolio-level risk controls can reduce the very large drawdown observed
in the frozen candidate without destroying its train/validation economics.

All sizing decisions use information available through the prior close.
No leverage above 1.0x is introduced.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.test_dma_family_rotation import (
    FAMILIES,
    aligned_data,
    common_index,
    score_frame,
)

DATA_DIR = ROOT / "data" / "research"
DMA = 250
TOP_N = 2
CADENCE = 5
VOL_LOOKBACKS = (20, 60)
VOL_TARGETS = (0.30, 0.40, 0.50, 0.60, 0.80)
DD_THRESHOLDS = (0.00, 0.15, 0.20, 0.25, 0.30)
DD_SCALE = 0.50
COST_BPS = (0, 10, 25, 50)
LATEST_DATE = (pd.Timestamp.now().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def base_weights() -> tuple[pd.DataFrame, pd.DataFrame]:
    idx = common_index()
    scores, eligible = score_frame(DMA)
    weights = pd.DataFrame(0.0, index=idx, columns=FAMILIES)
    last_rebalance = -CADENCE
    current = pd.Series(0.0, index=FAMILIES, dtype=float)

    for i, date in enumerate(idx):
        if i - last_rebalance >= CADENCE:
            candidates = scores.loc[date].where(eligible.loc[date]).dropna()
            current[:] = 0.0
            if len(candidates):
                selected = candidates.nlargest(min(TOP_N, len(candidates))).index
                current.loc[selected] = 1.0 / len(selected)
            last_rebalance = i
        weights.loc[date] = current

    returns = pd.DataFrame(
        {name: aligned_data(name)[1] for name in FAMILIES}, index=idx
    )
    return weights, returns


def summarize(frame: pd.DataFrame, label: str, split: str) -> dict[str, object]:
    if frame.empty:
        return {"strategy": label, "split": split, "observations": 0}
    daily = frame["portfolio_return"].fillna(0.0)
    equity = (1.0 + daily).cumprod()
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    dd = equity / equity.cummax() - 1.0
    std = daily.std(ddof=1)
    return {
        "strategy": label,
        "split": split,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "observations": len(frame),
        "total_return": equity.iloc[-1] - 1.0,
        "cagr": equity.iloc[-1] ** (1 / years) - 1.0,
        "volatility": std * np.sqrt(252),
        "sharpe": daily.mean() / std * np.sqrt(252) if std else np.nan,
        "max_drawdown": dd.min(),
        "average_exposure": frame["exposure"].mean(),
        "annualized_turnover": frame["turnover"].mean() * 252,
        "total_turnover": frame["turnover"].sum(),
    }


def build_overlay(
    base_w: pd.DataFrame,
    returns: pd.DataFrame,
    lookback: int,
    vol_target: float,
    dd_threshold: float,
) -> pd.DataFrame:
    idx = base_w.index
    raw = (base_w * returns).sum(axis=1)

    # Prior-close information only: the rolling volatility is shifted one day.
    realized_vol = raw.rolling(lookback).std(ddof=1).shift(1) * np.sqrt(252)
    exposure = pd.Series(1.0, index=idx, dtype=float)
    valid_vol = realized_vol.notna() & (realized_vol > 0)
    exposure.loc[valid_vol] = (vol_target / realized_vol.loc[valid_vol]).clip(upper=1.0)

    # Drawdown guard is based on the overlay's own equity curve and is
    # evaluated sequentially. Only the prior day's close/equity is used.
    if dd_threshold > 0:
        overlay_equity = 1.0
        peak = 1.0
        for date in idx:
            prior_dd = overlay_equity / peak - 1.0
            if prior_dd <= -dd_threshold:
                exposure.loc[date] *= DD_SCALE
            day_return = float((base_w.loc[date] * exposure.loc[date] * returns.loc[date]).sum())
            overlay_equity *= 1.0 + day_return
            peak = max(peak, overlay_equity)

    weights = base_w.mul(exposure, axis=0)
    portfolio_return = (weights * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights.iloc[0].abs().sum()

    out = pd.DataFrame(
        {
            "portfolio_return": portfolio_return,
            "turnover": turnover,
            "exposure": exposure,
        },
        index=idx,
    )
    return out


def apply_costs(frame: pd.DataFrame, cost_bps: int) -> pd.DataFrame:
    out = frame.copy()
    out["portfolio_return"] -= out["turnover"] * cost_bps / 10000.0
    return out


def splits(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "full": frame.loc["2010-01-01":LATEST_DATE],
        "train": frame.loc["2010-01-01":"2019-12-31"],
        "validation": frame.loc["2020-01-01":"2022-12-31"],
        "holdout": frame.loc["2023-01-01":"2026-09-25"],
    }


def main() -> None:
    base_w, returns = base_weights()
    base = pd.DataFrame(
        {
            "portfolio_return": (base_w * returns).sum(axis=1),
            "turnover": base_w.diff().abs().sum(axis=1),
            "exposure": base_w.sum(axis=1),
        },
        index=base_w.index,
    )
    base.loc[base.index[0], "turnover"] = base_w.iloc[0].abs().sum()

    rows: list[dict[str, object]] = []
    costs: list[dict[str, object]] = []

    # Frozen base control.
    for split, segment in splits(base).items():
        rows.append(summarize(segment, "BASE_ROTATE_DMA250_TOP2_C5", split))

    # Risk-overlay matrix. This is a diagnostic matrix, not a deployment selection.
    for lookback in VOL_LOOKBACKS:
        for target in VOL_TARGETS:
            for dd in DD_THRESHOLDS:
                label = f"RISK_V{int(target*100)}_L{lookback}_DD{int(dd*100)}"
                frame = build_overlay(base_w, returns, lookback, target, dd)
                for split, segment in splits(frame).items():
                    rows.append(summarize(segment, label, split))
                for cost in COST_BPS:
                    stressed = apply_costs(frame, cost)
                    for split, segment in splits(stressed).items():
                        row = summarize(segment, label, split)
                        row["cost_bps"] = cost
                        costs.append(row)

    out = pd.DataFrame(rows)
    cost_out = pd.DataFrame(costs)
    out.to_csv(DATA_DIR / "dma_family_rotation_risk_overlay_matrix.csv", index=False)
    cost_out.to_csv(DATA_DIR / "dma_family_rotation_risk_overlay_cost_stress.csv", index=False)

    # A train-only shortlist for inspection. Validation and holdout are not
    # used to select the candidate; this is only a compact diagnostic view.
    shortlist = out[
        (out["split"] == "train")
        & out["strategy"].str.startswith("RISK_")
    ].sort_values(["cagr", "sharpe"], ascending=False)
    shortlist.head(15).to_csv(
        DATA_DIR / "dma_family_rotation_risk_overlay_train_top15.csv", index=False
    )

    print("=== RISK OVERLAY TRAIN TOP 15 ===")
    print(shortlist.head(15).to_string(index=False))
    print("\n=== RISK OVERLAY ALL SPLITS ===")
    print(out.to_string(index=False))
    print("\n=== RISK OVERLAY COST STRESS ===")
    print(cost_out.to_string(index=False))


if __name__ == "__main__":
    main()
