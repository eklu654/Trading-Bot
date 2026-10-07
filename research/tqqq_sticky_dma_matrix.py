"""Causal sticky-DMA survivability matrix for synthetic and actual TQQQ.

Signal convention:
    close[t] -> next open[t+1]

Unlike the earlier daily-crossing partial-DMA test, this keeps a reduced
exposure once defense is entered and does not re-enter until the close is back
above the same DMA. This isolates whether whipsaw/re-entry is the reason the
full-history partial-DMA family failed.

Predeclared grid:
    DMA: 100, 150, 200
    below-DMA exposure: 0%, 25%, 50%, 75%
    immediate re-entry on the first close back above DMA

No threshold optimization, costs, or macro inputs.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_equity

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
INITIAL = 5000.0
START = "1999-03-10"
END = "2026-10-06"
DMAS = (100, 150, 200)
BELOW = (0.0, 0.25, 0.50, 0.75)


def qqq_frame():
    x = yf.download("QQQ", start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    x = x.rename(columns={"Open": "open", "Close": "close",
                          "Adj Close": "adj_close"}).sort_index().dropna()
    x["adj_open"] = x["open"] * x["adj_close"] / x["close"]
    x["overnight_3x"] = ((1 + 3 * (x["adj_open"] / x["adj_close"].shift(1) - 1)).clip(lower=0) - 1).fillna(0)
    x["intraday_3x"] = ((1 + 3 * (x["adj_close"] / x["adj_open"] - 1)).clip(lower=0) - 1).fillna(0)
    return x


def actual_tqqq():
    x = yf.download("TQQQ", start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    x = x.rename(columns={"Open": "open", "Close": "close",
                          "Adj Close": "adj_close"}).sort_index().dropna()
    x["adj_open"] = x["open"] * x["adj_close"] / x["close"]
    x["overnight_3x"] = (x["adj_open"] / x["adj_close"].shift(1) - 1).fillna(0)
    x["intraday_3x"] = (x["adj_close"] / x["adj_open"] - 1).fillna(0)
    return x


def sticky_weights(close, dma):
    ma = close.rolling(dma).mean()
    w = np.ones(len(close), dtype=float)
    defensive = False
    for i, (px, m) in enumerate(zip(close.to_numpy(), ma.to_numpy())):
        if not np.isfinite(m):
            w[i] = 0.0
            continue
        if not defensive and px < m:
            defensive = True
        elif defensive and px >= m:
            defensive = False
        w[i] = 0.0 if not defensive else np.nan
    return w


def fill_defense(raw, exposure):
    out = np.asarray(raw, dtype=float)
    return np.where(np.isnan(out), exposure, out)


def evaluate(frame, source, dma, exposure):
    raw = sticky_weights(frame["adj_close"], dma)
    sig = fill_defense(raw, exposure)
    eq = next_open_equity(sig, frame["overnight_3x"], frame["intraday_3x"], INITIAL)
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1
    years = (frame.index[-1] - frame.index[0]).days / 365.25
    return {
        "source": source,
        "dma": dma,
        "below_exposure": exposure,
        "final_balance": float(eq[-1]),
        "cagr": float((eq[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "minimum_equity": float(eq.min()),
        "avg_exposure": float(sig.mean()),
        "defensive_days": int((sig < 1).sum()),
    }


def main():
    rows = []
    for source, frame in [("synthetic_qqq_3x", qqq_frame()),
                          ("actual_tqqq", actual_tqqq())]:
        for dma in DMAS:
            for exposure in BELOW:
                rows.append(evaluate(frame, source, dma, exposure))

    out = pd.DataFrame(rows).sort_values(["source", "final_balance"], ascending=[True, False])
    DATA.mkdir(parents=True, exist_ok=True)
    out.to_csv(DATA / "tqqq_sticky_dma_matrix.csv", index=False)

    print(out.to_string(index=False))
    print("\nBEST BY SOURCE")
    print(out.sort_values("final_balance", ascending=False).groupby("source", as_index=False).head(8).to_string(index=False))


if __name__ == "__main__":
    main()
