"""Test the existing Fed-paused x 200-DMA idea as an overlay on the canonical shock/recovery baseline.

This experiment deliberately changes only one thing relative to the baseline:
a sticky defensive state can additionally arm when QQQ is below its existing
200-session moving average and the conservatively lagged Fed lifecycle state is
TIGHTENING_PAUSED. That overlay remains armed until QQQ closes back at/above
the 200-DMA. Baseline shock/recovery defense remains independently active.

No parameters are optimized here. The exact common QQQ/TQQQ input is downloaded
once per run, and baseline, overlay candidate, and buy-and-hold are all
calculated on the same aligned rows and adjusted OHLC convention.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from io import BytesIO

import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_daily_returns, next_open_cost_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "2010-01-01"
END = "2026-10-08"
INITIAL = 5000.0
SHOCK = -0.045
RECOVERY = 0.10
DMA = 200
FED_SERIES = ("DFEDTAR", "DFEDTARU", "DFEDTARL")


def download_market(symbol: str) -> pd.DataFrame:
    frame = yf.download(
        symbol, start=START, end=END, auto_adjust=False,
        progress=False, actions=False,
    )
    if frame.empty:
        raise RuntimeError(f"No market data returned for {symbol}")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame.sort_index().dropna()


def download_fed() -> pd.DataFrame:
    parts = []
    for series_id in FED_SERIES:
        req = Request(
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
            headers={"User-Agent": "Trading-Bot-research/1.0"},
        )
        with urlopen(req, timeout=30) as response:
            frame = pd.read_csv(BytesIO(response.read()))
        frame.columns = ["date", series_id.lower()]
        frame["date"] = pd.to_datetime(frame["date"])
        frame[series_id.lower()] = pd.to_numeric(
            frame[series_id.lower()], errors="coerce"
        )
        parts.append(frame.set_index("date"))
    fed = pd.concat(parts, axis=1).sort_index()
    fed["target_rate"] = fed["dfedtar"]
    midpoint = (fed["dfedtaru"] + fed["dfedtarl"]) / 2.0
    fed.loc[midpoint.notna(), "target_rate"] = midpoint[midpoint.notna()]
    fed = fed.loc[START:END].copy()
    fed["target_change"] = fed["target_rate"].diff()
    fed["action"] = np.select(
        [fed["target_change"] > 0.001, fed["target_change"] < -0.001],
        ["HIKE", "CUT"], default="HOLD",
    )
    fed["hike_90d"] = fed["action"].eq("HIKE").astype(int).rolling("90D").sum()
    fed["cut_90d"] = fed["action"].eq("CUT").astype(int).rolling("90D").sum()

    prior_year_dates = fed.index - pd.DateOffset(years=1)
    prior_positions = fed.index.searchsorted(prior_year_dates, side="right") - 1
    prior_rates = np.full(len(fed), np.nan, dtype=float)
    valid = prior_positions >= 0
    prior_rates[valid] = fed["target_rate"].to_numpy()[prior_positions[valid]]
    fed["net_change_12m"] = fed["target_rate"] - prior_rates
    fed["monetary_state"] = np.select(
        [
            fed["cut_90d"].fillna(0).gt(0)
            | fed["net_change_12m"].fillna(0).lt(-0.001),
            fed["hike_90d"].fillna(0).gt(0),
            fed["net_change_12m"].fillna(0).gt(0.001),
        ],
        ["EASING", "TIGHTENING_ACTIVE", "TIGHTENING_PAUSED"],
        default="NEUTRAL",
    )
    return fed[["target_rate", "target_change", "monetary_state"]]


def map_fed_state_to_market(fed: pd.DataFrame, market_index: pd.DatetimeIndex) -> pd.Series:
    left = pd.DataFrame({"date": market_index}).sort_values("date")
    right = fed[["monetary_state"]].reset_index()
    right.columns = ["date", "monetary_state"]
    right = right.sort_values("date")
    mapped = pd.merge_asof(left, right, on="date", direction="backward")
    # Conservative live-safe timing: a state derived from a date's Fed
    # observation is not used for that same QQQ session's close signal.
    state = pd.Series(mapped["monetary_state"].to_numpy(), index=market_index)
    return state.shift(1).fillna("INSUFFICIENT_HISTORY")


def build_shock_recovery_events(qqq_adj_close: pd.Series) -> list[tuple[int, int, int]]:
    prices = qqq_adj_close.astype(float).to_numpy()
    returns = qqq_adj_close.pct_change().fillna(0.0).to_numpy()
    armed = False
    shock_i = low_i = None
    events: list[tuple[int, int, int]] = []
    for i in range(1, len(prices)):
        if not armed and returns[i] <= SHOCK:
            armed = True
            shock_i = low_i = i
        if armed:
            if prices[i] < prices[low_i]:
                low_i = i
            if prices[i] / prices[low_i] - 1.0 >= RECOVERY:
                events.append((int(shock_i), int(low_i), i))
                armed = False
    return events


def build_baseline_signal(n: int, events: list[tuple[int, int, int]]) -> np.ndarray:
    signal = np.ones(n, dtype=float)
    for shock_i, _low_i, decision_i in events:
        signal[shock_i:decision_i] = 0.0
    return signal


def build_fed_dma_overlay(
    qqq_adj_close: pd.Series,
    lagged_fed_state: pd.Series,
    dma_length: int = DMA,
) -> tuple[np.ndarray, pd.DataFrame]:
    ma = qqq_adj_close.rolling(dma_length, min_periods=dma_length).mean()
    armed = False
    weights: list[float] = []
    transitions: list[dict[str, object]] = []
    for date, price, avg, fed_state in zip(
        qqq_adj_close.index, qqq_adj_close.to_numpy(), ma.to_numpy(),
        lagged_fed_state.reindex(qqq_adj_close.index).fillna("INSUFFICIENT_HISTORY"),
    ):
        if not np.isfinite(avg):
            if armed:
                armed = False
                transitions.append({"date": date.date().isoformat(), "state": "EXIT",
                                    "reason": "insufficient_dma_history"})
            weights.append(0.0 if armed else 1.0)
            continue
        entered = not armed and price < avg and fed_state == "TIGHTENING_PAUSED"
        exited = armed and price >= avg
        if entered:
            armed = True
            transitions.append({"date": date.date().isoformat(), "state": "ENTER",
                                "reason": "qqq_below_200dma_and_lagged_fed_paused",
                                "qqq_adj_close": float(price), "dma_200": float(avg),
                                "lagged_fed_state": str(fed_state)})
        elif exited:
            armed = False
            transitions.append({"date": date.date().isoformat(), "state": "EXIT",
                                "reason": "qqq_close_recovered_above_200dma",
                                "qqq_adj_close": float(price), "dma_200": float(avg),
                                "lagged_fed_state": str(fed_state)})
        weights.append(0.0 if armed else 1.0)
    return np.asarray(weights, dtype=float), pd.DataFrame(transitions)


def calculate_returns(
    frame: pd.DataFrame, signal: np.ndarray
) -> np.ndarray:
    adj_open = (
        frame["tqqq_open"].to_numpy(dtype=float)
        * frame["tqqq_adj_close"].to_numpy(dtype=float)
        / frame["tqqq_close"].to_numpy(dtype=float)
    )
    adj_close = frame["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(frame), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday = adj_close / adj_open - 1.0
    return next_open_daily_returns(signal, overnight, intraday)


def metrics(returns: np.ndarray, dates: pd.DatetimeIndex) -> dict[str, float]:
    equity = INITIAL * np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(equity)
    years = (dates[-1] - dates[0]).days / 365.25
    return {
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float((equity / peak - 1.0).min()),
        "minimum_equity": float(equity.min()),
    }


def make_period_rows(
    dates: pd.DatetimeIndex,
    return_map: dict[str, np.ndarray],
    equity_map: dict[str, np.ndarray],
    signal_map: dict[str, np.ndarray],
) -> pd.DataFrame:
    periods = [
        ("2010-2014", "2010-01-01", "2014-12-31"),
        ("2015-2019", "2015-01-01", "2019-12-31"),
        ("2020-2021", "2020-01-01", "2021-12-31"),
        ("2022-2024", "2022-01-01", "2024-12-31"),
        ("2025-current", "2025-01-01", END),
    ]
    rows = []
    for label, start, end in periods:
        mask = (dates >= start) & (dates <= end)
        for name, daily_returns in return_map.items():
            r = daily_returns[mask]
            local_eq = np.cumprod(1.0 + r)
            local_dd = (local_eq / np.maximum.accumulate(local_eq) - 1.0).min()
            equity = equity_map[name]
            sig = signal_map[name]
            rows.append({
                "period": label, "strategy": name,
                "return": float(local_eq[-1] - 1.0) if len(local_eq) else np.nan,
                "max_drawdown": float(local_dd) if len(local_eq) else np.nan,
                "start_equity_previous_close": float(equity[np.flatnonzero(mask)[0]-1])
                    if np.any(mask) and np.flatnonzero(mask)[0] > 0 else INITIAL,
                "end_equity": float(equity[np.flatnonzero(mask)[-1]]) if np.any(mask) else np.nan,
                "defensive_signal_days": int((sig[mask] < 1.0).sum()),
            })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    q = download_market("QQQ")
    t = download_market("TQQQ")
    q = q.rename(columns={
        "Open": "qqq_open", "High": "qqq_high", "Low": "qqq_low",
        "Close": "qqq_close", "Adj Close": "qqq_adj_close", "Volume": "qqq_volume",
    })
    t = t.rename(columns={
        "Open": "tqqq_open", "High": "tqqq_high", "Low": "tqqq_low",
        "Close": "tqqq_close", "Adj Close": "tqqq_adj_close", "Volume": "tqqq_volume",
    })
    common = q.join(t, how="inner").dropna().sort_index()
    if common.empty:
        raise RuntimeError("No common aligned QQQ/TQQQ observations")
    if not common.index.is_monotonic_increasing or common.index.has_duplicates:
        raise RuntimeError("Market data index must be sorted and unique")

    fed = download_fed()
    lagged_state = map_fed_state_to_market(fed, common.index)
    events = build_shock_recovery_events(common["qqq_adj_close"])
    baseline_signal = build_baseline_signal(len(common), events)
    overlay_signal, transitions = build_fed_dma_overlay(
        common["qqq_adj_close"], lagged_state, DMA
    )
    candidate_signal = np.minimum(baseline_signal, overlay_signal)
    buy_hold_signal = np.ones(len(common), dtype=float)

    # Guardrails: baseline stays independently intact, candidate never increases
    # exposure over the baseline, and every signal is a close-to-next-open weight.
    assert set(np.unique(baseline_signal)).issubset({0.0, 1.0})
    assert set(np.unique(overlay_signal)).issubset({0.0, 1.0})
    assert set(np.unique(candidate_signal)).issubset({0.0, 1.0})
    assert np.all(candidate_signal <= baseline_signal)
    assert len(events) >= 1

    signal_map = {
        "baseline_shock_recovery": baseline_signal,
        "baseline_plus_fed_paused_200dma": candidate_signal,
        "tqqq_buy_hold": buy_hold_signal,
    }
    return_map = {name: calculate_returns(common, signal) for name, signal in signal_map.items()}
    equity_map = {name: INITIAL * np.cumprod(1.0 + ret) for name, ret in return_map.items()}
    summary_rows = []
    for name, ret in return_map.items():
        row = {"strategy": name, **metrics(ret, common.index)}
        row["average_close_signal_exposure"] = float(signal_map[name].mean())
        row["defensive_signal_days"] = int((signal_map[name] < 1.0).sum())
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)

    event_rows = []
    for shock_i, low_i, decision_i in events:
        event_rows.append({
            "shock_date": common.index[shock_i].date().isoformat(),
            "low_date": common.index[low_i].date().isoformat(),
            "recovery_decision_close": common.index[decision_i].date().isoformat(),
            "defensive_signal_sessions": int(decision_i - shock_i),
        })
    event_df = pd.DataFrame(event_rows)

    daily = pd.DataFrame({
        "date": common.index,
        "qqq_adj_close": common["qqq_adj_close"].to_numpy(),
        "fed_state_lagged_one_session": lagged_state.to_numpy(),
        "qqq_dma_200": common["qqq_adj_close"].rolling(DMA, min_periods=DMA).mean().to_numpy(),
        "baseline_signal_close": baseline_signal,
        "fed_dma_overlay_signal_close": overlay_signal,
        "candidate_signal_close": candidate_signal,
        "baseline_daily_return": return_map["baseline_shock_recovery"],
        "candidate_daily_return": return_map["baseline_plus_fed_paused_200dma"],
        "buy_hold_daily_return": return_map["tqqq_buy_hold"],
        "baseline_equity": equity_map["baseline_shock_recovery"],
        "candidate_equity": equity_map["baseline_plus_fed_paused_200dma"],
        "buy_hold_equity": equity_map["tqqq_buy_hold"],
    })
    periods = make_period_rows(common.index, return_map, equity_map, signal_map)

    cost_rows = []
    adj_open = (
        common["tqqq_open"].to_numpy(dtype=float)
        * common["tqqq_adj_close"].to_numpy(dtype=float)
        / common["tqqq_close"].to_numpy(dtype=float)
    )
    adj_close = common["tqqq_adj_close"].to_numpy(dtype=float)
    overnight = np.zeros(len(common), dtype=float)
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    intraday = adj_close / adj_open - 1.0
    for name, signal in [
        ("baseline_shock_recovery", baseline_signal),
        ("baseline_plus_fed_paused_200dma", candidate_signal),
    ]:
        for bps in (0, 10, 25, 50):
            eq = next_open_cost_equity(signal, overnight, intraday, bps)
            peak = np.maximum.accumulate(eq)
            years = (common.index[-1] - common.index[0]).days / 365.25
            cost_rows.append({
                "strategy": name, "cost_bps_per_full_exposure_change": bps,
                "final_balance": float(eq[-1]),
                "cagr": float((eq[-1] / INITIAL) ** (1.0 / years) - 1.0),
                "max_drawdown": float((eq / peak - 1.0).min()),
            })
    costs = pd.DataFrame(cost_rows)

    common.to_csv(OUT / "canonical_fed_dma_overlay_frozen_inputs.csv",
                  index_label="date", float_format="%.12g")
    daily.to_csv(OUT / "canonical_fed_dma_overlay_daily.csv", index=False, float_format="%.12g")
    summary.to_csv(OUT / "canonical_fed_dma_overlay_summary.csv", index=False)
    periods.to_csv(OUT / "canonical_fed_dma_overlay_periods.csv", index=False)
    event_df.to_csv(OUT / "canonical_fed_dma_overlay_baseline_events.csv", index=False)
    transitions.to_csv(OUT / "canonical_fed_dma_overlay_transitions.csv", index=False)
    costs.to_csv(OUT / "canonical_fed_dma_overlay_costs.csv", index=False)

    input_hash = hashlib.sha256(
        (OUT / "canonical_fed_dma_overlay_frozen_inputs.csv").read_bytes()
    ).hexdigest()
    manifest = {
        "status": "COMPLETED_DIAGNOSTIC",
        "rule_id_baseline": "qqq_shock45_recovery10_actual_tqqq_v1",
        "candidate_rule_id": "baseline_plus_lagged_fed_paused_and_qqq_below_200dma_sticky_until_reclaim",
        "start": common.index[0].date().isoformat(),
        "end": common.index[-1].date().isoformat(),
        "rows": int(len(common)),
        "initial_balance": INITIAL,
        "input_sha256": input_hash,
        "baseline_shock_pct": SHOCK,
        "baseline_recovery_pct": RECOVERY,
        "overlay_dma": DMA,
        "fed_state_lag_sessions": 1,
        "overlay_entry": "QQQ adjusted close below 200-session SMA AND previous-session Fed state TIGHTENING_PAUSED",
        "overlay_exit": "QQQ adjusted close at/above 200-session SMA",
        "overlay_persists_until_exit": True,
        "execution": "close[t] signal -> open[t+1]; prior position earns overnight, new position earns intraday",
        "baseline_event_count": len(events),
        "overlay_transition_count": int(len(transitions)),
        "summary": summary.to_dict(orient="records"),
        "warning": "One predeclared overlay diagnostic; not a selected or live-approved strategy. Market and Fed inputs were downloaded once per run and shared by all candidates.",
    }
    (OUT / "canonical_fed_dma_overlay_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print("\nSUMMARY")
    print(summary.to_string(index=False))
    print("\nPERIODS (independently compounded period return; equity also shows inherited account values)")
    print(periods.to_string(index=False))
    print("\nBASELINE EVENTS")
    print(event_df.to_string(index=False))
    print("\nOVERLAY TRANSITIONS")
    print(transitions.to_string(index=False))
    print("\nCOST SENSITIVITY")
    print(costs.to_string(index=False))
    print("\nMANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
