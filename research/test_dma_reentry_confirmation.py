"""Compare immediate 200-DMA re-entry with the fixed five-session confirmation rule.

The five-session rule matches the project's stated intent: after a 200-DMA exit,
an ETF must remain above its 200-DMA for one full trading week before re-entry.
No parameter sweep is performed.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from research.backtest_dynamic_leverage import load

DATA_DIR = ROOT / "data" / "research"
START = pd.Timestamp("2018-01-01")
END = pd.Timestamp("2025-12-31")
MA_WINDOW = 200
CONFIRM_SESSIONS = 5
SYMBOLS = ("TQQQ", "SOXL", "SPXL")


def run(symbol: str, confirm_sessions: int) -> pd.DataFrame:
    price = load(symbol)["adj_close"].copy()
    ma = price.rolling(MA_WINDOW).mean()
    above = price >= ma
    held = pd.Series(False, index=price.index)
    active = False
    streak = 0

    for i, date in enumerate(price.index):
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
    return pd.DataFrame(
        {"portfolio_return": daily.where(held, 0.0), "held": held},
        index=price.index,
    )


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    frame = frame.loc[START:END]
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    equity = (1 + daily).cumprod()
    dd = equity / equity.cummax() - 1
    vol = daily.std(ddof=1) * np.sqrt(252)
    return {
        "strategy": label,
        "cagr": equity.iloc[-1] ** (1 / years) - 1,
        "volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252) if daily.std(ddof=1) else np.nan,
        "max_drawdown": dd.min(),
        "worst_day": daily.min(),
        "days_held": int(frame["held"].sum()),
    }


def main() -> None:
    rows = []
    for symbol in SYMBOLS:
        for sessions, label in ((1, "immediate"), (CONFIRM_SESSIONS, "five_session_confirmation")):
            rows.append(summarize(run(symbol, sessions), f"{symbol}_200DMA_{label}"))

    result = pd.DataFrame(rows)
    result.to_csv(DATA_DIR / "dma_reentry_confirmation_2018_2025.csv", index=False)
    print(result.to_string(index=False))
    print("\nArtifact:", DATA_DIR / "dma_reentry_confirmation_2018_2025.csv")


if __name__ == "__main__":
    main()
