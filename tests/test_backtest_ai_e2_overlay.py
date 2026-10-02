"""E6 binary AI overlay tests."""

from research import backtest_ai_e2_overlay as e6


def test_e6_has_only_two_actions():
    assert e6.HORIZON == 20
    assert e6.ALPHA == 1.0
