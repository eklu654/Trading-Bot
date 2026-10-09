"""Historical real-index Fed/DMA defense study; explicitly not a TQQQ simulation.

Downloads actual Nasdaq Composite and S&P 500 index closes, FRED daily effective
federal funds rate, and 3-month Treasury bill monthly yield. The pre-2008 Fed
state is a separately named historical proxy because the modern target-range
series used by the current QQQ candidate does not cover the 1970s.
"""
from __future__ import annotations
import hashlib, io, json
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "historical_real_index_fed_dma_2026-10-09"
START = "1971-01-01"
END = pd.Timestamp.utcnow().strftime("%Y-%m-%d")
INITIAL = 1.0
DMA = 200
EXPOSURES = (0.0, 0.25, 0.50, 0.75)
EPISODES = [
 ("1973-74 bear", "1973-01-01", "1975-12-31"),
 ("1980-82 inflation bear", "1980-01-01", "1982-12-31"),
 ("1987 crash", "1987-08-01", "1988-03-31"),
 ("1990 recession", "1989-07-01", "1991-03-31"),
 ("dot-com bear", "2000-01-01", "2002-12-31"),
 ("financial crisis", "2007-10-01", "2009-06-30"),
 ("2011 correction", "2011-04-01", "2011-12-31"),
 ("2015-16 correction", "2015-06-01", "2016-06-30"),
 ("2018 selloff", "2018-09-01", "2019-04-30"),
 ("COVID crash", "2020-02-01", "2020-08-31"),
 ("2022 tightening bear", "2022-01-01", "2022-12-31"),
]

def get_url(url: str) -> bytes:
    req = Request(url, headers={"User-Agent":"Trading-Bot-historical-research/1.0"})
    with urlopen(req, timeout=60) as response:
        return response.read()

def fred(series: str) -> pd.Series:
    frame = pd.read_csv(io.BytesIO(get_url(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}")))
    frame.columns = ["date", "value"]
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.dropna().set_index("date")["value"].sort_index().rename(series)

def index_close(ticker: str) -> pd.Series:
    frame = yf.download(ticker, start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if frame.empty:
        raise RuntimeError(f"No Yahoo Finance index data for {ticker}")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    s = frame["Close"].dropna().astype(float)
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index().rename(ticker)

def index_open(ticker: str) -> pd.Series:
    frame = yf.download(ticker, start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if frame.empty: raise RuntimeError(f'No Yahoo Finance index data for {ticker}')
    if isinstance(frame.columns, pd.MultiIndex): frame.columns = frame.columns.get_level_values(0)
    s = frame['Open'].dropna().astype(float)
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated(keep='last')].sort_index().rename(ticker+'_OPEN')

def state_frame(index: pd.DatetimeIndex, dff: pd.Series) -> pd.DataFrame:
    # DFF observations are published with a lag; shift the rate series by one
    # calendar day before mapping to index sessions, then lag mapped state one
    # index session. This historical proxy is not the modern target-rate builder.
    daily = dff.copy()
    daily.index = daily.index + pd.Timedelta(days=1)
    ix = pd.DataFrame({"date": pd.to_datetime(index).astype("datetime64[ns]")}).sort_values("date")
    rates = daily.rename("dff").reset_index()
    rates["date"] = pd.to_datetime(rates["date"]).astype("datetime64[ns]")
    rates.columns = ["date", "dff"]
    mapped = pd.merge_asof(ix, rates.sort_values("date"), on="date", direction="backward")
    mapped = mapped.set_index("date")
    rate = mapped["dff"]
    rate_90 = rate.reindex(rate.index - pd.Timedelta(days=90)).to_numpy()
    # use time-based asof lookup, explicitly only prior/available data
    prior_dates = rate.index - pd.Timedelta(days=90)
    pos = rate.index.searchsorted(prior_dates, side="right") - 1
    prior = np.full(len(rate), np.nan)
    ok = pos >= 0
    prior[ok] = rate.to_numpy()[pos[ok]]
    delta = rate.to_numpy() - prior
    # Historical policy proxy: rate above its 90-calendar-day prior level.
    # One-session lag is applied before state is used by the index signal.
    raw = pd.Series(np.where(np.isfinite(delta) & (delta > 0.01), "TIGHTENING_ACTIVE", "NOT_ACTIVE"), index=rate.index)
    lagged = raw.shift(1).fillna("INSUFFICIENT_HISTORY")
    return pd.DataFrame({"dff": rate, "dff_change_90d": delta, "fed_state_lagged": lagged}, index=rate.index)

def treasury_cash_returns(index: pd.DatetimeIndex, tb3ms: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    # TB3MS is a monthly annualized percent yield. Lag one calendar month to
    # avoid using the current month's as-yet-unpublished value.
    tb = tb3ms.copy()
    tb.index = tb.index + pd.offsets.MonthBegin(1)
    ix = pd.DataFrame({"date": pd.to_datetime(index).astype("datetime64[ns]")}).sort_values("date")
    right = tb.rename("yield_pct").reset_index()
    right["date"] = pd.to_datetime(right["date"]).astype("datetime64[ns]")
    right.columns = ["date", "yield_pct"]
    mapped = pd.merge_asof(ix, right.sort_values("date"), on="date", direction="backward").set_index("date")
    annual = mapped["yield_pct"].fillna(0).to_numpy() / 100.0
    daily = np.power(1.0 + annual, 1.0/252.0) - 1.0
    return daily, annual

def build_signal(close: pd.Series, fed_state: pd.Series, mode: str) -> tuple[np.ndarray, pd.DataFrame]:
    dma = close.rolling(DMA, min_periods=DMA).mean()
    below = close < dma
    active = fed_state.reindex(close.index).fillna("INSUFFICIENT_HISTORY").eq("TIGHTENING_ACTIVE")
    if mode == "combined":
        raw = below & active
    elif mode == "dma_only":
        raw = below
    elif mode == "fed_only":
        raw = active
    else:
        raise ValueError(mode)
    armed = False
    states, transitions = [], []
    for date, should_arm, price, avg, fstate in zip(close.index, raw.to_numpy(), close.to_numpy(), dma.to_numpy(), fed_state.reindex(close.index).fillna("INSUFFICIENT_HISTORY").to_numpy()):
        if mode == "combined":
            if not armed and bool(should_arm):
                armed = True
                transitions.append({"date":date.date().isoformat(),"event":"ENTER","mode":mode,"index_close":float(price),"dma200":float(avg),"fed_state":str(fstate)})
            elif armed and np.isfinite(avg) and price >= avg:
                armed = False
                transitions.append({"date":date.date().isoformat(),"event":"EXIT","mode":mode,"index_close":float(price),"dma200":float(avg),"fed_state":str(fstate)})
        else:
            armed = bool(should_arm)
            if not states or armed != states[-1]:
                transitions.append({"date":date.date().isoformat(),"event":"ENTER" if armed else "EXIT","mode":mode,"index_close":float(price),"dma200":float(avg) if np.isfinite(avg) else None,"fed_state":str(fstate)})
        states.append(armed)
    return np.asarray(states,dtype=bool), pd.DataFrame(transitions)

def calc_metrics(daily_returns: np.ndarray, dates: pd.DatetimeIndex, label: str) -> dict:
    eq = INITIAL * np.cumprod(1.0 + daily_returns)
    peak = np.maximum.accumulate(eq)
    years = max((dates[-1]-dates[0]).days/365.25, 0.01)
    roll = pd.Series(np.log1p(daily_returns)).rolling(252,min_periods=252).sum().dropna()
    return {"index":label,"final_normalized_wealth":float(eq[-1]),"cagr":float(eq[-1]**(1/years)-1),"max_drawdown":float((eq/peak-1).min()),"worst_rolling_252d_return":float(np.expm1(roll.min())) if len(roll) else None}

def run_one(close: pd.Series, open_price: pd.Series, fed: pd.Series, cash: np.ndarray, label: str, input_hashes: dict) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    close = close.loc[START:].dropna()
    rets = close.pct_change().fillna(0).to_numpy()
    open_price = open_price.reindex(close.index)
    overnight = open_price.to_numpy() / np.r_[close.to_numpy()[0], close.to_numpy()[:-1]] - 1.0
    overnight[0] = 0.0
    intraday = close.to_numpy() / open_price.to_numpy() - 1.0
    cash_half = np.sqrt(1.0 + cash)
    states = {}
    trans = []
    for mode in ("combined","fed_only","dma_only"):
        st, ev = build_signal(close, fed, mode)
        states[mode] = st
        if len(ev):
            ev.insert(0,"index",label)
            trans.append(ev)
    rows, episodes = [], []
    for mode, st in states.items():
        # Close-derived state changes exposure on the next session only.
        st_exec = np.r_[False, st[:-1]]
        for exposure in EXPOSURES:
            name = f"{mode}_defense_{int(exposure*100)}pct"
            weights = np.where(st_exec, exposure, 1.0)
            weights_prev = np.r_[1.0, weights[:-1]]
            overnight_factor = weights_prev*(1.0+overnight) + (1.0-weights_prev)*cash_half
            intraday_factor = weights*(1.0+intraday) + (1.0-weights)*cash_half
            portret = overnight_factor*intraday_factor - 1.0
            m = calc_metrics(portret, close.index, label)
            m.update({"mechanic":mode,"defensive_index_exposure":exposure,"defensive_sessions":int(st_exec.sum()),"defensive_fraction":float(st_exec.mean()),"signal_transitions":int(np.count_nonzero(st[1:]!=st[:-1])),"executed_exposure_transitions":int(np.count_nonzero(st_exec[1:]!=st_exec[:-1])),"input_hashes":json.dumps(input_hashes,sort_keys=True)})
            rows.append(m)
            eq = np.cumprod(1+portret)
            for ep, start, end in EPISODES:
                mask=(close.index>=start)&(close.index<=end)
                if not mask.any(): continue
                er=portret[mask]; ee=np.cumprod(1+er); dd=(ee/np.maximum.accumulate(ee)-1).min()
                episodes.append({"index":label,"episode":ep,"mechanic":mode,"defensive_index_exposure":exposure,"start":close.index[mask][0].date().isoformat(),"end":close.index[mask][-1].date().isoformat(),"return":float(ee[-1]-1),"local_max_drawdown":float(dd),"defensive_sessions":int(st_exec[mask].sum())})
    # Unprotected 100%-index control, measured on the exact same sessions.
    control = calc_metrics(rets, close.index, label)
    control.update({"mechanic":"no_defense","defensive_index_exposure":1.0,"defensive_sessions":0,"defensive_fraction":0.0,"signal_transitions":0,"executed_exposure_transitions":0,"input_hashes":json.dumps(input_hashes,sort_keys=True)})
    rows.append(control)
    for ep, start, end in EPISODES:
        mask=(close.index>=start)&(close.index<=end)
        if not mask.any(): continue
        er=rets[mask]; ee=np.cumprod(1+er); dd=(ee/np.maximum.accumulate(ee)-1).min()
        episodes.append({"index":label,"episode":ep,"mechanic":"no_defense","defensive_index_exposure":1.0,"start":close.index[mask][0].date().isoformat(),"end":close.index[mask][-1].date().isoformat(),"return":float(ee[-1]-1),"local_max_drawdown":float(dd),"defensive_sessions":0})
    # Zero-yield cash sensitivity for the combined mechanic, alongside the
    # primary TB3MS-cash scenario above.
    st = states["combined"]
    st_exec = np.r_[False, st[:-1]]
    for exposure in EXPOSURES:
        zero_cash = np.zeros_like(cash)
        weights = np.where(st_exec, exposure, 1.0)
        weights_prev = np.r_[1.0, weights[:-1]]
        overnight_factor = weights_prev*(1.0+overnight) + (1.0-weights_prev)*np.sqrt(1.0+zero_cash)
        intraday_factor = weights*(1.0+intraday) + (1.0-weights)*np.sqrt(1.0+zero_cash)
        portret = overnight_factor*intraday_factor - 1.0
        m = calc_metrics(portret, close.index, label)
        m.update({"mechanic":"combined_zero_yield_cash","defensive_index_exposure":exposure,"defensive_sessions":int(st_exec.sum()),"defensive_fraction":float(st_exec.mean()),"signal_transitions":int(np.count_nonzero(st[1:]!=st[:-1])),"executed_exposure_transitions":int(np.count_nonzero(st_exec[1:]!=st_exec[:-1])),"input_hashes":json.dumps(input_hashes,sort_keys=True)})
        rows.append(m)
        for ep, start, end in EPISODES:
            mask=(close.index>=start)&(close.index<=end)
            if not mask.any(): continue
            er=portret[mask]; ee=np.cumprod(1+er); dd=(ee/np.maximum.accumulate(ee)-1).min()
            episodes.append({"index":label,"episode":ep,"mechanic":"combined_zero_yield_cash","defensive_index_exposure":exposure,"start":close.index[mask][0].date().isoformat(),"end":close.index[mask][-1].date().isoformat(),"return":float(ee[-1]-1),"local_max_drawdown":float(dd),"defensive_sessions":int(st_exec[mask].sum())})
    return pd.DataFrame(rows),pd.concat(trans,ignore_index=True) if trans else pd.DataFrame(),pd.DataFrame(episodes)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources={}
    indexes={}
    opens={}
    for ticker in ("^IXIC","^GSPC"):
        indexes[ticker]=index_close(ticker)
        opens[ticker]=index_open(ticker)
        sources[ticker]=hashlib.sha256((indexes[ticker].to_csv()+opens[ticker].to_csv()).encode()).hexdigest()
    dff=fred("DFF")
    tb3ms=fred("TB3MS")
    sources["DFF"]=hashlib.sha256(dff.to_csv().encode()).hexdigest()
    sources["TB3MS"]=hashlib.sha256(tb3ms.to_csv().encode()).hexdigest()
    all_dates=sorted(set().union(*(s.index for s in indexes.values())))
    fedframe=state_frame(pd.DatetimeIndex(all_dates),dff)
    cash, annual_cash=treasury_cash_returns(pd.DatetimeIndex(all_dates),tb3ms)
    fed=pd.Series(fedframe["fed_state_lagged"].to_numpy(),index=fedframe.index)
    results=[]; events=[]; episode_rows=[]
    for ticker, close in indexes.items():
        idx=close.index
        local_fed=fed.reindex(idx).ffill().fillna("INSUFFICIENT_HISTORY")
        local_cash=pd.Series(cash,index=fedframe.index).reindex(idx).fillna(0).to_numpy()
        r,e,ep=run_one(close,opens[ticker],local_fed,local_cash,ticker,sources)
        results.append(r); episode_rows.append(ep)
        if len(e): events.append(e)
    summary=pd.concat(results,ignore_index=True)
    transitions=pd.concat(events,ignore_index=True) if events else pd.DataFrame()
    episodes=pd.concat(episode_rows,ignore_index=True)
    summary.to_csv(OUT/"summary.csv",index=False)
    transitions.to_csv(OUT/"transitions.csv",index=False)
    episodes.to_csv(OUT/"episodes.csv",index=False)
    for ticker,close in indexes.items():
        close.rename("close").to_csv(OUT/f"{ticker.replace('^','')}_daily_close.csv")
    fedframe.to_csv(OUT/"fed_state_daily.csv")
    (OUT/"manifest.json").write_text(json.dumps({"created_utc":pd.Timestamp.utcnow().isoformat(),"start":START,"end_exclusive":END,"rows":{k:len(v) for k,v in indexes.items()},"first_dates":{k:v.index.min().date().isoformat() for k,v in indexes.items()},"last_dates":{k:v.index.max().date().isoformat() for k,v in indexes.items()},"sha256":sources,"policy_state_definition":"historical proxy: DFF is available one calendar day later; lagged index-session state is TIGHTENING_ACTIVE when effective federal funds rate is >1 basis point above its value 90 calendar days earlier; this is NOT the modern DFEDTAR-based state builder","cash_definition":"TB3MS annualized percent yield lagged one month, converted to effective daily accrual using (1+y)^(1/252)-1; missing cash yield is zero","caveats":["price-index returns exclude dividends","index exposure is unleveraged; not TQQQ","Nasdaq Composite and S&P 500 are not QQQ","Yahoo Finance is the price data source and may revise historical observations"]},indent=2))
    print(summary[["index","mechanic","defensive_index_exposure","final_normalized_wealth","cagr","max_drawdown","worst_rolling_252d_return","defensive_sessions","executed_exposure_transitions"]].to_string(index=False))
    print(f"OUTPUT_DIR={OUT}")
if __name__=="__main__": main()
