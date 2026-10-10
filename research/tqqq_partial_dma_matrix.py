"""Predeclared B0 + partial-exposure DMA matrix for synthetic 3x QQQ.

Primary candidates combine the canonical QQQ -4.5% shock / +10% recovery
control (B0) with a DMA exposure overlay: B0's defensive signal always
takes precedence; outside B0 defensive windows, exposure is 100% above DMA
and the predeclared partial level below DMA. Re-entry from B0 is immediate.

DMA-only variants are retained as diagnostics only, not candidate strategies.
All candidates start with $5,000 on the same post-250-session evaluation
date. Signal history is computed before the evaluation slice. No optimization,
costs, or cash yield.
"""
from pathlib import Path
import numpy as np
import pandas as pd
try:
    from .causal_execution import next_open_equity
    from .tqqq_three_layer_event_attribution import build, INITIAL
    from .reentry_isolation import target_exposure
except ImportError:
    from causal_execution import next_open_equity
    from tqqq_three_layer_event_attribution import build, INITIAL
    from reentry_isolation import target_exposure

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
DMAS=[100,125,150,175,200,250]; BELOW=[1.0,0.75,0.50,0.25,0.0]


def equity(x,sig):
    w=np.asarray(sig,float)
    eq=next_open_equity(w,x.on3,x.in3,INITIAL)
    dd=eq/np.maximum.accumulate(eq)-1
    return float(eq[-1]),float(dd.min()),float(w.mean())


def combine_b0_and_dma(b0_signal, dma_signal):
    """B0 defensive state takes precedence; otherwise apply DMA exposure."""
    b0 = np.asarray(b0_signal, dtype=float)
    dma = np.asarray(dma_signal, dtype=float)
    if b0.shape != dma.shape:
        raise ValueError("B0 and DMA signals must have identical shapes")
    if not (np.isfinite(b0).all() and np.isfinite(dma).all()):
        raise ValueError("signals must be finite")
    if ((b0 < 0) | (b0 > 1) | (dma < 0) | (dma > 1)).any():
        raise ValueError("signals must be exposures in [0, 1]")
    return np.minimum(b0, dma)


def run_matrix(full):
    """Evaluate combined candidates and diagnostic DMA-only variants."""
    full=full.copy()
    max_dma=max(DMAS)
    b0_full=target_exposure(full.rename(columns={"adj_close":"Adj Close"}),"B0").to_numpy(dtype=float)
    signals={}
    for dma in DMAS:
        ma=full.adj_close.rolling(dma).mean()
        above=(full.adj_close.to_numpy()>=ma.to_numpy())
        for below in BELOW:
            sig=np.where(above,1.0,below)
            signals[(dma,below)]=sig
    start=max_dma-1
    x=full.iloc[start:].copy()
    b0=b0_full[start:]
    years=(x.index[-1]-x.index[0]).days/365.2425
    rows=[]

    def record(label,dma,below,sig):
        final,dd,exp=equity(x,sig)
        rows.append({"strategy":label,"dma":dma,"below_exposure":below,
                     "evaluation_start":x.index[0].date().isoformat(),
                     "evaluation_end":x.index[-1].date().isoformat(),
                     "observations":len(x),"starting_balance":INITIAL,
                     "final":final,"cagr":(final/INITIAL)**(1/years)-1,
                     "max_dd":dd,"avg_exposure":exp})

    record("B0_SHOCK_RECOVERY",-1,np.nan,b0)
    record("synthetic_3x_qqq_buy_hold",0,1.0,np.ones(len(x),dtype=float))
    for dma in DMAS:
        for below in BELOW:
            dma_signal = signals[(dma,below)][start:]
            combined = combine_b0_and_dma(b0, dma_signal)
            record("B0_PLUS_DMA_PARTIAL_EXPOSURE",dma,below,combined)
            record("DMA_ONLY_DIAGNOSTIC",dma,below,dma_signal)
    return pd.DataFrame(rows).sort_values("final",ascending=False),x.index[0],x.index[-1]


def main():
    full=build()
    out,start,end=run_matrix(full)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_partial_dma_matrix.csv",index=False)
    print("COMMON EVALUATION WINDOW",start.date(),"to",end.date(),
          "| initial capital",INITIAL,"| warmup",max(DMAS)-1,"sessions")
    print(out.to_string(index=False))
    print("\nBY DMA")
    print(out.sort_values(["dma","below_exposure"],ascending=[True,False]).to_string(index=False))


if __name__=="__main__":
    main()
