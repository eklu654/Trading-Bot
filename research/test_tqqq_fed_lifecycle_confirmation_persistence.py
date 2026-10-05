"""Predeclared structural-confirmation test for the Fed lifecycle signal.

A Fed pause + QQQ below 200 DMA is only allowed to arm after the QQQ close
has remained below the 200 DMA for N consecutive trading sessions. This is
intended to distinguish a structural break from short DMA whipsaws.

Persistence values are deliberately fixed before inspecting results: 10, 20,
and 40 trading sessions. Exposures tested: 0% and 50% TQQQ exposure while
defensive. Signals apply to the next trading day.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from test_tqqq_fed_lifecycle_sticky import load_data

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
PERSISTENCE = (10, 20, 40)
DEFENSIVE_EXPOSURES = (0.0, 0.5)


def backtest(f: pd.DataFrame, persistence: int, defensive_exposure: float):
    below = f["dma_below"].fillna(False)
    # Count consecutive trading sessions below the 200 DMA.
    run = below.astype(int).groupby((~below).cumsum()).cumsum()
    armed = False
    exposures = []
    triggers = []
    exits = []
    for date, r in f.iterrows():
        trigger = (
            r.monetary_state == "FRESH_PAUSE"
            and bool(r.dma_below)
            and int(run.loc[date]) >= persistence
        )
        if not armed and trigger:
            armed = True
            triggers.append(date)
        elif armed and pd.notna(r.dma_200) and not bool(r.dma_below):
            armed = False
            exits.append(date)
        exposures.append(defensive_exposure if armed else 1.0)

    exposure = pd.Series(exposures, index=f.index).shift(1).fillna(1.0)
    equity = (1 + exposure * f.synthetic_tqqq_ret).cumprod()
    dd = equity / equity.cummax() - 1
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = equity.iloc[-1] ** (1 / years) - 1
    return {
        "persistence_sessions": persistence,
        "defensive_exposure": defensive_exposure,
        "final_balance_multiple": float(equity.iloc[-1]),
        "cagr": float(cagr),
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
    rows = []
    for persistence in PERSISTENCE:
        for exposure in DEFENSIVE_EXPOSURES:
            rows.append(backtest(f, persistence, exposure))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "tqqq_fed_lifecycle_confirmation_persistence_summary.csv", index=False)
    print("\nFED PAUSE + PERSISTENT 200DMA CONFIRMATION")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
