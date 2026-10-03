"""Structural tests for the bull/cash/bear DMA research constraint."""

from pathlib import Path

SCRIPT = Path("research/test_dma_bull_bear_switching.py").read_text()


def test_inverse_pairs_are_explicit():
    assert '"SPXS"' in SCRIPT
    assert '"SQQQ"' in SCRIPT
    assert '"SOXS"' in SCRIPT
    assert '"SDOW"' in SCRIPT
    assert '"TZA"' in SCRIPT


def test_portfolio_states_are_exclusive():
    assert 'state = "CASH"' in SCRIPT
    assert 'state == "BULL"' in SCRIPT
    assert 'state == "BEAR"' in SCRIPT
    assert 'Bull and bear exposure overlapped.' in SCRIPT


def test_bear_weight_does_not_create_bull_overlap():
    assert '"bull_weight": [1.0 if s == "BULL" else 0.0 for s in states]' in SCRIPT
    assert '"bear_weight": [bear_weight if s == "BEAR" else 0.0 for s in states]' in SCRIPT


def test_cross_family_exposure_is_allowed():
    assert "backtest_multi_pair" in SCRIPT
    assert "cross-family bull/bear exposure is allowed" in SCRIPT
    assert 'out[f"{pair}_state"]' in SCRIPT
