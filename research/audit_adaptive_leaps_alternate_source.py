"""Cross-check replay-blocking LEAPS contract histories in a second preserved dataset copy.

This is a source-comparison diagnostic only. The alternate data-v1 release is a
preserved copy of an upstream dataset whose original sourcing was undocumented;
matching rows are not independent exchange-data verification.
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

ALIASES = {
    "contract": ("contract_id", "contract_symbol", "option_symbol", "occ_symbol", "option_ticker"),
    "date": ("date", "observation_date", "quote_date", "quotedate", "trade_date"),
    "expiration": ("expiration", "expiration_date", "expiry", "expirationdate"),
    "bid": ("bid", "bid_price"),
    "ask": ("ask", "ask_price"),
}


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def iso_date(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        value = value.date()
    return value.isoformat()


def choose_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    by_lower = {column.lower(): column for column in columns}
    return next((by_lower[name] for name in candidates if name in by_lower), None)


def inspect_contract_history(source: str | Path, symbol: str, contract_id: str) -> dict:
    source = str(source)
    con = duckdb.connect()
    try:
        description = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet({sql_string(source)})"
        ).fetchall()
        columns = [row[0] for row in description]
        selected = {key: choose_column(columns, aliases) for key, aliases in ALIASES.items()}
        missing = [key for key in ("contract", "date", "expiration", "bid", "ask") if selected[key] is None]
        base = {
            "report_type": "adaptive_leaps_alternate_source_contract_audit",
            "symbol": symbol,
            "contract_id": contract_id,
            "source": source,
            "source_columns": columns,
            "column_mapping": selected,
            "status": "schema_missing_required_columns" if missing else "not_found",
            "missing_required_columns": missing,
        }
        if missing:
            return base

        rows = con.execute(
            f"""
            SELECT
              TRY_CAST({ident(selected['date'])} AS DATE) AS observation_date,
              TRY_CAST({ident(selected['expiration'])} AS DATE) AS expiration,
              TRY_CAST({ident(selected['bid'])} AS DOUBLE) AS bid,
              TRY_CAST({ident(selected['ask'])} AS DOUBLE) AS ask
            FROM read_parquet({sql_string(source)})
            WHERE CAST({ident(selected['contract'])} AS VARCHAR) = ?
            ORDER BY observation_date
            """,
            [contract_id],
        ).fetchdf()
        if rows.empty:
            return base

        rows["valid_bid"] = rows["bid"].notna() & (rows["bid"] > 0)
        rows["valid_quote"] = (
            rows["valid_bid"]
            & rows["ask"].notna()
            & (rows["ask"] > 0)
            & (rows["ask"] >= rows["bid"])
        )
        last_bid_rows = rows.loc[rows["valid_bid"]]
        last_quote_rows = rows.loc[rows["valid_quote"]]
        last_bid_date = last_bid_rows["observation_date"].max() if not last_bid_rows.empty else None
        last_quote_date = last_quote_rows["observation_date"].max() if not last_quote_rows.empty else None
        expiration = rows["expiration"].dropna().max()
        last_bid_price = None
        if last_bid_date is not None:
            last_bid_price = float(last_bid_rows.loc[last_bid_rows["observation_date"] == last_bid_date, "bid"].iloc[-1])
        last_ask_price = None
        if last_quote_date is not None:
            last_ask_price = float(last_quote_rows.loc[last_quote_rows["observation_date"] == last_quote_date, "ask"].iloc[-1])
        last_row_date = rows["observation_date"].max()
        days_from_bid_to_expiration = (
            int((expiration - last_bid_date).days)
            if expiration is not None and last_bid_date is not None
            else None
        )
        rows_after_last_bid = (
            int((rows["observation_date"] > last_bid_date).sum())
            if last_bid_date is not None
            else None
        )
        base.update({
            "status": "completed",
            "rows": int(len(rows)),
            "first_row_date": iso_date(rows["observation_date"].min()),
            "last_row_date": iso_date(last_row_date),
            "expiration": iso_date(expiration),
            "valid_bid_rows": int(rows["valid_bid"].sum()),
            "fully_valid_quote_rows": int(rows["valid_quote"].sum()),
            "rows_after_last_positive_bid": rows_after_last_bid,
            "last_positive_bid_date": iso_date(last_bid_date),
            "last_positive_bid": last_bid_price,
            "last_fully_valid_quote_date": iso_date(last_quote_date),
            "last_fully_valid_quote_ask": last_ask_price,
            "days_from_last_positive_bid_to_expiration": days_from_bid_to_expiration,
            "interpretation": (
                "A matching history is an alternate preserved copy, not independent exchange-data validation. "
                "A missing or invalid bid is not replaced or imputed."
            ),
        })
        return base
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spy-source", required=True)
    parser.add_argument("--qqq-source", required=True)
    parser.add_argument("--out-dir", default="artifacts/adaptive_leaps_alternate_source")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for symbol, source in (("SPY", args.spy_source), ("QQQ", args.qqq_source)):
        report = inspect_contract_history(source, symbol, FLAGGED[symbol])
        reports.append(report)
        (out_dir / f"{symbol.lower()}_alternate_source_contract.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(json.dumps(report, indent=2))
    summary = {
        "report_type": "adaptive_leaps_alternate_source_contract_audit",
        "status": "completed" if all(r["status"] in {"completed", "not_found"} for r in reports) else "schema_error",
        "source_release": "lambdaclass/options_portfolio_backtester data-v1",
        "source_provenance_warning": (
            "The release notice says its original upstream disappeared and that upstream sourcing was undocumented; "
            "this audit is a preserved-copy comparison, not independent market-data validation."
        ),
        "contracts": reports,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if summary["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
