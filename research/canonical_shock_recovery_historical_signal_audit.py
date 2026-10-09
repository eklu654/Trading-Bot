"""Signal-only historical stress audit for the canonical shock rule and active-Fed/200-DMA state.

Actual TQQQ returns are intentionally NOT simulated before TQQQ existed. For
1970s/1987 the S&P 500 is only a broad-market signal proxy; for 2000-2002 QQQ
prices exist and the Fed-active/200-DMA state can be inspected, but no actual
TQQQ return series exists. Outputs are timing/state diagnostics only.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from test_tqqq_fed_paused_dma_sticky import download_fed, download_qqq, build_daily_states

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
SHOCK = -0.045
RECOVERY = 0.10
DMA = 200


def shock_events(price: pd.Series) -> list[dict]:
    p = price.astype(float).dropna()
    r = p.pct_change().fillna(0.0)
    armed = False
    shock_i = low_i = None
    rows = []
    for i in range(1, len(p)):
        if not armed and r.iloc[i] <= SHOCK:
            armed = True
            shock_i = low_i = i
        if armed:
            if p.iloc[i] < p.iloc[low_i]:
                low_i = i
            if p.iloc[i] / p.iloc[low_i] - 1 >= RECOVERY:
                rows.append({
                    "shock_date": p.index[shock_i].date().isoformat(),
                    "low_date": p.index[low_i].date().isoformat(),
                    "recovery_decision_close": p.index[i].date().isoformat(),
                    "sessions_defensive_signal": i - shock_i,
                })
                armed = False
    return rows


def drawdown_episodes(price: pd.Series, market: str, fed_state: pd.Series | None = None) -> list[dict]:
    p = price.astype(float).dropna()
    high = p.rolling(252, min_periods=1).max()
    dma = p.rolling(DMA, min_periods=DMA).mean()
    dd = p / high - 1
    raw_shock = p.pct_change().fillna(0).le(SHOCK)
    state = fed_state.reindex(p.index).fillna("UNAVAILABLE") if fed_state is not None else pd.Series("NOT_TESTED", index=p.index)
    armed = False
    ep = None
    rows = []
    for i, date in enumerate(p.index):
        if ep is None and p.iloc[i] <= high.iloc[i] * 0.95:
            win = p.iloc[max(0, i-251):i+1]
            ep = {"start_i": i, "start": date, "peak_date": win.idxmax(), "peak": float(high.iloc[i]), "trough_date": date, "trough": float(p.iloc[i])}
        if ep is not None:
            if p.iloc[i] < ep["trough"]:
                ep["trough"], ep["trough_date"] = float(p.iloc[i]), date
            if p.iloc[i] >= ep["peak"] * 0.95 or i == len(p)-1:
                maxdd = ep["trough"] / ep["peak"] - 1
                if maxdd <= -0.15:
                    segment = p.index[ep["start_i"]:i+1]
                    shocks = segment[raw_shock.loc[segment].to_numpy()]
                    states = state.loc[segment]
                    below = p.loc[segment] < dma.loc[segment]
                    active_condition = below & states.eq("TIGHTENING_ACTIVE")
                    rows.append({
                        "market": market,
                        "episode_start": ep["start"].date().isoformat(),
                        "reference_peak_date": ep["peak_date"].date().isoformat(),
                        "trough_date": ep["trough_date"].date().isoformat(),
                        "episode_end": date.date().isoformat(),
                        "peak_to_trough_drawdown": float(maxdd),
                        "sessions": int(i-ep["start_i"]+1),
                        "first_daily_shock": shocks[0].date().isoformat() if len(shocks) else "",
                        "sessions_until_first_shock": int(p.index.get_loc(shocks[0])-ep["start_i"]) if len(shocks) else None,
                        "fed_state_at_start": str(state.loc[ep["start"]]),
                        "fed_state_at_trough": str(state.loc[ep["trough_date"]]),
                        "below_200dma_sessions": int(below.sum()),
                        "active_fed_below_200dma_sessions": int(active_condition.sum()),
                        "first_active_fed_below_200dma": active_condition[active_condition].index[0].date().isoformat() if active_condition.any() else "",
                    })
                ep = None
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Historical S&P signal proxy, before QQQ existed.
    spx = yf.download("^GSPC", start="1970-01-01", end="1999-03-10", auto_adjust=False, progress=False, actions=False)
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    spx.index = pd.to_datetime(spx.index).tz_localize(None)
    spx_price = (spx["Adj Close"] if "Adj Close" in spx.columns else spx["Close"]).dropna().rename("price")
    # QQQ plus live-safe Fed state for its actual existence period.
    fed = download_fed()
    qqq = download_qqq()
    qqq_states = build_daily_states(fed, qqq)
    lagged_fed = qqq_states["monetary_state"].shift(1).fillna("INSUFFICIENT_HISTORY")
    qqq_price = qqq_states["close"].dropna()

    episodes = []
    episodes.extend(drawdown_episodes(spx_price, "SPX_signal_proxy_1970_to_1999"))
    episodes.extend(drawdown_episodes(qqq_price, "QQQ_signal_only", lagged_fed))
    episode_df = pd.DataFrame(episodes)

    event_rows = []
    for market, price in [("SPX_signal_proxy", spx_price), ("QQQ_signal_only", qqq_price)]:
        for event in shock_events(price):
            event_rows.append({"market": market, **event})
    event_df = pd.DataFrame(event_rows)

    qqq_dma = qqq_price.rolling(DMA, min_periods=DMA).mean()
    active = (qqq_price < qqq_dma) & lagged_fed.reindex(qqq_price.index).eq("TIGHTENING_ACTIVE")
    armed = False
    weights, transitions = [], []
    for date, price, ma, fed_state in zip(qqq_price.index, qqq_price, qqq_dma, lagged_fed.reindex(qqq_price.index)):
        if not np.isfinite(ma):
            weights.append(1.0)
            continue
        if not armed and price < ma and fed_state == "TIGHTENING_ACTIVE":
            armed = True
            transitions.append({"date": date.date().isoformat(), "state": "ENTER", "qqq_adj_close": float(price), "dma_200": float(ma), "fed_state_lagged": str(fed_state)})
        elif armed and price >= ma:
            armed = False
            transitions.append({"date": date.date().isoformat(), "state": "EXIT", "qqq_adj_close": float(price), "dma_200": float(ma), "fed_state_lagged": str(fed_state)})
        weights.append(0.0 if armed else 1.0)
    qqq_daily = pd.DataFrame({
        "date": qqq_price.index, "qqq_adjusted_close": qqq_price.to_numpy(),
        "dma_200": qqq_dma.to_numpy(), "fed_state_lagged": lagged_fed.reindex(qqq_price.index).to_numpy(),
        "active_fed_below_dma_condition": active.to_numpy(), "overlay_defensive_signal": np.asarray(weights),
    })
    windows = []
    for market, price in [("SPX_signal_proxy", spx_price), ("QQQ_signal_only", qqq_price)]:
        ranges = [("1971-1975","1971-01-01","1975-12-31"),("1973-1975","1973-01-01","1975-12-31"),("1987 crash","1987-01-01","1988-01-31"),("2000-2002 dot-com","2000-01-01","2002-12-31"),("2007-2009 GFC","2007-01-01","2009-12-31")]
        for label,start,end in ranges:
            mask=(price.index>=start)&(price.index<=end)
            if not mask.any(): continue
            s=price.loc[mask]; ret=float(s.iloc[-1]/s.iloc[0]-1); dd=float((s/s.cummax()-1).min())
            windows.append({"market":market,"window":label,"start":s.index[0].date().isoformat(),"end":s.index[-1].date().isoformat(),"index_total_return":ret,"index_max_drawdown":dd,"observations":len(s),"leveraged_tqqq_return":"NOT_APPLICABLE"})
    window_df=pd.DataFrame(windows)
    spx_frame=pd.DataFrame({"date":spx_price.index,"spx_adjusted_close":spx_price.to_numpy()})
    spx_frame.to_csv(OUT/"canonical_historical_signal_spx_inputs.csv",index=False,float_format="%.12g")
    qqq_states.to_csv(OUT/"canonical_historical_signal_qqq_fed_states.csv",index_label="date",float_format="%.12g")
    episode_df.to_csv(OUT/"canonical_historical_signal_drawdown_episodes.csv",index=False)
    event_df.to_csv(OUT/"canonical_historical_signal_shock_events.csv",index=False)
    qqq_daily.to_csv(OUT/"canonical_historical_signal_qqq_daily.csv",index=False,float_format="%.12g")
    pd.DataFrame(transitions).to_csv(OUT/"canonical_historical_signal_qqq_overlay_transitions.csv",index=False)
    window_df.to_csv(OUT/"canonical_historical_signal_window_summary.csv",index=False)
    digest=hashlib.sha256((OUT/"canonical_historical_signal_qqq_fed_states.csv").read_bytes()).hexdigest()
    manifest={
        "status":"SIGNAL_ONLY_HISTORICAL_AUDIT",
        "spx_start":spx_price.index[0].date().isoformat(),"spx_end":spx_price.index[-1].date().isoformat(),
        "qqq_start":qqq_price.index[0].date().isoformat(),"qqq_end":qqq_price.index[-1].date().isoformat(),
        "qqq_rows":len(qqq_price),"qqq_state_input_sha256":digest,
        "shock_threshold":SHOCK,"recovery_threshold":RECOVERY,"dma":DMA,
        "fed_state_lag_sessions":1,
        "episode_definition":"begin at <= -5% from rolling 252-session high; end at 95% of reference peak; report drawdown <= -15%",
        "warning":"No TQQQ returns are simulated before TQQQ existed. S&P 500 results are broad-market signal proxies, not QQQ/TQQQ backtests.",
    }
    (OUT/"canonical_historical_signal_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("\nHISTORICAL DRAWdown EPISODES"); print(episode_df.to_string(index=False))
    print("\nSHOCK/RECOVERY SIGNAL EVENTS"); print(event_df.to_string(index=False))
    print("\nQQQ ACTIVE-FED/200-DMA TRANSITIONS"); print(pd.DataFrame(transitions).to_string(index=False))
    print("\nWINDOWS"); print(window_df.to_string(index=False))
    print("\nMANIFEST"); print(json.dumps(manifest,indent=2))


if __name__ == "__main__":
    main()
