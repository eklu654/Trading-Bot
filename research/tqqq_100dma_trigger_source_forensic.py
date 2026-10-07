"""Forensic 100-DMA trigger-source experiment.

Compares two otherwise identical binary TQQQ strategies:
1. QQQ close >= QQQ 100-DMA -> 100% TQQQ; below -> 0%
2. TQQQ close >= TQQQ 100-DMA -> 100% TQQQ; below -> 0%

Signal is observed at today's close and becomes executable at the next session open.
No same-day use of the signal is permitted.

The purpose is diagnostic, not to assume either trigger is good or bad.
Outputs full-period performance plus per-trade/event diagnostics so a good-looking
signal can be reconciled with actual portfolio wealth.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_daily_returns, next_open_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-07"
DMA = 100
TRADING_DAYS = 252


def download(symbol: str) -> pd.DataFrame:
    x = yf.download(symbol, start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={
        "Open": "open", "Close": "close", "Adj Close": "adj_close"
    })[["open", "close", "adj_close"]].sort_index().dropna()


def dma_signal(price: pd.Series) -> pd.Series:
    ma = price.rolling(DMA).mean()
    s = (price >= ma).astype(float)
    s.iloc[:DMA - 1] = 0.0
    return s


def tqqq_returns(tqqq: pd.DataFrame):
    adj_open = tqqq["open"] * tqqq["adj_close"] / tqqq["close"]
    overnight = (adj_open / tqqq["adj_close"].shift(1) - 1).fillna(0.0)
    intraday = (tqqq["adj_close"] / adj_open - 1).fillna(0.0)
    return overnight, intraday


def stats(name, sig, daily, equity, idx):
    wealth = pd.Series(equity, index=idx)
    years = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    cagr = (wealth.iloc[-1] / INITIAL) ** (1 / years) - 1
    peak = wealth.cummax()
    dd = wealth / peak - 1
    exposure = float(sig.shift(1).fillna(0).mean())
    switches = int(sig.diff().abs().fillna(0).sum())
    return {
        "strategy": name,
        "start": str(idx[0].date()),
        "end": str(idx[-1].date()),
        "final_balance": float(wealth.iloc[-1]),
        "cagr": float(cagr),
        "max_drawdown": float(dd.min()),
        "average_exposure": exposure,
        "signal_switches": switches,
        "wealth_at_max_drawdown": float(wealth.loc[dd.idxmin()]),
        "max_drawdown_date": str(dd.idxmin().date()),
    }


def event_table(label, sig, tqqq, idx):
    # Execution happens next open, so report signal transitions and the
    # subsequent 1/5/20-session TQQQ returns from the next open.
    close = tqqq["adj_close"]
    transitions = sig.diff().fillna(0)
    rows = []
    for i in np.flatnonzero(transitions.to_numpy() != 0):
        if i + 1 >= len(idx):
            continue
        direction = "ENTER" if transitions.iloc[i] > 0 else "EXIT"
        entry_i = i + 1
        base = close.iloc[i]
        fwd = {}
        for n in (1, 5, 20):
            j = min(entry_i + n - 1, len(idx) - 1)
            fwd[f"tqqq_fwd_{n}d"] = float(close.iloc[j] / base - 1)
        rows.append({
            "signal_source": label,
            "signal_date": str(idx[i].date()),
            "execution_date": str(idx[entry_i].date()),
            "direction": direction,
            "trigger_price": float(close.iloc[i]),
            "days_since_prior_signal": int(i - np.flatnonzero(transitions.to_numpy() != 0)[np.flatnonzero(transitions.to_numpy() != 0) < i][-1])
                if np.any(np.flatnonzero(transitions.to_numpy() != 0) < i) else None,
            **fwd,
        })
    return pd.DataFrame(rows)


def main():
    qqq = download("QQQ")
    tqqq = download("TQQQ")
    idx = qqq.index.intersection(tqqq.index)
    qqq, tqqq = qqq.reindex(idx), tqqq.reindex(idx)

    qsig = dma_signal(qqq["adj_close"])
    tsig = dma_signal(tqqq["adj_close"])
    overnight, intraday = tqqq_returns(tqqq)

    bh = pd.Series(1.0, index=idx)
    rows = []
    for name, sig in [
        ("TQQQ buy_and_hold", bh),
        ("TQQQ 100DMA_QQQ_trigger", qsig),
        ("TQQQ 100DMA_TQQQ_trigger", tsig),
    ]:
        daily = next_open_daily_returns(sig, overnight, intraday)
        eq = INITIAL * np.cumprod(1 + daily)
        rows.append(stats(name, sig, daily, eq, idx))

    results = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "tqqq_100dma_trigger_source_forensic.csv", index=False)

    events = pd.concat([
        event_table("QQQ", qsig, tqqq, idx),
        event_table("TQQQ", tsig, tqqq, idx),
    ], ignore_index=True)
    events.to_csv(OUT / "tqqq_100dma_trigger_events.csv", index=False)

    disagreement = (qsig != tsig)
    diag = pd.DataFrame([{
        "qqq_tqqq_signal_disagreement_days": int(disagreement.sum()),
        "total_common_sessions": len(idx),
        "disagreement_pct": float(disagreement.mean()),
        "qqq_trigger_entries": int((qsig.diff() > 0).sum()),
        "qqq_trigger_exits": int((qsig.diff() < 0).sum()),
        "tqqq_trigger_entries": int((tsig.diff() > 0).sum()),
        "tqqq_trigger_exits": int((tsig.diff() < 0).sum()),
    }])
    diag.to_csv(OUT / "tqqq_100dma_trigger_diagnostics.csv", index=False)

    print(results.to_string(index=False))
    print("\nSignal diagnostics:")
    print(diag.to_string(index=False))
    print("\nArtifacts written:")
    print("  tqqq_100dma_trigger_source_forensic.csv")
    print("  tqqq_100dma_trigger_events.csv")
    print("  tqqq_100dma_trigger_diagnostics.csv")


if __name__ == "__main__":
    main()
