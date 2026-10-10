"""Small, explicit B0 counterfactual for QQQ trailing-high drawdown warnings.

Candidates reduce TQQQ exposure at the next open after QQQ adjusted close crosses
-10% or -15% below its rolling 252-session high. Exposure returns to 100% only
after QQQ drawdown recovers to -5% or -10%, respectively. Baseline B0 shock/recovery
signal remains the upper bound. Diagnostic only; no candidate is promoted.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .tqqq_canonical_same_input_reconciliation import (
        INITIAL, SHOCK, RECOVERY, make_frozen_input, build_events_and_signal,
        independently_rebuild_events,
    )
    from .causal_execution import next_open_daily_returns, next_open_cost_equity
except ImportError:
    from tqqq_canonical_same_input_reconciliation import (
        INITIAL, SHOCK, RECOVERY, make_frozen_input, build_events_and_signal,
        independently_rebuild_events,
    )
    from causal_execution import next_open_daily_returns, next_open_cost_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
CANDIDATES = ((-0.10, -0.05), (-0.15, -0.10))
EXPOSURES = (0.0, 0.50, 0.75)
COST_BPS = (0.0, 10.0, 25.0)


def build_warning_state(dd: np.ndarray, enter: float, reenter: float) -> np.ndarray:
    """Close-time exposure target; warning has hysteresis and executes next open."""
    if not enter < reenter <= 0:
        raise ValueError("Expected enter threshold below re-entry threshold <= 0")
    state = np.ones(len(dd), dtype=float)
    defensive = False
    for i, value in enumerate(dd):
        if not np.isfinite(value):
            state[i] = 1.0
            continue
        if not defensive and value <= enter:
            defensive = True
        elif defensive and value >= reenter:
            defensive = False
        state[i] = 0.0 if defensive else 1.0
    return state


def metrics(returns: np.ndarray, dates: pd.DatetimeIndex) -> dict:
    equity = INITIAL * np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(equity)
    years = (dates[-1] - dates[0]).days / 365.25
    log_returns = np.log1p(returns)
    rolling = pd.Series(log_returns).rolling(252, min_periods=252).sum().dropna()
    return {
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float((equity / peak - 1.0).min()),
        "worst_rolling_252_session_return": float(np.expm1(rolling.min())) if len(rolling) else None,
        "minimum_equity": float(equity.min()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x, frozen_path = make_frozen_input()
    dates = pd.DatetimeIndex(x.index)
    close = x["qqq_adj_close"].astype(float)
    events, baseline = build_events_and_signal(close)
    independent_events, independent_baseline = independently_rebuild_events(close)
    if events != independent_events or not np.array_equal(baseline, independent_baseline):
        raise AssertionError("Canonical baseline event/signal reconciliation failed")

    q_peak = close.rolling(252, min_periods=252).max()
    dd = (close / q_peak - 1.0).to_numpy(dtype=float)
    t_open = x["tqqq_adj_open"].to_numpy(dtype=float)
    t_close = x["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(x), dtype=float)
    intraday = np.zeros(len(x), dtype=float)
    overnight[1:] = t_open[1:] / t_close[:-1] - 1.0
    intraday[:] = t_close / t_open - 1.0
    overnight[0] = intraday[0] = 0.0

    signals = {"B0_baseline": baseline}
    rows = []
    daily = pd.DataFrame({"date": dates, "qqq_adj_close": close.to_numpy(),
                          "qqq_drawdown_from_252d_high": dd,
                          "b0_signal_close": baseline})
    for enter, reenter in CANDIDATES:
        state = build_warning_state(dd, enter, reenter)
        for exposure in EXPOSURES:
            name = f"DD{int(abs(enter)*100)}_EXP{int(exposure*100)}"
            warning_weight = np.where(state == 0.0, exposure, 1.0)
            signal = np.minimum(baseline, warning_weight)
            if not np.all(signal <= baseline + 1e-12):
                raise AssertionError(f"{name} exceeds baseline exposure")
            signals[name] = signal
            daily[f"{name}_warning_state_close"] = state
            daily[f"{name}_target_exposure_close"] = signal
            daily[f"{name}_daily_return"] = next_open_daily_returns(signal, overnight, intraday)
            eq = INITIAL * np.cumprod(1.0 + daily[f"{name}_daily_return"].to_numpy())
            daily[f"{name}_equity"] = eq
            ret = daily[f"{name}_daily_return"].to_numpy()
            row = {
                "strategy": name, "enter_drawdown": enter, "reenter_drawdown": reenter,
                "exposure_while_warning": exposure,
                "warning_sessions": int(np.sum(state == 0.0)),
                "warning_episode_count": int(np.sum((state == 0.0) & ~np.r_[False, state[:-1] == 0.0])),
                "mean_target_exposure": float(np.mean(signal)),
                "exposure_changes": int(np.sum(np.abs(np.diff(signal, prepend=0.0)) > 1e-12)),
                **metrics(ret, dates),
            }
            rows.append(row)

    base_ret = next_open_daily_returns(baseline, overnight, intraday)
    base_eq = INITIAL * np.cumprod(1.0 + base_ret)
    daily["B0_baseline_daily_return"] = base_ret
    daily["B0_baseline_equity"] = base_eq
    base_metrics = metrics(base_ret, dates)
    for row in rows:
        row["terminal_difference_vs_b0"] = row["final_balance"] - base_metrics["final_balance"]
        row["terminal_ratio_vs_b0"] = row["final_balance"] / base_metrics["final_balance"]

    summary = pd.DataFrame(rows).sort_values("final_balance", ascending=False)
    summary.to_csv(OUT / "qqq_drawdown_warning_b0_counterfactual_summary.csv", index=False)
    cost_rows = []
    for bps in COST_BPS:
        for name, signal in signals.items():
            curve = next_open_cost_equity(signal, overnight, intraday, bps, initial=INITIAL)
            curve_ret = np.zeros(len(curve), dtype=float)
            curve_ret[0] = curve[0] / INITIAL - 1.0
            curve_ret[1:] = curve[1:] / curve[:-1] - 1.0
            cost_rows.append({"strategy": name, "cost_bps_per_full_exposure_change": bps,
                              "final_balance": float(curve[-1]),
                              "max_drawdown": float((curve / np.maximum.accumulate(curve) - 1.0).min())})
    pd.DataFrame(cost_rows).to_csv(OUT / "qqq_drawdown_warning_b0_counterfactual_costs.csv", index=False)
    daily.to_csv(OUT / "qqq_drawdown_warning_b0_counterfactual_daily.csv", index=False, float_format="%.15g")

    digest = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    manifest = {
        "status": "DIAGNOSTIC_NOT_PROMOTED",
        "start": dates[0].date().isoformat(), "end": dates[-1].date().isoformat(),
        "rows": len(x), "initial_balance": INITIAL, "shock_threshold": SHOCK,
        "recovery_threshold": RECOVERY, "frozen_input_file": frozen_path.name,
        "frozen_input_sha256": digest,
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight, new position earns intraday; costs at exposure changes",
        "baseline_independent_reconciliation": True,
        "candidates": [{"enter_drawdown": a, "reenter_drawdown": b, "exposures": list(EXPOSURES)} for a,b in CANDIDATES],
        "reentry": "hysteresis: after entering warning at -10%/-15%, restore overlay to full only when QQQ drawdown recovers to -5%/-10%; B0 shock/recovery signal remains an upper bound",
        "cost_bps": list(COST_BPS),
        "selection_note": "Small retrospective diagnostic, not walk-forward validation; no candidate promoted.",
        "files": ["qqq_drawdown_warning_b0_counterfactual_summary.csv",
                  "qqq_drawdown_warning_b0_counterfactual_costs.csv",
                  "qqq_drawdown_warning_b0_counterfactual_daily.csv"],
    }
    (OUT / "qqq_drawdown_warning_b0_counterfactual_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"manifest": manifest, "baseline": base_metrics,
                      "summary": summary.to_dict(orient="records"),
                      "costs": cost_rows}, indent=2))


if __name__ == "__main__":
    main()
