from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from failed_bounce_structural_matrix import dl,features,rules,events
INITIAL=5000.0
OUT=Path("data/research"); SHOCKS=(-.03,-.04,-.045,-.05,-.06); EXPOSURES=(.25,.5,.75)
def equity(p,t,shock,rule,exposure):
    qr=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy(); ar=t.pct_change().fillna(0).to_numpy()
    f=features(p); armed=False; low=np.nan; flagged=False; invested=np.ones(len(p))
    for i in range(1,len(p)):
        if not armed and qr[i]<=shock: armed=True; low=px[i]; flagged=False
        if armed:
            if px[i]<low: low=px[i]
            gain=px[i]/low-1
            if gain>=.10 and not flagged:
                try: flagged=bool(rule(f.iloc[i]))
                except Exception: flagged=False
            if gain>=.10:
                invested[i]=exposure if flagged else 1.0
                armed=False; low=np.nan
            else: invested[i]=0.0
    ex=np.roll(invested,1); ex[0]=1.0
    return INITIAL*np.cumprod(1+ex*ar)[-1]
def main():
    p=dl("QQQ")["Adj Close"]; t=dl("TQQQ")["Adj Close"]; rows=[]
    for shock in SHOCKS:
      for name,rule in rules().items():
        for e in EXPOSURES:
          rows.append({"shock_pct":-shock,"strategy":name,"flagged_exposure":e,"final_balance":equity(p,t,shock,rule,e)})
    d=pd.DataFrame(rows).sort_values("final_balance",ascending=False); OUT.mkdir(parents=True,exist_ok=True); d.to_csv(OUT/"failed_bounce_structural_partial_exposure.csv",index=False); print(d.head(30).to_string(index=False))
if __name__=="__main__": main()
