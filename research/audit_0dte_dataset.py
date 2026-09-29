"""Audit historical SPY option data for 0DTE research feasibility.

This is intentionally an audit, not a 0DTE backtest. The current external
dataset is known to be daily-granularity in the existing replay. True 0DTE
management requires intraday timestamps/quotes, so this script measures what
same-day-expiration data exists and records whether the source can support
intraday entry/exit reconstruction without inventing prices.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "options001_0dte_dataset_audit.csv"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--options-source", required=True)
    args = p.parse_args()

    source = args.options_source.replace("'", "''")
    relation = f"read_parquet('{source}', hive_partitioning=false)"
    con = duckdb.connect()

    schema = con.execute(f"DESCRIBE SELECT * FROM {relation} LIMIT 1").fetchdf()
    columns = [str(x) for x in schema["column_name"].tolist()]
    timestamp_like = [c for c in columns if any(k in c.lower() for k in ("time", "timestamp", "datetime"))]

    query = f"""
        SELECT
            CAST(date AS DATE) AS trade_date,
            CAST(expiration AS DATE) AS expiration,
            COUNT(*) AS rows
        FROM {relation}
        WHERE CAST(date AS DATE) = CAST(expiration AS DATE)
        GROUP BY 1, 2
        ORDER BY 1
    """
    daily = con.execute(query).fetchdf()

    total_rows = int(daily["rows"].sum()) if not daily.empty else 0
    trading_days = int(len(daily))
    first_date = str(daily["trade_date"].min().date()) if not daily.empty else ""
    last_date = str(daily["trade_date"].max().date()) if not daily.empty else ""

    result = pd.DataFrame([{
        "source": args.options_source,
        "dataset_columns": ",".join(columns),
        "timestamp_like_columns": ",".join(timestamp_like),
        "has_intraday_timestamp_field": bool(timestamp_like),
        "zero_dte_rows": total_rows,
        "zero_dte_trading_days": trading_days,
        "zero_dte_first_date": first_date,
        "zero_dte_last_date": last_date,
        "true_intraday_replay_supported": bool(timestamp_like),
        "status": "READY_FOR_INTRADAY_REPLAY" if timestamp_like else "INSUFFICIENT_FOR_INTRADAY_REPLAY",
    }])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
