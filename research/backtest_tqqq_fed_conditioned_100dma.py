"""Daily backtest of the exact Fed-conditioned 100-DMA exit rule.

Baseline: QQQ adjusted close >= 100-DMA -> 100% synthetic TQQQ; otherwise 0%.
Conditioned: below 100-DMA, remain invested only when Fed target > 3.5%
and QQQ 60-day return >= 0%. Signal is close-to-next-open.
No transaction costs; 0% cash yield.
"""

from __future__ import annotations
from io import StringIO
from pathlib import Path
from urllib.request import urlopen
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
START = "1999-03-10"
END = "2026-10-05"
INITIAL = 5000.0
DMA = 100
RATE_THRESHOLD = 3.5

FED_EVENTS = [
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

def download_qqq():
    x = yf.download("QQQ", start=START, end=END, auto_adjust=False, progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x = x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index().dropna(subset=["open","close","adj_close"])

def fed_series(index):
    e = pd.DataFrame(FED_EVENTS, columns=["date","change","target"])
    e["date"] = pd.to_datetime(e["date"])
    vals = []
    for d in index:
        p = e[e.date <= d]
        vals.append(float(p.iloc[-1].target) if not p.empty else np.nan)
    return pd.Series(vals, index=index, name="fed_target")

def build(x):
    x = x.copy()
    x["adj_open"] = x.open * x.adj_close / x.close
    overnight = (x.adj_open / x.adj_close.shift(1) - 1).fillna(0)
    intraday = (x.adj_close / x.adj_open - 1).fillna(0)
    x["on3"] = (1 + 3*overnight).clip(lower=0) - 1
    x["in3"] = (1 + 3*intraday).clip(lower=0) - 1
    x["bh_daily"] = (1+x.on3)*(1+x.in3)-1
    x["bh_equity"] = INITIAL*(1+x.bh_daily).cumprod()
    x["dma"] = x.adj_close.rolling(DMA).mean()
    x["ret60"] = x.adj_close / x.adj_close.shift(60) - 1
    x["fed_target"] = fed_series(x.index)
    x["base_signal"] = (x.adj_close >= x.dma).astype(float)
    x.loc[x.index[:DMA-1], "base_signal"] = 0
    veto = (x.adj_close < x.dma) & (x.fed_target > RATE_THRESHOLD) & (x.ret60 >= 0)
    x["conditioned_signal"] = np.where(x.base_signal == 1, 1.0, np.where(veto, 1.0, 0.0))

    def equity(signal):
        w = signal.to_numpy()
        prev = np.roll(w, 1)
        prev[0] = 0
        daily = (1+prev*x.on3.to_numpy())*(1+w*x.in3.to_numpy())-1
        eq = INITIAL*np.cumprod(1+daily)
        dd = eq/np.maximum.accumulate(eq)-1
        return eq, dd, daily

    x["base_equity"], x["base_drawdown"], x["base_daily"] = equity(x.base_signal)
    x["conditioned_equity"], x["conditioned_drawdown"], x["conditioned_daily"] = equity(x.conditioned_signal)
    x["veto_active"] = veto
    return x

def episodes(x, signal_col):
    s = x[signal_col]
    exits = x.index[(s==0)&(s.shift(1)==1)]
    rows=[]
    for d in exits:
        i=x.index.get_loc(d); j=i+1
        while j<len(x) and x.iloc[j][signal_col]==0: j+=1
        if j>=len(x): continue
        seg=x.bh_equity.iloc[i:j+1]; base=float(seg.iloc[0])
        rows.append({
            "exit_date":d.date().isoformat(),
            "reentry_date":x.index[j].date().isoformat(),
            "flat_days":j-i-1,
            "bh_return_to_reentry":float(seg.iloc[-1]/base-1),
            "bh_worst_return":float((seg/base-1).min()),
            "fed_target":float(x.fed_target.iloc[i]),
            "ret60":float(x.ret60.iloc[i])
        })
    return pd.DataFrame(rows)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x = build(download_qqq())
    x.to_csv(OUT/"tqqq_fed_conditioned_100dma_daily.csv")
    base_ep = episodes(x, "base_signal")
    cond_ep = episodes(x, "conditioned_signal")
    base_ep.to_csv(OUT/"tqqq_fed_conditioned_100dma_baseline_episodes.csv", index=False)
    cond_ep.to_csv(OUT/"tqqq_fed_conditioned_100dma_conditioned_episodes.csv", index=False)

    final_base=float(x.base_equity.iloc[-1])
    final_cond=float(x.conditioned_equity.iloc[-1])
    years=(x.index[-1]-x.index[0]).days/365.2425
    print("\\nFULL PERIOD")
    print("start={} end={} years={:.3f}".format(x.index[0].date(), x.index[-1].date(), years))
    print("baseline_final={:,.2f}".format(final_base))
    print("conditioned_final={:,.2f}".format(final_cond))
    print("baseline_cagr={:.6%}".format((final_base/INITIAL)**(1/years)-1))
    print("conditioned_cagr={:.6%}".format((final_cond/INITIAL)**(1/years)-1))
    print("baseline_max_dd={:.6%}".format(x.base_drawdown.min()))
    print("conditioned_max_dd={:.6%}".format(x.conditioned_drawdown.min()))
    print("baseline_avg_exposure={:.6%}".format(x.base_signal.mean()))
    print("conditioned_avg_exposure={:.6%}".format(x.conditioned_signal.mean()))
    print("veto_days={}".format(int(x.veto_active.sum())))

    windows=[
        ("dotcom_2000_2003","2000-01-01","2003-12-31"),
        ("gfc_2008_2009","2008-01-01","2009-12-31"),
        ("covid_2020","2020-01-01","2020-12-31"),
        ("inflation_2022","2022-01-01","2022-12-31"),
        ("post2010","2010-01-01","2026-10-05")
    ]
    rows=[]
    for name,a,b in windows:
        z=x.loc[a:b]
        if z.empty: continue
        rows.append({
            "window":name,
            "baseline_return":float(z.base_equity.iloc[-1]/z.base_equity.iloc[0]-1),
            "conditioned_return":float(z.conditioned_equity.iloc[-1]/z.conditioned_equity.iloc[0]-1),
            "baseline_min_dd":float(z.base_drawdown.min()),
            "conditioned_min_dd":float(z.conditioned_drawdown.min()),
            "veto_days":int(z.veto_active.sum())
        })
    crisis=pd.DataFrame(rows)
    crisis.to_csv(OUT/"tqqq_fed_conditioned_100dma_crisis_comparison.csv",index=False)
    print("\\nCRISIS WINDOWS")
    print(crisis.to_string(index=False))
    print("\\nVETO EVENTS")
    print(x.loc[x.veto_active, ["adj_close","dma","ret60","fed_target"]].to_string())

if __name__=="__main__":
    main()
