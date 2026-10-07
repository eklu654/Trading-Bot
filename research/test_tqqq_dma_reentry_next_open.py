"""Causal next-open TQQQ DMA x re-entry sensitivity.

Same 56-cell DMA/re-entry matrix as the prior TQQQ grid, but executes state
changes at the next session's open and measures close-to-close returns while
held. Costs are charged on entry/exit turnover.

Purpose: determine whether the apparent leaders from the prior-close grid
survive realistic next-open execution, without assuming the old 5-session
re-entry rule is correct.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = pd.Timestamp("2010-03-11")
END = pd.Timestamp("2099-12-31")
INITIAL = 5000.0
DMAS = (100, 125, 150, 175, 200, 225, 250, 300)
CONFIRM = (0, 1, 3, 5, 10, 15, 20)
COSTS_BPS = (0, 10, 25, 50)


def download_history() -> pd.DataFrame:
    df = yf.download(
        "TQQQ",
        start="2010-01-01",
        end=(pd.Timestamp.utcnow().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
        actions=False,
    )
    if df.empty:
        raise RuntimeError("No TQQQ history returned.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    needed = {"Open", "Close", "Adj Close"}
    missing = needed - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns: {sorted(missing)}")
    out = pd.DataFrame(
        {
            "open": pd.to_numeric(df["Open"], errors="coerce"),
            "close": pd.to_numeric(df["Close"], errors="coerce"),
            "adj_close": pd.to_numeric(df["Adj Close"], errors="coerce"),
        },
        index=pd.to_datetime(df.index).tz_localize(None),
    ).dropna()
    out["adj_open"] = out["open"] * out["adj_close"] / out["close"]
    return out.loc[START:END]


def held_state(price: pd.Series, dma: int, confirmation: int) -> pd.Series:
    ma = price.rolling(dma).mean()
    above = price >= ma
    held = pd.Series(False, index=price.index)
    active = False
    streak = 0
    required = max(1, confirmation)

    for i in range(len(price)):
        if i == 0 or pd.isna(ma.iloc[i - 1]):
            continue
        prior_above = bool(above.iloc[i - 1])
        if active:
            if not prior_above:
                active = False
                streak = 0
        elif prior_above:
            streak += 1
            if streak >= required:
                active = True
        else:
            streak = 0
        held.iloc[i] = active
    return held


def next_open_returns(frame: pd.DataFrame, dma: int, confirmation: int, cost_bps: float) -> pd.DataFrame:
    held = held_state(frame["adj_close"], dma, confirmation)
    prev_held = held.shift(1).fillna(False)
    entry = held & ~prev_held
    exit_ = ~held & prev_held
    stay = held & prev_held

    ret = pd.Series(0.0, index=frame.index)
    ret.loc[entry] = frame.loc[entry, "adj_close"] / frame.loc[entry, "adj_open"] - 1.0
    ret.loc[stay] = frame.loc[stay, "adj_close"] / frame.loc[stay, "adj_close"].shift(1) - 1.0
    ret.loc[exit_] = frame.loc[exit_, "adj_open"] / frame.loc[exit_, "adj_close"].shift(1) - 1.0

    turnover = entry.astype(float) + exit_.astype(float)
    ret = ret - turnover * (cost_bps / 10000.0)

    equity = INITIAL * (1.0 + ret).cumprod()
    dd = equity / equity.cummax() - 1.0
    return pd.DataFrame({"return": ret, "held": held, "equity": equity, "drawdown": dd})


def summarize(frame: pd.DataFrame, dma: int, confirmation: int, cost_bps: int) -> dict:
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    final = float(frame["equity"].iloc[-1])
    daily = frame["return"].astype(float)
    return {
        "dma": dma,
        "confirmation_sessions": confirmation,
        "cost_bps": cost_bps,
        "start": frame.index[0],
        "end": frame.index[-1],
        "starting_balance": INITIAL,
        "final_balance": final,
        "total_return": final / INITIAL - 1.0,
        "cagr": (final / INITIAL) ** (1 / years) - 1.0,
        "max_drawdown": float(frame["drawdown"].min()),
        "worst_day": float(daily.min()),
        "pct_days_in_tqqq": float(frame["held"].mean()),
        "position_transitions": int(frame["held"].astype(int).diff().abs().fillna(0).sum()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = download_history()
    rows = []
    for cost in COSTS_BPS:
        for dma in DMAS:
            for confirmation in CONFIRM:
                result = next_open_returns(frame, dma, confirmation, cost)
                rows.append(summarize(result, dma, confirmation, cost))

    df = pd.DataFrame(rows)
    df["wealth_rank"] = df.groupby("cost_bps")["final_balance"].rank(ascending=False, method="min").astype(int)
    df["drawdown_rank"] = df.groupby("cost_bps")["max_drawdown"].rank(ascending=False, method="min").astype(int)
    df.to_csv(OUT / "tqqq_dma_reentry_next_open.csv", index=False)

    for cost in COSTS_BPS:
        top = df[df.cost_bps == cost].sort_values("final_balance", ascending=False).head(10)
        print(f"\n=== NEXT-OPEN TOP 10 @ {cost} bps ===")
        print(top[["dma","confirmation_sessions","final_balance","cagr","max_drawdown","position_transitions"]].to_string(index=False))

    best = df[df.cost_bps == 25].sort_values("final_balance", ascending=False).iloc[0]
    print("\n=== 25-BPS LEADER ===")
    print(best.to_string())

    # Explicit apples-to-apples controls for the audit:
    # these use the same actual TQQQ adjusted-close series and date range.
    bh = frame["adj_close"].iloc[-1] / frame["adj_close"].iloc[0] * INITIAL
    zero = df[(df["cost_bps"] == 0) & (df["dma"] == 100) & (df["confirmation_sessions"] == 0)].iloc[0]
    print("\n=== AUDIT CONTROLS ===")
    print(f"TQQQ adjusted-close buy-and-hold control: {bh:.6f}")
    print(f"TQQQ-signal 100-DMA immediate next-open: {zero['final_balance']:.6f}")
    print("Signal source: ACTUAL TQQQ adjusted close; execution: next session open.")


if __name__ == "__main__":
    main()
