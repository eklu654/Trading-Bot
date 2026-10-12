"""Audit deterministic availability for the frozen LEAPS DTE/delta candidate grid.

This is candidate-selection diagnostics only. It does not open trades or estimate P/L.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

TARGETS = [(270, 0.70), (270, 0.80), (270, 0.90),
           (365, 0.70), (365, 0.80), (365, 0.90),
           (540, 0.70), (540, 0.80), (540, 0.90)]


def args_parse() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--spy-source", required=True)
    p.add_argument("--qqq-source", required=True)
    p.add_argument("--spy-underlying", required=True)
    p.add_argument("--qqq-underlying", required=True)
    p.add_argument("--out-dir", default="artifacts/adaptive_leaps_candidates")
    return p.parse_args()


def pq(path: str) -> str:
    return "read_parquet('" + path.replace("'", "''") + "', hive_partitioning=false)"


def main() -> int:
    args = args_parse()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    frames = []
    for symbol in ("SPY", "QQQ"):
        options_path = getattr(args, f"{symbol.lower()}_source")
        underlying_path = getattr(args, f"{symbol.lower()}_underlying")
        targets_sql = ", ".join(f"({dte}, {delta})" for dte, delta in TARGETS)
        sql = f"""
        WITH targets(target_dte, target_delta) AS (VALUES {targets_sql}),
        underlying_dates AS (
          SELECT DISTINCT CAST(date AS DATE) AS obs_date
          FROM {pq(underlying_path)}
          WHERE close > 0
        ),
        options AS (
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
                 date_diff('day', CAST(date AS DATE), CAST(expiration AS DATE)) AS dte,
                 (CAST(ask AS DOUBLE) - CAST(bid AS DOUBLE)) /
                   NULLIF((CAST(ask AS DOUBLE) + CAST(bid AS DOUBLE)) / 2.0, 0) AS relative_spread
          FROM {pq(options_path)}
          WHERE lower(CAST(type AS VARCHAR)) = 'call'
        ),
        eligible AS (
          SELECT o.*, t.target_dte, t.target_delta,
                 abs(o.dte - t.target_dte) AS dte_error,
                 abs(abs(o.delta) - t.target_delta) AS delta_error
          FROM options o CROSS JOIN targets t
          WHERE o.dte BETWEEN t.target_dte - 45 AND t.target_dte + 45
            AND abs(o.delta) BETWEEN 0.60 AND 0.95
            AND o.bid > 0 AND o.ask >= o.bid AND o.mark > 0
            AND (coalesce(o.volume, 0) > 0 OR coalesce(o.open_interest, 0) > 0)
        ),
        ranked AS (
          SELECT *, row_number() OVER (
            PARTITION BY obs_date, target_dte, target_delta
            ORDER BY dte_error, delta_error, relative_spread ASC NULLS LAST,
                     open_interest DESC NULLS LAST, volume DESC NULLS LAST,
                     expiration, strike
          ) AS candidate_rank
          FROM eligible
        ),
        selected AS (
          SELECT * FROM ranked WHERE candidate_rank = 1
        )
        SELECT '{symbol}' AS symbol, year(u.obs_date) AS year,
               t.target_dte, t.target_delta,
               count(*) AS underlying_observation_dates,
               count(s.obs_date) AS dates_with_candidate,
               count(*) - count(s.obs_date) AS dates_without_candidate,
               round(100.0 * count(s.obs_date) / NULLIF(count(*), 0), 3) AS candidate_date_coverage_pct,
               median(s.dte) AS selected_median_dte,
               median(abs(s.delta)) AS selected_median_abs_delta,
               median(s.relative_spread) AS median_selected_relative_spread,
               median(s.dte_error) AS median_dte_error,
               median(s.delta_error) AS median_delta_error
        FROM underlying_dates u CROSS JOIN targets t
        LEFT JOIN selected s ON s.obs_date = u.obs_date
          AND s.target_dte = t.target_dte AND s.target_delta = t.target_delta
        GROUP BY ALL ORDER BY year, target_dte, target_delta
        """
        frames.append(con.execute(sql).fetchdf())
    report = pd.concat(frames, ignore_index=True)
    report.to_csv(out / "candidate_availability_by_year.csv", index=False)
    summary = {
        "report_type": "adaptive_leaps_candidate_selection_availability",
        "source_revision": "37f6c456fe1a4775c875673fb8ef907d5cd2fd66",
        "target_grid": [{"target_dte": d, "target_abs_delta": delta} for d, delta in TARGETS],
        "frozen_selector": {
            "eligible_dte_window": "target DTE +/-45 calendar days",
            "eligible_abs_delta": "0.60 through 0.95 inclusive",
            "quote_activity": "bid > 0, ask >= bid, mark > 0, and volume > 0 OR open interest > 0",
            "ranking": "smallest DTE error, then delta error, then relative spread, higher open interest, higher volume, earlier expiration, lower strike",
        },
        "limitations": [
            "This measures whether a deterministic candidate exists on a date, not whether an order fills.",
            "Target grid and +/-45 DTE window are the predeclared research grid, not optimized thresholds.",
            "A fixed entry calendar and long-leg replacement/exit rule must be frozen before any P/L replay.",
            "No assignment, dividends, corporate-action adjustment, fees, or slippage are simulated here.",
        ],
        "coverage": report.to_dict(orient="records"),
    }
    (out / "candidate_availability_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps({"report_type": summary["report_type"], "rows": len(report),
                      "target_combinations": len(TARGETS), "symbols": ["SPY", "QQQ"],
                      "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
