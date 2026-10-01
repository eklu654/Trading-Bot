"""Capital-equivalent OPTIONS-002 vs ETF-001 holdout comparison.

Descriptive only: no holdout selection or parameter optimization.
Uses the account-feasibility accepted/rejected lifecycle at the canonical
$5,000 starting balance and compares it with a continuously running ETF-001
25%-cash/200-DMA portfolio over the same 2023+ holdout.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
START = pd.Timestamp("2023-01-01")
STARTING_NLV = 5000.0
CASH = 0.25
MA_WINDOW = 200
REENTRY_SESSIONS = 5

def etf001_holdout_curve() -> pd.Series:
    symbols = ("tqqq", "spxl", "soxl")
    prices = {s: pd.read_csv(DATA / f"{s}_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index() for s in symbols}
    close = pd.concat({s: prices[s]["close"] for s in symbols}, axis=1).dropna()
    adjusted = pd.concat({s: prices[s]["adj_close"] for s in symbols}, axis=1).reindex(close.index)
    returns = adjusted.pct_change().fillna(0.0)
    holdings = {}
    for s in symbols:
        ma = close[s].rolling(MA_WINDOW, min_periods=MA_WINDOW).mean()
        active = False
        above = 0
        signal = []
        for date in close.index:
            value = close.loc[date, s]
            mean = ma.loc[date]
            if pd.isna(mean) or value < mean:
                active = False
                above = 0
            elif not active:
                above += 1
                if above >= REENTRY_SESSIONS:
                    active = True
            signal.append(active)
        holdings[s] = pd.Series(signal, index=close.index, dtype=bool).shift(1).fillna(False)
    sleeve = (1.0 - CASH) / len(symbols)
    daily = sum(sleeve * returns[s] * holdings[s].astype(float) for s in symbols)
    value = (1.0 + daily).cumprod()
    holdout = value.loc[value.index >= START].copy()
    if holdout.empty or not np.isfinite(holdout).all():
        raise ValueError("ETF-001 holdout curve is missing or non-finite.")
    return holdout / holdout.iloc[0] * STARTING_NLV

def option_config_results() -> pd.DataFrame:
    rows = []
    for path in sorted(DATA.glob("options002_*_account_5000_risk_0.07.csv")):
        account = pd.read_csv(path, parse_dates=["entry_date"])
        holdout = account.loc[account["entry_date"] >= START].copy()
        accepted = holdout.loc[holdout["accepted"] == True].copy()
        outcome_path = DATA / path.name.replace("_account_5000_risk_0.07.csv", "_candidate_outcomes.csv")
        if not outcome_path.exists():
            continue
        outcomes = pd.read_csv(outcome_path, parse_dates=["exit_date"])
        accepted = accepted.merge(outcomes, on="candidate_id", how="left").sort_values("entry_date")
        accepted = accepted.loc[accepted["pnl"].notna()].copy()
        nlv = STARTING_NLV
        peak = nlv
        max_drawdown = 0.0
        for row in accepted.itertuples(index=False):
            nlv += float(row.pnl)
            peak = max(peak, nlv)
            max_drawdown = min(max_drawdown, nlv / peak - 1.0)
        rows.append({
            "configuration": path.name.replace("_account_5000_risk_0.07.csv", ""),
            "accepted_holdout_trades": len(accepted),
            "rejected_holdout_candidates": len(holdout) - len(accepted),
            "option_net_pnl": nlv - STARTING_NLV,
            "option_ending_nlv": nlv,
            "option_max_drawdown": max_drawdown,
            "max_defined_loss_seen": float(holdout["max_defined_loss"].max()) if len(holdout) else np.nan,
        })
    return pd.DataFrame(rows)

def main() -> None:
    etf = etf001_holdout_curve()
    options = option_config_results()
    if options.empty:
        raise SystemExit("No $5,000 / 7% account-feasibility outputs found.")
    etf_ending = float(etf.iloc[-1])
    options["etf_ending_nlv_same_holdout"] = etf_ending
    options["etf_holdout_return"] = etf_ending / STARTING_NLV - 1.0
    options["option_holdout_return"] = options["option_ending_nlv"] / STARTING_NLV - 1.0
    options["option_vs_etf_ending_nlv_difference"] = options["option_ending_nlv"] - etf_ending
    output = DATA / "options002_etf001_capital_equivalent_holdout_summary.csv"
    options.to_csv(output, index=False)
    print(options.to_string(index=False))
    print()
    print(f"ETF-001 2023+ holdout: $\{STARTING_NLV:,.0f} -> $\{etf_ending:,.2f} (\{etf_ending / STARTING_NLV - 1:.2%}).")
    print("OPTIONS-002 rows are independent configuration backtests, not a combined portfolio and not a deployment recommendation.")

if __name__ == "__main__":
    main()
