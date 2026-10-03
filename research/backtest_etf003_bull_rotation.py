"""ETF-003 bull-only rotation and Dow-pivot research.

Tests whether adding/replacing the Dow 3x bull ETF improves the existing
75%-invested / 25%-cash leveraged ETF framework without using inverse ETFs.

Variants:
- BASE_3: TQQQ + SPXL + SOXL, equal weights, each only while its underlying
  is above its 200-DMA; otherwise that sleeve is cash.
- DOW_SWAP_3: UDOW + SPXL + SOXL under the same rule.
- TOP1_4/TOP2_4/TOP3_4: rank eligible bull ETFs TQQQ, SPXL, SOXL, UDOW by
  60-session underlying momentum and invest the 75% budget equally in the
  top N.
- TOP1_5/TOP2_5/TOP3_5: same with TNA/IWM added.

Signals at t are applied to returns beginning at t+1. No inverse ETF is used.
Chronological train/validation/holdout splits match ETF-001/002.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"

SPLITS = {
    "train": ("2010-03-01", "2019-12-31"),
    "validation": ("2020-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2099-12-31"),
}
CASH = 0.25
UNIVERSES = {
    "BASE_3": {"QQQ": "TQQQ", "SPY": "SPXL", "SOXX": "SOXL"},
    "DOW_SWAP_3": {"DIA": "UDOW", "SPY": "SPXL", "SOXX": "SOXL"},
    "TOP_4": {"QQQ": "TQQQ", "SPY": "SPXL", "SOXX": "SOXL", "DIA": "UDOW"},
    "TOP_5": {"QQQ": "TQQQ", "SPY": "SPXL", "SOXX": "SOXL", "DIA": "UDOW", "IWM": "TNA"},
}
TOP_N = (1, 2, 3)
LOOKBACK = 60
MA = 200


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
        "observations": len(r),
        "total_return": total,
        "annualized_return": ann,
        "max_drawdown": dd,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "ending_value_5000": 5000 * eq.iloc[-1],
    }


def run_universe(name, pairs):
    symbols = list(pairs)
    underlying = pd.concat({u: load(u)["close"] for u in symbols}, axis=1).dropna()
    etf = {ticker: load(ticker) for ticker in pairs.values()}
    signals = {}
    for u in symbols:
        c = underlying[u]
        signals[u] = pd.DataFrame(
            {
                "eligible": c >= c.rolling(MA, min_periods=MA).mean(),
                "score": c.pct_change(LOOKBACK),
            },
            index=underlying.index,
        )

    frames = {}
    if name in {"BASE_3", "DOW_SWAP_3"}:
        daily = []
        for i, date in enumerate(underlying.index):
            if i == 0:
                daily.append(0.0)
                continue
            prev = underlying.index[i - 1]
            ret = 0.0
            for u, ticker in pairs.items():
                sig = signals[u].loc[prev]
                if bool(sig["eligible"]):
                    p = etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
                    if prev in p.index and date in p.index:
                        ret += (1 - CASH) / len(pairs) * float(p.loc[date] / p.loc[prev] - 1)
            daily.append(ret)
        frames["fixed"] = pd.DataFrame({"return": daily}, index=underlying.index)
    else:
        for top_n in TOP_N:
            daily = []
            for i, date in enumerate(underlying.index):
                if i == 0:
                    daily.append(0.0)
                    continue
                prev = underlying.index[i - 1]
                candidates = []
                for u, ticker in pairs.items():
                    sig = signals[u].loc[prev]
                    if bool(sig["eligible"]) and pd.notna(sig["score"]):
                        p = etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
                        if prev in p.index and date in p.index:
                            candidates.append((float(sig["score"]), u, ticker))
                candidates.sort(reverse=True)
                chosen = candidates[:top_n]
                ret = 0.0
                weight = (1 - CASH) / top_n
                for _, _, ticker in chosen:
                    p = etf[ticker]["adj_close"] if "adj_close" in etf[ticker] else etf[ticker]["close"]
                    ret += weight * float(p.loc[date] / p.loc[prev] - 1)
                daily.append(ret)
            frames[f"top{top_n}"] = pd.DataFrame({"return": daily}, index=underlying.index)

    rows = []
    for variant, frame in frames.items():
        for split, (start, end) in SPLITS.items():
            rows.append({"strategy": name, "variant": variant, "split": split, **metrics(frame.loc[start:end])})
    return rows


def main():
    rows = []
    for name, pairs in UNIVERSES.items():
        rows.extend(run_universe(name, pairs))
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "etf003_bull_rotation_summary.csv", index=False)
    print("=== ETF-003 BULL-ONLY / DOW PIVOT ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
