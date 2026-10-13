from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import duckdb

from research import audit_adaptive_leaps_source_discontinuity as audit


class SourceDiscontinuityAuditTests(unittest.TestCase):
    def test_reports_underlying_sessions_after_contract_history_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            options_path = root / "options.parquet"
            underlying_path = root / "underlying.parquet"
            out = root / "out"
            con = duckdb.connect()
            con.execute("""
                CREATE TABLE options (
                  date DATE, expiration DATE, contract_id VARCHAR,
                  bid DOUBLE, ask DOUBLE, type VARCHAR
                )
            """)
            con.execute("""
                INSERT INTO options VALUES
                  ('2020-01-02','2020-01-10','TEST_CONTRACT',2,3,'call'),
                  ('2020-01-03','2020-01-10','TEST_CONTRACT',2,3,'call'),
                  ('2020-01-06','2020-01-10','OTHER_CONTRACT',1,2,'call'),
                  ('2020-01-07','2020-01-10','OTHER_CONTRACT',1,2,'call'),
                  ('2020-01-08','2020-01-10','OTHER_CONTRACT',1,2,'call'),
                  ('2020-01-09','2020-01-10','OTHER_CONTRACT',1,2,'call'),
                  ('2020-01-10','2020-01-10','OTHER_CONTRACT',1,2,'call')
            """)
            con.execute("""
                CREATE TABLE underlying (date DATE, close DOUBLE)
            """)
            con.execute("""
                INSERT INTO underlying VALUES
                  ('2020-01-02',100),('2020-01-03',101),('2020-01-06',102),
                  ('2020-01-07',103),('2020-01-08',104),('2020-01-09',105),
                  ('2020-01-10',106)
            """)
            con.execute(f"COPY options TO '{options_path.as_posix()}' (FORMAT PARQUET)")
            con.execute(f"COPY underlying TO '{underlying_path.as_posix()}' (FORMAT PARQUET)")
            con.close()

            argv = [
                "audit_adaptive_leaps_source_discontinuity",
                "--symbol", "SPY",
                "--contract-id", "TEST_CONTRACT",
                "--source", str(options_path),
                "--underlying", str(underlying_path),
                "--out-dir", str(out),
            ]
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(audit.main(), 0)

            report = json.loads((out / "spy_source_discontinuity.json").read_text())
            self.assertEqual(report["last_option_row"], "2020-01-03")
            self.assertEqual(report["last_valid_bid_date"], "2020-01-03")
            self.assertEqual(report["underlying_sessions_after_last_option_row"], 5)
            self.assertEqual(report["sessions_with_symbol_option_rows"], 5)
            self.assertEqual(report["sessions_without_symbol_option_rows"], 0)


if __name__ == "__main__":
    unittest.main()
