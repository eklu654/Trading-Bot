""""$5,000 implementation-feasibility replay for the frozen family-rotation risk overlay.

This is not a live-trading simulator. It tests small-account implementation with
whole-share positions, explicit cash, transaction costs, and two causal execution
models: prior-close execution (the existing research convention) and next-open
execution (a more realistic execution sensitivity).

Signals for session t are known at the prior close. The open model executes the
target allocation at session-t adjusted open, then measures the portfolio through
the next adjusted open. The close model preserves the original prior-close
convention. No current-session price is used to create that session's signal.

Whole shares are floored and residual cash remains uninvested.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_dynamic_leverage import load
from research.test_dma_family_rotation_risk_overlay import base_weights, build_overlay

DATA_DIR = ROOT / "data" / "research"
STARTING_BALANCE = 5000.0
COSTS = (0, 10, 25, 50)
CANDIDATES = (
    ("BASE_ROTATE_DMA250_TOP2_C5", None),
    ("RISK_V30_L20_DD20", (20, 0.30)),
    ("RISK_V30_L20_DD25", (25, 0.30)),
    ("RISK_V30_L20_DD30", (30, 0.30)),
)
SPLITS = {
    "full": ("2010-03-12", "2026-10-02"),
    "train": ("2010-03-12", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2026-10-02"),
}


def prices_for(names, idx):
    symbol_map = {
        "SP500": "SPXL",
        "NASDAQ100": "TQQQ",
        "SEMICONDUCTORS": "SOXL",
        "DOW30": "UDOW",
        "RUSSELL2000": "TNA",
    }
    frames = {}
    for name in names:
        raw = load(symbol_map[name]).reindex(idx)
        factor = raw["adj_close"] / raw["close"]
        frames[name] = pd.DataFrame(
            {"adj_open": raw["open"] * factor, "adj_close": raw["adj_close"]},
            index=idx,
        )
    return frames


def _trade_to_target(cash, shares, target, prices, cost_bps):
    equity = cash + float((shares * prices).sum())
    desired = pd.Series(0.0, index=target.index)
    for name in target.index:
        p = float(prices[name])
        if p > 0 and pd.notna(p):
            desired[name] = np.floor((equity * float(target[name])) / p)

    trade_value = float(((desired - shares).abs() * prices).sum())
    cost = trade_value * cost_bps / 10000.0
    cash -= float(((desired - shares) * prices).sum()) + cost
    return cash, desired, trade_value / max(equity, 1e-12)


def replay_close(targets: pd.DataFrame, prices, cost_bps: int) -> pd.DataFrame:
    """Original research convention: rebalance at prior adjusted close."""
    idx = targets.index
    cash = STARTING_BALANCE
    shares = pd.Series(0.0, index=targets.columns)
    rows = []

    for i in range(1, len(idx)):
        date = idx[i]
        prev = idx[i - 1]
        prev_prices = pd.Series(
            {name: float(prices[name].loc[prev, "adj_close"]) for name in targets.columns}
        )
        cur_prices = pd.Series(
            {name: float(prices[name].loc[date, "adj_close"]) for name in targets.columns}
        )
        cash, shares, turnover = _trade_to_target(
            cash, shares, targets.loc[date], prev_prices, cost_bps
        )
        equity_end = cash + float((shares * cur_prices).sum())
        rows.append((date, equity_end, turnover, cash))

    return pd.DataFrame(
        rows, columns=["date", "equity", "turnover", "cash"]
    ).set_index("date")


def replay_open(targets: pd.DataFrame, prices, cost_bps: int) -> pd.DataFrame:
    """Causal sensitivity: rebalance at session-t adjusted open.

    Existing positions experience the overnight move into today's open before
    the new target is applied. The new target then earns the open-to-next-open
    return. The final session is omitted because there is no following open.
    """
    idx = targets.index
    cash = STARTING_BALANCE
    shares = pd.Series(0.0, index=targets.columns)
    rows = []

    for i in range(1, len(idx) - 1):
        date = idx[i]
        next_date = idx[i + 1]
        open_prices = pd.Series(
            {name: float(prices[name].loc[date, "adj_open"]) for name in targets.columns}
        )
        next_open = pd.Series(
            {name: float(prices[name].loc[next_date, "adj_open"]) for name in targets.columns}
        )
        cash, shares, turnover = _trade_to_target(
            cash, shares, targets.loc[date], open_prices, cost_bps
        )
        equity_end = cash + float((shares * next_open).sum())
        rows.append((date, equity_end, turnover, cash))

    return pd.DataFrame(
        rows, columns=["date", "equity", "turnover", "cash"]
    ).set_index("date")


def _max_recovery_days(equity: pd.Series) -> float:
    """Longest completed peak-to-recovery interval in calendar days."""
    values = equity.to_numpy(dtype=float)
    dates = equity.index
    peak = values[0]
    peak_date = dates[0]
    max_days = 0.0
    for value, date in zip(values[1:], dates[1:]):
        if value >= peak:
            max_days = max(max_days, (date - peak_date).days)
            peak = value
            peak_date = date
    return float(max_days)


def summary(frame, label, cost, execution, split):
    eq = frame.equity
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    running_peak = eq.cummax()
    dollar_dd = eq - running_peak
    dd = eq / running_peak - 1
    daily = eq.pct_change().dropna()
    peak_mask = eq.eq(running_peak.iloc[-1]).to_numpy()
    last_peak_date = eq.index[peak_mask][-1]
    return {
        "strategy": label,
        "execution": execution,
        "cost_bps": cost,
        "split": split,
        "start": eq.index[0],
        "end": eq.index[-1],
        "ending_equity": eq.iloc[-1],
        "total_return": eq.iloc[-1] / STARTING_BALANCE - 1,
        "cagr": (eq.iloc[-1] / STARTING_BALANCE) ** (1 / years) - 1,
        "max_drawdown": dd.min(),
        "max_dollar_drawdown": dollar_dd.min(),
        "minimum_equity": eq.min(),
        "max_recovery_days": _max_recovery_days(eq),
        "current_underwater_days": (
            (eq.index[-1] - last_peak_date).days
            if eq.iloc[-1] < running_peak.iloc[-1]
            else 0
        ),
        "worst_observed_period": daily.min() if not daily.empty else np.nan,
        "average_cash": frame.cash.mean(),
        "annualized_turnover": frame.turnover.mean() * 252,
    }


def main():
    base_w, returns = base_weights()
    prices = prices_for(base_w.columns, base_w.index)
    rows = []

    for label, spec in CANDIDATES:
        if spec is None:
            targets = base_w
        else:
            dd, target = spec
            overlay = build_overlay(base_w, returns, 20, target, dd / 100.0)
            targets = base_w.mul(overlay.exposure, axis=0)

        for cost in COSTS:
            executions = {
                "prior_close": replay_close(targets, prices, cost),
                "next_open": replay_open(targets, prices, cost),
            }
            for execution, frame in executions.items():
                for split, (start, end) in SPLITS.items():
                    segment = frame.loc[start:end]
                    if not segment.empty:
                        rows.append(summary(segment, label, cost, execution, split))

    out = pd.DataFrame(rows)
    out.to_csv(DATA_DIR / "dma_family_rotation_5000_account_replay.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
