"""Frozen macro-regime interpretation test for the QQQ 100-DMA exit.

No parameter optimization. At each below-100-DMA break, classify the economic
state using fixed, predeclared conditions and compare ordinary 100-DMA defense
against a macro-confirmed defense that exits only in dangerous regimes.

Signal is close-to-next-open, synthetic daily-reset 3x QQQ, $5,000, 0% cash.
"""
from pathlib import Path
import numpy as np, pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START="1999-03-10"; END="2026-10-05"; INITIAL=5000.0

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
("2025-10-30",-.25,3.875),("2025-12-11",-.25,3.625),("2026-09-17",.25,3.875)]

def fed_series(idx):
 e=pd.DataFrame(FED_EVENTS,columns=["date","change","target"]); e.date=pd.to_datetime(e.date)
 return pd.Series([float(e[e.date<=d].target.iloc[-1]) if (e.date<=d).any() else np.nan for d in idx],index=idx)

def dl(t):
 x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def main():
 q=dl("QQQ"); v=dl("^VIX")[["close"]].rename(columns={"close":"vix"})
 x=q.join(v,how="left"); x.vix=x.vix.ffill()
 x["adj_open"]=x.open*x.adj_close/x.close
 x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
 x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
 x["dma"]=x.adj_close.rolling(100).mean(); x["fed"]=fed_series(x.index)
 for n,s in {"dgs10":"DGS10","t3m":"DTB3","unrate":"UNRATE","cpi":"CPIAUCSL","baa":"BAA10YM","nfci":"NFCI"}.items():
  z=pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}",parse_dates=["observation_date"],na_values=["."])
  z=z.rename(columns={"observation_date":"date",s:n}).set_index("date")[n].astype(float)
  x[n]=z.reindex(x.index,method="ffill")
 x["cpi_yoy"]=x.cpi.pct_change(252); x["unrate6"]=x.unrate-x.unrate.shift(126)
 x["curve"]=x.dgs10-x.t3m; x["baa3"]=x.baa-x.baa.shift(63); x["nfci13"]=x.nfci-x.nfci.shift(63)
 x["vix20"]=x.vix/x.vix.shift(20)-1; x["fed6"]=x.fed-x.fed.shift(126)

 def state(r):
  if r.vix20>=1: return "acute_shock"
  if r.fed6>0 and r.curve<0: return "structural_tightening"
  if r.cpi_yoy>.04 and r.fed6>0: return "inflation_liquidity_tightening"
  if r.unrate6>.5 or r.baa3>.25 or r.nfci13>.25: return "economic_credit_deterioration"
  if r.fed6>0: return "monetary_tightening"
  return "normal_mixed"

 x["state"]=x.apply(state,axis=1)
 # Mandatory DMA exits remain unchanged. Macro may only veto re-entry.
 base=(x.adj_close>=x.dma).astype(float); base.iloc[:99]=0
 dangerous=x.state.isin(["acute_shock","structural_tightening","inflation_liquidity_tightening","economic_credit_deterioration"])
 macro_reentry=np.zeros(len(x),dtype=float)
 in_pos=False
 vetoes=[]
 for i in range(100,len(x)):
  if in_pos and x.adj_close.iloc[i] < x.dma.iloc[i]:
   in_pos=False
  elif (not in_pos) and x.adj_close.iloc[i] >= x.dma.iloc[i]:
   if not bool(dangerous.iloc[i]):
    in_pos=True
   else:
    vetoes.append((x.index[i],x.state.iloc[i],x.adj_close.iloc[i]/x.dma.iloc[i]-1))
  macro_reentry[i]=1.0 if in_pos else 0.0
 confirmed=np.where(x.adj_close>=x.dma,1.0,np.where(dangerous,0.0,1.0))

 def equity(sig):
  w=np.asarray(sig,float); prev=np.roll(w,1); prev[0]=0
  daily=(1+prev*x.on3.to_numpy())*(1+w*x.in3.to_numpy())-1
  eq=INITIAL*np.cumprod(1+daily); dd=eq/np.maximum.accumulate(eq)-1
  return eq,dd

 rows=[]
 for name,sig in [("baseline_100dma",base),("macro_confirmed_exit_only",confirmed),("macro_reentry",macro_reentry)]:
  eq,dd=equity(sig); rows.append({"strategy":name,"final":eq[-1],"cagr":(eq[-1]/INITIAL)**(365.2425/(x.index[-1]-x.index[0]).days)-1,"max_dd":dd.min(),"avg_exposure":sig.mean()})
  x[name+"_signal"]=sig; x[name+"_equity"]=eq
 pd.DataFrame(rows).to_csv(OUT/"tqqq_frozen_regime_strategy_comparison.csv",index=False)

 br=(x.adj_close<x.dma)&(x.adj_close.shift(1)>=x.dma)
 audit=x.loc[br,["state","fed","fed6","curve","cpi_yoy","unrate6","baa3","nfci13","vix20"]].copy()
 audit["baseline_exits"]=True; audit["macro_confirmed_exits"]=audit.state.isin(["acute_shock","structural_tightening","inflation_liquidity_tightening","economic_credit_deterioration"])
 audit["macro_reentry_veto"]=False
 for d,st,gap in vetoes:
  if d in audit.index: audit.loc[d,"macro_reentry_veto"]=True
 audit.to_csv(OUT/"tqqq_frozen_regime_break_audit.csv")
 pd.DataFrame(vetoes,columns=["date","state","dma_gap"]).to_csv(OUT/"tqqq_frozen_regime_reentry_vetoes.csv",index=False)
 print(pd.DataFrame(rows).to_string(index=False))
 print("\nBREAK AUDIT BY STATE")
 print(audit.groupby("state").agg(breaks=("baseline_exits","size"),exits=("macro_confirmed_exits","sum")).to_string())

if __name__=="__main__": main()
