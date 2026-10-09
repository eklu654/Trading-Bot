"""Diagnostic-only attribution of Fed lifecycle states around baseline drawdowns.

This does not test or optimize a strategy. It asks whether the existing,
conservatively lagged Fed state is present early enough to plausibly help with
the specific slow-bear misses identified in the baseline audit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from canonical_shock_recovery_fed_dma_overlay import (
    START, END, DMA, SHOCK, RECOVERY,
    download_market, download_fed, map_fed_state_to_market,
    build_shock_recovery_events,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
MIN_DRAWDOWN = -0.15
EPISODE_ENTRY_DRAWDOWN = -0.05
REARM_FRACTION = 0.95


def make_episodes(
    qqq_adj_close: pd.Series,
    qqq_dma: pd.Series,
    fed_state: pd.Series,
) -> pd.DataFrame:
    px = qqq_adj_close.astype(float)
    daily_return = px.pct_change().fillna(0.0)
    rolling_high = px.rolling(252, min_periods=1).max()
    drawdown = px / rolling_high - 1.0
    raw_shock = daily_return.le(SHOCK)
    rows = []
    active = None

    for i, date in enumerate(px.index):
        high = float(rolling_high.iloc[i])
        if active is None and px.iloc[i] <= high * (1.0 + EPISODE_ENTRY_DRAWDOWN):
            lookback_start = max(0, i - 251)
            window = px.iloc[lookback_start:i + 1]
            peak_date = window.idxmax()
            active = {
                "start_i": i,
                "start": date,
                "peak_date": peak_date,
                "peak": high,
                "trough_i": i,
                "trough_date": date,
                "trough": float(px.iloc[i]),
            }

        if active is not None:
            if px.iloc[i] < active["trough"]:
                active["trough"] = float(px.iloc[i])
                active["trough_i"] = i
                active["trough_date"] = date

            if px.iloc[i] >= active["peak"] * REARM_FRACTION:
                end_i = i
                max_dd = active["trough"] / active["peak"] - 1.0
                if max_dd <= MIN_DRAWDOWN:
                    segment = px.index[active["start_i"]:end_i + 1]
                    shock_dates = segment[raw_shock.loc[segment].to_numpy()]
                    states = fed_state.loc[segment]
                    state_counts = states.value_counts().to_dict()
                    overlay_mask = (
                        px.loc[segment].lt(qqq_dma.loc[segment])
                        & states.eq("TIGHTENING_PAUSED")
                    )
                    first_shock = shock_dates[0] if len(shock_dates) else pd.NaT
                    first_shock_i = px.index.get_loc(first_shock) if pd.notna(first_shock) else None
                    first_shock_delay = (
                        int(first_shock_i - active["start_i"]) if first_shock_i is not None else None
                    )
                    first_overlay = segment[overlay_mask.to_numpy()]
                    rows.append({
                        "episode_start": active["start"].date().isoformat(),
                        "reference_peak_date": active["peak_date"].date().isoformat(),
                        "reference_peak_adj_close": active["peak"],
                        "episode_start_drawdown": float(px.loc[active["start"]] / active["peak"] - 1.0),
                        "trough_date": active["trough_date"].date().isoformat(),
                        "trough_drawdown": float(max_dd),
                        "episode_end": date.date().isoformat(),
                        "sessions": int(end_i - active["start_i"] + 1),
                        "first_daily_shock": first_shock.date().isoformat() if pd.notna(first_shock) else "",
                        "sessions_until_first_daily_shock": first_shock_delay,
                        "fed_state_at_start": str(fed_state.loc[active["start"]]),
                        "fed_state_at_first_shock": str(fed_state.loc[first_shock]) if pd.notna(first_shock) else "",
                        "fed_state_at_trough": str(fed_state.loc[active["trough_date"]]),
                        "below_200dma_sessions": int((px.loc[segment] < qqq_dma.loc[segment]).sum()),
                        "paused_and_below_200dma_sessions": int(overlay_mask.sum()),
                        "first_paused_below_200dma_date": first_overlay[0].date().isoformat() if len(first_overlay) else "",
                        "fed_state_session_counts": json.dumps({str(k): int(v) for k, v in state_counts.items()}, sort_keys=True),
                    })
                active = None

    if active is not None:
        end_i = len(px) - 1
        date = px.index[-1]
        max_dd = active["trough"] / active["peak"] - 1.0
        if max_dd <= MIN_DRAWDOWN:
            segment = px.index[active["start_i"]:end_i + 1]
            shock_dates = segment[raw_shock.loc[segment].to_numpy()]
            states = fed_state.loc[segment]
            state_counts = states.value_counts().to_dict()
            overlay_mask = px.loc[segment].lt(qqq_dma.loc[segment]) & states.eq("TIGHTENING_PAUSED")
            first_shock = shock_dates[0] if len(shock_dates) else pd.NaT
            first_shock_i = px.index.get_loc(first_shock) if pd.notna(first_shock) else None
            first_overlay = segment[overlay_mask.to_numpy()]
            rows.append({
                "episode_start": active["start"].date().isoformat(),
                "reference_peak_date": active["peak_date"].date().isoformat(),
                "reference_peak_adj_close": active["peak"],
                "episode_start_drawdown": float(px.loc[active["start"]] / active["peak"] - 1.0),
                "trough_date": active["trough_date"].date().isoformat(),
                "trough_drawdown": float(max_dd),
                "episode_end": date.date().isoformat(),
                "sessions": int(end_i - active["start_i"] + 1),
                "first_daily_shock": first_shock.date().isoformat() if pd.notna(first_shock) else "",
                "sessions_until_first_daily_shock": int(first_shock_i - active["start_i"]) if first_shock_i is not None else None,
                "fed_state_at_start": str(fed_state.loc[active["start"]]),
                "fed_state_at_first_shock": str(fed_state.loc[first_shock]) if pd.notna(first_shock) else "",
                "fed_state_at_trough": str(fed_state.loc[active["trough_date"]]),
                "below_200dma_sessions": int((px.loc[segment] < qqq_dma.loc[segment]).sum()),
                "paused_and_below_200dma_sessions": int(overlay_mask.sum()),
                "first_paused_below_200dma_date": first_overlay[0].date().isoformat() if len(first_overlay) else "",
                "fed_state_session_counts": json.dumps({str(k): int(v) for k, v in state_counts.items()}, sort_keys=True),
            })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    q = download_market("QQQ").rename(columns={
        "Open": "qqq_open", "High": "qqq_high", "Low": "qqq_low",
        "Close": "qqq_close", "Adj Close": "qqq_adj_close", "Volume": "qqq_volume",
    })
    t = download_market("TQQQ").rename(columns={
        "Open": "tqqq_open", "High": "tqqq_high", "Low": "tqqq_low",
        "Close": "tqqq_close", "Adj Close": "tqqq_adj_close", "Volume": "tqqq_volume",
    })
    common = q.join(t, how="inner").dropna().sort_index()
    fed = download_fed()
    lagged_state = map_fed_state_to_market(fed, common.index)
    dma = common["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean()
    episodes = make_episodes(common["qqq_adj_close"], dma, lagged_state)

    events = build_shock_recovery_events(common["qqq_adj_close"])
    event_rows = []
    qret = common["qqq_adj_close"].pct_change().fillna(0.0)
    for shock_i, low_i, decision_i in events:
        shock_date = common.index[shock_i]
        low_date = common.index[low_i]
        decision_date = common.index[decision_i]
        event_rows.append({
            "shock_date": shock_date.date().isoformat(),
            "low_date": low_date.date().isoformat(),
            "recovery_decision_close": decision_date.date().isoformat(),
            "qqq_return_on_shock": float(qret.iloc[shock_i]),
            "fed_state_at_shock_lagged": str(lagged_state.loc[shock_date]),
            "qqq_below_200dma_at_shock": bool(common["qqq_adj_close"].iloc[shock_i] < dma.iloc[shock_i]) if np.isfinite(dma.iloc[shock_i]) else False,
            "fed_state_at_recovery_lagged": str(lagged_state.loc[decision_date]),
            "qqq_above_200dma_at_recovery": bool(common["qqq_adj_close"].iloc[decision_i] >= dma.iloc[decision_i]) if np.isfinite(dma.iloc[decision_i]) else False,
            "sessions_from_shock_to_recovery": int(decision_i - shock_i),
        })
    event_df = pd.DataFrame(event_rows)

    transitions = []
    prior = None
    for date, state in lagged_state.items():
        if state != prior:
            transitions.append({"date": date.date().isoformat(), "fed_state_lagged": str(state)})
            prior = state
    transition_df = pd.DataFrame(transitions)

    frozen = common.copy()
    frozen["fed_state_lagged_one_session"] = lagged_state
    frozen["qqq_dma_200"] = dma
    frozen["qqq_drawdown_from_rolling_252_high"] = common["qqq_adj_close"] / common["qqq_adj_close"].rolling(252, min_periods=1).max() - 1.0
    frozen.to_csv(OUT / "canonical_fed_state_attribution_frozen_inputs.csv", index_label="date", float_format="%.12g")
    episodes.to_csv(OUT / "canonical_fed_state_attribution_episodes.csv", index=False)
    event_df.to_csv(OUT / "canonical_fed_state_attribution_baseline_events.csv", index=False)
    transition_df.to_csv(OUT / "canonical_fed_state_attribution_transitions.csv", index=False)

    digest = hashlib.sha256((OUT / "canonical_fed_state_attribution_frozen_inputs.csv").read_bytes()).hexdigest()
    manifest = {
        "status": "DIAGNOSTIC_ONLY",
        "start": common.index[0].date().isoformat(),
        "end": common.index[-1].date().isoformat(),
        "rows": len(common),
        "market_and_state_input_sha256": digest,
        "fed_state_lag_sessions": 1,
        "episode_definition": "start at <= -5% from rolling 252-session high; end at recovery to 95% of reference peak; report trough <= -15%",
        "baseline_shock_rule": f"QQQ adjusted-close daily return <= {SHOCK}",
        "baseline_recovery_rule": f"close >= {RECOVERY:.0%} above post-shock running low; execution next open",
        "dma": DMA,
        "episode_count_reported": len(episodes),
        "baseline_event_count": len(event_df),
        "warning": "This is state attribution only; it does not evaluate a new trading candidate or claim the Fed state predicts returns.",
    }
    (OUT / "canonical_fed_state_attribution_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\nDRAWDOWN EPISODES")
    print(episodes.to_string(index=False))
    print("\nBASELINE EVENTS")
    print(event_df.to_string(index=False))
    print("\nFED STATE TRANSITIONS")
    print(transition_df.to_string(index=False))
    print("\nMANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
