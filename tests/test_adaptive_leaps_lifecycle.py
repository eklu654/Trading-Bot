"""Unit tests for deterministic LEAPS lifecycle primitives."""
import unittest
from datetime import date

from research.adaptive_leaps_lifecycle import (
    OptionQuote,
    can_execute_next_observation,
    conservative_buy_cost,
    conservative_sell_proceeds,
    quote_is_eligible,
    select_long_call,
    should_exit_long_call,
)


def q(*, obs=date(2020, 1, 2), exp=date(2020, 10, 28), strike=100,
      delta=0.80, bid=10, ask=10.5, mark=10.25, volume=10, oi=100,
      kind="call", cid="x"):
    return OptionQuote("SPY", obs, exp, strike, kind, delta, bid, ask,
                       mark, volume, oi, cid)


class LifecycleTests(unittest.TestCase):
    def test_valid_quote_and_activity_required(self):
        self.assertTrue(quote_is_eligible(q()))
        self.assertFalse(quote_is_eligible(q(bid=0)))
        self.assertFalse(quote_is_eligible(q(ask=9, bid=10)))
        self.assertFalse(quote_is_eligible(q(mark=0)))
        self.assertFalse(quote_is_eligible(q(volume=0, oi=0)))
        self.assertFalse(quote_is_eligible(q(kind="put")))

    def test_target_dte_precedes_delta_and_spread(self):
        target_dte = q(cid="target-dte", exp=date(2020, 9, 28), delta=0.70, bid=9, ask=9.1)
        exact_delta_but_worse_dte = q(cid="target-delta", exp=date(2020, 10, 28), delta=0.80, bid=10, ask=11)
        self.assertEqual(select_long_call([exact_delta_but_worse_dte, target_dte]).contract_id, "target-dte")

    def test_delta_distance_then_spread_tiebreak(self):
        target = q(cid="target", exp=date(2020, 10, 28), delta=0.80, bid=10, ask=11)
        wrong_delta = q(cid="delta", exp=date(2020, 10, 28), delta=0.70, bid=9, ask=9.1)
        wider = q(cid="wide", exp=date(2020, 10, 28), delta=0.80, bid=10, ask=11.5)
        self.assertEqual(select_long_call([wider, wrong_delta, target]).contract_id, "target")

    def test_no_candidate_returns_none(self):
        self.assertIsNone(select_long_call([q(bid=0)]))

    def test_buy_ask_sell_bid_convention(self):
        quote = q(bid=10, ask=10.5)
        self.assertEqual(conservative_buy_cost(quote), 1050)
        self.assertEqual(conservative_sell_proceeds(quote), 1000)

    def test_reject_invalid_execution_quote(self):
        with self.assertRaises(ValueError):
            conservative_buy_cost(q(bid=10, ask=9))
        with self.assertRaises(ValueError):
            conservative_sell_proceeds(q(bid=0))

    def test_expiry_buffer_boundary(self):
        self.assertTrue(should_exit_long_call(q(obs=date(2020, 10, 1), exp=date(2020, 10, 28))))
        self.assertFalse(should_exit_long_call(q(obs=date(2020, 10, 1), exp=date(2020, 11, 5))))

    def test_execution_must_follow_signal_date(self):
        self.assertFalse(can_execute_next_observation(date(2020, 1, 2), date(2020, 1, 2)))
        self.assertTrue(can_execute_next_observation(date(2020, 1, 2), date(2020, 1, 3)))


if __name__ == "__main__":
    unittest.main()
