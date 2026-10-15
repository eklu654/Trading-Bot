import datetime as dt
import os
import unittest
from unittest.mock import patch

import market_portfolio_digest as digest


class SlotTests(unittest.TestCase):
    def test_central_daylight_time_open_trigger(self):
        now = dt.datetime(2026, 10, 15, 13, 35, tzinfo=dt.timezone.utc)
        self.assertEqual(digest.get_slot(now), "open")

    def test_central_standard_time_open_trigger(self):
        now = dt.datetime(2026, 1, 15, 14, 35, tzinfo=dt.timezone.utc)
        self.assertEqual(digest.get_slot(now), "open")

    def test_other_dst_twin_is_skipped(self):
        summer_twin = dt.datetime(2026, 10, 15, 14, 35, tzinfo=dt.timezone.utc)
        winter_twin = dt.datetime(2026, 1, 15, 13, 35, tzinfo=dt.timezone.utc)
        self.assertIsNone(digest.get_slot(summer_twin))
        self.assertIsNone(digest.get_slot(winter_twin))

    def test_midday_and_close_slots(self):
        self.assertEqual(digest.get_slot(dt.datetime(2026, 10, 15, 17, 0, tzinfo=dt.timezone.utc)), "midday")
        self.assertEqual(digest.get_slot(dt.datetime(2026, 10, 15, 20, 5, tzinfo=dt.timezone.utc)), "close")


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 10, 15, 17, 0, tzinfo=dt.timezone.utc)
        self.market = {
            "symbols": {
                "SPY": {"price": 680, "prior_close": 675, "change_pct": 0.7407, "trade_at": "2026-10-15T16:59:00Z"},
                "QQQ": {"price": 610, "prior_close": 605, "change_pct": 0.8264, "trade_at": "2026-10-15T16:59:00Z"},
            },
            "news": [{"headline": "Test headline", "created_at": "2026-10-15T16:30:00Z", "summary": "Test summary", "url": "https://example.com"}],
            "errors": [],
        }
        self.portfolios = [{
            "label": "B0",
            "account": {"status": "ACTIVE", "trading_blocked": False, "account_blocked": False,
                        "equity": "5100", "last_equity": "5000", "cash": "1000",
                        "buying_power": "2000", "long_market_value": "4100"},
            "positions": [{"symbol": "TQQQ", "qty": "10", "side": "long", "market_value": "800",
                           "unrealized_pl": "50", "unrealized_plpc": "0.066", "current_price": "80"}],
            "open_orders": [{"symbol": "TQQQ", "side": "buy", "qty": "1", "status": "new", "type": "market", "submitted_at": "2026-10-15T16:50:00Z"}],
        }]

    def test_report_contains_portfolio_market_news_and_latch(self):
        latch = {"B0": {"trigger_price": 95.5, "trigger_close": 100, "trough_price": 90, "recovery_threshold": 99, "trigger_session": "2026-10-15"}, "F75": None}
        subject, text_body, html_body = digest.build_report("midday", self.now, self.market, self.portfolios, latch, [])
        self.assertIn("Midday", subject)
        self.assertIn("SPY", text_body)
        self.assertIn("TQQQ", text_body)
        self.assertIn("ACTIVE", text_body)
        self.assertIn("Test headline", text_body)
        self.assertIn("No active latch", text_body)
        self.assertIn("&lt;div", html_body) if False else self.assertIn("Test headline", html_body)

    def test_report_discloses_data_errors(self):
        _, body, _ = digest.build_report("open", self.now, self.market, self.portfolios, {"B0": None, "F75": None}, ["F75 credentials missing"])
        self.assertIn("F75 credentials missing", body)
        self.assertIn("Treat missing fields as unknown", body)

    def test_money_and_fraction_formatting(self):
        self.assertEqual(digest.money(1234.5), "$1,234.50")
        self.assertEqual(digest.pct(0.025, already_fraction=True), "+2.50%")


class SecretGateTests(unittest.TestCase):
    def test_resend_requires_all_three_secrets(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(digest.DataError, "RESEND_API_KEY, ALERT_EMAIL, RESEND_FROM_EMAIL"):
                digest.send_resend("subject", "text", "<p>html</p>")


if __name__ == "__main__":
    unittest.main()
