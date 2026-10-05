"""Episode-level test of the live-safe Fed lifecycle x DMA signal.

Counts each contiguous signal episode once instead of treating every daily
observation as independent. This is a validation layer for the prior
descriptive study, not parameter optimization.

Signals tested:
- FRESH_PAUSE + QQQ below 100/200 DMA
- FRESH_PAUSE + QQQ above 100/200 DMA
- TIGHTENING_ACTIVE + QQQ below 100/200 DMA
- DMA-only below controls

Forward horizons: 3, 6, 12 months.
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
START, END = "1999-03-10", "2026-10-04"


def fred_csv(series_id: str) -> pd.DataFrame:
    req = Request(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
        headers={"User-Agent": "Trading-Bot-research/1.0"},
    )
    with urlopen(req, timeout=30) as response:
        frame = pd.read_csv(BytesIO(response.read()))
    frame.columns = ["date", series_id.lower()]
    frame["date"] = pd.to_datetime(frame["date"])
    frame[series_id.lower()] = pd.to_numeric(frame[series_id.lower()], errors="coerce")
    return frame.set_index("date")


def load_frame() -> pd.DataFrame:
    fed = pd.concat([fred_csv(s) for s in ("DFEDTAR", "DFEDTARU", "DFEDTARL")], axis=1).sort_index()
    fed["target_rate"] = fed["dfedtar"]
    mid = (fed["dfedtaru"] + fed["dfedtarl"]) / 2
    fed.loc[mid.notna(), "target_rate"] = mid[mid.notna()]
    fed = fed.loc[START:END].copy()
    fed["target_change"] = fed["target_rate"].diff()
    fed["action"] = np.select(
        [fed["target_change"] > .001, fed["target_change"] < -.001],
        ["HIKE", "CUT"], default="HOLD"
    )
    fed["hike_90d"] = fed["action"].eq("HIKE").astype(int).rolling("90D").sum()
    fed["cut_90d"] = fed["action"].eq("CUT").astype(int).rolling("90D").sum()
    lookback = fed.index - pd.DateOffset(years=1)
    pos = fed.index.searchsorted(lookback, side="right") - 1
    past = np.full(len(fed), np.nan)
    ok = pos >= 0
    past[ok] = fed["target_rate"].to_numpy()[pos[ok]]
    fed["net_change_12m"] = fed["target_rate"] - past
    latest_hike = pd.Series(
        fed.index.where(fed["action"].eq("HIKE")), index=fed.index,
        dtype="datetime64[ns]"
    ).ffill()
    fed["days_since_hike"] = (fed.index - latest_hike).dt.days

    q = yf.download("QQQ", start=START, end=END, auto_adjust=True, progress=False, actions=False)
    if isinstance(q.columns, pd.MultiIndex):
        q.columns = q.columns.get_level_values(0)
    q = q.rename(columns={"Close": "close"})
    q.index = pd.to_datetime(q.index).tz_localize(None)
    q = q[["close"]].dropna().sort_index()
    for n in (100, 200):
        q[f"dma_{n}"] = q.close.rolling(n, min_periods=n).mean()
        q[f"dma_{n}_state"] = np.where(q.close >= q[f"dma_{n}"], "ABOVE", "BELOW")
        q.loc[q[f"dma_{n}"].isna(), f"dma_{n}_state"] = "INSUFFICIENT"
    q["synthetic_tqqq"] = (1 + 3*q.close.pct_change().fillna(0)).clip(lower=0).cumprod()

    a = fed.reset_index().rename(columns={"index":"date"})
    b = q.reset_index().rename(columns={q.index.name or "Date":"date"})
    a.date = pd.to_datetime(a.date).dt.tz_localize(None)
    b.date = pd.to_datetime(b.date).dt.tz_localize(None)
    m = pd.merge_asof(b.sort_values("date"), a.sort_values("date"), on="date", direction="backward").set_index("date")
    m["monetary_state"] = np.select(
        [
            m.cut_90d.fillna(0).gt(0) | m.net_change_12m.fillna(0).lt(-.001),
            m.hike_90d.fillna(0).gt(0),
            m.net_change_12m.fillna(0).gt(.001) & m.days_since_hike.fillna(99999).le(365),
            m.net_change_12m.fillna(0).gt(.001) & m.days_since_hike.fillna(99999).gt(365),
        ],
        ["EASING","TIGHTENING_ACTIVE","FRESH_PAUSE","EXTENDED_PAUSE"], default="NEUTRAL"
    )
    m.loc[m.dma_200_state.eq("INSUFFICIENT"), "monetary_state"] = "INSUFFICIENT"
    return m


def forward(series: pd.Series, anchor: pd.Timestamp, months: int) -> tuple[float,float]:
    target = anchor + pd.DateOffset(months=months)
    w = series.loc[anchor:target]
    if w.empty or w.index[-1] < target - pd.Timedelta(days=45):
        return np.nan, np.nan
    return float(w.iloc[-1]/w.iloc[0]-1), float((w/w.cummax()-1).min())


def first_days_in_episode(mask: pd.Series) -> list[pd.Timestamp]:
    mask = mask.fillna(False)
    starts = mask & ~mask.shift(1, fill_value=False)
    return list(mask.index[starts])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f = load_frame()
    rows = []
    signal_defs = []
    for dma in (100, 200):
        signal_defs += [
            (f"FRESH_PAUSE_BELOW_{dma}", (f.monetary_state=="FRESH_PAUSE") & (f[f"dma_{dma}_state"]=="BELOW")),
            (f"FRESH_PAUSE_ABOVE_{dma}", (f.monetary_state=="FRESH_PAUSE") & (f[f"dma_{dma}_state"]=="ABOVE")),
            (f"TIGHTENING_BELOW_{dma}", (f.monetary_state=="TIGHTENING_ACTIVE") & (f[f"dma_{dma}_state"]=="BELOW")),
            (f"DMA_ONLY_BELOW_{dma}", f[f"dma_{dma}_state"]=="BELOW"),
        ]
    for name, mask in signal_defs:
        for anchor in first_days_in_episode(mask):
            r = f.loc[anchor]
            for months in (3,6,12):
                qr, qdd = forward(f.close, anchor, months)
                tr, tdd = forward(f.synthetic_tqqq, anchor, months)
                rows.append({
                    "signal": name, "date": anchor.date().isoformat(),
                    "target_rate": float(r.target_rate), "days_since_hike": float(r.days_since_hike) if pd.notna(r.days_since_hike) else np.nan,
                    "horizon_months": months, "qqq_forward_return": qr,
                    "qqq_forward_max_dd": qdd, "synthetic_tqqq_forward_return": tr,
                    "synthetic_tqqq_forward_max_dd": tdd,
                })
    events = pd.DataFrame(rows)
    summary = events.groupby(["signal","horizon_months"]).agg(
        episodes=("date","count"),
        mean_qqq_return=("qqq_forward_return","mean"),
        median_qqq_return=("qqq_forward_return","median"),
        pct_positive_qqq=("qqq_forward_return",lambda x: float((x>0).mean())),
        mean_qqq_max_dd=("qqq_forward_max_dd","mean"),
        mean_tqqq_return=("synthetic_tqqq_forward_return","mean"),
        median_tqqq_return=("synthetic_tqqq_forward_return","median"),
        pct_positive_tqqq=("synthetic_tqqq_forward_return",lambda x: float((x>0).mean())),
        mean_tqqq_max_dd=("synthetic_tqqq_forward_max_dd","mean"),
    ).reset_index()
    events.to_csv(OUT/"tqqq_fed_lifecycle_episode_events.csv", index=False)
    summary.to_csv(OUT/"tqqq_fed_lifecycle_episode_summary.csv", index=False)
    print("\nEPISODE-LEVEL FED LIFECYCLE x DMA TEST")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
