"""Contemporaneous Fed lifecycle x market confirmation event study.

Research-only. No hindsight-defined final-hike state is used.

Monetary states:
- TIGHTENING_ACTIVE: hike in trailing 90 calendar days.
- FRESH_PAUSE: no hike/cut in trailing 90 days, positive 12m net rate change,
  and <=365 days since the most recent hike.
- EXTENDED_PAUSE: same positive-rate-change condition, >365 days since hike.
- EASING: cut in trailing 90 days OR negative 12m net rate change.
- NEUTRAL: otherwise.

Market confirmation:
- QQQ above/below 100-DMA
- QQQ above/below 200-DMA

All state inputs are knowable on the observation date. Forward returns are
measurement only and are never used to define a state.
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


def fred_csv(series_id: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    req = Request(url, headers={"User-Agent": "Trading-Bot-research/1.0"})
    with urlopen(req, timeout=30) as response:
        data = response.read()
    frame = pd.read_csv(BytesIO(data))
    frame.columns = ["date", series_id.lower()]
    frame["date"] = pd.to_datetime(frame["date"])
    frame[series_id.lower()] = pd.to_numeric(frame[series_id.lower()], errors="coerce")
    return frame.set_index("date")


def download_fed() -> pd.DataFrame:
    fed = pd.concat(
        [fred_csv(s) for s in ("DFEDTAR", "DFEDTARU", "DFEDTARL")], axis=1
    ).sort_index()
    fed["target_rate"] = fed["dfedtar"]
    midpoint = (fed["dfedtaru"] + fed["dfedtarl"]) / 2
    fed.loc[midpoint.notna(), "target_rate"] = midpoint[midpoint.notna()]
    fed = fed.loc[START:END].copy()
    fed["target_change"] = fed["target_rate"].diff()
    fed["action"] = np.select(
        [fed["target_change"] > 0.001, fed["target_change"] < -0.001],
        ["HIKE", "CUT"], default="HOLD"
    )
    return fed


def download_qqq() -> pd.DataFrame:
    frame = yf.download(
        "QQQ", start=START, end=END, auto_adjust=True,
        progress=False, actions=False
    )
    if frame.empty:
        raise RuntimeError("No QQQ history returned.")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(columns={"Close": "close"})
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame[["close"]].dropna().sort_index()


def build_states(fed: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    daily = qqq.copy()
    for n in (100, 200):
        daily[f"dma_{n}"] = daily["close"].rolling(n, min_periods=n).mean()
        daily[f"dma_{n}_state"] = np.where(
            daily["close"] >= daily[f"dma_{n}"], "ABOVE", "BELOW"
        )
        daily.loc[daily[f"dma_{n}"].isna(), f"dma_{n}_state"] = "INSUFFICIENT"

    ret = daily["close"].pct_change().fillna(0.0)
    daily["synthetic_tqqq"] = (1.0 + 3.0 * ret).clip(lower=0.0).cumprod()

    a = fed[["target_rate", "action"]].copy()
    a["hike_90d"] = a["action"].eq("HIKE").astype(int).rolling("90D").sum()
    a["cut_90d"] = a["action"].eq("CUT").astype(int).rolling("90D").sum()

    lookback = a.index - pd.DateOffset(years=1)
    pos = a.index.searchsorted(lookback, side="right") - 1
    past = np.full(len(a), np.nan)
    ok = pos >= 0
    past[ok] = a["target_rate"].to_numpy()[pos[ok]]
    a["net_change_12m"] = a["target_rate"] - past

    # Days since most recent hike, using only past/current Fed actions.
    # Forward-filling the hike dates avoids mixing positions in the full
    # daily Fed index with positions in the much shorter hike-date index.
    latest_hike = pd.Series(
        a.index.where(a["action"].eq("HIKE")),
        index=a.index,
        dtype="datetime64[ns]",
    ).ffill()
    a["days_since_hike"] = (a.index - latest_hike).dt.days

    usable = a.reset_index().rename(columns={"index": "date"})
    base = daily.reset_index().rename(columns={daily.index.name or "Date": "date"})
    base["date"] = pd.to_datetime(base["date"]).dt.tz_localize(None)
    usable["date"] = pd.to_datetime(usable["date"]).dt.tz_localize(None)

    merged = pd.merge_asof(
        base.sort_values("date"), usable.sort_values("date"),
        on="date", direction="backward"
    ).set_index("date")

    merged["monetary_state"] = np.select(
        [
            merged["cut_90d"].fillna(0).gt(0)
            | merged["net_change_12m"].fillna(0).lt(-0.001),
            merged["hike_90d"].fillna(0).gt(0),
            merged["net_change_12m"].fillna(0).gt(0.001)
            & merged["days_since_hike"].fillna(99999).le(365),
            merged["net_change_12m"].fillna(0).gt(0.001)
            & merged["days_since_hike"].fillna(99999).gt(365),
        ],
        ["EASING", "TIGHTENING_ACTIVE", "FRESH_PAUSE", "EXTENDED_PAUSE"],
        default="NEUTRAL",
    )
    merged.loc[
        merged["dma_200_state"].eq("INSUFFICIENT"), "monetary_state"
    ] = "INSUFFICIENT"
    return merged


def forward_metrics(series: pd.Series, anchor: pd.Timestamp, months: int) -> tuple[float, float]:
    target = anchor + pd.DateOffset(months=months)
    w = series.loc[anchor:target]
    if w.empty or w.index[-1] < target - pd.Timedelta(days=45):
        return np.nan, np.nan
    r = float(w.iloc[-1] / w.iloc[0] - 1.0)
    dd = float((w / w.cummax() - 1.0).min())
    return r, dd


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build_states(download_fed(), download_qqq())

    rows = []
    for date, row in frame.iterrows():
        if row["dma_200_state"] == "INSUFFICIENT":
            continue
        for dma in (100, 200):
            dma_state = row[f"dma_{dma}_state"]
            for months in (3, 6, 12):
                qret, qdd = forward_metrics(frame["close"], date, months)
                tret, tdd = forward_metrics(frame["synthetic_tqqq"], date, months)
                rows.append({
                    "date": date.date().isoformat(),
                    "monetary_state": row["monetary_state"],
                    "dma": dma,
                    "dma_state": dma_state,
                    "target_rate": float(row["target_rate"]),
                    "days_since_hike": float(row["days_since_hike"]) if pd.notna(row["days_since_hike"]) else np.nan,
                    "horizon_months": months,
                    "qqq_forward_return": qret,
                    "qqq_forward_max_dd": qdd,
                    "synthetic_tqqq_forward_return": tret,
                    "synthetic_tqqq_forward_max_dd": tdd,
                })

    events = pd.DataFrame(rows)
    summary = (
        events.groupby(["dma", "dma_state", "monetary_state", "horizon_months"])
        .agg(
            observations=("date", "count"),
            mean_qqq_return=("qqq_forward_return", "mean"),
            median_qqq_return=("qqq_forward_return", "median"),
            pct_positive_qqq=("qqq_forward_return", lambda x: float((x > 0).mean())),
            mean_qqq_max_dd=("qqq_forward_max_dd", "mean"),
            mean_tqqq_return=("synthetic_tqqq_forward_return", "mean"),
            median_tqqq_return=("synthetic_tqqq_forward_return", "median"),
            pct_positive_tqqq=("synthetic_tqqq_forward_return", lambda x: float((x > 0).mean())),
            mean_tqqq_max_dd=("synthetic_tqqq_forward_max_dd", "mean"),
        )
        .reset_index()
        .sort_values(["dma", "horizon_months", "dma_state", "monetary_state"])
    )

    frame.to_csv(OUT / "tqqq_fed_lifecycle_confirmation_daily_states.csv")
    events.to_csv(OUT / "tqqq_fed_lifecycle_confirmation_events.csv", index=False)
    summary.to_csv(OUT / "tqqq_fed_lifecycle_confirmation_summary.csv", index=False)

    print("\nFED LIFECYCLE x DMA CONFIRMATION")
    print(summary.to_string(index=False))
    print(f"\nArtifacts written to {OUT}")


if __name__ == "__main__":
    main()
