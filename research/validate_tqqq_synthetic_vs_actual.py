"""Validate synthetic daily-reset 3x QQQ against actual TQQQ from inception.

Runs the canonical 100-DMA / 0%-below-DMA / immediate-reentry strategy on:
1. synthetic 3x QQQ built from QQQ adjusted OHLC
2. actual TQQQ adjusted OHLC

Same dates and next-open accounting are used. This is a validation study,
not a parameter optimization.
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START="2010-02-11"; END="2026-10-04"; DMA=100; INITIAL=5000.0

def dl(ticker):
    x=yf.download(ticker,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x=x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x.index=pd.to_datetime(x.index).tz_localize(None); x.index.name="Date"
    return x.sort_index().dropna(subset=["open","close","adj_close"])

def synthetic(q):
    x=q.copy(); x["adj_open"]=x.open*x.adj_close/x.close
    ov=(x.adj_open/x.adj_close.shift(1)-1).fillna(0); intra=(x.adj_close/x.adj_open-1).fillna(0)
    x["ov"]=np.clip(1+3*ov,0,None)-1; x["intra"]=np.clip(1+3*intra,0,None)-1
    return x

def strategy(x,lev=False):
    if lev:
        ov=(x.adj_open/x.adj_close.shift(1)-1).fillna(0); intra=(x.adj_close/x.adj_open-1).fillna(0)
        x["ov"]=ov; x["intra"]=intra
    ma=x.adj_close.rolling(DMA).mean(); w=(x.adj_close>=ma).astype(float); w.iloc[:DMA-1]=0
    prev=np.roll(w.to_numpy(),1); prev[0]=0
    daily=(1+prev*x.ov.to_numpy())*(1+w.to_numpy()*x.intra.to_numpy())-1
    eq=INITIAL*np.cumprod(1+daily)
    bh=INITIAL*np.cumprod((1+x.ov)*(1+x.intra))
    return pd.DataFrame({"strategy":eq,"buy_hold":bh},index=x.index)

def main():
    q=synthetic(dl("QQQ"))
    t=dl("TQQQ")
    sq=strategy(q)
    st=strategy(t,lev=True)
    out=pd.DataFrame({
        "synthetic_strategy":sq.strategy,
        "synthetic_buy_hold":sq.buy_hold,
        "actual_tqqq_strategy":st.strategy,
        "actual_tqqq_buy_hold":st.buy_hold,
    })
    rows=[]
    for c in out:
        rows.append({"series":c,"ending_balance":out[c].iloc[-1],
                     "cagr":(out[c].iloc[-1]/INITIAL)**(252/len(out))-1,
                     "max_drawdown":(out[c]/out[c].cummax()-1).min()})
    s=pd.DataFrame(rows)
    out.to_csv(OUT/"tqqq_100dma_synthetic_vs_actual_equity.csv")
    s.to_csv(OUT/"tqqq_100dma_synthetic_vs_actual_summary.csv",index=False)
    print(s.to_string(index=False))
if __name__=="__main__": main()
