"""Event-level attribution for the three-layer TQQQ architecture.

Rebuilds the frozen three-layer rule and measures:
- total terminal wealth lift: conditioned vs base
- total terminal wealth lift: three-layer vs conditioned
- one-day counterfactual terminal impact of each veto day
- one-day counterfactual impact of each shock-overlap day
No threshold optimization.
"""
from pathlib import Path
import numpy as np, pandas as pd
import yfinance as yf
from causal_execution import next_open_daily_returns, next_open_equity, next_open_cost_daily_returns

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START="1999-03-10"; END="2026-10-05"; INITIAL=5000.0
RATE_THRESHOLD=3.5; SHOCK_THRESHOLD=1.0
FED_EVENTS=[("1999-06-30",.25,5),("1999-08-24",.25,5.25),("1999-11-16",.25,5.5),("2000-02-02",.25,5.75),("2000-03-21",.25,6),("2000-05-16",.5,6.5),("2001-01-03",-.5,6),("2001-01-31",-.5,5.5),("2001-03-20",-.5,5),("2001-04-18",-.5,4.5),("2001-05-15",-.5,4),("2001-06-27",-.25,3.75),("2001-08-21",-.25,3.5),("2001-09-17",-.5,3),("2001-10-02",-.5,2.5),("2001-11-06",-.5,2),("2001-12-11",-.25,1.75),("2002-11-06",-.5,1.25),("2003-06-25",-.25,1),("2004-06-30",.25,1.25),("2004-08-10",.25,1.5),("2004-09-21",.25,1.75),("2004-11-10",.25,2),("2004-12-14",.25,2.25),("2005-02-02",.25,2.5),("2005-03-22",.25,2.75),("2005-05-03",.25,3),("2005-06-30",.25,3.25),("2005-08-09",.25,3.5),("2005-09-20",.25,3.75),("2005-11-01",.25,4),("2005-12-13",.25,4.25),("2006-01-31",.25,4.5),("2006-03-28",.25,4.75),("2006-05-10",.25,5),("2006-06-29",.25,5.25),("2007-09-18",-.5,4.75),("2007-10-31",-.25,4.5),("2007-12-11",-.25,4.25),("2008-01-22",-.75,3.5),("2008-01-30",-.5,3),("2008-03-18",-.75,2.25),("2008-04-30",-.25,2),("2008-10-08",-.5,1.5),("2008-10-29",-.5,1),("2008-12-16",-.75,.125),("2015-12-17",.25,.375),("2016-12-15",.25,.625),("2017-03-16",.25,.875),("2017-06-15",.25,1.125),("2017-12-14",.25,1.375),("2018-03-22",.25,1.625),("2018-06-14",.25,1.875),("2018-09-27",.25,2.125),("2018-12-20",.25,2.375),("2019-08-01",-.25,2.125),("2019-09-19",-.25,1.875),("2019-10-31",-.25,1.625),("2020-03-04",-.5,1.125),("2020-03-16",-1,.125),("2022-03-17",.25,.375),("2022-05-05",.5,.875),("2022-06-16",.75,1.625),("2022-07-28",.75,2.375),("2022-09-22",.75,3.125),("2022-11-03",.75,3.875),("2022-12-15",.5,4.375),("2023-02-02",.25,4.625),("2023-03-23",.25,4.875),("2023-05-04",.25,5.125),("2023-07-27",.25,5.375),("2024-09-19",-.5,4.875),("2024-11-08",-.25,4.625),("2024-12-19",-.25,4.375),("2025-09-18",-.25,4.125),("2025-10-30",-.25,3.875),("2025-12-11",-.25,3.625),("2026-09-17",.25,3.875)]

def dl(t):
 x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def fed_series(idx):
 e=pd.DataFrame(FED_EVENTS,columns=["date","change","target"]); e.date=pd.to_datetime(e.date)
 return pd.Series([float(e.loc[e.date<=d,"target"].iloc[-1]) if (e.date<=d).any() else np.nan for d in idx],index=idx)

def build():
 q=dl("QQQ"); v=dl("^VIX")[["close"]].rename(columns={"close":"vix"}); x=q.join(v,how="left"); x.vix=x.vix.ffill()
 x["adj_open"]=x.open*x.adj_close/x.close
 x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
 x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
 x["dma"]=x.adj_close.rolling(100).mean(); x["ret60"]=x.adj_close/x.adj_close.shift(60)-1
 x["daily_ret"]=x.adj_close.pct_change(); x["rv20"]=x.daily_ret.rolling(20).std()*np.sqrt(252)
 x["vix_chg20"]=x.vix/x.vix.shift(20)-1; x["rv_chg20"]=x.rv20/x.rv20.shift(20)-1; x["fed"]=fed_series(x.index)
 x["base"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:99],"base"]=0
 x["veto"]=(x.adj_close<x.dma)&(x.fed>RATE_THRESHOLD)&(x.ret60>=0)
 x["shock"]=(x.vix_chg20>=SHOCK_THRESHOLD)|(x.rv_chg20>=SHOCK_THRESHOLD)
 x["conditioned"]=np.where(x.base==1,1.0,np.where(x.veto,1.0,0.0))
 x["three"]=np.where(x.base==1,1.0,np.where(x.veto & ~x.shock,1.0,0.0))
 return x

def equity(x,sig):
 w=np.asarray(sig,float)
 return next_open_equity(w,x.on3,x.in3,INITIAL)

def one_day_impact(x, sig, idx):
 s=np.asarray(sig,float).copy(); s[idx]=1-s[idx]
 return equity(x,s)[-1]

def main():
 x=build(); base=equity(x,x.base); cond=equity(x,x.conditioned); three=equity(x,x.three)
 rows=[{"comparison":"conditioned_minus_base","base_final":base[-1],"comparison_final":cond[-1],"terminal_delta":cond[-1]-base[-1],"terminal_ratio":cond[-1]/base[-1]},
       {"comparison":"three_layer_minus_conditioned","base_final":cond[-1],"comparison_final":three[-1],"terminal_delta":three[-1]-cond[-1],"terminal_ratio":three[-1]/cond[-1]}]
 pd.DataFrame(rows).to_csv(OUT/"tqqq_three_layer_attribution_summary.csv",index=False)
 events=[]
 for i in np.flatnonzero(x.veto.to_numpy()):
  if x.shock.iloc[i]: continue
  cf=one_day_impact(x,x.three,i)
  events.append({"date":x.index[i].date(),"type":"veto_without_shock","vix_chg20":x.vix_chg20.iloc[i],"rv_chg20":x.rv_chg20.iloc[i],"terminal_cf_without_event":cf,"event_terminal_delta":cf-three[-1]})
 for i in np.flatnonzero((x.veto&x.shock).to_numpy()):
  cf=one_day_impact(x,x.three,i)
  events.append({"date":x.index[i].date(),"type":"veto_shock_overlap","vix_chg20":x.vix_chg20.iloc[i],"rv_chg20":x.rv_chg20.iloc[i],"terminal_cf_without_event":cf,"event_terminal_delta":cf-three[-1]})
 ev=pd.DataFrame(events).sort_values("date")
 ev["year"]=pd.to_datetime(ev["date"]).dt.year
 ev["era"]=pd.cut(ev["year"],bins=[-np.inf,2003,2009,2019,2021,2026],labels=["dotcom","gfc","pre_covid_2010s","covid","post_covid"],right=True)
 ev.to_csv(OUT/"tqqq_three_layer_event_attribution.csv",index=False)
 print(pd.DataFrame(rows).to_string(index=False))
 print("\nTOP POSITIVE EVENT IMPACTS")
 print(ev.sort_values("event_terminal_delta").tail(10).to_string(index=False))
 print("\nTOP NEGATIVE EVENT IMPACTS")
 print(ev.sort_values("event_terminal_delta").head(10).to_string(index=False))
 print("\nEVENT COUNTS",len(ev),"veto-only",int((ev.type=="veto_without_shock").sum()),"overlap",int((ev.type=="veto_shock_overlap").sum()))
 pos=ev.loc[ev.event_terminal_delta>0,"event_terminal_delta"].sum()
 neg=ev.loc[ev.event_terminal_delta<0,"event_terminal_delta"].sum()
 print("EVENT IMPACT SUMS positive",float(pos),"negative",float(neg),"net",float(pos+neg))
 print("\nEVENT ATTRIBUTION BY ERA")
 print(ev.groupby("era",observed=True)["event_terminal_delta"].agg(["count","sum","mean","min","max"]).to_string())
 print("\nTOP 5 POSITIVE SHARE",float(ev.nlargest(5,"event_terminal_delta").event_terminal_delta.sum()/pos) if pos else 0.0)
 print("TOP 5 NEGATIVE ABS SHARE",float(ev.nsmallest(5,"event_terminal_delta").event_terminal_delta.abs().sum()/abs(neg)) if neg else 0.0)
 overlap=ev[ev.type=="veto_shock_overlap"]
 print("\nSHOCK-OVERLAP EVENTS")
 print(overlap[["date","vix_chg20","rv_chg20","event_terminal_delta"]].to_string(index=False))
 print("SHOCK-OVERLAP IMPACT SUM",float(overlap.event_terminal_delta.sum()))
if __name__=="__main__": main()
