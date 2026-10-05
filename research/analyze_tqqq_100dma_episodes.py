"""Episode attribution for the frozen 100-DMA synthetic-TQQQ defense.

This is deliberately descriptive, not an optimization search. It freezes:
- QQQ adjusted-close signal
- 100-day DMA
- 0% exposure below the DMA
- immediate re-entry
- next-open execution
- $5,000 initial capital
- synthetic daily-reset 3x QQQ proxy

For each exit/re-entry episode, the report measures:
- duration out of market
- synthetic buy-and-hold return during the defensive interval
- worst interim buy-and-hold loss
- best interim rebound
- calendar-era classification

It also creates a compact crisis-era comparison for 2000-2003, 2008-2009,
2020, and 2022. This test does not use macro data and does not tune any
thresholds; it is intended to establish the price-action anatomy before
adding Fed/macro context.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "1999-03-10"
END = "2026-10-04"
DMA = 100


def download_qqq() -> pd.DataFrame:
    frame = yf.download(
        "QQQ",
        start=START,
        end=END,
        auto_adjust=False,
        progress=False,
        actions=False,
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
    frame = frame.sort_index().dropna(subset=["close", "adj_close"])
    return frame


def build_synthetic(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    qqq_ret = out["adj_close"].pct_change().fillna(0.0)
    growth = (1.0 + 3.0 * qqq_ret).clip(lower=0.0)
    out["synthetic_close"] = INITIAL * growth.cumprod()

    out["adj_open"] = out["open"] * out["adj_close"] / out["close"]
    overnight = (out["adj_open"] / out["adj_close"].shift(1) - 1.0).fillna(0.0)
    intraday = (out["adj_close"] / out["adj_open"] - 1.0).fillna(0.0)
    out["overnight_3x"] = np.clip(1.0 + 3.0 * overnight, 0.0, None) - 1.0
    out["intraday_3x"] = np.clip(1.0 + 3.0 * intraday, 0.0, None) - 1.0
    return out


def make_100dma_path(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    ma = out["adj_close"].rolling(DMA).mean()
    active = out["adj_close"] >= ma
    active.iloc[: DMA - 1] = False
    weights = active.astype(float).to_numpy()

    prev_w = np.roll(weights, 1)
    prev_w[0] = 0.0
    daily = (
        (1.0 + prev_w * out["overnight_3x"].to_numpy())
        * (1.0 + weights * out["intraday_3x"].to_numpy())
        - 1.0
    )
    equity = INITIAL * np.cumprod(1.0 + daily)

    bh_daily = (
        (1.0 + out["overnight_3x"].to_numpy())
        * (1.0 + out["intraday_3x"].to_numpy())
        - 1.0
    )
    bh_equity = INITIAL * np.cumprod(1.0 + bh_daily)

    out["dma"] = ma
    out["weight"] = weights
    out["equity"] = equity
    out["bh_equity"] = bh_equity
    out["drawdown"] = equity / np.maximum.accumulate(equity) - 1.0
    return out


def era(year: int) -> str:
    if 2000 <= year <= 2003:
        return "dotcom_2000_2003"
    if 2008 <= year <= 2009:
        return "gfc_2008_2009"
    if year == 2020:
        return "covid_2020"
    if year == 2022:
        return "inflation_2022"
    if year < 2000:
        return "pre_dotcom"
    if 2004 <= year <= 2007:
        return "2004_2007"
    if 2010 <= year <= 2019:
        return "2010_2019"
    return "2021_2026"


def episodes(frame: pd.DataFrame) -> pd.DataFrame:
    exits = frame.index[(frame["weight"] == 0) & (frame["weight"].shift(1) == 1)]
    rows: list[dict[str, object]] = []

    for exit_date in exits:
        i = frame.index.get_loc(exit_date)
        j = i + 1
        while j < len(frame) and frame.iloc[j]["weight"] == 0:
            j += 1
        if j >= len(frame):
            continue

        reentry_date = frame.index[j]
        segment = frame.loc[exit_date:reentry_date, "bh_equity"]
        base = float(segment.iloc[0])
        rel = segment / base - 1.0

        rows.append(
            {
                "exit_date": exit_date.date().isoformat(),
                "reentry_date": reentry_date.date().isoformat(),
                "exit_year": exit_date.year,
                "era": era(exit_date.year),
                "flat_trading_days": max(j - i - 1, 0),
                "exit_equity": float(frame.loc[exit_date, "equity"]),
                "exit_drawdown": float(frame.loc[exit_date, "drawdown"]),
                "bh_return_to_reentry": float(frame.loc[reentry_date, "bh_equity"] / base - 1.0),
                "bh_worst_return_during_episode": float(rel.min()),
                "bh_best_return_during_episode": float(rel.max()),
                "defensive_value_added": float(
                    -(frame.loc[reentry_date, "bh_equity"] / base - 1.0)
                ),
            }
        )

    return pd.DataFrame(rows)


def summarize(ep: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, group in ep.groupby("era", sort=False):
        rows.append(
            {
                "era": label,
                "episodes": len(group),
                "median_flat_days": float(group.flat_trading_days.median()),
                "median_bh_return_to_reentry": float(group.bh_return_to_reentry.median()),
                "mean_bh_return_to_reentry": float(group.bh_return_to_reentry.mean()),
                "negative_bh_return_rate": float((group.bh_return_to_reentry < 0).mean()),
                "median_worst_interim_return": float(
                    group.bh_worst_return_during_episode.median()
                ),
                "max_defensive_loss_avoided": float(group.defensive_value_added.max()),
            }
        )
    return pd.DataFrame(rows)


def crisis_windows(frame: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("dotcom_2000_2003", "2000-01-01", "2003-12-31"),
        ("gfc_2008_2009", "2008-01-01", "2009-12-31"),
        ("covid_2020", "2020-01-01", "2020-12-31"),
        ("inflation_2022", "2022-01-01", "2022-12-31"),
    ]
    rows = []
    for label, start, end in specs:
        x = frame.loc[start:end]
        if x.empty:
            continue
        rows.append(
            {
                "window": label,
                "start": x.index[0].date().isoformat(),
                "end": x.index[-1].date().isoformat(),
                "bh_start": float(x.bh_equity.iloc[0]),
                "bh_end": float(x.bh_equity.iloc[-1]),
                "bh_window_return": float(x.bh_equity.iloc[-1] / x.bh_equity.iloc[0] - 1.0),
                "dma_start": float(x.equity.iloc[0]),
                "dma_end": float(x.equity.iloc[-1]),
                "dma_window_return": float(x.equity.iloc[-1] / x.equity.iloc[0] - 1.0),
                "dma_min_drawdown": float(x.drawdown.min()),
                "defensive_days": int((x.weight == 0).sum()),
                "defensive_pct": float((x.weight == 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = make_100dma_path(build_synthetic(download_qqq()))
    ep = episodes(frame)
    summary = summarize(ep)
    crisis = crisis_windows(frame)

    ep.to_csv(OUT / "tqqq_100dma_episode_attribution.csv", index=False)
    summary.to_csv(OUT / "tqqq_100dma_episode_attribution_summary.csv", index=False)
    crisis.to_csv(OUT / "tqqq_100dma_episode_crisis_windows.csv", index=False)

    print("\n100-DMA EPISODE ATTRIBUTION")
    print(summary.to_string(index=False))
    print("\nCRISIS WINDOWS")
    print(crisis.to_string(index=False))
    print("\nMOST BENEFICIAL DEFENSIVE EPISODES")
    print(
        ep.sort_values("defensive_value_added", ascending=False)
        .head(15)
        .to_string(index=False)
    )
    print(f"\nEpisodes analyzed: {len(ep)}")


if __name__ == "__main__":
    main()
