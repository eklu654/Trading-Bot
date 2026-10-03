"""ETF-004: inverse-ETF fallback versus cash for the existing three sleeves.

For each of TQQQ/SPXL/SOXL (25% sleeve):
- Bull sleeve is held while its underlying is >= 200-DMA.
- When below 200-DMA, the sleeve either becomes cash or switches to the
  corresponding inverse ETF (SQQQ/SPXS/SOXS).
- Re-entry to the bull side requires 5 consecutive sessions >= 200-DMA.
- No same-underlying bull and bear ETF can coexist.

This isolates the question "cash or inverse ETF when the 200-DMA triggers?"
without changing the portfolio universe or adding cross-underlying rotation.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
PAIRS = {"QQQ": ("TQQQ", "SQQQ"), "SPY": ("SPXL", "SPXS"), "SOXX": ("SOXL", "SOXS")}
SLEEVE = 0.25
MA = 200
REENTRY = 5
SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}

def load(symbol):
    return pd.read_csv(DATA / f"{symbol.lower()}_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()

def metrics(frame):
    r = frame["return"].dropna()
    if r.empty:
        return {"observations": 0}
    eq = (1 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365.25)
    total = eq.iloc[-1] - 1
    ann = (1 + total) ** (1 / years) - 1
    vol = r.std(ddof=1) * np.sqrt(252)
    dd = (eq / eq.cummax() - 1).min()
    neg = r[r < 0].std(ddof=1)
    sharpe = r.mean() / r.std(ddof=1) * np.sqrt(252) if r.std(ddof=1) > 0 else np.nan
    sortino = r.mean() / neg * np.sqrt(252) if pd.notna(neg) and neg > 0 else np.nan
    return {
        "observations": len(r), "total_return": total, "annualized_return": ann,
        "max_drawdown": dd, "annualized_volatility": vol,
        "sharpe": sharpe, "sortino": sortino, "ending_value_5000": 5000 * eq.iloc[-1],
    }

def signal_states(close):
    ma = close.rolling(MA, min_periods=MA).mean()
    above = (close >= ma).fillna(False)
    state = pd.Series(False, index=close.index)
    current = False
    below_streak = 0
    for i, date in enumerate(close.index):
        if above.iloc[i]:
            current = True
            below_streak = 0
        else:
            below_streak += 1
            if below_streak >= REENTRY:
                current = False
        state.iloc[i] = current
    return state

def main():
    underlying = {u: load(u)["close"] for u in PAIRS}
    common = pd.concat(underlying, axis=1).dropna()
    etf = {t: load(t) for pair in PAIRS.values() for t in pair}
    states = {u: signal_states(common[u]) for u in PAIRS}

    rows = []
    for fallback in ("CASH", "INVERSE"):
        daily = []
        for i, date in enumerate(common.index):
            if i == 0:
                daily.append(0.0)
                continue
            prev = common.index[i - 1]
            ret = 0.0
            for u, (bull, bear) in PAIRS.items():
                ticker = bull if bool(states[u].loc[prev]) else (bear if fallback == "INVERSE" else None)
                if ticker is not None:
                    p = etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
                    if prev in p.index and date in p.index:
                        ret += SLEEVE * float(p.loc[date] / p.loc[prev] - 1)
            daily.append(ret)
        frame = pd.DataFrame({"return": daily}, index=common.index)
        for split, (start, end) in SPLITS.items():
            rows.append({"strategy": fallback, "split": split, **metrics(frame.loc[start:end])})
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "etf004_inverse_vs_cash_summary.csv", index=False)
    print("=== ETF-004 INVERSE FALLBACK VS CASH ===")
    print(out.to_string(index=False))

if __name__ == "__main__":
    main()
