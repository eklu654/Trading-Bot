"""Test the existing frozen macro-regime classifier as an independent overlay.

This is an actual-TQQQ comparison against the canonical shock/recovery baseline,
not a synthetic leveraged-QQQ backtest. The existing macro classifier thresholds
and three predeclared exposure policies are retained. To avoid using a month-end
observation at the start of the next month, the classifier's decision date is
pushed one additional month beyond its existing one-month lag. Baseline,
macro overlays, and buy-and-hold share the same market inputs and execution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from causal_execution import next_open_cost_equity
from canonical_shock_recovery_active_tightening_overlay import (
    START, END, INITIAL, DMA, SHOCK, RECOVERY,
    download_market, build_shock_recovery_events, build_baseline_signal,
    calculate_returns, metrics, rolling_12m_worst, make_period_rows,
    targeted_windows,
)
from test_tqqq_macro_regime import download_macro, apply_macro_states

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    q = download_market("QQQ").rename(columns={
        "Open": "qqq_open", "High": "qqq_high", "Low": "qqq_low",
        "Close": "qqq_close", "Adj Close": "qqq_adj_close", "Volume": "qqq_volume",
    })
    t = download_market("TQQQ").rename(columns={
        "Open": "tqqq_open", "High": "tqqq_high", "Low": "tqqq_low",
        "Close": "tqqq_close", "Adj Close": "tqqq_adj_close", "Volume": "tqqq_volume",
    })
    common = q.join(t, how="inner").dropna().sort_index()
    if common.empty or common.index.has_duplicates or not common.index.is_monotonic_increasing:
        raise RuntimeError("Common market input must be non-empty, unique, and sorted")

    macro = download_macro()
    # The existing code labels a full month's last observation with the month
    # start. Its one-month offset therefore makes it usable on the next month
    # start. Push decision dates one additional month to ensure a full month
    # after the observed month has elapsed; this is intentionally conservative.
    macro = macro.copy()
    macro["decision_date"] = pd.to_datetime(macro["available_date"]) + pd.offsets.MonthBegin(1)
    common = apply_macro_states(common, macro)

    events = build_shock_recovery_events(common["qqq_adj_close"])
    baseline_signal = build_baseline_signal(len(common), events)
    macro_weights = {
        "light": common["weight_light"].to_numpy(dtype=float),
        "medium": common["weight_medium"].to_numpy(dtype=float),
        "hard": common["weight_hard"].to_numpy(dtype=float),
    }
    signal_map = {
        "baseline_shock_recovery": baseline_signal,
        "baseline_plus_macro_light": np.minimum(baseline_signal, macro_weights["light"]),
        "baseline_plus_macro_medium": np.minimum(baseline_signal, macro_weights["medium"]),
        "baseline_plus_macro_hard": np.minimum(baseline_signal, macro_weights["hard"]),
        "tqqq_buy_hold": np.ones(len(common), dtype=float),
    }
    return_map = {name: calculate_returns(common, signal) for name, signal in signal_map.items()}
    equity_map = {name: INITIAL * np.cumprod(1.0 + ret) for name, ret in return_map.items()}

    summary_rows = []
    for name, ret in return_map.items():
        row = {"strategy": name, **metrics(ret, common.index)}
        row["worst_rolling_252_session_return"] = rolling_12m_worst(ret)
        row["average_close_signal_exposure"] = float(signal_map[name].mean())
        row["defensive_signal_days"] = int((signal_map[name] < 1.0).sum())
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    periods = make_period_rows(common.index, return_map, equity_map, signal_map)
    windows = targeted_windows(common.index, return_map, equity_map, signal_map)

    qret = common["qqq_adj_close"].pct_change().fillna(0.0)
    dma = common["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean()
    event_rows = []
    for shock_i, low_i, decision_i in events:
        event_rows.append({
            "shock_date": common.index[shock_i].date().isoformat(),
            "low_date": common.index[low_i].date().isoformat(),
            "recovery_decision_close": common.index[decision_i].date().isoformat(),
            "qqq_return_on_shock": float(qret.iloc[shock_i]),
            "macro_state_at_shock": str(common["macro_state"].iloc[shock_i]),
            "macro_state_at_recovery": str(common["macro_state"].iloc[decision_i]),
            "qqq_below_200dma_at_shock": bool(common["qqq_adj_close"].iloc[shock_i] < dma.iloc[shock_i]) if np.isfinite(dma.iloc[shock_i]) else False,
        })
    event_df = pd.DataFrame(event_rows)

    state_transitions = []
    prior_state = None
    prior_weights = None
    for date, state, light, medium, hard in zip(
        common.index, common["macro_state"].astype(str),
        common["weight_light"], common["weight_medium"], common["weight_hard"],
    ):
        weights = (float(light), float(medium), float(hard))
        if state != prior_state or weights != prior_weights:
            state_transitions.append({
                "date": date.date().isoformat(), "macro_state": state,
                "weight_light": weights[0], "weight_medium": weights[1], "weight_hard": weights[2],
            })
            prior_state, prior_weights = state, weights
    transitions = pd.DataFrame(state_transitions)

    daily = pd.DataFrame({
        "date": common.index,
        "qqq_adj_close": common["qqq_adj_close"].to_numpy(),
        "macro_state": common["macro_state"].astype(str).to_numpy(),
        "weight_light": common["weight_light"].to_numpy(),
        "weight_medium": common["weight_medium"].to_numpy(),
        "weight_hard": common["weight_hard"].to_numpy(),
        "baseline_signal_close": baseline_signal,
    })
    for name, signal in signal_map.items():
        daily[f"{name}_signal_close"] = signal
        daily[f"{name}_daily_return"] = return_map[name]
        daily[f"{name}_equity"] = equity_map[name]

    adj_open = common["tqqq_open"].to_numpy(dtype=float) * common["tqqq_adj_close"].to_numpy(dtype=float) / common["tqqq_close"].to_numpy(dtype=float)
    adj_close = common["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(common), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday = adj_close / adj_open - 1.0
    cost_rows = []
    for name in ["baseline_shock_recovery", "baseline_plus_macro_light", "baseline_plus_macro_medium", "baseline_plus_macro_hard"]:
        for bps in (0, 10, 25, 50):
            eq = next_open_cost_equity(signal_map[name], overnight, intraday, bps)
            peak = np.maximum.accumulate(eq)
            years = (common.index[-1] - common.index[0]).days / 365.25
            cost_rows.append({
                "strategy": name, "cost_bps_per_full_exposure_change": bps,
                "final_balance": float(eq[-1]),
                "cagr": float((eq[-1] / INITIAL) ** (1.0 / years) - 1.0),
                "max_drawdown": float((eq / peak - 1.0).min()),
            })
    costs = pd.DataFrame(cost_rows)

    frozen = common[[
        "qqq_open", "qqq_high", "qqq_low", "qqq_close", "qqq_adj_close", "qqq_volume",
        "tqqq_open", "tqqq_high", "tqqq_low", "tqqq_close", "tqqq_adj_close", "tqqq_volume",
        "macro_state", "weight_light", "weight_medium", "weight_hard",
    ]].copy()
    frozen.to_csv(OUT / "canonical_macro_overlay_frozen_inputs.csv", index_label="date", float_format="%.12g")
    daily.to_csv(OUT / "canonical_macro_overlay_daily.csv", index=False, float_format="%.12g")
    summary.to_csv(OUT / "canonical_macro_overlay_summary.csv", index=False)
    periods.to_csv(OUT / "canonical_macro_overlay_periods.csv", index=False)
    windows.to_csv(OUT / "canonical_macro_overlay_stress_windows.csv", index=False)
    event_df.to_csv(OUT / "canonical_macro_overlay_baseline_events.csv", index=False)
    transitions.to_csv(OUT / "canonical_macro_overlay_transitions.csv", index=False)
    costs.to_csv(OUT / "canonical_macro_overlay_costs.csv", index=False)

    manifest = {
        "status": "COMPLETED_ACTUAL_TQQQ_MACRO_OVERLAY_TEST",
        "baseline_rule_id": "qqq_shock45_recovery10_actual_tqqq_v1",
        "candidate_rule_family": "baseline_plus_existing_frozen_macro_state_light_medium_hard",
        "start": common.index[0].date().isoformat(),
        "end": common.index[-1].date().isoformat(),
        "rows": len(common),
        "initial_balance": INITIAL,
        "market_and_mapped_macro_input_sha256": hashlib.sha256((OUT / "canonical_macro_overlay_frozen_inputs.csv").read_bytes()).hexdigest(),
        "macro_source": "Existing frozen macro classifier: UNRATE, INDPRO, BAA10YM, T10Y3MM",
        "availability_rule": "Existing one-month availability date plus one additional month-start lag; intentionally conservative pending exact vintage/release-date reconstruction",
        "exposures": {
            "light": "STRUCTURAL_EXPANSION=100%, MACRO_DETERIORATION=75%, MACRO_CRISIS=25%",
            "medium": "STRUCTURAL_EXPANSION=100%, MACRO_DETERIORATION=50%, MACRO_CRISIS=0%",
            "hard": "STRUCTURAL_EXPANSION=100%, MACRO_DETERIORATION=25%, MACRO_CRISIS=0%",
        },
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight, new position earns intraday",
        "baseline_event_count": len(events),
        "summary": summary.to_dict(orient="records"),
        "warning": "Actual TQQQ price history, not synthetic TQQQ. Existing macro thresholds are frozen. One conservative additional availability lag is used; no strategy is selected or live-approved.",
    }
    (OUT / "canonical_macro_overlay_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("\nSUMMARY")
    print(summary.to_string(index=False))
    print("\nPERIODS")
    print(periods.to_string(index=False))
    print("\nTARGETED STRESS WINDOWS")
    print(windows.to_string(index=False))
    print("\nBASELINE EVENTS")
    print(event_df.to_string(index=False))
    print("\nMACRO TRANSITIONS")
    print(transitions.to_string(index=False))
    print("\nCOST SENSITIVITY")
    print(costs.to_string(index=False))
    print("\nMANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
