import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from paper_virtual_portfolio import new_state, state_json
from record_emergency_exit_latch import process


class RecordEmergencyExitLatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for portfolio in ("b0", "f75"):
            (self.root / f"{portfolio}_state.json").write_text(
                state_json(new_state(portfolio)) + "\n", encoding="utf-8")
        now = datetime.now(timezone.utc)
        stamp = now.isoformat()
        self.report_path = self.root / "report.json"
        self.report = {
            "status": "THRESHOLD_BREACHED", "threshold_breached": True,
            "symbol": "QQQ", "threshold_pct": "4.5",
            "session": now.date().isoformat(), "observed_at_utc": stamp,
            "trade_timestamp": stamp, "qqq_price": "95.5", "prior_close": "100",
        }
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_breach_latches_both_portfolios_and_is_idempotent(self):
        first = process(str(self.report_path), str(self.root))
        self.assertEqual(first["status"], "LATCH_ACTIVATED")
        self.assertFalse(first["orders_submitted"])
        for portfolio in ("b0", "f75"):
            state = json.loads((self.root / f"{portfolio}_state.json").read_text())
            self.assertTrue(state["emergency_exit_latch"]["active"])
            self.assertEqual(state["emergency_exit_latch"]["trigger_sha256"], first["trigger_sha256"])
        second = process(str(self.report_path), str(self.root))
        self.assertEqual(second["status"], "LATCH_ACTIVE_NO_CHANGE")
        self.assertEqual(second["trigger_sha256"], first["trigger_sha256"])

    def test_trough_moves_down_and_recovery_releases_both_flat_ledgers(self):
        first = process(str(self.report_path), str(self.root))
        self.assertEqual(first["status"], "LATCH_ACTIVATED")
        self.report.update({
            "status": "THRESHOLD_BREACHED", "threshold_breached": True,
            "qqq_price": "90", "prior_close": "100",
        })
        now = datetime.now(timezone.utc).isoformat()
        self.report["observed_at_utc"] = now
        self.report["trade_timestamp"] = now
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        lower = process(str(self.report_path), str(self.root))
        self.assertEqual(lower["status"], "LATCH_RECOVERY_TRACKED")
        self.assertEqual(lower["trough_price"], "90")
        self.assertEqual(lower["recovery_threshold"], "99.0000")

        self.report.update({
            "status": "MONITORING", "threshold_breached": False,
            "qqq_price": "99", "prior_close": "100",
        })
        now = datetime.now(timezone.utc).isoformat()
        self.report["observed_at_utc"] = now
        self.report["trade_timestamp"] = now
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        released = process(str(self.report_path), str(self.root))
        self.assertEqual(released["status"], "LATCH_RELEASED_AFTER_RECOVERY")
        self.assertTrue(released["both_portfolios_flat"])
        for portfolio in ("b0", "f75"):
            state = json.loads((self.root / f"{portfolio}_state.json").read_text())
            self.assertIsNone(state["emergency_exit_latch"])
            self.assertEqual(state["last_emergency_exit_latch"]["reentry_status"], "RECOVERY_CONFIRMED")

    def test_recovery_does_not_release_while_either_portfolio_has_position(self):
        process(str(self.report_path), str(self.root))
        f75_path = self.root / "f75_state.json"
        f75 = json.loads(f75_path.read_text())
        f75["qty"] = "1.000"
        f75_path.write_text(json.dumps(f75), encoding="utf-8")
        self.report.update({
            "status": "MONITORING", "threshold_breached": False,
            "qqq_price": "105.05", "prior_close": "100",
        })
        now = datetime.now(timezone.utc).isoformat()
        self.report["observed_at_utc"] = now
        self.report["trade_timestamp"] = now
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        result = process(str(self.report_path), str(self.root))
        self.assertNotEqual(result["status"], "LATCH_RELEASED_AFTER_RECOVERY")
        for portfolio in ("b0", "f75"):
            state = json.loads((self.root / f"{portfolio}_state.json").read_text())
            self.assertIsNotNone(state["emergency_exit_latch"])

    def test_non_trigger_report_does_not_mutate_ledger(self):
        before = {p: (self.root / f"{p}_state.json").read_text() for p in ("b0", "f75")}
        self.report.update({"status": "MONITORING", "threshold_breached": False,
                            "qqq_price": "96", "prior_close": "100"})
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        result = process(str(self.report_path), str(self.root))
        self.assertEqual(result["status"], "NO_TRIGGER")
        self.assertEqual(before, {p: (self.root / f"{p}_state.json").read_text() for p in ("b0", "f75")})

    def test_stale_trigger_report_fails_closed(self):
        self.report["observed_at_utc"] = "2020-01-01T00:00:00+00:00"
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        with self.assertRaisesRegex(Exception, "stale"):
            process(str(self.report_path), str(self.root))

    def test_wrong_threshold_and_weak_move_rejected(self):
        self.report["threshold_pct"] = "45"
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        with self.assertRaisesRegex(Exception, "threshold mismatch"):
            process(str(self.report_path), str(self.root))
        self.report["threshold_pct"] = "4.5"
        self.report["qqq_price"] = "95.51"
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        with self.assertRaisesRegex(Exception, "threshold flag does not match"):
            process(str(self.report_path), str(self.root))


if __name__ == "__main__":
    unittest.main(verbosity=2)
