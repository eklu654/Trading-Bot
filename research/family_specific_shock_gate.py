"""Family-specific shock/recovery overlay on the frozen DMA250/top-2/cadence-5 rotation."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data" / "research"
INITIAL = 5000.0
COSTS = (0, 10, 25, 50)
SHOCK = -0.045
RECOVERY = 0.10
SPLITS = {
    "full": ("2010-03-12", "2026-10-02"),
    "train": ("2010-03-12", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-10-02"),
}

from research.replay_family_rotation_account import apply_family_endpoint_patch
from research.test_dma_family_rotation_risk_overlay import FAMILIES, aligned_data, base_weights, score_frame


def family_gate_weights(base: pd.DataFrame, benchmarks: pd.DataFrame,
                        shock: float = SHOCK, recovery: float = RECOVERY) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply a separate benchmark shock state to each family, known at prior close."""
    if not base.index.equals(benchmarks.index) or not base.columns.equals(benchmarks.columns):
        raise ValueError("base weights and benchmark closes must have identical axes")
    if not (shock < 0 and recovery > 0):
        raise ValueError("shock must be negative and recovery positive")
    gated = base.copy()
    gate_states = pd.DataFrame(False, index=base.index, columns=base.columns)
    for family in base.columns:
        px = benchmarks[family].astype(float).to_numpy()
        daily = pd.Series(px, index=base.index).pct_change().to_numpy()
        defensive = False
        low = np.nan
        for i in range(1, len(base)):
            # Row i's target may only use benchmark data through the prior close.
            j = i - 1
            if j >= 1:
                shock_today = daily[j] <= shock
                if not defensive and shock_today:
                    defensive = True
                    low = px[j]
                elif defensive:
                    if shock_today:
                        low = px[j]
                    else:
                        low = min(low, px[j])
                        if px[j] / low - 1.0 >= recovery:
                            defensive = False
                            low = np.nan
            gate_states.iat[i, gate_states.columns.get_loc(family)] = defensive
            if defensive:
                gated.iat[i, gated.columns.get_loc(family)] = 0.0
    return gated, gate_states


def rotating_gate_weights(base: pd.DataFrame, scores: pd.DataFrame,
                           eligible: pd.DataFrame, gate_states: pd.DataFrame,
                           top_n: int = 2, cadence: int = 5) -> pd.DataFrame:
    """Replace gated slots only at the frozen rebalance cadence; never re-enter off-cycle."""
    axes = (base.index, base.columns)
    for frame in (scores, eligible, gate_states):
        if not frame.index.equals(axes[0]) or not frame.columns.equals(axes[1]):
            raise ValueError("scores, eligibility, and gate states must match base-weight axes")
    if top_n < 1 or cadence < 1:
        raise ValueError("top_n and cadence must be positive")
    weights = pd.DataFrame(0.0, index=base.index, columns=base.columns)
    current = pd.Series(0.0, index=base.columns, dtype=float)
    last_rebalance = -cadence
    for i, date in enumerate(base.index):
        if i - last_rebalance >= cadence:
            allowed = eligible.loc[date].astype(bool) & ~gate_states.loc[date].astype(bool)
            candidates = scores.loc[date].where(allowed).dropna()
            current[:] = 0.0
            if len(candidates):
                selected = candidates.nlargest(min(top_n, len(candidates))).index
                current.loc[selected] = 1.0 / len(selected)
            last_rebalance = i
        # Immediate family-specific exit; the slot remains empty until the
        # next scheduled rebalance, even if its recovery gate clears earlier.
        current.loc[gate_states.loc[date].astype(bool)] = 0.0
        weights.loc[date] = current
    return weights


def metrics(frame: pd.DataFrame, strategy: str, split: str, cost_bps: int) -> dict:
    if frame.empty:
        return {"strategy": strategy, "split": split, "cost_bps": cost_bps, "observations": 0}
    r = frame["portfolio_return"].astype(float)
    equity = INITIAL * (1.0 + r).cumprod()
    peak = equity.cummax()
    dd = equity / peak - 1.0
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1 / 365.25)
    return {
        "strategy": strategy, "split": split, "cost_bps": cost_bps,
        "start": equity.index[0], "end": equity.index[-1], "observations": len(frame),
        "ending_equity": float(equity.iloc[-1]),
        "cagr": float((equity.iloc[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "worst_252_session_return": float(r.rolling(252, min_periods=252).apply(
            lambda x: np.prod(1.0 + x) - 1.0, raw=True).min()),
        "minimum_equity": float(equity.min()),
        "average_exposure": float(frame["exposure"].mean()),
        "average_cash_weight": float(1.0 - frame["exposure"].mean()),
        "annualized_turnover": float(frame["turnover"].mean() * 252),
    }


def build_return_frame(weights: pd.DataFrame, returns: pd.DataFrame, cost_bps: int) -> pd.DataFrame:
    gross = (weights * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1)
    if len(turnover):
        turnover.iloc[0] = weights.iloc[0].abs().sum()
    net = gross - turnover * cost_bps / 10000.0
    return pd.DataFrame({"portfolio_return": net, "turnover": turnover,
                         "exposure": weights.sum(axis=1)}, index=weights.index)


def main():
    apply_family_endpoint_patch()
    base, returns = base_weights()
    benchmark = pd.DataFrame(
        {name: aligned_data(name)[0].reindex(base.index) for name in FAMILIES},
        index=base.index,
    )
    if benchmark.isna().any().any() or returns.isna().any().any():
        raise AssertionError("common family benchmark/return panel contains missing values")
    overlay, gates = family_gate_weights(base, benchmark)
    scores, eligible = score_frame(250)
    scores = scores.reindex(index=base.index, columns=base.columns)
    eligible = eligible.reindex(index=base.index, columns=base.columns)
    rotated = rotating_gate_weights(base, scores, eligible, gates)
    ungated_replay = rotating_gate_weights(
        base, scores, eligible, pd.DataFrame(False, index=base.index, columns=base.columns)
    )

    # Baseline identity: the ungated replay must exactly reproduce the frozen base.
    if not np.array_equal(base.to_numpy(), base_weights()[0].to_numpy()):
        raise AssertionError("frozen family-rotation base weights changed")
    if not np.array_equal(ungated_replay.to_numpy(), base.to_numpy()):
        raise AssertionError("replacement-rotation builder does not reproduce the frozen base without gates")
    for candidate in (overlay, rotated):
        if not np.all((candidate.to_numpy() >= 0.0) & (candidate.to_numpy() <= 1.0 + 1e-12)):
            raise AssertionError("overlay created negative or above-100% exposure")
    if not np.all(overlay.to_numpy() <= base.to_numpy() + 1e-12):
        raise AssertionError("cash gate increased a family weight")
    if not np.all(rotated.to_numpy().sum(axis=1) <= 1.0 + 1e-12):
        raise AssertionError("replacement rotation exceeded total portfolio exposure")

    rows, curves = [], []
    for cost in COSTS:
        for label, weights in (("BASE_ROTATE_DMA250_TOP2_C5", base),
                               ("FAMILY_SHOCK_GATE_45_10", overlay),
                               ("FAMILY_SHOCK_GATE_ROTATE_45_10", rotated)):
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
    summary.to_csv(DATA / "family_shock_gate_summary.csv", index=False)
    curve.to_csv(DATA / "family_shock_gate_equity.csv", index=False, float_format="%.12g")
    base.to_csv(DATA / "family_shock_gate_base_weights.csv", index_label="Date")
    overlay.to_csv(DATA / "family_shock_gate_overlay_weights.csv", index_label="Date")
    rotated.to_csv(DATA / "family_shock_gate_rotated_weights.csv", index_label="Date")
    gates.to_csv(DATA / "family_shock_gate_states.csv", index_label="Date")
    benchmark.to_csv(DATA / "family_shock_gate_benchmarks.csv", index_label="Date")
    returns.to_csv(DATA / "family_shock_gate_bull_returns.csv", index_label="Date")
    manifest = {
        "start": base.index[0].date().isoformat(), "end": base.index[-1].date().isoformat(),
        "sessions": int(len(base)), "initial": INITIAL, "shock": SHOCK,
        "recovery": RECOVERY, "costs_bps": list(COSTS), "dma": 250, "top_n": 2,
        "rebalance_cadence": 5, "family_specific_only": True, "reallocate_gated_weight": False,
        "families": list(base.columns),
        "benchmark_sha256": hashlib.sha256((DATA / "family_shock_gate_benchmarks.csv").read_bytes()).hexdigest(),
        "returns_sha256": hashlib.sha256((DATA / "family_shock_gate_bull_returns.csv").read_bytes()).hexdigest(),
    }
    (DATA / "family_shock_gate_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("FAMILY-SPECIFIC SHOCK GATE RESULTS")
    print(summary.to_string(index=False))
    print("PASS: frozen base preserved; cash gate only removes exposure; replacement rotation only selects eligible ungated families at scheduled rebalance dates.")
    print("MANIFEST:", json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
