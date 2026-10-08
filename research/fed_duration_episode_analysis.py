"""Frozen Fed-tightening x recovery-duration episode analysis.

No TQQQ backtest and no parameter optimization.
Frozen Fed state: >=50 bp increase in target over prior 63 calendar days.
Market event definition remains: first >=4.5% daily NDX shock, then first +10%
from the post-shock low.

This analysis adds only a predeclared descriptive dimension:
shock-to-recovery duration buckets:
  fast <= 10 trading days
  medium 11-30
  slow > 30
and low-to-recovery buckets:
  fast <= 5, medium 6-20, slow >20.

It also constructs contiguous "stress episodes" by merging events whose next
shock occurs before the prior event's recovery plus 20 trading days. This is
descriptive and not used to optimize a trading rule.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import requests, io, yfinance as yf

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
SHOCK=-.045; REC=.10; FED_DAYS=63; FED_BP=50
START="1985-01-01"; END="2026-10-09"

def get_ndx():
 x=yf.download("^NDX",start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None); return x["Close"].astype(float).sort_index()

def get_fed():
 u="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTAR,DFEDTARL,DFEDTARU"
 z=pd.read_csv(io.StringIO(requests.get(u,timeout=30).text)); z.observation_date=pd.to_datetime(z.observation_date)
 for c in ["DFEDTAR","DFEDTARL","DFEDTARU"]: z[c]=pd.to_numeric(z[c],errors="coerce")
 z["target"]=z.DFEDTAR; m=z.DFEDTARL.notna()&z.DFEDTARU.notna()
 z.loc[m,"target"]=(z.loc[m,"DFEDTARL"]+z.loc[m,"DFEDTARU"])/2
 return z.set_index("observation_date").target.dropna()

def event_ledger(px,fed):
 ret=px.pct_change().fillna(0).to_numpy(); a=px.to_numpy()
 armed=False; low=np.nan; li=si=None; rows=[]
 for i in range(1,len(px)):
  if not armed and ret[i]<=SHOCK: armed=True; low=a[i]; li=si=i
  if armed:
   if a[i]<low: low=a[i]; li=i
   if a[i]/low-1>=REC:
    d=px.index[i]; lowd=px.index[li]; sd=px.index[si]
    f=fed.loc[:d]
    cur=float(f.iloc[-1]); p=f.loc[:d-pd.Timedelta(days=FED_DAYS)]
    old=float(p.iloc[-1]) if len(p) else np.nan
    row={"shock_date":sd,"low_date":lowd,"recovery_date":d,
         "shock_to_recovery_td":i-si,"low_to_recovery_td":i-li,
         "fed_change_63d_bp":(cur-old)*100,
         "fed_aggressive":int((cur-old)*100>=FED_BP),
         "shock_to_recovery_bucket":("fast" if i-si<=10 else "medium" if i-si<=30 else "slow"),
         "low_to_recovery_bucket":("fast" if i-li<=5 else "medium" if i-li<=20 else "slow")}
    for n in [20,60,120,252]:
     fwd=px.loc[d:].iloc[:n+1]
     row[f"fwd_{n}d"]=float(fwd.iloc[-1]/fwd.iloc[0]-1) if len(fwd)>1 else np.nan
    rows.append(row); armed=False; low=np.nan; li=si=None
 return pd.DataFrame(rows)

def episodes(ev, px):
 ev=ev.sort_values("shock_date").copy()
 # A new shock within 20 ACTUAL NDX trading sessions after the prior
 # recovery is part of the same stress episode. This avoids a calendar-day
 # approximation.
 pos={d:i for i,d in enumerate(px.index)}
 ep=[]; current=-1; prev_recovery_i=None
 for _,r in ev.iterrows():
  shock_i=pos[r.shock_date]
  if prev_recovery_i is None or shock_i-prev_recovery_i>20:
   current+=1
  ep.append(current)
  prev_recovery_i=pos[r.recovery_date]
 ev["episode_id"]=ep
 return ev

if __name__=="__main__":
 OUT.mkdir(parents=True,exist_ok=True); px=get_ndx(); fed=get_fed()
 ev=event_ledger(px,fed); ev=episodes(ev,px)
 ev["fed_duration_cell"]=ev.fed_aggressive.astype(str)+"_"+ev.shock_to_recovery_bucket
 ev.to_csv(OUT/"fed_duration_event_ledger.csv",index=False)

 cell=ev.groupby(["fed_aggressive","shock_to_recovery_bucket"],as_index=False).agg(
  events=("recovery_date","size"),median_fwd60=("fwd_60d","median"),
  median_fwd120=("fwd_120d","median"),median_fwd252=("fwd_252d","median"),
  mean_fwd120=("fwd_120d","mean"))
 cell.to_csv(OUT/"fed_duration_matrix.csv",index=False)

 ep=ev.groupby("episode_id").agg(start=("shock_date","min"),end=("recovery_date","max"),
     events=("recovery_date","size"),fed_aggressive_events=("fed_aggressive","sum"),
     max_shock_to_recovery=("shock_to_recovery_td","max"),
     max_low_to_recovery=("low_to_recovery_td","max")).reset_index()
 ep.to_csv(OUT/"fed_duration_episodes.csv",index=False)

 print("\nFROZEN FED RULE: >=50bp / 63d")
 print("\nEVENT LEDGER"); print(ev.to_string(index=False))
 print("\n2x3 MATRIX"); print(cell.to_string(index=False))
 print("\nEPISODES"); print(ep.to_string(index=False))
