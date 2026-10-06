"""Descriptive pre-exit signatures for frozen 100-DMA exits.

This is mechanism research, not parameter optimization. It compares the
market immediately before each 100-DMA break using underlying QQQ data:
momentum, DMA geometry, realized-volatility acceleration, raw overnight vs
intraday deterioration, VIX, Treasury curve, and Fed state.
"""
from __future__ import annotations
from pathlib import Path
from io import StringIO
from urllib.request import urlopen
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START="1999-03-10"; END="2026-10-04"; DMA=100
FED_EVENTS=[("1999-06-30",.25,5),("1999-08-24",.25,5.25),("1999-11-16",.25,5.5),("2000-02-02",.25,5.75),("2000-03-21",.25,6),("2000-05-16",.5,6.5),("2001-01-03",-0.5,6),("2001-01-31",-0.5,5.5),("2001-03-20",-0.5,5),("2001-04-18",-0.5,4.5),("2001-05-15",-0.5,4),("2001-06-27",-0.25,3.75),("2001-08-21",-0.25,3.5),("2001-09-17",-0.5,3),("2001-10-02",-0.5,2.5),("2001-11-06",-0.5,2),("2001-12-11",-0.25,1.75),("2002-11-06",-0.5,1.25),("2003-06-25",-0.25,1),("2004-06-30",.25,1.25),("2004-08-10",.25,1.5),("2004-09-21",.25,1.75),("2004-11-10",.25,2),("2004-12-14",.25,2.25),("2005-02-02",.25,2.5),("2005-03-22",.25,2.75),("2005-05-03",.25,3),("2005-06-30",.25,3.25),("2005-08-09",.25,3.5),("2005-09-20",.25,3.75),("2005-11-01",.25,4),("2005-12-13",.25,4.25),("2006-01-31",.25,4.5),("2006-03-28",.25,4.75),("2006-05-10",.25,5),("2006-06-29",.25,5.25),("2007-09-18",-0.5,4.75),("2007-10-31",-0.25,4.5),("2007-12-11",-0.25,4.25),("2008-01-22",-0.75,3.5),("2008-01-30",-0.5,3),("2008-03-18",-0.75,2.25),("2008-04-30",-0.25,2),("2008-10-08",-0.5,1.5),("2008-10-29",-0.5,1),("2008-12-16",-0.75,.125),("2015-12-17",.25,.375),("2016-12-15",.25,.625),("2017-03-16",.25,.875),("2017-06-15",.25,1.125),("2017-12-14",.25,1.375),("2018-03-22",.25,1.625),("2018-06-14",.25,1.875),("2018-09-27",.25,2.125),("2018-12-20",.25,2.375),("2019-08-01",-0.25,2.125),("2019-09-19",-0.25,1.875),("2019-10-31",-0.25,1.625),("2020-03-04",-0.5,1.125),("2020-03-16",-1,.125),("2022-03-17",.25,.375),("2022-05-05",.5,.875),("2022-06-16",.75,1.625),("2022-07-28",.75,2.375),("2022-09-22",.75,3.125),("2022-11-03",.75,3.875),("2022-12-15",.5,4.375),("2023-02-02",.25,4.625),("2023-03-23",.25,4.875),("2023-05-04",.25,5.125),("2023-07-27",.25,5.375),("2024-09-19",-0.5,4.875),("2024-11-08",-0.25,4.625),("2024-12-19",-0.25,4.375),("2025-09-18",-0.25,4.125),("2025-10-30",-0.25,3.875),("2025-12-11",-0.25,3.625),("2026-09-17",.25,3.875)]

def download(ticker):
    x=yf.download(ticker,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x=x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}); x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def fed_state(idx):
    e=pd.DataFrame(FED_EVENTS,columns=["date","change","target"]); e.date=pd.to_datetime(e.date); out=[]
    for d in idx:
        p=e[e.date<=d]
        if p.empty: out.append((d,np.nan,"unknown",np.nan,np.nan)); continue
        z=p.iloc[-1]; s=np.sign(p.change.to_numpy()); cur=s[-1]; k=len(s)-1
        while k>0 and s[k-1]==cur:k-=1
        c=p.iloc[k:]; out.append((d,float(z.target),"tightening" if cur>0 else "easing",float(c.change.sum()),int((d-z.date).days)))
    return pd.DataFrame(out,columns=["Date","fed_target","fed_direction","fed_cycle_change","days_since_fed_move"]).set_index("Date")

def fred(name):
    with urlopen(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={name}",timeout=30) as r:
        z=pd.read_csv(StringIO(r.read().decode()),parse_dates=["observation_date"]).set_index("observation_date")
    return pd.to_numeric(z[name],errors="coerce").rename(name)

def build(x,vix):
    x=x.dropna(subset=["open","close","adj_close"]).copy(); x["adj_open"]=x.open*x.adj_close/x.close
    x["overnight"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0); x["intraday"]=(x.adj_close/x.adj_open-1).fillna(0)
    x["on5"]=x.overnight.rolling(5).sum(); x["intra5"]=x.intraday.rolling(5).sum()
    x["dma"]=x.adj_close.rolling(DMA).mean(); x["weight"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:DMA-1],"weight"]=0
    w=x.weight.to_numpy(); pw=np.roll(w,1); pw[0]=0; on3=(1+3*x.overnight).clip(lower=0)-1; in3=(1+3*x.intraday).clip(lower=0)-1
    daily=(1+pw*on3.to_numpy())*(1+w*in3.to_numpy())-1; x["equity"]=5000*np.cumprod(1+daily); x["bh_equity"]=5000*np.cumprod((1+on3)*(1+in3)); x["drawdown"]=x.equity/x.equity.cummax()-1
    x["dma_gap"]=x.adj_close/x.dma-1; x["dma_slope20"]=x.dma/x.dma.shift(20)-1
    for n in (5,20,60): x[f"ret{n}"]=x.adj_close/x.adj_close.shift(n)-1
    x["vol20"]=x.adj_close.pct_change().rolling(20).std()*np.sqrt(252); x["vol_change20"]=x.vol20/x.vol20.shift(20)-1
    x["vix"]=vix.reindex(x.index).ffill(); x["vix_change5"]=x.vix/x.vix.shift(5)-1; x["vix_change20"]=x.vix/x.vix.shift(20)-1
    curve=pd.concat([fred("DGS10"),fred("DGS2")],axis=1); curve["curve"]=curve.DGS10-curve.DGS2; curve["curve_change20"]=curve.curve-curve.curve.shift(20)
    return x.join(fed_state(x.index)).join(curve[["curve","curve_change20"]])

def era(y):
    if 2000<=y<=2003 or 2008<=y<=2009:return "A_structural_bear_candidate"
    if y==2020:return "B_fast_shock_candidate"
    if y==2022:return "C_inflation_liquidity_candidate"
    return "D_or_normal_candidate"

def main():
    OUT.mkdir(parents=True,exist_ok=True); x=build(download("QQQ"),download("^VIX")["adj_close"].rename("vix"))
    exits=x.index[(x.weight==0)&(x.weight.shift(1)==1)]; rows=[]
    for d in exits:
        i=x.index.get_loc(d); j=i+1
        while j<len(x) and x.iloc[j].weight==0:j+=1
        if j>=len(x):continue
        seg=x.bh_equity.iloc[i:j+1]; base=float(seg.iloc[0])
        rows.append({"exit_date":d.date().isoformat(),"reentry_date":x.index[j].date().isoformat(),"era_candidate":era(d.year),"flat_days":j-i-1,
          "bh_return_to_reentry":float(seg.iloc[-1]/base-1),"bh_worst_return":float((seg/base-1).min()),
          "ret5":float(x.ret5.iloc[i]),"ret20":float(x.ret20.iloc[i]),"ret60":float(x.ret60.iloc[i]),"dma_gap":float(x.dma_gap.iloc[i]),
          "dma_slope20":float(x.dma_slope20.iloc[i]),"vol20":float(x.vol20.iloc[i]),"vol_change20":float(x.vol_change20.iloc[i]),
          "qqq_overnight5":float(x.on5.iloc[i]),"qqq_intraday5":float(x.intra5.iloc[i]),"vix":float(x.vix.iloc[i]),
          "vix_change5":float(x.vix_change5.iloc[i]),"vix_change20":float(x.vix_change20.iloc[i]),"curve_2s10s":float(x.curve.iloc[i]),
          "curve_change20":float(x.curve_change20.iloc[i]),"fed_target":float(x.fed_target.iloc[i]),"fed_direction":x.fed_direction.iloc[i],
          "fed_cycle_change":float(x.fed_cycle_change.iloc[i]),"days_since_fed_move":float(x.days_since_fed_move.iloc[i])})
    ep=pd.DataFrame(rows); ep["persistent_20d"]=ep.flat_days>=20; ep["severe_50pct"]=ep.bh_worst_return<=-.5
    ep.to_csv(OUT/"tqqq_100dma_exit_signatures.csv",index=False)
    summary=ep.groupby("era_candidate").agg(episodes=("exit_date","size"),persistent_rate=("persistent_20d","mean"),severe_rate=("severe_50pct","mean"),
      median_ret5=("ret5","median"),median_ret20=("ret20","median"),median_ret60=("ret60","median"),median_dma_gap=("dma_gap","median"),
      median_dma_slope20=("dma_slope20","median"),median_vol20=("vol20","median"),median_vol_change20=("vol_change20","median"),
      median_overnight5=("qqq_overnight5","median"),median_intraday5=("qqq_intraday5","median"),median_vix=("vix","median"),
      median_vix_change20=("vix_change20","median"),median_curve=("curve_2s10s","median"),median_fed_cycle_change=("fed_cycle_change","median"))
    summary.to_csv(OUT/"tqqq_100dma_exit_signature_summary.csv"); print("\nEXIT SIGNATURES\n",ep.to_string(index=False)); print("\nERA SUMMARY\n",summary.to_string()); print("\nMAJOR EPISODES\n",ep.sort_values("bh_worst_return").head(20).to_string(index=False))
if __name__=="__main__": main()
