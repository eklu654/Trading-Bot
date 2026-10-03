"""$5,000 implementation-feasibility replay for the frozen family-rotation risk overlay.

This is not a live-trading simulator. It tests whether the strategy remains
implementable with whole-share positions, explicit cash, and transaction costs.

Signals are generated exactly as in the research backtest. A target allocation
for session t is executed at the prior session's adjusted close, then the
session-t close-to-close return is realized. Whole shares are floored; residual
cash remains uninvested. This preserves the no-lookahead convention while
adding a realistic small-account constraint.
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


def prices_for(names, idx):
    return pd.DataFrame(
        {name: load({"SP500":"SPXL","NASDAQ100":"TQQQ","SEMICONDUCTORS":"SOXL",
                     "DOW30":"UDOW","RUSSELL2000":"TNA"}[name])["adj_close"]
         .reindex(idx)
         for name in names},
        index=idx,
    )


def replay(targets: pd.DataFrame, prices: pd.DataFrame, cost_bps: int) -> pd.DataFrame:
    idx = targets.index
    cash = STARTING_BALANCE
    shares = pd.Series(0.0, index=targets.columns)
    rows = []
    for i in range(1, len(idx)):
        date = idx[i]
        prev = idx[i - 1]
        prev_prices = prices.loc[prev]
        cur_prices = prices.loc[date]
        equity_before = cash + float((shares * prev_prices).sum())

        desired = pd.Series(0.0, index=targets.columns)
        for name in targets.columns:
            p = float(prev_prices[name])
            if p > 0:
                desired[name] = np.floor((equity_before * float(targets.loc[date, name])) / p)

        trade_value = float(((desired - shares).abs() * prev_prices).sum())
        cost = trade_value * cost_bps / 10000.0
        cash -= float(((desired - shares) * prev_prices).sum()) + cost
        shares = desired

        equity_end = cash + float((shares * cur_prices).sum())
        rows.append((date, equity_end, trade_value / max(equity_before, 1e-12), cash))
    return pd.DataFrame(rows, columns=["date","equity","turnover","cash"]).set_index("date")


def summary(frame, label, cost):
    eq = frame.equity
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1/365.25)
    dd = eq / eq.cummax() - 1
    return {
        "strategy": label, "cost_bps": cost, "start": eq.index[0],
        "end": eq.index[-1], "ending_equity": eq.iloc[-1],
        "total_return": eq.iloc[-1] / STARTING_BALANCE - 1,
        "cagr": (eq.iloc[-1] / STARTING_BALANCE) ** (1 / years) - 1,
        "max_drawdown": dd.min(), "minimum_equity": eq.min(),
        "average_cash": frame.cash.mean(), "annualized_turnover": frame.turnover.mean() * 252,
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
            exposure = overlay.exposure
            targets = base_w.mul(exposure, axis=0)
        for cost in COSTS:
            frame = replay(targets, prices, cost)
            rows.append(summary(frame, label, cost))
    out = pd.DataFrame(rows)
    out.to_csv(DATA_DIR / "dma_family_rotation_5000_account_replay.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
