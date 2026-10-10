"""Targeted announcement-vs-effective-date sensitivity for the 2015/2016 Fed hikes.

This diagnostic changes only the two previously verified FRED announcement-date
observations to the prior target until the effective date. It compares mapped
Fed state and the existing paused-Fed x 200-DMA overlay signals. It does NOT
run a portfolio backtest unless a state or overlay signal changes.
"""
from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START, END = "2010-01-01", "2026-10-08"
SERIES = ("DFEDTAR", "DFEDTARL", "DFEDTARU")
# (announcement date, effective date), both official Fed dates documented in
# FED_EVENT_TABLE_FRED_RECONCILIATION_RESULT_2026-10-10.md.
DATE_PAIRS = (("2015-12-16", "2015-12-17"), ("2016-12-14", "2016-12-15"))
DMA = 200


def download_target() -> pd.Series:
    parts = []
    for sid in SERIES:
        req = Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
                      headers={"User-Agent": "Trading-Bot-Fed-Date-Sensitivity/1.0"})
        with urlopen(req, timeout=30) as response:
            frame = pd.read_csv(BytesIO(response.read()))
        frame.columns = ["date", sid.lower()]
        frame["date"] = pd.to_datetime(frame["date"])
        frame[sid.lower()] = pd.to_numeric(frame[sid.lower()], errors="coerce")
        parts.append(frame.set_index("date"))
    fed = pd.concat(parts, axis=1).sort_index()
    target = fed["dfedtar"].copy()
    midpoint = (fed["dfedtarl"] + fed["dfedtaru"]) / 2.0
    valid = midpoint.notna()
    target.loc[valid] = midpoint.loc[valid]
    target = target.dropna()
    target.index = pd.DatetimeIndex(target.index).tz_localize(None)
    return target


def classify(target: pd.Series) -> pd.DataFrame:
    fed = pd.DataFrame({"target_rate": target.sort_index()})
    fed["target_change"] = fed["target_rate"].diff()
    fed["action"] = np.select(
        [fed["target_change"] > 0.001, fed["target_change"] < -0.001],
        ["HIKE", "CUT"], default="HOLD")
    fed["hike_90d"] = fed["action"].eq("HIKE").astype(int).rolling("90D").sum()
    fed["cut_90d"] = fed["action"].eq("CUT").astype(int).rolling("90D").sum()
    prior_dates = fed.index - pd.DateOffset(years=1)
    positions = fed.index.searchsorted(prior_dates, side="right") - 1
    prior = np.full(len(fed), np.nan)
    good = positions >= 0
    prior[good] = fed["target_rate"].to_numpy()[positions[good]]
    fed["net_change_12m"] = fed["target_rate"].to_numpy() - prior
    fed["monetary_state"] = np.select(
        [
            fed["cut_90d"].fillna(0).gt(0) | fed["net_change_12m"].fillna(0).lt(-0.001),
            fed["hike_90d"].fillna(0).gt(0),
            fed["net_change_12m"].fillna(0).gt(0.001),
        ],
        ["EASING", "TIGHTENING_ACTIVE", "TIGHTENING_PAUSED"],
        default="NEUTRAL")
    return fed


def map_state(fed: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.Series:
    left = pd.DataFrame({"date": dates})
    right = fed[["monetary_state"]].reset_index()
    right.columns = ["date", "monetary_state"]
    mapped = pd.merge_asof(left.sort_values("date"), right.sort_values("date"),
                           on="date", direction="backward")
    return pd.Series(mapped["monetary_state"].to_numpy(), index=dates).shift(1).fillna(
        "INSUFFICIENT_HISTORY")


def overlay(prices: pd.Series, state: pd.Series) -> np.ndarray:
    avg = prices.rolling(DMA, min_periods=DMA).mean().to_numpy()
    px = prices.to_numpy()
    st = state.reindex(prices.index).fillna("INSUFFICIENT_HISTORY").to_numpy()
    armed = False
    weights = []
    for price, ma, fs in zip(px, avg, st):
        if not np.isfinite(ma):
            armed = False
        elif not armed and price < ma and fs == "TIGHTENING_PAUSED":
            armed = True
        elif armed and price >= ma:
            armed = False
        weights.append(0.0 if armed else 1.0)
    return np.asarray(weights)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    q = yf.download("QQQ", start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(q.columns, pd.MultiIndex):
        q.columns = q.columns.get_level_values(0)
    q.index = pd.to_datetime(q.index).tz_localize(None)
    prices = q["Adj Close"].dropna().astype(float).sort_index()
    raw = download_target()
    effective = raw.copy()
    edit_rows = []
    for announcement, effective_date in DATE_PAIRS:
        ann, eff = pd.Timestamp(announcement), pd.Timestamp(effective_date)
        if ann not in effective.index or eff not in effective.index:
            raise RuntimeError(f"Missing FRED observation for {announcement} or {effective_date}")
        prior = effective.loc[effective.index < ann]
        if prior.empty:
            raise RuntimeError(f"No prior target rate for {announcement}")
        old, announced = float(prior.iloc[-1]), float(effective.loc[ann])
        effective.loc[ann] = old
        edit_rows.append({
            "announcement_date": announcement,
            "effective_date": effective_date,
            "target_before_announcement": old,
            "fred_target_on_announcement": announced,
            "fred_target_on_effective_date": float(effective.loc[eff]),
            "transformed_target_on_announcement": float(effective.loc[ann]),
            "transformation_applied": bool(abs(old-announced) > 1e-8 and abs(float(effective.loc[eff])-announced) < 1e-8),
        })
    raw_state = map_state(classify(raw), prices.index)
    eff_state = map_state(classify(effective), prices.index)
    raw_overlay = overlay(prices, raw_state)
    eff_overlay = overlay(prices, eff_state)
    dates = prices.index
    ledger = pd.DataFrame({
        "date": dates,
        "raw_lagged_fed_state": raw_state.to_numpy(),
        "effective_date_lagged_fed_state": eff_state.to_numpy(),
        "fed_state_differs": (raw_state.to_numpy() != eff_state.to_numpy()),
        "raw_overlay_signal": raw_overlay,
        "effective_date_overlay_signal": eff_overlay,
        "overlay_signal_differs": (raw_overlay != eff_overlay),
    })
    ledger.to_csv(OUT / "fed_2015_2016_effective_date_signal_diff.csv", index=False)
    edits = pd.DataFrame(edit_rows)
    edits.to_csv(OUT / "fed_2015_2016_effective_date_transform.csv", index=False)
    state_diffs = ledger.loc[ledger["fed_state_differs"]]
    signal_diffs = ledger.loc[ledger["overlay_signal_differs"]]
    manifest = {
        "status": "COMPLETED_SIGNAL_DIAGNOSTIC",
        "method": "Move only the 2015-12-16 and 2016-12-14 announcement-day FRED target changes to their documented effective dates; retain classifier, one-session market-calendar lag, and 200-DMA overlay logic.",
        "market_start": dates.min().date().isoformat(),
        "market_end": dates.max().date().isoformat(),
        "market_rows": len(dates),
        "fed_raw_sha256": hashlib.sha256(raw.to_csv(float_format="%.8f").encode()).hexdigest(),
        "fed_transformed_sha256": hashlib.sha256(effective.to_csv(float_format="%.8f").encode()).hexdigest(),
        "transforms": edit_rows,
        "fed_state_difference_sessions": int(state_diffs.shape[0]),
        "overlay_signal_difference_sessions": int(signal_diffs.shape[0]),
        "fed_state_difference_dates": state_diffs["date"].dt.strftime("%Y-%m-%d").tolist(),
        "overlay_signal_difference_dates": signal_diffs["date"].dt.strftime("%Y-%m-%d").tolist(),
        "portfolio_backtest_required": bool(signal_diffs.shape[0] > 0),
        "note": "Signal diagnostic only. No portfolio return claim. A full backtest is warranted only if an overlay signal differs.",
    }
    (OUT / "fed_2015_2016_effective_date_signal_diff_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    if signal_diffs.empty:
        print("\nGATE: No overlay signal differences; do not run a full portfolio backtest.")
    else:
        print("\nGATE: Overlay signals differ; review dates and then run a targeted portfolio counterfactual.")


if __name__ == "__main__":
    main()
