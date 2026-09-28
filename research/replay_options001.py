"""First-pass OPTIONS-001 SPY short-strangle replay.

The raw option dataset is intentionally external. This engine accepts either a
local Parquet glob or an HTTP(S) Parquet URL and performs the historical chain
selection/quote replay in bulk.

Baseline:
- 45 DTE target, 30-60 DTE eligible
- 16-delta short call/put
- one SPY position at a time
- 50% profit target
- 21 DTE time exit
- 2x initial-credit loss benchmark (research placeholder, not yet frozen)
- conservative bid/ask or midpoint execution

This is a daily EOD reconstruction, not an intraday execution simulation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from evaluate_regime_candidates import candidate_labels

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "data" / "research"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--options-source", required=True,
                   help="Local parquet glob or HTTP(S) parquet URL")
    p.add_argument("--candidate", default="BROAD_SIDEWAYS",
                   choices=["CURRENT", "BALANCED", "BROAD_SIDEWAYS", "TURBULENT_ONLY"])
    p.add_argument("--fill-model", default="conservative", choices=["conservative", "mid"])
    p.add_argument("--target-dte", type=int, default=45)
    p.add_argument("--target-delta", type=float, default=0.16)
    p.add_argument("--min-dte", type=int, default=30)
    p.add_argument("--max-dte", type=int, default=60)
    p.add_argument("--profit-target", type=float, default=0.50)
    p.add_argument("--exit-dte", type=int, default=21)
    p.add_argument("--loss-credit-multiple", type=float, default=2.0,
                   help="Loss benchmark in multiples of initial credit; <=0 disables it")
    p.add_argument("--start-date", default="2010-01-01")
    p.add_argument("--end-date", default="2025-12-31")
    return p.parse_args()


def load_regime(candidate: str, start: str, end: str) -> pd.DataFrame:
    frame = pd.read_csv(
        RESEARCH_DIR / "historical_regime_dataset.csv",
        parse_dates=["Date"],
    ).set_index("Date").sort_index()

    labels = candidate_labels(frame, candidate).shift(1)
    if candidate == "TURBULENT_ONLY":
        labels = pd.Series(
            "TURBULENT_HIGH_VOL",
            index=frame.index,
        ).where(frame["vix_percentile252"] >= 0.90, "TRENDING_NORMAL")

    frame["entry_regime"] = labels
    frame["eligible"] = labels.isin({"SIDEWAYS_CHOPPY", "TURBULENT_HIGH_VOL"})
    frame = frame.loc[start:end]
    return frame


def source_sql(source: str) -> str:
    escaped = source.replace("'", "''")
    return f"read_parquet('{escaped}', hive_partitioning=false)"


def validate_local_source(source: str) -> None:
    if source.startswith(("http://", "https://")):
        return
    matches = list(Path(source).parent.glob(Path(source).name))
    if not matches:
        raise FileNotFoundError(f"No option parquet files matched: {source}")


def select_entries(
    con: duckdb.DuckDBPyConnection,
    source: str,
    regime: pd.DataFrame,
    args: argparse.Namespace,
) -> pd.DataFrame:
    eligible = regime.index[regime["eligible"]]
    if len(eligible) == 0:
        return pd.DataFrame()

    dates = pd.DataFrame({"entry_date": eligible})
    con.register("eligible_dates", dates)

    q = f"""
        WITH candidates AS (
            SELECT
                CAST(o.date AS DATE) AS entry_date,
                o.contract_id,
                CAST(o.expiration AS DATE) AS expiration,
                o.strike,
                o.type,
                o.bid,
                o.ask,
                o.mark,
                o.volume,
                o.open_interest,
                o.delta,
                o.implied_volatility,
                datediff('day', CAST(o.date AS DATE), CAST(o.expiration AS DATE)) AS dte
            FROM {source_sql(source)} o
            INNER JOIN eligible_dates d ON CAST(o.date AS DATE) = d.entry_date
            WHERE CAST(o.expiration AS DATE) BETWEEN
                    CAST(o.date AS DATE) + INTERVAL '{args.min_dte}' DAY
                AND CAST(o.date AS DATE) + INTERVAL '{args.max_dte}' DAY
                AND o.bid > 0
                AND o.ask >= o.bid
                AND o.mark > 0
                AND (o.volume > 0 OR o.open_interest > 0)
        ),
        chosen_expiry AS (
            SELECT entry_date, expiration
            FROM (
                SELECT
                    entry_date,
                    expiration,
                    min(abs(dte - {args.target_dte})) OVER (
                        PARTITION BY entry_date
                    ) AS best_distance
                FROM candidates
            )
            GROUP BY entry_date, expiration, best_distance
            QUALIFY best_distance = min(best_distance) OVER (PARTITION BY entry_date)
        ),
        chain AS (
            SELECT c.*
            FROM candidates c
            INNER JOIN chosen_expiry e
                ON c.entry_date = e.entry_date
               AND c.expiration = e.expiration
        ),
        ranked AS (
            SELECT *,
                CASE
                    WHEN lower(type) = 'call'
                        THEN abs(delta - {args.target_delta})
                    ELSE abs(abs(delta) - {args.target_delta})
                END AS delta_distance,
                row_number() OVER (
                    PARTITION BY entry_date, type
                    ORDER BY
                        CASE
                            WHEN lower(type) = 'call'
                                THEN abs(delta - {args.target_delta})
                            ELSE abs(abs(delta) - {args.target_delta})
                        END,
                        volume DESC NULLS LAST,
                        open_interest DESC NULLS LAST
                ) AS rn
            FROM chain
            WHERE (lower(type) = 'call' AND delta > 0)
               OR (lower(type) = 'put' AND delta < 0)
        )
        SELECT *
        FROM ranked
        WHERE rn = 1
        ORDER BY entry_date, type
    """
    result = con.execute(q).fetchdf()
    con.unregister("eligible_dates")
    if result.empty:
        return result

    # Require both legs and collapse to one row per entry.
    result["type"] = result["type"].str.lower()
    calls = result[result["type"] == "call"].copy()
    puts = result[result["type"] == "put"].copy()
    merged = calls.merge(
        puts,
        on="entry_date",
        suffixes=("_call", "_put"),
    )
    return merged.sort_values("entry_date").reset_index(drop=True)


def quote_replay(
    con: duckdb.DuckDBPyConnection,
    source: str,
    entries: pd.DataFrame,
    args: argparse.Namespace,
) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    selected = entries[[
        "entry_date", "contract_id_call", "contract_id_put",
        "expiration_call",
    ]].rename(columns={"expiration_call": "expiration"})
    con.register("selected_entries", selected)

    q = f"""
        SELECT
            s.entry_date,
            s.contract_id_call,
            s.contract_id_put,
            s.expiration,
            CAST(o.date AS DATE) AS date,
            o.contract_id,
            o.bid,
            o.ask,
            o.mark
        FROM selected_entries s
        INNER JOIN {source_sql(source)} o
          ON o.contract_id IN (s.contract_id_call, s.contract_id_put)
         AND CAST(o.date AS DATE) > s.entry_date
         AND CAST(o.date AS DATE) <= s.expiration
        ORDER BY s.entry_date, o.date
    """
    quotes = con.execute(q).fetchdf()
    con.unregister("selected_entries")
    return quotes


def first_pass_trades(
    entries: pd.DataFrame,
    quotes: pd.DataFrame,
    regime: pd.DataFrame,
    args: argparse.Namespace,
) -> pd.DataFrame:
    if entries.empty or quotes.empty:
        return pd.DataFrame()

    lookup = entries.set_index("entry_date")
    trades = []
    active_until = pd.Timestamp.min

    for entry_date, row in entries.iterrows():
        # Only one SPY position at a time in this baseline.
        entry_date = pd.Timestamp(row["entry_date"])
        if entry_date <= active_until:
            continue

        call_credit = float(row["mark_call"] if args.fill_model == "mid" else row["bid_call"])
        put_credit = float(row["mark_put"] if args.fill_model == "mid" else row["bid_put"])
        credit = call_credit + put_credit
        if credit <= 0:
            continue

        call_id = str(row["contract_id_call"])
        put_id = str(row["contract_id_put"])
        expiry = pd.Timestamp(row["expiration_call"])

        q = quotes[quotes["entry_date"] == entry_date]
        if q.empty:
            continue

        by_date = q.pivot(index="date", columns="contract_id", values=["bid", "ask", "mark"])
        close_field = "mark" if args.fill_model == "mid" else "ask"

        for date, quote_row in by_date.iterrows():
            if (close_field, call_id) not in quote_row or (close_field, put_id) not in quote_row:
                continue
            call_exit = quote_row[(close_field, call_id)]
            put_exit = quote_row[(close_field, put_id)]
            if pd.isna(call_exit) or pd.isna(put_exit):
                continue

            debit = float(call_exit + put_exit)
            dte = (expiry - pd.Timestamp(date)).days
            reason = None

            if debit <= credit * (1 - args.profit_target):
                reason = "PROFIT_50"
            elif args.loss_credit_multiple > 0 and debit >= credit * args.loss_credit_multiple:
                reason = f"LOSS_{args.loss_credit_multiple:g}X_CREDIT"
            elif dte <= args.exit_dte:
                reason = "DTE_21"

            if reason:
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": pd.Timestamp(date),
                    "expiration": expiry,
                    "entry_credit": credit,
                    "exit_debit": debit,
                    "pnl": (credit - debit) * 100,
                    "exit_reason": reason,
                    "entry_dte": (expiry - entry_date).days,
                    "exit_dte": dte,
                    "call_strike": row["strike_call"],
                    "put_strike": row["strike_put"],
                    "call_delta": row["delta_call"],
                    "put_delta": row["delta_put"],
                    "call_contract_id": call_id,
                    "put_contract_id": put_id,
                    "regime": regime.loc[entry_date, "entry_regime"],
                })
                active_until = pd.Timestamp(date)
                break

    return pd.DataFrame(trades)


def main() -> None:
    args = parse_args()
    validate_local_source(args.options_source)
    regime = load_regime(args.candidate, args.start_date, args.end_date)

    con = duckdb.connect()
    entries = select_entries(con, args.options_source, regime, args)
    quotes = quote_replay(con, args.options_source, entries, args)
    result = first_pass_trades(entries, quotes, regime, args)
    con.close()

    out = RESEARCH_DIR / f"options001_replay_{args.candidate.lower()}_{args.fill_model}.csv"
    result.to_csv(out, index=False)

    print("OPTIONS-001 first-pass replay")
    print(f"candidate={args.candidate} fill_model={args.fill_model}")
    print(f"eligible_entry_dates={len(regime.index[regime['eligible']])}")
    print(f"selected_entry_dates={len(entries)}")
    print(f"completed_trades={len(result)}")

    if result.empty:
        print("No completed trades. Check source coverage and liquidity filters.")
        return

    print(f"total_pnl={result['pnl'].sum():.2f}")
    print(f"mean_pnl={result['pnl'].mean():.2f}")
    print(f"win_rate={(result['pnl'] > 0).mean():.3f}")
    print(result["exit_reason"].value_counts().to_string())
    print(result.groupby("regime")["pnl"].agg(["count", "mean", "sum"]).to_string())


if __name__ == "__main__":
    main()
