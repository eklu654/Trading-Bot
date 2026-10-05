"""Fed + yield-curve lifecycle defense with genuine 200-DMA recovery.

Entry: FRESH_PAUSE + QQQ below 200 DMA + frozen curve stress.
Recovery requires five consecutive trading sessions where QQQ is above the
200 DMA AND the 200 DMA is rising versus the prior session. Signals apply
to the next trading day. This is a predeclared structural confirmation,
not a parameter search.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data
from test_tqqq_macro_regime import download_macro

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
EXPOSURES = (0.0, 0.25, 0.50, 0.75)
RECOVERY_DAYS = 5


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


def run(f, macro, defensive):
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
        recovered = bool(recovery_run.loc[date] >= RECOVERY_DAYS)
        if not armed and trigger:
            armed = True
            triggers.append(date)
        elif armed and recovered:
            armed = False
            exits.append(date)
        exposures.append(defensive if armed else 1.0)

    exposure = pd.Series(exposures, index=f.index).shift(1).fillna(1.0)
    equity = (1 + exposure * f.synthetic_tqqq_ret).cumprod()
    dd = equity / equity.cummax() - 1
    years = (f.index[-1] - f.index[0]).days / 365.25
    return {
        "defensive_exposure": defensive,
        "recovery_rule": "5 sessions above 200DMA + rising 200DMA",
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
    out = pd.DataFrame([run(f, macro, x) for x in EXPOSURES])
    out.to_csv(OUT / "tqqq_fed_curve_rising_dma_recovery_summary.csv", index=False)
    print("\nFED PAUSE + CURVE + RISING 200DMA RECOVERY")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
