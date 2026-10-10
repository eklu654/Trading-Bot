"""Actual-TQQQ validation of B0 + partial-exposure DMA combinations.

Primary candidates combine the QQQ -4.5% shock / +10% recovery control (B0)
with a QQQ-DMA exposure overlay. B0's defensive state takes precedence;
outside B0 defensive windows, exposure is 100% above DMA and the predeclared
partial level below DMA. B0 re-entry is immediate. DMA-only variants remain
diagnostic rows, not candidate strategies.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_equity
from reentry_isolation import target_exposure

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-05"
DMAS=[100,125,150,175,200,250]
BELOW=[1.0,0.75,0.50,0.25,0.0]

def dl(t, start=START):
    x=yf.download(t,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def main():
    # QQQ starts before TQQQ so B0's running-low state is initialized from
    # the full signal history; evaluation capital still begins on the shared
    # post-250-DMA date below.
    q=dl("QQQ",start="1999-03-10"); t=dl("TQQQ",start=START)
    b0_signal=target_exposure(q.rename(columns={"adj_close":"Adj Close"}),"B0")
    x=q.join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="inner")
    x["b0_signal"]=b0_signal.reindex(x.index)
    t_adj_open=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close
    x["on"]=(t_adj_open/x.tqqq_adj_close.shift(1)-1).fillna(0)
    x["in"]=(x.tqqq_adj_close/t_adj_open-1).fillna(0)

    # One common evaluation window after the maximum 250-session lookback.
    # All strategies begin with the same $5,000 on the same date. Moving
    # averages are calculated on full history before slicing, so signals are
    # warmed up without cash-only warmup days distorting ending balances.
    max_dma=max(DMAS)
    x["eval_date"] = x.index
    for dma in DMAS:
        x[f"ma_{dma}"] = x.adj_close.rolling(dma).mean()
    x=x.iloc[max_dma-1:].copy()
    years=(x.index[-1]-x.index[0]).days/365.2425
    rows=[]

    def record(label,dma,below,sig):
        eq=next_open_equity(sig,x.on,x["in"],INITIAL)
        dd=eq/np.maximum.accumulate(eq)-1
        rows.append({"strategy":label,"dma":dma,"below_exposure":below,
                     "evaluation_start":x.index[0].date().isoformat(),
                     "evaluation_end":x.index[-1].date().isoformat(),
                     "final":float(eq[-1]),
                     "cagr":(float(eq[-1])/INITIAL)**(1/years)-1,
                     "max_dd":float(dd.min()),"avg_exposure":float(np.mean(sig))})

    record("BUY_HOLD",0,1.0,np.ones(len(x)))
    record("B0_SHOCK_RECOVERY",-1,np.nan,x.b0_signal.to_numpy(dtype=float))
    for dma in DMAS:
        ma=x[f"ma_{dma}"].to_numpy()
        above=(x.adj_close.to_numpy()>=ma)
        for below in BELOW:
            sig=np.where(above,1.0,below)
            combined=np.minimum(x.b0_signal.to_numpy(dtype=float),sig)
            record("B0_PLUS_DMA_PARTIAL",dma,below,combined)
            record("DMA_ONLY_DIAGNOSTIC",dma,below,sig)

    out=pd.DataFrame(rows).sort_values("final",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"tqqq_actual_partial_dma_matrix.csv",index=False)
    print("ACTUAL TQQQ; QQQ DMA signal; next-open execution")
    print("COMMON EVALUATION WINDOW",x.index[0].date(),"to",x.index[-1].date(),
          "| initial capital",INITIAL)
    print(out.to_string(index=False))
    print("\\nBY DMA")
    print(out.sort_values(["dma","below_exposure"]).to_string(index=False))
if __name__=="__main__": main()
