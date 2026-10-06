"""Attribute frozen 100-DMA exit episodes with contemporaneous macro context.

This is a descriptive attribution layer, NOT a strategy optimization.

Frozen market strategy:
- synthetic daily-reset 3x QQQ
- 100-day DMA
- 0% exposure below DMA
- immediate re-entry
- next-open execution

Macro fields are attached to each already-defined exit/re-entry episode:
- Fed target rate immediately before the exit
- cumulative hikes/cuts in the current policy cycle
- days since latest Fed move
- policy-cycle direction
- 2s10s Treasury curve immediately before the exit
- curve slope change over the prior 20 trading days

Fed target changes are taken from the Federal Reserve's historical target-rate
record and encoded explicitly so the episode classification is reproducible.
Treasury yields come from FRED daily CSV endpoints.

Important: this report is descriptive. It must not be used to tune the
100-DMA or to claim that macro variables were known before publication.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "1999-03-10"
END = "2026-10-04"
DMA = 100
INITIAL = 5000.0

# Federal Reserve historical target-rate changes, 1999 onward.
# Each tuple is (date, change in percentage points, resulting target midpoint
# or single target rate). Range targets use their midpoint for numeric analysis.
FED_EVENTS = [
    ("1999-06-30", +0.25, 5.00),
    ("1999-08-24", +0.25, 5.25),
    ("1999-11-16", +0.25, 5.50),
    ("2000-02-02", +0.25, 5.75),
    ("2000-03-21", +0.25, 6.00),
    ("2000-05-16", +0.50, 6.50),
    ("2001-01-03", -0.50, 6.00),
    ("2001-01-31", -0.50, 5.50),
    ("2001-03-20", -0.50, 5.00),
    ("2001-04-18", -0.50, 4.50),
    ("2001-05-15", -0.50, 4.00),
    ("2001-06-27", -0.25, 3.75),
    ("2001-08-21", -0.25, 3.50),
    ("2001-09-17", -0.50, 3.00),
    ("2001-10-02", -0.50, 2.50),
    ("2001-11-06", -0.50, 2.00),
    ("2001-12-11", -0.25, 1.75),
    ("2002-11-06", -0.50, 1.25),
    ("2003-06-25", -0.25, 1.00),
    ("2004-06-30", +0.25, 1.25),
    ("2004-08-10", +0.25, 1.50),
    ("2004-09-21", +0.25, 1.75),
    ("2004-11-10", +0.25, 2.00),
    ("2004-12-14", +0.25, 2.25),
    ("2005-02-02", +0.25, 2.50),
    ("2005-03-22", +0.25, 2.75),
    ("2005-05-03", +0.25, 3.00),
    ("2005-06-30", +0.25, 3.25),
    ("2005-08-09", +0.25, 3.50),
    ("2005-09-20", +0.25, 3.75),
    ("2005-11-01", +0.25, 4.00),
    ("2005-12-13", +0.25, 4.25),
    ("2006-01-31", +0.25, 4.50),
    ("2006-03-28", +0.25, 4.75),
    ("2006-05-10", +0.25, 5.00),
    ("2006-06-29", +0.25, 5.25),
    ("2007-09-18", -0.50, 4.75),
    ("2007-10-31", -0.25, 4.50),
    ("2007-12-11", -0.25, 4.25),
    ("2008-01-22", -0.75, 3.50),
    ("2008-01-30", -0.50, 3.00),
    ("2008-03-18", -0.75, 2.25),
    ("2008-04-30", -0.25, 2.00),
    ("2008-10-08", -0.50, 1.50),
    ("2008-10-29", -0.50, 1.00),
    ("2008-12-16", -0.75, 0.125),
    ("2015-12-17", +0.25, 0.375),
    ("2016-12-15", +0.25, 0.625),
    ("2017-03-16", +0.25, 0.875),
    ("2017-06-15", +0.25, 1.125),
    ("2017-12-14", +0.25, 1.375),
    ("2018-03-22", +0.25, 1.625),
    ("2018-06-14", +0.25, 1.875),
    ("2018-09-27", +0.25, 2.125),
    ("2018-12-20", +0.25, 2.375),
    ("2019-08-01", -0.25, 2.125),
    ("2019-09-19", -0.25, 1.875),
    ("2019-10-31", -0.25, 1.625),
    ("2020-03-04", -0.50, 1.125),
    ("2020-03-16", -1.00, 0.125),
    ("2022-03-17", +0.25, 0.375),
    ("2022-05-05", +0.50, 0.875),
    ("2022-06-16", +0.75, 1.625),
    ("2022-07-28", +0.75, 2.375),
    ("2022-09-22", +0.75, 3.125),
    ("2022-11-03", +0.75, 3.875),
    ("2022-12-15", +0.50, 4.375),
    ("2023-02-02", +0.25, 4.625),
    ("2023-03-23", +0.25, 4.875),
    ("2023-05-04", +0.25, 5.125),
    ("2023-07-27", +0.25, 5.375),
    ("2024-09-19", -0.50, 4.875),
    ("2024-11-08", -0.25, 4.625),
    ("2024-12-19", -0.25, 4.375),
    ("2025-09-18", -0.25, 4.125),
    ("2025-10-30", -0.25, 3.875),
    ("2025-12-11", -0.25, 3.625),
    ("2026-09-17", +0.25, 3.875),
]


def download_qqq() -> pd.DataFrame:
    frame = yf.download(
        "QQQ", start=START, end=END, auto_adjust=False, progress=False, actions=False
    )
    if frame.empty:
        raise RuntimeError("No QQQ history returned.")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(
        columns={"Open": "open", "Close": "close", "Adj Close": "adj_close"}
    )
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    return frame.sort_index().dropna(subset=["open", "close", "adj_close"])


def build_path(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    qqq_ret = out.adj_close.pct_change().fillna(0.0)
    out["adj_open"] = out.open * out.adj_close / out.close
    overnight = (out.adj_open / out.adj_close.shift(1) - 1.0).fillna(0.0)
    intraday = (out.adj_close / out.adj_open - 1.0).fillna(0.0)
    out["overnight_3x"] = np.clip(1.0 + 3.0 * overnight, 0.0, None) - 1.0
    out["intraday_3x"] = np.clip(1.0 + 3.0 * intraday, 0.0, None) - 1.0
    ma = out.adj_close.rolling(DMA).mean()
    active = (out.adj_close >= ma).astype(float)
    active.iloc[: DMA - 1] = 0.0
    w = active.to_numpy()
    prev = np.roll(w, 1)
    prev[0] = 0.0
    daily = (1 + prev * out.overnight_3x.to_numpy()) * (
        1 + w * out.intraday_3x.to_numpy()
    ) - 1
    out["dma"] = ma
    out["weight"] = w
    out["equity"] = INITIAL * np.cumprod(1 + daily)
    bh_daily = (1 + out.overnight_3x) * (1 + out.intraday_3x) - 1
    out["bh_equity"] = INITIAL * np.cumprod(1 + bh_daily)
    out["drawdown"] = out.equity / out.equity.cummax() - 1
    return out


def fred_daily(series: str) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    data = pd.read_csv(StringIO(raw), parse_dates=["DATE"]).set_index("DATE")
    values = pd.to_numeric(data[series], errors="coerce").replace(".", np.nan)
    values.index.name = "Date"
    return values.rename(series)


def fed_context(dates: pd.DatetimeIndex) -> pd.DataFrame:
    events = pd.DataFrame(FED_EVENTS, columns=["date", "change", "target"])
    events.date = pd.to_datetime(events.date)
    events = events.sort_values("date")
    rows = []
    for date in dates:
        prior = events[events.date <= date]
        if prior.empty:
            rows.append({"Date": date, "fed_target": np.nan, "fed_cycle_direction": "unknown",
                         "fed_cycle_net_change": np.nan, "days_since_fed_move": np.nan,
                         "fed_moves_in_cycle": 0})
            continue
        latest = prior.iloc[-1]
        # A cycle is a consecutive run of moves in the same direction.
        signs = np.sign(prior.change.to_numpy())
        current_sign = signs[-1]
        start = len(signs) - 1
        while start > 0 and signs[start - 1] == current_sign:
            start -= 1
        cycle = prior.iloc[start:]
        cycle_peak = float(cycle.target.max())
        cycle_trough = float(cycle.target.min())
        rows.append({
            "Date": date,
            "fed_target": float(latest.target),
            "fed_cycle_direction": "tightening" if current_sign > 0 else "easing",
            "fed_cycle_net_change": float(cycle.change.sum()),
            "days_since_fed_move": int((date - latest.date).days),
            "fed_moves_in_cycle": int(len(cycle)),
            "fed_cycle_peak_target": cycle_peak,
            "fed_cycle_trough_target": cycle_trough,
            "fed_distance_from_cycle_peak": float(latest.target - cycle_peak),
            "fed_distance_from_cycle_trough": float(latest.target - cycle_trough),
        })
    return pd.DataFrame(rows).set_index("Date")


def add_macro(frame: pd.DataFrame) -> pd.DataFrame:
    curve = pd.concat([fred_daily("DGS10"), fred_daily("DGS2")], axis=1)
    curve["curve_2s10s"] = curve.DGS10 - curve.DGS2
    curve["curve_change_20d"] = curve.curve_2s10s - curve.curve_2s10s.shift(20)
    macro = fed_context(frame.index).join(curve[["curve_2s10s", "curve_change_20d"]], how="left")
    macro[["curve_2s10s", "curve_change_20d"]] = macro[["curve_2s10s", "curve_change_20d"]].ffill()
    return frame.join(macro)


def extract_episodes(frame: pd.DataFrame) -> pd.DataFrame:
    exits = frame.index[(frame.weight == 0) & (frame.weight.shift(1) == 1)]
    rows = []
    for exit_date in exits:
        i = frame.index.get_loc(exit_date)
        j = i + 1
        while j < len(frame) and frame.iloc[j].weight == 0:
            j += 1
        if j >= len(frame):
            continue
        reentry = frame.index[j]
        segment = frame.loc[exit_date:reentry]
        base = float(segment.bh_equity.iloc[0])
        rows.append({
            "exit_date": exit_date.date().isoformat(),
            "reentry_date": reentry.date().isoformat(),
            "exit_year": exit_date.year,
            "flat_trading_days": max(j - i - 1, 0),
            "exit_equity": float(frame.loc[exit_date, "equity"]),
            "exit_drawdown": float(frame.loc[exit_date, "drawdown"]),
            "bh_return_to_reentry": float(segment.bh_equity.iloc[-1] / base - 1),
            "bh_worst_return_during_episode": float((segment.bh_equity / base - 1).min()),
            "fed_target_at_exit": float(frame.loc[exit_date, "fed_target"]),
            "fed_cycle_direction": frame.loc[exit_date, "fed_cycle_direction"],
            "fed_cycle_net_change": float(frame.loc[exit_date, "fed_cycle_net_change"]),
            "days_since_fed_move": float(frame.loc[exit_date, "days_since_fed_move"]),
            "fed_moves_in_cycle": int(frame.loc[exit_date, "fed_moves_in_cycle"]),
            "fed_cycle_peak_target": float(frame.loc[exit_date, "fed_cycle_peak_target"]),
            "fed_cycle_trough_target": float(frame.loc[exit_date, "fed_cycle_trough_target"]),
            "fed_distance_from_cycle_peak": float(frame.loc[exit_date, "fed_distance_from_cycle_peak"]),
            "fed_distance_from_cycle_trough": float(frame.loc[exit_date, "fed_distance_from_cycle_trough"]),
            "curve_2s10s_at_exit": float(frame.loc[exit_date, "curve_2s10s"]),
            "curve_change_20d_at_exit": float(frame.loc[exit_date, "curve_change_20d"]),
        })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = add_macro(build_path(download_qqq()))
    ep = extract_episodes(frame)
    ep.to_csv(OUT / "tqqq_100dma_macro_episode_attribution.csv", index=False)

    print("\n100-DMA MACRO EPISODE ATTRIBUTION")
    cols = [
        "exit_date", "reentry_date", "flat_trading_days", "bh_return_to_reentry",
        "fed_target_at_exit", "fed_cycle_direction", "fed_cycle_net_change",
        "days_since_fed_move", "curve_2s10s_at_exit", "curve_change_20d_at_exit",
    ]
    print(ep[cols].to_string(index=False))
    print("\nEPISODE COUNTS BY FED CYCLE")
    print(ep.groupby("fed_cycle_direction").size().to_string())
    print("\nEPISODES WITH NEGATIVE BUY-AND-HOLD RETURN")
    print(float((ep.bh_return_to_reentry < 0).mean()))
    print(f"\nEpisodes analyzed: {len(ep)}")


if __name__ == "__main__":
    main()
