"""Trigger-asset audit for the crash architecture.
Identical execution and reentry rules; only trigger asset changes: QQQ vs TQQQ.
Execution: signal at today's close, position change at next day's adjusted open.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"research";INITIAL=5000.
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-07",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex):x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None);return x
def adjopen(x):
 return x["Open"].squeeze().astype(float)*(x["Adj Close"].squeeze().astype(float)/x["Close"].squeeze().astype(float))
def main():
 q=dl("QQQ");t=dl("TQQQ");idx=q.index.intersection(t.index);q,t=q.reindex(idx),t.reindex(idx);qp=q["Close"].squeeze().astype(float);tp=t["Close"].squeeze().astype(float);qo=adjopen(q);to=adjopen(t);qret=qo.shift(-1)/qo-1;tret=to.shift(-1)/to-1
 rows=[{"trigger":"BENCHMARK","rule":"TQQQ_BH","final":INITIAL*np.prod(1+tret.fillna(0).to_numpy()),"cagr":(INITIAL*np.prod(1+tret.fillna(0).to_numpy())/INITIAL)**(365.25/((idx[-1]-idx[0]).days))-1,"maxdd":float((pd.Series(INITIAL*np.cumprod(1+tret.fillna(0).to_numpy()))/pd.Series(INITIAL*np.cumprod(1+tret.fillna(0).to_numpy())).cummax()-1).min()),"cash":0}]
 for trigger,price in [("QQQ",qp),("TQQQ",tp)]:
  r=price.pct_change().fillna(0)
  for shock in [-.04,-.05,-.06,-.07]:
   for mom in [5,10,15,20]:
    state=np.ones(len(idx));armed=False
    for i in range(1,len(idx)):
     if r.iloc[i]<=shock:armed=True
     if armed and i>=mom and price.iloc[i]/price.iloc[i-mom]-1>0:armed=False
     elif armed:state[i]=0
    ex=np.roll(state,1);ex[0]=1;d=1+tret.to_numpy()*ex;e=INITIAL*np.cumprod(np.nan_to_num(d,nan=1.0));w=pd.Series(e,index=idx);yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"trigger":trigger,"rule":f"S{shock}_M{mom}","final":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"cash":float((state==0).mean())})
 out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/"trigger_asset_audit_open_execution.csv",index=False);print(out.sort_values("final",ascending=False).head(30).to_string(index=False))
if __name__=="__main__":main()

# trigger
