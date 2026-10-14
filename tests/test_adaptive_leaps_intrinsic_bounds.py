from __future__ import annotations

import unittest
from pathlib import Path

import duckdb

from research.audit_adaptive_leaps_intrinsic_bounds import audit_cohort, audit_one


class IntrinsicBoundDiagnosticTests(unittest.TestCase):
    def test_reports_raw_and_adjusted_price_basis_without_imputing(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            options_path = root / "qqq.parquet"
            underlying_path = root / "underlying.parquet"
            con = duckdb.connect()
            con.execute(
                """
                CREATE TABLE options AS SELECT
                  'QQQ140920C00077000' AS contract_id,
                  DATE '2014-03-11' AS date,
                  DATE '2014-09-20' AS expiration,
                  77.0 AS strike,
                  'call' AS type,
                  6.70 AS bid,
                  7.67 AS ask
                """
            )
            con.execute(f"COPY options TO '{options_path}' (FORMAT PARQUET)")
            con.execute(
                """
                CREATE TABLE underlying AS SELECT
                  DATE '2014-03-11' AS date,
                  'QQQ' AS symbol,
                  90.22 AS close,
                  81.88 AS adj_close
                """
            )
            con.execute(f"COPY underlying TO '{underlying_path}' (FORMAT PARQUET)")
            report = audit_one(con, "QQQ", str(options_path), str(underlying_path))
            con.close()

            self.assertEqual(report["underlying_price_fields_checked"], ["close", "adj_close"])
            day = next(x for x in report["check_dates"] if x["date"] == "2014-03-11")
            self.assertEqual(day["option_rows_found"], 1)
            quote = day["quotes"][0]
            raw = quote["intrinsic_checks_by_underlying_field"]["close"]
            adjusted = quote["intrinsic_checks_by_underlying_field"]["adj_close"]
            self.assertAlmostEqual(raw["intrinsic_value"], 13.22)
            self.assertTrue(raw["ask_below_intrinsic_by_more_than_0_01"])
            self.assertAlmostEqual(adjusted["intrinsic_value"], 4.88)
            self.assertFalse(adjusted["ask_below_intrinsic_by_more_than_0_01"])
            self.assertIn("adjustment bases are verified", report["interpretation_guardrail"])


    def test_cohort_summary_counts_raw_close_violations_separately(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            options_path = root / "qqq_cohort.parquet"
            underlying_path = root / "underlying.parquet"
            con = duckdb.connect()
            con.execute(
                """
                CREATE TABLE options AS
                SELECT 'QQQ140920C00077000' AS contract_id,
                       DATE '2014-03-11' AS date, DATE '2014-09-20' AS expiration,
                       77.0 AS strike, 'call' AS type, 6.70 AS bid, 7.67 AS ask
                UNION ALL
                SELECT 'QQQ140920C00095000', DATE '2014-03-11', DATE '2014-09-20',
                       95.0, 'call', 1.00, 2.00
                UNION ALL
                SELECT 'QQQ140920P00080000', DATE '2014-03-11', DATE '2014-09-20',
                       80.0, 'put', 10.00, 12.00
                """
            )
            con.execute(f"COPY options TO '{options_path}' (FORMAT PARQUET)")
            con.execute(
                """
                CREATE TABLE underlying AS SELECT
                  DATE '2014-03-11' AS date, 'QQQ' AS symbol,
                  90.22 AS close, 81.88 AS adj_close
                """
            )
            con.execute(f"COPY underlying TO '{underlying_path}' (FORMAT PARQUET)")
            report = audit_cohort(con, "QQQ", str(options_path), str(underlying_path))
            con.close()

            self.assertEqual(report["option_rows_in_expiration_year"], 3)
            raw = report["counts_by_underlying_field"]["close"]
            adjusted = report["counts_by_underlying_field"]["adj_close"]
            self.assertEqual(raw["ask_below_intrinsic_rows"], 1)
            self.assertEqual(raw["bid_below_intrinsic_rows"], 1)
            self.assertEqual(adjusted["ask_below_intrinsic_rows"], 0)
            self.assertEqual(adjusted["bid_below_intrinsic_rows"], 0)
            self.assertLess(raw["ask_to_intrinsic_ratio_quantiles_for_itm_quotes"]["p50"], 0.75)
            self.assertGreater(adjusted["ask_to_intrinsic_ratio_quantiles_for_itm_quotes"]["p50"], 1.0)
            self.assertEqual(raw["sample_ask_violations"][0]["contract_id"], "QQQ140920C00077000")


if __name__ == "__main__":
    unittest.main()
