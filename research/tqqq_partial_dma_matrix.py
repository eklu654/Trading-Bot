"""Predeclared B0 + partial-exposure DMA matrix for synthetic 3x QQQ.

Primary candidates combine the canonical QQQ -4.5% shock / +10% recovery
control (B0) with a DMA exposure overlay: B0's defensive signal always
takes precedence; outside B0 defensive windows, exposure is 100% above DMA
and the predeclared partial level below DMA. Re-entry from B0 is immediate.

DMA-only variants are retained as diagnostics only, not candidate strategies.
All candidates start with $5,000 on the same post-250-session evaluation
date. Signal history is computed before the evaluation slice. No parameter
optimization; cost stress is 0/10/25/50 bps per exposure change; no cash yield.
"""
from pathlib import Path
import numpy as np
import pandas as pd
try:
    from .causal_execution import next_open_cost_equity
    from .tqqq_three_layer_event_attribution import build, INITIAL
    from .reentry_isolation import target_exposure
except ImportError:
    from causal_execution import next_open_cost_equity
    from tqqq_three_layer_event_attribution import build, INITIAL
    from reentry_isolation import target_exposure

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
DMAS=[100,125,150,175,200,250]; BELOW=[1.0,0.75,0.50,0.25,0.0]; COSTS=(0,10,25,50)
PERIODS=(
    ("dotcom_bear","2000-03-03","2002-12-31"),
    ("post_dotcom_recovery","2003-01-01","2007-12-31"),
    ("gfc_and_recovery","2008-01-01","2012-12-31"),
    ("bull_2013_2019","2013-01-01","2019-12-31"),
    ("covid","2020-01-01","2021-12-31"),
    ("2022_to_latest","2022-01-01","2026-10-02"),
)


def equity(x,sig,cost_bps=0):
    w=np.asarray(sig,float)
    eq=next_open_cost_equity(w,x.on3,x.in3,cost_bps,INITIAL)
    dd=eq/np.maximum.accumulate(eq)-1
    return float(eq[-1]),float(dd.min()),float(w.mean()),eq


def period_metrics(dates, equity_path, period_start, period_end):
    dates=pd.DatetimeIndex(dates)
    mask=(dates>=pd.Timestamp(period_start))&(dates<=pd.Timestamp(period_end))
    positions=np.flatnonzero(mask)
    if len(positions)<2:
        return None
    first,last=int(positions[0]),int(positions[-1])
    prior_equity=INITIAL if first==0 else float(equity_path[first-1])
    segment=np.concatenate(([INITIAL], INITIAL*np.asarray(equity_path[first:last+1])/prior_equity))
    peaks=np.maximum.accumulate(segment)
    dd=segment/peaks-1
    span_days=(dates[last]-(dates[first-1] if first>0 else dates[first])).days
    years=max(span_days/365.25,1/365.25)
    return {
        "period_start":dates[first].date().isoformat(),
        "period_end":dates[last].date().isoformat(),
        "observations":int(len(positions)),
        "ending_balance":float(segment[-1]),
        "cagr":float((segment[-1]/INITIAL)**(1/years)-1),
        "max_drawdown":float(dd.min()),
        "minimum_equity":float(segment.min()),
    }


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
    period_rows=[]

    def record(label,dma,below,sig,cost_bps):
        final,dd,exp,path=equity(x,sig,cost_bps)
        dd_path=path/np.maximum.accumulate(path)-1
        trough=int(np.argmin(dd_path))
        peak=int(np.argmax(path[:trough+1]))
        rows.append({"strategy":label,"dma":dma,"below_exposure":below,
                     "cost_bps_per_exposure_change":cost_bps,
                     "evaluation_start":x.index[0].date().isoformat(),
                     "evaluation_end":x.index[-1].date().isoformat(),
                     "observations":len(x),"starting_balance":INITIAL,
                     "final":final,"cagr":(final/INITIAL)**(1/years)-1,
                     "max_dd":dd,"max_dd_peak_date":x.index[peak].date().isoformat(),
                     "max_dd_trough_date":x.index[trough].date().isoformat(),
                     "avg_exposure":exp})
        for period_name,period_start,period_end in PERIODS:
            metrics=period_metrics(x.index,path,period_start,period_end)
            if metrics is not None:
                period_rows.append({"strategy":label,"dma":dma,"below_exposure":below,
                                    "cost_bps_per_exposure_change":cost_bps,
                                    "period":period_name,**metrics})

    for cost_bps in COSTS:
        record("B0_SHOCK_RECOVERY",-1,np.nan,b0,cost_bps)
        record("synthetic_3x_qqq_buy_hold",0,1.0,np.ones(len(x),dtype=float),cost_bps)
        for dma in DMAS:
            for below in BELOW:
                dma_signal = signals[(dma,below)][start:]
                combined = combine_b0_and_dma(b0, dma_signal)
                record("B0_PLUS_DMA_PARTIAL_EXPOSURE",dma,below,combined,cost_bps)
                record("DMA_ONLY_DIAGNOSTIC",dma,below,dma_signal,cost_bps)
    return (pd.DataFrame(rows).sort_values("final",ascending=False),
            pd.DataFrame(period_rows),x.index[0],x.index[-1])


def main():
    full=build()
    out,periods,start,end=run_matrix(full)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_partial_dma_matrix.csv",index=False)
    periods.to_csv(OUT/"tqqq_partial_dma_periods.csv",index=False)
    print("COMMON EVALUATION WINDOW",start.date(),"to",end.date(),
          "| initial capital",INITIAL,"| warmup",max(DMAS)-1,"sessions")
    print(out.to_string(index=False))
    print("\nBY DMA")
    print(out.sort_values(["dma","below_exposure"],ascending=[True,False]).to_string(index=False))


if __name__=="__main__":
    main()
