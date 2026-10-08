"""Chronological, frozen validation of the Fed x market-response hypothesis.

FROZEN before this run:
  Fed aggressive = >=50 bp target-rate increase over prior 63 calendar days.
  Prolonged recovery = >30 NDX trading sessions from shock to first +10%.
  Structural-warning cell = both conditions true.

No thresholds are selected from this script. It only evaluates the already-frozen
rule across chronological eras and reports every event, including counterexamples.

Important: this is a diagnostic regime test, NOT a TQQQ trading backtest.
"""
from pathlib import Path
import io, requests, numpy as np, pandas as pd, yfinance as yf
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START="1985-01-01"; END="2026-10-09"; SHOCK=-.045; REC=.10; FED_DAYS=63; FED_BP=50; DUR=30

def market():
 x=yf.download("^NDX",start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.Close.astype(float).sort_index()
def fed():
 u="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTAR,DFEDTARL,DFEDTARU"
 z=pd.read_csv(io.StringIO(requests.get(u,timeout=30).text)); z.observation_date=pd.to_datetime(z.observation_date)
 for c in ["DFEDTAR","DFEDTARL","DFEDTARU"]: z[c]=pd.to_numeric(z[c],errors="coerce")
 z["target"]=z.DFEDTAR; m=z.DFEDTARL.notna()&z.DFEDTARU.notna()
 z.loc[m,"target"]=(z.loc[m,"DFEDTARL"]+z.loc[m,"DFEDTARU"])/2
 return z.set_index("observation_date").target.dropna()
def ledger(px,fr):
 r=px.pct_change().fillna(0).to_numpy(); a=px.to_numpy(); armed=False; low=np.nan;li=si=None; rows=[]
 for i in range(1,len(px)):
  if not armed and r[i]<=SHOCK: armed=True; low=a[i];li=si=i
  if armed:
   if a[i]<low: low=a[i];li=i
   if a[i]/low-1>=REC:
    d=px.index[i]; f=fr.loc[:d]; cur=float(f.iloc[-1]); p=f.loc[:d-pd.Timedelta(days=FED_DAYS)]
    old=float(p.iloc[-1]) if len(p) else np.nan; bp=(cur-old)*100
    fs=fr.loc[:px.index[si]]; shock_rate=float(fs.iloc[-1])
    row={"shock_date":px.index[si],"low_date":px.index[li],"recovery_date":d,
         "shock_to_recovery_td":i-si,"low_to_recovery_td":i-li,
         "fed_target_at_shock":shock_rate,"fed_target_at_recovery":cur,
         "fed_change_shock_to_recovery_bp":(cur-shock_rate)*100,
         "fed_63d_bp":bp,"aggressive":bp>=FED_BP,"prolonged":(i-si)>DUR}
    for n in [60,120,252]:
     q=px.loc[d:].iloc[:n+1]; row[f"fwd_{n}d"]=float(q.iloc[-1]/q.iloc[0]-1) if len(q)>1 else np.nan
    # Diagnostic only: whether the target was still higher at recovery than at shock.
    # This is NOT yet a trading rule or selection criterion.
    row["tightening_persisted_to_recovery"]=row["fed_change_shock_to_recovery_bp"]>0
    row["warning_rule"]=row["aggressive"] and row["prolonged"]
    rows.append(row); armed=False;low=np.nan;li=si=None
 return pd.DataFrame(rows)
def era(d):
 if d<pd.Timestamp("2000-01-01"): return "1985-1999"
 if d<pd.Timestamp("2008-01-01"): return "2000-2007"
 if d<pd.Timestamp("2020-01-01"): return "2008-2019"
 return "2020-2026"
if __name__=="__main__":
 OUT.mkdir(parents=True,exist_ok=True); e=ledger(market(),fed()); e["era"]=e.recovery_date.map(era)
 e["outcome_120"]=np.where(e.fwd_120d<0,"negative","nonnegative")
 e.to_csv(OUT/"fed_chronological_frozen_event_ledger.csv",index=False)
 s=e.groupby(["era","warning_rule"],as_index=False).agg(events=("recovery_date","size"),median_fwd120=("fwd_120d","median"),median_duration=("shock_to_recovery_td","median"))
 s["negative_share_120d"]=s.apply(lambda x: np.nan if x.events==0 else (e.loc[(e.era==x.era)&(e.warning_rule==x.warning_rule),"fwd_120d"]<0).mean(),axis=1)
 s.to_csv(OUT/"fed_chronological_frozen_summary.csv",index=False)
 print("FROZEN RULE: aggressive >=50bp/63d AND shock-to-+10% >30 trading days")
 print("\nALL EVENTS"); print(e.to_string(index=False))
 print("\nSUMMARY"); print(s.to_string(index=False))
 print("\nRULE-HIT EVENTS"); print(e[e.warning_rule].to_string(index=False))
