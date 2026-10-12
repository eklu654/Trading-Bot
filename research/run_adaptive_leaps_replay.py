"""Run the frozen long-call replay on a local Parquet chain dataset.

Example:
  python -m research.run_adaptive_leaps_replay --symbol SPY \
    --source "data/options/SPY/**/*.parquet" --out-dir artifacts/leaps-spy
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

import duckdb

from research.adaptive_leaps_lifecycle import OptionQuote
from research.adaptive_leaps_replay import replay_long_call


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", required=True, choices=("SPY", "QQQ"))
    p.add_argument("--source", required=True, help="Parquet path or glob")
    p.add_argument("--out-dir", default="artifacts/adaptive_leaps_replay")
    p.add_argument("--starting-cash", type=float, default=5000.0)
    p.add_argument("--target-dte", type=int, default=270)
    p.add_argument("--target-abs-delta", type=float, default=0.80)
    p.add_argument("--exit-dte", type=int, default=30)
    p.add_argument("--enforce-account-cash", action="store_true")
    return p.parse_args()


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    args = parse_args()
    source = sql_string(args.source)
    target = args.target_dte
    con = duckdb.connect()
    # First identify contracts that ever pass the frozen entry-candidate gate.
    # Then retain their full available histories so next-date fills, exit marks,
    # and invalid/missing quote cases can be evaluated without look-ahead.
    sql = f"""
    WITH source AS (
      SELECT CAST(date AS DATE) AS obs_date,
             CAST(expiration AS DATE) AS expiration,
             CAST(strike AS DOUBLE) AS strike,
             lower(CAST(type AS VARCHAR)) AS option_type,
             CAST(delta AS DOUBLE) AS delta,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark,
             CAST(volume AS DOUBLE) AS volume,
             CAST(open_interest AS DOUBLE) AS open_interest,
             CAST(contract_id AS VARCHAR) AS contract_id
      FROM read_parquet({source}, hive_partitioning=false)
    ),
    eligible_ids AS (
      SELECT DISTINCT contract_id FROM source
      WHERE option_type='call'
        AND date_diff('day', obs_date, expiration) BETWEEN {target - 45} AND {target + 45}
        AND abs(delta) BETWEEN 0.60 AND 0.95
        AND bid > 0 AND ask >= bid AND mark > 0
        AND (coalesce(volume, 0) > 0 OR coalesce(open_interest, 0) > 0)
        AND contract_id IS NOT NULL
    )
    SELECT s.* FROM source s
    INNER JOIN eligible_ids e USING (contract_id)
    ORDER BY obs_date, expiration, strike, contract_id
    """
    cursor = con.execute(sql)
    names = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    quotes = []
    for row in rows:
        item = dict(zip(names, row))
        quotes.append(OptionQuote(
            symbol=args.symbol,
            observation_date=item["obs_date"],
            expiration=item["expiration"],
            strike=float(item["strike"]),
            option_type=str(item["option_type"]),
            delta=float(item["delta"]) if item["delta"] is not None else 0.0,
            bid=float(item["bid"]) if item["bid"] is not None else 0.0,
            ask=float(item["ask"]) if item["ask"] is not None else 0.0,
            mark=float(item["mark"]) if item["mark"] is not None else 0.0,
            volume=float(item["volume"]) if item["volume"] is not None else None,
            open_interest=float(item["open_interest"]) if item["open_interest"] is not None else None,
            contract_id=str(item["contract_id"]),
        ))
    result = replay_long_call(
        quotes, symbol=args.symbol, starting_cash=args.starting_cash,
        target_dte=args.target_dte, target_abs_delta=args.target_abs_delta,
        exit_dte=args.exit_dte, enforce_account_cash=args.enforce_account_cash,
    )
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    import csv
    ledger_path = out / "daily_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(result.ledger[0]).keys()) if result.ledger else [
            "date", "event", "symbol", "cash", "contract_id", "dte", "bid_mark",
            "market_value", "equity", "realized_pnl", "detail",
        ])
        writer.writeheader()
        for row in result.ledger:
            payload = asdict(row)
            payload["date"] = row.date.isoformat()
            writer.writerow(payload)
    transaction_path = out / "transactions.csv"
    transaction_fields = sorted({k for txn in result.transactions for k in txn})
    with transaction_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=transaction_fields or ["date", "action"])
        writer.writeheader()
        writer.writerows(result.transactions)
    summary = {
        "status": "completed",
        "symbol": args.symbol,
        "source": args.source,
        "candidate_history_rows_loaded": len(quotes),
        "observation_dates": len(result.ledger),
        "transactions": len(result.transactions),
        "rejected_orders": result.rejected_orders,
        "starting_cash": args.starting_cash,
        "final_cash": result.final_cash,
        "final_equity": result.final_equity,
        "final_mark_available": result.final_mark_available,
        "target_dte": args.target_dte,
        "target_abs_delta": args.target_abs_delta,
        "exit_dte": args.exit_dte,
        "fill_model": "buy ask / sell bid; decisions on close t execute no earlier than next observation date",
        "account_cash_enforced": args.enforce_account_cash,
        "interpretation": "EOD historical quote-side replay; not proof of executable fills or broker feasibility",
        "ledger_csv": str(ledger_path),
        "transactions_csv": str(transaction_path),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
