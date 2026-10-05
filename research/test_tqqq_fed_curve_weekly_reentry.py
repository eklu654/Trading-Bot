"""Fed pause + yield-curve confirmation with the existing 1-week DMA reentry rule.

Entry: FRESH_PAUSE + QQQ below 200 DMA + frozen curve_stress.
Exit/reentry: once defensive, remain defensive until QQQ has closed above
its 200 DMA for 5 consecutive trading sessions. Exposure applies next day.
No crisis labels or future Fed information are used.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data
from test_tqqq_macro_regime import download_macro

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
EXPOSURES = (0.0, 0.25, 0.50, 0.75)
REENTRY_DAYS = 5


def curve_signal(macro: pd.DataFrame) -> pd.Series:
    raw = macro["curve_stress"].fillna(False)
    active = False
    stress_run = 0
    safe_run = 0
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


def run(f: pd.DataFrame, macro: pd.DataFrame, defensive: float):
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

    below = f["dma_below"].fillna(False)
    above_run = below.eq(False).astype(int).groupby(below.astype(int).cumsum()).cumsum()

    armed = False
    exposures, triggers, exits = [], [], []
    for date, r in f.iterrows():
        trigger = (
            r.monetary_state == "FRESH_PAUSE"
            and bool(r.dma_below)
            and bool(curve_daily.loc[date])
        )
        recovered = pd.notna(r.dma_200) and not bool(r.dma_below) and int(above_run.loc[date]) >= REENTRY_DAYS
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
        "reentry_above_dma_days": REENTRY_DAYS,
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
    out.to_csv(OUT / "tqqq_fed_curve_weekly_reentry_summary.csv", index=False)
    print("\nFED PAUSE + CURVE + 200DMA + 5-DAY REENTRY")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
