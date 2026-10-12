"""Audit historical LEAPS-chain coverage before strategy backtesting.

Uses EOD option-chain rows only; this is a data-quality/coverage gate, not a P/L
backtest. The source is expected to provide symbol, date, expiration, strike,
type, bid, ask, mark, volume, open_interest, implied_volatility, and delta.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spy-source", required=True, help="SPY Parquet glob")
    parser.add_argument("--qqq-source", required=True, help="QQQ Parquet glob")
    parser.add_argument("--out-dir", default="artifacts/adaptive_leaps_coverage")
    return parser.parse_args()


def quote_sql(source: str) -> str:
    return "read_parquet('" + source.replace("'", "''") + "', hive_partitioning=false)"


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    reports: list[pd.DataFrame] = []
    summaries: dict[str, object] = {}

    for symbol, source in (("SPY", args.spy_source), ("QQQ", args.qqq_source)):
        # Fail explicitly if a glob is empty; silent empty output would be misleading.
        try:
            schema = con.execute(f"DESCRIBE SELECT * FROM {quote_sql(source)} LIMIT 0").fetchdf()
        except Exception as exc:
            raise RuntimeError(f"Cannot read {symbol} source {source!r}: {exc}") from exc
        required = {
            "date", "expiration", "strike", "type", "bid", "ask", "mark",
            "volume", "open_interest", "delta", "implied_volatility",
        }
        available = set(schema["column_name"].str.lower())
        missing = sorted(required - available)
        if missing:
            raise ValueError(f"{symbol} source missing required columns: {missing}")

        source_expr = quote_sql(source)
        rows = con.execute(f"""
            WITH base AS (
                SELECT
                    CAST(date AS DATE) AS obs_date,
                    CAST(expiration AS DATE) AS expiration,
                    lower(CAST(type AS VARCHAR)) AS option_type,
                    CAST(strike AS DOUBLE) AS strike,
                    CAST(bid AS DOUBLE) AS bid,
                    CAST(ask AS DOUBLE) AS ask,
                    CAST(mark AS DOUBLE) AS mark,
                    CAST(volume AS DOUBLE) AS volume,
                    CAST(open_interest AS DOUBLE) AS open_interest,
                    CAST(delta AS DOUBLE) AS delta,
                    CAST(implied_volatility AS DOUBLE) AS iv,
                    date_diff('day', CAST(date AS DATE), CAST(expiration AS DATE)) AS dte
                FROM {source_expr}
            ),
            classified AS (
                SELECT *,
                    CASE
                      WHEN dte BETWEEN 0 AND 90 THEN '000-090'
                      WHEN dte BETWEEN 91 AND 180 THEN '091-180'
                      WHEN dte BETWEEN 181 AND 269 THEN '181-269'
                      WHEN dte BETWEEN 270 AND 364 THEN '270-364'
                      WHEN dte BETWEEN 365 AND 539 THEN '365-539'
                      WHEN dte BETWEEN 540 AND 730 THEN '540-730'
                      WHEN dte > 730 THEN '731+'
                      ELSE 'INVALID'
                    END AS dte_bucket,
                    CASE
                      WHEN abs(delta) < 0.60 THEN '<0.60'
                      WHEN abs(delta) < 0.75 THEN '0.60-0.74'
                      WHEN abs(delta) < 0.85 THEN '0.75-0.84'
                      WHEN abs(delta) <= 1.00 THEN '0.85-1.00'
                      ELSE 'INVALID'
                    END AS abs_delta_bucket,
                    (bid > 0 AND ask >= bid AND mark > 0) AS valid_quote,
                    (volume > 0 OR open_interest > 0) AS has_activity
                FROM base
            )
            SELECT
                '{symbol}' AS symbol,
                year(obs_date) AS year,
                dte_bucket,
                option_type,
                abs_delta_bucket,
                count(*) AS contract_day_rows,
                count(DISTINCT obs_date) AS observation_dates,
                count(*) FILTER (WHERE valid_quote) AS valid_quote_rows,
                count(*) FILTER (WHERE valid_quote AND has_activity) AS valid_quote_active_rows,
                count(*) FILTER (WHERE valid_quote AND has_activity AND iv > 0) AS usable_iv_rows,
                count(*) FILTER (WHERE bid = 0 OR ask = 0 OR mark = 0) AS any_zero_quote_rows,\n                count(*) FILTER (WHERE bid IS NULL OR ask IS NULL OR mark IS NULL) AS missing_quote_rows,
                count(*) FILTER (WHERE ask < bid) AS crossed_quote_rows,
                count(*) FILTER (WHERE valid_quote IS NOT TRUE) AS invalid_quote_rows,
                median((ask - bid) / NULLIF((ask + bid) / 2.0, 0))
                    FILTER (WHERE valid_quote AND (ask + bid) > 0) AS median_relative_spread,
                median(dte) AS median_dte,
                min(obs_date) AS first_observation,
                max(obs_date) AS last_observation
            FROM classified
            GROUP BY ALL
            ORDER BY year, dte_bucket, option_type, abs_delta_bucket
        """).fetchdf()
        reports.append(rows)
        total_rows = int(rows["contract_day_rows"].sum()) if not rows.empty else 0
        summaries[symbol] = {
            "source": source,
            "rows": total_rows,
            "years": sorted(int(y) for y in rows["year"].dropna().unique()),
            "dte_270_plus_rows": int(rows.loc[rows["dte_bucket"].isin(["270-364", "365-539", "540-730", "731+"]), "contract_day_rows"].sum()) if not rows.empty else 0,
            "dte_270_plus_valid_active_rows": int(rows.loc[rows["dte_bucket"].isin(["270-364", "365-539", "540-730", "731+"]), "valid_quote_active_rows"].sum()) if not rows.empty else 0,
            "note": "Counts are EOD contract-day observations, not unique contracts or executable fills."
        }

    combined = pd.concat(reports, ignore_index=True) if reports else pd.DataFrame()
    csv_path = out_dir / "coverage_by_year_dte_delta.csv"
    json_path = out_dir / "summary.json"
    combined.to_csv(csv_path, index=False)
    payload = {
        "report_type": "adaptive_leaps_options_data_coverage",
        "source_observation": "EOD 16:00 ET snapshots",
        "primary_quote_quality_rule": "bid > 0, ask >= bid, mark > 0",
        "activity_rule": "volume > 0 OR open_interest > 0",
        "symbols": summaries,
        "limitations": [
            "Coverage counts do not prove fillability or reliable assignment modeling.",
            "EOD data cannot reconstruct intraday quote paths or order priority.",
            "DTE coverage can be biased near dataset start/end; inspect years separately."
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
