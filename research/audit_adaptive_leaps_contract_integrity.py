"""Validate LEAPS candidate contract identity and same-date underlying-price joins.

This is a data-integrity gate, not a trading or fillability backtest. It deliberately
fails if the underlying-price schema cannot be identified unambiguously.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for sym in ("spy", "qqq"):
        p.add_argument(f"--{sym}-source", required=True, help=f"{sym.upper()} option parquet glob")
        p.add_argument(f"--{sym}-underlying", required=True, help=f"{sym.upper()} underlying-price parquet")
    p.add_argument("--out-dir", default="artifacts/adaptive_leaps_integrity")
    return p.parse_args()


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def parquet_expr(path: str) -> str:
    return "read_parquet('" + path.replace("'", "''") + "', hive_partitioning=false)"


def choose(columns: set[str], candidates: tuple[str, ...], label: str, symbol: str) -> str:
    matches = [name for name in candidates if name.lower() in columns]
    if len(matches) != 1:
        raise ValueError(
            f"{symbol} underlying schema needs exactly one recognizable {label} column; "
            f"candidates={candidates}, found={matches}, columns={sorted(columns)}"
        )
    return matches[0]


def main() -> int:
    args = parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    reports = []
    details = {}

    for symbol in ("SPY", "QQQ"):
        source = getattr(args, f"{symbol.lower()}_source")
        underlying = getattr(args, f"{symbol.lower()}_underlying")
        options_expr, underlying_expr = parquet_expr(source), parquet_expr(underlying)

        opt_schema = con.execute(f"DESCRIBE SELECT * FROM {options_expr} LIMIT 0").fetchdf()
        opt_cols = {str(c).lower() for c in opt_schema["column_name"]}
        required = {"date", "expiration", "strike", "type", "delta", "bid", "ask", "mark"}
        missing = sorted(required - opt_cols)
        if missing:
            raise ValueError(f"{symbol} option source missing required columns: {missing}")

        und_schema = con.execute(f"DESCRIBE SELECT * FROM {underlying_expr} LIMIT 0").fetchdf()
        actual_und_cols = [str(c) for c in und_schema["column_name"]]
        und_cols = {c.lower() for c in actual_und_cols}
        date_col = choose(und_cols, ("date", "timestamp", "trading_date", "time"), "date", symbol)
        price_col = choose(
            und_cols,
            ("underlying_price", "close", "close_price", "price", "adj_close", "underlying_close"),
            "price", symbol,
        )
        # Restore the actual column spelling from the schema.
        date_col = next(c for c in actual_und_cols if c.lower() == date_col.lower())
        price_col = next(c for c in actual_und_cols if c.lower() == price_col.lower())

        sql = f"""
        WITH opt AS (
          SELECT CAST(date AS DATE) AS obs_date,
                 CAST(expiration AS DATE) AS expiration,
                 CAST(strike AS DOUBLE) AS strike,
                 lower(CAST(type AS VARCHAR)) AS option_type,
                 CAST(delta AS DOUBLE) AS delta,
                 CAST(bid AS DOUBLE) AS bid,
                 CAST(ask AS DOUBLE) AS ask,
                 CAST(mark AS DOUBLE) AS mark,
                 date_diff('day', CAST(date AS DATE), CAST(expiration AS DATE)) AS dte
          FROM {options_expr}
        ),
        candidate AS (
          SELECT * FROM opt
          WHERE option_type = 'call' AND dte BETWEEN 270 AND 539
            AND abs(delta) >= 0.60 AND abs(delta) < 0.85
        ),
        und AS (
          SELECT CAST({ident(date_col)} AS DATE) AS obs_date,
                 CAST({ident(price_col)} AS DOUBLE) AS underlying_price
          FROM {underlying_expr}
        ),
        und_day AS (
          SELECT obs_date, count(*) AS rows_on_date,
                 count(*) FILTER (WHERE underlying_price > 0) AS positive_price_rows,
                 max(underlying_price) FILTER (WHERE underlying_price > 0) AS price
          FROM und GROUP BY obs_date
        ),
        duplicates AS (
          SELECT obs_date, expiration, strike, option_type, count(*) AS n
          FROM candidate
          GROUP BY ALL HAVING count(*) > 1
        )
        SELECT '{symbol}' AS symbol, year(c.obs_date) AS year,
               count(*) AS candidate_rows,
               count(*) FILTER (WHERE c.bid > 0 AND c.ask >= c.bid AND c.mark > 0) AS valid_quote_rows,
               count(*) FILTER (WHERE u.obs_date IS NOT NULL) AS underlying_date_matched_rows,
               count(*) FILTER (WHERE u.positive_price_rows > 0) AS positive_underlying_join_rows,
               count(*) FILTER (WHERE u.rows_on_date > 1) AS rows_joining_duplicate_underlying_dates,
               count(*) FILTER (WHERE c.bid > 0 AND c.ask >= c.bid AND c.mark > 0
                                  AND u.positive_price_rows > 0) AS valid_quote_positive_underlying_rows
        FROM candidate c LEFT JOIN und_day u USING (obs_date)
        GROUP BY year(c.obs_date) ORDER BY year
        """
        rows = con.execute(sql).fetchdf()
        dup_sql = f"""
        WITH c AS (
          SELECT CAST(date AS DATE) AS obs_date, CAST(expiration AS DATE) AS expiration,
                 CAST(strike AS DOUBLE) AS strike, lower(CAST(type AS VARCHAR)) AS option_type,
                 date_diff('day', CAST(date AS DATE), CAST(expiration AS DATE)) AS dte,
                 CAST(delta AS DOUBLE) AS delta
          FROM {options_expr}
        )
        SELECT count(*) AS duplicate_key_groups,
               coalesce(sum(n - 1), 0) AS excess_duplicate_rows,
               coalesce(max(n), 1) AS max_rows_per_key
        FROM (
          SELECT count(*) AS n FROM c
          WHERE option_type='call' AND dte BETWEEN 270 AND 539
            AND abs(delta) >= 0.60 AND abs(delta) < 0.85
          GROUP BY obs_date, expiration, strike, option_type
          HAVING count(*) > 1
        )
        """
        dup = con.execute(dup_sql).fetchone()
        rows["underlying_match_pct"] = (
            rows["underlying_date_matched_rows"] / rows["candidate_rows"] * 100
        ).round(4)
        rows["positive_underlying_pct"] = (
            rows["positive_underlying_join_rows"] / rows["candidate_rows"] * 100
        ).round(4)
        reports.append(rows)
        details[symbol] = {
            "option_source": source,
            "underlying_source": underlying,
            "underlying_date_column": date_col,
            "underlying_price_column": price_col,
            "candidate_region": "calls, 270-539 DTE, abs(delta) 0.60-0.84",
            "duplicate_key_groups": int(dup[0]),
            "excess_duplicate_rows": int(dup[1]),
            "max_rows_per_key": int(dup[2]),
            "years": rows.to_dict(orient="records"),
        }

    import pandas as pd
    combined = pd.concat(reports, ignore_index=True)
    combined.to_csv(out / "integrity_by_year.csv", index=False)
    payload = {
        "report_type": "adaptive_leaps_contract_integrity",
        "status": "completed",
        "scope": "candidate-region identity and same-date underlying joins; not fills or P/L",
        "symbols": details,
        "interpretation_guardrails": [
            "Duplicate key findings are diagnostics; some duplicates may reflect source-specific schema or corrections and must be investigated.",
            "A date match is not proof of correct adjustment factors or an executable option quote.",
            "This gate does not model expiration, exercise, assignment, dividends, corporate actions, or fills.",
        ],
    }
    (out / "integrity_summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))
    print(f"Wrote {out / 'integrity_by_year.csv'} and {out / 'integrity_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
