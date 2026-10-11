"""Stress-conditioned SOXL cap: fixed 60-session drawdown hysteresis, no parameter sweep."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data" / "research"
COSTS = (0, 10, 25, 50)
INITIAL = 5000.0
SOXL_FAMILY = "SEMICONDUCTORS"
SOXL_CAP = 0.25
TOP_N = 2
CADENCE = 5
LOOKBACK = 60
STRESS_ENTER = -0.15
STRESS_EXIT = -0.10
SPLITS = {
    "full": ("2010-03-12", "2026-10-02"),
    "train": ("2010-03-12", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-10-02"),
}

from research.family_specific_shock_gate import apply_family_endpoint_patch, aligned_data, base_weights, build_return_frame, metrics
from research.test_dma_family_rotation_risk_overlay import FAMILIES, score_frame
from research.soxl_concentration_cap import soxl_cap_weights


def stress_conditioned_weights(base: pd.DataFrame, scores: pd.DataFrame,
                               eligible: pd.DataFrame, soxx_close: pd.Series,
                               cap: float = SOXL_CAP, top_n: int = TOP_N,
                               cadence: int = CADENCE, lookback: int = LOOKBACK,
                               stress_enter: float = STRESS_ENTER,
                               stress_exit: float = STRESS_EXIT) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Apply SOXL cap only in a close-known SOXX drawdown stress state."""
    if not 0.0 < cap < 1.0 or not stress_enter < stress_exit < 0.0:
        raise ValueError("invalid cap or stress hysteresis thresholds")
    for frame in (scores, eligible):
        if not frame.index.equals(base.index) or not frame.columns.equals(base.columns):
            raise ValueError("scores and eligibility must match base axes")
    if not soxx_close.index.equals(base.index):
        raise ValueError("SOXX closes must match base index")
    prior_close = soxx_close.astype(float).shift(1)
    prior_high = prior_close.rolling(lookback, min_periods=lookback).max()
    drawdown = prior_close / prior_high - 1.0

    weights = pd.DataFrame(0.0, index=base.index, columns=base.columns)
    stress_state = pd.Series(False, index=base.index, name="stress_active")
    drawdown_signal = drawdown.rename("SOXX_drawdown_from_prior_60_session_high")
    current = pd.Series(0.0, index=base.columns, dtype=float)
    active = False
    last_rebalance = -cadence

    for i, date in enumerate(base.index):
        if i - last_rebalance >= cadence:
            dd = drawdown.loc[date]
            if np.isfinite(dd):
                if not active and dd <= stress_enter:
                    active = True
                elif active and dd >= stress_exit:
                    active = False

            candidates = scores.loc[date].where(eligible.loc[date].astype(bool)).dropna()
            selected = list(candidates.nlargest(min(top_n, len(candidates))).index)
            current[:] = 0.0
            if selected:
                current.loc[selected] = 1.0 / len(selected)
            if active and SOXL_FAMILY in selected:
                current.loc[SOXL_FAMILY] = cap
                replacements = candidates.drop(labels=selected, errors="ignore")
                if len(replacements):
                    replacement = replacements.nlargest(1).index[0]
                    current.loc[replacement] = cap
            last_rebalance = i
        weights.loc[date] = current
        stress_state.loc[date] = active
    return weights, stress_state, drawdown_signal


def main():
    apply_family_endpoint_patch()
    base, returns = base_weights()
    scores, eligible = score_frame(250)
    scores = scores.reindex(index=base.index, columns=base.columns)
    eligible = eligible.reindex(index=base.index, columns=base.columns)
    soxx_close = aligned_data(SOXL_FAMILY)[0].reindex(base.index)
    if soxx_close.isna().any():
        raise AssertionError("SOXX benchmark panel contains missing values")

    permanent = soxl_cap_weights(base, scores, eligible)
    conditional, stress_state, stress_dd = stress_conditioned_weights(base, scores, eligible, soxx_close)

    # Control and candidate invariants.
    if not np.array_equal(base.to_numpy(), base_weights()[0].to_numpy()):
        raise AssertionError("frozen base weights changed")
    inactive = ~stress_state
    if not np.array_equal(conditional.loc[inactive].to_numpy(), base.loc[inactive].to_numpy()):
        raise AssertionError("conditional cap changed weights while stress state was inactive")
    if (conditional[SOXL_FAMILY] > SOXL_CAP + 1e-12).where(stress_state, False).any():
        raise AssertionError("SOXL cap exceeded while stress was active")
    for candidate in (permanent, conditional):
        if (candidate.to_numpy() < -1e-12).any() or (candidate.sum(axis=1).to_numpy() > 1.0 + 1e-12).any():
            raise AssertionError("invalid exposure weights")

    rows, curves = [], []
    strategies = (("BASE_ROTATE_DMA250_TOP2_C5", base),
                  ("SOXL_CAP25_ROTATE", permanent),
                  ("SOXL_CAP25_STRESS60_DD15_10", conditional))
    for cost in COSTS:
        for label, weights in strategies:
            frame = build_return_frame(weights, returns, cost)
            for split, (start, end) in SPLITS.items():
                rows.append(metrics(frame.loc[start:end], label, split, cost))
            if cost == 0:
                daily = frame["portfolio_return"]
                equity = INITIAL * (1.0 + daily).cumprod()
                curves.append(pd.DataFrame({
                    "Date": frame.index, "strategy": label,
                    "portfolio_return_0bps": daily.to_numpy(),
                    "equity_0bps": equity.to_numpy(),
                    "exposure": frame["exposure"].to_numpy(),
                    "turnover": frame["turnover"].to_numpy(),
                }))

    summary = pd.DataFrame(rows)
    curve = pd.concat(curves, ignore_index=True)
    summary.to_csv(DATA / "soxl_stress_cap_summary.csv", index=False)
    curve.to_csv(DATA / "soxl_stress_cap_equity.csv", index=False, float_format="%.12g")
    base.to_csv(DATA / "soxl_stress_cap_base_weights.csv", index_label="Date")
    permanent.to_csv(DATA / "soxl_stress_cap_permanent_weights.csv", index_label="Date")
    conditional.to_csv(DATA / "soxl_stress_cap_conditional_weights.csv", index_label="Date")
    stress_state.to_csv(DATA / "soxl_stress_cap_state.csv", index_label="Date")
    stress_dd.to_csv(DATA / "soxl_stress_cap_drawdown_signal.csv", index_label="Date")
    returns.to_csv(DATA / "soxl_stress_cap_bull_returns.csv", index_label="Date")
    manifest = {
        "start": base.index[0].date().isoformat(), "end": base.index[-1].date().isoformat(),
        "sessions": int(len(base)), "initial": INITIAL, "soxl_cap": SOXL_CAP,
        "stress_lookback": LOOKBACK, "stress_enter": STRESS_ENTER, "stress_exit": STRESS_EXIT,
        "dma": 250, "top_n": TOP_N, "cadence": CADENCE, "costs_bps": list(COSTS),
        "stress_updated_at_rebalance_only": True,
        "replacement": "next-highest eligible family, otherwise cash",
        "returns_sha256": hashlib.sha256((DATA / "soxl_stress_cap_bull_returns.csv").read_bytes()).hexdigest(),
        "base_weights_sha256": hashlib.sha256((DATA / "soxl_stress_cap_base_weights.csv").read_bytes()).hexdigest(),
        "conditional_weights_sha256": hashlib.sha256((DATA / "soxl_stress_cap_conditional_weights.csv").read_bytes()).hexdigest(),
    }
    (DATA / "soxl_stress_cap_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("STRESS-CONDITIONED SOXL CAP RESULTS")
    print(summary.to_string(index=False))
    print("PASS: conditional weights equal base while stress is inactive; cap and total-exposure invariants hold.")
    print("MANIFEST:", json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
