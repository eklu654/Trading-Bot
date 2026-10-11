"""Frozen family-rotation selector audit: attribution and recovery participation, no tuning."""
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
COST_BPS = 25
FAMILIES = ("SP500", "NASDAQ100", "SEMICONDUCTORS", "DOW30", "RUSSELL2000")
SPLITS = {
    "full": ("2010-03-12", "2026-10-02"),
    "train": ("2010-03-12", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-10-02"),
}

from research.replay_family_rotation_account import apply_family_endpoint_patch
from research.test_dma_family_rotation_risk_overlay import base_weights, aligned_data


def make_episode_table(equity: pd.Series) -> pd.DataFrame:
    """Identify peak-to-trough episodes and the subsequent peak recovery, if any."""
    peak_value = equity.cummax()
    dd = equity / peak_value - 1.0
    in_episode = dd < -1e-12
    episodes = []
    i = 0
    while i < len(equity):
        if not in_episode.iloc[i]:
            i += 1
            continue
        start = i
        peak = start - 1 if start > 0 else start
        trough = start
        j = start
        while j < len(equity) and in_episode.iloc[j]:
            if dd.iloc[j] < dd.iloc[trough]:
                trough = j
            j += 1
        recovered = j if j < len(equity) else None
        episodes.append({
            "peak_date": equity.index[peak],
            "peak_equity": float(equity.iloc[peak]),
            "trough_date": equity.index[trough],
            "trough_equity": float(equity.iloc[trough]),
            "max_drawdown": float(dd.iloc[trough]),
            "recovery_date": equity.index[recovered] if recovered is not None else pd.NaT,
            "recovery_sessions": int(recovered - trough) if recovered is not None else np.nan,
            "episode_end_idx": recovered if recovered is not None else len(equity) - 1,
            "peak_idx": peak, "trough_idx": trough,
        })
        i = j
    return pd.DataFrame(episodes)


def main():
    apply_family_endpoint_patch()
    weights, returns = base_weights()
    weights = weights.loc["2010-03-12":"2026-10-02"].copy()
    returns = returns.reindex(index=weights.index, columns=FAMILIES)
    if weights.isna().any().any() or returns.isna().any().any():
        raise AssertionError("weights/returns contain missing values")
    if (weights < -1e-12).any().any() or (weights.sum(axis=1) > 1 + 1e-12).any():
        raise AssertionError("invalid long-only exposure")
    if not weights.columns.equals(returns.columns):
        raise AssertionError("weights and returns columns differ")

    gross = (weights * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights.iloc[0].abs().sum()
    net = gross - turnover * COST_BPS / 10000.0
    equity = INITIAL * (1.0 + net).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    family_contrib = weights * returns
    family_weight_days = weights.copy()
    family_weight_days["Date"] = family_weight_days.index
    family_weight_days.to_csv(DATA / "selector_audit_daily_weights.csv", index=False)
    family_contrib_out = family_contrib.copy()
    family_contrib_out["Date"] = family_contrib_out.index
    family_contrib_out.to_csv(DATA / "selector_audit_daily_family_contributions.csv", index=False)

    # Overall and chronological-split selector diagnostics.
    summaries = []
    for split, (start, end) in SPLITS.items():
        mask = (weights.index >= start) & (weights.index <= end)
        w = weights.loc[mask]
        r = returns.loc[mask]
        c = family_contrib.loc[mask]
        segment_net = net.loc[mask]
        eq = INITIAL * (1.0 + segment_net).cumprod()
        dd = eq / eq.cummax() - 1.0
        row = {
            "split": split, "start": str(w.index.min().date()), "end": str(w.index.max().date()),
            "sessions": int(len(w)), "ending_equity": float(eq.iloc[-1]),
            "max_drawdown": float(dd.min()), "avg_exposure": float(w.sum(axis=1).mean()),
            "cash_fraction_sessions": float((w.sum(axis=1) < 0.999999).mean()),
            "annualized_turnover": float(turnover.loc[mask].mean() * 252),
            "avg_daily_net_return": float(segment_net.mean()),
        }
        for fam in FAMILIES:
            row[f"{fam}_avg_weight"] = float(w[fam].mean())
            row[f"{fam}_weight_share"] = float(w[fam].sum() / max(w.to_numpy().sum(), 1e-12))
            row[f"{fam}_weighted_return_sum"] = float(c[fam].sum())
            row[f"{fam}_negative_contribution_sum"] = float(c[fam].clip(upper=0).sum())
            row[f"{fam}_positive_contribution_sum"] = float(c[fam].clip(lower=0).sum())
        summaries.append(row)
    summary = pd.DataFrame(summaries)
    summary.to_csv(DATA / "selector_audit_summary.csv", index=False)

    # Worst non-overlapping drawdown episodes in the whole observed history.
    episodes = make_episode_table(equity)
    episodes = episodes.sort_values("max_drawdown").head(12).copy()
    event_rows = []
    for _, ep in episodes.iterrows():
        peak_i, trough_i = int(ep["peak_idx"]), int(ep["trough_idx"])
        end_i = int(ep["episode_end_idx"])
        # Contributions from peak day through trough and from trough through
        # the first 63 sessions after trough, respectively; additive attribution.
        episode_slice = slice(peak_i + 1, trough_i + 1)
        recovery_slice = slice(trough_i + 1, min(trough_i + 64, len(weights)))
        wr = weights.iloc[peak_i:trough_i + 1]
        er = equity.iloc[peak_i:trough_i + 1]
        row = {
            "peak_date": str(ep["peak_date"].date()),
            "trough_date": str(ep["trough_date"].date()),
            "recovery_date": str(ep["recovery_date"].date()) if pd.notna(ep["recovery_date"]) else "",
            "max_drawdown": float(ep["max_drawdown"]),
            "peak_equity": float(ep["peak_equity"]),
            "trough_equity": float(ep["trough_equity"]),
            "recovery_sessions": ep["recovery_sessions"],
            "drawdown_sessions": int(trough_i - peak_i),
            "mean_exposure_peak_to_trough": float(wr.sum(axis=1).mean()),
            "SOXL_mean_weight_peak_to_trough": float(wr["SEMICONDUCTORS"].mean()),
            "SOXL_weight_share_peak_to_trough": float(wr["SEMICONDUCTORS"].sum() / max(wr.to_numpy().sum(), 1e-12)),
            "net_return_peak_to_trough": float((1 + net.iloc[episode_slice]).prod() - 1) if trough_i > peak_i else 0.0,
            "net_return_next_63_sessions": float((1 + net.iloc[recovery_slice]).prod() - 1) if recovery_slice.stop > recovery_slice.start else np.nan,
            "exposure_next_63_sessions": float(weights.iloc[recovery_slice].sum(axis=1).mean()) if recovery_slice.stop > recovery_slice.start else np.nan,
        }
        for fam in FAMILIES:
            row[f"{fam}_contribution_drawdown"] = float(family_contrib[fam].iloc[episode_slice].sum())
            row[f"{fam}_contribution_next_63"] = float(family_contrib[fam].iloc[recovery_slice].sum()) if recovery_slice.stop > recovery_slice.start else np.nan
            row[f"{fam}_mean_weight_next_63"] = float(weights[fam].iloc[recovery_slice].mean()) if recovery_slice.stop > recovery_slice.start else np.nan
        event_rows.append(row)
    event_table = pd.DataFrame(event_rows)
    event_table.to_csv(DATA / "selector_audit_worst_drawdowns.csv", index=False)

    # Worst portfolio drawdown days: snapshot selected exposure and realized family losses.
    worst_days = drawdown.nsmallest(100).index
    daily = pd.DataFrame({
        "Date": weights.index,
        "equity": equity.to_numpy(),
        "drawdown": drawdown.to_numpy(),
        "net_return": net.to_numpy(),
        "gross_return": gross.to_numpy(),
        "turnover": turnover.to_numpy(),
        "exposure": weights.sum(axis=1).to_numpy(),
    }).set_index("Date")
    for fam in FAMILIES:
        daily[f"{fam}_weight"] = weights[fam]
        daily[f"{fam}_return"] = returns[fam]
        daily[f"{fam}_contribution"] = family_contrib[fam]
    daily.loc[worst_days].sort_values("drawdown").to_csv(DATA / "selector_audit_worst_100_days.csv")

    manifest = {
        "strategy": "BASE_ROTATE_DMA250_TOP2_C5",
        "start": str(weights.index.min().date()), "end": str(weights.index.max().date()),
        "sessions": int(len(weights)), "initial_equity": INITIAL, "cost_bps": COST_BPS,
        "purpose": "diagnostic attribution only; no candidate selection or parameter tuning",
        "weighting": "DMA250 eligibility; rank benchmark distance above DMA; equal-weight top two; rebalance every five sessions",
        "data_sha256": {
            "summary": hashlib.sha256((DATA / "selector_audit_summary.csv").read_bytes()).hexdigest(),
            "worst_drawdowns": hashlib.sha256((DATA / "selector_audit_worst_drawdowns.csv").read_bytes()).hexdigest(),
            "daily_weights": hashlib.sha256((DATA / "selector_audit_daily_weights.csv").read_bytes()).hexdigest(),
            "worst_days": hashlib.sha256((DATA / "selector_audit_worst_100_days.csv").read_bytes()).hexdigest(),
        },
    }
    (DATA / "selector_audit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("FROZEN SELECTOR AUDIT SUMMARY")
    print(summary.to_string(index=False))
    print("\nWORST DRAWDOWN EPISODES")
    print(event_table.to_string(index=False))
    print("\nAUDIT MANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
