"""Frozen chronological robustness test for B0, F50, and F75.

No parameter search. Signals and the Fed-state machine are generated once over the
full available history; evaluation windows are descriptive, not independent OOS.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from canonical_shock_recovery_active_tightening_overlay import (
    INITIAL, DMA, SHOCK, RECOVERY, download_market, download_fed,
    map_fed_state_to_market, build_shock_recovery_events, build_baseline_signal,
    build_active_tightening_overlay, rolling_12m_worst,
)
from causal_execution import next_open_cost_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
COSTS = (0, 10, 25, 50)
CANDIDATES = {"B0": None, "F50": 0.50, "F75": 0.75}
WINDOWS = [
    ("2010_2014", "2010-02-11", "2014-12-31"),
    ("2015_2019", "2015-01-01", "2019-12-31"),
    ("2020_2021", "2020-01-01", "2021-12-31"),
    ("2022_2024", "2022-01-01", "2024-12-31"),
    ("2025_recent", "2025-01-01", "2099-12-31"),
    ("2018_recovery_risk", "2018-12-04", "2019-03-29"),
    ("covid_crash_rebound", "2020-02-19", "2020-08-31"),
    ("2022_tightening", "2022-01-03", "2023-12-29"),
]


def summarize_window(name, window, dates, equity, full_returns, signal, bps):
    label, start, end = window
    mask = (dates >= start) & (dates <= end)
    idx = np.flatnonzero(mask)
    if not len(idx):
        return None
    first, last = int(idx[0]), int(idx[-1])
    inherited = float(equity[first - 1]) if first > 0 else INITIAL
    local_eq = equity[idx] / inherited
    trough_idx = int(np.argmin(local_eq / np.maximum.accumulate(local_eq)))
    dd_curve = local_eq / np.maximum.accumulate(local_eq) - 1.0
    peak_idx = int(np.argmax(local_eq[:trough_idx + 1]))
    local_ret = full_returns[idx]
    return {
        "window": label, "strategy": name, "cost_bps": bps,
        "start_date": dates[first].date().isoformat(),
        "end_date": dates[last].date().isoformat(),
        "inherited_start_equity": inherited, "ending_equity": float(equity[last]),
        "compounded_return": float(equity[last] / inherited - 1.0),
        "local_max_drawdown": float(dd_curve.min()),
        "local_dd_peak_date": dates[first + peak_idx].date().isoformat(),
        "local_dd_trough_date": dates[first + trough_idx].date().isoformat(),
        "worst_rolling_252_session_return": rolling_12m_worst(local_ret),
        "sessions_0pct": int(np.sum(signal[idx] <= 0.0)),
        "sessions_partial": int(np.sum((signal[idx] > 0.0) & (signal[idx] < 1.0))),
        "sessions_100pct": int(np.sum(signal[idx] >= 1.0)),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = download_market("QQQ").rename(columns={
        "Open": "qqq_open", "High": "qqq_high", "Low": "qqq_low",
        "Close": "qqq_close", "Adj Close": "qqq_adj_close", "Volume": "qqq_volume",
    })
    t = download_market("TQQQ").rename(columns={
        "Open": "tqqq_open", "High": "tqqq_high", "Low": "tqqq_low",
        "Close": "tqqq_close", "Adj Close": "tqqq_adj_close", "Volume": "tqqq_volume",
    })
    frame = q.join(t, how="inner").dropna().sort_index()
    if frame.empty or frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise RuntimeError("Frozen common input must be non-empty, unique, and sorted")

    fed = download_fed()
    lagged_fed = map_fed_state_to_market(fed, frame.index)
    events = build_shock_recovery_events(frame["qqq_adj_close"])
    b0 = build_baseline_signal(len(frame), events)
    overlay_state, transitions = build_active_tightening_overlay(frame["qqq_adj_close"], lagged_fed)
    signals = {"B0": b0}
    for name, fraction in (("F50", 0.50), ("F75", 0.75)):
        overlay_weights = np.where(overlay_state == 0.0, fraction, 1.0)
        signals[name] = np.minimum(b0, overlay_weights)
    if not np.all(signals["F50"] <= signals["B0"]) or not np.all(signals["F75"] <= signals["B0"]):
        raise AssertionError("Overlay must never exceed B0 exposure")
    if not set(np.unique(signals["F50"])).issubset({0.0, 0.5, 1.0}):
        raise AssertionError("Unexpected F50 exposure")
    if not set(np.unique(signals["F75"])).issubset({0.0, 0.75, 1.0}):
        raise AssertionError("Unexpected F75 exposure")

    adj_open = frame["tqqq_open"].to_numpy(float) * frame["tqqq_adj_close"].to_numpy(float) / frame["tqqq_close"].to_numpy(float)
    adj_close = frame["tqqq_adj_close"].to_numpy(float)
    overnight = np.zeros(len(frame), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday = adj_close / adj_open - 1.0
    dates = frame.index
    daily_rows, window_rows, summary_rows = [], [], []
    equity_cache = {}
    for bps in COSTS:
        for name, signal in signals.items():
            equity = next_open_cost_equity(signal, overnight, intraday, bps, INITIAL)
            if not np.all(np.isfinite(equity)) or np.any(equity < 0):
                raise AssertionError(f"Invalid equity for {name} at {bps} bps")
            ret = np.zeros(len(equity), dtype=float)
            ret[1:] = equity[1:] / np.maximum(equity[:-1], 1e-300) - 1.0
            equity_cache[(name, bps)] = equity
            peak = np.maximum.accumulate(equity)
            dd = equity / np.maximum(peak, 1e-300) - 1.0
            summary_rows.append({
                "strategy": name, "cost_bps": bps, "start_date": dates[0].date().isoformat(),
                "end_date": dates[-1].date().isoformat(), "sessions": len(dates),
                "starting_equity": INITIAL, "ending_equity": float(equity[-1]),
                "total_return": float(equity[-1] / INITIAL - 1.0),
                "cagr": float((equity[-1] / INITIAL) ** (365.25 / max((dates[-1]-dates[0]).days, 1)) - 1.0),
                "max_drawdown": float(dd.min()),
                "max_dd_peak_date": dates[int(np.argmax(np.where(np.arange(len(dd)) <= int(np.argmin(dd)), equity, -np.inf)))].date().isoformat(),
                "max_dd_trough_date": dates[int(np.argmin(dd))].date().isoformat(),
                "worst_rolling_252_session_return": rolling_12m_worst(ret),
                "average_signal_exposure": float(signal.mean()),
                "sessions_0pct": int(np.sum(signal <= 0.0)),
                "sessions_partial": int(np.sum((signal > 0.0) & (signal < 1.0))),
                "sessions_100pct": int(np.sum(signal >= 1.0)),
            })
            for win in WINDOWS:
                row = summarize_window(name, win, dates, equity, ret, signal, bps)
                if row:
                    window_rows.append(row)
            for i, date in enumerate(dates):
                daily_rows.append({
                    "date": date.date().isoformat(), "strategy": name, "cost_bps": bps,
                    "signal_close": float(signal[i]), "equity": float(equity[i]), "daily_return": float(ret[i]),
                    "qqq_adj_close": float(frame["qqq_adj_close"].iloc[i]),
                    "fed_state_lagged": str(lagged_fed.iloc[i]),
                    "overlay_state_close": float(overlay_state[i]),
                })

    summary = pd.DataFrame(summary_rows)
    windows = pd.DataFrame(window_rows)
    daily = pd.DataFrame(daily_rows)
    comparisons = []
    for bps in COSTS:
        b0row = summary[(summary.strategy == "B0") & (summary.cost_bps == bps)].iloc[0]
        for candidate in ("F50", "F75"):
            crow = summary[(summary.strategy == candidate) & (summary.cost_bps == bps)].iloc[0]
            comparisons.append({
                "candidate": candidate, "cost_bps": bps,
                "ending_equity_difference_vs_B0": float(crow.ending_equity - b0row.ending_equity),
                "terminal_wealth_retention_vs_B0": float(crow.ending_equity / b0row.ending_equity),
                "max_drawdown_improvement_pp": float((crow.max_drawdown - b0row.max_drawdown) * 100),
                "worst_rolling_252_improvement_pp": float((crow.worst_rolling_252_session_return - b0row.worst_rolling_252_session_return) * 100),
            })
    compare = pd.DataFrame(comparisons)

    # Gate evaluation uses the frozen 25-bps comparison and fixed local windows.
    gate_rows = []
    for candidate in ("F50", "F75"):
        c = summary[(summary.strategy == candidate) & (summary.cost_bps == 25)].iloc[0]
        b = summary[(summary.strategy == "B0") & (summary.cost_bps == 25)].iloc[0]
        w25 = windows[(windows.strategy == candidate) & (windows.cost_bps == 25)].set_index("window")
        wb = windows[(windows.strategy == "B0") & (windows.cost_bps == 25)].set_index("window")
        covid_diff = float(w25.loc["covid_crash_rebound", "compounded_return"] - wb.loc["covid_crash_rebound", "compounded_return"])
        recovery_diff = float(w25.loc["2018_recovery_risk", "compounded_return"] - wb.loc["2018_recovery_risk", "compounded_return"])
        gates = {
            "positive_finite_equity": bool(c.ending_equity > 0 and np.isfinite(c.ending_equity)),
            "wealth_retention_ge_90pct": bool(c.ending_equity / b.ending_equity >= 0.90),
            "max_dd_improvement_ge_5pp": bool((c.max_drawdown - b.max_drawdown) >= 0.05),
            "worst_rolling_year_improvement_ge_5pp": bool((c.worst_rolling_252_session_return - b.worst_rolling_252_session_return) >= 0.05),
            "covid_underperformance_not_worse_than_15pp": bool(covid_diff >= -0.15),
            "2018_recovery_underperformance_not_worse_than_15pp": bool(recovery_diff >= -0.15),
        }
        gate_rows.append({"candidate": candidate, **gates, "passes_all_gates": all(gates.values()),
                          "covid_return_difference_vs_B0": covid_diff,
                          "2018_recovery_return_difference_vs_B0": recovery_diff})
    gates = pd.DataFrame(gate_rows)

    input_path = OUT / "fed_dma_chronological_robustness_frozen_inputs.csv"
    frame.to_csv(input_path, index_label="date", float_format="%.12g")
    input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    summary.to_csv(OUT / "fed_dma_chronological_robustness_summary.csv", index=False)
    windows.to_csv(OUT / "fed_dma_chronological_robustness_windows.csv", index=False)
    compare.to_csv(OUT / "fed_dma_chronological_robustness_comparison.csv", index=False)
    gates.to_csv(OUT / "fed_dma_chronological_robustness_gates.csv", index=False)
    daily.to_csv(OUT / "fed_dma_chronological_robustness_daily.csv", index=False)
    transitions.to_csv(OUT / "fed_dma_chronological_robustness_transitions.csv", index=False)
    manifest = {
        "status": "COMPLETED_FROZEN_CHRONOLOGICAL_ROBUSTNESS",
        "protocol": "docs/research/FED_DMA_OVERLAY_CHRONOLOGICAL_ROBUSTNESS_PREREGISTRATION_2026-10-11.md",
        "initial_balance": INITIAL, "start": dates[0].date().isoformat(), "end": dates[-1].date().isoformat(),
        "sessions": len(dates), "input_sha256": input_hash, "cost_bps": list(COSTS),
        "candidates": list(CANDIDATES), "baseline_shock_pct": SHOCK, "baseline_recovery_pct": RECOVERY,
        "dma": DMA, "fed_state_lag_sessions": 1,
        "warnings": ["All windows are retrospective descriptive regime checks, not untouched holdouts.",
                     "No pre-inception synthetic leveraged ETF data are included.",
                     "No candidate is authorized for paper or live trading."],
        "gate_results": gates.to_dict(orient="records"),
    }
    (OUT / "fed_dma_chronological_robustness_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\nSUMMARY\n", summary.to_string(index=False))
    print("\nCOMPARISON\n", compare.to_string(index=False))
    print("\nGATES\n", gates.to_string(index=False))


if __name__ == "__main__":
    main()
