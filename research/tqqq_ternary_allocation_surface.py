"""Causal ternary allocation: QQQ signal chooses TQQQ, QQQ, or cash."""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-07"
def dl(s):
    x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()
def ret(t):
    ao=t.open*t.adj_close/t.close
    return ((ao/t.adj_close.shift(1)-1).fillna(0).to_numpy(),
            (t.adj_close/ao-1).fillna(0).to_numpy())
def main():
    q,t=dl("QQQ"),dl("TQQQ")
    idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx)
    qo,qi=ret(q); to,ti=ret(t); p=q.adj_close; rows=[]
    for look in [5,10,20,50]:
      mom=p.pct_change(look).to_numpy(); ma=p.rolling(look).mean().to_numpy(); price=p.to_numpy()
      for strong in [.01,.02,.05,.10]:
       for weak in [-.05,-.02,0,.01]:
        if weak>=strong: continue
        state=np.where((mom>=strong),2,np.where((mom>weak)&(price>ma),1,0))
        ex=np.roll(state,1); ex[0]=0; prev=np.roll(ex,1); prev[0]=0
        daily=np.ones(len(idx))
        for i in range(len(idx)):
            if prev[i]==1: daily[i]*=1+qo[i]
            elif prev[i]==2: daily[i]*=1+to[i]
            if ex[i]==1: daily[i]*=1+qi[i]
            elif ex[i]==2: daily[i]*=1+ti[i]
        e=INITIAL*np.cumprod(daily); w=pd.Series(e,index=idx); yrs=(idx[-1]-idx[0]).days/365.25
        rows.append({"strategy":f"L{look}_S{strong}_W{weak}","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"tqqq_pct":float((state==2).mean()),"qqq_pct":float((state==1).mean())})
    bh_daily=(1+to)*(1+ti)-1; e=INITIAL*np.cumprod(1+bh_daily); w=pd.Series(e,index=idx); yrs=(idx[-1]-idx[0]).days/365.25
    rows.append({"strategy":"TQQQ_BH","final_balance":e[-1],"cagr":(e[-1]/INITIAL)**(1/yrs)-1,"maxdd":float((w/w.cummax()-1).min()),"tqqq_pct":1.,"qqq_pct":0.})
    r=pd.DataFrame(rows).sort_values("final_balance",ascending=False); OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_ternary_allocation_surface.csv",index=False); print(r.head(40).to_string(index=False))
if __name__=="__main__": main()
