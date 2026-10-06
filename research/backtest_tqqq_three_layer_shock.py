"""Three-layer TQQQ backtest: 100-DMA, Fed/60d veto, and shock override.

Strategy 1: plain 100-DMA.
Strategy 2: exact frozen Fed/60d-conditioned rule from the prior study.
Strategy 3: Strategy 2 plus a deliberately predeclared shock override:
  when the Fed/60d veto would keep us invested below the 100-DMA, exit if
  either VIX 20-day percentage change >= 100% OR QQQ 20-day realized-vol
  percentage change >= 100%.

The shock thresholds are NOT optimized here. This run is a mechanism test.
Signal is close-to-next-open. Synthetic daily-reset 3x QQQ. No costs/cash yield.
Also reports a stress test with Fed target artificially held at 5% during 2020.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
START="1999-03-10"
END="2026-10-05"
INITIAL=5000.0
DMA=100
RATE_THRESHOLD=3.5
SHOCK_THRESHOLD=1.0

FED_EVENTS=[
("1999-06-30",.25,5),("1999-08-24",.25,5.25),("1999-11-16",.25,5.5),
("2000-02-02",.25,5.75),("2000-03-21",.25,6),("2000-05-16",.5,6.5),
("2001-01-03",-.5,6),("2001-01-31",-.5,5.5),("2001-03-20",-.5,5),
("2001-04-18",-.5,4.5),("2001-05-15",-.5,4),("2001-06-27",-.25,3.75),
("2001-08-21",-.25,3.5),("2001-09-17",-.5,3),("2001-10-02",-.5,2.5),
("2001-11-06",-.5,2),("2001-12-11",-.25,1.75),("2002-11-06",-.5,1.25),
("2003-06-25",-.25,1),("2004-06-30",.25,1.25),("2004-08-10",.25,1.5),
("2004-09-21",.25,1.75),("2004-11-10",.25,2),("2004-12-14",.25,2.25),
("2005-02-02",.25,2.5),("2005-03-22",.25,2.75),("2005-05-03",.25,3),
("2005-06-30",.25,3.25),("2005-08-09",.25,3.5),("2005-09-20",.25,3.75),
("2005-11-01",.25,4),("2005-12-13",.25,4.25),("2006-01-31",.25,4.5),
("2006-03-28",.25,4.75),("2006-05-10",.25,5),("2006-06-29",.25,5.25),
("2007-09-18",-.5,4.75),("2007-10-31",-.25,4.5),("2007-12-11",-.25,4.25),
("2008-01-22",-.75,3.5),("2008-01-30",-.5,3),("2008-03-18",-.75,2.25),
("2008-04-30",-.25,2),("2008-10-08",-.5,1.5),("2008-10-29",-.5,1),
("2008-12-16",-.75,.125),("2015-12-17",.25,.375),("2016-12-15",.25,.625),
("2017-03-16",.25,.875),("2017-06-15",.25,1.125),("2017-12-14",.25,1.375),
("2018-03-22",.25,1.625),("2018-06-14",.25,1.875),("2018-09-27",.25,2.125),
("2018-12-20",.25,2.375),("2019-08-01",-.25,2.125),("2019-09-19",-.25,1.875),
("2019-10-31",-.25,1.625),("2020-03-04",-.5,1.125),("2020-03-16",-1,.125),
("2022-03-17",.25,.375),("2022-05-05",.5,.875),("2022-06-16",.75,1.625),
("2022-07-28",.75,2.375),("2022-09-22",.75,3.125),("2022-11-03",.75,3.875),
("2022-12-15",.5,4.375),("2023-02-02",.25,4.625),("2023-03-23",.25,4.875),
("2023-05-04",.25,5.125),("2023-07-27",.25,5.375),("2024-09-19",-.5,4.875),
("2024-11-08",-.25,4.625),("2024-12-19",-.25,4.375),("2025-09-18",-.25,4.125),
("2025-10-30",-.25,3.875),("2025-12-11",-.25,3.625),("2026-09-17",.25,3.875)
]

def download(ticker):
    x=yf.download(ticker,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x=x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna()

def fed_series(index):
    e=pd.DataFrame(FED_EVENTS,columns=["date","change","target"]); e.date=pd.to_datetime(e.date)
    return pd.Series([float(e.loc[e.date<=d,"target"].iloc[-1]) if (e.date<=d).any() else np.nan for d in index],index=index)

def build():
    q=download("QQQ"); v=download("^VIX")[["close"]].rename(columns={"close":"vix"})
    x=q.join(v,how="left")
    x.vix=x.vix.ffill()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["overnight"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["intraday"]=(x.adj_close/x.adj_open-1).fillna(0)
    x["on3"]=(1+3*x.overnight).clip(lower=0)-1
    x["in3"]=(1+3*x.intraday).clip(lower=0)-1
    x["bh_daily"]=(1+x.on3)*(1+x.in3)-1
    x["bh_equity"]=INITIAL*(1+x.bh_daily).cumprod()
    x["dma"]=x.adj_close.rolling(DMA).mean()
    x["ret20"]=x.adj_close/x.adj_close.shift(20)-1
    x["ret60"]=x.adj_close/x.adj_close.shift(60)-1
    x["rv20"]=x.ret20 # placeholder overwritten below
    x["daily_ret"]=x.adj_close.pct_change()
    x["rv20"]=x.daily_ret.rolling(20).std()*np.sqrt(252)
    x["vix_chg20"]=x.vix/x.vix.shift(20)-1
    x["rv_chg20"]=x.rv20/x.rv20.shift(20)-1
    x["fed_target"]=fed_series(x.index)
    x["base_signal"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:DMA-1],"base_signal"]=0
    veto=(x.adj_close<x.dma)&(x.fed_target>RATE_THRESHOLD)&(x.ret60>=0)
    shock=(x.vix_chg20>=SHOCK_THRESHOLD)|(x.rv_chg20>=SHOCK_THRESHOLD)
    x["veto"]=veto
    x["shock"]=shock
    x["conditioned_signal"]=np.where(x.base_signal==1,1.0,np.where(veto,1.0,0.0))
    x["three_layer_signal"]=np.where(x.base_signal==1,1.0,np.where(veto&~shock,1.0,0.0))
    def equity(sig):
        w=sig.to_numpy(); prev=np.roll(w,1); prev[0]=0
        daily=(1+prev*x.on3.to_numpy())*(1+w*x.in3.to_numpy())-1
        eq=INITIAL*np.cumprod(1+daily); dd=eq/np.maximum.accumulate(eq)-1
        return eq,dd,daily
    for name,sig in [("base",x.base_signal),("conditioned",x.conditioned_signal),("three_layer",x.three_layer_signal)]:
        x[f"{name}_equity"],x[f"{name}_dd"],x[f"{name}_daily"]=equity(sig)
    return x

def window_metrics(z):
    years=(z.index[-1]-z.index[0]).days/365.2425
    out={"start":str(z.index[0].date()),"end":str(z.index[-1].date())}
    for n in ["base","conditioned","three_layer"]:
        daily=z[f"{n}_daily"].fillna(0).to_numpy()
        eq=INITIAL*np.cumprod(1+daily)
        dd=eq/np.maximum.accumulate(eq)-1
        out[f"{n}_final"]=float(eq[-1])
        out[f"{n}_cagr"]=float((eq[-1]/INITIAL)**(1/years)-1)
        out[f"{n}_dd"]=float(dd.min())
    return out

def stress_2020(x):
    z=x.loc["2020-01-01":"2020-12-31"].copy()
    veto=(z.adj_close<z.dma)&(z.ret60>=0)
    cond=np.where(z.base_signal==1,1.0,np.where(veto,1.0,0.0))
    three=np.where(z.base_signal==1,1.0,np.where(veto & ~z.shock,1.0,0.0))
    rows={}
    for name,sig in [("conditioned",cond),("three_layer",three)]:
        prev=np.roll(sig,1); prev[0]=0
        daily=(1+prev*z.on3.to_numpy())*(1+sig*z.in3.to_numpy())-1
        eq=INITIAL*np.cumprod(1+daily); dd=eq/np.maximum.accumulate(eq)-1
        rows[f"high_rate_{name}_2020_final"]=float(eq[-1])
        rows[f"high_rate_{name}_2020_max_dd"]=float(dd.min())
        rows[f"high_rate_{name}_mar06_signal"]=float(sig[np.where(z.index>=pd.Timestamp("2020-03-06"))[0][0]])
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True); x=build()
    x.to_csv(OUT/"tqqq_three_layer_shock_daily.csv")
    windows=[("full","1999-03-10","2026-10-05"),("dotcom","2000-01-01","2003-12-31"),("gfc","2008-01-01","2009-12-31"),("covid","2020-01-01","2020-12-31"),("inflation","2022-01-01","2022-12-31"),("post2010","2010-01-01","2026-10-05"),("modern2020plus","2020-01-01","2026-10-05")]
    rows=[]
    for n,a,b in windows:
        z=x.loc[a:b]
        if z.empty: continue
        r={"window":n,"start":str(z.index[0].date()),"end":str(z.index[-1].date())}
        r.update(window_metrics(z))
        r["veto_days"]=int(z.veto.sum()); r["shock_days"]=int(z.shock.sum()); r["veto_shock_overlap"]=int((z.veto&z.shock).sum())
        rows.append(r)
    pd.DataFrame(rows).to_csv(OUT/"tqqq_three_layer_shock_windows.csv",index=False)
    stress=pd.DataFrame([stress_2020(x)])
    stress.to_csv(OUT/"tqqq_three_layer_high_rate_covid_stress.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False)); print("\nSTRESS\n",stress.to_string(index=False))
    print("\nKEY COVID DAYS\n",x.loc["2020-03-05":"2020-03-11",["adj_close","dma","ret60","vix","vix_chg20","rv20","rv_chg20","fed_target","veto","shock","conditioned_signal","three_layer_signal"]].to_string())
if __name__=="__main__": main()
