"""Fed-gated frozen macro quorum test.

Entry requires:
- FRESH_PAUSE or EASING Fed state,
- QQQ below 200 DMA,
- >=2 of 4 frozen macro transmission dimensions structurally stressed.

A 3-of-4 control is also tested. Macro dimensions use the existing frozen
2-month entry / 3-month recovery persistence and conservative next-month
availability. Recovery is five sessions above a rising 200 DMA. Defense is 0%.
No thresholds are optimized here.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data
from test_tqqq_macro_regime import download_macro

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"


def dim_state(macro, dim):
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


def run(f, macro, quorum):
    daily_dims = []
    for dim in ("labor_stress", "activity_stress", "credit_stress", "curve_stress"):
        state = dim_state(macro, dim)
        available = pd.DataFrame({
            "date": state.index + pd.offsets.MonthBegin(1),
            dim: state.values,
        }).sort_values("date")
        mapped = pd.merge_asof(
            pd.DataFrame({"date": f.index}), available,
            on="date", direction="backward"
        ).set_index("date")
        daily_dims.append(mapped[dim].reindex(f.index).fillna(False).astype(int))
    macro_count = pd.concat(daily_dims, axis=1).sum(axis=1)

    dma_rising = f["dma_200"] > f["dma_200"].shift(1)
    recovery_raw = (~f["dma_below"]) & dma_rising & f["dma_200"].notna()
    recovery_run = recovery_raw.astype(int).groupby((~recovery_raw).cumsum()).cumsum()

    armed = False
    exposures, triggers, exits = [], [], []
    for date, r in f.iterrows():
        trigger = (
            r.monetary_state in ("FRESH_PAUSE", "EASING")
            and bool(r.dma_below)
            and int(macro_count.loc[date]) >= quorum
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
    return {
        "quorum": f"{quorum}of4",
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
    out = pd.DataFrame([run(f, macro, q) for q in (2, 3)])
    out.to_csv(OUT / "tqqq_fed_gated_macro_quorum_summary.csv", index=False)
    print("\nFED GATED MACRO QUORUM + 200DMA")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
