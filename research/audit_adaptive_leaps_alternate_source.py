"""Cross-check replay-blocking LEAPS contract histories in a second preserved dataset copy.

This is a source-comparison diagnostic only. The alternate data-v1 release is a
preserved copy of an upstream dataset whose original sourcing was undocumented;
matching rows are not independent exchange-data verification.
"""
from __future__ import annotations

import argparse
import json
from datetime import timedelta
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
            f"DESCRIBE SELECT * FROM read_parquet({sql_string(source)}, union_by_name=true)"
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
            FROM read_parquet({sql_string(source)}, union_by_name=true)
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
        exit_threshold_date = (
            expiration - timedelta(days=30)
            if expiration is not None
            else None
        )
        exit_window = (
            rows.loc[
                (rows["observation_date"] >= exit_threshold_date)
                & (rows["observation_date"] <= expiration)
            ]
            if exit_threshold_date is not None and expiration is not None
            else rows.iloc[0:0]
        )
        last_observation_to_expiration_days = (
            int((expiration - last_row_date).days)
            if expiration is not None and last_row_date is not None
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
            "exit_threshold_dte_calendar_days": 30,
            "exit_threshold_date": iso_date(exit_threshold_date),
            "rows_on_or_after_exit_threshold_through_expiration": int(len(exit_window)),
            "positive_bid_rows_on_or_after_exit_threshold_through_expiration": int(
                (exit_window["valid_bid"]).sum()
            ),
            "last_observation_to_expiration_days": last_observation_to_expiration_days,
            "interpretation": (
                "A matching history is an alternate preserved copy, not independent exchange-data validation. "
                "A missing or invalid bid is not replaced or imputed."
            ),
        })
        return base
    finally:
        con.close()


def _quote_rows(source: str | Path, contract_id: str):
    import pandas as pd

    source = str(source)
    con = duckdb.connect()
    try:
        description = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet({sql_string(source)}, union_by_name=true)"
        ).fetchall()
        columns = [row[0] for row in description]
        selected = {key: choose_column(columns, aliases) for key, aliases in ALIASES.items()}
        missing = [key for key in ("contract", "date", "expiration", "bid", "ask") if selected[key] is None]
        if missing:
            return None, {"status": "schema_missing_required_columns", "missing_required_columns": missing, "source_columns": columns}
        rows = con.execute(
            f"""
            SELECT
              TRY_CAST({ident(selected['date'])} AS DATE) AS observation_date,
              TRY_CAST({ident(selected['expiration'])} AS DATE) AS expiration,
              TRY_CAST({ident(selected['bid'])} AS DOUBLE) AS bid,
              TRY_CAST({ident(selected['ask'])} AS DOUBLE) AS ask
            FROM read_parquet({sql_string(source)}, union_by_name=true)
            WHERE CAST({ident(selected['contract'])} AS VARCHAR) = ?
            ORDER BY observation_date
            """,
            [contract_id],
        ).fetchdf()
        if rows.empty:
            return {}, {"status": "not_found", "source_columns": columns}
        result = {}
        duplicates = []
        for row in rows.itertuples(index=False):
            day = iso_date(row.observation_date)
            if day in result:
                duplicates.append(day)
            result[day] = {
                "bid": None if pd.isna(row.bid) else float(row.bid),
                "ask": None if pd.isna(row.ask) else float(row.ask),
                "expiration": iso_date(row.expiration),
            }
        return result, {"status": "completed", "rows": len(rows), "duplicate_dates": sorted(set(duplicates)), "source_columns": columns}
    finally:
        con.close()


def compare_contract_rows(primary_source: str | Path, alternate_source: str | Path, contract_id: str) -> dict:
    primary, primary_meta = _quote_rows(primary_source, contract_id)
    alternate, alternate_meta = _quote_rows(alternate_source, contract_id)
    report = {
        "status": "completed" if primary_meta["status"] == alternate_meta["status"] == "completed" else "comparison_incomplete",
        "contract_id": contract_id,
        "primary_source": str(primary_source),
        "alternate_source": str(alternate_source),
        "primary": primary_meta,
        "alternate": alternate_meta,
    }
    if report["status"] != "completed":
        return report

    primary_dates, alternate_dates = set(primary), set(alternate)
    shared = sorted(primary_dates & alternate_dates)
    bid_validity_disagreements = []
    bid_value_differences = []
    ask_value_differences = []
    expiration_differences = []
    for day in shared:
        p, a = primary[day], alternate[day]
        p_valid = p["bid"] is not None and p["bid"] > 0
        a_valid = a["bid"] is not None and a["bid"] > 0
        if p_valid != a_valid:
            bid_validity_disagreements.append(day)
        if p["bid"] != a["bid"]:
            bid_value_differences.append(day)
        if p["ask"] != a["ask"]:
            ask_value_differences.append(day)
        if p["expiration"] != a["expiration"]:
            expiration_differences.append(day)
    report.update({
        "primary_row_count": len(primary),
        "alternate_row_count": len(alternate),
        "shared_date_count": len(shared),
        "primary_only_date_count": len(primary_dates - alternate_dates),
        "alternate_only_date_count": len(alternate_dates - primary_dates),
        "primary_only_dates_sample": sorted(primary_dates - alternate_dates)[:10],
        "alternate_only_dates_sample": sorted(alternate_dates - primary_dates)[:10],
        "bid_validity_disagreement_count": len(bid_validity_disagreements),
        "bid_validity_disagreement_dates_sample": bid_validity_disagreements[:10],
        "bid_value_difference_count": len(bid_value_differences),
        "bid_value_difference_dates_sample": bid_value_differences[:10],
        "ask_value_difference_count": len(ask_value_differences),
        "ask_value_difference_dates_sample": ask_value_differences[:10],
        "expiration_difference_count": len(expiration_differences),
        "exact_core_quote_history_match": (
            not (primary_dates - alternate_dates)
            and not (alternate_dates - primary_dates)
            and not bid_value_differences
            and not ask_value_differences
            and not expiration_differences
        ),
        "interpretation": "This compares preserved datasets only; exact agreement is not independent exchange-data validation.",
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spy-source", required=True)
    parser.add_argument("--qqq-source", required=True)
    parser.add_argument("--spy-primary-source", required=True)
    parser.add_argument("--qqq-primary-source", required=True)
    parser.add_argument("--out-dir", default="artifacts/adaptive_leaps_alternate_source")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    sources = {
        "SPY": (args.spy_source, args.spy_primary_source),
        "QQQ": (args.qqq_source, args.qqq_primary_source),
    }
    for symbol, (source, primary_source) in sources.items():
        report = inspect_contract_history(source, symbol, FLAGGED[symbol])
        report["primary_source_comparison"] = compare_contract_rows(
            primary_source, source, FLAGGED[symbol]
        )
        reports.append(report)
        (out_dir / f"{symbol.lower()}_alternate_source_contract.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(json.dumps(report, indent=2))
    summary = {
        "report_type": "adaptive_leaps_alternate_source_contract_audit",
        "status": "completed" if all(r["status"] == "completed" and r.get("primary_source_comparison", {}).get("status") == "completed" for r in reports) else "audit_incomplete",
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
