"""Fed tightening-cycle lifecycle x QQQ 200-DMA event study.

Descriptive research only. This study uses completed tightening-cycle dates
retrospectively to understand the lifecycle of monetary restriction. It is NOT
a live trading signal and never uses a future final-hike label in a simulated
strategy.

Lifecycle phases:
- PRE_TIGHTENING: 365 calendar days before the first hike.
- EARLY_TIGHTENING: first 90 days beginning on the first hike.
- MATURE_TIGHTENING: after day 90 through the final hike.
- POST_FINAL_HIKE_LAG: first 365 days after the final hike.
- RESTRICTIVE_PAUSE: after that 365-day lag through the first cut, if any.
- BENIGN_EASING / CRISIS_EASING: first 365 days after the first cut, split
  retrospectively according to whether an NBER recession begins within the
  following 12 months.

Each lifecycle phase is crossed with QQQ 200-DMA state:
- ABOVE_DMA
- BELOW_DMA

Synthetic TQQQ is used for the full historical period because actual TQQQ did
not exist during the dot-com cycle. It is a descriptive 3x daily-reset proxy.
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
START = "1999-03-10"
END = "2026-10-04"

FRED_SERIES = {
    "target_old": "DFEDTAR",
    "target_upper": "DFEDTARU",
    "target_lower": "DFEDTARL",
}

CYCLES = [
    ("1999-06-01", "2000-07-31", "1999-2000"),
    ("2004-06-01", "2006-08-31", "2004-06"),
    ("2015-12-01", "2019-01-31", "2015-18"),
    ("2022-03-01", "2024-01-31", "2022-23"),
]

RECESSION_STARTS = pd.to_datetime([
    "2001-03-01",
    "2007-12-01",
    "2020-02-01",
])


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
    fed = pd.concat(
        [fred_csv(series_id) for series_id in FRED_SERIES.values()],
        axis=1,
    ).sort_index()
    fed["target_rate"] = fed["dfedtar"]
    midpoint = (fed["dfedtaru"] + fed["dfedtarl"]) / 2
    fed.loc[midpoint.notna(), "target_rate"] = midpoint[midpoint.notna()]
    fed = fed.loc["1994-01-01":END].copy()
    fed["target_change"] = fed["target_rate"].diff()
    fed["action"] = np.select(
        [fed["target_change"] > 0.001, fed["target_change"] < -0.001],
        ["HIKE", "CUT"],
        default="HOLD",
    )
    return fed


def download_qqq() -> pd.DataFrame:
    frame = yf.download(
        "QQQ",
        start=START,
        end=END,
        auto_adjust=True,
        progress=False,
        actions=False,
    )
    if frame.empty:
        raise RuntimeError("No QQQ history returned.")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(columns={"Close": "close"})
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame[["close"]].dropna().sort_index()


def cycle_dates(
    fed: pd.DataFrame, start: str, end: str
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp | None]:
    window = fed.loc[start:end]
    hikes = window.index[window["action"].eq("HIKE")]
    cuts = window.index[window["action"].eq("CUT")]
    if len(hikes) == 0:
        raise RuntimeError(f"No hikes found for {start} to {end}.")
    first_hike = hikes[0]
    final_hike = hikes[-1]
    later_cuts = cuts[cuts > final_hike]
    first_cut = later_cuts[0] if len(later_cuts) else None
    return first_hike, final_hike, first_cut


def easing_type(first_cut: pd.Timestamp | None) -> str | None:
    if first_cut is None:
        return None
    horizon = first_cut + pd.DateOffset(months=12)
    # Treat easing as crisis-oriented only when a recession begins soon after
    # the cut. A recession many months later can be an unrelated shock (for
    # example, the COVID recession after the 2019 precautionary cuts).
    crisis = any(
        (start >= first_cut)
        and (start <= horizon)
        and ((start - first_cut).days <= 180)
        for start in RECESSION_STARTS
    )
    return "CRISIS_EASING" if crisis else "BENIGN_EASING"


def phase_for_date(
    date: pd.Timestamp,
    first_hike: pd.Timestamp,
    final_hike: pd.Timestamp,
    first_cut: pd.Timestamp | None,
) -> str | None:
    if first_hike - pd.DateOffset(days=365) <= date < first_hike:
        return "PRE_TIGHTENING"

    if first_hike <= date <= first_hike + pd.DateOffset(days=90):
        return "EARLY_TIGHTENING"

    if first_hike + pd.DateOffset(days=91) <= date <= final_hike:
        return "MATURE_TIGHTENING"

    lag_end = final_hike + pd.DateOffset(days=365)
    if final_hike < date <= lag_end:
        return "POST_FINAL_HIKE_LAG"

    if first_cut is not None:
        if lag_end < date < first_cut:
            return "RESTRICTIVE_PAUSE"

        easing_end = first_cut + pd.DateOffset(days=365)
        if first_cut <= date <= easing_end:
            return easing_type(first_cut)

    return None


def build_daily_states(
    fed: pd.DataFrame,
    qqq: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    daily = qqq.copy()
    daily["dma_200"] = daily["close"].rolling(200, min_periods=200).mean()
    qqq_ret = daily["close"].pct_change().fillna(0.0)
    daily["synthetic_tqqq"] = (
        1.0 + 3.0 * qqq_ret
    ).clip(lower=0.0).cumprod()
    daily["dma_state"] = np.where(
        daily["close"] >= daily["dma_200"],
        "ABOVE_DMA",
        "BELOW_DMA",
    )
    daily.loc[daily["dma_200"].isna(), "dma_state"] = "INSUFFICIENT_HISTORY"

    cycle_rows: list[dict[str, object]] = []
    phase_values = pd.Series(index=daily.index, dtype="object")
    phase_cycle = pd.Series(index=daily.index, dtype="object")

    for start, end, label in CYCLES:
        first_hike, final_hike, first_cut = cycle_dates(fed, start, end)
        phase_label = easing_type(first_cut)

        cycle_rows.append({
            "cycle": label,
            "first_hike": first_hike.date().isoformat(),
            "final_hike": final_hike.date().isoformat(),
            "first_cut_after_cycle": (
                first_cut.date().isoformat() if first_cut is not None else None
            ),
            "hike_count": int(fed.loc[start:end, "action"].eq("HIKE").sum()),
            "cumulative_hike_pct": float(
                fed.loc[start:end, "target_change"]
                .where(fed.loc[start:end, "action"].eq("HIKE"))
                .sum()
            ),
            "easing_classification": phase_label,
        })

        eligible_start = first_hike - pd.DateOffset(days=365)
        eligible_end = (
            first_cut + pd.DateOffset(days=365)
            if first_cut is not None
            else final_hike + pd.DateOffset(days=365)
        )
        for date in daily.index:
            if date < eligible_start or date > eligible_end:
                continue
            phase = phase_for_date(date, first_hike, final_hike, first_cut)
            if phase is not None and pd.isna(phase_values.loc[date]):
                phase_values.loc[date] = phase
                phase_cycle.loc[date] = label

    daily["lifecycle_phase"] = phase_values
    daily["cycle"] = phase_cycle
    return daily, pd.DataFrame(cycle_rows)


def forward_return(series: pd.Series, anchor: pd.Timestamp, months: int) -> float:
    target = anchor + pd.DateOffset(months=months)
    window = series.loc[anchor:target]
    if window.empty or window.index[-1] < target - pd.Timedelta(days=45):
        return np.nan
    return float(window.iloc[-1] / window.iloc[0] - 1.0)


def build_events(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = frame[
        frame["lifecycle_phase"].notna()
        & frame["dma_state"].isin(["ABOVE_DMA", "BELOW_DMA"])
    ]
    for date, row in usable.iterrows():
        rows.append({
            "date": date.date().isoformat(),
            "cycle": row["cycle"],
            "lifecycle_phase": row["lifecycle_phase"],
            "dma_state": row["dma_state"],
            "close": float(row["close"]),
            "dma_200": float(row["dma_200"]),
            "return_3m": forward_return(frame["close"], date, 3),
            "return_6m": forward_return(frame["close"], date, 6),
            "return_12m": forward_return(frame["close"], date, 12),
            "synthetic_tqqq_return_3m": forward_return(
                frame["synthetic_tqqq"], date, 3
            ),
            "synthetic_tqqq_return_6m": forward_return(
                frame["synthetic_tqqq"], date, 6
            ),
            "synthetic_tqqq_return_12m": forward_return(
                frame["synthetic_tqqq"], date, 12
            ),
        })
    return pd.DataFrame(rows)


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    summary = (
        events.groupby(["lifecycle_phase", "dma_state"], dropna=False)
        .agg(
            observations=("date", "count"),
            cycles=("cycle", "nunique"),
            mean_3m=("return_3m", "mean"),
            median_3m=("return_3m", "median"),
            mean_6m=("return_6m", "mean"),
            median_6m=("return_6m", "median"),
            mean_12m=("return_12m", "mean"),
            median_12m=("return_12m", "median"),
            pct_positive_12m=("return_12m", lambda x: float((x > 0).mean())),
            mean_tqqq_12m=("synthetic_tqqq_return_12m", "mean"),
            median_tqqq_12m=("synthetic_tqqq_return_12m", "median"),
            pct_positive_tqqq_12m=(
                "synthetic_tqqq_return_12m",
                lambda x: float((x > 0).mean()),
            ),
        )
        .reset_index()
    )
    return summary.sort_values(["lifecycle_phase", "dma_state"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fed = download_fed()
    qqq = download_qqq()
    daily, cycles = build_daily_states(fed, qqq)
    events = build_events(daily)
    summary = summarize(events)

    daily.to_csv(OUT / "tqqq_fed_lifecycle_daily_states.csv")
    cycles.to_csv(OUT / "tqqq_fed_lifecycle_cycles.csv", index=False)
    events.to_csv(OUT / "tqqq_fed_lifecycle_event_observations.csv", index=False)
    summary.to_csv(OUT / "tqqq_fed_lifecycle_event_summary.csv", index=False)

    print("\nFED TIGHTENING-CYCLE LIFECYCLE")
    print(cycles.to_string(index=False))
    print("\nLIFECYCLE x 200-DMA SUMMARY")
    print(summary.to_string(index=False))
    print(f"\nArtifacts written to {OUT}")


if __name__ == "__main__":
    main()
