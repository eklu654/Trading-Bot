"""Fed-cycle event study for TQQQ/Nasdaq defensive research.

Purpose
-------
Establish the historical monetary-policy timeline before combining Fed regime
information with the DMA/partial-exposure family.

This is a DESCRIPTIVE study, not an optimized trading strategy.

Fixed benchmark principle
-------------------------
The maximum-growth tier remains 100% TQQQ buy-and-hold with no DMA.
This study does not modify that benchmark.

Method
------
1. Pull the Fed target-rate history from FRED series derived from FOMC actions.
2. Use the Federal Reserve's published tightening-cycle boundaries as the
   cycle labels: 1994-02→1995-03, 1999-07→2000-07, 2004-06→2006-08,
   2015-12→2018-07, and 2022-03→present.
3. Pull Nasdaq-100 history (^NDX) and, where available, actual TQQQ history.
4. Measure forward market outcomes from first-hike and final-hike dates:
   3/6/12/18/24 months, plus max drawdown in each window.
5. Produce the complete Fed action timeline so later studies can classify
   monetary states without hindsight.

No Fed action is treated as a standalone sell signal here.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "1994-01-01"
END = "2026-10-04"

FRED_SERIES = {
    "target_old": "DFEDTAR",
    "target_upper": "DFEDTARU",
    "target_lower": "DFEDTARL",
}

# Published by the Federal Reserve in its financial-conditions research.
# These are descriptive cycle labels, not optimized from market outcomes.
CYCLES = [
    ("1994-02-01", "1995-03-01", "1994-95"),
    ("1999-07-01", "2000-07-01", "1999-2000"),
    ("2004-06-01", "2006-08-01", "2004-06"),
    ("2015-12-01", "2018-07-01", "2015-18"),
    ("2022-03-01", END, "2022-present"),
]


def fred_csv(series_id: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    req = Request(url, headers={"User-Agent": "Trading-Bot-research/1.0"})
    with urlopen(req, timeout=30) as response:
        data = response.read()
    frame = pd.read_csv(BytesIO(data))
    frame.columns = ["date", series_id.lower()]
    frame["date"] = pd.to_datetime(frame["date"])
    frame[series_id.lower()] = pd.to_numeric(
        frame[series_id.lower()], errors="coerce"
    )
    return frame.set_index("date")


def download_fed() -> pd.DataFrame:
    old = fred_csv(FRED_SERIES["target_old"])
    upper = fred_csv(FRED_SERIES["target_upper"])
    lower = fred_csv(FRED_SERIES["target_lower"])
    fed = pd.concat([old, upper, lower], axis=1).sort_index()

    # Before the target became a range, DFEDTAR is the historical target.
    # After the range transition, use the midpoint when both bounds exist.
    fed["target_rate"] = fed["dfedtar"]
    midpoint = (fed["dfedtaru"] + fed["dfedtarl"]) / 2
    fed.loc[midpoint.notna(), "target_rate"] = midpoint[midpoint.notna()]
    fed = fed.loc[START:END].copy()
    fed["target_change"] = fed["target_rate"].diff()

    # Action dates are dates on which the target changed. Small numerical
    # artifacts are ignored with a tight tolerance.
    fed["action"] = np.select(
        [fed["target_change"] > 0.001, fed["target_change"] < -0.001],
        ["HIKE", "CUT"],
        default="HOLD",
    )
    fed["cumulative_hikes"] = fed["target_change"].clip(lower=0).cumsum()
    fed["cumulative_cuts"] = (-fed["target_change"].clip(upper=0)).cumsum()
    fed["net_change_from_start"] = fed["target_rate"] - fed["target_rate"].dropna().iloc[0]
    return fed


def download_market(ticker: str) -> pd.DataFrame:
    frame = yf.download(
        ticker,
        start=START,
        end=END,
        auto_adjust=True,
        progress=False,
        actions=False,
    )
    if frame.empty:
        raise RuntimeError(f"No history returned for {ticker}.")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    close_col = "Close"
    frame = frame.rename(columns={close_col: "close"})
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame[["close"]].dropna().sort_index()


def forward_metrics(series: pd.Series, anchor: pd.Timestamp) -> dict[str, float | str | None]:
    series = series.dropna()
    if anchor not in series.index:
        prior = series.loc[:anchor]
        if prior.empty:
            return {}
        anchor = prior.index[-1]

    start_value = float(series.loc[anchor])
    out: dict[str, float | str | None] = {
        "anchor_date": anchor.date().isoformat(),
        "anchor_value": start_value,
    }

    for months in (3, 6, 12, 18, 24):
        end_date = anchor + pd.DateOffset(months=months)
        window = series.loc[anchor:end_date]
        if window.empty or window.index[-1] < end_date - pd.Timedelta(days=45):
            out[f"return_{months}m"] = np.nan
            out[f"max_dd_{months}m"] = np.nan
            continue
        end_value = float(window.iloc[-1])
        out[f"return_{months}m"] = end_value / start_value - 1.0
        peak = window.cummax()
        out[f"max_dd_{months}m"] = float((window / peak - 1.0).min())

    return out


def cycle_action_dates(fed: pd.DataFrame, start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    window = fed.loc[start:end]
    hikes = window.index[window["action"] == "HIKE"]
    if len(hikes) == 0:
        raise RuntimeError(f"No hikes found in cycle {start} to {end}.")
    return hikes[0], hikes[-1]


def build_cycle_table(fed: pd.DataFrame, ndx: pd.Series, tqqq: pd.Series) -> pd.DataFrame:
    rows = []
    for start, end, label in CYCLES:
        first_hike, final_hike = cycle_action_dates(fed, start, end)
        cycle_window = fed.loc[start:end]
        hike_rows = cycle_window[cycle_window["action"] == "HIKE"]
        cut_rows = cycle_window[cycle_window["action"] == "CUT"]

        for anchor_type, anchor in [("FIRST_HIKE", first_hike), ("FINAL_HIKE", final_hike)]:
            ndx_m = forward_metrics(ndx, anchor)
            tqqq_m = forward_metrics(tqqq, anchor)
            row = {
                "cycle": label,
                "anchor_type": anchor_type,
                "first_hike_date": first_hike.date().isoformat(),
                "final_hike_date": final_hike.date().isoformat(),
                "hike_count": int(len(hike_rows)),
                "cumulative_hikes_pct": float(hike_rows["target_change"].sum()),
                "cut_count_during_cycle": int(len(cut_rows)),
                "target_at_first_hike_pct": float(fed.loc[first_hike, "target_rate"]),
                "target_at_final_hike_pct": float(fed.loc[final_hike, "target_rate"]),
            }
            for k, v in ndx_m.items():
                row[f"ndx_{k}"] = v
            for k, v in tqqq_m.items():
                row[f"tqqq_{k}"] = v
            rows.append(row)
    return pd.DataFrame(rows)


def build_action_timeline(fed: pd.DataFrame) -> pd.DataFrame:
    actions = fed[fed["action"] != "HOLD"].copy()
    return actions.reset_index().rename(columns={"index": "date"})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    fed = download_fed()
    ndx = download_market("^NDX")["close"]
    tqqq = download_market("TQQQ")["close"]

    cycles = build_cycle_table(fed, ndx, tqqq)
    actions = build_action_timeline(fed)

    cycle_summary = []
    for start, end, label in CYCLES:
        first_hike, final_hike = cycle_action_dates(fed, start, end)
        window = fed.loc[start:end]
        hikes = window[window["action"] == "HIKE"]
        cycle_summary.append(
            {
                "cycle": label,
                "first_hike": first_hike.date().isoformat(),
                "final_hike": final_hike.date().isoformat(),
                "hike_count": int(len(hikes)),
                "cumulative_hike_pct": float(hikes["target_change"].sum()),
                "starting_target_pct": float(fed.loc[first_hike, "target_rate"] - fed.loc[first_hike, "target_change"]),
                "final_target_pct": float(fed.loc[final_hike, "target_rate"]),
                "cycle_net_target_change_pct": float(
                    fed.loc[final_hike, "target_rate"]
                    - (fed.loc[first_hike, "target_rate"] - fed.loc[first_hike, "target_change"])
                ),
            }
        )

    fed.reset_index().to_csv(OUT / "fed_action_timeline.csv", index=False)
    actions.to_csv(OUT / "fed_action_dates.csv", index=False)
    pd.DataFrame(cycle_summary).to_csv(OUT / "fed_tightening_cycles.csv", index=False)
    cycles.to_csv(OUT / "fed_cycle_market_event_study.csv", index=False)

    print("\nFED TIGHTENING CYCLES")
    print(pd.DataFrame(cycle_summary).to_string(index=False))
    print("\nMARKET EVENT STUDY")
    print(cycles.to_string(index=False))
    print(f"\nArtifacts written to {OUT}")


if __name__ == "__main__":
    main()
