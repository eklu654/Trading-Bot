import pandas as pd
import pytest

from research.evaluate_etf_exit_switcher import build_switcher_path


def test_switcher_keeps_cash_while_option_is_open():
    dates = pd.date_range("2023-01-01", periods=5, freq="D")
    etf = pd.DataFrame(
        {
            "portfolio_return": [0.0, 0.10, 0.10, 0.10, 0.10],
            "active_sleeves": [0, 1, 1, 1, 1],
        },
        index=dates,
    )
    accepted = pd.DataFrame(
        [
            {
                "entry_date": dates[0],
                "exit_date": dates[2],
                "net_pnl": 50.0,
                "max_defined_loss": 300.0,
            }
        ]
    )

    result = build_switcher_path(etf, accepted, capital=5000.0)

    assert result["option_active"].tolist() == [True, True, True, False, False]
    assert result["selector_return"].tolist() == pytest.approx(
        [0.0, 0.0, 0.01, 0.10, 0.10]
    )
    assert result.loc[dates[2], "selector_source"] == "OPTIONS_REALIZED"
    assert result.loc[dates[3], "selector_source"] == "CASH_OR_ETF"
    assert result["selector_equity"].iloc[-1] == pytest.approx(6110.5)


def test_switcher_does_not_double_count_etf_return_on_option_exit():
    dates = pd.date_range("2023-01-01", periods=3, freq="D")
    etf = pd.DataFrame(
        {
            "portfolio_return": [0.0, 0.25, 0.25],
            "active_sleeves": [0, 1, 1],
        },
        index=dates,
    )
    accepted = pd.DataFrame(
        [
            {
                "entry_date": dates[0],
                "exit_date": dates[1],
                "net_pnl": 100.0,
                "max_defined_loss": 300.0,
            }
        ]
    )

    result = build_switcher_path(etf, accepted, capital=5000.0)

    assert result.loc[dates[1], "selector_return"] == pytest.approx(0.02)
    assert result.loc[dates[2], "selector_return"] == pytest.approx(0.25)
    assert result["selector_equity"].iloc[-1] == pytest.approx(6375.0)


def test_option_pnl_is_applied_to_current_equity_not_initial_capital():
    dates = pd.date_range("2023-01-01", periods=4, freq="D")
    etf = pd.DataFrame(
        {
            "portfolio_return": [0.10, 0.0, 0.0, 0.10],
            "active_sleeves": [1, 0, 0, 1],
        },
        index=dates,
    )
    accepted = pd.DataFrame(
        [
            {
                "entry_date": dates[1],
                "exit_date": dates[2],
                "net_pnl": 100.0,
                "max_defined_loss": 300.0,
            }
        ]
    )

    result = build_switcher_path(etf, accepted, capital=5000.0)

    # The account first grows to $5,500 through ETF exposure. The $100 option
    # realization then becomes $5,600, rather than being treated as a 2%
    # return on the original $5,000 capital.
    assert result.loc[dates[0], "selector_equity"] == pytest.approx(5500.0)
    assert result.loc[dates[2], "selector_equity"] == pytest.approx(5600.0)
    assert result.loc[dates[2], "selector_return"] == pytest.approx(100.0 / 5500.0)
    assert result.loc[dates[3], "selector_equity"] == pytest.approx(6160.0)
