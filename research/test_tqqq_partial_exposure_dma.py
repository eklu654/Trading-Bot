"""Systematic TQQQ partial-exposure DMA research.

Research question:
    Can tiered exposure below a DMA preserve substantially more of TQQQ's
    buy-and-hold upside than binary 100%/0% DMA timing while reducing tail risk?

The experiment is deliberately systematic rather than hand-picked:
- $5,000 starting balance.
- Exact common period: 2010-03-11 through 2026-10-02.
- Adjusted-close / split-distribution-adjusted price frame.
- Prior-close signal; portfolio state changes at the next session open.
- Above DMA: 100% TQQQ.
- Below DMA: three distance zones plus a severe tail zone, with exposure chosen
  from every monotone 75/50/25/0% tier combination.
- DMA windows: 100/125/150/175/200/225/250/300.
- Distance thresholds: every ordered 3-threshold combination from the
  predeclared grid 0.5%, 1%, 2%, 3%, 5%, 7.5%, 10%, 15%, 20%.
- No parameter is selected before seeing the full matrix.

This is an exploratory research matrix. The highest historical wealth row is
not a production selection.
"""

from __future__ import annotations

from itertools import combinations, product
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_dynamic_leverage import load

OUT = ROOT / "data" / "research"
SYMBOL = "TQQQ"
INITIAL = 5000.0
START = pd.Timestamp("2010-03-11")
END = pd.Timestamp("2026-10-02")
EXPECTED_OBSERVATIONS = 4167

DMAS = (100, 125, 150, 175, 200, 225, 250, 300)
DISTANCE_GRID = (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20)
EXPOSURES = (0.0, 0.25, 0.50, 0.75)
THRESHOLD_TUPLES = tuple(combinations(DISTANCE_GRID, 3))
WEIGHT_TUPLES = tuple(
    w for w in product(EXPOSURES, repeat=4)
    if w[0] >= w[1] >= w[2] >= w[3]
)

def price_frame() -> pd.DataFrame:
    frame = load(SYMBOL).copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame = frame.loc[START:END].copy()
    required = {"open", "close", "adj_close"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"Missing TQQQ fields: {sorted(missing)}")
    frame["adj_open"] = frame["open"] * frame["adj_close"] / frame["close"]
    frame = frame.dropna(subset=["adj_open", "adj_close"])
    if len(frame) != EXPECTED_OBSERVATIONS:
        raise RuntimeError(
            f"Expected exactly {EXPECTED_OBSERVATIONS} observations from "
            f"{START.date()} through {END.date()}, found {len(frame)} "
            f"({frame.index.min().date()} through {frame.index.max().date()})."
        )
    if frame.index.min() != START or frame.index.max() != END:
        raise RuntimeError("TQQQ period endpoints do not match the frozen research period.")
    return frame

def evaluate_weights(
    frame: pd.DataFrame,
    target_weights: np.ndarray,
    label: str,
    dma: int | None,
    thresholds: tuple[float, ...] | None,
    weights: tuple[float, ...] | None,
) -> dict[str, object]:
    # target_weights is the desired TQQQ fraction at each close, applied at
    # that day's next open. Portfolio return is split into overnight return on
    # the prior state and intraday return on the new state.
    prev_w = np.roll(target_weights, 1)
    prev_w[0] = 0.0
    overnight = frame["adj_open"].to_numpy() / frame["adj_close"].shift(1).to_numpy() - 1.0
    intraday = frame["adj_close"].to_numpy() / frame["adj_open"].to_numpy() - 1.0
    daily = prev_w * np.nan_to_num(overnight, nan=0.0) + target_weights * np.nan_to_num(intraday, nan=0.0)
    daily[0] = 0.0

    equity = INITIAL * np.cumprod(1.0 + daily)
    running = np.maximum.accumulate(equity)
    drawdown = equity / running - 1.0
    years = (frame.index[-1] - frame.index[0]).days / 365.25
    final = float(equity[-1])
    daily_s = pd.Series(daily, index=frame.index)
    std = float(daily_s.std(ddof=1))
    downside = daily_s.where(daily_s < 0).std(ddof=1)

    return {
        "strategy": label,
        "dma": dma,
        "t1_pct": None if thresholds is None else thresholds[0] * 100,
        "t2_pct": None if thresholds is None else thresholds[1] * 100,
        "t3_pct": None if thresholds is None else thresholds[2] * 100,
        "w1_pct": None if weights is None else weights[0] * 100,
        "w2_pct": None if weights is None else weights[1] * 100,
        "w3_pct": None if weights is None else weights[2] * 100,
        "w4_pct": None if weights is None else weights[3] * 100,
        "start": frame.index[0],
        "end": frame.index[-1],
        "observations": len(frame),
        "starting_balance": INITIAL,
        "final_balance": final,
        "total_return": final / INITIAL - 1.0,
        "cagr": (final / INITIAL) ** (1.0 / years) - 1.0,
        "max_drawdown": float(drawdown.min()),
        "annualized_volatility": std * np.sqrt(252),
        "sharpe": float(daily_s.mean() / std * np.sqrt(252)) if std else np.nan,
        "sortino": float(daily_s.mean() / downside * np.sqrt(252)) if pd.notna(downside) and downside else np.nan,
        "pct_days_full_tqqq": float((target_weights >= 0.999999).mean()),
        "avg_tqqq_exposure": float(target_weights.mean()),
        "position_changes": int(np.count_nonzero(np.diff(target_weights))),
    }

def run_buy_hold(frame: pd.DataFrame) -> np.ndarray:
    return np.ones(len(frame), dtype=float)

def run_dma_binary(frame: pd.DataFrame, dma: int) -> np.ndarray:
    ma = frame["adj_close"].rolling(dma).mean()
    prior_close = frame["adj_close"].shift(1)
    prior_ma = ma.shift(1)
    return (prior_close >= prior_ma).fillna(False).astype(float).to_numpy()

def run_partial(frame: pd.DataFrame, dma: int, thresholds: tuple[float, ...], weights: tuple[float, ...]) -> np.ndarray:
    ma = frame["adj_close"].rolling(dma).mean().shift(1)
    prior = frame["adj_close"].shift(1)
    distance = prior / ma - 1.0

    out = np.zeros(len(frame), dtype=float)
    valid = ma.notna().to_numpy()
    d = distance.to_numpy()

    # Above DMA is always 100%.
    out[valid & (d >= 0.0)] = 1.0

    # Below DMA: four increasingly severe zones.
    lower = -np.array(thresholds)
    masks = (
        valid & (d < 0.0) & (d >= lower[0]),
        valid & (d < lower[0]) & (d >= lower[1]),
        valid & (d < lower[1]) & (d >= lower[2]),
        valid & (d < lower[2]),
    )
    for mask, weight in zip(masks, weights):
        out[mask] = weight
    return out

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = price_frame()

    rows: list[dict[str, object]] = []

    # Direct controls on the exact same 4,167 observations.
    rows.append(evaluate_weights(frame, run_buy_hold(frame), "TQQQ buy-and-hold", None, None, None))
    for dma in DMAS:
        rows.append(
            evaluate_weights(
                frame,
                run_dma_binary(frame, dma),
                f"TQQQ {dma}-DMA binary",
                dma,
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
            )
        )

    # Full systematic partial-exposure matrix.
    for dma in DMAS:
        for thresholds in THRESHOLD_TUPLES:
            for weights in WEIGHT_TUPLES:
                exposure = run_partial(frame, dma, thresholds, weights)
                label = (
                    f"TQQQ {dma}-DMA partial "
                    f"{'/'.join(f'{x*100:g}' for x in thresholds)}pct "
                    f"{'/'.join(f'{x*100:g}' for x in weights)}pct"
                )
                rows.append(evaluate_weights(frame, exposure, label, dma, thresholds, weights))

    result = pd.DataFrame(rows)
    result["wealth_rank"] = result["final_balance"].rank(ascending=False, method="min").astype(int)
    result["drawdown_rank"] = result["max_drawdown"].rank(ascending=False, method="min").astype(int)
    result["wealth_to_drawdown_rank"] = (
        result["final_balance"].rank(ascending=False, method="min")
        + result["max_drawdown"].rank(ascending=False, method="min")
    )

    controls = result[result["strategy"].str.contains("buy-and-hold|binary", regex=True)].copy()
    partial = result[result["strategy"].str.contains("partial")].copy()
    expected_partial = len(DMAS) * len(THRESHOLD_TUPLES) * len(WEIGHT_TUPLES)
    if len(partial) != expected_partial:
        raise RuntimeError(f"Expected {expected_partial} partial rows, found {len(partial)}")

    result.to_csv(OUT / "tqqq_partial_exposure_dma_full_matrix.csv", index=False)
    controls.to_csv(OUT / "tqqq_partial_exposure_dma_controls.csv", index=False)

    # Descriptive leaders only; no promotion decision is encoded here.
    top_wealth = partial.sort_values("final_balance", ascending=False).head(50)
    top_risk = partial.sort_values(
        ["max_drawdown", "final_balance"], ascending=[False, False]
    ).head(50)
    top_balanced = partial.sort_values(
        ["wealth_to_drawdown_rank", "final_balance"], ascending=[True, False]
    ).head(50)
    top_wealth.to_csv(OUT / "tqqq_partial_exposure_top_wealth.csv", index=False)
    top_risk.to_csv(OUT / "tqqq_partial_exposure_top_drawdown.csv", index=False)
    top_balanced.to_csv(OUT / "tqqq_partial_exposure_top_balanced.csv", index=False)

    # Aggregate robustness views by DMA and by exposure profile. These help
    # identify broad regions rather than selecting a single lucky threshold.
    dma_summary = (
        partial.groupby("dma")
        .agg(
            strategies=("final_balance", "size"),
            median_final_balance=("final_balance", "median"),
            p25_final_balance=("final_balance", lambda s: s.quantile(0.25)),
            p75_final_balance=("final_balance", lambda s: s.quantile(0.75)),
            median_max_drawdown=("max_drawdown", "median"),
            best_final_balance=("final_balance", "max"),
            best_max_drawdown=("max_drawdown", "max"),
        )
        .reset_index()
    )
    dma_summary.to_csv(OUT / "tqqq_partial_exposure_dma_summary.csv", index=False)

    print(f"Observations: {len(frame)} ({frame.index[0].date()} -> {frame.index[-1].date()})")
    print(f"Partial strategies tested: {len(partial):,}")
    print("\n=== CONTROLS ===")
    print(controls[["strategy","final_balance","cagr","max_drawdown","avg_tqqq_exposure"]].to_string(index=False))
    print("\n=== TOP 20 PARTIAL BY FINAL BALANCE ===")
    print(top_wealth.head(20)[["dma","t1_pct","t2_pct","t3_pct","w1_pct","w2_pct","w3_pct","w4_pct","final_balance","cagr","max_drawdown","avg_tqqq_exposure"]].to_string(index=False))
    print("\n=== TOP 20 PARTIAL BY BALANCED RANK ===")
    print(top_balanced.head(20)[["dma","t1_pct","t2_pct","t3_pct","w1_pct","w2_pct","w3_pct","final_balance","cagr","max_drawdown","avg_tqqq_exposure"]].to_string(index=False))

if __name__ == "__main__":
    main()
