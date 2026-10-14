"""Compare preserved option quotes with intrinsic-value lower bounds.

This is a diagnostic, not an execution or accounting policy. It deliberately
reports every available underlying price field because the dataset's public
documentation does not specify whether historical OHLCV is raw or adjusted.
A lower-bound violation is not interpreted as a bad executable quote until the
underlying/option price basis is established.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


FLAGGED = {
    "SPY": {
        "contract_id": "SPY080930C00148000",
        "check_dates": ["2008-01-03", "2008-08-11"],
    },
    "QQQ": {
        "contract_id": "QQQ140920C00077000",
        "check_dates": ["2013-12-23", "2014-03-11"],
    },
}

ALIASES = {
    "contract": ("contract_id", "contract_symbol", "option_symbol", "occ_symbol", "option_ticker"),
    "date": ("date", "observation_date", "quote_date", "quotedate", "trade_date"),
    "expiration": ("expiration", "expiration_date", "expiry", "expirationdate"),
    "strike": ("strike", "strike_price", "strikeprice"),
    "type": ("type", "option_type", "right", "call_put", "put_call"),
    "bid": ("bid", "bid_price"),
    "ask": ("ask", "ask_price"),
}


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def resolve_columns(con: duckdb.DuckDBPyConnection, path: str) -> dict[str, str]:
    expr = "read_parquet(" + sql_string(path) + ", union_by_name=true)"
    schema = con.execute(f"DESCRIBE SELECT * FROM {expr} LIMIT 0").fetchdf()
    actual = [str(c) for c in schema["column_name"]]
    lower_to_actual = {c.lower(): c for c in actual}
    resolved = {}
    for key, candidates in ALIASES.items():
        found = next((lower_to_actual[c] for c in candidates if c in lower_to_actual), None)
        if found is not None:
            resolved[key] = found
    return resolved


def audit_one(
    con: duckdb.DuckDBPyConnection,
    symbol: str,
    option_source: str,
    underlying_source: str,
) -> dict:
    target = FLAGGED[symbol]
    contract_id = target["contract_id"]
    option_expr = "read_parquet(" + sql_string(option_source) + ", union_by_name=true)"
    underlying_expr = "read_parquet(" + sql_string(underlying_source) + ", union_by_name=true)"
    option_cols = resolve_columns(con, option_source)
    missing = sorted(set(ALIASES) - set(option_cols))
    if missing:
        raise ValueError(f"{symbol} option source lacks required columns {missing}")

    underlying_schema = con.execute(f"DESCRIBE SELECT * FROM {underlying_expr} LIMIT 0").fetchdf()
    underlying_columns = [str(c) for c in underlying_schema["column_name"]]
    lower_to_actual = {c.lower(): c for c in underlying_columns}
    date_col = next((lower_to_actual[c] for c in ("date", "observation_date", "trading_date", "time") if c in lower_to_actual), None)
    if date_col is None:
        raise ValueError(f"{symbol} underlying source has no recognized date column: {underlying_columns}")
    symbol_col = lower_to_actual.get("symbol")
    price_cols = [
        lower_to_actual[c] for c in
        ("close", "close_price", "underlying_close", "adj_close", "adjclose", "adjusted_close", "underlying_price", "price")
        if c in lower_to_actual
    ]
    if not price_cols:
        raise ValueError(f"{symbol} underlying source has no recognized price column: {underlying_columns}")

    c = {key: ident(value) for key, value in option_cols.items()}
    rows = []
    for day in target["check_dates"]:
        option_sql = f"""
            SELECT CAST({c['date']} AS DATE) AS quote_date,
                   CAST({c['expiration']} AS DATE) AS expiration,
                   CAST({c['strike']} AS DOUBLE) AS strike,
                   CAST({c['type']} AS VARCHAR) AS option_type,
                   CAST({c['bid']} AS DOUBLE) AS bid,
                   CAST({c['ask']} AS DOUBLE) AS ask
            FROM {option_expr}
            WHERE CAST({c['contract']} AS VARCHAR) = {sql_string(contract_id)}
              AND CAST({c['date']} AS DATE) = DATE {sql_string(day)}
            ORDER BY quote_date
        """
        option_rows = con.execute(option_sql).fetchdf()
        underlying_select = ", ".join(f"CAST({ident(col)} AS DOUBLE) AS {ident(col)}" for col in price_cols)
        symbol_filter = f" AND CAST({ident(symbol_col)} AS VARCHAR) = {sql_string(symbol)}" if symbol_col else ""
        underlying_sql = f"""
            SELECT {underlying_select}
            FROM {underlying_expr}
            WHERE CAST({ident(date_col)} AS DATE) = DATE {sql_string(day)}{symbol_filter}
            LIMIT 1
        """
        underlying_rows = con.execute(underlying_sql).fetchdf()
        underlying_values = {}
        if not underlying_rows.empty:
            underlying_values = {
                str(col): (float(underlying_rows.iloc[0][col]) if underlying_rows.iloc[0][col] is not None else None)
                for col in price_cols
            }
        day_result = {
            "date": day,
            "option_rows_found": int(len(option_rows)),
            "underlying_rows_found": int(len(underlying_rows)),
            "underlying_price_fields": underlying_values,
            "quotes": [],
        }
        for _, row in option_rows.iterrows():
            option_type = str(row["option_type"]).strip().lower()
            strike = float(row["strike"])
            bid = float(row["bid"]) if row["bid"] is not None else None
            ask = float(row["ask"]) if row["ask"] is not None else None
            quote = {
                "expiration": row["expiration"].date().isoformat() if hasattr(row["expiration"], "date") else str(row["expiration"]),
                "strike": strike,
                "option_type": option_type,
                "bid": bid,
                "ask": ask,
                "intrinsic_checks_by_underlying_field": {},
            }
            for price_field, spot in underlying_values.items():
                if spot is None or spot <= 0:
                    intrinsic = None
                elif option_type in ("c", "call"):
                    intrinsic = max(spot - strike, 0.0)
                elif option_type in ("p", "put"):
                    intrinsic = max(strike - spot, 0.0)
                else:
                    intrinsic = None
                quote["intrinsic_checks_by_underlying_field"][price_field] = {
                    "underlying_price": spot,
                    "intrinsic_value": intrinsic,
                    "bid_below_intrinsic_by_more_than_0_01": bool(bid is not None and intrinsic is not None and bid + 0.01 < intrinsic),
                    "ask_below_intrinsic_by_more_than_0_01": bool(ask is not None and intrinsic is not None and ask + 0.01 < intrinsic),
                }
            day_result["quotes"].append(quote)
        rows.append(day_result)

    return {
        "symbol": symbol,
        "contract_id": contract_id,
        "option_source": option_source,
        "underlying_source": underlying_source,
        "underlying_columns": underlying_columns,
        "underlying_price_fields_checked": price_cols,
        "check_dates": rows,
        "interpretation_guardrail": (
            "A quote below intrinsic on a candidate price field is only a warning until "
            "the underlying and option premium adjustment bases are verified. Do not use "
            "this diagnostic to impute a quote or approve terminal equity."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spy-source", required=True)
    parser.add_argument("--qqq-source", required=True)
    parser.add_argument("--spy-underlying", required=True)
    parser.add_argument("--qqq-underlying", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    con = duckdb.connect()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    reports = {
        "SPY": audit_one(con, "SPY", args.spy_source, args.spy_underlying),
        "QQQ": audit_one(con, "QQQ", args.qqq_source, args.qqq_underlying),
    }
    for symbol, report in reports.items():
        path = out / f"{symbol.lower()}_intrinsic_bound_diagnostic.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    (out / "intrinsic_bound_diagnostic_summary.json").write_text(
        json.dumps({
            "report_type": "adaptive_leaps_intrinsic_bound_diagnostic",
            "status": "completed",
            "symbols": {
                symbol: {
                    "contract_id": report["contract_id"],
                    "underlying_columns": report["underlying_columns"],
                    "underlying_price_fields_checked": report["underlying_price_fields_checked"],
                    "check_dates": [
                        {
                            "date": day["date"],
                            "option_rows_found": day["option_rows_found"],
                            "underlying_rows_found": day["underlying_rows_found"],
                            "quotes": day["quotes"],
                        }
                        for day in report["check_dates"]
                    ],
                }
                for symbol, report in reports.items()
            },
            "interpretation_guardrail": "Price-basis warning only; no price is imputed and no strategy result is approved.",
        }, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
