"""Tests for the fixed risk-budget overlay; no network or market data required."""
import numpy as np
import pytest

from research.risk_budget_isolation import apply_cap


def test_cap_scales_invested_exposure_and_preserves_cash():
    b0 = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
    assert np.array_equal(apply_cap(b0, 0.95), [0.95, 0.0, 0.95, 0.0, 0.95])
    assert np.array_equal(apply_cap(b0, 0.90), [0.90, 0.0, 0.90, 0.0, 0.90])


def test_cap_rejects_invalid_values():
    for cap in (0.0, -0.1, 1.01):
        with pytest.raises(ValueError):
            apply_cap(np.array([1.0, 0.0]), cap)


def test_cap_does_not_change_b0_cash_days():
    b0 = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
    for cap in (0.95, 0.90):
        got = apply_cap(b0, cap)
        assert np.array_equal(got == 0.0, b0 == 0.0)
        assert np.all((got >= 0.0) & (got <= cap))
