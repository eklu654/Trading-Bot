"""Evaluate fixed, predeclared risk overlays on the E4 Ridge policy.

These overlays are not tuned to the AI result. They reuse the project's
existing 200-DMA and VIX-percentile concepts to test whether a hard controller
can reduce catastrophic AI drawdowns without changing the learned selector.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research"
sys.path.insert(0, str(ROOT))

from research.backtest_ai_action_selector import ACTIONS, load

VIX_HIGH_PERCENTILE = 0.80
WINDOWS = {
    "covid_crash": ("2020-02-19", "2020-04-30"),
    "2022_rate_hike_bear": ("2022-01-03", "2022-12-30"),
    "2023_2024_recovery": ("2023-01-03", "2024-12-31"),
}


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    total = (1 + daily).prod() - 1
    vol = daily.std(ddof=1) * np.sqrt(252)
    dd = (1 + daily).cumprod()
    dd = dd / dd.cummax() - 1
    return {
        "strategy": label,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "cagr": (1 + total) ** (1 / years) - 1,
        "volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252) if daily.std(ddof=1) else np.nan,
        "max_drawdown": dd.min(),
        "worst_day": daily.min(),
        "cash_pct": float((frame["action"] == "cash").mean()),
    }


def build_policy(ai: pd.DataFrame, features: pd.DataFrame, mode: str) -> pd.DataFrame:
    spy = load("SPY")["adj_close"]
    ma200 = spy.rolling(200).mean()
    vix_pct = features["vix_pct"]

    prices = {action: (load(symbol)["adj_close"] if symbol else None)
              for action, symbol in ACTIONS.items()}
    spy = prices["SPY_1x"]
    records = []
    equity = 1.0
    for _, row in ai.iterrows():
        decision_date = pd.Timestamp(row["decision_date"])
        next_date = pd.Timestamp(row.name)
        action = str(row["action"])
        risk_cash = False

        spy_price = spy.reindex([decision_date]).iloc[0]
        trend = ma200.reindex([decision_date]).iloc[0]
        vix = vix_pct.reindex([decision_date]).iloc[0]
        if mode in ("dma200", "both") and pd.notna(spy_price) and pd.notna(trend):
            risk_cash = risk_cash or bool(spy_price < trend)
        if mode in ("vix80", "both") and pd.notna(vix):
            risk_cash = risk_cash or bool(vix >= VIX_HIGH_PERCENTILE)

        effective = "cash" if risk_cash else action
        symbol = ACTIONS[effective]
        if symbol is None:
            daily_return = 0.0
        else:
            price_series = prices[effective]
            prev = price_series.reindex([decision_date]).iloc[0]
            cur = price_series.reindex([next_date]).iloc[0]
            daily_return = float(cur / prev - 1) if pd.notna(prev) and pd.notna(cur) and prev != 0 else 0.0

        equity *= 1 + daily_return
        records.append({
            "Date": next_date,
            "decision_date": decision_date,
            "portfolio_return": daily_return,
            "portfolio_value": equity,
            "action": effective,
            "raw_action": action,
            "risk_cash": risk_cash,
        })

    out = pd.DataFrame(records).set_index("Date")
    return out


def main() -> None:
    ai = pd.read_csv(DATA_DIR / "e4_ai_backtest.csv", parse_dates=["Date"]).set_index("Date")
    features = pd.read_csv(DATA_DIR / "e4_ai_features.csv", parse_dates=["Date"]).set_index("Date")

    policies = {
        "AI_Ridge_raw": "none",
        "AI_Ridge_200DMA_gate": "dma200",
        "AI_Ridge_VIX80_gate": "vix80",
        "AI_Ridge_both_gates": "both",
    }

    rows = []
    stress_rows = []
    for label, mode in policies.items():
        frame = ai if mode == "none" else build_policy(ai, features, mode)
        if mode == "none":
            frame = frame.copy()
            frame["action"] = frame["action"].astype(str)
        rows.append(summarize(frame, label))
        for window, (start, end) in WINDOWS.items():
            segment = frame.loc[start:end]
            if not segment.empty:
                stats = summarize(segment, f"{label}_{window}")
                stats["window"] = window
                stress_rows.append(stats)

    summary = pd.DataFrame(rows)
    stress = pd.DataFrame(stress_rows)
    summary.to_csv(DATA_DIR / "e4_ai_risk_overlay_summary.csv", index=False)
    stress.to_csv(DATA_DIR / "e4_ai_risk_overlay_stress.csv", index=False)

    print(summary.to_string(index=False))
    print("\nStress windows")
    print(stress.to_string(index=False))
