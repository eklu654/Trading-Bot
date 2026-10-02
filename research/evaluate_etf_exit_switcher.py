"""Evaluate a conservative ETF-full-exit -> capital-feasible defined-risk-options switcher.

This is research only. Option trades must come from the authoritative $5,000
account-feasibility ledger and must already be marked accepted=True. The
selector only permits an accepted OPTIONS-002 trade when the ETF basket is
fully out of its sleeves on the option entry date.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--etf-backtest", default="data/research/etf001_dma_25cash_backtest.csv")
    p.add_argument("--options-trades", required=True)
    p.add_argument("--capital", type=float, default=5000.0)
    p.add_argument("--output", required=True)
    return p.parse_args()


def main() -> None:
    a = args()
    etf = pd.read_csv(ROOT / a.etf_backtest, parse_dates=["Date"]).set_index("Date").sort_index()
    required = {"portfolio_return", "active_sleeves"}
    missing = required - set(etf.columns)
    if missing:
        raise ValueError(f"ETF backtest missing columns: {sorted(missing)}")

    trades = pd.read_csv(ROOT / a.options_trades, parse_dates=["entry_date", "exit_date"])
    required_trades = {"accepted", "entry_date", "exit_date", "net_pnl", "max_defined_loss"}
    missing = required_trades - set(trades.columns)
    if missing:
        raise ValueError(f"Account-feasibility ledger missing columns: {sorted(missing)}")

    trades = trades.loc[trades["accepted"].eq(True)].copy()
    trades = trades.loc[trades["exit_date"].notna()].copy()

    exit_days = etf["active_sleeves"].eq(0)
    eligible = trades[
        trades["entry_date"].isin(etf.index)
        & trades["entry_date"].map(exit_days).fillna(False)
    ].copy()

    accepted = []
    active_until = pd.Timestamp.min
    for _, row in eligible.sort_values(["entry_date", "exit_date"]).iterrows():
        entry = pd.Timestamp(row["entry_date"])
        exit_ = pd.Timestamp(row["exit_date"])
        if entry <= active_until or exit_ < entry:
            continue
        accepted.append(row)
        active_until = exit_

    accepted_df = pd.DataFrame(accepted)
    daily = etf[["portfolio_return", "active_sleeves"]].copy()
    daily["selector_pnl"] = 0.0
    daily["selector_source"] = "CASH_OR_ETF"
    daily["selector_return"] = daily["portfolio_return"].where(
        daily["active_sleeves"] > 0, 0.0
    )

    if not accepted_df.empty:
        for _, row in accepted_df.iterrows():
            exit_date = pd.Timestamp(row["exit_date"])
            if exit_date in daily.index:
                daily.loc[exit_date, "selector_pnl"] += float(row["net_pnl"])
                daily.loc[exit_date, "selector_source"] = "OPTIONS_REALIZED"
        daily["selector_return"] += daily["selector_pnl"] / a.capital

    daily["selector_equity"] = a.capital * (1.0 + daily["selector_return"]).cumprod()
    daily["etf_equity"] = a.capital * (1.0 + daily["portfolio_return"]).cumprod()

    daily.to_csv(ROOT / a.output)
    summary = pd.DataFrame([{
        "capital": a.capital,
        "accepted_option_trades": len(accepted_df),
        "option_net_pnl": float(accepted_df["net_pnl"].sum()) if not accepted_df.empty else 0.0,
        "selector_ending_equity": float(daily["selector_equity"].iloc[-1]),
        "etf_ending_equity": float(daily["etf_equity"].iloc[-1]),
        "selector_total_return": float(daily["selector_equity"].iloc[-1] / a.capital - 1.0),
        "etf_total_return": float(daily["etf_equity"].iloc[-1] / a.capital - 1.0),
        "incremental_vs_etf": float(
            daily["selector_equity"].iloc[-1] - daily["etf_equity"].iloc[-1]
        ),
    }])
    summary.to_csv(
        ROOT / (Path(a.output).with_name(Path(a.output).stem + "_summary.csv")),
        index=False,
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
