"""Frozen macro-dimension attribution study for TQQQ structural defense.

Purpose:
Identify which already-frozen macro dimensions are responsible for the
composite strategy's modern-era over-defense, without tuning thresholds.

This is attribution, not optimization. It reuses the existing labor/activity/
credit/curve stress definitions and the same 2-observation entry / 3-observation
recovery persistence used by the baseline macro classifier.

Variants:
- each individual dimension
- each pair
- each triple
- all four
- baseline 2-of-4
- baseline 3-of-4
- baseline 4-of-4

For each variant, defense begins after two consecutive monthly observations
satisfy the selected structural condition and ends after three consecutive
monthly observations do not. The defensive exposure is frozen at 0% TQQQ.

This deliberately does not search thresholds, exposure, DMA lengths, or
named-crisis dates.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from research.test_tqqq_macro_regime import download_macro, download_qqq, build_synthetic

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
PERIODS = {
    "1999_2009": ("1999-03-10", "2009-12-31"),
    "2010_2019": ("2010-01-01", "2019-12-31"),
    "2020_2026": ("2020-01-01", "2026-10-04"),
}
DIMS = ("labor_stress", "activity_stress", "credit_stress", "curve_stress")


def build_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    macro = download_macro()
    qqq = build_synthetic(download_qqq())
    return macro, qqq


def dimension_signal(macro: pd.DataFrame, dims: tuple[str, ...], quorum: int) -> pd.Series:
    raw = macro[list(dims)].sum(axis=1) >= quorum
    states: list[bool] = []
    active = False
    det_run = 0
    safe_run = 0
    for value in raw.fillna(False):
        if value:
            det_run += 1
            safe_run = 0
        else:
            det_run = 0
            safe_run += 1
        if not active and det_run >= 2:
            active = True
        elif active and safe_run >= 3:
            active = False
        states.append(active)
    return pd.Series(states, index=macro.index, dtype=bool)


def map_to_daily(macro_state: pd.Series, qqq: pd.DataFrame) -> pd.Series:
    available = pd.DataFrame(
        {"date": macro_state.index + pd.offsets.MonthBegin(1), "state": macro_state.values}
    ).sort_values("date")
    daily = pd.DataFrame({"date": qqq.index})
    mapped = pd.merge_asof(daily, available, on="date", direction="backward")
    return mapped.set_index("date")["state"].fillna(False).astype(bool)


def evaluate(qqq: pd.DataFrame, daily_defense: pd.Series, label: str) -> dict[str, object]:
    defense = daily_defense.reindex(qqq.index).fillna(False)
    weights = np.where(defense.to_numpy(), 0.0, 1.0)
    daily_return = weights * qqq["overnight_3x"].to_numpy() + 0.0
    # Preserve the existing macro baseline's overnight/intraday accounting:
    # a close-derived monthly state affects the next available trading day.
    prev_w = np.roll(weights, 1)
    prev_w[0] = 1.0
    daily_return = (
        (1 + prev_w * qqq["overnight_3x"].to_numpy())
        * (1 + weights * qqq["intraday_3x"].to_numpy())
        - 1
    )
    equity = INITIAL * np.cumprod(1 + daily_return)
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1
    years = max((qqq.index[-1] - qqq.index[0]).days / 365.25, 1 / 365.25)
    return {
        "variant": label,
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "minimum_equity": float(equity.min()),
        "average_exposure": float(weights.mean()),
        "defensive_days": int(defense.sum()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    macro, qqq = build_features()
    rows: list[dict[str, object]] = []
    paths: list[pd.DataFrame] = []

    specs: list[tuple[str, tuple[str, ...], int]] = []
    for dim in DIMS:
        specs.append((dim.replace("_stress", ""), (dim,), 1))
    for n in (2, 3, 4):
        for dims in combinations(DIMS, n):
            specs.append((f"{n}of{n}_" + "_".join(d.replace("_stress", "") for d in dims), dims, n))
    specs.extend(
        [
            ("baseline_2of4", DIMS, 2),
            ("baseline_3of4", DIMS, 3),
            ("baseline_4of4", DIMS, 4),
        ]
    )

    for label, dims, quorum in specs:
        monthly = dimension_signal(macro, dims, quorum)
        daily = map_to_daily(monthly, qqq)
        row = evaluate(qqq, daily, label)
        for period, (start, end) in PERIODS.items():
            sliced = qqq.loc[start:end]
            ds = daily.loc[start:end]
            w = np.where(ds.to_numpy(), 0.0, 1.0)
            prev_w = np.roll(w, 1)
            prev_w[0] = 1.0
            r = (
                (1 + prev_w * sliced["overnight_3x"].to_numpy())
                * (1 + w * sliced["intraday_3x"].to_numpy())
                - 1
            )
            eq = INITIAL * np.cumprod(1 + r)
            years = max((sliced.index[-1] - sliced.index[0]).days / 365.25, 1 / 365.25)
            dd = eq / np.maximum.accumulate(eq) - 1
            row[f"{period}_cagr"] = float((eq[-1] / INITIAL) ** (1 / years) - 1)
            row[f"{period}_max_drawdown"] = float(dd.min())
            row[f"{period}_defense_pct"] = float(ds.mean())
        rows.append(row)
        paths.append(pd.DataFrame({"Date": qqq.index, "variant": label, "defensive": daily.to_numpy()}))

    # Permanent benchmark.
    bh = evaluate(qqq, pd.Series(False, index=qqq.index), "BUY_AND_HOLD")
    rows.append(bh)
    paths.append(pd.DataFrame({"Date": qqq.index, "variant": "BUY_AND_HOLD", "defensive": False}))

    result = pd.DataFrame(rows).sort_values("final_balance", ascending=False)
    result.to_csv(OUT / "tqqq_macro_dimension_attribution.csv", index=False)
    pd.concat(paths, ignore_index=True).to_csv(
        OUT / "tqqq_macro_dimension_attribution_paths.csv", index=False
    )

    print("\nMACRO DIMENSION ATTRIBUTION — FROZEN THRESHOLDS")
    print(result.to_string(index=False))
    print("\nReport completed.")
    print(f"Artifacts written to {OUT}")


if __name__ == "__main__":
    main()
