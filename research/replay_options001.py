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
- optional loss benchmark for comparison; <=0 disables it
- conservative bid/ask or midpoint execution

This is a daily EOD reconstruction, not an intraday execution simulation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

try:
    from evaluate_regime_candidates import candidate_labels
except ModuleNotFoundError:
    from research.evaluate_regime_candidates import candidate_labels

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "data" / "research"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--options-source", required=True,
                   help="Local parquet glob or HTTP(S) parquet URL")
    p.add_argument("--candidate", default="BROAD_SIDEWAYS",
                   choices=["CURRENT", "BALANCED", "BROAD_SIDEWAYS", "TURBULENT_ONLY", "ALL_DAYS"])
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

    if candidate == "ALL_DAYS":
        frame["entry_regime"] = "ALL_DAYS"
        frame["eligible"] = True
        return frame.loc[start:end]
    if candidate == "TURBULENT_ONLY":
        labels = pd.Series(
            "TURBULENT_HIGH_VOL",
            index=frame.index,
        ).where(frame["vix_percentile252"] >= 0.90, "TRENDING_NORMAL").shift(1)
        frame["entry_regime"] = labels
        frame["eligible"] = labels == "TURBULENT_HIGH_VOL"
        return frame.loc[start:end]

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
        expiry_candidates AS (
            SELECT DISTINCT entry_date, expiration, dte
            FROM candidates
        ),
        chosen_expiry AS (
            SELECT entry_date, expiration
            FROM (
                SELECT
                    entry_date,
                    expiration,
                    row_number() OVER (
                        PARTITION BY entry_date
                        ORDER BY abs(dte - {args.target_dte}), expiration
                    ) AS expiry_rank
                FROM expiry_candidates
            )
            WHERE expiry_rank = 1
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


def candidate_mark_ledger(
    entries: pd.DataFrame,
    quotes: pd.DataFrame,
    args: argparse.Namespace,
    regime: pd.DataFrame,
) -> pd.DataFrame:
    """Persist daily option debits and underlying closes for account risk marks."""
    if entries.empty or quotes.empty:
        return pd.DataFrame(columns=["candidate_id", "date", "mark_debit", "underlying_close", "mark_model"])

    rows = []
    for _, row in entries.iterrows():
        candidate_id = row.get(
            "candidate_id",
            f"{pd.Timestamp(row['entry_date']).date()}:{row['contract_id_call']}:{row['contract_id_put']}",
        )
        call_id = str(row["contract_id_call"])
        put_id = str(row["contract_id_put"])
        q = quotes[quotes["entry_date"] == row["entry_date"]]
        if q.empty:
            continue
        by_date = q.pivot(index="date", columns="contract_id", values=["bid", "ask", "mark"])
        field = "mark" if args.fill_model == "mid" else "ask"
        for date, quote_row in by_date.iterrows():
            call_key = (field, call_id)
            put_key = (field, put_id)
            if call_key not in quote_row or put_key not in quote_row:
                continue
            call_value = quote_row[call_key]
            put_value = quote_row[put_key]
            if pd.isna(call_value) or pd.isna(put_value):
                continue
            rows.append({
                "candidate_id": candidate_id,
                "date": pd.Timestamp(date),
                "mark_debit": float(call_value + put_value),
                "underlying_close": float(regime.loc[pd.Timestamp(date), "spy_close"])
                    if pd.Timestamp(date) in regime.index else float("nan"),
                "mark_model": field,
            })
    return pd.DataFrame(rows)


def candidate_trade_outcomes(
    entries: pd.DataFrame,
    quotes: pd.DataFrame,
    regime: pd.DataFrame,
    args: argparse.Namespace,
    *,
    enforce_one_position: bool = True,
) -> pd.DataFrame:
    """Reconstruct each candidate independently unless baseline sequencing is requested."""
    if entries.empty or quotes.empty:
        return pd.DataFrame()

    trades = []
    active_until = pd.Timestamp.min

    for entry_date, row in entries.iterrows():
        entry_date = pd.Timestamp(row["entry_date"])
        if enforce_one_position and entry_date <= active_until:
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

        max_debit = 0.0
        first_challenge = None
        challenge_side = None

        for date, quote_row in by_date.iterrows():
            if (close_field, call_id) not in quote_row or (close_field, put_id) not in quote_row:
                continue
            call_exit = quote_row[(close_field, call_id)]
            put_exit = quote_row[(close_field, put_id)]
            if pd.isna(call_exit) or pd.isna(put_exit):
                continue

            debit = float(call_exit + put_exit)
            max_debit = max(max_debit, debit)
            dte = (expiry - pd.Timestamp(date)).days
            underlying_close = regime.loc[pd.Timestamp(date), "spy_close"] if pd.Timestamp(date) in regime.index else float("nan")
            current_challenge = None
            if pd.notna(underlying_close):
                if underlying_close >= float(row["strike_call"]):
                    current_challenge = "CALL"
                elif underlying_close <= float(row["strike_put"]):
                    current_challenge = "PUT"
            if first_challenge is None and current_challenge is not None:
                first_challenge = pd.Timestamp(date)
                challenge_side = current_challenge
            reason = None

            if debit <= credit * (1 - args.profit_target):
                reason = "PROFIT_50"
            elif args.loss_credit_multiple > 0 and debit >= credit * args.loss_credit_multiple:
                reason = f"LOSS_{args.loss_credit_multiple:g}X_CREDIT"
            elif dte <= args.exit_dte:
                reason = "DTE_21"

            if reason:
                trades.append({
                    "candidate_id": row.get("candidate_id", f"{entry_date.date()}:{call_id}:{put_id}"),
                    "entry_date": entry_date,
                    "exit_date": pd.Timestamp(date),
                    "expiration": expiry,
                    "entry_credit": credit,
                    "exit_debit": debit,
                    "pnl": (credit - debit) * 100,
                    "max_debit": max_debit,
                    "max_loss_pnl": (credit - max_debit) * 100,
                    "first_challenge_date": first_challenge,
                    "challenge_side": challenge_side,
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
                if enforce_one_position:
                    active_until = pd.Timestamp(date)
                break

    return pd.DataFrame(trades)


def first_pass_trades(
    entries: pd.DataFrame,
    quotes: pd.DataFrame,
    regime: pd.DataFrame,
    args: argparse.Namespace,
) -> pd.DataFrame:
    """Baseline non-overlapping trade-economics replay."""
    return candidate_trade_outcomes(
        entries, quotes, regime, args, enforce_one_position=True
    )


def main() -> None:
    args = parse_args()
    validate_local_source(args.options_source)
    regime = load_regime(args.candidate, args.start_date, args.end_date)

    con = duckdb.connect()
    entries = select_entries(con, args.options_source, regime, args)
    if not entries.empty:
        entries["candidate_id"] = (
            entries["entry_date"].astype(str)
            + ":"
            + entries["contract_id_call"].astype(str)
            + ":"
            + entries["contract_id_put"].astype(str)
        )
    quotes = quote_replay(con, args.options_source, entries, args)
    result = first_pass_trades(entries, quotes, regime, args)
    independent_outcomes = candidate_trade_outcomes(
        entries, quotes, regime, args, enforce_one_position=False
    )
    candidate_marks = candidate_mark_ledger(entries, quotes, args, regime)
    con.close()

    # Persist the complete candidate universe separately from completed trades.
    # Account feasibility must evaluate every generated candidate, not only
    # candidates that happened to complete a trade.
    candidate_ledger = entries.copy()
    candidate_ledger["underlying_close"] = candidate_ledger["entry_date"].map(
        regime["spy_close"]
    )
    if args.fill_model == "conservative":
        candidate_ledger["entry_credit"] = (
            candidate_ledger["bid_call"] + candidate_ledger["bid_put"]
        )
    else:
        candidate_ledger["entry_credit"] = (
            candidate_ledger["mark_call"] + candidate_ledger["mark_put"]
        )
    loss_tag = "nostop" if args.loss_credit_multiple <= 0 else f"loss{args.loss_credit_multiple:g}x"
    stem = f"options001_replay_{args.candidate.lower()}_{args.fill_model}_{loss_tag}"
    candidate_ledger.to_csv(RESEARCH_DIR / f"{stem}_candidates.csv", index=False)
    independent_outcomes.to_csv(
        RESEARCH_DIR / f"{stem}_candidate_outcomes.csv", index=False
    )
    candidate_marks.to_csv(
        RESEARCH_DIR / f"{stem}_candidate_marks.csv", index=False
    )
    out = RESEARCH_DIR / f"{stem}.csv"
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
    challenged = result["first_challenge_date"].notna()
    print(f"challenged_trades={challenged.sum()}")
    if challenged.any():
        print(f"challenge_rate={challenged.mean():.3f}")
        print(result.loc[challenged, "challenge_side"].value_counts().to_string())
        print(result.groupby("challenge_side", dropna=False)["pnl"].agg(["count", "mean", "sum"]).to_string())
        print(f"worst_max_loss_pnl={result['max_loss_pnl'].min():.2f}")

if __name__ == "__main__":
    main()
