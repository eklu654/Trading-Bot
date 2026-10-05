"""Chronological holdout validation of the frozen Fed+curve+rising-DMA candidate.

No parameters are changed here. The exact candidate from the prior study is
replayed and compared with buy-and-hold synthetic TQQQ. Metrics are reported
for the full sample and three chronological eras:
1999-2009, 2010-2019, 2020-2026.

Candidate:
- entry: FRESH_PAUSE + curve stress + QQQ below 200 DMA
- defense: 0% TQQQ
- recovery: 5 consecutive sessions above 200 DMA with rising 200 DMA
- next-day execution
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data
from test_tqqq_macro_regime import download_macro

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0


def curve_signal(macro):
    raw = macro["curve_stress"].fillna(False)
    active = False
    stress_run = safe_run = 0
    states = []
    for value in raw:
        if value:
            stress_run += 1
            safe_run = 0
        else:
            stress_run = 0
            safe_run += 1
        if not active and stress_run >= 2:
            active = True
        elif active and safe_run >= 3:
            active = False
        states.append(active)
    return pd.Series(states, index=macro.index, dtype=bool)


def build_candidate(f, macro):
    curve = curve_signal(macro)
    available = pd.DataFrame({
        "date": curve.index + pd.offsets.MonthBegin(1),
        "curve_stress": curve.values,
    }).sort_values("date")
    mapped = pd.merge_asof(
        pd.DataFrame({"date": f.index}), available,
        on="date", direction="backward"
    ).set_index("date")
    curve_daily = mapped["curve_stress"].reindex(f.index).fillna(False).astype(bool)

    dma_rising = f["dma_200"] > f["dma_200"].shift(1)
    recovery_raw = (~f["dma_below"]) & dma_rising & f["dma_200"].notna()
    recovery_run = recovery_raw.astype(int).groupby((~recovery_raw).cumsum()).cumsum()

    armed = False
    exposures, triggers, exits = [], [], []
    for date, r in f.iterrows():
        trigger = (
            r.monetary_state == "FRESH_PAUSE"
            and bool(r.dma_below)
            and bool(curve_daily.loc[date])
        )
        recovered = bool(recovery_run.loc[date] >= 5)
        if not armed and trigger:
            armed = True
            triggers.append(date)
        elif armed and recovered:
            armed = False
            exits.append(date)
        exposures.append(0.0 if armed else 1.0)

    exposure = pd.Series(exposures, index=f.index).shift(1).fillna(1.0)
    daily = exposure * f.synthetic_tqqq_ret
    equity = INITIAL * (1 + daily).cumprod()
    return equity, exposure, triggers, exits


def metrics(equity, exposure, start, end, label):
    sub = equity.loc[start:end]
    w = exposure.loc[start:end]
    if len(sub) < 2:
        return None
    years = (sub.index[-1] - sub.index[0]).days / 365.25
    peak = sub.cummax()
    dd = sub / peak - 1
    return {
        "strategy": label,
        "period": f"{start}:{end}",
        "start_balance": float(sub.iloc[0]),
        "end_balance": float(sub.iloc[-1]),
        "period_cagr": float((sub.iloc[-1] / sub.iloc[0]) ** (1 / years) - 1),
        "period_max_drawdown": float(dd.min()),
        "defensive_fraction": float((w < 1).mean()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = load_data()
    macro = download_macro()
    candidate, exposure, triggers, exits = build_candidate(f, macro)
    buyhold = INITIAL * (1 + f.synthetic_tqqq_ret).cumprod()
    always = pd.Series(1.0, index=f.index)

    rows = []
    periods = [
        ("1999-03-10", "2009-12-31"),
        ("2010-01-01", "2019-12-31"),
        ("2020-01-01", "2026-10-04"),
        ("1999-03-10", "2026-10-04"),
    ]
    for start, end in periods:
        rows.append(metrics(candidate, exposure, start, end, "FED_CURVE_RISING_DMA"))
        rows.append(metrics(buyhold, always, start, end, "BUY_AND_HOLD"))

    summary = pd.DataFrame(rows)
    candidate.to_csv(OUT / "tqqq_fed_curve_rising_dma_candidate_equity.csv", header=["equity"])
    exposure.to_csv(OUT / "tqqq_fed_curve_rising_dma_candidate_exposure.csv", header=["exposure"])
    summary.to_csv(OUT / "tqqq_fed_curve_rising_dma_holdout_summary.csv", index=False)

    print("\nFROZEN FED+CURVE+RISING-DMA CHRONOLOGICAL HOLDOUT")
    print(summary.to_string(index=False))
    print("\nTriggers:", [d.date().isoformat() for d in triggers])
    print("Recoveries:", [d.date().isoformat() for d in exits])


if __name__ == "__main__":
    main()
