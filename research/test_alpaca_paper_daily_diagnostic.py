import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from alpaca_paper_daily_diagnostic import read_latest_signal, DiagnosticBlocked

class ReadOnlySignalLedgerTests(unittest.TestCase):
    def write_fixture(self, directory, session="2026-10-09", b0="1.0", f75="0.75"):
        ledger = Path(directory) / "ledger.csv"
        state_path = Path(directory) / "state.json"
        columns = ["date", "source_canonical_sha256", "b0_signal_close", "f75_signal_close", "b0_equity_0bps", "f75_equity_0bps"]
        rows = [
            {"date": "2026-10-08", "source_canonical_sha256": "source-hash", "b0_signal_close": "1.0", "f75_signal_close": "1.0", "b0_equity_0bps": "5000", "f75_equity_0bps": "5000"},
            {"date": session, "source_canonical_sha256": "source-hash", "b0_signal_close": b0, "f75_signal_close": f75, "b0_equity_0bps": "4973.0786567", "f75_equity_0bps": "4973.0786567"},
        ]
        with ledger.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        state = {"ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
                 "mode": "SHADOW_ONLY_NO_ORDERS", "last_observation": session,
                 "canonical_input_sha256": "source-hash", "ledger_rows_total": len(rows)}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        return ledger, state_path

    def test_reads_latest_completed_session_signal(self):
        with tempfile.TemporaryDirectory() as d:
            ledger, state = self.write_fixture(d)
            session, b0, f75, digest = read_latest_signal(
                ledger, state, datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc))
            self.assertEqual((session, str(b0), str(f75), digest),
                             ("2026-10-09", "1.0", "0.75", "source-hash"))

    def test_rejects_tampered_ledger_hash(self):
        with tempfile.TemporaryDirectory() as d:
            ledger, state = self.write_fixture(d)
            ledger.write_text(ledger.read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DiagnosticBlocked, "hash"):
                read_latest_signal(ledger, state, datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc))

    def test_rejects_current_session_row(self):
        with tempfile.TemporaryDirectory() as d:
            ledger, state = self.write_fixture(d, session="2026-10-12")
            with self.assertRaisesRegex(DiagnosticBlocked, "current-session"):
                read_latest_signal(ledger, state, datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc))

    def test_rejects_f75_when_b0_flat(self):
        with tempfile.TemporaryDirectory() as d:
            ledger, state = self.write_fixture(d, b0="0.0", f75="0.75")
            with self.assertRaisesRegex(DiagnosticBlocked, "B0 eligibility"):
                read_latest_signal(ledger, state, datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc))

    def test_rejects_row_count_manifest_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            ledger, state = self.write_fixture(d)
            data = json.loads(state.read_text())
            data["ledger_rows_total"] = 3
            state.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(DiagnosticBlocked, "row count"):
                read_latest_signal(ledger, state, datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc))

if __name__ == "__main__":
    unittest.main()
