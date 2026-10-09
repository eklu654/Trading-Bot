"""Test one frozen TIGHTENING_ACTIVE x 200-DMA overlay on the canonical baseline.

Candidate enters a sticky defensive state only when QQQ is below its existing
200-session SMA and the one-session-lagged Fed lifecycle state is
TIGHTENING_ACTIVE. It stays defensive until QQQ closes at/above the 200-DMA.
The baseline shock/recovery defense remains independently active.

This is a single candidate test, not a grid search.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from canonical_shock_recovery_fed_dma_overlay import (
    START, END, INITIAL, DMA, download_market, download_fed,
    map_fed_state_to_market, build_shock_recovery_events,
    build_baseline_signal, calculate_returns, metrics, make_period_rows,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"


def build_active_tightening_overlay(
    qqq_adj_close: pd.Series,
    lagged_fed_state: pd.Series,
) -> tuple[np.ndarray, pd.DataFrame]:
    ma = qqq_adj_close.rolling(DMA, min_periods=DMA).mean()
    armed = False
    weights: list[float] = []
    transitions: list[dict[str, object]] = []
    states = lagged_fed_state.reindex(qqq_adj_close.index).fillna("INSUFFICIENT_HISTORY")
    for date, price, avg, fed_state in zip(
        qqq_adj_close.index, qqq_adj_close.to_numpy(), ma.to_numpy(), states.to_numpy()
    ):
        if not np.isfinite(avg):
            weights.append(0.0 if armed else 1.0)
            continue
        if not armed and price < avg and fed_state == "TIGHTENING_ACTIVE":
            armed = True
            transitions.append({
                "date": date.date().isoformat(), "state": "ENTER",
                "reason": "qqq_below_200dma_and_lagged_fed_active",
                "qqq_adj_close": float(price), "dma_200": float(avg),
                "lagged_fed_state": str(fed_state),
            })
        elif armed and price >= avg:
            armed = False
            transitions.append({
                "date": date.date().isoformat(), "state": "EXIT",
                "reason": "qqq_close_recovered_above_200dma",
                "qqq_adj_close": float(price), "dma_200": float(avg),
                "lagged_fed_state": str(fed_state),
            })
        weights.append(0.0 if armed else 1.0)
    return np.asarray(weights, dtype=float), pd.DataFrame(transitions)


def rolling_12m_worst(returns: np.ndarray) -> float:
    log_returns = np.log1p(np.asarray(returns, dtype=float))
    rolling = pd.Series(log_returns).rolling(252, min_periods=252).sum()
    valid = rolling.dropna()
    return float(np.expm1(valid.min())) if not valid.empty else float("nan")


def targeted_windows(
    dates: pd.DatetimeIndex,
    return_map: dict[str, np.ndarray],
    equity_map: dict[str, np.ndarray],
    signal_map: dict[str, np.ndarray],
) -> pd.DataFrame:
    windows = [
        ("2010 slow correction", "2010-05-03", "2010-09-30"),
        ("2016 slow correction", "2015-12-15", "2016-04-30"),
        ("2018 Q4 bear", "2018-10-01", "2019-03-31"),
        ("COVID crash and rebound", "2020-02-19", "2020-07-31"),
        ("2022 tightening bear", "2022-01-03", "2022-12-30"),
        ("2025 correction", "2025-02-19", "2025-06-30"),
    ]
    rows = []
    for label, start, end in windows:
        mask = (dates >= start) & (dates <= end)
        if not mask.any():
            continue
        first = int(np.flatnonzero(mask)[0])
        last = int(np.flatnonzero(mask)[-1])
        for name, ret in return_map.items():
            local_returns = ret[mask]
            local_eq = np.cumprod(1.0 + local_returns)
            local_dd = (local_eq / np.maximum.accumulate(local_eq) - 1.0).min()
            inherited_start = float(equity_map[name][first - 1]) if first > 0 else INITIAL
            rows.append({
                "window": label, "strategy": name,
                "start_date": dates[first].date().isoformat(),
                "end_date": dates[last].date().isoformat(),
                "inherited_start_equity": inherited_start,
                "end_equity": float(equity_map[name][last]),
                "inherited_account_return": float(equity_map[name][last] / inherited_start - 1.0),
                "period_reset_return": float(local_eq[-1] - 1.0),
                "local_max_drawdown": float(local_dd),
                "defensive_signal_days": int((signal_map[name][mask] < 1.0).sum()),
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
    overlay_signal, transitions = build_active_tightening_overlay(
        common["qqq_adj_close"], lagged_state
    )
    candidate_signal = np.minimum(baseline_signal, overlay_signal)
    buy_hold_signal = np.ones(len(common), dtype=float)
    assert np.all(candidate_signal <= baseline_signal)
    assert set(np.unique(candidate_signal)).issubset({0.0, 1.0})

    signal_map = {
        "baseline_shock_recovery": baseline_signal,
        "baseline_plus_active_tightening_200dma": candidate_signal,
        "tqqq_buy_hold": buy_hold_signal,
    }
    return_map = {
        name: calculate_returns(common, signal)
        for name, signal in signal_map.items()
    }
    equity_map = {
        name: INITIAL * np.cumprod(1.0 + ret)
        for name, ret in return_map.items()
    }
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

    event_rows = []
    for shock_i, low_i, decision_i in events:
        event_rows.append({
            "shock_date": common.index[shock_i].date().isoformat(),
            "low_date": common.index[low_i].date().isoformat(),
            "recovery_decision_close": common.index[decision_i].date().isoformat(),
            "lagged_fed_state_at_shock": str(lagged_state.iloc[shock_i]),
            "qqq_below_200dma_at_shock": bool(common["qqq_adj_close"].iloc[shock_i] < common["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean().iloc[shock_i]),
        })
    event_df = pd.DataFrame(event_rows)

    daily = pd.DataFrame({
        "date": common.index,
        "qqq_adj_close": common["qqq_adj_close"].to_numpy(),
        "fed_state_lagged_one_session": lagged_state.to_numpy(),
        "qqq_dma_200": common["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean().to_numpy(),
        "baseline_signal_close": baseline_signal,
        "active_tightening_overlay_signal_close": overlay_signal,
        "candidate_signal_close": candidate_signal,
        "baseline_daily_return": return_map["baseline_shock_recovery"],
        "candidate_daily_return": return_map["baseline_plus_active_tightening_200dma"],
        "buy_hold_daily_return": return_map["tqqq_buy_hold"],
        "baseline_equity": equity_map["baseline_shock_recovery"],
        "candidate_equity": equity_map["baseline_plus_active_tightening_200dma"],
        "buy_hold_equity": equity_map["tqqq_buy_hold"],
    })

    common.to_csv(OUT / "canonical_active_tightening_overlay_frozen_inputs.csv", index_label="date", float_format="%.12g")
    daily.to_csv(OUT / "canonical_active_tightening_overlay_daily.csv", index=False, float_format="%.12g")
    summary.to_csv(OUT / "canonical_active_tightening_overlay_summary.csv", index=False)
    periods.to_csv(OUT / "canonical_active_tightening_overlay_periods.csv", index=False)
    windows.to_csv(OUT / "canonical_active_tightening_overlay_stress_windows.csv", index=False)
    event_df.to_csv(OUT / "canonical_active_tightening_overlay_baseline_events.csv", index=False)
    transitions.to_csv(OUT / "canonical_active_tightening_overlay_transitions.csv", index=False)

    adj_open = common["tqqq_open"].to_numpy(dtype=float) * common["tqqq_adj_close"].to_numpy(dtype=float) / common["tqqq_close"].to_numpy(dtype=float)
    adj_close = common["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(common), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday = adj_close / adj_open - 1.0
    cost_rows = []
    for name, signal in [
        ("baseline_shock_recovery", baseline_signal),
        ("baseline_plus_active_tightening_200dma", candidate_signal),
    ]:
        for bps in (0, 10, 25, 50):
            eq = next_open_cost_equity(signal, overnight, intraday, bps)
            peak = np.maximum.accumulate(eq)
            years = (common.index[-1] - common.index[0]).days / 365.25
            cost_rows.append({
                "strategy": name, "cost_bps_per_full_exposure_change": bps,
                "final_balance": float(eq[-1]),
                "cagr": float((eq[-1] / INITIAL) ** (1.0 / years) - 1.0),
                "max_drawdown": float((eq / peak - 1.0).min()),
            })
    costs = pd.DataFrame(cost_rows)
    costs.to_csv(OUT / "canonical_active_tightening_overlay_costs.csv", index=False)

    market_path = OUT / "canonical_active_tightening_overlay_frozen_inputs.csv"
    input_hash = hashlib.sha256(market_path.read_bytes()).hexdigest()
    manifest = {
        "status": "COMPLETED_SINGLE_CANDIDATE_TEST",
        "baseline_rule_id": "qqq_shock45_recovery10_actual_tqqq_v1",
        "candidate_rule_id": "baseline_plus_lagged_fed_active_and_qqq_below_200dma_sticky_until_reclaim",
        "start": common.index[0].date().isoformat(),
        "end": common.index[-1].date().isoformat(),
        "rows": len(common),
        "initial_balance": INITIAL,
        "market_input_sha256": input_hash,
        "baseline_shock_pct": SHOCK,
        "baseline_recovery_pct": RECOVERY,
        "dma": DMA,
        "fed_state_lag_sessions": 1,
        "entry": "QQQ adjusted close below 200-session SMA AND previous-session Fed state TIGHTENING_ACTIVE",
        "exit": "QQQ adjusted close at/above 200-session SMA",
        "sticky_until_exit": True,
        "baseline_and_candidate_same_input": True,
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight, new position earns intraday",
        "baseline_event_count": len(events),
        "overlay_transition_count": len(transitions),
        "summary": summary.to_dict(orient="records"),
        "warning": "Single predeclared candidate; not optimized. FRED states are conservatively lagged one market session. Not live-approved.",
    }
    (OUT / "canonical_active_tightening_overlay_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("\nSUMMARY")
    print(summary.to_string(index=False))
    print("\nPERIODS")
    print(periods.to_string(index=False))
    print("\nTARGETED STRESS WINDOWS")
    print(windows.to_string(index=False))
    print("\nBASELINE EVENTS")
    print(event_df.to_string(index=False))
    print("\nOVERLAY TRANSITIONS")
    print(transitions.to_string(index=False))
    print("\nCOST SENSITIVITY")
    print(costs.to_string(index=False))
    print("\nMANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
