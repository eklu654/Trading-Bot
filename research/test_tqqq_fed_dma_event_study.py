"""Frozen monetary-policy state x DMA event study.

Descriptive research only. No strategy optimization and no hindsight-defined
"final hike" state. Monetary state is constructed only from information
available through each date, then cross-tabulated with QQQ trend state.

States:
- TIGHTENING_ACTIVE: at least one hike in trailing 90 calendar days.
- TIGHTENING_PAUSED: no recent hike, no recent cut, and the 12-month
  net target-rate change is positive.
- EASING: at least one cut in trailing 90 calendar days OR the 12-month
  net target-rate change is negative.
- NEUTRAL: otherwise.

DMA state:
- ABOVE_DMA when QQQ adjusted close >= its 200-day rolling mean.
- BELOW_DMA otherwise.

The key test is whether monetary state changes forward outcomes after the
market-trend state is already known. It does not claim causality.
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
    fed = fed.loc[START:END].copy()
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


def build_daily_states(fed: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    daily = qqq.copy()
    daily["dma_200"] = daily["close"].rolling(200, min_periods=200).mean()
    qqq_ret = daily["close"].pct_change().fillna(0.0)
    daily["synthetic_tqqq"] = (1.0 + 3.0 * qqq_ret).clip(lower=0.0).cumprod()
    daily["dma_state"] = np.where(
        daily["close"] >= daily["dma_200"], "ABOVE_DMA", "BELOW_DMA"
    )
    daily.loc[daily["dma_200"].isna(), "dma_state"] = "INSUFFICIENT_HISTORY"

    actions = fed[["target_rate", "target_change", "action"]].copy()
    actions["hike_90d"] = (
        actions["action"].eq("HIKE").astype(int).rolling("90D").sum()
    )
    actions["cut_90d"] = (
        actions["action"].eq("CUT").astype(int).rolling("90D").sum()
    )
    # Use an exact calendar-year lookback rather than a fixed number of
    # observations. FRED's target-rate series is not guaranteed to have one
    # row per calendar day, so shift(365) would not mean 12 calendar months.
    lookback_dates = actions.index - pd.DateOffset(years=1)
    positions = actions.index.searchsorted(lookback_dates, side="right") - 1
    past_rates = np.full(len(actions), np.nan, dtype=float)
    valid = positions >= 0
    past_rates[valid] = actions["target_rate"].to_numpy()[positions[valid]]
    actions["net_change_12m"] = actions["target_rate"] - past_rates

    usable = actions.reset_index().rename(columns={"index": "date"})
    base = daily.reset_index().rename(columns={daily.index.name or "Date": "date"})
    base["date"] = pd.to_datetime(base["date"]).dt.tz_localize(None)
    usable["date"] = pd.to_datetime(usable["date"]).dt.tz_localize(None)

    merged = pd.merge_asof(
        base.sort_values("date"),
        usable.sort_values("date"),
        on="date",
        direction="backward",
    ).set_index("date")

    # All monetary fields are lag-free because only information through the
    # current date is used. No final-hike knowledge is introduced.
    merged["monetary_state"] = np.select(
        [
            merged["cut_90d"].fillna(0).gt(0)
            | merged["net_change_12m"].fillna(0).lt(-0.001),
            merged["hike_90d"].fillna(0).gt(0),
            merged["net_change_12m"].fillna(0).gt(0.001),
        ],
        ["EASING", "TIGHTENING_ACTIVE", "TIGHTENING_PAUSED"],
        default="NEUTRAL",
    )
    merged.loc[
        merged["dma_state"].eq("INSUFFICIENT_HISTORY"), "monetary_state"
    ] = "INSUFFICIENT_HISTORY"
    return merged


def forward_return(series: pd.Series, anchor: pd.Timestamp, months: int) -> float:
    target = anchor + pd.DateOffset(months=months)
    window = series.loc[anchor:target]
    if window.empty or window.index[-1] < target - pd.Timedelta(days=45):
        return np.nan
    return float(window.iloc[-1] / window.iloc[0] - 1.0)


def event_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for date, row in frame.iterrows():
        if row["dma_state"] == "INSUFFICIENT_HISTORY":
            continue
        rows.append(
            {
                "date": date.date().isoformat(),
                "monetary_state": row["monetary_state"],
                "dma_state": row["dma_state"],
                "close": float(row["close"]),
                "dma_200": float(row["dma_200"]),
                "return_3m": forward_return(frame["close"], date, 3),
                "return_6m": forward_return(frame["close"], date, 6),
                "return_12m": forward_return(frame["close"], date, 12),
                "synthetic_tqqq_return_3m": forward_return(frame["synthetic_tqqq"], date, 3),
                "synthetic_tqqq_return_6m": forward_return(frame["synthetic_tqqq"], date, 6),
                "synthetic_tqqq_return_12m": forward_return(frame["synthetic_tqqq"], date, 12),
            }
        )
    return pd.DataFrame(rows)


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        events.groupby(["dma_state", "monetary_state"], dropna=False)
        .agg(
            observations=("date", "count"),
            mean_3m=("return_3m", "mean"),
            median_3m=("return_3m", "median"),
            mean_6m=("return_6m", "mean"),
            median_6m=("return_6m", "median"),
            mean_12m=("return_12m", "mean"),
            median_12m=("return_12m", "median"),
            pct_positive_12m=("return_12m", lambda x: float((x > 0).mean())),
            mean_tqqq_12m=("synthetic_tqqq_return_12m", "mean"),
            median_tqqq_12m=("synthetic_tqqq_return_12m", "median"),
            pct_positive_tqqq_12m=("synthetic_tqqq_return_12m", lambda x: float((x > 0).mean())),
        )
        .reset_index()
    )
    return grouped.sort_values(["dma_state", "monetary_state"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fed = download_fed()
    qqq = download_qqq()
    frame = build_daily_states(fed, qqq)
    events = event_table(frame)
    summary = summarize(events)

    frame.to_csv(OUT / "tqqq_fed_dma_daily_states.csv")
    events.to_csv(OUT / "tqqq_fed_dma_event_observations.csv", index=False)
    summary.to_csv(OUT / "tqqq_fed_dma_event_summary.csv", index=False)

    print("\nFED STATE x 200-DMA FORWARD-RETURN SUMMARY")
    print(summary.to_string(index=False))
    print("\nArtifacts written to", OUT)


if __name__ == "__main__":
    main()
