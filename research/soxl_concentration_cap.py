"""One preregistered SOXL family concentration cap on the frozen DMA250/top-2/cadence-5 rotation."""
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
SPLITS = {
    "full": ("2010-03-12", "2026-10-02"),
    "train": ("2010-03-12", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-10-02"),
}

from research.family_specific_shock_gate import apply_family_endpoint_patch, aligned_data, base_weights, build_return_frame, metrics
from research.test_dma_family_rotation_risk_overlay import FAMILIES, score_frame


def soxl_cap_weights(base: pd.DataFrame, scores: pd.DataFrame,
                     eligible: pd.DataFrame, cap: float = SOXL_CAP,
                     top_n: int = TOP_N, cadence: int = CADENCE) -> pd.DataFrame:
    """Cap SOXL only when selected; fill its released 25% slot with next rank if eligible."""
    if not 0.0 < cap < 1.0:
        raise ValueError("cap must be in (0, 1)")
    for frame in (scores, eligible):
        if not frame.index.equals(base.index) or not frame.columns.equals(base.columns):
            raise ValueError("scores and eligibility must match base axes")
    if top_n < 1 or cadence < 1:
        raise ValueError("top_n and cadence must be positive")
    weights = pd.DataFrame(0.0, index=base.index, columns=base.columns)
    current = pd.Series(0.0, index=base.columns, dtype=float)
    last_rebalance = -cadence
    for i, date in enumerate(base.index):
        if i - last_rebalance >= cadence:
            candidates = scores.loc[date].where(eligible.loc[date].astype(bool)).dropna()
            selected = list(candidates.nlargest(min(top_n, len(candidates))).index)
            current[:] = 0.0
            if selected:
                current.loc[selected] = 1.0 / len(selected)
            if SOXL_FAMILY in selected:
                # With top_n=2 and two selected families, the non-SOXL slot
                # remains 50%, SOXL is capped at 25%, and a third eligible
                # family receives the released 25%. Missing replacement stays cash.
                current.loc[SOXL_FAMILY] = cap
                replacements = candidates.drop(labels=selected, errors="ignore")
                if len(replacements):
                    replacement = replacements.nlargest(1).index[0]
                    current.loc[replacement] = cap
            last_rebalance = i
        weights.loc[date] = current
    return weights


def main():
    apply_family_endpoint_patch()
    base, returns = base_weights()
    scores, eligible = score_frame(250)
    scores = scores.reindex(index=base.index, columns=base.columns)
    eligible = eligible.reindex(index=base.index, columns=base.columns)
    candidate = soxl_cap_weights(base, scores, eligible)

    # The candidate must be byte-for-byte equivalent to the frozen base
    # on dates where SOXL is not in the selected top two.
    selected_soxl = base[SOXL_FAMILY] > 0.0
    unaffected = ~selected_soxl
    if not np.array_equal(candidate.loc[unaffected].to_numpy(),
                          base.loc[unaffected].to_numpy()):
        raise AssertionError("candidate changed weights on dates where SOXL was not selected")
    if not np.all(candidate.to_numpy() >= 0.0) or not np.all(candidate.sum(axis=1).to_numpy() <= 1.0 + 1e-12):
        raise AssertionError("candidate has invalid weights or exceeds 100% exposure")
    if (candidate[SOXL_FAMILY] > SOXL_CAP + 1e-12).any():
        raise AssertionError("SOXL concentration cap was breached")

    rows, curves = [], []
    for cost in COSTS:
        for label, weights in (("BASE_ROTATE_DMA250_TOP2_C5", base),
                               ("SOXL_CAP25_ROTATE", candidate)):
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
    summary.to_csv(DATA / "soxl_cap_summary.csv", index=False)
    curve.to_csv(DATA / "soxl_cap_equity.csv", index=False, float_format="%.12g")
    base.to_csv(DATA / "soxl_cap_base_weights.csv", index_label="Date")
    candidate.to_csv(DATA / "soxl_cap_candidate_weights.csv", index_label="Date")
    returns.to_csv(DATA / "soxl_cap_bull_returns.csv", index_label="Date")
    manifest = {
        "start": base.index[0].date().isoformat(), "end": base.index[-1].date().isoformat(),
        "sessions": int(len(base)), "initial": INITIAL, "soxl_cap": SOXL_CAP,
        "dma": 250, "top_n": TOP_N, "cadence": CADENCE, "costs_bps": list(COSTS),
        "replacement": "next-highest eligible family, otherwise cash",
        "candidate_changes_only_when_soxl_selected": True,
        "returns_sha256": hashlib.sha256((DATA / "soxl_cap_bull_returns.csv").read_bytes()).hexdigest(),
        "base_weights_sha256": hashlib.sha256((DATA / "soxl_cap_base_weights.csv").read_bytes()).hexdigest(),
        "candidate_weights_sha256": hashlib.sha256((DATA / "soxl_cap_candidate_weights.csv").read_bytes()).hexdigest(),
    }
    (DATA / "soxl_cap_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("SOXL CONCENTRATION CAP RESULTS")
    print(summary.to_string(index=False))
    print("PASS: frozen base unchanged outside SOXL-selected rebalance decisions; SOXL <= 25%; total exposure <= 100%.")
    print("MANIFEST:", json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
