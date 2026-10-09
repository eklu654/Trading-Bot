"""Preregistered B0 + 250-DMA partial-exposure hybrid validation.

Runs the same candidates on a corrected synthetic pre-TQQQ proxy and actual
TQQQ, using common windows, the shared causal execution engine, and 0/10/25/50
bp exposure-change cost stress. See the companion preregistration document.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

try:
    from .causal_execution import next_open_cost_equity
    from .reentry_isolation import target_exposure
    from .synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices
except ImportError:
    from causal_execution import next_open_cost_equity
    from reentry_isolation import target_exposure
    from synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START_QQQ = "1999-03-10"
START_TQQQ = "2010-02-11"
END = "2026-10-03"
DMA = 250
BELOW = (0.25, 0.50, 0.75)
COSTS = (0, 10, 25, 50)
EVAL_START_INDEX = DMA - 1


def download(ticker, start):
    frame = yf.download(
        ticker, start=start, end=END, auto_adjust=False,
        progress=False, actions=False,
    )
    if frame.empty:
        raise RuntimeError(f"No {ticker} history returned.")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    frame = frame.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Adj Close": "adj_close",
    }).sort_index()
    required = {"open", "close", "adj_close"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"{ticker} is missing fields: {sorted(missing)}")
    return frame.dropna(subset=["open", "close", "adj_close"])


def hybrid_target_exposure(b0, qqq_close, dma_close, below):
    """Keep B0 cash exits; cap invested B0 exposure below the 250-DMA."""
    b0 = np.asarray(b0, dtype=float)
    close = np.asarray(qqq_close, dtype=float)
    ma = np.asarray(dma_close, dtype=float)
    if not (len(b0) == len(close) == len(ma)):
        raise ValueError("B0, QQQ close, and DMA arrays must align.")
    if not 0.0 <= below <= 1.0:
        raise ValueError("below-DMA exposure must be between 0 and 1.")
    return np.where(b0 <= 0.0, 0.0, np.where(close >= ma, b0, below))


def build_candidates(close, b0):
    ma = pd.Series(close).rolling(DMA).mean().to_numpy()
    close = np.asarray(close, dtype=float)
    b0 = np.asarray(b0, dtype=float)
    out = {"B0": b0.copy()}
    for below in BELOW:
        pct = int(round(100 * below))
        out[f"B0_250DMA_{pct}"] = hybrid_target_exposure(b0, close, ma, below)
    out["PURE_250DMA_25"] = np.where(close >= ma, 1.0, 0.25)
    return out, ma


def summarize_equity(dates, weights, equity, sample, candidate, cost_bps):
    dates = pd.DatetimeIndex(dates)
    equity = np.asarray(equity, dtype=float)
    weights = np.asarray(weights, dtype=float)
    dd = equity / np.maximum.accumulate(equity) - 1.0
    years = max((dates[-1] - dates[0]).days / 365.2425, 1.0 / 365.2425)
    rolling = equity[252:] / equity[:-252] - 1.0 if len(equity) > 252 else np.array([])
    min_i = int(np.argmin(equity))
    changes = int(np.count_nonzero(np.abs(np.diff(weights)) > 1e-12))
    row = {
        "sample": sample, "candidate": candidate, "cost_bps": cost_bps,
        "evaluation_start": dates[0].date().isoformat(),
        "evaluation_end": dates[-1].date().isoformat(),
        "observations": len(dates), "starting_balance": INITIAL,
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float(dd.min()),
        "worst_252_session_return": float(rolling.min()) if len(rolling) else np.nan,
        "minimum_equity": float(equity[min_i]),
        "minimum_equity_date": dates[min_i].date().isoformat(),
        "average_target_exposure": float(weights.mean()),
        "exposure_changes": changes,
        "first_crossing_dd_99pct": first_crossing(dates, dd, -0.99) if sample == "synthetic" else "",
        "first_crossing_dd_99_9pct": first_crossing(dates, dd, -0.999) if sample == "synthetic" else "",
        "first_zero_equity_date": first_crossing(dates, equity, 0.0) if sample == "synthetic" else "",
        "return_2020": window_return(dates, equity, "2020-02-01", "2020-12-31"),
        "return_2022": window_return(dates, equity, "2022-01-01", "2022-12-31"),
    }
    return row, dd


def first_crossing(dates, values, threshold):
    ix = np.flatnonzero(np.asarray(values) <= threshold)
    return dates[int(ix[0])].date().isoformat() if len(ix) else ""


def window_return(dates, equity, start, end):
    ix = np.flatnonzero((dates >= start) & (dates <= end))
    if len(ix) < 2:
        return np.nan
    return float(equity[int(ix[-1])] / equity[int(ix[0])] - 1.0)


def run_sample(sample, dates, candidates, overnight, intraday, start_index):
    dates = pd.DatetimeIndex(dates)
    dates = dates[start_index:]
    rows, paths = [], []
    for candidate, full_weights in candidates.items():
        weights = np.asarray(full_weights, dtype=float)[start_index:]
        on = np.asarray(overnight, dtype=float)[start_index:]
        inn = np.asarray(intraday, dtype=float)[start_index:]
        for bps in COSTS:
            equity = next_open_cost_equity(weights, on, inn, bps, INITIAL)
            row, dd = summarize_equity(dates, weights, equity, sample, candidate, bps)
            rows.append(row)
            if bps in (0, 10):
                paths.append(pd.DataFrame({
                    "Date": dates, "sample": sample, "candidate": candidate,
                    "cost_bps": bps, "target_exposure_at_close": weights,
                    "equity": equity, "drawdown": dd,
                }))
    return rows, paths


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = download("QQQ", START_QQQ)
    t = download("TQQQ", START_TQQQ)
    q["adj_open"] = q.open * q.adj_close / q.close
    qqq_signal_frame = q.rename(columns={"adj_close": "Adj Close"})
    b0_full = target_exposure(qqq_signal_frame, "B0").to_numpy(dtype=float)
    syn_on, syn_in = synthetic_3x_legs_from_adjusted_prices(q.adj_open, q.adj_close)
    syn_candidates, ma_full = build_candidates(q.adj_close.to_numpy(), b0_full)

    # Actual TQQQ: QQQ signals are calculated on the full history and aligned
    # to TQQQ dates before applying the common 250-session warm-up.
    x = q.join(t[["open", "close", "adj_close"]].add_prefix("tqqq_"), how="inner")
    actual_b0 = pd.Series(b0_full, index=q.index).reindex(x.index).to_numpy(dtype=float)
    actual_candidates, actual_ma = build_candidates(x.adj_close.to_numpy(), actual_b0)
    t_adj_open = x.tqqq_open * x.tqqq_adj_close / x.tqqq_close
    actual_on = (t_adj_open / x.tqqq_adj_close.shift(1) - 1.0).fillna(0.0).to_numpy()
    actual_in = (x.tqqq_adj_close / t_adj_open - 1.0).fillna(0.0).to_numpy()

    syn_rows, syn_paths = run_sample(
        "synthetic", q.index, syn_candidates, syn_on, syn_in, EVAL_START_INDEX
    )
    actual_rows, actual_paths = run_sample(
        "actual_tqqq", x.index, actual_candidates, actual_on, actual_in, EVAL_START_INDEX
    )
    summary = pd.DataFrame(syn_rows + actual_rows)
    paths = pd.concat(syn_paths + actual_paths, ignore_index=True)
    q[["open", "close", "adj_close", "adj_open"]].assign(
        on3=syn_on, in3=syn_in, b0=b0_full, dma250=ma_full
    ).to_csv(OUT / "b0_250dma_hybrid_frozen_qqq.csv", index_label="Date", float_format="%.12g")
    x[["tqqq_open", "tqqq_close", "tqqq_adj_close"]].assign(
        actual_on=actual_on, actual_in=actual_in, b0=actual_b0, dma250=actual_ma
    ).to_csv(OUT / "b0_250dma_hybrid_frozen_actual_tqqq.csv", index_label="Date", float_format="%.12g")
    summary.to_csv(OUT / "b0_250dma_hybrid_summary.csv", index=False, float_format="%.12g")
    paths.to_csv(OUT / "b0_250dma_hybrid_paths_0_10bps.csv", index=False, float_format="%.12g")
    print("B0 + 250-DMA hybrid preregistration; starting balance $5,000.")
    print("Synthetic common window:", q.index[EVAL_START_INDEX].date(), "to", q.index[-1].date())
    print("Actual TQQQ common window:", x.index[EVAL_START_INDEX].date(), "to", x.index[-1].date())
    print("\n10 bps summary")
    print(summary[summary.cost_bps == 10].sort_values(["sample", "final_balance"], ascending=[True, False]).to_string(index=False))
    print("\n0/10/25/50 bps summary written to artifact.")
    assert summary.groupby(["sample", "cost_bps"]).size().eq(len(syn_candidates)).all()
    print("PASS: same candidate set, common windows, corrected synthetic legs, and shared causal cost engine.")


if __name__ == "__main__":
    main()
