"""Cross-proxy robustness: frozen Fed timing rule on NASDAQ Composite, 1971-1984.

Uses DFF (effective federal funds rate), not the target-rate series, because the target series is not populated consistently for this early window. This is a separate robustness check, not comparable to the main target-rate test.

This is deliberately separate from the NDX ledger because NASDAQ Composite is
broader than the Nasdaq-100. It is only used to ask whether the Fed-timing
mechanism appears in earlier tightening eras.

Candidate frozen for this run:
  aggressive = >=50bp target increase in prior 63 calendar days
  persistent = Fed target at recovery > target at shock
  warning = aggressive AND persistent

No TQQQ returns and no threshold optimization.
"""
from pathlib import Path
import io,requests,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research"
START="1971-02-05";END="1985-01-01";SHOCK=-.045;REC=.10;DAYS=63;BP=50

def market():
 u="https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM"
 z=pd.read_csv(io.StringIO(requests.get(u,timeout=30).text))
 z.observation_date=pd.to_datetime(z.observation_date);z.NASDAQCOM=pd.to_numeric(z.NASDAQCOM,errors="coerce")
 return z.set_index("observation_date").NASDAQCOM.loc[START:END].dropna()
def fed():
 u="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"
 z=pd.read_csv(io.StringIO(requests.get(u,timeout=30).text))
 z.observation_date=pd.to_datetime(z.observation_date);z.DFF=pd.to_numeric(z.DFF,errors="coerce")
 return z.set_index("observation_date").DFF.dropna()
def run(px,fr):
 r=px.pct_change().fillna(0).to_numpy();a=px.to_numpy();armed=False;low=np.nan;li=si=None;rows=[]
 for i in range(1,len(px)):
  if not armed and r[i]<=SHOCK:armed=True;low=a[i];li=si=i
  if armed:
   if a[i]<low:low=a[i];li=i
   if a[i]/low-1>=REC:
    d=px.index[i];f=fr.loc[:d];cur=float(f.iloc[-1]);p=f.loc[:d-pd.Timedelta(days=DAYS)]
    old=float(p.iloc[-1]) if len(p) else np.nan;fs=fr.loc[:px.index[si]];sr=float(fs.iloc[-1])
    row={"shock_date":px.index[si],"recovery_date":d,"shock_to_recovery_td":i-si,
         "fed_63d_bp":(cur-old)*100,"fed_change_shock_to_recovery_bp":(cur-sr)*100,
         "aggressive":(cur-old)*100>=BP,"persistent":cur>sr}
    row["warning"] = row["aggressive"] and row["persistent"]
    for n in [60,120,252]:
     q=px.loc[d:].iloc[:n+1];row[f"fwd_{n}d"]=float(q.iloc[-1]/q.iloc[0]-1) if len(q)>1 else np.nan
    rows.append(row);armed=False;low=np.nan;li=si=None
 return pd.DataFrame(rows)
if __name__=="__main__":
 OUT.mkdir(parents=True,exist_ok=True);e=run(market(),fed());e.to_csv(OUT/"fed_early_nasdaq_crossproxy.csv",index=False)
 print("FROZEN CANDIDATE: >=50bp/63d AND target higher at recovery than shock")
 print(e.to_string(index=False))
 print("\nSUMMARY")
 print(e.groupby("warning").agg(events=("recovery_date","size"),negative120=("fwd_120d",lambda x:(x<0).sum()),median120=("fwd_120d","median"),median252=("fwd_252d","median")).to_string())
