"""OPTIONS-001 defense replay: no adjustment vs deterministic roll of the untested leg.

This research extension uses the same entry/exit framework as replay_options001.py,
but tests one defensive adjustment after the first EOD challenge:
- challenge = SPY close reaches/breaches a current short strike
- ROLL_UNTESTED = close the untested short and replace it at the same expiry
  with the nearest liquid strike halfway from its old strike toward spot
- the replacement must remain on the untested side of spot and the tested strike
- at most one adjustment is allowed per trade in this first defense experiment

Execution is conservative bid/ask or midpoint. This is an EOD reconstruction,
not an intraday execution simulation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from evaluate_regime_candidates import candidate_labels
from replay_options001 import (
    RESEARCH_DIR,
    load_regime,
    select_entries,
    source_sql,
    validate_local_source,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--options-source", required=True)
    p.add_argument("--candidate", default="BROAD_SIDEWAYS",
                   choices=["CURRENT", "BALANCED", "BROAD_SIDEWAYS", "TURBULENT_ONLY"])
    p.add_argument("--defense", default="none", choices=["none", "roll-untested"])
    p.add_argument("--fill-model", default="conservative", choices=["conservative", "mid"])
    p.add_argument("--target-dte", type=int, default=45)
    p.add_argument("--target-delta", type=float, default=0.16)
    p.add_argument("--min-dte", type=int, default=30)
    p.add_argument("--max-dte", type=int, default=60)
    p.add_argument("--profit-target", type=float, default=0.50)
    p.add_argument("--exit-dte", type=int, default=21)
    p.add_argument("--start-date", default="2010-01-01")
    p.add_argument("--end-date", default="2025-12-31")
    return p.parse_args()


def challenge_events(
    con: duckdb.DuckDBPyConnection,
    source: str,
    entries: pd.DataFrame,
    regime: pd.DataFrame,
) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    selected = entries[[
        "entry_date", "contract_id_call", "contract_id_put", "expiration_call",
        "strike_call", "strike_put",
    ]].rename(columns={"expiration_call": "expiration"})
    con.register("selected_entries", selected)
    q = f"""
        SELECT
            s.entry_date,
            s.contract_id_call,
            s.contract_id_put,
            s.expiration,
            s.strike_call,
            s.strike_put,
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
    if quotes.empty:
        return quotes

    out = []
    for entry_date, qg in quotes.groupby("entry_date", sort=True):
        row = entries[entries["entry_date"] == entry_date].iloc[0]
        for date, day in qg.groupby("date", sort=True):
            spot = regime.loc[pd.Timestamp(date), "spy_close"] if pd.Timestamp(date) in regime.index else float("nan")
            if pd.isna(spot):
                continue
            call = day[day["contract_id"].astype(str) == str(row["contract_id_call"])]
            put = day[day["contract_id"].astype(str) == str(row["contract_id_put"])]
            if call.empty or put.empty:
                continue
            if float(spot) >= float(row["strike_call"]):
                out.append({"entry_date": entry_date, "challenge_date": date, "side": "CALL",
                            "spot": float(spot), "tested_strike": float(row["strike_call"]),
                            "untested_strike": float(row["strike_put"]),
                            "untested_type": "put", "expiration": row["expiration_call"]})
                break
            if float(spot) <= float(row["strike_put"]):
                out.append({"entry_date": entry_date, "challenge_date": date, "side": "PUT",
                            "spot": float(spot), "tested_strike": float(row["strike_put"]),
                            "untested_strike": float(row["strike_call"]),
                            "untested_type": "call", "expiration": row["expiration_call"]})
                break
    return pd.DataFrame(out)


def choose_roll_contract(
    con: duckdb.DuckDBPyConnection,
    source: str,
    events: pd.DataFrame,
) -> pd.DataFrame:
    if events.empty:
        return events

    con.register("roll_events", events[[
        "entry_date", "challenge_date", "side", "spot", "tested_strike",
        "untested_strike", "untested_type", "expiration",
    ]])
    q = f"""
        WITH candidates AS (
            SELECT
                e.entry_date,
                e.challenge_date,
                e.side,
                e.spot,
                e.tested_strike,
                e.untested_strike,
                e.untested_type,
                e.expiration,
                o.contract_id,
                o.strike,
                o.type,
                o.bid,
                o.ask,
                o.mark,
                o.volume,
                o.open_interest,
                o.delta,
                abs(o.strike - ((e.untested_strike + e.spot) / 2.0)) AS strike_distance
            FROM roll_events e
            INNER JOIN {source_sql(source)} o
              ON CAST(o.date AS DATE) = e.challenge_date
             AND CAST(o.expiration AS DATE) = e.expiration
             AND lower(o.type) = e.untested_type
            WHERE o.bid > 0
              AND o.ask >= o.bid
              AND o.mark > 0
              AND (o.volume > 0 OR o.open_interest > 0)
              AND (
                (e.untested_type = 'put' AND o.strike < e.spot AND o.strike < e.tested_strike)
                OR
                (e.untested_type = 'call' AND o.strike > e.spot AND o.strike > e.tested_strike)
              )
        ),
        ranked AS (
            SELECT *,
                row_number() OVER (
                    PARTITION BY entry_date
                    ORDER BY strike_distance, volume DESC NULLS LAST,
                             open_interest DESC NULLS LAST, strike
                ) AS rn
            FROM candidates
        )
        SELECT * FROM ranked WHERE rn = 1
    """
    result = con.execute(q).fetchdf()
    con.unregister("roll_events")
    return result


def fetch_contract_quotes(
    con: duckdb.DuckDBPyConnection,
    source: str,
    contracts: pd.DataFrame,
) -> pd.DataFrame:
    if contracts.empty:
        return pd.DataFrame()
    con.register("contracts", contracts[["entry_date", "contract_id", "from_date", "expiration"]])
    q = f"""
        SELECT
            c.entry_date,
            c.contract_id,
            CAST(o.date AS DATE) AS date,
            o.bid, o.ask, o.mark
        FROM contracts c
        INNER JOIN {source_sql(source)} o
          ON o.contract_id = c.contract_id
         AND CAST(o.date AS DATE) >= c.from_date
         AND CAST(o.date AS DATE) <= c.expiration
        ORDER BY c.entry_date, o.date
    """
    result = con.execute(q).fetchdf()
    con.unregister("contracts")
    return result


def price(row: pd.Series, model: str, action: str) -> float:
    # action=open_short uses bid; close_short uses ask in conservative mode.
    if model == "mid":
        return float(row["mark"])
    return float(row["bid"] if action == "open_short" else row["ask"])


def replay(
    con: duckdb.DuckDBPyConnection,
    source: str,
    entries: pd.DataFrame,
    regime: pd.DataFrame,
    args: argparse.Namespace,
) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    events = challenge_events(con, source, entries, regime)
    rolls = choose_roll_contract(con, source, events) if args.defense == "roll-untested" else pd.DataFrame()

    # Original legs are enough to discover the first challenge and to replay
    # no-adjustment trades. For adjusted trades, fetch the replacement leg
    # beginning on its challenge date.
    original_contracts = []
    for _, r in entries.iterrows():
        original_contracts.extend([
            {"entry_date": r["entry_date"], "contract_id": str(r["contract_id_call"]),
             "from_date": pd.Timestamp(r["entry_date"]) + pd.Timedelta(days=1),
             "expiration": pd.Timestamp(r["expiration_call"])},
            {"entry_date": r["entry_date"], "contract_id": str(r["contract_id_put"]),
             "from_date": pd.Timestamp(r["entry_date"]) + pd.Timedelta(days=1),
             "expiration": pd.Timestamp(r["expiration_call"])},
        ])
    original_quotes = fetch_contract_quotes(con, source, pd.DataFrame(original_contracts))
    if rolls.empty:
        roll_quotes = pd.DataFrame()
    else:
        roll_contracts = rolls[["entry_date", "contract_id", "expiration"]].copy()
        roll_contracts["from_date"] = pd.to_datetime(rolls["challenge_date"])
        roll_quotes = fetch_contract_quotes(con, source, roll_contracts)

    entry_lookup = entries.set_index("entry_date")
    roll_lookup = rolls.set_index("entry_date") if not rolls.empty else pd.DataFrame()
    trades = []
    active_until = pd.Timestamp.min

    for _, row in entries.iterrows():
        entry_date = pd.Timestamp(row["entry_date"])
        if entry_date <= active_until:
            continue

        call_id = str(row["contract_id_call"])
        put_id = str(row["contract_id_put"])
        expiry = pd.Timestamp(row["expiration_call"])
        initial_credit = (
            float(row["mark_call"] if args.fill_model == "mid" else row["bid_call"])
            + float(row["mark_put"] if args.fill_model == "mid" else row["bid_put"])
        )
        if initial_credit <= 0:
            continue

        oq = original_quotes[original_quotes["entry_date"] == row["entry_date"]]
        rq = roll_quotes[roll_quotes["entry_date"] == row["entry_date"]] if not roll_quotes.empty else pd.DataFrame()
        roll = roll_lookup.loc[entry_date] if args.defense == "roll-untested" and entry_date in roll_lookup.index else None

        net_credit = initial_credit
        adjusted = False
        adjustment = 0.0
        challenge_date = None
        challenge_side = None
        max_debit = 0.0
        exit_reason = None
        exit_date = None
        exit_debit = None
        current_call = call_id
        current_put = put_id

        dates = sorted(set(oq["date"].tolist()) | set(rq["date"].tolist()))
        for date in dates:
            date = pd.Timestamp(date)
            day = oq[oq["date"] == date]
            if day.empty:
                continue
            vals = {str(x["contract_id"]): x for _, x in day.iterrows()}
            call_row = vals.get(current_call)
            put_row = vals.get(current_put)

            if adjusted and current_call != call_id:
                rday = rq[rq["date"] == date]
                if not rday.empty:
                    vals.update({str(x["contract_id"]): x for _, x in rday.iterrows()})
                call_row = vals.get(current_call)
                put_row = vals.get(current_put)
            elif adjusted and current_put != put_id:
                rday = rq[rq["date"] == date]
                if not rday.empty:
                    vals.update({str(x["contract_id"]): x for _, x in rday.iterrows()})
                call_row = vals.get(current_call)
                put_row = vals.get(current_put)

            if call_row is None or put_row is None:
                continue

            call_close = price(call_row, args.fill_model, "close_short")
            put_close = price(put_row, args.fill_model, "close_short")
            debit = call_close + put_close
            max_debit = max(max_debit, debit)

            if not adjusted and roll is not None and date >= pd.Timestamp(roll["challenge_date"]):
                if date == pd.Timestamp(roll["challenge_date"]):
                    old_type = str(roll["untested_type"])
                    old_row = put_row if old_type == "put" else call_row
                    new_id = str(roll["contract_id"])
                    rday = rq[rq["date"] == date]
                    new_rows = rday[rday["contract_id"].astype(str) == new_id]
                    if not new_rows.empty:
                        new_row = new_rows.iloc[0]
                        close_old = price(old_row, args.fill_model, "close_short")
                        open_new = price(new_row, args.fill_model, "open_short")
                        adjustment = open_new - close_old
                        net_credit += adjustment
                        if old_type == "put":
                            current_put = new_id
                        else:
                            current_call = new_id
                        adjusted = True
                        challenge_date = date
                        challenge_side = str(roll["side"])
                        # Re-price the active position after the adjustment.
                        call_row = new_row if old_type == "call" else call_row
                        put_row = new_row if old_type == "put" else put_row
                        call_close = price(call_row, args.fill_model, "close_short")
                        put_close = price(put_row, args.fill_model, "close_short")
                        debit = call_close + put_close
                        max_debit = max(max_debit, debit)

            dte = (expiry - date).days
            if net_credit > 0 and debit <= net_credit * (1 - args.profit_target):
                exit_reason = "PROFIT_50"
            elif dte <= args.exit_dte:
                exit_reason = "DTE_21"

            if exit_reason:
                exit_date = date
                exit_debit = debit
                break

        if exit_reason is None or exit_date is None or exit_debit is None:
            continue

        trades.append({
            "entry_date": entry_date,
            "exit_date": exit_date,
            "expiration": expiry,
            "initial_credit": initial_credit,
            "adjustment_pnl": adjustment * 100,
            "net_credit": net_credit,
            "exit_debit": exit_debit,
            "pnl": (net_credit - exit_debit) * 100,
            "max_loss_pnl": (net_credit - max_debit) * 100,
            "adjusted": adjusted,
            "challenge_date": challenge_date,
            "challenge_side": challenge_side,
            "rolled_contract_id": str(roll["contract_id"]) if adjusted else None,
            "rolled_strike": float(roll["strike"]) if adjusted else None,
            "rolled_delta": float(roll["delta"]) if adjusted else None,
            "entry_dte": (expiry - entry_date).days,
            "exit_dte": (expiry - exit_date).days,
            "call_strike": float(row["strike_call"]),
            "put_strike": float(row["strike_put"]),
            "call_contract_id": call_id,
            "put_contract_id": put_id,
            "final_call_contract_id": current_call,
            "final_put_contract_id": current_put,
            "regime": regime.loc[entry_date, "entry_regime"],
            "exit_reason": exit_reason,
        })
        active_until = exit_date

    return pd.DataFrame(trades)


def main() -> None:
    args = parse_args()
    validate_local_source(args.options_source)
    regime = load_regime(args.candidate, args.start_date, args.end_date)
    con = duckdb.connect()
    entries = select_entries(con, args.options_source, regime, args)
    result = replay(con, args.options_source, entries, regime, args)
    con.close()

    tag = args.defense.replace("-", "_")
    out = RESEARCH_DIR / f"options001_defense_{args.candidate.lower()}_{args.fill_model}_{tag}.csv"
    result.to_csv(out, index=False)

    print("OPTIONS-001 defense replay")
    print(f"candidate={args.candidate} defense={args.defense} fill_model={args.fill_model}")
    print(f"selected_entry_dates={len(entries)} completed_trades={len(result)}")
    if result.empty:
        print("No completed trades.")
        return
    print(f"total_pnl={result['pnl'].sum():.2f}")
    print(f"mean_pnl={result['pnl'].mean():.2f}")
    print(f"win_rate={(result['pnl'] > 0).mean():.3f}")
    print(result["exit_reason"].value_counts().to_string())
    print(f"adjusted_trades={int(result['adjusted'].sum())}")
    if result["adjusted"].any():
        print(f"adjustment_rate={result['adjusted'].mean():.3f}")
        print(f"mean_adjustment_pnl={result.loc[result['adjusted'], 'adjustment_pnl'].mean():.2f}")
    print(f"worst_max_loss_pnl={result['max_loss_pnl'].min():.2f}")
    print(result.groupby("regime")["pnl"].agg(["count", "mean", "sum"]).to_string())


if __name__ == "__main__":
    main()
