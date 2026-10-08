"""Historical Fed-regime falsification test.

This file deliberately does NOT backtest TQQQ or assign synthetic TQQQ returns.
It extends the frozen event/classification hypothesis to a long Nasdaq-100 proxy
history so older Fed tightening cycles can falsify the rule.

FROZEN hypothesis:
    At the first +10% recovery from the post-shock low following a >=4.5%
    one-day decline, aggressive tightening is present iff the Fed target
    increased by >=50 bp over the preceding 63 calendar days.

No threshold optimization is performed here.
Market proxy: Yahoo ^NDX (Nasdaq-100), not QQQ/TQQQ.
Fed source: FRED DFEDTAR (pre-2008 target) plus DFEDTARL/U (post-2008 range),
converted to a midpoint after 2008.
"""
from pathlib import Path
import io
import numpy as np
import pandas as pd
import requests
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
SHOCK=-0.045
RECOVERY=0.10
WINDOW_DAYS=63
THRESHOLD_BP=50
START="1985-01-01"
END="2026-10-09"

def market():
    x=yf.download("^NDX",start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x["Close"].astype(float).sort_index()

def fred():
    url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTAR,DFEDTARL,DFEDTARU"
    r=requests.get(url,timeout=30)
    r.raise_for_status()
    x=pd.read_csv(io.StringIO(r.text))
    x.observation_date=pd.to_datetime(x.observation_date)
    for c in ["DFEDTAR","DFEDTARL","DFEDTARU"]:
        x[c]=pd.to_numeric(x[c],errors="coerce")
    # Historical single target through 2008; target range thereafter.
    x["target"]=x["DFEDTAR"]
    rng=x["DFEDTARL"].notna() & x["DFEDTARU"].notna()
    x.loc[rng,"target"]=(x.loc[rng,"DFEDTARL"]+x.loc[rng,"DFEDTARU"])/2
    return x.set_index("observation_date")["target"].dropna()

def events(px):
    r=px.pct_change().fillna(0).to_numpy()
    a=px.to_numpy()
    armed=False; low=np.nan; low_i=None; shock_i=None; rows=[]
    for i in range(1,len(px)):
        if not armed and r[i] <= SHOCK:
            armed=True; low=a[i]; low_i=i; shock_i=i
        if armed:
            if a[i] < low: low=a[i]; low_i=i
            gain=a[i]/low-1
            if gain >= RECOVERY:
                rows.append({
                    "shock_date":str(px.index[shock_i].date()),
                    "low_date":str(px.index[low_i].date()),
                    "recovery_date":str(px.index[i].date()),
                    "days_low_to_recovery":int((px.index[i]-px.index[low_i]).days),
                    "trading_days_low_to_recovery":int(i-low_i),
                    "shock_to_recovery_trading_days":int(i-shock_i),
                })
                armed=False; low=np.nan; low_i=None; shock_i=None
    return pd.DataFrame(rows)

def add_fed_features(ev,rate):
    out=ev.copy()
    idx=rate.index
    for col in ["shock_date","low_date","recovery_date"]:
        out[col]=pd.to_datetime(out[col])
    vals=[]
    for d in out.recovery_date:
        prior=rate.loc[:d]
        cur=float(prior.iloc[-1])
        past=rate.loc[:d-pd.Timedelta(days=WINDOW_DAYS)]
        old=float(past.iloc[-1]) if len(past) else np.nan
        vals.append((cur,old,cur-old))
    f=pd.DataFrame(vals,columns=["fed_target","fed_target_63d_prior","fed_change_63d"],index=out.index)
    out=pd.concat([out,f],axis=1)
    out["hike_bp_63d"]=out.fed_change_63d*100
    out["aggressive_tightening_50bp"]=out.hike_bp_63d>=THRESHOLD_BP
    # Forward market path is descriptive only; it is NOT used to define the rule.
    for days in [20,60,120,252]:
        vals=[]
        for d in out.recovery_date:
            future=px.loc[d:]
            if len(future)<=1: vals.append(np.nan); continue
            future=future.iloc[:days+1]
            vals.append(float(future.iloc[-1]/future.iloc[0]-1))
        out[f"forward_{days}d_return"]=vals
    return out

if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    px=market()
    rate=fred()
    ev=events(px)
    # globals used only for descriptive forward returns
    globals()["px"]=px
    ev=add_fed_features(ev,rate)
    ev["era"]=pd.cut(ev.recovery_date,
        bins=[pd.Timestamp("1989-12-31"),pd.Timestamp("1995-12-31"),
              pd.Timestamp("2001-12-31"),pd.Timestamp("2007-12-31"),
              pd.Timestamp("2013-12-31"),pd.Timestamp("2019-12-31"),
              pd.Timestamp("2023-12-31"),pd.Timestamp("2100-01-01")],
        labels=["1990-95","2000-01","2002-07","2008-13","2014-19","2020-23","2024+"])
    ev.to_csv(OUT/"fed_historical_falsification_event_ledger.csv",index=False)
    print("\nFROZEN RULE: >=50bp target increase in prior 63 calendar days")
    print("\nEVENTS")
    print(ev.to_string(index=False))
    print("\nRULE COVERAGE BY ERA")
    print(ev.groupby("era",observed=True)["aggressive_tightening_50bp"].agg(["count","sum","mean"]).to_string())
    print("\nGATED EVENTS")
    print(ev[ev.aggressive_tightening_50bp][["shock_date","low_date","recovery_date","hike_bp_63d","days_low_to_recovery","forward_120d_return"]].to_string(index=False))
    print("\nNON-GATED EVENTS")
    print(ev[~ev.aggressive_tightening_50bp][["shock_date","low_date","recovery_date","hike_bp_63d","days_low_to_recovery","forward_120d_return"]].to_string(index=False))
