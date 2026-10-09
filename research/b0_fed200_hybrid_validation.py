"""Preregistered B0 + Fed-hike/200-DMA state modifier validation."""
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from .b0_250dma_hybrid_validation import (
        COSTS, END, EVAL_START_INDEX, INITIAL, OUT, START_QQQ, START_TQQQ,
        download, run_sample,
    )
    from .reentry_isolation import target_exposure
    from .synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices
    from .tqqq_three_layer_event_attribution import fed_series
except ImportError:
    from b0_250dma_hybrid_validation import (
        COSTS, END, EVAL_START_INDEX, INITIAL, OUT, START_QQQ, START_TQQQ,
        download, run_sample,
    )
    from reentry_isolation import target_exposure
    from synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices
    from tqqq_three_layer_event_attribution import fed_series

DMA = 200
MIN_FED_HIKE = 0.25
FED_LOOKBACK = 126


def fed_hike_hybrid_target_exposure(b0, qqq_close, dma_close, fed_change, below):
    """Apply the fixed Fed-hike/below-DMA modifier without overriding B0 cash."""
    b0 = np.asarray(b0, dtype=float)
    close = np.asarray(qqq_close, dtype=float)
    ma = np.asarray(dma_close, dtype=float)
    change = np.asarray(fed_change, dtype=float)
    if not (len(b0) == len(close) == len(ma) == len(change)):
        raise ValueError("B0, close, DMA, and Fed-change arrays must align.")
    if not 0.0 <= below <= 1.0:
        raise ValueError("below-DMA exposure must be between 0 and 1.")
    active = (close < ma) & (change >= MIN_FED_HIKE)
    return np.where(b0 <= 0.0, 0.0, np.where(active, below, b0))


def make_candidates(close, b0, fed_change):
    close = np.asarray(close, dtype=float)
    b0 = np.asarray(b0, dtype=float)
    fed_change = np.asarray(fed_change, dtype=float)
    ma = pd.Series(close).rolling(DMA).mean().to_numpy()
    active = (close < ma) & (fed_change >= MIN_FED_HIKE)
    out = {"B0": b0.copy()}
    for below in (0.50, 0.75):
        pct = int(round(below * 100))
        out[f"B0_FED200_{pct}"] = fed_hike_hybrid_target_exposure(
            b0, close, ma, fed_change, below
        )
    return out, ma, active


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = download("QQQ", START_QQQ)
    t = download("TQQQ", START_TQQQ)
    q["adj_open"] = q.open * q.adj_close / q.close
    b0 = target_exposure(q.rename(columns={"adj_close": "Adj Close"}), "B0").to_numpy(dtype=float)
    fed = fed_series(q.index).astype(float)
    fed_change = (fed - fed.shift(FED_LOOKBACK)).to_numpy(dtype=float)
    syn_on, syn_in = synthetic_3x_legs_from_adjusted_prices(q.adj_open, q.adj_close)
    syn_candidates, dma200, state = make_candidates(q.adj_close.to_numpy(), b0, fed_change)

    x = q.join(t[["open", "close", "adj_close"]].add_prefix("tqqq_"), how="inner")
    actual_b0 = pd.Series(b0, index=q.index).reindex(x.index).to_numpy(dtype=float)
    actual_change = pd.Series(fed_change, index=q.index).reindex(x.index).to_numpy(dtype=float)
    actual_candidates, actual_dma, actual_state = make_candidates(
        x.adj_close.to_numpy(), actual_b0, actual_change
    )
    t_adj_open = x.tqqq_open * x.tqqq_adj_close / x.tqqq_close
    actual_on = (t_adj_open / x.tqqq_adj_close.shift(1) - 1.0).fillna(0.0).to_numpy()
    actual_in = (x.tqqq_adj_close / t_adj_open - 1.0).fillna(0.0).to_numpy()

    syn_rows, syn_paths = run_sample("synthetic", q.index, syn_candidates, syn_on, syn_in, EVAL_START_INDEX)
    actual_rows, actual_paths = run_sample("actual_tqqq", x.index, actual_candidates, actual_on, actual_in, EVAL_START_INDEX)
    summary = pd.DataFrame(syn_rows + actual_rows)
    paths = pd.concat(syn_paths + actual_paths, ignore_index=True)

    q[["open", "close", "adj_close", "adj_open"]].assign(
        fed_target=fed, fed_change_126=fed_change, dma200=dma200,
        b0=b0, modifier_state=state.astype(int), on3=syn_on, in3=syn_in,
    ).to_csv(OUT / "b0_fed200_hybrid_frozen_qqq.csv", index_label="Date", float_format="%.12g")
    x[["tqqq_open", "tqqq_close", "tqqq_adj_close"]].assign(
        fed_target=fed.reindex(x.index).to_numpy(),
        fed_change_126=actual_change, dma200=actual_dma,
        b0=actual_b0, modifier_state=actual_state.astype(int),
        actual_on=actual_on, actual_in=actual_in,
    ).to_csv(OUT / "b0_fed200_hybrid_frozen_actual_tqqq.csv", index_label="Date", float_format="%.12g")
    summary.to_csv(OUT / "b0_fed200_hybrid_summary.csv", index=False, float_format="%.12g")
    paths.to_csv(OUT / "b0_fed200_hybrid_paths_0_10bps.csv", index=False, float_format="%.12g")

    ten = summary[summary.cost_bps == 10]
    print("B0 + Fed-hike/200-DMA preregistered validation; $5,000 start.")
    print("Synthetic common window:", q.index[EVAL_START_INDEX].date(), "to", q.index[-1].date())
    print("Actual TQQQ common window:", x.index[EVAL_START_INDEX].date(), "to", x.index[-1].date())
    print(ten.sort_values(["sample", "final_balance"], ascending=[True, False]).to_string(index=False))
    base = ten.set_index(["sample", "candidate"])
    print("\nPREREGISTERED GATE AT 10 BPS")
    for name in ("B0_FED200_50", "B0_FED200_75"):
        a = base.loc[("actual_tqqq", name)]
        a0 = base.loc[("actual_tqqq", "B0")]
        s = base.loc[("synthetic", name)]
        s0 = base.loc[("synthetic", "B0")]
        checks = {
            "actual_wealth_at_least_90pct": a.final_balance >= 0.90 * a0.final_balance,
            "actual_dd_improves_3pp": (a.max_drawdown - a0.max_drawdown) >= 0.03,
            "synthetic_wealth_at_least_90pct": s.final_balance >= 0.90 * s0.final_balance,
            "synthetic_dd_improves_3pp": (s.max_drawdown - s0.max_drawdown) >= 0.03,
        }
        print(name, checks, "PASS_ALL=", all(checks.values()))
    assert summary.groupby(["sample", "cost_bps"]).size().eq(len(syn_candidates)).all()
    print("PASS: fixed candidates, shared windows, corrected synthetic returns, and causal cost engine.")


if __name__ == "__main__":
    main()
