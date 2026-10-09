"""Same-frozen-input comparison of canonical baseline and F50/F75 overlays.

Market prices are downloaded once by tqqq_canonical_same_input_reconciliation.make_frozen_input,
then all candidates are calculated from that exact reloaded CSV. Fed state is downloaded
once and mapped with the existing one-session conservative lag. No rule is optimized.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tqqq_canonical_same_input_reconciliation import (
    INITIAL, SHOCK, RECOVERY, make_frozen_input, build_events_and_signal,
    independently_rebuild_events, independent_daily_returns,
)
from canonical_shock_recovery_fed_dma_overlay import download_fed, map_fed_state_to_market
from canonical_shock_recovery_active_tightening_overlay import build_active_tightening_overlay
from causal_execution import next_open_daily_returns, next_open_cost_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
DMA = 200
EXPOSURES = (0.0, 0.25, 0.50, 0.75)
COST_BPS = (0.0, 10.0, 25.0, 50.0)


def metrics(returns: np.ndarray, dates: pd.DatetimeIndex, initial: float = INITIAL) -> dict:
    equity = initial * np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(equity)
    years = (dates[-1] - dates[0]).days / 365.25
    log_returns = np.log1p(returns)
    rolling = pd.Series(log_returns).rolling(252, min_periods=252).sum()
    valid = rolling.dropna()
    worst_252 = float(np.expm1(valid.min())) if len(valid) else float("nan")
    return {
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / initial) ** (1.0 / years) - 1.0),
        "max_drawdown": float((equity / peak - 1.0).min()),
        "worst_rolling_252_session_return": worst_252,
        "minimum_equity": float(equity.min()),
        "mean_target_exposure": float("nan"),
    }


def episode_contributions(dates, x, baseline, overlay_binary, exposure):
    """Conditional leave-one-overlay-episode-out effects; not additive."""
    active = overlay_binary == 0.0
    starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
    ends = np.flatnonzero(active & ~np.r_[active[1:], False])
    overlay_weights = np.where(active, exposure, 1.0)
    full_signal = np.minimum(baseline, overlay_weights)
    adj_open = x["tqqq_adj_open"].to_numpy(dtype=float)
    adj_close = x["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(x), dtype=float)
    intraday = np.zeros(len(x), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday[:] = adj_close / adj_open - 1.0
    full_returns = next_open_daily_returns(full_signal, overnight, intraday)
    full_final = float(INITIAL * np.cumprod(1.0 + full_returns)[-1])
    rows = []
    for number, (start_i, end_i) in enumerate(zip(starts, ends), start=1):
        counterfactual_overlay = overlay_weights.copy()
        counterfactual_overlay[start_i:end_i + 1] = 1.0
        counterfactual_signal = np.minimum(baseline, counterfactual_overlay)
        counterfactual_returns = next_open_daily_returns(counterfactual_signal, overnight, intraday)
        counterfactual_final = float(INITIAL * np.cumprod(1.0 + counterfactual_returns)[-1])
        rows.append({
            "exposure_in_overlay": exposure,
            "episode": number,
            "start_date": dates[start_i].date().isoformat(),
            "end_date": dates[end_i].date().isoformat(),
            "overlay_sessions": int(end_i - start_i + 1),
            "incremental_defense_sessions": int(np.sum(baseline[start_i:end_i + 1] == 1.0)),
            "overlap_with_baseline_defense_sessions": int(np.sum(baseline[start_i:end_i + 1] == 0.0)),
            "candidate_final": full_final,
            "counterfactual_final_without_episode": counterfactual_final,
            "conditional_terminal_contribution": full_final - counterfactual_final,
        })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    x, frozen_path = make_frozen_input()
    dates = pd.DatetimeIndex(x.index)
    if len(x) == 0 or dates.has_duplicates or not dates.is_monotonic_increasing:
        raise AssertionError("Frozen market input must be non-empty, unique, sorted")
    required = {"qqq_adj_close", "tqqq_adj_close", "tqqq_adj_open", "tqqq_close"}
    if not required.issubset(x.columns):
        raise AssertionError(f"Missing frozen columns: {sorted(required - set(x.columns))}")

    # The baseline event builder is checked against its separate implementation.
    events, baseline = build_events_and_signal(x["qqq_adj_close"])
    independent_events, independent_baseline = independently_rebuild_events(x["qqq_adj_close"])
    if events != independent_events or not np.array_equal(baseline, independent_baseline):
        raise AssertionError("Canonical event ledger/signal implementations disagree")

    fed = download_fed()
    lagged_fed = map_fed_state_to_market(fed, dates).reindex(dates)
    if len(lagged_fed) != len(dates) or lagged_fed.isna().any():
        raise AssertionError("Lagged Fed state must cover every market session")
    overlay_binary, transitions = build_active_tightening_overlay(
        x["qqq_adj_close"], lagged_fed
    )
    if len(overlay_binary) != len(x):
        raise AssertionError("Overlay signal length differs from frozen market input")
    signals = {"B0_baseline": baseline, "TQQQ_buy_hold": np.ones(len(x), dtype=float)}
    for exposure in EXPOSURES:
        overlay_weight = np.where(overlay_binary == 0.0, exposure, 1.0)
        signals[f"F{int(exposure * 100):02d}"] = np.minimum(baseline, overlay_weight)
    if not np.all(signals["F50"] <= baseline) or not np.all(signals["F75"] <= baseline):
        raise AssertionError("Candidate exposure must never exceed baseline target exposure")

    adj_open = x["tqqq_adj_open"].to_numpy(dtype=float)
    adj_close = x["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(x), dtype=float)
    intraday = np.zeros(len(x), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday[:] = adj_close / adj_open - 1.0
    overnight[0] = intraday[0] = 0.0

    daily_returns = {
        name: next_open_daily_returns(signal, overnight, intraday)
        for name, signal in signals.items()
    }
    independent_base = independent_daily_returns(baseline, overnight, intraday)
    if not np.allclose(daily_returns["B0_baseline"], independent_base, rtol=1e-12, atol=1e-12):
        raise AssertionError("Baseline shared engine disagrees with independent execution loop")
    equity = {name: INITIAL * np.cumprod(1.0 + ret) for name, ret in daily_returns.items()}

    summary_rows = []
    for name, signal in signals.items():
        row = {"strategy": name, **metrics(daily_returns[name], dates)}
        row["mean_target_exposure"] = float(np.mean(signal))
        row["defensive_sessions"] = int(np.sum(signal < 1.0))
        row["exposure_change_count"] = int(np.sum(np.abs(np.diff(signal, prepend=0.0)) > 1e-12))
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "canonical_frozen_overlay_comparison_summary.csv", index=False)

    # Independent-reset subperiod scorecard; continuous equity remains in daily output.
    periods = [
        ("2010-2014", "2010-01-01", "2014-12-31"),
        ("2015-2019", "2015-01-01", "2019-12-31"),
        ("2020-2021", "2020-01-01", "2021-12-31"),
        ("2022-2024", "2022-01-01", "2024-12-31"),
        ("2025-current", "2025-01-01", dates[-1].date().isoformat()),
    ]
    period_rows = []
    for label, start, end in periods:
        mask = (dates >= start) & (dates <= end)
        if not mask.any():
            continue
        d = dates[mask]
        for name, ret in daily_returns.items():
            local = ret[mask]
            local_eq = np.cumprod(1.0 + local)
            period_rows.append({
                "period": label, "strategy": name,
                "start_date": d[0].date().isoformat(), "end_date": d[-1].date().isoformat(),
                "period_reset_return": float(local_eq[-1] - 1.0),
                "period_reset_max_drawdown": float((local_eq / np.maximum.accumulate(local_eq) - 1.0).min()),
                "continuous_start_equity_previous_close": float(equity[name][np.flatnonzero(mask)[0]-1]) if np.flatnonzero(mask)[0] else INITIAL,
                "continuous_end_equity": float(equity[name][np.flatnonzero(mask)[-1]]),
            })
    pd.DataFrame(period_rows).to_csv(OUT / "canonical_frozen_overlay_comparison_periods.csv", index=False)

    cost_rows = []
    for bps in COST_BPS:
        for name, signal in signals.items():
            curve = next_open_cost_equity(signal, overnight, intraday, bps, initial=INITIAL)
            cost_returns = np.zeros(len(curve), dtype=float)
            cost_returns[0] = curve[0] / INITIAL - 1.0
            cost_returns[1:] = curve[1:] / curve[:-1] - 1.0
            cost_metrics = metrics(cost_returns, dates)
            cost_rows.append({
                "cost_bps_per_full_exposure_change": bps, "strategy": name,
                "final_balance": float(curve[-1]),
                "max_drawdown": float((curve / np.maximum.accumulate(curve) - 1.0).min()),
                "worst_rolling_252_session_return": cost_metrics["worst_rolling_252_session_return"],
            })
    pd.DataFrame(cost_rows).to_csv(OUT / "canonical_frozen_overlay_comparison_costs.csv", index=False)

    contribution_rows = []
    for exposure in EXPOSURES:
        contribution_rows.extend(
            episode_contributions(dates, x, baseline, overlay_binary, exposure).to_dict(orient="records")
        )
    pd.DataFrame(contribution_rows).to_csv(
        OUT / "canonical_frozen_overlay_comparison_episode_contributions.csv", index=False
    )

    daily = pd.DataFrame({
        "date": dates,
        "qqq_adj_close": x["qqq_adj_close"].to_numpy(),
        "fed_state_lagged_one_session": lagged_fed.to_numpy(),
        "qqq_sma_200": x["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean().to_numpy(),
        "baseline_signal_close": baseline,
        "active_tightening_overlay_state_close": overlay_binary,
    })
    for name, signal in signals.items():
        daily[f"{name}_target_exposure_close"] = signal
        daily[f"{name}_daily_return"] = daily_returns[name]
        daily[f"{name}_equity"] = equity[name]
    daily.to_csv(OUT / "canonical_frozen_overlay_comparison_daily.csv", index=False, float_format="%.15g")

    event_rows = [{
        "shock_date": dates[s].date().isoformat(),
        "post_shock_low_date": dates[low].date().isoformat(),
        "recovery_decision_close": dates[decision].date().isoformat(),
        "shock_qqq_return": float(x["qqq_adj_close"].pct_change().fillna(0.0).iloc[s]),
    } for s, low, decision in events]
    pd.DataFrame(event_rows).to_csv(OUT / "canonical_frozen_overlay_comparison_events.csv", index=False)
    transitions.to_csv(OUT / "canonical_frozen_overlay_comparison_fed_dma_transitions.csv", index=False)
    pd.DataFrame({"date": dates, "fed_state_lagged_one_session": lagged_fed.to_numpy()}).to_csv(
        OUT / "canonical_frozen_overlay_comparison_fed_state.csv", index=False
    )

    input_sha = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    fed_bytes = (OUT / "canonical_frozen_overlay_comparison_fed_state.csv").read_bytes()
    fed_sha = hashlib.sha256(fed_bytes).hexdigest()
    manifest = {
        "status": "PASS",
        "commit_note": "Same frozen QQQ/TQQQ market input for B0, F00, F25, F50, F75, and buy-and-hold.",
        "market_input_file": frozen_path.name,
        "market_input_sha256": input_sha,
        "lagged_fed_state_file": "canonical_frozen_overlay_comparison_fed_state.csv",
        "lagged_fed_state_sha256": fed_sha,
        "rows": int(len(x)),
        "start": dates[0].date().isoformat(),
        "end": dates[-1].date().isoformat(),
        "initial_balance": INITIAL,
        "shock_threshold": SHOCK,
        "recovery_threshold": RECOVERY,
        "dma": DMA,
        "overlay_rule": "QQQ below SMA200 and previous-session Fed lifecycle state TIGHTENING_ACTIVE; sticky until close >= SMA200; baseline shock defense overrides",
        "exposures_in_overlay": list(EXPOSURES),
        "cost_bps": list(COST_BPS),
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight; executed position earns intraday; costs at exposure changes",
        "event_count": len(events),
        "baseline_independent_execution_match": True,
        "candidate_selection": "none; full sample previously inspected; this is retrospective development evidence",
        "files": [
            "canonical_frozen_overlay_comparison_summary.csv",
            "canonical_frozen_overlay_comparison_periods.csv",
            "canonical_frozen_overlay_comparison_costs.csv",
            "canonical_frozen_overlay_comparison_episode_contributions.csv",
            "canonical_frozen_overlay_comparison_daily.csv",
            "canonical_frozen_overlay_comparison_events.csv",
            "canonical_frozen_overlay_comparison_fed_dma_transitions.csv",
            "canonical_frozen_overlay_comparison_fed_state.csv",
        ],
    }
    (OUT / "canonical_frozen_overlay_comparison_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if input_sha != hashlib.sha256(frozen_path.read_bytes()).hexdigest():
        raise AssertionError("Frozen market input hash changed during comparison")
    print(json.dumps({
        "status": "PASS", "rows": len(x), "start": str(dates[0].date()),
        "end": str(dates[-1].date()), "market_input_sha256": input_sha,
        "fed_state_sha256": fed_sha, "summary": summary.to_dict(orient="records"),
    }, indent=2))


if __name__ == "__main__":
    main()
