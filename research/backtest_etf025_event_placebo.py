"""ETF-025: event-concentration placebo diagnostic for the walk-forward inverse signal.

The ETF-023/024 advantage is concentrated in three holdout activation dates.
This diagnostic does not optimize anything. It compares those fixed dates with
deterministic random-date placebos having the same event count, measuring
whether their subsequent benchmark weakness is unusual.

The dates come from the frozen research record, not from this script's output.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
SEED=20261003
HOLDOUT_START="2023-01-01"
FIXED_DATES=pd.DatetimeIndex(["2024-07-09","2024-07-10","2024-07-11"])
N_DRAWS=20000
HORIZONS=(5,10,20,40)


def load(symbol):
    return pd.read_csv(DATA/f"{symbol.lower()}_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()["close"]


def main():
    prices=pd.concat({s:load(s) for s in ("QQQ","SPY","SOXX")},axis=1).dropna()
    bench=prices.pct_change().mean(axis=1)
    # Equal-weight daily arithmetic return is the same benchmark convention
    # used by the walk-forward research diagnostic.
    dates=prices.index[prices.index>=pd.Timestamp(HOLDOUT_START)]
    dates=dates[dates.isin(prices.index)]

    def forward(h):
        return prices.mean(axis=1).shift(-h)/prices.mean(axis=1)-1

    rng=np.random.default_rng(SEED)
    rows=[]
    for h in HORIZONS:
        f=forward(h)
        fixed=f.reindex(FIXED_DATES).dropna()
        fixed_mean=float(fixed.mean())
        fixed_median=float(fixed.median())
        sample_size=len(fixed)

        eligible=dates[dates<=f.index.max()-pd.tseries.offsets.BDay(h)]
        placebo=np.empty(N_DRAWS)
        for i in range(N_DRAWS):
            draw=rng.choice(eligible,size=sample_size,replace=False)
            placebo[i]=f.reindex(draw).mean()

        rows.append({
            "horizon":h,
            "fixed_events":sample_size,
            "fixed_mean_forward_return":fixed_mean,
            "fixed_median_forward_return":fixed_median,
            "placebo_mean":float(placebo.mean()),
            "placebo_std":float(placebo.std(ddof=1)),
            "placebo_p05":float(np.quantile(placebo,.05)),
            "placebo_p50":float(np.quantile(placebo,.50)),
            "placebo_p95":float(np.quantile(placebo,.95)),
            "percent_placebo_at_or_below_fixed":float((placebo<=fixed_mean).mean()),
            "percent_placebo_below_zero":float((placebo<0).mean()),
        })

    out=pd.DataFrame(rows)
    out.to_csv(DATA/"etf025_event_placebo_results.csv",index=False)
    print("=== ETF-025 EVENT-CONCENTRATION PLACEBO ===")
    print(out.to_string(index=False))


if __name__=="__main__":
    main()
