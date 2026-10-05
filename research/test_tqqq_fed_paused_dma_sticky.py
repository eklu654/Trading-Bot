"""Fed paused-state x DMA sticky-defense strategy study.

This is the first strategy test derived from the completed Fed lifecycle and
Fed-state x DMA event studies.

Live-safe trigger:
- Enter defense when QQQ is BELOW its 200-DMA and monetary state is
  TIGHTENING_PAUSED.
- Remain in defense until QQQ closes ABOVE its 200-DMA.

The Fed state itself is contemporaneously knowable; no final-hike hindsight is
used. Exposure inside defense is frozen to a small predeclared family:
0%, 25%, 50%, and 75% TQQQ.

This is a research control, not a production rule.
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

FRED_SERIES = ("DFEDTAR", "DFEDTARU", "DFEDTARL")
DEFENSE_EXPOSURES = (0.0, 0.25, 0.50, 0.75)


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
    fed = pd.concat([fred_csv(s) for s in FRED_SERIES], axis=1).sort_index()
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
    daily["synthetic_tqqq_return"] = (
        1.0 + 3.0 * qqq_ret
    ).clip(lower=0.0) - 1.0

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


def strategy_weights(frame: pd.DataFrame, defense_exposure: float) -> pd.Series:
    defensive = False
    weights: list[float] = []

    for _, row in frame.iterrows():
        if (
            not defensive
            and row["dma_state"] == "BELOW_DMA"
            and row["monetary_state"] == "TIGHTENING_PAUSED"
        ):
            defensive = True
        elif (
            defensive
            and row["dma_state"] == "ABOVE_DMA"
        ):
            defensive = False

        weights.append(defense_exposure if defensive else 1.0)

    return pd.Series(weights, index=frame.index, dtype=float)


def summarize_path(
    frame: pd.DataFrame, strategy: str, weights: pd.Series
) -> dict[str, object]:
    returns = frame["synthetic_tqqq_return"]
    equity = 5000.0 * (1.0 + returns * weights).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1.0
    years = (frame.index[-1] - frame.index[0]).days / 365.25

    return {
        "strategy": strategy,
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "starting_balance": 5000.0,
        "final_balance": float(equity.iloc[-1]),
        "cagr": float(equity.iloc[-1] ** (1.0 / years) - 1.0),
        "max_drawdown": float(drawdown.min()),
        "minimum_equity": float(equity.min()),
        "average_exposure": float(weights.mean()),
        "defensive_days": int((weights < 1.0).sum()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fed = download_fed()
    qqq = download_qqq()
    frame = build_daily_states(fed, qqq)

    weights_by_strategy: dict[str, pd.Series] = {
        "BUY_AND_HOLD": pd.Series(1.0, index=frame.index),
    }

    for exposure in DEFENSE_EXPOSURES:
        label = f"FED_PAUSED_DMA_STICKY_{int(exposure * 100)}"
        weights_by_strategy[label] = strategy_weights(frame, exposure)

    # Existing fixed controls remain comparisons, not candidates for tuning.
    weights_by_strategy["DMA_200_50"] = np.where(
        frame["dma_state"].eq("BELOW_DMA"), 0.50, 1.0
    )
    weights_by_strategy["DMA_200_75"] = np.where(
        frame["dma_state"].eq("BELOW_DMA"), 0.75, 1.0
    )
    weights_by_strategy = {
        k: pd.Series(v, index=frame.index, dtype=float)
        for k, v in weights_by_strategy.items()
    }

    summary = pd.DataFrame(
        [
            summarize_path(frame, name, weights)
            for name, weights in weights_by_strategy.items()
        ]
    ).sort_values("final_balance", ascending=False)

    transitions = []
    for name, weights in weights_by_strategy.items():
        if not name.startswith("FED_PAUSED_DMA_STICKY_"):
            continue
        changed = weights.ne(weights.shift()).fillna(False)
        for date in weights.index[changed]:
            transitions.append(
                {
                    "strategy": name,
                    "date": date.date().isoformat(),
                    "weight": float(weights.loc[date]),
                    "dma_state": frame.loc[date, "dma_state"],
                    "monetary_state": frame.loc[date, "monetary_state"],
                }
            )

    path_rows = []
    for name, weights in weights_by_strategy.items():
        equity = 5000.0 * (
            1.0 + frame["synthetic_tqqq_return"] * weights
        ).cumprod()
        peak = equity.cummax()
        drawdown = equity / peak - 1.0
        for date in frame.index:
            path_rows.append(
                {
                    "date": date.date().isoformat(),
                    "strategy": name,
                    "equity": float(equity.loc[date]),
                    "drawdown": float(drawdown.loc[date]),
                    "weight": float(weights.loc[date]),
                    "dma_state": frame.loc[date, "dma_state"],
                    "monetary_state": frame.loc[date, "monetary_state"],
                }
            )

    frame.to_csv(OUT / "tqqq_fed_paused_dma_sticky_daily_states.csv")
    summary.to_csv(
        OUT / "tqqq_fed_paused_dma_sticky_summary.csv", index=False
    )
    pd.DataFrame(transitions).to_csv(
        OUT / "tqqq_fed_paused_dma_sticky_transitions.csv", index=False
    )
    pd.DataFrame(path_rows).to_csv(
        OUT / "tqqq_fed_paused_dma_sticky_paths.csv", index=False
    )

    print("\nFED PAUSED + DMA STICKY DEFENSE")
    print(summary.to_string(index=False))
    print("\nDEFENSIVE TRANSITIONS")
    print(pd.DataFrame(transitions).to_string(index=False))
    print("\nArtifacts written to", OUT)


if __name__ == "__main__":
    main()
