"""Comprehensive TQQQ DMA sensitivity test with terminal account values.

Clean apples-to-apples control matrix:
- $5,000 starting balance.
- First common TQQQ trading session in 2010 through latest available data.
- Adjusted-close daily returns.
- Prior-session signal, next-session execution.
- Exit below the selected DMA.
- Re-enter only after five consecutive prior sessions above the DMA.
- Cash earns 0%.
- Primary DMA windows: 100/125/150/175/200/225/250/300.
- Buy-and-hold is the no-signal control.

A 200-DMA immediate-reentry control is also reported for reconciliation with
earlier 200-DMA research.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_dynamic_leverage import load

DATA_DIR = ROOT / "data" / "research"
SYMBOL = "TQQQ"
START_CAPITAL = 5000.0
DMA_WINDOWS = (100, 125, 150, 175, 200, 225, 250, 300)
CONFIRM_SESSIONS = 5
START = pd.Timestamp("2010-01-01")
END = pd.Timestamp("2099-12-31")


def run_dma(price: pd.Series, dma_window: int, confirm_sessions: int) -> pd.DataFrame:
    ma = price.rolling(dma_window).mean()
    above = price >= ma
    held = pd.Series(False, index=price.index)
    active = False
    streak = 0

    for i in range(len(price)):
        if i == 0 or pd.isna(ma.iloc[i - 1]):
            held.iloc[i] = False
            continue

        prior_above = bool(above.iloc[i - 1])
        if active:
            if not prior_above:
                active = False
                streak = 0
        else:
            if prior_above:
                streak += 1
                if streak >= confirm_sessions:
                    active = True
            else:
                streak = 0

        held.iloc[i] = active

    daily = price.pct_change().fillna(0.0)
    out = pd.DataFrame(
        {"portfolio_return": daily.where(held, 0.0), "held": held, "dma": ma},
        index=price.index,
    )
    out["portfolio_value"] = START_CAPITAL * (1.0 + out["portfolio_return"]).cumprod()
    out["running_max"] = out["portfolio_value"].cummax()
    out["drawdown"] = out["portfolio_value"] / out["running_max"] - 1.0
    out.attrs["confirm_sessions"] = confirm_sessions
    return out


def run_buy_hold(price: pd.Series) -> pd.DataFrame:
    daily = price.pct_change().fillna(0.0)
    out = pd.DataFrame({"portfolio_return": daily, "held": True}, index=price.index)
    out["portfolio_value"] = START_CAPITAL * (1.0 + daily).cumprod()
    out["running_max"] = out["portfolio_value"].cummax()
    out["drawdown"] = out["portfolio_value"] / out["running_max"] - 1.0
    return out


def summarize(frame: pd.DataFrame, strategy: str, dma_window: int | None) -> dict[str, object]:
    segment = frame.loc[START:END].copy()
    daily = segment["portfolio_return"].fillna(0.0)
    years = max((segment.index[-1] - segment.index[0]).days / 365.25, 1 / 365.25)
    equity = segment["portfolio_value"]
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    transitions = segment["held"].astype(int).diff().abs().fillna(0).sum()
    final_balance = float(equity.iloc[-1])
    cagr = (final_balance / START_CAPITAL) ** (1 / years) - 1.0

    return {
        "strategy": strategy,
        "dma": dma_window,
        "confirmation_sessions": int(frame.attrs.get("confirm_sessions", 0)),
        "start": segment.index.min(),
        "end": segment.index.max(),
        "starting_balance": START_CAPITAL,
        "final_balance": final_balance,
        "total_return": final_balance / START_CAPITAL - 1.0,
        "cagr": cagr,
        "max_drawdown": float(segment["drawdown"].min()),
        "annualized_volatility": float(vol),
        "sharpe": float(daily.mean() / daily.std(ddof=1) * np.sqrt(252))
        if daily.std(ddof=1)
        else np.nan,
        "sortino": float(daily.mean() / downside * np.sqrt(252))
        if pd.notna(downside) and downside
        else np.nan,
        "worst_day": float(daily.min()),
        "pct_days_in_tqqq": float(segment["held"].mean()),
        "position_transitions": int(transitions),
    }


def main() -> None:
    price = load(SYMBOL)["adj_close"].dropna().loc[START:END]
    if price.empty:
        raise RuntimeError("No TQQQ price data is available.")

    rows = []
    rows.append(summarize(run_buy_hold(price), "TQQQ buy-and-hold", None))

    for window in DMA_WINDOWS:
        rows.append(
            summarize(
                run_dma(price, window, CONFIRM_SESSIONS),
                f"TQQQ {window}-DMA + 5-session re-entry",
                window,
            )
        )

    rows.append(
        summarize(
            run_dma(price, 200, 1),
            "TQQQ 200-DMA + immediate re-entry",
            200,
        )
    )

    summary = pd.DataFrame(rows)
    summary["final_balance_rank"] = summary["final_balance"].rank(
        ascending=False, method="min"
    ).astype(int)
    summary["max_drawdown_rank"] = summary["max_drawdown"].rank(
        ascending=False, method="min"
    ).astype(int)

    summary.to_csv(DATA_DIR / "tqqq_dma_sensitivity_2010_latest.csv", index=False)
    primary = summary[summary["confirmation_sessions"] == CONFIRM_SESSIONS].copy()
    primary.to_csv(DATA_DIR / "tqqq_dma_sensitivity_primary.csv", index=False)

    print("=== TQQQ DMA SENSITIVITY: 2010-LATEST ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
