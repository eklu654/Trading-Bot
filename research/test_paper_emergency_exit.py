import unittest
from decimal import Decimal

from paper_emergency_exit import (
    EmergencyExitBlocked, build_exit_intent, order_payload,
    transition_exit, validate_trigger, PAPER_URL,
)


class EmergencyExitCoreTests(unittest.TestCase):
    def test_trigger_exactly_at_minus_4_5_percent(self):
        result = validate_trigger("2026-10-12", "95.5", "100")
        self.assertTrue(result["triggered"])
        self.assertEqual(result["change_pct"], "-4.500")

    def test_trigger_does_not_fire_above_threshold(self):
        self.assertFalse(validate_trigger("2026-10-12", "95.51", "100")["triggered"])

    def test_invalid_price_and_date_fail_closed(self):
        for price in ("0", "-1", "NaN", "Infinity"):
            with self.subTest(price=price), self.assertRaises(EmergencyExitBlocked):
                validate_trigger("2026-10-12", price, "100")
        with self.assertRaises(EmergencyExitBlocked):
            validate_trigger("not-a-date", "95", "100")

    def test_intent_is_deterministic_and_sells_only_long_position(self):
        digest = "a" * 64
        one = build_exit_intent("b0", "2026-10-12", "12.345", digest)
        two = build_exit_intent("b0", "2026-10-12", "12.345", digest)
        self.assertEqual(one, two)
        self.assertEqual(one["side"], "sell")
        self.assertEqual(one["endpoint"], PAPER_URL)
        self.assertEqual(order_payload(one), {
            "symbol": "TQQQ", "qty": "12.345", "side": "sell",
            "type": "market", "time_in_force": "day",
            "client_order_id": one["client_order_id"],
        })

    def test_rejects_invalid_portfolio_quantity_and_trigger_hash(self):
        with self.assertRaises(EmergencyExitBlocked):
            build_exit_intent("live", "2026-10-12", "1", "a" * 64)
        with self.assertRaises(EmergencyExitBlocked):
            build_exit_intent("b0", "2026-10-12", "0", "a" * 64)
        with self.assertRaises(EmergencyExitBlocked):
            build_exit_intent("b0", "2026-10-12", "1", "not-a-hash")

    def test_rejects_live_endpoint_or_buy_order(self):
        intent = build_exit_intent("b0", "2026-10-12", "1", "a" * 64)
        with self.assertRaises(EmergencyExitBlocked):
            order_payload({**intent, "endpoint": "https://api.alpaca.markets"})
        with self.assertRaises(EmergencyExitBlocked):
            order_payload({**intent, "side": "buy"})

    def test_broker_order_must_match_intent(self):
        intent = build_exit_intent("b0", "2026-10-12", "1", "a" * 64)
        with self.assertRaises(EmergencyExitBlocked):
            transition_exit(intent, "SUBMITTED", {
                "client_order_id": "tb-wrong", "symbol": "TQQQ", "side": "sell"
            })

    def test_filled_requires_zero_broker_position(self):
        intent = build_exit_intent("b0", "2026-10-12", "1", "a" * 64)
        with self.assertRaises(EmergencyExitBlocked):
            transition_exit(intent, "FILLED", broker_position_qty="1")
        with self.assertRaises(EmergencyExitBlocked):
            transition_exit(intent, "FILLED", broker_order={
                "id": "paper-order-1", "client_order_id": intent["client_order_id"],
                "symbol": "TQQQ", "side": "sell", "status": "accepted",
            }, broker_position_qty="0")
        submitting = transition_exit(intent, "SUBMITTING")
        submitted = transition_exit(submitting, "SUBMITTED", broker_order={
            "id": "paper-order-1", "client_order_id": intent["client_order_id"],
            "symbol": "TQQQ", "side": "sell", "status": "filled",
        })
        done = transition_exit(submitted, "FILLED", broker_order={
            "id": "paper-order-1", "client_order_id": intent["client_order_id"],
            "symbol": "TQQQ", "side": "sell", "status": "filled",
        }, broker_position_qty="0")
        self.assertEqual(done["status"], "FILLED")
        self.assertEqual(done["broker_position_qty_after"], "0")


    def test_terminal_states_cannot_be_reopened(self):
        intent = build_exit_intent("b0", "2026-10-12", "1", "a" * 64)
        blocked = transition_exit(intent, "BLOCKED")
        with self.assertRaises(EmergencyExitBlocked):
            transition_exit(blocked, "SUBMITTING")
        submitted = transition_exit(transition_exit(intent, "SUBMITTING"), "SUBMITTED")
        filled_order = {
            "id": "paper-order-2", "client_order_id": intent["client_order_id"],
            "symbol": "TQQQ", "side": "sell", "status": "filled",
        }
        done = transition_exit(submitted, "FILLED", broker_order=filled_order,
                               broker_position_qty="0")
        with self.assertRaises(EmergencyExitBlocked):
            transition_exit(done, "STAGED")

    def test_unexpected_short_or_negative_position_rejected(self):
        intent = build_exit_intent("b0", "2026-10-12", "1", "a" * 64)
        with self.assertRaises(EmergencyExitBlocked):
            transition_exit(intent, "FILLED", broker_position_qty="-1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
