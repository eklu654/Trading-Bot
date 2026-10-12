"""Synthetic chronology/accounting tests for the LEAPS replay engine."""
import unittest
from datetime import date, timedelta

from research.adaptive_leaps_lifecycle import OptionQuote
from research.adaptive_leaps_replay import replay_long_call


def q(day, *, exp=None, cid="A", bid=10.0, ask=10.5, delta=0.8, volume=10, oi=100):
    return OptionQuote(
        "SPY", day, exp or day + timedelta(days=270), 100, "call", delta,
        bid, ask, (bid + ask) / 2, volume, oi, cid,
    )


class ReplayTests(unittest.TestCase):
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

    def test_cash_and_bid_mark_accounting(self):
        d1, d2 = date(2020, 1, 2), date(2020, 1, 3)
        exp = date(2020, 9, 28)
        result = replay_long_call([q(d1, exp=exp), q(d2, exp=exp, bid=12, ask=13)], symbol="SPY")
        self.assertEqual(result.ledger[1].cash, 3700)
        self.assertEqual(result.ledger[1].market_value, 1200)
        self.assertEqual(result.ledger[1].equity, 4900)

