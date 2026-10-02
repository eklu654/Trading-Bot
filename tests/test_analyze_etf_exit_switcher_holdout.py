import pandas as pd
import pytest

from research.analyze_etf_exit_switcher_holdout import split_metrics


def test_split_metrics_resets_capital_for_each_chronological_split():
    frame = pd.DataFrame(
        {
            "Date": pd.date_range("2023-01-01", periods=3, freq="D"),
            "portfolio_return": [0.10, 0.0, 0.0],
            "selector_return": [0.10, 0.02, 0.0],
            "selector_pnl": [0.0, 10.0, 0.0],
            "selector_source": ["CASH_OR_ETF", "OPTIONS_REALIZED", "CASH_OR_ETF"],
        }
    )
    result = split_metrics(frame, capital=5000.0, minimum_option_days=2)
    holdout = result[result["split"] == "HOLDOUT"].iloc[0]
    assert holdout["selector_ending_equity"] == pytest.approx(5610.0)
    assert holdout["etf_ending_equity"] == pytest.approx(5500.0)
    assert holdout["incremental_vs_etf"] == pytest.approx(110.0)
    assert holdout["option_realized_days"] == 1
    assert holdout["sample_status"] == "INSUFFICIENT_OPTION_SAMPLE"
