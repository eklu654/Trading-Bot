import numpy as np
import pandas as pd

from research.backtest_etf031_tqqq_robustness import (
    cagr,
    equity_from_returns,
    max_drawdown,
    path_permutation_stress,
    summarize,
)


def test_equity_and_drawdown_are_deterministic():
    ret = pd.Series(
        [0.10, -0.05, 0.20],
        index=pd.date_range("2020-01-01", periods=3, freq="D"),
    )
    equity = equity_from_returns(ret)
    assert np.isclose(equity.iloc[-1], 1.254)
    assert np.isclose(max_drawdown(equity), -0.05 / 1.10)


def test_summary_starts_from_5000():
    ret = pd.Series(
        [0.10, 0.0],
        index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
    )
    result = summarize(ret, "synthetic")
    assert np.isclose(result["ending_balance_5000"], 5500.0)


def test_path_permutation_preserves_terminal_multiple(tmp_path, monkeypatch):
    dates = pd.date_range("2020-01-01", periods=8, freq="D")
    price = pd.Series(
        [100, 110, 99, 120, 108, 130, 117, 140],
        index=dates,
        name="adj_close",
    )
    result = path_permutation_stress(price)
    terminal = result["terminal_multiple"].to_numpy()
    assert np.allclose(terminal, terminal[0])
    assert np.isfinite(result["max_drawdown"]).all()


def test_cagr_requires_positive_terminal_equity():
    ret = pd.Series(
        [0.0, 0.0],
        index=pd.date_range("2020-01-01", periods=2),
    )
    assert cagr(equity_from_returns(ret)) == 0.0
