"""Conditional OPTIONS-002 analysis during ETF-001 full-exit periods.

This is a diagnostic, not a strategy selector. It asks whether the existing
capital-feasible $5,000 OPTIONS-002 candidates generated useful incremental
P/L specifically while the canonical ETF-001 25%-cash/200-DMA portfolio had
zero active ETF sleeves.

The option daily contribution is reconstructed from the existing candidate
marks. It is reported separately from full-trade P/L so overlap with ETF exit
episodes cannot be mistaken for a standalone account equity curve.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
START = pd.Timestamp("2023-01-01")
STARTING_NLV = 5000.0
CASH = 0.25
SYMBOLS = ("tqqq", "spxl", "soxl")
MA_WINDOW = 200
REENTRY_SESSIONS = 5
RISK_PCT = 0.07


def etf_state() -> pd.DataFrame:
    prices = {
        s: pd.read_csv(DATA / f"{s}_daily.csv", parse_dates=["Date"])
        .set_index("Date").sort_index()
        for s in SYMBOLS
    }
    close = pd.concat({s: prices[s]["close"] for s in SYMBOLS}, axis=1).dropna()
    adjusted = pd.concat(
        {s: prices[s]["adj_close"] for s in SYMBOLS}, axis=1
    ).reindex(close.index)
    returns = adjusted.pct_change().fillna(0.0)

    signals = {}
    for s in SYMBOLS:
        ma = close[s].rolling(MA_WINDOW, min_periods=MA_WINDOW).mean()
        active = False
        above = 0
        values = []
        for date in close.index:
            price, mean = close.loc[date, s], ma.loc[date]
            if pd.isna(mean) or price < mean:
                active, above = False, 0
            elif not active:
                above += 1
                if above >= REENTRY_SESSIONS:
                    active = True
            values.append(active)
        signals[s] = pd.Series(values, index=close.index, dtype=bool)

    holdings = pd.DataFrame(
        {s: signals[s].shift(1).fillna(False) for s in SYMBOLS},
        index=close.index,
    )
    state = pd.DataFrame(index=close.index)
    state["active_sleeves"] = holdings.sum(axis=1).astype(int)
    state["invested_weight"] = state["active_sleeves"] * ((1.0 - CASH) / len(SYMBOLS))
    state["full_exit"] = state["active_sleeves"].eq(0)
    state["portfolio_return"] = sum(
        ((1.0 - CASH) / len(SYMBOLS))
        * returns[s] * holdings[s].astype(float)
        for s in SYMBOLS
    )
    state["portfolio_value"] = (1.0 + state["portfolio_return"]).cumprod()
    return state.loc[state.index >= START].copy()


def episode_table(state: pd.DataFrame) -> pd.DataFrame:
    flags = state["full_exit"]
    group = flags.ne(flags.shift()).cumsum()
    rows = []
    for _, g in state[flags].groupby(group[flags]):
        rows.append({
            "episode_id": len(rows) + 1,
            "start": g.index.min(),
            "end": g.index.max(),
            "days": len(g),
        })
    return pd.DataFrame(rows)


def accepted_trade_frames(config_stem: str):
    account_path = DATA / f"{config_stem}_account_5000_risk_{RISK_PCT:.2f}.csv"
    outcomes_path = DATA / f"{config_stem}_candidate_outcomes.csv"
    marks_path = DATA / f"{config_stem}_candidate_marks.csv"
    if not account_path.exists() or not outcomes_path.exists() or not marks_path.exists():
        return None
    account = pd.read_csv(account_path, parse_dates=["entry_date"])
    outcomes = pd.read_csv(outcomes_path, parse_dates=["exit_date"])
    marks = pd.read_csv(marks_path, parse_dates=["date"])
    accepted = account.loc[account["accepted"] == True].copy()
    accepted = accepted.merge(
        outcomes[["candidate_id", "exit_date", "pnl", "exit_debit"]],
        on="candidate_id", how="left", validate="one_to_one",
    )
    accepted = accepted.loc[accepted["exit_date"].notna()].copy()
    return accepted, marks


def option_daily_contribution(trade: pd.Series, marks: pd.DataFrame) -> pd.DataFrame:
    cid = trade["candidate_id"]
    m = marks.loc[marks["candidate_id"] == cid].sort_values("date").copy()
    if m.empty:
        return pd.DataFrame(columns=["date", "daily_option_pnl"])
    credit = float(trade["entry_credit"]) * 100.0
    entry_fee = float(trade.get("entry_fee", 0.0))
    exit_fee = float(trade.get("exit_fee", 0.0))
    prev_equity = 0.0
    rows = []
    exit_date = pd.Timestamp(trade["exit_date"])
    for _, r in m.iterrows():
        date = pd.Timestamp(r["date"])
        if date < START or date > exit_date:
            continue
        equity = credit - float(r["mark_debit"]) * 100.0 - float(trade.get("entry_fee", 0.0))
        daily = equity - prev_equity
        if date == exit_date:
            # Replace the marked value with realized net trade P/L so exit fees
            # are reflected exactly once on the lifecycle's final day.
            realized = float(trade["pnl"]) * 1.0
            daily = realized - prev_equity
        rows.append({
            "candidate_id": cid,
            "date": date,
            "daily_option_pnl": daily,
        })
        prev_equity = equity if date != exit_date else float(trade["net_pnl"])
    return pd.DataFrame(rows)


def config_analysis(stem: str, state: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    loaded = accepted_trade_frames(stem)
    if loaded is None:
        return {}, pd.DataFrame()
    accepted, marks = loaded
    parts = []
    for _, trade in accepted.iterrows():
        part = option_daily_contribution(trade, marks)
        if not part.empty:
            parts.append(part)
    daily = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["candidate_id", "date", "daily_option_pnl"]
    )
    daily = daily.merge(
        state[["active_sleeves", "full_exit", "portfolio_return"]],
        left_on="date", right_index=True, how="inner",
    )
    exit_daily = daily.loc[daily["full_exit"]].copy()
    episodes = episode_table(state)
    if exit_daily.empty:
        summary = {
            "configuration": stem,
            "exit_days": int(state["full_exit"].sum()),
            "exit_episodes": len(episodes),
            "option_active_exit_days": 0,
            "option_exit_day_pnl": 0.0,
            "positive_option_exit_days": np.nan,
            "mean_option_exit_day_pnl": np.nan,
            "median_option_exit_day_pnl": np.nan,
            "worst_option_exit_day_pnl": np.nan,
            "best_option_exit_day_pnl": np.nan,
            "exit_day_pnl_std": np.nan,
            "full_trade_count_holdout": len(accepted),
            "full_trade_pnl_holdout": float(accepted["pnl"].sum()),
            "full_trade_win_rate_holdout": float((accepted["pnl"] > 0).mean()) if len(accepted) else np.nan,
        }
        return summary, daily

    by_date = exit_daily.groupby("date", as_index=False)["daily_option_pnl"].sum()
    summary = {
        "configuration": stem,
        "exit_days": int(state["full_exit"].sum()),
        "exit_episodes": len(episodes),
        "option_active_exit_days": len(by_date),
        "option_exit_day_pnl": float(by_date["daily_option_pnl"].sum()),
        "positive_option_exit_days": float((by_date["daily_option_pnl"] > 0).mean()),
        "mean_option_exit_day_pnl": float(by_date["daily_option_pnl"].mean()),
        "median_option_exit_day_pnl": float(by_date["daily_option_pnl"].median()),
        "worst_option_exit_day_pnl": float(by_date["daily_option_pnl"].min()),
        "best_option_exit_day_pnl": float(by_date["daily_option_pnl"].max()),
        "exit_day_pnl_std": float(by_date["daily_option_pnl"].std(ddof=1)) if len(by_date) > 1 else np.nan,
        "full_trade_count_holdout": len(accepted),
        "full_trade_pnl_holdout": float(accepted["pnl"].sum()),
        "full_trade_win_rate_holdout": float((accepted["pnl"] > 0).mean()) if len(accepted) else np.nan,
    }
    return summary, daily


def main() -> None:
    state = etf_state()
    stems = sorted(
        p.name.replace("_account_5000_risk_0.07.csv", "")
        for p in DATA.glob("options002_*_account_5000_risk_0.07.csv")
    )
    if not stems:
        raise SystemExit("No canonical $5,000 OPTIONS-002 account ledgers found.")

    summaries, details = [], []
    for stem in stems:
        summary, daily = config_analysis(stem, state)
        if summary:
            summaries.append(summary)
        if not daily.empty:
            details.append(daily.assign(configuration=stem))

    summary_df = pd.DataFrame(summaries)
    detail_df = pd.concat(details, ignore_index=True) if details else pd.DataFrame()
    episodes = episode_table(state)

    summary_df.to_csv(DATA / "etf_exit_options_conditional_summary.csv", index=False)
    detail_df.to_csv(DATA / "etf_exit_options_conditional_daily.csv", index=False)
    episodes.to_csv(DATA / "etf001_full_exit_episodes_holdout.csv", index=False)

    print("=== ETF-EXIT CONDITIONAL OPTIONS ANALYSIS ===")
    print(summary_df.to_string(index=False))
    print()
    print("ETF-001 full-exit episodes:")
    print(episodes.to_string(index=False))
    print()
    print("Cash reference: $0 daily P/L during ETF full-exit periods.")
    print("OPTIONS rows are overlap diagnostics, not a switcher backtest or deployment recommendation.")


if __name__ == "__main__":
    main()
