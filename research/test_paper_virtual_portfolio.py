import unittest
from decimal import Decimal
from paper_virtual_portfolio import (
    new_state, validate_state, apply_fills, mark_to_market, plan_target,
    stage_intent, mark_submission_outcome, reconcile_order,
    complete_terminal_intent, mark_submission_attempting, abort_unsubmitted_intent, LedgerSafetyError, state_json,
)

class VirtualPortfolioTests(unittest.TestCase):
    def test_starts_with_5000_cash_and_zero_shares(self):
        s = new_state("b0")
        self.assertEqual(s["cash"], "5000.00")
        self.assertEqual(s["qty"], "0.000")
        self.assertTrue(validate_state(s))

    def test_fill_application_is_idempotent(self):
        s = new_state("b0")
        fill = {"id":"fill-1","symbol":"TQQQ","side":"buy","qty":"10","price":"100"}
        a = apply_fills(s, [fill])
        b = apply_fills(a, [fill])
        self.assertEqual(a, b)
        self.assertEqual(a["qty"], "10.000")
        self.assertEqual(a["cash"], "4000.000000")
        self.assertEqual(len(a["processed_fill_ids"]), 1)

    def test_partial_fills_apply_incrementally_by_unique_activity_id(self):
        s = new_state("b0")
        s = apply_fills(s, [
            {"id":"f1","symbol":"TQQQ","side":"buy","qty":"5","price":"100"},
            {"id":"f2","symbol":"TQQQ","side":"buy","qty":"5","price":"101"},
        ])
        self.assertEqual(s["qty"], "10.000")
        self.assertEqual(s["cash"], "3995.000000")
        s = mark_to_market(s, "2026-10-09", "101")
        self.assertEqual(s["equity"], "5005.00")

    def test_rejects_sell_that_would_create_short(self):
        with self.assertRaisesRegex(LedgerSafetyError, "exceeds virtual long"):
            apply_fills(new_state("b0"), [
                {"id":"s1","symbol":"TQQQ","side":"sell","qty":"1","price":"100"}])

    def test_rejects_wrong_symbol_and_invalid_fill(self):
        with self.assertRaisesRegex(LedgerSafetyError, "unexpected fill symbol"):
            apply_fills(new_state("b0"), [{"id":"x","symbol":"SOXL","side":"buy","qty":"1","price":"10"}])
        with self.assertRaisesRegex(LedgerSafetyError, "invalid"):
            apply_fills(new_state("b0"), [{"id":"x","symbol":"TQQQ","side":"hold","qty":"1","price":"10"}])

    def test_mark_to_market_is_monotonic_and_idempotent(self):
        s = new_state("b0")
        s = mark_to_market(s, "2026-10-09", "100")
        self.assertEqual(mark_to_market(s, "2026-10-09", "100"), s)
        with self.assertRaisesRegex(LedgerSafetyError, "cannot be rewritten"):
            mark_to_market(s, "2026-10-09", "101")
        with self.assertRaisesRegex(LedgerSafetyError, "backwards"):
            mark_to_market(s, "2026-10-08", "100")

    def test_target_sizing_uses_compounded_virtual_equity(self):
        s = new_state("b0")
        s = apply_fills(s, [{"id":"f1","symbol":"TQQQ","side":"buy","qty":"10","price":"100"}])
        s = mark_to_market(s, "2026-10-09", "110")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="110")
        self.assertEqual(intent["virtual_equity"], "5100.00")
        self.assertEqual(intent["target_notional"], "5100.00")
        self.assertEqual(intent["target_qty"], "46.363")

    def test_f75_requires_and_respects_b0_eligibility(self):
        s = new_state("f75")
        with self.assertRaisesRegex(LedgerSafetyError, "requires the B0"):
            plan_target(s, signal_session="2026-10-09", target_weight="0.75", reference_price="100")
        with self.assertRaisesRegex(LedgerSafetyError, "B0 eligibility"):
            plan_target(s, signal_session="2026-10-09", target_weight="0.75", reference_price="100", baseline_weight="0")
        self.assertIsNone(plan_target(s, signal_session="2026-10-09", target_weight="0", reference_price="100", baseline_weight="0"))

    def test_staged_intent_blocks_a_second_order(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        with self.assertRaisesRegex(LedgerSafetyError, "unresolved order"):
            plan_target(s, signal_session="2026-10-12", target_weight="1", reference_price="100")
        self.assertEqual(s["pending_intent"]["submission_state"], "STAGED")

    def test_unknown_submission_is_never_retried_automatically(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        s = mark_submission_outcome(s, "unknown")
        s = reconcile_order(s, None)
        self.assertEqual(s["pending_intent"]["submission_state"], "UNKNOWN")
        with self.assertRaisesRegex(LedgerSafetyError, "unresolved order"):
            plan_target(s, signal_session="2026-10-12", target_weight="1", reference_price="100")

    def test_reconcile_requires_exact_client_id(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        with self.assertRaisesRegex(LedgerSafetyError, "does not match"):
            reconcile_order(s, {"client_order_id":"other","id":"broker-1","status":"new"})

    def test_terminal_order_requires_fill_ledger_position_reconciliation(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        s = mark_submission_outcome(s, "accepted", "broker-1")
        s = reconcile_order(s, {"client_order_id":intent["client_order_id"],"id":"broker-1","status":"filled"})
        with self.assertRaisesRegex(LedgerSafetyError, "does not reconcile"):
            complete_terminal_intent(s, broker_qty="50", broker_status="filled")
        s = apply_fills(s, [{"id":"f1","symbol":"TQQQ","side":"buy","qty":"50","price":"100"}])
        s = complete_terminal_intent(s, broker_qty="50", broker_status="filled")
        self.assertIsNone(s["pending_intent"])
        self.assertEqual(s["last_terminal_order"]["status"], "filled")

    def test_rejected_order_cannot_be_replayed_with_same_client_id(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        s = mark_submission_outcome(s, "rejected")
        s = complete_terminal_intent(s, broker_qty="0", broker_status="rejected")
        with self.assertRaisesRegex(LedgerSafetyError, "already used"):
            plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")

    def test_completed_order_blocks_rebalance_replay_for_same_signal_session(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        s = mark_submission_outcome(s, "accepted", "broker-1")
        s = reconcile_order(s, {"client_order_id":intent["client_order_id"],"id":"broker-1","status":"filled"})
        s = apply_fills(s, [{"id":"f1","symbol":"TQQQ","side":"buy","qty":"50","price":"100"}])
        s = complete_terminal_intent(s, broker_qty="50", broker_status="filled")
        with self.assertRaisesRegex(LedgerSafetyError, "already completed for this signal session"):
            plan_target(s, signal_session="2026-10-09", target_weight="0", reference_price="99")

    def test_aborted_before_submit_is_safe_and_never_reused_same_session(self):
        s = new_state("b0")
        intent = plan_target(s, signal_session="2026-10-09", target_weight="1", reference_price="100")
        s = stage_intent(s, intent)
        s = mark_submission_attempting(s)
        s = abort_unsubmitted_intent(s, "market closed before POST")
        self.assertIsNone(s["pending_intent"])
        self.assertEqual(s["last_terminal_order"]["status"], "aborted_before_submit")
        with self.assertRaisesRegex(LedgerSafetyError, "already completed for this signal session"):
            plan_target(s, signal_session="2026-10-09", target_weight="0", reference_price="100")
        self.assertIsNotNone(plan_target(s, signal_session="2026-10-12", target_weight="1", reference_price="100"))

    def test_state_serialization_is_stable_and_secret_free(self):
        s = new_state("f75")
        self.assertEqual(state_json(s), state_json(s))
        self.assertNotIn("secret", state_json(s).lower())
        self.assertNotIn("api_key", state_json(s).lower())

if __name__ == "__main__":
    unittest.main()
