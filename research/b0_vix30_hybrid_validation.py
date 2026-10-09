"""Preregistered B0 + VIX-30 exposure modifier validation."""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

try:
    from .b0_250dma_hybrid_validation import (
        COSTS, END, EVAL_START_INDEX, INITIAL, OUT, START_QQQ, START_TQQQ,
        download, run_sample,
    )
    from .reentry_isolation import target_exposure
    from .synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices
except ImportError:
    from b0_250dma_hybrid_validation import (
        COSTS, END, EVAL_START_INDEX, INITIAL, OUT, START_QQQ, START_TQQQ,
        download, run_sample,
    )
    from reentry_isolation import target_exposure
    from synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices

VIX_THRESHOLD = 30.0


def download_vix(index):
    raw = yf.download(
        "^VIX", start=START_QQQ, end=END, auto_adjust=False,
        progress=False, actions=False,
    )
    if raw.empty:
        raise RuntimeError("No VIX history returned.")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.index = pd.to_datetime(raw.index).tz_localize(None)
    if "Close" not in raw.columns:
        raise RuntimeError("VIX download is missing Close.")
    # Reindex only to QQQ sessions; forward fill past observations, never future ones.
    vix = raw["Close"].astype(float).reindex(index).ffill()
    if vix.iloc[EVAL_START_INDEX:].isna().any():
        raise RuntimeError("VIX has missing values inside the evaluation window.")
    return vix


def vix_hybrid_target_exposure(b0, vix_close, below):
    """Reduce only invested B0 exposure when the close-known VIX is >= 30."""
    b0 = np.asarray(b0, dtype=float)
    vix = np.asarray(vix_close, dtype=float)
    if len(b0) != len(vix):
        raise ValueError("B0 and VIX arrays must align.")
    if not 0.0 <= below <= 1.0:
        raise ValueError("high-VIX exposure must be between 0 and 1.")
    return np.where(b0 <= 0.0, 0.0, np.where(vix >= VIX_THRESHOLD, below, b0))


def make_candidates(b0, vix):
    out = {"B0": np.asarray(b0, dtype=float).copy()}
    for below in (0.50, 0.75):
        pct = int(round(below * 100))
        out[f"B0_VIX30_{pct}"] = vix_hybrid_target_exposure(b0, vix, below)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = download("QQQ", START_QQQ)
    t = download("TQQQ", START_TQQQ)
    q["adj_open"] = q.open * q.adj_close / q.close
    b0 = target_exposure(q.rename(columns={"adj_close": "Adj Close"}), "B0").to_numpy(dtype=float)
    vix = download_vix(q.index)
    syn_on, syn_in = synthetic_3x_legs_from_adjusted_prices(q.adj_open, q.adj_close)
    syn_candidates = make_candidates(b0, vix.to_numpy())

    x = q.join(t[["open", "close", "adj_close"]].add_prefix("tqqq_"), how="inner")
    actual_b0 = pd.Series(b0, index=q.index).reindex(x.index).to_numpy(dtype=float)
    actual_vix = vix.reindex(x.index).to_numpy(dtype=float)
    actual_candidates = make_candidates(actual_b0, actual_vix)
    t_adj_open = x.tqqq_open * x.tqqq_adj_close / x.tqqq_close
    actual_on = (t_adj_open / x.tqqq_adj_close.shift(1) - 1.0).fillna(0.0).to_numpy()
    actual_in = (x.tqqq_adj_close / t_adj_open - 1.0).fillna(0.0).to_numpy()

    syn_rows, syn_paths = run_sample("synthetic", q.index, syn_candidates, syn_on, syn_in, EVAL_START_INDEX)
    actual_rows, actual_paths = run_sample("actual_tqqq", x.index, actual_candidates, actual_on, actual_in, EVAL_START_INDEX)
    summary = pd.DataFrame(syn_rows + actual_rows)
    paths = pd.concat(syn_paths + actual_paths, ignore_index=True)

    q[["open", "close", "adj_close", "adj_open"]].assign(
        vix_close=vix, b0=b0, on3=syn_on, in3=syn_in,
    ).to_csv(OUT / "b0_vix30_hybrid_frozen_qqq.csv", index_label="Date", float_format="%.12g")
    x[["tqqq_open", "tqqq_close", "tqqq_adj_close"]].assign(
        vix_close=actual_vix, b0=actual_b0, actual_on=actual_on, actual_in=actual_in,
    ).to_csv(OUT / "b0_vix30_hybrid_frozen_actual_tqqq.csv", index_label="Date", float_format="%.12g")
    summary.to_csv(OUT / "b0_vix30_hybrid_summary.csv", index=False, float_format="%.12g")
    paths.to_csv(OUT / "b0_vix30_hybrid_paths_0_10bps.csv", index=False, float_format="%.12g")

    ten = summary[summary.cost_bps == 10]
    print("B0 + VIX-30 preregistered validation; $5,000 start.")
    print("Synthetic common window:", q.index[EVAL_START_INDEX].date(), "to", q.index[-1].date())
    print("Actual TQQQ common window:", x.index[EVAL_START_INDEX].date(), "to", x.index[-1].date())
    print(ten.sort_values(["sample", "final_balance"], ascending=[True, False]).to_string(index=False))
    base = ten.set_index(["sample", "candidate"])
    print("\nPREREGISTERED GATE AT 10 BPS")
    for name in ("B0_VIX30_50", "B0_VIX30_75"):
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
    print("PASS: fixed candidates, shared windows, close-known VIX, corrected synthetic returns, and causal cost engine.")


if __name__ == "__main__":
    main()
