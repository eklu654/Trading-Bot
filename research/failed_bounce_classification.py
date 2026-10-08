import numpy as np,pandas as pd,yfinance as yf
from pathlib import Path
O=Path("data/research"); O.mkdir(parents=True,exist_ok=True)
def dl(s):
 x=yf.download(s,start="2010-01-01",end="2026-10-08",auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None); return x
q=dl("QQQ"); v=dl("^VIX"); p=q["Close"].squeeze().astype(float); vx=v["Close"].squeeze().astype(float).reindex(p.index).ffill()
x=pd.DataFrame({"qqq":p,"ret1":p.pct_change(),"vix":vx,"vix5":vx/vx.shift(5)-1})
for n in [5,10,20,60]: x[f"ret{n}"]=p/p.shift(n)-1
for n in [20,50,100,200]:
 m=p.rolling(n).mean(); x[f"gap{n}"]=p/m-1; x[f"slope{n}"]=m/m.shift(20)-1
d=p.diff(); g=d.clip(lower=0).rolling(14).mean(); l=(-d.clip(upper=0)).rolling(14).mean(); x["rsi14"]=100-100/(1+g/l.replace(0,np.nan))
rows=[]; si=np.flatnonzero(x.ret1.to_numpy()<=-.045)
for k,i in enumerate(si):
 z=x.iloc[i:si[k+1] if k+1<len(si) else len(x)]
 if len(z)<2: continue
 pre=float(x.qqq.iloc[i-1]); tr=int(z.qqq.to_numpy().argmin()); low=float(z.qqq.iloc[tr]); rec=z.qqq/low-1; h=np.flatnonzero(rec.to_numpy()>=.10)
 if not len(h): rows.append({"date":z.index[0].date(),"outcome":"no_10pct"}); continue
 j=int(h[0]); r=z.iloc[j]; f=z.iloc[j:]; peak=np.maximum.accumulate(f.qqq.to_numpy()); dd=float((f.qqq.to_numpy()/peak-1).min())
 rows.append({"date":z.index[0].date(),"recovery":r.name.date(),"outcome":"severe" if dd<=-.2 else "failed" if dd<=-.1 else "continued","post10_dd":dd,"drawdown":low/pre-1,"recovery_days":j-tr,**{c:float(r[c]) for c in x.columns if c not in ["qqq","ret1"]}})
e=pd.DataFrame(rows); e.to_csv(O/"failed_bounce_event_classification.csv",index=False)
z=e[e.outcome!="no_10pct"].copy(); z["failed"]=z.outcome.isin(["failed","severe"]); z["severe"]=z.outcome.eq("severe")
out=[]
for c in ["ret60","ret20","ret10","ret5","gap20","gap50","gap100","gap200","slope50","slope100","slope200","rsi14","vix","vix5","drawdown","recovery_days"]:
 a=z[[c,"failed","severe"]].dropna(); m=a[c].median()
 out.append({"feature":c,"n":len(a),"median_failed":a.loc[a.failed,c].median(),"median_continued":a.loc[~a.failed,c].median(),"low_half_failure":a.loc[a[c]<=m,"failed"].mean(),"high_half_failure":a.loc[a[c]>m,"failed"].mean(),"low_half_severe":a.loc[a[c]<=m,"severe"].mean(),"high_half_severe":a.loc[a[c]>m,"severe"].mean()})
pd.DataFrame(out).to_csv(O/"failed_bounce_feature_separation.csv",index=False)
print(e.outcome.value_counts().to_string()); print(pd.DataFrame(out).sort_values("low_half_severe",ascending=False).to_string(index=False))