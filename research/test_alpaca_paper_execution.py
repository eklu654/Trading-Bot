import unittest
from alpaca_paper_execution import PAPER_BASE_URL, SafetyGateError, plan_order, canonical_json

def plan(**overrides):
    args = dict(portfolio="b0", endpoint=PAPER_BASE_URL, account_status="ACTIVE",
        account_blocked=False, trading_blocked=False, currency="USD", market_is_open=True,
        session_date="2026-10-09", latest_bar_date="2026-10-09", price="100",
        target_weight="1", current_qty="0", open_order_count=0)
    args.update(overrides)
    return plan_order(**args)

class PaperPlannerTests(unittest.TestCase):
    def test_b0_sizes_from_fixed_5000_virtual_sleeve(self):
        x=plan()
        self.assertEqual(x.target_notional,"5000.00")
        self.assertEqual(x.target_qty,"50.000")
        self.assertEqual(x.side,"buy")
        self.assertEqual(x.mode,"PLAN_ONLY_NO_SUBMISSION")
    def test_f75_weight_is_capped_at_75_percent_or_full(self):
        self.assertEqual(plan(portfolio="f75",target_weight="0.75").target_notional,"3750.00")
        with self.assertRaisesRegex(SafetyGateError,"frozen portfolio"):
            plan(portfolio="f75",target_weight="0.8")
    def test_flat_target_sells_existing_long(self):
        x=plan(target_weight="0",current_qty="12")
        self.assertEqual((x.side,x.qty,x.target_qty),("sell","12.000","0.000"))
    def test_already_aligned_returns_no_order(self):
        self.assertIsNone(plan(current_qty="50"))
    def test_endpoint_must_be_paper_exact(self):
        with self.assertRaisesRegex(SafetyGateError,"paper API"):
            plan(endpoint="https://api.alpaca.markets")
    def test_account_must_be_active_and_unblocked(self):
        for changes in ({"account_status":"INACTIVE"},{"account_blocked":True},
                        {"trading_blocked":True},{"currency":"EUR"}):
            with self.subTest(changes=changes),self.assertRaises(SafetyGateError): plan(**changes)
    def test_unresolved_open_order_blocks_plan(self):
        with self.assertRaisesRegex(SafetyGateError,"open orders"): plan(open_order_count=1)
    def test_closed_market_blocks_plan(self):
        with self.assertRaisesRegex(SafetyGateError,"market must be open"): plan(market_is_open=False)
    def test_stale_or_mismatched_session_blocks_plan(self):
        with self.assertRaisesRegex(SafetyGateError,"latest completed session"):
            plan(latest_bar_date="2026-10-08")
        with self.assertRaisesRegex(SafetyGateError,"stale signal"): plan(max_bar_age_sessions=1)
    def test_invalid_prices_and_short_positions_block(self):
        for changes in ({"price":"0"},{"price":"NaN"},{"current_qty":"-1"}):
            with self.subTest(changes=changes),self.assertRaises(SafetyGateError): plan(**changes)
    def test_client_id_is_deterministic_and_changes_with_session(self):
        x=plan()
        self.assertEqual(x.client_order_id,plan().client_order_id)
        self.assertNotEqual(x.client_order_id,plan(session_date="2026-10-12",
            latest_bar_date="2026-10-12").client_order_id)
    def test_ledger_json_contains_no_credentials_and_is_stable(self):
        x=plan()
        self.assertEqual(canonical_json(x),canonical_json(x))
        self.assertNotIn("secret",canonical_json(x).lower())
        self.assertNotIn("key_id",canonical_json(x).lower())

if __name__ == "__main__": unittest.main()
