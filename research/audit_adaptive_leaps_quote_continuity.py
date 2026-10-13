"""Audit post-entry option quote continuity for the frozen LEAPS candidate cohort.

This is a source-data diagnostic, not a strategy backtest. It reports only rows
actually present in the source; calendar gaps between rows are exposed and are
not imputed as quotes. Missing/invalid bids never become zero-value marks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", required=True, choices=("SPY", "QQQ"))
    p.add_argument("--source", required=True, help="Option-chain Parquet path/glob")
    p.add_argument("--out-dir", default="artifacts/adaptive_leaps_quote_continuity")
    p.add_argument("--target-dte", type=int, default=270)
    p.add_argument("--dte-window", type=int, default=45)
    p.add_argument("--min-abs-delta", type=float, default=0.60)
    p.add_argument("--max-abs-delta", type=float, default=0.95)
    p.add_argument("--contract-ids", default="", help="Optional comma-separated contract IDs to flag")
    return p.parse_args()


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    args = parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    source = sql_string(args.source)
    low_dte, high_dte = args.target_dte - args.dte_window, args.target_dte + args.dte_window
    flagged = [item.strip() for item in args.contract_ids.split(",") if item.strip()]
    flagged_sql = ", ".join(sql_string(item) for item in flagged) or "NULL"

    sql = f"""
    WITH source AS (
      SELECT CAST(date AS DATE) AS obs_date,
             CAST(expiration AS DATE) AS expiration,
             CAST(delta AS DOUBLE) AS delta,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark,
             CAST(volume AS DOUBLE) AS volume,
             CAST(open_interest AS DOUBLE) AS open_interest,
             lower(CAST(type AS VARCHAR)) AS option_type,
             CAST(contract_id AS VARCHAR) AS contract_id,
             date_diff('day', CAST(date AS DATE), CAST(expiration AS DATE)) AS dte
      FROM read_parquet({source}, hive_partitioning=false)
      WHERE contract_id IS NOT NULL
    ),
    eligible AS (
      SELECT contract_id, min(obs_date) AS first_eligible_date,
             count(*) AS eligible_observations
      FROM source
      WHERE option_type='call'
        AND dte BETWEEN {low_dte} AND {high_dte}
        AND abs(delta) BETWEEN {args.min_abs_delta} AND {args.max_abs_delta}
        AND bid > 0 AND ask >= bid AND mark > 0
        AND (coalesce(volume, 0) > 0 OR coalesce(open_interest, 0) > 0)
      GROUP BY contract_id
    ),
    history AS (
      SELECT s.*, e.first_eligible_date, e.eligible_observations
      FROM source s JOIN eligible e USING (contract_id)
      WHERE s.obs_date >= e.first_eligible_date
        AND s.obs_date <= s.expiration
    ),
    with_gaps AS (
      SELECT *, lag(obs_date) OVER (PARTITION BY contract_id ORDER BY obs_date) AS prior_obs_date
      FROM history
    ),
    aggregates AS (
      SELECT contract_id, min(expiration) AS expiration,
             min(first_eligible_date) AS first_eligible_date,
             min(obs_date) AS first_history_row,
             max(obs_date) AS last_history_row,
             max(eligible_observations) AS eligible_observations,
             count(*) AS history_rows_present,
             count(*) FILTER (WHERE bid > 0 AND ask >= bid AND mark > 0) AS valid_quote_rows,
             count(*) FILTER (WHERE bid > 0 AND ask >= bid) AS valid_bid_rows,
             count(*) FILTER (WHERE bid IS NULL OR bid <= 0 OR ask IS NULL OR ask < bid) AS invalid_or_missing_bid_rows,
             max(obs_date) FILTER (WHERE bid > 0 AND ask >= bid) AS last_valid_bid_date,
             max(obs_date) FILTER (WHERE bid > 0 AND ask >= bid AND mark > 0) AS last_fully_valid_quote_date,
             max(date_diff('day', prior_obs_date, obs_date)) AS max_calendar_gap_between_rows,
             count(*) FILTER (WHERE prior_obs_date IS NOT NULL AND date_diff('day', prior_obs_date, obs_date) > 4) AS gaps_over_4_calendar_days,
             count(*) FILTER (WHERE obs_date > (
               SELECT max(h2.obs_date) FROM history h2
               WHERE h2.contract_id = history.contract_id AND h2.bid > 0 AND h2.ask >= h2.bid
             )) AS rows_after_last_valid_bid,
             bool_or(contract_id IN ({flagged_sql})) AS specifically_flagged
      FROM with_gaps AS history
      GROUP BY contract_id
    ),
    enriched AS (
      SELECT *,
             date_diff('day', last_valid_bid_date, expiration) AS dte_at_last_valid_bid,
             date_diff('day', last_valid_bid_date, last_history_row) AS days_from_last_valid_bid_to_last_row,
             round(100.0 * valid_bid_rows / nullif(history_rows_present, 0), 4) AS valid_bid_pct_of_rows,
             round(100.0 * valid_quote_rows / nullif(history_rows_present, 0), 4) AS valid_quote_pct_of_rows
      FROM aggregates
    )
    SELECT * FROM enriched ORDER BY specifically_flagged DESC, first_eligible_date, contract_id
    """
    df = con.execute(sql).fetchdf()
    csv_path = out / f"{args.symbol.lower()}_quote_continuity_by_contract.csv"
    df.to_csv(csv_path, index=False)

    def num(series, value):
        return int((series == value).sum())

    flagged_rows = df[df["specifically_flagged"] == True] if not df.empty else df
    report = {
        "report_type": "adaptive_leaps_quote_continuity",
        "status": "completed",
        "symbol": args.symbol,
        "source": args.source,
        "selection": {
            "target_dte": args.target_dte,
            "dte_window": args.dte_window,
            "min_abs_delta": args.min_abs_delta,
            "max_abs_delta": args.max_abs_delta,
            "eligible_contract_definition": "calls within DTE window, delta bounds, positive bid/mark, non-crossed ask, and volume or open interest",
        },
        "cohort": {
            "eligible_contracts": int(len(df)),
            "contracts_with_any_valid_bid": int(df["last_valid_bid_date"].notna().sum()) if not df.empty else 0,
            "contracts_with_no_valid_bid_after_eligibility": int(df["last_valid_bid_date"].isna().sum()) if not df.empty else 0,
            "contracts_last_valid_bid_more_than_30_days_before_expiration": int((df["dte_at_last_valid_bid"] > 30).sum()) if not df.empty else 0,
            "contracts_last_valid_bid_at_or_before_30_dte": int(((df["dte_at_last_valid_bid"] <= 30) & df["dte_at_last_valid_bid"].notna()).sum()) if not df.empty else 0,
            "median_valid_bid_pct_of_present_rows": float(df["valid_bid_pct_of_rows"].median()) if not df.empty else None,
            "median_max_calendar_gap_between_rows": float(df["max_calendar_gap_between_rows"].median()) if not df.empty else None,
        },
        "flagged_contracts": flagged_rows.to_dict(orient="records"),
        "limitations": [
            "Only rows present in the source are counted; a gap between rows is not an observed quote.",
            "A positive historical bid is not proof of executable liquidity or an actual fill.",
            "This report does not simulate exits, expiration, exercise, assignment, corporate actions, or P/L.",
            "Contract IDs are grouped as provided by the pinned source; source identity and adjustment conventions still require validation.",
        ],
        "csv": str(csv_path),
    }
    json_path = out / f"{args.symbol.lower()}_quote_continuity_summary.json"
    json_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print(f"Wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
