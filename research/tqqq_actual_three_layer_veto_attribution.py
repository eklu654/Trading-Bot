from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from tqqq_three_layer_event_attribution import RATE_THRESHOLD,SHOCK_THRESHOLD,fed_series
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.; START="2010-01-01"; END="2026-10-05"
def dl(t):
 x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()
def main():
 q=dl("QQQ"); t=dl("TQQQ"); v=dl("^VIX")[["close"]].rename(columns={"close":"vix"})
 x=q.join(v,how="left").join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="inner"); x.vix=x.vix.ffill()
 x["dma"]=x.adj_close.rolling(100).mean(); x["ret60"]=x.adj_close/x.adj_close.shift(60)-1; x["rv20"]=x.adj_close.pct_change().rolling(20).std()*np.sqrt(252)
 x["vix_chg20"]=x.vix/x.vix.shift(20)-1; x["rv_chg20"]=x.rv20/x.rv20.shift(20)-1; x["fed"]=fed_series(x.index)
 x["base"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:99],"base"]=0
 x["veto"]=(x.adj_close<x.dma)&(x.fed>RATE_THRESHOLD)&(x.ret60>=0); x["shock"]=(x.vix_chg20>=SHOCK_THRESHOLD)|(x.rv_chg20>=SHOCK_THRESHOLD)
 x["three"]=np.where(x.base==1,1.,np.where(x.veto&~x.shock,1.,0.))
 x["aopen"]=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close; x["on"]=(x.aopen/x.tqqq_adj_close.shift(1)-1).fillna(0); x["inn"]=(x.tqqq_adj_close/x.aopen-1).fillna(0)
 def eq(sig):
  w=sig.to_numpy(float); p=np.roll(w,1); p[0]=0; d=(1+p*x.on.to_numpy())*(1+w*x.inn.to_numpy())-1; e=INITIAL*np.cumprod(1+d); return d,e
 bd,be=eq(x.base); td,te=eq(x.three)
 # Each exception day: actual incremental return from three vs base, and terminal counterfactual delta from toggling that day's position.
 rows=[]
 for i in np.where(x.veto.to_numpy())[0]:
  alt=x.three.copy(); alt.iloc[i]=x.base.iloc[i]
  _,ae=eq(alt)
  rows.append({"date":x.index[i],"shock":bool(x.shock.iloc[i]),"ret60":x.ret60.iloc[i],"fed":x.fed.iloc[i],"vix_chg20":x.vix_chg20.iloc[i],"rv_chg20":x.rv_chg20.iloc[i],"base_equity":be[i],"three_equity":te[i],"terminal_delta":te[-1]-ae[-1]})
 out=pd.DataFrame(rows); out.to_csv(OUT/"tqqq_actual_three_layer_veto_attribution.csv",index=False)
 print("ACTUAL VETO EVENTS",len(out),"sum terminal deltas",out.terminal_delta.sum())
 print("positive",out.loc[out.terminal_delta>0,"terminal_delta"].sum(),"negative",out.loc[out.terminal_delta<0,"terminal_delta"].sum())
 print(out.sort_values("terminal_delta",ascending=False).head(10).to_string(index=False)); print(out.sort_values("terminal_delta").head(10).to_string(index=False))
 print("\nBY SHOCK",out.groupby("shock").terminal_delta.agg(["count","sum","mean"]).to_string())
if __name__=="__main__": main()
