"""Cross-check flagged option-history cutoffs against underlying trading dates.

This diagnostic tests whether contract-specific history ends while the underlying
source and the symbol's option-chain files continue trading. It does not infer
that a missing quote was executable, and it does not alter replay fills or P/L.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


FLAGGED = {
    "SPY": "SPY080930C00148000",
    "QQQ": "QQQ140920C00077000",
}


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, choices=("SPY", "QQQ"))
    parser.add_argument("--source", required=True, help="Option-chain Parquet path/glob")
    parser.add_argument("--underlying", required=True, help="Underlying-price Parquet path")
    parser.add_argument("--contract-id", default="", help="Override the known flagged contract ID")
    parser.add_argument("--out-dir", default="artifacts/adaptive_leaps_source_discontinuity")
    args = parser.parse_args()

    symbol = args.symbol
    contract_id = args.contract_id.strip() or FLAGGED[symbol]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    option_expr = "read_parquet(" + sql_string(args.source) + ", hive_partitioning=false)"
    underlying_expr = "read_parquet(" + sql_string(args.underlying) + ", hive_partitioning=false)"

    und_schema = con.execute(f"DESCRIBE SELECT * FROM {underlying_expr} LIMIT 0").fetchdf()
    actual_cols = [str(c) for c in und_schema["column_name"]]
    lower_to_actual = {c.lower(): c for c in actual_cols}
    date_candidates = ("date", "timestamp", "trading_date", "time")
    price_candidates = ("underlying_price", "close", "close_price", "price", "adj_close", "underlying_close")
    date_col = next((lower_to_actual[c] for c in date_candidates if c in lower_to_actual), None)
    price_col = next((lower_to_actual[c] for c in price_candidates if c in lower_to_actual), None)
    if date_col is None or price_col is None:
        raise ValueError(f"Unrecognized underlying schema: {actual_cols}")

    sql = f"""
    WITH opt AS (
      SELECT CAST(date AS DATE) AS obs_date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             lower(CAST(type AS VARCHAR)) AS option_type
      FROM {option_expr}
      WHERE contract_id IS NOT NULL
    ),
    target AS (
      SELECT contract_id, min(expiration) AS expiration,
             min(obs_date) AS first_option_row,
             max(obs_date) FILTER (WHERE obs_date <= min_expiration) AS last_option_row
      FROM (
        SELECT *, min(expiration) OVER (PARTITION BY contract_id) AS min_expiration
        FROM opt WHERE contract_id = {sql_string(contract_id)}
      ) t
      GROUP BY contract_id
    ),
    contract_stats AS (
      SELECT min(o.obs_date) AS first_option_row,
             max(o.obs_date) AS last_option_row,
             min(o.expiration) AS expiration,
             count(*) AS contract_rows,
             count(*) FILTER (WHERE o.bid > 0 AND o.ask >= o.bid) AS valid_bid_rows,
             max(o.obs_date) FILTER (WHERE o.bid > 0 AND o.ask >= o.bid) AS last_valid_bid_date
      FROM opt o
      WHERE o.contract_id = {sql_string(contract_id)}
        AND o.obs_date <= o.expiration
    ),
    und AS (
      SELECT DISTINCT CAST({ident(date_col)} AS DATE) AS obs_date,
             max(CAST({ident(price_col)} AS DOUBLE)) AS price
      FROM {underlying_expr}
      GROUP BY 1
    ),
    option_sessions AS (SELECT DISTINCT obs_date FROM opt),
    coverage AS (
      SELECT max(obs_date) AS option_source_end_date FROM opt
    ),
    session_stats AS (
      SELECT count(*) FILTER (WHERE u.price > 0) AS underlying_sessions_after_last_option_row,
             min(u.obs_date) FILTER (WHERE u.price > 0) AS first_underlying_session_after_last_option_row,
             max(u.obs_date) FILTER (WHERE u.price > 0) AS last_underlying_session_through_expiry,
             count(*) FILTER (WHERE u.price > 0 AND os.obs_date IS NOT NULL) AS sessions_with_symbol_option_rows,
             count(*) FILTER (WHERE u.price > 0 AND os.obs_date IS NULL) AS sessions_without_symbol_option_rows
      FROM contract_stats c
      JOIN und u ON u.obs_date > c.last_option_row AND u.obs_date <= c.expiration
      LEFT JOIN option_sessions os USING (obs_date)
    )
    SELECT {sql_string(symbol)} AS symbol, {sql_string(contract_id)} AS contract_id,
           c.first_option_row, c.last_option_row, c.last_valid_bid_date, c.expiration,
           c.contract_rows, c.valid_bid_rows,
           date_diff('day', c.last_valid_bid_date, c.expiration) AS days_from_last_bid_to_expiry,
           date_diff('day', c.last_option_row, c.expiration) AS days_from_last_row_to_expiry,
           cv.option_source_end_date,
           s.underlying_sessions_after_last_option_row,
           s.first_underlying_session_after_last_option_row,
           s.last_underlying_session_through_expiry,
           s.sessions_with_symbol_option_rows,
           s.sessions_without_symbol_option_rows
    FROM contract_stats c CROSS JOIN coverage cv CROSS JOIN session_stats s
    """
    result = con.execute(sql).fetchdf()
    if result.empty:
        raise ValueError(f"No source rows found for contract {contract_id}")
    record = result.iloc[0].to_dict()
    for key, value in list(record.items()):
        if hasattr(value, "isoformat"):
            record[key] = value.isoformat()
        elif value != value:
            record[key] = None
        elif hasattr(value, "item"):
            record[key] = value.item()
    record["interpretation"] = (
        "Underlying trading dates after the last contract row indicate a contract-history cutoff; "
        "they do not establish a valid or executable option bid."
    )
    csv_path = out / f"{symbol.lower()}_source_discontinuity.csv"
    result.to_csv(csv_path, index=False)
    json_path = out / f"{symbol.lower()}_source_discontinuity.json"
    json_path.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, default=str))
    print(f"Wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
