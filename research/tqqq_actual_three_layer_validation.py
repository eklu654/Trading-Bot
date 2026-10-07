"""Actual-TQQQ validation of the frozen three-layer QQQ signal architecture.

Signals are generated from QQQ/VIX/Fed exactly as the synthetic study.
Execution is on actual TQQQ adjusted open/close data, so this tests whether
the architecture survives real leveraged-ETF path behavior.
"""
from pathlib import Path
import numpy as np, pandas as pd
import yfinance as yf
from tqqq_three_layer_event_attribution import FED_EVENTS, RATE_THRESHOLD, SHOCK_THRESHOLD, fed_series

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"; INITIAL=5000.0
START="2010-01-01"; END="2026-10-05"

def dl(t):
    x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def main():
    q=dl("QQQ"); t=dl("TQQQ"); v=dl("^VIX")[["close"]].rename(columns={"close":"vix"})
    x=q.join(v,how="left").join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="inner")
    x.vix=x.vix.ffill()
    # Canonical signal source is QQQ. TQQQ is execution-only.
    x["dma"]=x.adj_close.rolling(100).mean(); x["ret60"]=x.adj_close/x.adj_close.shift(60)-1
    x["daily_ret"]=x.adj_close.pct_change(); x["rv20"]=x.daily_ret.rolling(20).std()*np.sqrt(252)
    x["vix_chg20"]=x.vix/x.vix.shift(20)-1; x["rv_chg20"]=x.rv20/x.rv20.shift(20)-1
    x["fed"]=fed_series(x.index)
    x["base"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:99],"base"]=0
    x["veto"]=(x.adj_close<x.dma)&(x.fed>RATE_THRESHOLD)&(x.ret60>=0)
    x["shock"]=(x.vix_chg20>=SHOCK_THRESHOLD)|(x.rv_chg20>=SHOCK_THRESHOLD)
    x["conditioned"]=np.where(x.base==1,1.0,np.where(x.veto,1.0,0.0))
    x["three"]=np.where(x.base==1,1.0,np.where(x.veto&~x.shock,1.0,0.0))
    x["t_adj_open"]=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close
    x["on"]=(x.t_adj_open/x.tqqq_adj_close.shift(1)-1).fillna(0)
    x["in"]=(x.tqqq_adj_close/x.t_adj_open-1).fillna(0)

    def eq(sig):
        # Signal at close t is executable at open t+1.
        # Thus the overnight leg into day t+1 belongs to the position
        # that was already held before that open; the intraday leg uses
        # the newly executed prior-close signal.
        w=np.asarray(sig,float)
        exec_w=np.roll(w,1); exec_w[0]=0
        prev_exec=np.roll(exec_w,1); prev_exec[0]=0
        daily=(1+prev_exec*x.on.to_numpy())*(1+exec_w*x["in"].to_numpy())-1
        e=INITIAL*np.cumprod(1+daily); dd=e/np.maximum.accumulate(e)-1
        return float(e[-1]),float(dd.min()),float(w.mean())

    rows=[]
    years=(x.index[-1]-x.index[0]).days/365.2425
    for name in ["base","conditioned","three"]:
        final,dd,exp=eq(x[name]); rows.append({"strategy":name,"final":final,"cagr":(final/INITIAL)**(1/years)-1,"max_dd":dd,"avg_exposure":exp})
    bh,bd,be=eq(np.ones(len(x)))
    rows.append({"strategy":"actual_tqqq_buy_hold","final":bh,"cagr":(bh/INITIAL)**(1/years)-1,"max_dd":bd,"avg_exposure":be})
    out=pd.DataFrame(rows); OUT.mkdir(parents=True,exist_ok=True); out.to_csv(OUT/"tqqq_actual_three_layer_validation.csv",index=False)
    print(out.to_string(index=False))
    print("\nSIGNAL SOURCE: QQQ adjusted close / 100-DMA; EXECUTION: actual TQQQ next session open.")
    print("\nACTUAL TQQQ COST STRESS (causal next-open execution)")
    cost_rows=[]
    for bps in [0,5,10,25,50]:
        for name in ["base","conditioned","three"]:
            w=x[name].to_numpy()
            exec_w=np.roll(w,1); exec_w[0]=0
            prev_exec=np.roll(exec_w,1); prev_exec[0]=0
            daily=(1+prev_exec*x.on.to_numpy())*(1+exec_w*x["in"].to_numpy())-1
            daily-=np.abs(exec_w-prev_exec)*(bps/10000.0)
            e=INITIAL*np.cumprod(1+daily); dd=e/np.maximum.accumulate(e)-1
            cost_rows.append({"bps":bps,"strategy":name,"final":float(e[-1]),"cagr":float((e[-1]/INITIAL)**(1/years)-1),"max_dd":float(dd.min())})
    print(pd.DataFrame(cost_rows).to_string(index=False))
    print("\nCOUNTS",int(x.veto.sum()),int(x.shock.sum()),int((x.veto&x.shock).sum()))
if __name__=="__main__": main()
