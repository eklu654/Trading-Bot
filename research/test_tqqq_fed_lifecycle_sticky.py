"""Backtest a live-safe sticky Fed-lifecycle defense for synthetic TQQQ.

Trigger: after a fresh Fed pause is established, if QQQ is below its 200 DMA,
enter partial defense. Once armed, remain at the chosen defensive exposure until
QQQ closes back above its 200 DMA. Exposure is applied to the NEXT trading day,
avoiding same-close lookahead.

Controls:
- Buy & hold synthetic TQQQ.
- 200 DMA-only sticky defense with the same exposure levels.

The Fed trigger is not allowed to use final-hike knowledge.
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
EXPOSURES = (0.0, 0.25, 0.50, 0.75)


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


def load_data() -> pd.DataFrame:
    fed = pd.concat(
        [fred_csv(s) for s in ("DFEDTAR", "DFEDTARU", "DFEDTARL")], axis=1
    ).sort_index()
    fed["target_rate"] = fed["dfedtar"]
    mid = (fed["dfedtaru"] + fed["dfedtarL"]) / 2 if "dfedtarL" in fed else np.nan
    # Column names are lower-cased by fred_csv.
    mid = (fed["dfedtaru"] + fed["dfedtarl"]) / 2
    fed.loc[mid.notna(), "target_rate"] = mid[mid.notna()]
    fed = fed.loc[START:END].copy()
    fed["target_change"] = fed["target_rate"].diff()
    fed["action"] = np.select(
        [fed["target_change"] > 0.001, fed["target_change"] < -0.001],
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
        fed.index.where(fed["action"].eq("HIKE")),
        index=fed.index, dtype="datetime64[ns]"
    ).ffill()
    fed["days_since_hike"] = (fed.index - latest_hike).dt.days

    q = yf.download(
        "QQQ", start=START, end=END, auto_adjust=True,
        progress=False, actions=False
    )
    if isinstance(q.columns, pd.MultiIndex):
        q.columns = q.columns.get_level_values(0)
    q = q.rename(columns={"Close": "qqq_close"})
    q.index = pd.to_datetime(q.index).tz_localize(None)
    q = q[["qqq_close"]].dropna().sort_index()
    q["dma_200"] = q.qqq_close.rolling(200, min_periods=200).mean()
    q["dma_below"] = q.qqq_close < q.dma_200
    q["qqq_ret"] = q.qqq_close.pct_change().fillna(0.0)
    q["synthetic_tqqq_ret"] = (1.0 + 3.0 * q.qqq_ret).clip(lower=0.0) - 1.0

    a = fed.reset_index().rename(columns={"index": "date"})
    b = q.reset_index().rename(columns={q.index.name or "Date": "date"})
    a.date = pd.to_datetime(a.date).dt.tz_localize(None)
    b.date = pd.to_datetime(b.date).dt.tz_localize(None)
    f = pd.merge_asof(
        b.sort_values("date"), a.sort_values("date"),
        on="date", direction="backward"
    ).set_index("date")

    f["monetary_state"] = np.select(
        [
            f.cut_90d.fillna(0).gt(0) | f.net_change_12m.fillna(0).lt(-0.001),
            f.hike_90d.fillna(0).gt(0),
            f.net_change_12m.fillna(0).gt(0.001)
            & f.days_since_hike.fillna(99999).le(365),
            f.net_change_12m.fillna(0).gt(0.001)
            & f.days_since_hike.fillna(99999).gt(365),
        ],
        ["EASING", "TIGHTENING_ACTIVE", "FRESH_PAUSE", "EXTENDED_PAUSE"],
        default="NEUTRAL",
    )
    f.loc[f.dma_200.isna(), "monetary_state"] = "INSUFFICIENT"
    return f


def run_sticky(f: pd.DataFrame, defensive_exposure: float, fed_trigger: bool) -> tuple[pd.DataFrame, dict]:
    armed = False
    exposures = []
    triggers = []
    exits = []
    for _, r in f.iterrows():
        trigger = (
            (r.monetary_state == "FRESH_PAUSE" and bool(r.dma_below))
            if fed_trigger else bool(r.dma_below)
        )
        exit_signal = not bool(r.dma_below) if pd.notna(r.dma_200) else False
        if not armed and trigger:
            armed = True
            triggers.append(r.name)
        elif armed and exit_signal:
            armed = False
            exits.append(r.name)
        exposures.append(defensive_exposure if armed else 1.0)
    # Signals are known at today's close; apply tomorrow.
    exposure = pd.Series(exposures, index=f.index, dtype=float).shift(1).fillna(1.0)
    equity = (1.0 + exposure * f.synthetic_tqqq_ret).cumprod()
    dd = equity / equity.cummax() - 1.0
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0
    result = f.copy()
    result["exposure"] = exposure
    result["equity"] = equity
    result["drawdown"] = dd
    result["triggered_today"] = False
    result.loc[pd.DatetimeIndex(triggers), "triggered_today"] = True
    result["exited_today"] = False
    if exits:
        result.loc[pd.DatetimeIndex(exits), "exited_today"] = True
    metrics = {
        "final_balance_multiple": float(equity.iloc[-1]),
        "cagr": float(cagr),
        "max_drawdown": float(dd.min()),
        "days_defensive": int((exposure < 1.0).sum()),
        "defensive_fraction": float((exposure < 1.0).mean()),
        "trigger_count": len(triggers),
        "exit_count": len(exits),
    }
    for year_end, label in [
        ("2009-12-31", "pre_2010"),
        ("2019-12-31", "2010_2019"),
        (END, "2020_2026"),
    ]:
        sub = equity.loc[:year_end]
        if len(sub) > 1:
            y = (sub.index[-1] - sub.index[0]).days / 365.25
            metrics[f"{label}_cagr"] = float(sub.iloc[-1] ** (1 / y) - 1)
    return result, metrics


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f = load_data()
    rows = []

    bh_equity = (1.0 + f.synthetic_tqqq_ret).cumprod()
    years = (f.index[-1] - f.index[0]).days / 365.25
    bh_dd = bh_equity / bh_equity.cummax() - 1.0
    rows.append({
        "strategy": "BUY_HOLD",
        "defensive_exposure": np.nan,
        "final_balance_multiple": float(bh_equity.iloc[-1]),
        "cagr": float(bh_equity.iloc[-1] ** (1 / years) - 1),
        "max_drawdown": float(bh_dd.min()),
        "days_defensive": 0,
        "defensive_fraction": 0.0,
        "trigger_count": 0,
        "exit_count": 0,
    })

    for fed_trigger, prefix in [(True, "FED_PAUSE_200DMA"), (False, "DMA_200_STICKY")]:
        for exposure in EXPOSURES:
            result, metrics = run_sticky(f, exposure, fed_trigger)
            rows.append({
                "strategy": prefix,
                "defensive_exposure": exposure,
                **metrics,
            })
            safe = str(exposure).replace(".", "_")
            result[["qqq_close", "dma_200", "monetary_state", "exposure", "equity", "drawdown",
                    "triggered_today", "exited_today"]].to_csv(
                OUT / f"tqqq_fed_lifecycle_sticky_{prefix.lower()}_{safe}.csv"
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "tqqq_fed_lifecycle_sticky_summary.csv", index=False)
    print("\nFED LIFECYCLE STICKY DEFENSE BACKTEST")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
