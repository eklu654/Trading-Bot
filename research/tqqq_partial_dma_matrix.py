"""Predeclared partial-exposure DMA matrix for synthetic 3x QQQ.

Tests DMA lengths 125/150/175/200/250 with fixed below-DMA exposures
75%, 50%, and 25%. Above DMA is always 100%; re-entry is immediate.
No optimization, costs, or cash yield.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from causal_execution import next_open_equity
from tqqq_three_layer_event_attribution import build, INITIAL

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
DMAS=[100,125,150,175,200,250]; BELOW=[1.0,0.75,0.50,0.25,0.0]

def equity(x,sig):
 w=np.asarray(sig,float)
 eq=next_open_equity(w,x.on3,x.in3,INITIAL); dd=eq/np.maximum.accumulate(eq)-1
 return float(eq[-1]),float(dd.min()),float((w>0).mean())

def main():
    x=build(); years=(x.index[-1]-x.index[0]).days/365.2425; rows=[]
    for dma in DMAS:
        ma=x.adj_close.rolling(dma).mean()
        for below in BELOW:
            sig=np.where(x.adj_close>=ma,1.0,below); sig[:dma-1]=0
            final,dd,exp=equity(x,sig)
            cagr=(final/INITIAL)**(1/years)-1
            rows.append({"dma":dma,"below_exposure":below,"final":final,"cagr":cagr,"max_dd":dd,"avg_exposure":exp})
    out=pd.DataFrame(rows).sort_values("final",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True); out.to_csv(OUT/"tqqq_partial_dma_matrix.csv",index=False)
    print(out.to_string(index=False))
    print("\nBY DMA")
    print(out.sort_values(["dma","below_exposure"],ascending=[True,False]).to_string(index=False))

if __name__=="__main__":
    main()
