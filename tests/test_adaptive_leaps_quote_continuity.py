"""Synthetic tests for the LEAPS quote-continuity audit."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb

from research import audit_adaptive_leaps_quote_continuity as audit


class QuoteContinuityAuditTests(unittest.TestCase):
    def test_reports_last_valid_bid_and_post_quote_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parquet = root / "synthetic_options.parquet"
            out_dir = root / "out"
            con = duckdb.connect()
            con.execute("""
                CREATE TABLE options (
                    date DATE, expiration DATE, delta DOUBLE, bid DOUBLE, ask DOUBLE,
                    mark DOUBLE, volume DOUBLE, open_interest DOUBLE, type VARCHAR,
                    contract_id VARCHAR, strike DOUBLE
                )
            """)
            con.execute("""
                INSERT INTO options VALUES
                ('2026-12-04', '2027-09-30', 0.80, 1.00, 1.10, 1.05, 10, 100, 'call', 'TEST270C', 100),
                ('2027-08-01', '2027-09-30', 0.25, 0.20, 0.30, 0.25, 1, 10, 'call', 'TEST270C', 100),
                ('2027-08-11', '2027-09-30', 0.10, 0.00, 0.00, 0.00, 0, 0, 'call', 'TEST270C', 100),
                ('2027-09-01', '2027-09-30', 0.01, 0.00, 0.00, 0.00, 0, 0, 'call', 'TEST270C', 100),
                ('2027-12-04', '2028-09-30', 0.80, 1.00, 1.10, 1.05, 10, 100, 'call', 'CENSORED', 100)
            """)
            con.execute(f"COPY options TO '{parquet.as_posix()}' (FORMAT PARQUET)")
            con.close()

            argv = [
                "audit_adaptive_leaps_quote_continuity",
                "--symbol", "SPY",
                "--source", str(parquet),
                "--out-dir", str(out_dir),
                "--contract-ids", "TEST270C",
            ]
            with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(), 0)

            report = json.loads((out_dir / "spy_quote_continuity_summary.json").read_text())
            self.assertEqual(report["cohort"]["eligible_contracts"], 2)
            self.assertEqual(report["cohort"]["fully_observed_to_expiration_contracts"], 1)
            self.assertEqual(report["cohort"]["right_censored_contracts_expiration_after_source_coverage"], 1)
            self.assertEqual(report["cohort"]["fully_observed_contracts_last_valid_bid_more_than_30_days_before_expiration"], 1)
            flagged = report["flagged_contracts"]
            self.assertEqual(len(flagged), 1)
            self.assertEqual(flagged[0]["contract_id"], "TEST270C")
            self.assertEqual(flagged[0]["dte_at_last_valid_bid"], 60)
            self.assertEqual(flagged[0]["rows_after_last_valid_bid"], 2)
            self.assertEqual(flagged[0]["history_rows_present"], 4)
            self.assertEqual(flagged[0]["valid_bid_rows"], 2)


if __name__ == "__main__":
    unittest.main()
