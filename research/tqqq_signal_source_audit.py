"""Explicit audit of QQQ-vs-TQQQ 100-DMA signal source and next-open timing.

The canonical research rule is:
    signal = QQQ close vs QQQ 100-DMA
    execution = actual TQQQ, beginning next session

This test exists to prevent the two common confusions that caused the recent
reconciliation problems:
1. accidentally using TQQQ instead of QQQ for the signal;
2. applying today's close-derived signal to today's intraday return.

It prints both QQQ-signal and TQQQ-signal controls, plus buy-and-hold.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-05"
DMA = 100


def download(symbol: str) -> pd.DataFrame:
    x = yf.download(
        symbol,
        start=START,
        end=END,
        auto_adjust=False,
        progress=False,
        actions=False,
    )
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return (
        x.rename(
            columns={"Open": "open", "Close": "close", "Adj Close": "adj_close"}
        )[["open", "close", "adj_close"]]
        .sort_index()
        .dropna()
    )


def signal(price: pd.Series) -> pd.Series:
    dma = price.rolling(DMA).mean()
    out = (price >= dma).astype(float)
    out.iloc[: DMA - 1] = 0.0
    return out


def actual_tqqq_returns(tqqq: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    adj_open = tqqq["open"] * tqqq["adj_close"] / tqqq["close"]
    overnight = (adj_open / tqqq["adj_close"].shift(1) - 1.0).fillna(0.0)
    intraday = (tqqq["adj_close"] / adj_open - 1.0).fillna(0.0)
    return overnight, intraday


def equity(sig: pd.Series, overnight: pd.Series, intraday: pd.Series) -> float:
    w = sig.to_numpy(float)
    exec_w = np.roll(w, 1)
    exec_w[0] = 0.0
    # The prior-close signal controls the entire next session. In particular,
    # today's close-derived signal must NOT receive today's intraday return.
    daily = (1.0 + exec_w * overnight.to_numpy()) * (
        1.0 + exec_w * intraday.to_numpy()
    ) - 1.0
    return float(INITIAL * np.cumprod(1.0 + daily)[-1])


def main() -> None:
    qqq = download("QQQ")
    tqqq = download("TQQQ")
    idx = qqq.index.intersection(tqqq.index)
    qqq = qqq.reindex(idx)
    tqqq = tqqq.reindex(idx)

    qqq_signal = signal(qqq["adj_close"])
    tqqq_signal = signal(tqqq["adj_close"])
    overnight, intraday = actual_tqqq_returns(tqqq)

    results = pd.DataFrame(
        [
            {
                "control": "actual_tqqq_buy_hold",
                "signal_source": "none",
                "final_balance": equity(
                    pd.Series(1.0, index=idx), overnight, intraday
                ),
            },
            {
                "control": "actual_tqqq_100dma_qqq_signal",
                "signal_source": "QQQ adjusted close",
                "final_balance": equity(qqq_signal, overnight, intraday),
            },
            {
                "control": "actual_tqqq_100dma_tqqq_signal",
                "signal_source": "TQQQ adjusted close",
                "final_balance": equity(tqqq_signal, overnight, intraday),
            },
        ]
    )

    signal_disagreement = int((qqq_signal != tqqq_signal).sum())
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "tqqq_signal_source_audit.csv", index=False)

    print(results.to_string(index=False))
    print(f"\nQQQ-vs-TQQQ signal-day disagreements: {signal_disagreement}")
    print("CANONICAL SIGNAL: QQQ adjusted close vs QQQ 100-DMA")
    print("EXECUTION: actual TQQQ; prior-close signal controls next session")
    print("LOOK-AHEAD CHECK: today's intraday return uses prior day's signal only.")


if __name__ == "__main__":
    main()
