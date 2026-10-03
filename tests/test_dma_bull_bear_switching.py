"""Behavioral tests for the bull/cash/bear DMA research constraint."""

import pandas as pd
import pytest

from research import test_dma_bull_bear_switching as module


def test_inverse_pairs_are_explicit():
    assert module.PAIRS["SP500"]["bear"] == "SPXS"
    assert module.PAIRS["NASDAQ100"]["bear"] == "SQQQ"
    assert module.PAIRS["SEMICONDUCTORS"]["bear"] == "SOXS"
    assert module.PAIRS["DOW30"]["bear"] == "SDOW"
    assert module.PAIRS["RUSSELL2000"]["bear"] == "TZA"


def test_validate_exclusivity_rejects_same_family_overlap():
    frame = pd.DataFrame(
        {
            "state": ["BULL"],
            "bull_weight": [1.0],
            "bear_weight": [0.25],
        }
    )
    with pytest.raises(AssertionError, match="Bull and bear exposure overlapped"):
        module.validate_exclusivity(frame)


def test_validate_exclusivity_allows_cash_or_one_side():
    frame = pd.DataFrame(
        {
            "state": ["CASH", "BULL", "BEAR"],
            "bull_weight": [0.0, 1.0, 0.0],
            "bear_weight": [0.0, 0.0, 0.50],
        }
    )
    module.validate_exclusivity(frame)


def test_cross_family_opposite_exposure_is_allowed(monkeypatch):
    index = pd.date_range("2026-01-01", periods=2, freq="D")
    frames = {}
    for i, pair in enumerate(module.PAIRS):
        state = "BULL" if i == 0 else "BEAR" if i == 1 else "CASH"
        frames[pair] = pd.DataFrame(
            {
                "portfolio_return": [
                    0.0,
                    0.01 if state == "BULL" else -0.01 if state == "BEAR" else 0.0,
                ],
                "state": [state, state],
                "bull_weight": [1.0 if state == "BULL" else 0.0] * 2,
                "bear_weight": [0.50 if state == "BEAR" else 0.0] * 2,
            },
            index=index,
        )

    monkeypatch.setattr(module, "backtest_pair", lambda *args, **kwargs: frames[args[0]])
    out = module.backtest_multi_pair(200, 50, 1, 0.50)

    assert out.loc[index[0], "SP500_state"] == "BULL"
    assert out.loc[index[0], "NASDAQ100_state"] == "BEAR"
    assert out.loc[index[0], "SP500_bull_weight"] > 0
    assert out.loc[index[0], "NASDAQ100_bear_weight"] > 0


def test_partial_inverse_weight_is_explicit():
    assert module.BEAR_WEIGHTS == (0.25, 0.50, 0.75, 1.00)
    assert all(0.0 < weight <= 1.0 for weight in module.BEAR_WEIGHTS)
