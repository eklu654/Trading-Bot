"""Evaluate a conservative ETF-full-exit -> defined-risk-options switcher.

This is a research comparison, not a deployment rule. The selector only permits
an OPTIONS-002 trade when the ETF basket is fully out of its sleeves on the
option entry date. Option P/L is realized on its recorded exit date. Days with
neither an ETF position nor an eligible option trade remain in cash.

The output reports the switcher's dollar/equity path and compares it with the
ETF-only backtest over the same dates.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--etf-backtest", default="data/research/etf001_dma_25cash_backtest.csv")
    p.add_argument("--options-trades", required=True)
    p.add_argument("--capital", type=float, default=5000.0)
    p.add_argument("--max-risk-pct", type=float, default=0.07)
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
    if trades.empty:
        trades = pd.DataFrame(columns=["entry_date", "exit_date", "pnl", "max_defined_loss"])

    # Full ETF exit means all three sleeves are inactive. This is the exact
    # state used by the existing ETF-001 execution model.
    exit_days = etf["active_sleeves"].eq(0)

    eligible = trades[
        trades["entry_date"].isin(etf.index)
        & trades["entry_date"].map(exit_days).fillna(False)
    ].copy()

    if "max_defined_loss" in eligible:
        eligible["risk_ok"] = eligible["max_defined_loss"] <= a.capital * a.max_risk_pct
        eligible = eligible[eligible["risk_ok"]].copy()

    # Enforce one option position at a time and prevent trades from overlapping.
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

    # ETF return is used only while at least one ETF sleeve is active.
    daily["selector_return"] = daily["portfolio_return"].where(
        daily["active_sleeves"] > 0, 0.0
    )

    # A qualifying option trade replaces cash during an ETF full-exit episode.
    # P/L is recognized on the actual replay exit date; no synthetic intraday
    # mark is introduced.
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
        "max_risk_pct": a.max_risk_pct,
        "accepted_option_trades": len(accepted_df),
        "option_pnl": float(accepted_df["net_pnl"].sum()) if not accepted_df.empty else 0.0,
        "selector_ending_equity": float(daily["selector_equity"].iloc[-1]),
        "etf_ending_equity": float(daily["etf_equity"].iloc[-1]),
        "selector_total_return": float(daily["selector_equity"].iloc[-1] / a.capital - 1.0),
        "etf_total_return": float(daily["etf_equity"].iloc[-1] / a.capital - 1.0),
        "incremental_vs_etf": float(
            daily["selector_equity"].iloc[-1] - daily["etf_equity"].iloc[-1]
        ),
    }])
    summary.to_csv(ROOT / (Path(a.output).with_name(Path(a.output).stem + "_summary.csv")), index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
