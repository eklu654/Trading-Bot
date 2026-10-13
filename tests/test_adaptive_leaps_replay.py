"""Synthetic chronology/accounting tests for the LEAPS replay engine."""
import unittest
from datetime import date, timedelta

from research.adaptive_leaps_lifecycle import OptionQuote
from research.adaptive_leaps_replay import replay_long_call
from research.run_adaptive_leaps_replay import calculate_diagnostics


def q(day, *, exp=None, cid="A", bid=10.0, ask=10.5, delta=0.8, volume=10, oi=100):
    return OptionQuote(
        "SPY", day, exp or day + timedelta(days=270), 100, "call", delta,
        bid, ask, (bid + ask) / 2, volume, oi, cid,
    )


class ReplayTests(unittest.TestCase):

    def test_duplicate_contract_date_rows_fail_closed(self):
        day = date(2020, 1, 2)
        with self.assertRaisesRegex(ValueError, "duplicate quote key"):
            replay_long_call([q(day, cid="A"), q(day, cid="A", bid=9)], symbol="SPY")

    def test_entry_occurs_only_on_next_observation_and_uses_ask(self):
        d1, d2 = date(2020, 1, 2), date(2020, 1, 6)
        exp = date(2020, 9, 28)
        result = replay_long_call([q(d1, exp=exp), q(d2, exp=exp, bid=12, ask=13)], symbol="SPY")
        self.assertEqual(result.transactions[0]["date"], d2.isoformat())
        self.assertEqual(result.transactions[0]["signal_date"], d1.isoformat())
        self.assertEqual(result.transactions[0]["price"], 13)
        self.assertEqual(result.ledger[0].event, "FLAT")
        self.assertEqual(result.ledger[1].event, "BUY")
        self.assertEqual(result.final_cash, 3700)

    def test_exit_buffer_executes_next_observation_at_bid(self):
        d1, d2, d3 = date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6)
        exp = date(2020, 1, 3) + timedelta(days=30)
        entry = q(d1, exp=exp, cid="A", bid=10, ask=10.5)
        near_exit = q(d2, exp=exp, cid="A", bid=7, ask=8)
        exit_quote = q(d3, exp=exp, cid="A", bid=6, ask=7)
        replacement = q(d3, exp=d3 + timedelta(days=270), cid="B", bid=9, ask=9.5)
        result = replay_long_call([entry, near_exit, exit_quote, replacement], symbol="SPY", target_dte=31)
        sells = [t for t in result.transactions if t["action"] == "SELL"]
        self.assertEqual(len(sells), 1)
        self.assertEqual(sells[0]["date"], d3.isoformat())
        self.assertEqual(sells[0]["price"], 6)
        self.assertEqual(sells[0]["contract_id"], "A")

    def test_missing_entry_quote_is_rejected_then_retried(self):
        d1, d2, d3 = date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6)
        result = replay_long_call([q(d1, cid="A"), q(d2, cid="B"), q(d3, cid="B")], symbol="SPY")
        self.assertEqual(result.ledger[1].event, "ENTRY_REJECTED")
        self.assertEqual(result.transactions[0]["date"], d3.isoformat())


    def test_missing_exit_quote_retains_position_and_retries(self):
        d1, d2, d3, d4 = date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6), date(2020, 1, 7)
        exp = d2 + timedelta(days=30)
        result = replay_long_call([
            q(d1, exp=exp, cid="A"),
            q(d2, exp=exp, cid="A", bid=8, ask=9),
            q(d3, cid="B"),
            q(d4, exp=exp, cid="A", bid=6, ask=7),
        ], symbol="SPY", target_dte=31)
        self.assertEqual(result.ledger[2].event, "EXIT_REJECTED")
        self.assertEqual(result.ledger[2].contract_id, "A")
        sells = [txn for txn in result.transactions if txn["action"] == "SELL"]
        self.assertEqual(len(sells), 1)
        self.assertEqual(sells[0]["date"], d4.isoformat())
        self.assertEqual(sells[0]["price"], 6)

    def test_account_cash_gate_rejects_unaffordable_contract(self):
        d1, d2 = date(2020, 1, 2), date(2020, 1, 3)
        result = replay_long_call([q(d1, bid=60, ask=61), q(d2, bid=60, ask=61)],
                                  symbol="SPY", starting_cash=5000, enforce_account_cash=True)
        self.assertEqual(result.ledger[1].event, "ENTRY_REJECTED")
        self.assertEqual(result.final_cash, 5000)

    def test_invalid_terminal_mark_is_not_silently_cash(self):
        d1, d2, d3 = date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6)
        exp = date(2020, 10, 1)
        result = replay_long_call([
            q(d1, exp=exp, cid="A"),
            q(d2, exp=exp, cid="A"),
            q(d3, exp=exp, cid="A", bid=0, ask=1),
        ], symbol="SPY")
        self.assertFalse(result.final_mark_available)
        self.assertIsNone(result.final_equity)

    def test_diagnostics_identify_unresolved_expired_contract_and_last_mark(self):
        d1 = date(2020, 1, 2)
        expiration = d1 + timedelta(days=2)
        d2, d3, d4 = d1 + timedelta(days=1), d1 + timedelta(days=2), d1 + timedelta(days=3)
        result = replay_long_call([
            q(d1, exp=expiration, cid="A"),
            q(d2, exp=expiration, cid="A"),
            q(d3, exp=expiration, cid="A", bid=7, ask=8),
            q(d4, cid="B"),
        ], symbol="SPY", target_dte=2, exit_dte=0)
        diagnostics = calculate_diagnostics(result, starting_cash=5000)
        self.assertFalse(result.final_mark_available)
        self.assertTrue(diagnostics["terminal_position_open"])
        self.assertEqual(diagnostics["terminal_contract_id"], "A")
        self.assertEqual(diagnostics["terminal_dte"], -1)
        self.assertTrue(diagnostics["unresolved_expired_position"])
        self.assertEqual(diagnostics["days_past_expiration"], 1)
        self.assertEqual(diagnostics["last_valid_bid_mark_date"], d3.isoformat())
        self.assertEqual(diagnostics["days_since_last_valid_bid_mark"], 1)
        self.assertEqual(diagnostics["exit_rejected_observations"], 1)

    def test_cash_and_bid_mark_accounting(self):
        d1, d2 = date(2020, 1, 2), date(2020, 1, 3)
        exp = date(2020, 9, 28)
        result = replay_long_call([q(d1, exp=exp), q(d2, exp=exp, bid=12, ask=13)], symbol="SPY")
        self.assertEqual(result.ledger[1].cash, 3700)
        self.assertEqual(result.ledger[1].market_value, 1200)
        self.assertEqual(result.ledger[1].equity, 4900)

    def test_diagnostics_reconcile_cash_and_report_exposure(self):
        d1, d2 = date(2020, 1, 2), date(2020, 1, 6)
        exp = date(2020, 9, 28)
        result = replay_long_call(
            [q(d1, exp=exp), q(d2, exp=exp, bid=12, ask=13)],
            symbol="SPY",
        )
        diagnostics = calculate_diagnostics(result, starting_cash=5000)
        self.assertTrue(diagnostics["transaction_cash_reconciles"])
        self.assertEqual(diagnostics["transaction_cash_reconciliation_difference"], 0)
        self.assertTrue(diagnostics["all_fills_after_signal_observation"])
        self.assertEqual(diagnostics["completed_trades"], 0)
        self.assertEqual(diagnostics["observations_held"], 1)
        self.assertEqual(diagnostics["time_invested_observation_pct"], 50.0)
        self.assertTrue(diagnostics["max_drawdown_is_complete"])

