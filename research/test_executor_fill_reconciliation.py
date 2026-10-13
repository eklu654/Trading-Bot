"""Focused tests for broker fill-to-ledger reconciliation (no network calls)."""
import unittest
from unittest.mock import patch

import alpaca_paper_order_executor as executor
from paper_virtual_portfolio import new_state, stage_intent, mark_submission_attempting


def staged_state():
    state = new_state("b0")
    intent = {
        "portfolio": "b0", "symbol": "TQQQ", "signal_session": "2026-10-12",
        "target_weight": "1", "virtual_equity": "5000.00", "target_notional": "5000.00",
        "reference_price": "50", "current_qty": "0", "target_qty": "99.502",
        "side": "buy", "qty": "99.502", "client_order_id": "tb-test-fill-reconcile",
        "endpoint": executor.PAPER_URL, "mode": "PLAN_ONLY_NO_SUBMISSION",
    }
    return mark_submission_attempting(stage_intent(state, intent))


class FillReconciliationTests(unittest.TestCase):
    def test_filled_order_applies_fill_and_clears_only_after_position_matches(self):
        state = staged_state()
        order = {
            "id": "broker-order-1", "client_order_id": "tb-test-fill-reconcile",
            "status": "filled",
        }
        activities = [{
            "id": "fill-1", "order_id": "broker-order-1", "symbol": "TQQQ",
            "side": "buy", "qty": "2", "price": "50",
        }]
        def fake_get_json(url, key, secret, allow_404=False):
            if "/account/activities/FILL?" in url:
                return activities
            if url.endswith("/v2/positions"):
                return [{"symbol": "TQQQ", "qty": "2", "side": "long"}]
            raise AssertionError("unexpected URL: " + url)
        with patch.object(executor, "get_json", side_effect=fake_get_json):
            result = executor.reconcile_order_fills(state, order, "key", "secret")
        self.assertEqual(result["qty"], "2.000")
        self.assertEqual(result["processed_fill_ids"], ["fill-1"])
        self.assertIsNone(result["pending_intent"])
        self.assertEqual(result["last_terminal_order"]["status"], "filled")

    def test_repeated_fill_activity_is_applied_once(self):
        state = staged_state()
        state["qty"] = "2.000"
        state["cash"] = "4900.000000"
        state["equity"] = "5000.00"
        state["processed_fill_ids"] = ["fill-1"]
        order = {
            "id": "broker-order-1", "client_order_id": "tb-test-fill-reconcile",
            "status": "filled",
        }
        activities = [{
            "id": "fill-1", "order_id": "broker-order-1", "symbol": "TQQQ",
            "side": "buy", "qty": "2", "price": "50",
        }]
        def fake_get_json(url, key, secret, allow_404=False):
            if "/account/activities/FILL?" in url:
                return activities
            if url.endswith("/v2/positions"):
                return [{"symbol": "TQQQ", "qty": "2", "side": "long"}]
            raise AssertionError("unexpected URL: " + url)
        with patch.object(executor, "get_json", side_effect=fake_get_json):
            result = executor.reconcile_order_fills(state, order, "key", "secret")
        self.assertEqual(result["qty"], "2.000")
        self.assertEqual(result["processed_fill_ids"], ["fill-1"])
        self.assertIsNone(result["pending_intent"])

    def test_position_mismatch_fails_closed_and_preserves_pending_intent(self):
        state = staged_state()
        order = {
            "id": "broker-order-1", "client_order_id": "tb-test-fill-reconcile",
            "status": "filled",
        }
        activities = [{
            "id": "fill-1", "order_id": "broker-order-1", "symbol": "TQQQ",
            "side": "buy", "qty": "2", "price": "50",
        }]
        def fake_get_json(url, key, secret, allow_404=False):
            if "/account/activities/FILL?" in url:
                return activities
            if url.endswith("/v2/positions"):
                return [{"symbol": "TQQQ", "qty": "1", "side": "long"}]
            raise AssertionError("unexpected URL: " + url)
        with patch.object(executor, "get_json", side_effect=fake_get_json):
            with self.assertRaises(executor.ExecutorBlocked):
                executor.reconcile_order_fills(state, order, "key", "secret")


if __name__ == "__main__":
    unittest.main()
