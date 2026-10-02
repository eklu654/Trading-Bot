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

    # The option entry occurs while ETF sleeves are flat. ETF returns on the
    # next two sessions must remain suppressed until the option exits.
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

    # Exit-day performance is option P&L only. ETF exposure resumes on the
    # following session, so the exit-day 25% ETF return cannot be combined
    # with the option realization.
    assert result.loc[dates[1], "selector_return"] == pytest.approx(0.02)
    assert result.loc[dates[2], "selector_return"] == pytest.approx(0.25)
    assert result["selector_equity"].iloc[-1] == pytest.approx(6375.0)
