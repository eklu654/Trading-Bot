"""Predeclared partial-exposure sensitivity for the active-tightening overlay.

The market/Fed state rule is fixed: QQQ below its existing 200-DMA while the
one-session-lagged Fed state is TIGHTENING_ACTIVE; remain in that state until
QQQ closes at/above the 200-DMA. Only exposure during that state varies across
the predeclared 0%, 25%, 50%, and 75% family. No DMA/threshold optimization.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from canonical_shock_recovery_active_tightening_overlay import (
    START, END, INITIAL, DMA, SHOCK, RECOVERY,
    download_market, download_fed, map_fed_state_to_market,
    build_shock_recovery_events, build_baseline_signal,
    build_active_tightening_overlay, calculate_returns, metrics,
    rolling_12m_worst, make_period_rows, targeted_windows,
)
from causal_execution import next_open_cost_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
DEFENSE_EXPOSURES = (0.0, 0.25, 0.50, 0.75)


def episode_contributions(
    frame: pd.DataFrame,
    baseline_signal: np.ndarray,
    overlay_binary: np.ndarray,
    exposure: float,
) -> pd.DataFrame:
    mask = overlay_binary == 0.0
    starts = np.flatnonzero(mask & ~np.r_[False, mask[:-1]])
    ends = np.flatnonzero(mask & ~np.r_[mask[1:], False])
    overlay_weights = np.where(mask, exposure, 1.0)
    full_signal = np.minimum(baseline_signal, overlay_weights)
    full_returns = calculate_returns(frame, full_signal)
    full_final = float(INITIAL * np.cumprod(1.0 + full_returns)[-1])
    rows = []
    for number, (start_i, end_i) in enumerate(zip(starts, ends), start=1):
        cf_overlay = overlay_weights.copy()
        cf_overlay[start_i:end_i + 1] = 1.0
        cf_signal = np.minimum(baseline_signal, cf_overlay)
        cf_returns = calculate_returns(frame, cf_signal)
        cf_final = float(INITIAL * np.cumprod(1.0 + cf_returns)[-1])
        rows.append({
            "defense_exposure": exposure,
            "episode": number,
            "start_date": frame.index[start_i].date().isoformat(),
            "end_date": frame.index[end_i].date().isoformat(),
            "overlay_state_sessions": int(end_i - start_i + 1),
            "incremental_defense_sessions": int((baseline_signal[start_i:end_i + 1] == 1.0).sum()),
            "baseline_defense_overlap_sessions": int((baseline_signal[start_i:end_i + 1] == 0.0).sum()),
            "candidate_final": full_final,
            "counterfactual_final_without_episode": cf_final,
            "conditional_terminal_contribution": full_final - cf_final,
        })
    return pd.DataFrame(rows)


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

    fed = download_fed()
    lagged_state = map_fed_state_to_market(fed, common.index)
    events = build_shock_recovery_events(common["qqq_adj_close"])
    baseline_signal = build_baseline_signal(len(common), events)
    overlay_binary, transitions = build_active_tightening_overlay(
        common["qqq_adj_close"], lagged_state
    )

    signal_map = {
        "baseline_shock_recovery": baseline_signal,
        "tqqq_buy_hold": np.ones(len(common), dtype=float),
    }
    for exposure in DEFENSE_EXPOSURES:
        weights = np.where(overlay_binary == 0.0, exposure, 1.0)
        signal_map[f"baseline_plus_active_tightening_{int(exposure * 100)}"] = np.minimum(baseline_signal, weights)

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

    contrib = pd.concat([
        episode_contributions(common, baseline_signal, overlay_binary, exposure)
        for exposure in DEFENSE_EXPOSURES
    ], ignore_index=True)

    event_rows = []
    qret = common["qqq_adj_close"].pct_change().fillna(0.0)
    dma = common["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean()
    for shock_i, low_i, decision_i in events:
        event_rows.append({
            "shock_date": common.index[shock_i].date().isoformat(),
            "low_date": common.index[low_i].date().isoformat(),
            "recovery_decision_close": common.index[decision_i].date().isoformat(),
            "qqq_return_on_shock": float(qret.iloc[shock_i]),
            "lagged_fed_state_at_shock": str(lagged_state.iloc[shock_i]),
            "qqq_below_200dma_at_shock": bool(common["qqq_adj_close"].iloc[shock_i] < dma.iloc[shock_i]) if np.isfinite(dma.iloc[shock_i]) else False,
        })
    event_df = pd.DataFrame(event_rows)

    daily = pd.DataFrame({
        "date": common.index,
        "qqq_adj_close": common["qqq_adj_close"].to_numpy(),
        "fed_state_lagged_one_session": lagged_state.to_numpy(),
        "qqq_dma_200": dma.to_numpy(),
        "baseline_signal_close": baseline_signal,
        "overlay_binary_state_close": overlay_binary,
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
    for name in [n for n in signal_map if n.startswith("baseline_plus_active_tightening_")] + ["baseline_shock_recovery"]:
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

    common.to_csv(OUT / "canonical_active_tightening_exposure_frozen_inputs.csv", index_label="date", float_format="%.12g")
    daily.to_csv(OUT / "canonical_active_tightening_exposure_daily.csv", index=False, float_format="%.12g")
    summary.to_csv(OUT / "canonical_active_tightening_exposure_summary.csv", index=False)
    periods.to_csv(OUT / "canonical_active_tightening_exposure_periods.csv", index=False)
    windows.to_csv(OUT / "canonical_active_tightening_exposure_stress_windows.csv", index=False)
    contrib.to_csv(OUT / "canonical_active_tightening_exposure_episode_contributions.csv", index=False)
    event_df.to_csv(OUT / "canonical_active_tightening_exposure_baseline_events.csv", index=False)
    transitions.to_csv(OUT / "canonical_active_tightening_exposure_transitions.csv", index=False)
    costs.to_csv(OUT / "canonical_active_tightening_exposure_costs.csv", index=False)

    market_path = OUT / "canonical_active_tightening_exposure_frozen_inputs.csv"
    manifest = {
        "status": "COMPLETED_PREDECLARED_EXPOSURE_SENSITIVITY",
        "baseline_rule_id": "qqq_shock45_recovery10_actual_tqqq_v1",
        "candidate_rule_family": "baseline_plus_lagged_fed_active_and_qqq_below_200dma_sticky_until_reclaim",
        "defense_exposures": list(DEFENSE_EXPOSURES),
        "start": common.index[0].date().isoformat(),
        "end": common.index[-1].date().isoformat(),
        "rows": len(common),
        "initial_balance": INITIAL,
        "market_input_sha256": hashlib.sha256(market_path.read_bytes()).hexdigest(),
        "dma": DMA,
        "fed_state_lag_sessions": 1,
        "entry": "QQQ adjusted close below 200-session SMA AND previous-session Fed state TIGHTENING_ACTIVE",
        "exit": "QQQ adjusted close at/above 200-session SMA",
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight, new position earns intraday",
        "baseline_event_count": len(events),
        "overlay_episode_count": int((~np.asarray(overlay_binary, dtype=bool)).sum() > 0 and (overlay_binary == 0).sum()),
        "summary": summary.to_dict(orient="records"),
        "warning": "Exposure sensitivity only; no threshold/DMA optimization. All candidates use identical market inputs and execution.",
    }
    (OUT / "canonical_active_tightening_exposure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("\nSUMMARY")
    print(summary.to_string(index=False))
    print("\nPERIODS")
    print(periods.to_string(index=False))
    print("\nTARGETED STRESS WINDOWS")
    print(windows.to_string(index=False))
    print("\nEPISODE CONTRIBUTIONS (leave-one-out; conditional, non-additive)")
    print(contrib.to_string(index=False))
    print("\nCOST SENSITIVITY")
    print(costs.to_string(index=False))
    print("\nMANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
