"""Post-tightening Fed lifecycle transmission study.

This is the next frozen architecture test, not parameter optimization.

Entry requires:
- Fed state is FRESH_PAUSE or EASING (both live-safe states),
- QQQ below 200 DMA,
- one frozen macro transmission dimension is structurally stressed.

Recovery is fixed at five consecutive sessions above a rising 200 DMA.
Defense is 0% TQQQ. The study reports each transmission dimension separately.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data
from test_tqqq_macro_regime import download_macro

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
DIMS = ("labor_stress", "activity_stress", "credit_stress", "curve_stress")


def dimension_signal(macro, dim):
    raw = macro[dim].fillna(False)
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


def run(f, macro, dim):
    signal = dimension_signal(macro, dim)
    available = pd.DataFrame({
        "date": signal.index + pd.offsets.MonthBegin(1),
        "stress": signal.values,
    }).sort_values("date")
    mapped = pd.merge_asof(
        pd.DataFrame({"date": f.index}), available,
        on="date", direction="backward"
    ).set_index("date")
    stress = mapped["stress"].reindex(f.index).fillna(False).astype(bool)

    dma_rising = f["dma_200"] > f["dma_200"].shift(1)
    recovery_raw = (~f["dma_below"]) & dma_rising & f["dma_200"].notna()
    recovery_run = recovery_raw.astype(int).groupby((~recovery_raw).cumsum()).cumsum()

    armed = False
    exposures = []
    triggers = []
    exits = []
    for date, r in f.iterrows():
        trigger = (
            r.monetary_state in ("FRESH_PAUSE", "EASING")
            and bool(r.dma_below)
            and bool(stress.loc[date])
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
    equity = (1 + exposure * f.synthetic_tqqq_ret).cumprod()
    dd = equity / equity.cummax() - 1
    years = (f.index[-1] - f.index[0]).days / 365.25
    row = {
        "dimension": dim,
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
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = load_data()
    macro = download_macro()
    out = pd.DataFrame([run(f, macro, dim) for dim in DIMS])
    out.to_csv(OUT / "tqqq_fed_post_tightening_transmission_summary.csv", index=False)
    print("\nFRESH PAUSE OR EASING + 200DMA + MACRO TRANSMISSION")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
