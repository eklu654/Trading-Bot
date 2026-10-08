"""Composite Fed + macro + DMA structural defense study.

Frozen rule:
- Enter defense when either:
  (a) QQQ is below its 200-DMA while the Fed is TIGHTENING_PAUSED, or
  (b) the macro classifier is MACRO_DETERIORATION or MACRO_CRISIS.
- Remain defensive until BOTH:
  (a) QQQ is above its 200-DMA, and
  (b) macro state is STRUCTURAL_EXPANSION.

Fed state and macro state are contemporaneously constructed; no final-hike
hindsight is used.

The only defense exposures are a predeclared 0%, 25%, 50%, and 75% TQQQ.
The test is a strategy-family study, not parameter optimization.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from research.test_tqqq_fed_paused_dma_sticky import (
    build_daily_states as build_fed_states,
    download_fed,
)
from research.test_tqqq_macro_regime import (
    apply_macro_states,
    build_synthetic,
    download_macro,
    download_qqq,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
DEFENSE_EXPOSURES = (0.0, 0.25, 0.50, 0.75)


def build_composite_frame() -> pd.DataFrame:
    qqq = download_qqq()
    fed = build_fed_states(download_fed(), qqq)[
        ["close", "dma_200", "dma_state", "monetary_state"]
    ].copy()

    macro = apply_macro_states(build_synthetic(qqq), download_macro())[
        ["macro_state"]
    ].copy()

    # pandas 3/4 can preserve different datetime resolutions on independently
    # constructed indices (e.g. datetime64[s] vs datetime64[us]). Normalize
    # both indexes to the same explicit ns dtype before joining.
    fed.index = pd.DatetimeIndex(pd.to_datetime(fed.index)).astype("datetime64[ns]")
    macro.index = pd.DatetimeIndex(pd.to_datetime(macro.index)).astype("datetime64[ns]")

    frame = fed.join(macro, how="left")
    frame["qqq_return"] = frame["close"].pct_change().fillna(0.0)
    frame["synthetic_tqqq_return"] = (
        1.0 + 3.0 * frame["qqq_return"]
    ).clip(lower=0.0) - 1.0
    frame["macro_state"] = (
        frame["macro_state"].ffill().fillna("STRUCTURAL_EXPANSION")
    )
    return frame


def composite_weights(frame: pd.DataFrame, defense_exposure: float) -> pd.Series:
    defensive = False
    weights: list[float] = []

    for _, row in frame.iterrows():
        enter = (
            row["macro_state"] in {"MACRO_DETERIORATION", "MACRO_CRISIS"}
            or (
                row["dma_state"] == "BELOW_DMA"
                and row["monetary_state"] == "TIGHTENING_PAUSED"
            )
        )
        exit_ok = (
            row["dma_state"] == "ABOVE_DMA"
            and row["macro_state"] == "STRUCTURAL_EXPANSION"
        )

        if not defensive and enter:
            defensive = True
        elif defensive and exit_ok:
            defensive = False

        weights.append(defense_exposure if defensive else 1.0)

    return pd.Series(weights, index=frame.index, dtype=float)


def evaluate(
    frame: pd.DataFrame, label: str, signal_weights: pd.Series
) -> tuple[dict[str, object], pd.DataFrame]:
    # A close-derived state becomes active on the following trading day.
    # This deliberately avoids applying a newly observed close signal to the
    # same day's return.
    applied = signal_weights.shift(1).fillna(1.0)
    daily_return = frame["synthetic_tqqq_return"] * applied
    equity = INITIAL * (1.0 + daily_return).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1.0
    years = max(
        (frame.index[-1] - frame.index[0]).days / 365.25,
        1 / 365.25,
    )
    final = float(equity.iloc[-1])

    row = {
        "strategy": label,
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "starting_balance": INITIAL,
        "final_balance": final,
        "cagr": float((final / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float(drawdown.min()),
        "minimum_equity": float(equity.min()),
        "average_exposure": float(applied.mean()),
        "defensive_days": int((applied < 1.0).sum()),
    }
    path = pd.DataFrame(
        {
            "Date": frame.index,
            "strategy": label,
            "equity": equity,
            "drawdown": drawdown,
            "applied_weight": applied,
            "signal_weight": signal_weights,
            "dma_state": frame["dma_state"].to_numpy(),
            "monetary_state": frame["monetary_state"].to_numpy(),
            "macro_state": frame["macro_state"].to_numpy(),
        }
    )
    return row, path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build_composite_frame()

    strategies: dict[str, pd.Series] = {
        "BUY_AND_HOLD": pd.Series(1.0, index=frame.index)
    }
    for exposure in DEFENSE_EXPOSURES:
        strategies[f"COMPOSITE_STRUCTURAL_{int(exposure * 100)}"] = (
            composite_weights(frame, exposure)
        )

    rows: list[dict[str, object]] = []
    paths: list[pd.DataFrame] = []
    for label, weights in strategies.items():
        row, path = evaluate(frame, label, weights)
        rows.append(row)
        paths.append(path)

    summary = pd.DataFrame(rows).sort_values(
        "final_balance", ascending=False
    )

    transition_rows = []
    for label, weights in strategies.items():
        if not label.startswith("COMPOSITE_"):
            continue
        changed = weights.ne(weights.shift()).fillna(False)
        for date in weights.index[changed]:
            transition_rows.append(
                {
                    "strategy": label,
                    "date": date.date().isoformat(),
                    "signal_weight": float(weights.loc[date]),
                    "dma_state": frame.loc[date, "dma_state"],
                    "monetary_state": frame.loc[date, "monetary_state"],
                    "macro_state": frame.loc[date, "macro_state"],
                }
            )

    summary.to_csv(
        OUT / "tqqq_composite_structural_defense_summary.csv", index=False
    )
    pd.concat(paths, ignore_index=True).to_csv(
        OUT / "tqqq_composite_structural_defense_paths.csv", index=False
    )
    pd.DataFrame(transition_rows).to_csv(
        OUT / "tqqq_composite_structural_defense_transitions.csv",
        index=False,
    )
    frame.to_csv(
        OUT / "tqqq_composite_structural_defense_daily_states.csv"
    )

    print("\nCOMPOSITE FED + MACRO + DMA STRUCTURAL DEFENSE")
    print(summary.to_string(index=False))
    print("\nTRANSITIONS")
    print(pd.DataFrame(transition_rows).to_string(index=False))
    print("\nArtifacts written to", OUT)


if __name__ == "__main__":
    main()
