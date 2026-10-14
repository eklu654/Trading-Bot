from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import duckdb

from research.audit_adaptive_leaps_alternate_source import inspect_contract_history


class AlternateSourceContractAuditTests(unittest.TestCase):
    def test_reports_history_after_last_positive_bid_without_imputation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alternate.parquet"
            con = duckdb.connect()
            con.execute("""
                CREATE TABLE options (
                  contract_symbol VARCHAR, date DATE, expiration DATE,
                  bid DOUBLE, ask DOUBLE
                )
            """)
            con.execute("""
                INSERT INTO options VALUES
                  ('SPY080930C00148000','2008-08-08','2008-09-30',2.1,2.3),
                  ('SPY080930C00148000','2008-08-11','2008-09-30',2.0,2.2),
                  ('SPY080930C00148000','2008-08-12','2008-09-30',NULL,NULL),
                  ('SPY080930C00148000','2008-08-13','2008-09-30',0,0),
                  ('OTHER','2008-08-13','2008-09-30',1,2)
            """)
            con.execute(f"COPY options TO '{path.as_posix()}' (FORMAT PARQUET)")
            con.close()

            report = inspect_contract_history(path, "SPY", "SPY080930C00148000")

            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["rows"], 4)
            self.assertEqual(report["first_row_date"], "2008-08-08")
            self.assertEqual(report["last_row_date"], "2008-08-13")
            self.assertEqual(report["last_positive_bid_date"], "2008-08-11")
            self.assertEqual(report["last_fully_valid_quote_date"], "2008-08-11")
            self.assertEqual(report["rows_after_last_positive_bid"], 2)
            self.assertEqual(report["days_from_last_positive_bid_to_expiration"], 50)


if __name__ == "__main__":
    unittest.main()
