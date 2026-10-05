"""Baseline macro-regime control for synthetic TQQQ survivability research.

This is deliberately a BASELINE, not an optimized production strategy.
It tests the user's proposed architecture:
100% TQQQ with no DMA during normal conditions, with defense activated
only after persistent broad economic deterioration.

To avoid look-ahead from revised macro releases, the baseline uses a
conservative one-full-month availability lag for monthly FRED series.
This is intentionally stricter than using observation dates directly,
although a later study should replace it with exact release-date vintages.

Macro dimensions:
- labor: unemployment 3-month average versus prior 12-month low
- activity: industrial production 6-month change
- credit: Baa spread level and 3-month deterioration
- curve: 10Y-3M monthly spread

Frozen baseline state logic:
DETERIORATION requires >=2 of 4 dimensions.
CRISIS requires >=3 of 4, including labor or credit.
Persistence: 2 consecutive monthly observations.
Recovery: 3 consecutive months below deterioration criteria.

This script does NOT tune thresholds on the dot-com outcome.
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
INITIAL = 5000.0
START = "1999-03-10"
END = "2026-10-03"

FRED = {
    "unrate": "UNRATE",
    "indpro": "INDPRO",
    "credit": "BAA10YM",
    "curve": "T10Y3MM",
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


def download_macro() -> pd.DataFrame:
    frames = [fred_csv(series_id) for series_id in FRED.values()]
    macro = pd.concat(frames, axis=1).sort_index()

    # Conservative information-availability rule:
    # a month's observation is not allowed to affect the next month's
    # decisions. This is intentionally a full-month lag and therefore
    # avoids pretending the observation was known on its observation date.
    macro = macro.resample("MS").last()
    macro["available_date"] = macro.index + pd.offsets.MonthBegin(2)

    macro["unrate_3m"] = macro["unrate"].rolling(3).mean()
    macro["unrate_12m_low"] = macro["unrate_3m"].rolling(12).min()
    macro["labor_stress"] = (
        macro["unrate_3m"] - macro["unrate_12m_low"] >= 0.30
    )

    macro["indpro_6m"] = macro["indpro"].pct_change(6)
    macro["activity_stress"] = macro["indpro_6m"] <= -0.01

    macro["credit_3m_change"] = macro["credit"] - macro["credit"].shift(3)
    macro["credit_stress"] = (
        (macro["credit"] >= 2.50)
        & (macro["credit_3m_change"] >= 0.50)
    )

    macro["curve_stress"] = macro["curve"] <= 0.0

    dimensions = [
        "labor_stress",
        "activity_stress",
        "credit_stress",
        "curve_stress",
    ]
    macro["stress_count"] = macro[dimensions].sum(axis=1)

    # Baseline structural classifier. Thresholds are frozen for this
    # first pass and are not selected from the final stress outcome.
    raw_det = macro["stress_count"] >= 2
    raw_crisis = (
        (macro["stress_count"] >= 3)
        & (macro["labor_stress"] | macro["credit_stress"])
    )

    # Persistence/hysteresis.
    det_run = raw_det.astype(int).groupby(
        (~raw_det).cumsum()
    ).cumsum()
    crisis_run = raw_crisis.astype(int).groupby(
        (~raw_crisis).cumsum()
    ).cumsum()

    state = pd.Series("STRUCTURAL_EXPANSION", index=macro.index)
    state[det_run >= 2] = "MACRO_DETERIORATION"
    state[crisis_run >= 2] = "MACRO_CRISIS"

    # Recovery requires three consecutive months without the deterioration
    # threshold before returning to expansion.
    safe = ~raw_det
    safe_run = safe.astype(int).groupby((~safe).cumsum()).cumsum()
    state.loc[(state != "STRUCTURAL_EXPANSION") & (safe_run < 3)] = np.nan
    state = state.ffill().fillna("STRUCTURAL_EXPANSION")

    macro["state"] = state
    macro["decision_date"] = macro["available_date"]
    return macro


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
        columns={
            "Open": "open",
            "Close": "close",
            "Adj Close": "adj_close",
        }
    )
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    return frame.sort_index().dropna(subset=["close", "adj_close"])


def build_synthetic(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    qqq_ret = out["adj_close"].pct_change().fillna(0.0)
    out["synthetic_tqqq_close"] = INITIAL * (
        (1.0 + 3.0 * qqq_ret).clip(lower=0.0).cumprod()
    )
    out["adj_open"] = out["open"] * out["adj_close"] / out["close"]
    overnight = (out["adj_open"] / out["adj_close"].shift(1) - 1).fillna(0)
    intraday = (out["adj_close"] / out["adj_open"] - 1).fillna(0)
    out["overnight_3x"] = np.clip(1 + 3 * overnight, 0, None) - 1
    out["intraday_3x"] = np.clip(1 + 3 * intraday, 0, None) - 1
    return out


def apply_macro_states(
    frame: pd.DataFrame, macro: pd.DataFrame
) -> pd.DataFrame:
    out = frame.copy()

    # State becomes usable only on the conservative availability date.
    usable = macro[["decision_date", "state"]].dropna().copy()
    usable = usable.sort_values("decision_date")

    daily = pd.DataFrame(index=out.index)
    daily["date"] = daily.index
    mapped = pd.merge_asof(
        daily.reset_index(drop=True),
        usable.rename(columns={"decision_date": "date"}),
        on="date",
        direction="backward",
    ).set_index("date")

    out["macro_state"] = mapped["state"].reindex(out.index).ffill().fillna(
        "STRUCTURAL_EXPANSION"
    )

    # Most-aggressive mode: 100% TQQQ during expansion.
    # Macro defense levels are deliberately simple frozen controls.
    out["weight_light"] = np.select(
        [
            out["macro_state"].eq("MACRO_CRISIS"),
            out["macro_state"].eq("MACRO_DETERIORATION"),
        ],
        [0.25, 0.75],
        default=1.0,
    )
    out["weight_medium"] = np.select(
        [
            out["macro_state"].eq("MACRO_CRISIS"),
            out["macro_state"].eq("MACRO_DETERIORATION"),
        ],
        [0.0, 0.50],
        default=1.0,
    )
    out["weight_hard"] = np.select(
        [
            out["macro_state"].eq("MACRO_CRISIS"),
            out["macro_state"].eq("MACRO_DETERIORATION"),
        ],
        [0.0, 0.25],
        default=1.0,
    )
    return out


def evaluate(frame: pd.DataFrame, weight_col: str, label: str):
    weights = frame[weight_col].to_numpy(dtype=float)
    prev_w = np.roll(weights, 1)
    prev_w[0] = 0.0

    daily = (
        (1 + prev_w * frame["overnight_3x"].to_numpy())
        * (1 + weights * frame["intraday_3x"].to_numpy())
        - 1
    )
    equity = INITIAL * np.cumprod(1 + daily)
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1

    crash = (frame.index >= "2000-01-01") & (frame.index <= "2002-12-31")
    idx = np.flatnonzero(crash)
    trough_idx = int(idx[np.argmin(equity[idx])])
    pre = idx[: np.argmin(equity[idx]) + 1]
    peak_idx = int(pre[np.argmax(equity[pre])])
    peak_value = float(equity[peak_idx])
    trough_value = float(equity[trough_idx])

    recovery = np.flatnonzero(equity[trough_idx:] >= peak_value)
    recovery_idx = (
        trough_idx + int(recovery[0]) if len(recovery) else None
    )

    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    final = float(equity[-1])
    row = {
        "strategy": label,
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "starting_balance": INITIAL,
        "final_balance": final,
        "cagr": (final / INITIAL) ** (1 / years) - 1,
        "max_drawdown": float(dd.min()),
        "minimum_equity": float(equity.min()),
        "dotcom_peak_date": frame.index[peak_idx].date().isoformat(),
        "dotcom_peak_balance": peak_value,
        "dotcom_trough_date": frame.index[trough_idx].date().isoformat(),
        "dotcom_trough_balance": trough_value,
        "dotcom_peak_to_trough_drawdown": trough_value / peak_value - 1,
        "dotcom_peak_recovery_date": (
            frame.index[recovery_idx].date().isoformat()
            if recovery_idx is not None else None
        ),
        "avg_exposure": float(weights.mean()),
        "pct_expansion": float(
            (frame["macro_state"] == "STRUCTURAL_EXPANSION").mean()
        ),
        "pct_deterioration": float(
            (frame["macro_state"] == "MACRO_DETERIORATION").mean()
        ),
        "pct_crisis": float(
            (frame["macro_state"] == "MACRO_CRISIS").mean()
        ),
    }
    path = pd.DataFrame(
        {
            "Date": frame.index,
            "strategy": label,
            "equity": equity,
            "drawdown": dd,
            "weight": weights,
            "macro_state": frame["macro_state"].to_numpy(),
        }
    )
    return row, path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    macro = download_macro()
    qqq = build_synthetic(download_qqq())
    frame = apply_macro_states(qqq, macro)

    rows = []
    paths = []
    for col, label in [
        ("weight_light", "MACRO_LIGHT"),
        ("weight_medium", "MACRO_MEDIUM"),
        ("weight_hard", "MACRO_HARD"),
    ]:
        row, path = evaluate(frame, col, label)
        rows.append(row)
        paths.append(path)

    bh_weights = np.ones(len(frame))
    frame["weight_bh"] = bh_weights
    bh_row, bh_path = evaluate(frame, "weight_bh", "BUY_AND_HOLD")
    rows.append(bh_row)
    paths.append(bh_path)

    summary = pd.DataFrame(rows).sort_values("final_balance", ascending=False)
    summary.to_csv(
        OUT / "tqqq_macro_regime_baseline_summary.csv", index=False
    )
    pd.concat(paths, ignore_index=True).to_csv(
        OUT / "tqqq_macro_regime_baseline_paths.csv", index=False
    )
    macro.to_csv(OUT / "tqqq_macro_regime_macro_features.csv")
    frame[
        ["macro_state", "weight_light", "weight_medium", "weight_hard"]
    ].to_csv(OUT / "tqqq_macro_regime_daily_states.csv")

    print(summary.to_string(index=False))
    print("Macro regime baseline completed.")
    print(f"Artifacts written to {OUT}")


if __name__ == "__main__":
    main()
