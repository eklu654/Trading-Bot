"""First-pass OPTIONS-001 SPY short-strangle replay.

Expected local data:
    data/options/spy/options_*.parquet

This baseline tests deterministic entry/exit mechanics only. Defensive rolls
are intentionally a separate later variant.
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
    p.add_argument("--options-glob", required=True)
    p.add_argument("--candidate", default="BROAD_SIDEWAYS",
                   choices=["CURRENT", "BALANCED", "BROAD_SIDEWAYS", "TURBULENT_ONLY"])
    p.add_argument("--fill-model", default="conservative", choices=["conservative", "mid"])
    p.add_argument("--target-dte", type=int, default=45)
    p.add_argument("--target-delta", type=float, default=0.16)
    p.add_argument("--min-dte", type=int, default=30)
    p.add_argument("--max-dte", type=int, default=60)
    p.add_argument("--profit-target", type=float, default=0.50)
    p.add_argument("--exit-dte", type=int, default=21)
    p.add_argument("--loss-credit-multiple", type=float, default=2.0)
    return p.parse_args()


def load_regime(candidate: str) -> pd.DataFrame:
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
    return frame


def sql_date(value: pd.Timestamp) -> str:
    return value.strftime("%Y-%m-%d")


def choose_contracts(con, glob: str, date: pd.Timestamp, args: argparse.Namespace):
    q = """
        SELECT contract_id, expiration, strike, type, bid, ask, mark,
               volume, open_interest, delta, implied_volatility
        FROM read_parquet(?)
        WHERE date = ?
          AND expiration BETWEEN ?::DATE AND ?::DATE
          AND bid > 0 AND ask >= bid AND mark > 0
          AND (volume > 0 OR open_interest > 0)
    """
    min_exp = sql_date(date + pd.Timedelta(days=args.min_dte))
    max_exp = sql_date(date + pd.Timedelta(days=args.max_dte))
    rows = con.execute(q, [glob, sql_date(date), min_exp, max_exp]).fetchdf()
    if rows.empty:
        return None

    rows["dte"] = (pd.to_datetime(rows["expiration"]) - date).dt.days
    rows = rows[(rows["dte"] >= args.min_dte) & (rows["dte"] <= args.max_dte)]
    if rows.empty:
        return None

    expiry_table = rows.groupby("expiration")["dte"].first().to_frame()
    expiry_table["distance"] = (expiry_table["dte"] - args.target_dte).abs()
    expiry = expiry_table.sort_values(["distance", "dte"]).index[0]
    chain = rows[rows["expiration"] == expiry].copy()

    calls = chain[(chain["type"].str.lower() == "call") & (chain["delta"] > 0)].copy()
    puts = chain[(chain["type"].str.lower() == "put") & (chain["delta"] < 0)].copy()
    if calls.empty or puts.empty:
        return None

    calls["delta_distance"] = (calls["delta"] - args.target_delta).abs()
    puts["delta_distance"] = (puts["delta"].abs() - args.target_delta).abs()

    call = calls.sort_values(
        ["delta_distance", "volume", "open_interest"],
        ascending=[True, False, False],
    ).iloc[0].to_dict()
    put = puts.sort_values(
        ["delta_distance", "volume", "open_interest"],
        ascending=[True, False, False],
    ).iloc[0].to_dict()
    return call, put


def sell_price(row: dict, fill_model: str) -> float:
    return float(row["mark"] if fill_model == "mid" else row["bid"])


def buy_price(row: pd.Series, fill_model: str) -> float:
    return float(row["mark"] if fill_model == "mid" else row["ask"])


def replay_trade(con, glob: str, entry_date: pd.Timestamp, call: dict, put: dict, args):
    credit = sell_price(call, args.fill_model) + sell_price(put, args.fill_model)
    if credit <= 0:
        return None

    expiry = pd.Timestamp(call["expiration"])
    call_id, put_id = str(call["contract_id"]), str(put["contract_id"])

    q = """
        SELECT date, contract_id, bid, ask, mark
        FROM read_parquet(?)
        WHERE contract_id IN (?, ?)
          AND date > ? AND date <= ?
        ORDER BY date
    """
    quotes = con.execute(
        q,
        [glob, call_id, put_id, sql_date(entry_date), sql_date(expiry)],
    ).fetchdf()
    if quotes.empty:
        return None

    pivot = quotes.pivot(index="date", columns="contract_id", values=["bid", "ask", "mark"])
    close_field = "mark" if args.fill_model == "mid" else "ask"

    for date, row in pivot.iterrows():
        if (close_field, call_id) not in row or (close_field, put_id) not in row:
            continue
        call_exit = row[(close_field, call_id)]
        put_exit = row[(close_field, put_id)]
        if pd.isna(call_exit) or pd.isna(put_exit):
            continue

        debit = float(call_exit + put_exit)
        dte = (expiry - pd.Timestamp(date)).days
        reason = None

        if debit <= credit * (1 - args.profit_target):
            reason = "PROFIT_50"
        elif debit >= credit * args.loss_credit_multiple:
            reason = "LOSS_2X_CREDIT"
        elif dte <= args.exit_dte:
            reason = "DTE_21"

        if reason:
            return {
                "entry_date": entry_date,
                "exit_date": pd.Timestamp(date),
                "expiration": expiry,
                "entry_credit": credit,
                "exit_debit": debit,
                "pnl": (credit - debit) * 100,
                "exit_reason": reason,
                "entry_dte": (expiry - entry_date).days,
                "exit_dte": dte,
                "call_strike": call["strike"],
                "put_strike": put["strike"],
                "call_delta": call["delta"],
                "put_delta": put["delta"],
                "call_contract_id": call_id,
                "put_contract_id": put_id,
            }
    return None


def main() -> None:
    args = parse_args()
    glob = str((ROOT / args.options_glob).resolve())
    matches = list(Path(glob).parent.glob(Path(glob).name))
    if not matches:
        raise FileNotFoundError(f"No option parquet files matched: {glob}")

    regime = load_regime(args.candidate)
    con = duckdb.connect()
    trades = []

    for entry_date in regime.index[regime["eligible"]]:
        chosen = choose_contracts(con, glob, entry_date, args)
        if not chosen:
            continue
        trade = replay_trade(con, glob, entry_date, chosen[0], chosen[1], args)
        if trade:
            trade["regime"] = regime.loc[entry_date, "entry_regime"]
            trades.append(trade)

    con.close()

    result = pd.DataFrame(trades)
    out = RESEARCH_DIR / f"options001_replay_{args.candidate.lower()}_{args.fill_model}.csv"
    result.to_csv(out, index=False)

    print("OPTIONS-001 first-pass replay")
    print(f"candidate={args.candidate} fill_model={args.fill_model}")
    print(f"trades={len(result)}")
    if result.empty:
        print("No completed trades. Check dataset path, coverage, and filters.")
        return

    print(f"total_pnl={result['pnl'].sum():.2f}")
    print(f"mean_pnl={result['pnl'].mean():.2f}")
    print(f"win_rate={(result['pnl'] > 0).mean():.3f}")
    print(result["exit_reason"].value_counts().to_string())
    print(result.groupby("regime")["pnl"].agg(["count", "mean", "sum"]).to_string())


if __name__ == "__main__":
    main()
