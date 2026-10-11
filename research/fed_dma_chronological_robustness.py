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


def terminal_unrecovered_shock_start(qqq_adj_close: pd.Series) -> int | None:
    """Return the start index of a shock that is still armed at the sample end.

    A terminal open episode must remain defensive through the final observation;
    it must not disappear merely because a +10% recovery has not yet occurred.
    """
    prices = qqq_adj_close.astype(float).to_numpy()
    returns = qqq_adj_close.pct_change().fillna(0.0).to_numpy()
    armed = False
    shock_i = None
    low_i = None
    for i in range(1, len(prices)):
        if not armed and returns[i] <= SHOCK:
            armed = True
            shock_i = low_i = i
        if armed:
            if prices[i] < prices[low_i]:
                low_i = i
            if prices[i] / prices[low_i] - 1.0 >= RECOVERY:
                armed = False
                shock_i = low_i = None
    return int(shock_i) if armed and shock_i is not None else None


def build_censored_baseline_signal(n: int, events, terminal_shock_i: int | None) -> np.ndarray:
    """Build B0 and explicitly censor any shock still unrecovered at sample end."""
    signal = build_baseline_signal(n, events)
    if terminal_shock_i is not None:
        if not 0 <= terminal_shock_i < n:
            raise ValueError("terminal shock index is outside the sample")
        signal[terminal_shock_i:] = 0.0
    return signal


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
    canonical_path = OUT / "canonical_b0" / "tqqq_actual_partial_dma_frozen_input.csv"
    if not canonical_path.exists():
        raise FileNotFoundError(
            "Canonical frozen B0 input artifact is required; workflow must download "
            "artifact tqqq-actual-partial-dma-matrix from run 38117700318 first"
        )
    source_hash = hashlib.sha256(canonical_path.read_bytes()).hexdigest()
    expected_source_hash = "6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55"
    if source_hash != expected_source_hash:
        raise RuntimeError(f"Canonical B0 frozen input SHA-256 mismatch: {source_hash}")
    canonical = pd.read_csv(canonical_path, parse_dates=["date"]).set_index("date").sort_index()
    required = {"adj_close", "tqqq_adj_open", "tqqq_adj_close", "on", "in", "b0_signal"}
    missing = required.difference(canonical.columns)
    if missing:
        raise RuntimeError(f"Canonical frozen input missing columns: {sorted(missing)}")
    frame = pd.DataFrame(index=canonical.index)
    frame["qqq_adj_close"] = canonical["adj_close"].astype(float)
    frame["tqqq_adj_open"] = canonical["tqqq_adj_open"].astype(float)
    frame["tqqq_adj_close"] = canonical["tqqq_adj_close"].astype(float)
    frame["overnight_return"] = canonical["on"].astype(float)
    frame["intraday_return"] = canonical["in"].astype(float)
    if frame.empty or frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise RuntimeError("Frozen common input must be non-empty, unique, and sorted")

    fed = download_fed()
    lagged_fed = map_fed_state_to_market(fed, frame.index)
    events = build_shock_recovery_events(frame["qqq_adj_close"])
    terminal_shock_i = terminal_unrecovered_shock_start(frame["qqq_adj_close"])
    reconstructed_b0 = build_censored_baseline_signal(len(frame), events, terminal_shock_i)
    canonical_b0 = canonical["b0_signal"].to_numpy(dtype=float)
    if not np.array_equal(reconstructed_b0, canonical_b0):
        mismatch = int(np.flatnonzero(reconstructed_b0 != canonical_b0)[0])
        raise RuntimeError(
            f"Canonical B0 signal mismatch at index {mismatch} / {frame.index[mismatch].date()}"
        )
    b0 = canonical_b0.copy()
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

    overnight = frame["overnight_return"].to_numpy(float)
    intraday = frame["intraday_return"].to_numpy(float)
    dates = frame.index
    daily_rows, window_rows, summary_rows = [], [], []
    equity_cache = {}
    return_cache = {}
    for bps in COSTS:
        for name, signal in signals.items():
            equity = next_open_cost_equity(signal, overnight, intraday, bps, INITIAL)
            if not np.all(np.isfinite(equity)) or np.any(equity < 0):
                raise AssertionError(f"Invalid equity for {name} at {bps} bps")
            ret = np.zeros(len(equity), dtype=float)
            ret[1:] = equity[1:] / np.maximum(equity[:-1], 1e-300) - 1.0
            equity_cache[(name, bps)] = equity
            return_cache[(name, bps)] = ret
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

    # Descriptive concentration check: remove only the fixed 2022-2024 returns.
    ex_mask = ~((dates >= "2022-01-01") & (dates <= "2024-12-31"))
    exclusion_rows = []
    for bps in COSTS:
        excluded_finals = {name: float(INITIAL * np.prod(1.0 + return_cache[(name, bps)][ex_mask])) for name in ("B0", "F50", "F75")}
        for name in ("B0", "F50", "F75"):
            row = {"strategy": name, "cost_bps": bps, "excluded_window": "2022-01-01_to_2024-12-31", "remaining_sessions": int(ex_mask.sum()), "ending_equity_excluding_window_returns": excluded_finals[name]}
            if name != "B0":
                row["difference_vs_B0_excluding_window"] = excluded_finals[name] - excluded_finals["B0"]
                row["advantage_persists_excluding_window"] = excluded_finals[name] > excluded_finals["B0"]
            exclusion_rows.append(row)
    exclusion = pd.DataFrame(exclusion_rows)

    input_path = OUT / "fed_dma_chronological_robustness_frozen_inputs.csv"
    frame.to_csv(input_path, index_label="date", float_format="%.12g")
    input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    summary.to_csv(OUT / "fed_dma_chronological_robustness_summary.csv", index=False)
    windows.to_csv(OUT / "fed_dma_chronological_robustness_windows.csv", index=False)
    compare.to_csv(OUT / "fed_dma_chronological_robustness_comparison.csv", index=False)
    gates.to_csv(OUT / "fed_dma_chronological_robustness_gates.csv", index=False)
    exclusion.to_csv(OUT / "fed_dma_chronological_robustness_ex_2022_2024.csv", index=False)
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
        "excluding_2022_2024_return_diagnostic": exclusion.to_dict(orient="records"),
    }
    (OUT / "fed_dma_chronological_robustness_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\nSUMMARY\n", summary.to_string(index=False))
    print("\nCOMPARISON\n", compare.to_string(index=False))
    print("\nGATES\n", gates.to_string(index=False))


if __name__ == "__main__":
    main()
