"""Batch OPTIONS-002/defense replays using one immutable DuckDB chain table.

The historical Parquet rows are materialized once per runner and reused across
all variants. This is an I/O/process optimization only: each variant still
uses the existing selection, fill, exit, and replay functions unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from replay_options002 import attach_wings, replay as replay002, select_entries as select_entries002
from replay_options001 import load_regime, validate_local_source, source_sql
from replay_options001_defense import replay as replay_defense
from replay_options001_defense import select_entries as select_entries001


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "data" / "research"
SOURCE = "table:options_cache"


def materialize(con: duckdb.DuckDBPyConnection, source: str) -> None:
    escaped = source.replace("'", "''")
    con.execute(
        f"CREATE TEMP TABLE options_cache AS "
        f"SELECT * FROM read_parquet('{escaped}', hive_partitioning=false)"
    )


def write_options002(con, regime_name: str, fill: str) -> None:
    regime = load_regime(regime_name, "2010-01-01", "2025-12-31")
    args = argparse.Namespace(
        candidate=regime_name,
        fill_model=fill,
        target_dte=45,
        target_delta=0.16,
        long_delta=None,
        wing_width=2.0,
        strategy_label=None,
        min_dte=30,
        max_dte=60,
        profit_target=0.50,
        exit_dte=21,
        start_date="2010-01-01",
        end_date="2025-12-31",
    )
    entries = attach_wings(
        con, SOURCE, select_entries002(con, SOURCE, regime, args), args
    )
    label = "delta16_w2"
    stem = f"options002_{label}_{regime_name.lower()}_{fill}"

    if entries.empty:
        pd.DataFrame().to_csv(RESEARCH_DIR / f"{stem}_candidates.csv", index=False)
        pd.DataFrame(columns=["candidate_id","exit_date","pnl","exit_debit"]).to_csv(
            RESEARCH_DIR / f"{stem}_candidate_outcomes.csv", index=False
        )
        pd.DataFrame(columns=["candidate_id","date","mark_debit","underlying_close"]).to_csv(
            RESEARCH_DIR / f"{stem}_candidate_marks.csv", index=False
        )
        pd.DataFrame().to_csv(RESEARCH_DIR / f"{stem}.csv", index=False)
        return

    selected = entries[
        ["entry_date","expiration_call","contract_id_call","contract_id_put",
         "long_call_id","long_put_id"]
    ]
    con.register("selected", selected)
    q = f"""SELECT s.entry_date,s.contract_id_call,s.contract_id_put,s.long_call_id,s.long_put_id,
                   s.expiration_call expiration,CAST(o.date AS DATE) date,o.contract_id,o.bid,o.ask,o.mark
            FROM selected s JOIN {source_sql(SOURCE)} o
              ON o.contract_id IN(s.contract_id_call,s.contract_id_put,s.long_call_id,s.long_put_id)
             AND CAST(o.date AS DATE)>s.entry_date AND CAST(o.date AS DATE)<=s.expiration_call
            ORDER BY s.entry_date,o.date"""
    quotes = con.execute(q).fetchdf()
    con.unregister("selected")

    trades, marks = replay002(entries, quotes, regime, args)
    candidates = []
    for _, row in entries.iterrows():
        credit = (
            float(row.mark_call + row.mark_put - row.mark_long_call - row.mark_long_put)
            if fill == "mid"
            else float(row.bid_call + row.bid_put - row.ask_long_call - row.ask_long_put)
        )
        if credit <= 0:
            continue
        cid = f"{pd.Timestamp(row.entry_date).date()}:{row.contract_id_call}:{row.contract_id_put}:{row.long_call_id}:{row.long_put_id}"
        candidates.append({
            "candidate_id": cid,
            "entry_date": pd.Timestamp(row.entry_date),
            "entry_credit": credit,
            "call_strike": float(row.strike_call),
            "put_strike": float(row.strike_put),
            "long_call_strike": float(row.long_call_strike),
            "long_put_strike": float(row.long_put_strike),
            "wing_width_call": float(row.wing_width_call),
            "wing_width_put": float(row.wing_width_put),
            "underlying_close": float(regime.loc[pd.Timestamp(row.entry_date), "spy_close"]),
            "max_defined_loss": max(float(row.wing_width_call), float(row.wing_width_put))*100-credit*100,
        })
    pd.DataFrame(candidates).to_csv(RESEARCH_DIR / f"{stem}_candidates.csv", index=False)
    (trades[["candidate_id","exit_date","pnl","exit_debit"]]
     if not trades.empty else
     pd.DataFrame(columns=["candidate_id","exit_date","pnl","exit_debit"])).to_csv(
        RESEARCH_DIR / f"{stem}_candidate_outcomes.csv", index=False
    )
    marks.to_csv(RESEARCH_DIR / f"{stem}_candidate_marks.csv", index=False)
    trades.to_csv(RESEARCH_DIR / f"{stem}.csv", index=False)
    print(f"OPTIONS-002 {regime_name} {fill}: entries={len(entries)} trades={len(trades)}", flush=True)


def write_defense(con, fill: str, defense: str) -> None:
    regime = load_regime("BROAD_SIDEWAYS", "2010-01-01", "2025-12-31")
    args = argparse.Namespace(
        candidate="BROAD_SIDEWAYS",
        defense=defense,
        fill_model=fill,
        target_dte=45,
        target_delta=0.16,
        min_dte=30,
        max_dte=60,
        profit_target=0.50,
        exit_dte=21,
        start_date="2010-01-01",
        end_date="2025-12-31",
    )
    entries = select_entries001(con, SOURCE, regime, args)
    trades = replay_defense(con, SOURCE, entries, regime, args)
    stem = f"options001_defense_broad_sideways_{fill}_{defense}"
    summary_stem = f"options001_defense_summary_broad_sideways_{fill}_{defense}"
    trades.to_csv(RESEARCH_DIR / f"{stem}.csv", index=False)

    if trades.empty:
        summary = pd.DataFrame([{"trades": 0, "total_pnl": 0.0, "win_rate": float("nan")}])
    else:
        summary = pd.DataFrame([{
            "trades": len(trades),
            "total_pnl": float(trades["pnl"].sum()),
            "win_rate": float((trades["pnl"] > 0).mean()),
        }])
    summary.to_csv(RESEARCH_DIR / f"{summary_stem}.csv", index=False)
    print(f"DEFENSE {fill} {defense}: trades={len(trades)}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--options-source", required=True)
    args = p.parse_args()
    validate_local_source(args.options_source)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("PRAGMA threads=2")
    print("Materializing immutable option chain once...", flush=True)
    materialize(con, args.options_source)
    print("Option chain ready; running six OPTIONS-002 + four defense variants.", flush=True)

    for regime in ("ALL_DAYS", "BROAD_SIDEWAYS", "TURBULENT_ONLY"):
        for fill in ("conservative", "mid"):
            write_options002(con, regime, fill)

    for defense in ("none", "roll-untested"):
        for fill in ("conservative", "mid"):
            write_defense(con, fill, defense)

    con.close()


if __name__ == "__main__":
    main()
