"""Actual-TQQQ partial-exposure DMA matrix.

Signal: QQQ adjusted close vs its DMA.
Execution: actual TQQQ at next session open.
Above DMA: 100% TQQQ.
Below DMA: fixed predeclared exposure.
Immediate re-entry when QQQ closes back above DMA.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-05"
DMAS=[100,125,150,175,200,250]
BELOW=[1.0,0.75,0.50,0.25,0.0]

def dl(t):
    x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def main():
    q=dl("QQQ"); t=dl("TQQQ")
    x=q.join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="inner")
    t_adj_open=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close
    x["on"]= (t_adj_open/x.tqqq_adj_close.shift(1)-1).fillna(0)
    x["in"]= (x.tqqq_adj_close/t_adj_open-1).fillna(0)
    years=(x.index[-1]-x.index[0]).days/365.2425
    rows=[]
    for dma in DMAS:
        ma=x.adj_close.rolling(dma).mean()
        for below in BELOW:
            sig=np.where(x.adj_close>=ma,1.0,below)
            sig[:dma-1]=0.0
            eq=next_open_equity(sig,x.on,x["in"],INITIAL)
            dd=eq/np.maximum.accumulate(eq)-1
            final=float(eq[-1])
            rows.append({"dma":dma,"below_exposure":below,"final":final,
                         "cagr":(final/INITIAL)**(1/years)-1,
                         "max_dd":float(dd.min()),"avg_exposure":float(np.mean(sig))})
    bh=next_open_equity(np.ones(len(x)),x.on,x["in"],INITIAL)
    bdd=bh/np.maximum.accumulate(bh)-1
    rows.append({"dma":"BUY_HOLD","below_exposure":1.0,"final":float(bh[-1]),
                 "cagr":(bh[-1]/INITIAL)**(1/years)-1,
                 "max_dd":float(bdd.min()),"avg_exposure":1.0})
    out=pd.DataFrame(rows).sort_values("final",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_actual_partial_dma_matrix.csv",index=False)
    print(out.to_string(index=False))
    print("\nBY DMA")
    print(out.sort_values(["dma","below_exposure"],key=lambda c:c.astype(str)).to_string(index=False))
if __name__=="__main__": main()
