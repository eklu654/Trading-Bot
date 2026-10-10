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
import hashlib, json, platform
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
         "fed_63d_bp":bp,"aggressive":bp>=FED_BP,"prolonged":(i-si)>DUR,
         "recovered":True,"right_censored":False,"episode_end_date":d,"censor_date":pd.NaT}
    for n in [60,120,252]:
     q=px.loc[d:].iloc[:n+1]; row[f"fwd_{n}d"]=float(q.iloc[-1]/q.iloc[0]-1) if len(q)==n+1 else np.nan
    # Diagnostic only: whether the target was still higher at recovery than at shock.
    # This is NOT yet a trading rule or selection criterion.
    row["tightening_persisted_to_recovery"]=row["fed_change_shock_to_recovery_bp"]>0
    row["candidate_persistent_tightening"]=row["aggressive"] and row["tightening_persisted_to_recovery"]
    row["candidate_persistent_tightening_slow"]=row["candidate_persistent_tightening"] and row["prolonged"]
    row["warning_rule"]=row["aggressive"] and row["prolonged"]
    row["retrospective_warning_label"]=row["warning_rule"]
    rows.append(row); armed=False;low=np.nan;li=si=None
 # Preserve an unresolved terminal episode instead of silently dropping it.
 if armed:
  d=px.index[-1]; f=fr.loc[:d]; cur=float(f.iloc[-1]) if len(f) else np.nan
  p=f.loc[:d-pd.Timedelta(days=FED_DAYS)]; old=float(p.iloc[-1]) if len(p) else np.nan
  fs=fr.loc[:px.index[si]]; shock_rate=float(fs.iloc[-1]) if len(fs) else np.nan
  rows.append({"shock_date":px.index[si],"low_date":px.index[li],"recovery_date":pd.NaT,
   "shock_to_recovery_td":np.nan,"low_to_recovery_td":np.nan,"fed_target_at_shock":shock_rate,
   "fed_target_at_recovery":np.nan,"fed_change_shock_to_recovery_bp":np.nan,
   "fed_63d_bp":(cur-old)*100 if np.isfinite(cur) and np.isfinite(old) else np.nan,
   "aggressive":bool(np.isfinite(cur) and np.isfinite(old) and (cur-old)*100>=FED_BP),
   "prolonged":False,"tightening_persisted_to_recovery":False,"candidate_persistent_tightening":False,
   "candidate_persistent_tightening_slow":False,"warning_rule":False,"recovered":False,
   "right_censored":True,"episode_end_date":d,"censor_date":d,"retrospective_warning_label":False,
   "tightening_persisted_to_episode_end":bool(np.isfinite(cur) and np.isfinite(shock_rate) and cur>shock_rate),
   **{f"fwd_{n}d":np.nan for n in [60,120,252]}})
 return pd.DataFrame(rows)
def era(d):
 if d<pd.Timestamp("2000-01-01"): return "1985-1999"
 if d<pd.Timestamp("2008-01-01"): return "2000-2007"
 if d<pd.Timestamp("2020-01-01"): return "2008-2019"
 return "2020-2026"
if __name__=="__main__":
 OUT.mkdir(parents=True,exist_ok=True); px=market(); fr=fed(); e=ledger(px,fr); e["era"]=e.episode_end_date.map(era)
 e["outcome_120"]=np.where(e.fwd_120d.isna(),"censored_horizon",np.where(e.fwd_120d<0,"negative","nonnegative"))
 e.to_csv(OUT/"fed_chronological_frozen_event_ledger.csv",index=False,date_format="%Y-%m-%d")
 done=e[e.recovered].copy(); s=done.groupby(["era","retrospective_warning_label"],as_index=False).agg(events=("recovery_date","size"),median_fwd120=("fwd_120d","median"),median_duration=("shock_to_recovery_td","median"),complete_120d_horizons=("fwd_120d","count"))
 s["negative_share_120d"]=s.apply(lambda x: np.nan if x.events==0 else (done.loc[(done.era==x.era)&(done.retrospective_warning_label==x.retrospective_warning_label),"fwd_120d"]<0).mean(),axis=1)
 s.to_csv(OUT/"fed_chronological_frozen_summary.csv",index=False)
 print("FROZEN RULE: aggressive >=50bp/63d AND shock-to-+10% >30 trading days")
 print("\nALL EVENTS"); print(e.to_string(index=False))
 print("\nSUMMARY"); print(s.to_string(index=False))
 print("\nCURRENT FROZEN WARNING-HIT EVENTS"); print(e[e.retrospective_warning_label].to_string(index=False))
 print("\nEXPLORATORY PERSISTENT-TIGHTENING CANDIDATE (NOT FROZEN)"); print(e[e.candidate_persistent_tightening].to_string(index=False))
 print("\nEXPLORATORY CANDIDATE SUMMARY"); print(e.groupby("candidate_persistent_tightening").agg(events=("recovery_date","size"),negative_120d=("fwd_120d",lambda x:(x<0).sum()),median_fwd120=("fwd_120d","median"),median_fwd252=("fwd_252d","median")).to_string())
