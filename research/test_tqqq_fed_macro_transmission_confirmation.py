"""Frozen Fed lifecycle + macro transmission confirmation study.

A sticky TQQQ defense can arm only when all three conditions are true:
1) live-safe FRESH_PAUSE Fed state,
2) QQQ below 200 DMA,
3) one frozen macro transmission dimension is structurally stressed.

Each macro dimension uses the existing frozen 2-month entry / 3-month recovery
logic and conservative next-month availability mapping. No thresholds are tuned.
Once armed, defense persists until QQQ closes back above 200 DMA.

This tests whether Fed tightening lifecycle becomes materially more useful when
paired with evidence that monetary restriction is actually transmitting into
the economy/markets.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data
from test_tqqq_macro_regime import download_macro, dimension_signal, map_to_daily

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
DIMENSIONS = ("labor_stress", "activity_stress", "credit_stress", "curve_stress")
DEFENSIVE_EXPOSURES = (0.0, 0.5)


def run(f: pd.DataFrame, macro: pd.DataFrame, dim: str, defensive: float):
    macro_state = dimension_signal(macro, (dim,), 1)
    # Use the same conservative availability rule as the frozen macro work.
    available = pd.DataFrame({
        "date": macro_state.index + pd.offsets.MonthBegin(1),
        "state": macro_state.values,
    }).sort_values("date")
    daily = pd.DataFrame({"date": f.index})
    mapped = pd.merge_asof(daily, available, on="date", direction="backward")
    stressed = mapped.set_index("date")["state"].reindex(f.index).fillna(False).astype(bool)

    armed = False
    exposures, triggers, exits = [], [], []
    for date, r in f.iterrows():
        trigger = (
            r.monetary_state == "FRESH_PAUSE"
            and bool(r.dma_below)
            and bool(stressed.loc[date])
        )
        if not armed and trigger:
            armed = True
            triggers.append(date)
        elif armed and pd.notna(r.dma_200) and not bool(r.dma_below):
            armed = False
            exits.append(date)
        exposures.append(defensive if armed else 1.0)

    exposure = pd.Series(exposures, index=f.index).shift(1).fillna(1.0)
    equity = (1 + exposure * f.synthetic_tqqq_ret).cumprod()
    dd = equity / equity.cummax() - 1
    years = (f.index[-1] - f.index[0]).days / 365.25
    return {
        "dimension": dim,
        "defensive_exposure": defensive,
        "final_balance_multiple": float(equity.iloc[-1]),
        "cagr": float(equity.iloc[-1] ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "days_defensive": int((exposure < 1).sum()),
        "defensive_fraction": float((exposure < 1).mean()),
        "trigger_count": len(triggers),
        "exit_count": len(exits),
        "trigger_dates": ",".join(d.date().isoformat() for d in triggers),
        "exit_dates": ",".join(d.date().isoformat() for d in exits),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = load_data()
    macro = download_macro()
    rows = []
    for dim in DIMENSIONS:
        for defensive in DEFENSIVE_EXPOSURES:
            rows.append(run(f, macro, dim, defensive))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "tqqq_fed_macro_transmission_confirmation_summary.csv", index=False)
    print("\nFED PAUSE + 200DMA + FROZEN MACRO TRANSMISSION")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
