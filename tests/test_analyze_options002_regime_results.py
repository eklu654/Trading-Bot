import pandas as pd

from research.analyze_options002_regime_results import summarize


def test_summarize_trade_metrics():
    frame = pd.DataFrame({"pnl": [10.0, 5.0, -3.0, -2.0]})
    result = summarize(frame)
    assert result["trades"] == 4
    assert result["total_pnl"] == 10.0
    assert result["win_rate"] == 0.5
    assert result["worst_trade"] == -3.0
    assert result["profit_factor"] == 3.0


def test_summarize_empty():
    assert summarize(pd.DataFrame({"pnl": []})) == {"trades": 0}
