from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import duckdb

from research import audit_adaptive_leaps_alternate_source as audit
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
                  ('SPY080930C00148000','2008-09-02','2008-09-30',NULL,NULL),
                  ('OTHER','2008-08-13','2008-09-30',1,2)
            """)
            con.execute(f"COPY options TO '{path.as_posix()}' (FORMAT PARQUET)")
            con.close()

            report = inspect_contract_history(path, "SPY", "SPY080930C00148000")

            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["rows"], 5)
            self.assertEqual(report["first_row_date"], "2008-08-08")
            self.assertEqual(report["last_row_date"], "2008-09-02")
            self.assertEqual(report["last_positive_bid_date"], "2008-08-11")
            self.assertEqual(report["last_fully_valid_quote_date"], "2008-08-11")
            self.assertEqual(report["rows_after_last_positive_bid"], 3)
            self.assertEqual(report["days_from_last_positive_bid_to_expiration"], 50)
            self.assertEqual(report["exit_threshold_date"], "2008-08-31")
            self.assertEqual(report["rows_on_or_after_exit_threshold_through_expiration"], 1)
            self.assertEqual(report["positive_bid_rows_on_or_after_exit_threshold_through_expiration"], 0)
            self.assertEqual(report["last_observation_to_expiration_days"], 28)


    def test_compares_primary_and_alternate_bid_validity_by_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary_path = root / "primary.parquet"
            alternate_path = root / "alternate.parquet"
            con = duckdb.connect()
            con.execute("""
                CREATE TABLE primary_options (
                  contract_id VARCHAR, date DATE, expiration DATE,
                  bid DOUBLE, ask DOUBLE
                )
            """)
            con.execute("""
                INSERT INTO primary_options VALUES
                  ('TEST_CONTRACT','2020-01-02','2020-02-01',2,2.2),
                  ('TEST_CONTRACT','2020-01-03','2020-02-01',NULL,NULL)
            """)
            con.execute("""
                CREATE TABLE alternate_options (
                  contract_id VARCHAR, date DATE, expiration DATE,
                  bid DOUBLE, ask DOUBLE
                )
            """)
            con.execute("""
                INSERT INTO alternate_options VALUES
                  ('TEST_CONTRACT','2020-01-02','2020-02-01',2,2.2),
                  ('TEST_CONTRACT','2020-01-03','2020-02-01',1,1.2),
                  ('TEST_CONTRACT','2020-01-06','2020-02-01',0.5,0.7)
            """)
            con.execute(f"COPY primary_options TO '{primary_path.as_posix()}' (FORMAT PARQUET)")
            con.execute(f"COPY alternate_options TO '{alternate_path.as_posix()}' (FORMAT PARQUET)")
            con.close()

            report = audit.compare_contract_rows(primary_path, alternate_path, "TEST_CONTRACT")

            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["primary_row_count"], 2)
            self.assertEqual(report["alternate_row_count"], 3)
            self.assertEqual(report["primary_only_date_count"], 0)
            self.assertEqual(report["alternate_only_date_count"], 1)
            self.assertEqual(report["bid_validity_disagreement_count"], 1)
            self.assertEqual(report["bid_validity_disagreement_dates_sample"], ["2020-01-03"])
            self.assertFalse(report["exact_core_quote_history_match"])


if __name__ == "__main__":
    unittest.main()
