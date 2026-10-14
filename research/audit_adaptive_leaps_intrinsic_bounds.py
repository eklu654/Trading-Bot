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


def quantiles(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "p10": None, "p25": None, "p50": None, "p75": None, "p90": None}

    ordered = sorted(values)

    def at(p: float) -> float:
        position = (len(ordered) - 1) * p
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        fraction = position - lower
        return ordered[lower] * (1 - fraction) + ordered[upper] * fraction

    return {
        "count": len(ordered),
        "p10": at(0.10),
        "p25": at(0.25),
        "p50": at(0.50),
        "p75": at(0.75),
        "p90": at(0.90),
    }


def audit_cohort(
    con: duckdb.DuckDBPyConnection,
    symbol: str,
    option_source: str,
    underlying_source: str,
) -> dict:
    """Count quote/intrinsic lower-bound warnings across same-year expiries."""
    check_date = "2008-08-11" if symbol == "SPY" else "2014-03-11"
    option_expr = "read_parquet(" + sql_string(option_source) + ", union_by_name=true)"
    underlying_expr = "read_parquet(" + sql_string(underlying_source) + ", union_by_name=true)"
    option_cols = resolve_columns(con, option_source)
    required = ("contract", "date", "expiration", "strike", "type", "bid", "ask")
    missing = sorted(set(required) - set(option_cols))
    if missing:
        raise ValueError(f"{symbol} option source lacks required columns {missing}")
    underlying_schema = con.execute(f"DESCRIBE SELECT * FROM {underlying_expr} LIMIT 0").fetchdf()
    underlying_columns = [str(c) for c in underlying_schema["column_name"]]
    lower_to_actual = {c.lower(): c for c in underlying_columns}
    date_col = next((lower_to_actual[c] for c in ("date", "observation_date", "trading_date", "time") if c in lower_to_actual), None)
    symbol_col = lower_to_actual.get("symbol")
    price_cols = [
        lower_to_actual[c] for c in
        ("close", "close_price", "underlying_close", "adj_close", "adjclose", "adjusted_close", "underlying_price", "price")
        if c in lower_to_actual
    ]
    if date_col is None or not price_cols:
        raise ValueError(f"{symbol} underlying source has unrecognized schema: {underlying_columns}")
    year = int(check_date[:4])
    oc = {key: ident(value) for key, value in option_cols.items()}
    option_rows = con.execute(f"""
        SELECT CAST({oc['contract']} AS VARCHAR) AS contract_id,
               CAST({oc['expiration']} AS DATE) AS expiration,
               CAST({oc['strike']} AS DOUBLE) AS strike,
               lower(trim(CAST({oc['type']} AS VARCHAR))) AS option_type,
               CAST({oc['bid']} AS DOUBLE) AS bid,
               CAST({oc['ask']} AS DOUBLE) AS ask
        FROM {option_expr}
        WHERE CAST({oc['date']} AS DATE) = DATE {sql_string(check_date)}
          AND year(CAST({oc['expiration']} AS DATE)) = {year}
    """).fetchdf()
    symbol_filter = f" AND CAST({ident(symbol_col)} AS VARCHAR) = {sql_string(symbol)}" if symbol_col else ""
    price_select = ", ".join(f"CAST({ident(col)} AS DOUBLE) AS {ident(col)}" for col in price_cols)
    underlying_rows = con.execute(f"""
        SELECT {price_select}
        FROM {underlying_expr}
        WHERE CAST({ident(date_col)} AS DATE) = DATE {sql_string(check_date)}{symbol_filter}
        LIMIT 1
    """).fetchdf()
    spots = {
        str(col): float(underlying_rows.iloc[0][col])
        for col in price_cols
        if not underlying_rows.empty and underlying_rows.iloc[0][col] is not None
    }
    counts = {
        field: {
            "positive_ask_rows": 0,
            "positive_bid_rows": 0,
            "ask_below_intrinsic_rows": 0,
            "bid_below_intrinsic_rows": 0,
            "ask_to_intrinsic_ratios_for_itm_quotes": [],
            "by_option_type": {
                kind: {
                    "positive_ask_rows": 0,
                    "positive_bid_rows": 0,
                    "ask_below_intrinsic_rows": 0,
                    "bid_below_intrinsic_rows": 0,
                    "ask_to_intrinsic_ratios_for_itm_quotes": [],
                    "sample_ask_violations": [],
                }
                for kind in ("call", "put")
            },
            "sample_ask_violations": [],
        }
        for field in spots
    }
    for _, row in option_rows.iterrows():
        option_type = str(row["option_type"]).strip().lower()
        if option_type in ("c", "call"):
            kind = "call"
        elif option_type in ("p", "put"):
            kind = "put"
        else:
            continue
        strike = float(row["strike"])
        bid = float(row["bid"]) if row["bid"] is not None else 0.0
        ask = float(row["ask"]) if row["ask"] is not None else 0.0
        for field, spot in spots.items():
            intrinsic = max(spot - strike, 0.0) if kind == "call" else max(strike - spot, 0.0)
            result = counts[field]
            type_result = result["by_option_type"][kind]
            result["positive_ask_rows"] += int(ask > 0)
            result["positive_bid_rows"] += int(bid > 0)
            type_result["positive_ask_rows"] += int(ask > 0)
            type_result["positive_bid_rows"] += int(bid > 0)
            ask_violation = ask > 0 and ask + 0.01 < intrinsic
            bid_violation = bid > 0 and bid + 0.01 < intrinsic
            result["ask_below_intrinsic_rows"] += int(ask_violation)
            result["bid_below_intrinsic_rows"] += int(bid_violation)
            type_result["ask_below_intrinsic_rows"] += int(ask_violation)
            type_result["bid_below_intrinsic_rows"] += int(bid_violation)
            if ask > 0 and intrinsic > 0:
                ratio = ask / intrinsic
                result["ask_to_intrinsic_ratios_for_itm_quotes"].append(ratio)
                type_result["ask_to_intrinsic_ratios_for_itm_quotes"].append(ratio)
            violation = {
                "contract_id": str(row["contract_id"]),
                "expiration": row["expiration"].date().isoformat() if hasattr(row["expiration"], "date") else str(row["expiration"]),
                "strike": strike,
                "option_type": kind,
                "bid": bid,
                "ask": ask,
                "underlying_price": spot,
                "intrinsic_value": intrinsic,
            }
            if ask_violation and len(result["sample_ask_violations"]) < 10:
                result["sample_ask_violations"].append(violation)
            if ask_violation and len(type_result["sample_ask_violations"]) < 10:
                type_result["sample_ask_violations"].append(violation)

    for field, result in counts.items():
        result["ask_to_intrinsic_ratio_quantiles_for_itm_quotes"] = quantiles(
            result.pop("ask_to_intrinsic_ratios_for_itm_quotes")
        )
        for type_result in result["by_option_type"].values():
            type_result["ask_to_intrinsic_ratio_quantiles_for_itm_quotes"] = quantiles(
                type_result.pop("ask_to_intrinsic_ratios_for_itm_quotes")
            )
    return {
        "symbol": symbol,
        "check_date": check_date,
        "expiration_year_filter": year,
        "underlying_rows_found": int(len(underlying_rows)),
        "option_rows_in_expiration_year": int(len(option_rows)),
        "underlying_price_fields_checked": list(spots),
        "counts_by_underlying_field": counts,
        "interpretation_guardrail": (
            "Counts are lower-bound diagnostics only. A violation against one candidate spot field "
            "does not establish bad market data until option-premium and underlying adjustment bases are verified."
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
    cohorts = {
        "SPY": audit_cohort(con, "SPY", args.spy_source, args.spy_underlying),
        "QQQ": audit_cohort(con, "QQQ", args.qqq_source, args.qqq_underlying),
    }
    for symbol, report in reports.items():
        report["same_expiration_year_cohort"] = cohorts[symbol]
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
                    "same_expiration_year_cohort": cohorts[symbol],
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
