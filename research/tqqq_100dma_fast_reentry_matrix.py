"""100-DMA fixed-exit / faster-reentry forensic matrix.

The 100-DMA exit is held constant. Only the re-entry rule changes.

Trigger assets:
  QQQ, TQQQ

Exit:
  trigger close < 100-DMA -> exit at next open.

Re-entry candidates:
  100-DMA reclaim (baseline)
  50-DMA reclaim
  20-DMA reclaim
  20-DMA + 50-DMA trend confirmation (close > 20 and 20 > 50)

No lookahead: signals are observed at close and executed next session open.
This is a diagnostic matrix, not an optimization exercise.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-07"
EXIT_DMA = 100
REENTRY_DMAS = (100, 50, 20)


def download(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open": "open", "Close": "close",
                             "Adj Close": "adj_close"})[
        ["open", "close", "adj_close"]
    ].sort_index().dropna()


def tqqq_returns(tqqq):
    adj_open = tqqq["open"] * tqqq["adj_close"] / tqqq["close"]
    overnight = (adj_open / tqqq["adj_close"].shift(1) - 1).fillna(0.0)
    intraday = (tqqq["adj_close"] / adj_open - 1).fillna(0.0)
    return overnight, intraday


def signal_series(price, reentry):
    ma100 = price.rolling(EXIT_DMA).mean()
    mare = price.rolling(reentry).mean()
    trend50 = price.rolling(50).mean()

    in_market = False
    out = []
    for i in range(len(price)):
        if not in_market:
            # Initial state is invested once the exit DMA has warmed up.
            # During a defensive state, only the re-entry rule can restore risk.
            if i >= EXIT_DMA - 1 and price.iloc[i] >= mare.iloc[i]:
                if reentry == 20 and i >= 49:
                    if price.iloc[i] >= mare.iloc[i] and mare.iloc[i] >= trend50.iloc[i]:
                        in_market = True
                else:
                    in_market = True
        else:
            if i >= EXIT_DMA - 1 and price.iloc[i] < ma100.iloc[i]:
                in_market = False
        out.append(float(in_market))
    return pd.Series(out, index=price.index)


def event_diagnostics(trigger, sig, tqqq):
    tr = sig.diff().fillna(0)
    close = tqqq["adj_close"]
    rows = []
    transition_idx = np.flatnonzero(tr.to_numpy() != 0)
    for k, i in enumerate(transition_idx):
        if i + 1 >= len(sig):
            continue
        direction = "ENTER" if tr.iloc[i] > 0 else "EXIT"
        if direction == "ENTER":
            # From the signal date through execution, measure how much TQQQ
            # rebound occurred before the re-entry and how much was missed.
            exit_candidates = transition_idx[:k][tr.iloc[transition_idx[:k]].to_numpy() < 0]
            exit_i = int(exit_candidates[-1]) if len(exit_candidates) else None
            if exit_i is not None:
                exec_i = i + 1
                post_exit = close.iloc[exit_i:exec_i + 1]
                trough_i = int(post_exit.idxmin().to_pydatetime().toordinal()) if False else post_exit.index.get_loc(post_exit.idxmin())
                trough_date = post_exit.index[trough_i]
                trough_pos = close.index.get_loc(trough_date)
                missed = float(close.iloc[exec_i] / close.iloc[trough_pos] - 1)
                exit_to_reentry = float(close.iloc[exec_i] / close.iloc[exit_i] - 1)
                rows.append({
                    "trigger": trigger,
                    "event": "REENTRY",
                    "exit_signal_date": str(close.index[exit_i].date()),
                    "reentry_signal_date": str(close.index[i].date()),
                    "reentry_execution_date": str(close.index[exec_i].date()),
                    "days_out": int((close.index[i] - close.index[exit_i]).days),
                    "tqqq_exit_to_reentry_return": exit_to_reentry,
                    "tqqq_trough_to_reentry_return": missed,
                    "trough_date": str(trough_date.date()),
                })
    return pd.DataFrame(rows)


def stats(name, sig, daily, idx):
    eq = INITIAL * np.cumprod(1 + daily)
    wealth = pd.Series(eq, index=idx)
    years = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    cagr = (wealth.iloc[-1] / INITIAL) ** (1 / years) - 1
    dd = wealth / wealth.cummax() - 1
    return {
        "strategy": name,
        "start": str(idx[0].date()),
        "end": str(idx[-1].date()),
        "final_balance": float(wealth.iloc[-1]),
        "cagr": float(cagr),
        "max_drawdown": float(dd.min()),
        "average_exposure": float(sig.shift(1).fillna(0).mean()),
        "signal_switches": int(sig.diff().abs().fillna(0).sum()),
    }


def main():
    qqq = download("QQQ")
    tqqq = download("TQQQ")
    idx = qqq.index.intersection(tqqq.index)
    qqq, tqqq = qqq.reindex(idx), tqqq.reindex(idx)
    overnight, intraday = tqqq_returns(tqqq)

    rows = []
    events = []
    for trigger_name, trigger in [("QQQ", qqq["adj_close"]),
                                  ("TQQQ", tqqq["adj_close"])]:
        for reentry in REENTRY_DMAS:
            sig = signal_series(trigger, reentry)
            daily = next_open_daily_returns(sig, overnight, intraday)
            rows.append(stats(f"TQQQ | {trigger_name} 100DMA exit + {reentry}DMA reentry",
                              sig, daily, idx))
            ev = event_diagnostics(trigger_name, sig, tqqq)
            ev["reentry_rule"] = f"{reentry}DMA"
            events.append(ev)

        # Trend-confirmed fast reentry is intentionally separate.
        ma20 = trigger.rolling(20).mean()
        ma50 = trigger.rolling(50).mean()
        ma100 = trigger.rolling(100).mean()
        invested = False
        vals = []
        for i in range(len(idx)):
            if invested and trigger.iloc[i] < ma100.iloc[i]:
                invested = False
            elif not invested and i >= 49 and trigger.iloc[i] >= ma20.iloc[i] and ma20.iloc[i] >= ma50.iloc[i]:
                invested = True
            vals.append(float(invested))
        sig = pd.Series(vals, index=idx)
        daily = next_open_daily_returns(sig, overnight, intraday)
        rows.append(stats(f"TQQQ | {trigger_name} 100DMA exit + 20/50 trend reentry",
                          sig, daily, idx))
        ev = event_diagnostics(trigger_name, sig, tqqq)
        ev["reentry_rule"] = "20DMA+50DMA"
        events.append(ev)

    bh = pd.Series(1.0, index=idx)
    daily = next_open_daily_returns(bh, overnight, intraday)
    rows.append(stats("TQQQ buy_and_hold", bh, daily, idx))

    results = pd.DataFrame(rows)
    event_df = pd.concat(events, ignore_index=True) if events else pd.DataFrame()
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "tqqq_100dma_fast_reentry_matrix.csv", index=False)
    event_df.to_csv(OUT / "tqqq_100dma_fast_reentry_events.csv", index=False)

    print(results.sort_values("final_balance", ascending=False).to_string(index=False))
    if not event_df.empty:
        print("\nRe-entry diagnostics:")
        print(event_df.groupby(["trigger", "reentry_rule"]).agg(
            reentries=("event", "count"),
            median_days_out=("days_out", "median"),
            median_trough_to_reentry=("tqqq_trough_to_reentry_return", "median"),
            mean_trough_to_reentry=("tqqq_trough_to_reentry_return", "mean"),
        ).reset_index().to_string(index=False))
    print("\nArtifacts:")
    print("  tqqq_100dma_fast_reentry_matrix.csv")
    print("  tqqq_100dma_fast_reentry_events.csv")


if __name__ == "__main__":
    main()
