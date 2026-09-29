"""Focused accounting tests for ETF-001 benchmark semantics."""

import numpy as np
import pandas as pd

from research.backtest_etf001 import backtest


def make_prices(rows=4):
    index = pd.date_range("2026-01-02", periods=rows, freq="D")
    # Total-return prices double on the final day so the drift calculation is
    # distinguishable from periodic equal-weight rebalancing.
    values = np.array([100.0, 100.0, 100.0, 200.0])[:rows]
    prices = {}
    for symbol in ("TQQQ", "SPXL", "SOXL"):
        prices[symbol] = pd.DataFrame(
            {"close": values, "adj_close": values}, index=index
        )
    vix = pd.Series(15.0, index=index, name="vix")
    return prices, vix


def test_buy_and_hold_preserves_initial_sleeve_weights_then_drifts():
    prices, vix = make_prices()
    frame = backtest(
        prices,
        vix,
        use_vix_overlay=False,
        cash_allocation=0.25,
        buy_and_hold=True,
    )

    # Initial portfolio = 25% cash + 75% equally split among the ETFs.
    # A 100% final price gain in every ETF therefore produces a 1.75x NAV,
    # with no rebalancing back to 25% per sleeve.
    assert frame["portfolio_value"].iloc[-1] == 1.75
    assert frame["cash_weight"].iloc[-1] == 0.25


def test_buy_and_hold_cash_levels_change_invested_exposure():
    prices, vix = make_prices()

    no_cash = backtest(
        prices, vix, use_vix_overlay=False, cash_allocation=0.0, buy_and_hold=True
    )
    half_cash = backtest(
        prices, vix, use_vix_overlay=False, cash_allocation=0.5, buy_and_hold=True
    )

    assert no_cash["portfolio_value"].iloc[-1] == 2.0
    assert half_cash["portfolio_value"].iloc[-1] == 1.5


def test_timed_strategy_uses_next_session_holdings():
    index = pd.date_range("2026-01-02", periods=202, freq="D")
    values = np.full(len(index), 100.0)
    prices = {
        symbol: pd.DataFrame(
            {"close": values, "adj_close": values}, index=index
        )
        for symbol in ("TQQQ", "SPXL", "SOXL")
    }
    vix = pd.Series(15.0, index=index, name="vix")

    frame = backtest(
        prices, vix, use_vix_overlay=False, cash_allocation=0.25, buy_and_hold=False
    )

    # No signal can be active before the 200-session moving-average warmup.
    assert frame["invested_weight"].iloc[198] == 0.0
    # Once the signal is established, holdings are shifted one session so the
    # close that generates the signal cannot also receive that day's return.
    assert frame["invested_weight"].iloc[201] == 0.75
