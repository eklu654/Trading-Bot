"""OPTIONS-002 defined-risk SPY iron-condor replay.

Frozen research baseline:
- 45 DTE target, 30-60 DTE eligible
- ~16-delta short call/put
- fixed 2-point wings (one contract)
- 50% credit profit target OR 21 DTE
- no undefined-risk loss stop; max loss is structurally bounded
- conservative bid/ask or midpoint execution
- daily EOD quote reconstruction

This is a research candidate, not a production strategy.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from evaluate_regime_candidates import candidate_labels
from replay_options001 import load_regime, source_sql, validate_local_source

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "data" / "research"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--options-source", required=True)
    p.add_argument("--candidate", default="ALL_DAYS",
                   choices=["CURRENT", "BALANCED", "BROAD_SIDEWAYS", "TURBULENT_ONLY", "ALL_DAYS"])
    p.add_argument("--fill-model", default="conservative", choices=["conservative", "mid"])
    p.add_argument("--target-dte", type=int, default=45)
    p.add_argument("--target-delta", type=float, default=0.16)
    p.add_argument("--wing-width", type=float, default=2.0)
    p.add_argument("--min-dte", type=int, default=30)
    p.add_argument("--max-dte", type=int, default=60)
    p.add_argument("--profit-target", type=float, default=0.50)
    p.add_argument("--exit-dte", type=int, default=21)
    p.add_argument("--start-date", default="2010-01-01")
    p.add_argument("--end-date", default="2025-12-31")
    p.add_argument("--starting-nlv", type=float, default=5000.0)
    p.add_argument("--max-bpr-pct", type=float, default=0.50)
    return p.parse_args()


def select_entries(con, source: str, regime: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    eligible = regime.index[regime["eligible"]]
    if len(eligible) == 0:
        return pd.DataFrame()
    con.register("eligible_dates", pd.DataFrame({"entry_date": eligible}))
    q = f"""
        WITH candidates AS (
            SELECT CAST(o.date AS DATE) entry_date, o.contract_id,
                   CAST(o.expiration AS DATE) expiration, o.strike, o.type,
                   o.bid, o.ask, o.mark, o.volume, o.open_interest, o.delta,
                   datediff('day', CAST(o.date AS DATE), CAST(o.expiration AS DATE)) dte
            FROM {source_sql(source)} o
            INNER JOIN eligible_dates d ON CAST(o.date AS DATE)=d.entry_date
            WHERE CAST(o.expiration AS DATE) BETWEEN
                  CAST(o.date AS DATE)+INTERVAL '{args.min_dte}' DAY
              AND CAST(o.date AS DATE)+INTERVAL '{args.max_dte}' DAY
              AND o.bid > 0 AND o.ask >= o.bid AND o.mark > 0
              AND (o.volume > 0 OR o.open_interest > 0)
        ),
        expiries AS (
            SELECT DISTINCT entry_date, expiration, dte FROM candidates
        ),
        chosen AS (
            SELECT entry_date, expiration FROM (
                SELECT *, row_number() OVER (
                    PARTITION BY entry_date
                    ORDER BY abs(dte-{args.target_dte}), expiration
                ) rn FROM expiries
            ) WHERE rn=1
        ),
        chain AS (
            SELECT c.* FROM candidates c
            INNER JOIN chosen e USING(entry_date, expiration)
        ),
        shorts AS (
            SELECT *, row_number() OVER (
                PARTITION BY entry_date, type
                ORDER BY
                  CASE WHEN lower(type)='call'
                       THEN abs(delta-{args.target_delta})
                       ELSE abs(abs(delta)-{args.target_delta}) END,
                  volume DESC NULLS LAST, open_interest DESC NULLS LAST
            ) rn
            FROM chain
            WHERE (lower(type)='call' AND delta > 0)
               OR (lower(type)='put' AND delta < 0)
        )
        SELECT * FROM shorts WHERE rn=1 ORDER BY entry_date, type
    """
    result = con.execute(q).fetchdf()
    con.unregister("eligible_dates")
    if result.empty:
        return result
    result["type"] = result["type"].str.lower()
    calls = result[result.type == "call"].copy()
    puts = result[result.type == "put"].copy()
    merged = calls.merge(puts, on="entry_date", suffixes=("_call", "_put"))
    return merged.sort_values("entry_date").reset_index(drop=True)


def choose_wings(con, source: str, entries: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if entries.empty:
        return entries
    selected = entries[["entry_date", "expiration_call", "strike_call", "strike_put"]].copy()
    con.register("shorts", selected)
    q = f"""
      SELECT s.*, o.contract_id, o.strike, lower(o.type) type, o.bid, o.ask, o.mark,
             o.volume, o.open_interest
      FROM shorts s
      INNER JOIN {source_sql(source)} o
        ON CAST(o.date AS DATE)=s.entry_date
       AND CAST(o.expiration AS DATE)=s.expiration_call
       AND o.bid > 0 AND o.ask >= o.bid
       AND (o.volume > 0 OR o.open_interest > 0)
      WHERE (lower(o.type)='call' AND o.strike >= s.strike_call + {args.wing_width})
         OR (lower(o.type)='put' AND o.strike <= s.strike_put - {args.wing_width})
      ORDER BY s.entry_date, o.strike
    """
    wings = con.execute(q).fetchdf()
    con.unregister("shorts")
    if wings.empty:
        return pd.DataFrame()
    rows = []
    for date, g in wings.groupby("entry_date"):
        row = entries.loc[entries.entry_date == date].iloc[0].copy()
        calls = g[g.type == "call"].copy()
        puts = g[g.type == "put"].copy()
        if calls.empty or puts.empty:
            continue
        # Nearest available wing at or beyond the requested width.
        call_w = calls.sort_values(["strike", "volume"], ascending=[True, False]).iloc[0]
        put_w = puts.sort_values(["strike", "volume"], ascending=[False, False]).iloc[0]
        if float(call_w["strike"]) <= float(row["strike_call"]) or float(put_w["strike"]) >= float(row["strike_put"]):
            continue
        if float(call_w["strike"]) - float(row["strike_call"]) < args.wing_width - 1e-9:
            continue
        if float(row["strike_put"]) - float(put_w["strike"]) < args.wing_width - 1e-9:
            continue
        row["long_call_id"] = str(call_w["contract_id"])
        row["long_put_id"] = str(put_w["contract_id"])
        row["long_call_strike"] = float(call_w["strike"])
        row["long_put_strike"] = float(put_w["strike"])
        row["wing_width_call"] = float(call_w["strike"]) - float(row["strike_call"])
        row["wing_width_put"] = float(row["strike_put"]) - float(put_w["strike"])
        rows.append(row)
    return pd.DataFrame(rows)


def quote_replay(con, source: str, entries: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()
    ids = []
    for _, r in entries.iterrows():
        ids += [str(r.contract_id_call), str(r.contract_id_put),
                str(r.long_call_id), str(r.long_put_id)]
    selected = entries[["entry_date", "expiration_call", "contract_id_call",
                        "contract_id_put", "long_call_id", "long_put_id"]].copy()
    con.register("selected", selected)
    q = f"""
      SELECT s.entry_date, s.contract_id_call, s.contract_id_put,
             s.long_call_id, s.long_put_id, s.expiration_call expiration,
             CAST(o.date AS DATE) date, o.contract_id, o.bid, o.ask, o.mark
      FROM selected s
      INNER JOIN {source_sql(source)} o
        ON o.contract_id IN (s.contract_id_call, s.contract_id_put,
                             s.long_call_id, s.long_put_id)
       AND CAST(o.date AS DATE) > s.entry_date
       AND CAST(o.date AS DATE) <= s.expiration_call
      ORDER BY s.entry_date, o.date
    """
    result = con.execute(q).fetchdf()
    con.unregister("selected")
    return result


def price(row, field: str) -> float:
    value = row[field]
    return float(value) if pd.notna(value) and float(value) >= 0 else float("nan")


def replay_entries(entries: pd.DataFrame, quotes: pd.DataFrame, regime: pd.DataFrame,
                   args: argparse.Namespace):
    trades, marks = [], []
    for _, r in entries.iterrows():
        entry_date = pd.Timestamp(r.entry_date)
        q = quotes[quotes.entry_date == r.entry_date]
        if q.empty:
            continue
        by_date = q.pivot(index="date", columns="contract_id", values=["bid","ask","mark"])
        ids = [str(r.contract_id_call), str(r.contract_id_put),
               str(r.long_call_id), str(r.long_put_id)]
        field = "mark" if args.fill_model == "mid" else "bid"
        entry_vals = []
        # Credit received: shorts at bid, longs paid at ask.
        for cid, legfield in [(ids[0], "bid"), (ids[1], "bid"), (ids[2], "ask"), (ids[3], "ask")]:
            if ("mark" if args.fill_model == "mid" else legfield, cid) not in by_date.columns:
                entry_vals = []
                break
            f = "mark" if args.fill_model == "mid" else legfield
            entry_vals.append(price({f:f, "value": by_date.loc[entry_date, (f,cid)]} if entry_date in by_date.index else {"value":float("nan")}, "value"))
        if len(entry_vals) != 4 or any(pd.isna(x) for x in entry_vals):
            # Entry quotes are already present in the source row; use those directly.
            if args.fill_model == "mid":
                credit = float(r.mark_call + r.mark_put - r.mark_long_call - r.mark_long_put)
            else:
                credit = float(r.bid_call + r.bid_put - r.ask_long_call - r.ask_long_put)
        else:
            credit = entry_vals[0] + entry_vals[1] - entry_vals[2] - entry_vals[3]
        if credit <= 0:
            continue

        candidate_id = f"{entry_date.date()}:{r.contract_id_call}:{r.contract_id_put}:{r.long_call_id}:{r.long_put_id}"
        exit_date = None
        exit_debit = None
        max_debit = 0.0

        for date, qr in by_date.iterrows():
            vals = {}
            ok = True
            f = "mark" if args.fill_model == "mid" else "ask"
            for cid in ids:
                if (f, cid) not in qr.index or pd.isna(qr[(f,cid)]):
                    ok = False
                    break
                vals[cid] = float(qr[(f,cid)])
            if not ok:
                continue
            debit = vals[ids[0]] + vals[ids[1]] - vals[ids[2]] - vals[ids[3]]
            debit = max(0.0, debit)
            max_debit = max(max_debit, debit)
            underlying = float(regime.loc[pd.Timestamp(date), "spy_close"]) if pd.Timestamp(date) in regime.index else float("nan")
            marks.append({"candidate_id":candidate_id,"date":pd.Timestamp(date),
                          "mark_debit":debit,"underlying_close":underlying})
            dte = (pd.Timestamp(r.expiration_call) - pd.Timestamp(date)).days
            reason = None
            if debit <= credit * (1 - args.profit_target):
                reason = "PROFIT_50"
            elif dte <= args.exit_dte:
                reason = "DTE_21"
            if reason:
                exit_date = pd.Timestamp(date)
                exit_debit = debit
                break
        if exit_date is None:
            continue
        trades.append({
            "candidate_id":candidate_id,"entry_date":entry_date,"exit_date":exit_date,
            "expiration":pd.Timestamp(r.expiration_call),"entry_credit":credit,
            "exit_debit":exit_debit,"pnl":(credit-exit_debit)*100,
            "max_debit":max_debit,"max_loss_pnl":(credit-max_debit)*100,
            "entry_dte":(pd.Timestamp(r.expiration_call)-entry_date).days,
            "exit_dte":(pd.Timestamp(r.expiration_call)-exit_date).days,
            "call_strike":float(r.strike_call),"put_strike":float(r.strike_put),
            "long_call_strike":float(r.long_call_strike),"long_put_strike":float(r.long_put_strike),
            "call_delta":float(r.delta_call),"put_delta":float(r.delta_put),
            "regime":regime.loc[entry_date,"entry_regime"],
            "max_defined_loss":max(float(r.wing_width_call),float(r.wing_width_put))*100-credit*100,
        })
    return pd.DataFrame(trades), pd.DataFrame(marks)


def main():
    args = parse_args()
    validate_local_source(args.options_source)
    regime = load_regime(args.candidate, args.start_date, args.end_date)
    con = duckdb.connect()
    entries = select_entries(con, args.options_source, regime, args)
    entries = choose_wings(con, args.options_source, entries, args)
    quotes = quote_replay(con, args.options_source, entries)
    trades, marks = replay_entries(entries, quotes, regime, args)
    con.close()

    if entries.empty:
        print("No feasible chain candidates selected.")
        return

    candidate_rows = []
    for _, r in entries.iterrows():
        if args.fill_model == "mid":
            credit = float(r.mark_call + r.mark_put - r.mark_long_call - r.mark_long_put)
        else:
            # Wing quotes are added by choose_wings below.
            credit = float(r.bid_call + r.bid_put - r.ask_long_call - r.ask_long_put)
        if credit <= 0:
            continue
        candidate_id = f"{pd.Timestamp(r.entry_date).date()}:{r.contract_id_call}:{r.contract_id_put}:{r.long_call_id}:{r.long_put_id}"
        candidate_rows.append({
            "candidate_id":candidate_id,"entry_date":pd.Timestamp(r.entry_date),
            "exit_date":pd.NaT,"entry_credit":credit,
            "call_strike":float(r.strike_call),"put_strike":float(r.strike_put),
            "long_call_strike":float(r.long_call_strike),"long_put_strike":float(r.long_put_strike),
            "wing_width_call":float(r.wing_width_call),"wing_width_put":float(r.wing_width_put),
            "underlying_close":float(regime.loc[pd.Timestamp(r.entry_date),"spy_close"]),
            "max_defined_loss":max(float(r.wing_width_call),float(r.wing_width_put))*100-credit*100,
        })
    candidates = pd.DataFrame(candidate_rows)
    outcomes = trades[["candidate_id","exit_date","pnl","exit_debit"]].copy() if not trades.empty else pd.DataFrame(columns=["candidate_id","exit_date","pnl","exit_debit"])
    marks.to_csv(RESEARCH_DIR / f"options002_replay_{args.candidate.lower()}_{args.fill_model}_candidate_marks.csv", index=False)
    candidates.to_csv(RESEARCH_DIR / f"options002_replay_{args.candidate.lower()}_{args.fill_model}_candidates.csv", index=False)
    outcomes.to_csv(RESEARCH_DIR / f"options002_replay_{args.candidate.lower()}_{args.fill_model}_candidate_outcomes.csv", index=False)
    out = RESEARCH_DIR / f"options002_replay_{args.candidate.lower()}_{args.fill_model}.csv"
    trades.to_csv(out, index=False)

    print("OPTIONS-002 iron-condor replay")
    print(f"candidate={args.candidate} fill_model={args.fill_model} wing_width={args.wing_width}")
    print(f"selected_entry_dates={len(entries)} completed_trades={len(trades)}")
    if not trades.empty:
        print(f"total_pnl={trades.pnl.sum():.2f}")
        print(f"win_rate={(trades.pnl>0).mean():.3f}")
        print(f"worst_trade={trades.pnl.min():.2f}")
        print(trades.groupby("regime").pnl.agg(["count","mean","sum"]).to_string())


if __name__ == "__main__":
    main()
