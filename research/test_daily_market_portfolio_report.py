import os
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import daily_market_portfolio_report as report


class ReportTests(unittest.TestCase):
    def test_market_slot_labels(self):
        tz = ZoneInfo("America/Chicago")
        with patch.object(report, "market_section", return_value=(["- SPY"], [])), \
             patch.object(report, "fetch_headlines", return_value=(["- headline"], [])), \
             patch.object(report, "portfolio_lines", return_value=(["- B0"], [])), \
             patch.object(report, "ledger_lines", return_value=["- ledger"]), \
             patch.object(report, "latest_executor_run", return_value="workflow ok"):
            subject, body = report.build_report(datetime(2026, 10, 14, 8, 30, tzinfo=tz))
        self.assertIn("Market open", subject)
        self.assertIn("headline", body)
        self.assertIn("workflow ok", body)

    def test_schedule_slot_is_identified_from_cron_not_start_time(self):
        tz = ZoneInfo("America/Chicago")
        now = datetime(2026, 10, 16, 12, 33, tzinfo=tz)
        title, reason = report.resolve_scheduled_slot(now, "schedule", "0 17 * * 1-5")
        self.assertEqual(title, "Midday")
        self.assertIn("33 minutes", reason)

    def test_wrong_dst_candidate_is_rejected(self):
        tz = ZoneInfo("America/Chicago")
        now = datetime(2026, 10, 16, 12, 5, tzinfo=tz)
        title, reason = report.resolve_scheduled_slot(now, "schedule", "0 18 * * 1-5")
        self.assertIsNone(title)
        self.assertIn("daylight-saving-time", reason)

    def test_overdue_slot_is_suppressed_instead_of_mislabelled(self):
        tz = ZoneInfo("America/Chicago")
        now = datetime(2026, 10, 16, 14, 49, tzinfo=tz)
        title, reason = report.resolve_scheduled_slot(now, "schedule", "0 17 * * 1-5")
        self.assertIsNone(title)
        self.assertIn("late", reason)

    def test_html_email_has_structured_headings_and_plain_text_fallback(self):
        body = "Trading Bot — Market open\nGenerated now\n\nMARKET SNAPSHOT\n- SPY: $1.00"
        html_body = report.render_html(body)
        self.assertIn("<h1", html_body)
        self.assertIn("MARKET SNAPSHOT", html_body)
        self.assertIn("<li", html_body)

    def test_email_fails_closed_without_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(report.ReportError):
                report.send_email("subject", "body")

    def test_broker_failure_is_explicit_not_inferred(self):
        with patch.object(report, "account_snapshot", side_effect=report.ReportError("unavailable")):
            lines, errors = report.portfolio_lines()
        self.assertTrue(any("UNAVAILABLE" in line for line in lines))
        self.assertEqual(len(errors), 2)

    def test_ledger_never_claims_broker_confirmation(self):
        with patch.object(report.Path, "exists", return_value=True), \
             patch.object(report.Path, "read_text", return_value='{"cash":5000,"equity":5000,"quantity":0}'):
            lines = report.ledger_lines()
        self.assertTrue(all("not broker-confirmed" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
