"""Fed-active tightening + QQQ DMA sticky-defense test.

Frozen rule family:
- Enter defense when QQQ is below its chosen DMA AND the Fed has hiked
  within the trailing 90 days (TIGHTENING_ACTIVE).
- Once defensive, remain defensive until QQQ closes back above the same DMA.
- Signal is close-to-next-open.
- Defense exposures: 0%, 25%, 50%, 75%.
- DMA: 100, 150, 200.

This directly tests whether the Fed hiking cycle is the missing regime
modifier, especially for the 2022 tightening regime.
"""

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd
import yfinance as yf

from causal_execution import next_open_equity

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
INITIAL=5000.0
START="1999-03-10"
END="2026-10-06"
DMAS=(100,150,200)
EXPOSURES=(0.0,0.25,0.50,0.75)


def fred_csv(series_id):
    req=Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
               headers={"User-Agent":"Trading-Bot-research/1.0"})
    with urlopen(req,timeout=30) as response:
        x=pd.read_csv(BytesIO(response.read()))
    x.columns=["date",series_id.lower()]
    x["date"]=pd.to_datetime(x["date"])
    x[series_id.lower()]=pd.to_numeric(x[series_id.lower()],errors="coerce")
    return x.set_index("date")


def fed_state(index):
    fed=pd.concat([fred_csv(s) for s in ("DFEDTAR","DFEDTARU","DFEDTARL")],axis=1).sort_index()
    fed["target"] = fed["dfedtar"]
    mid=(fed["dfedtaru"]+fed["dfedtarl"])/2
    fed.loc[mid.notna(),"target"]=mid[mid.notna()]
    fed["change"]=fed["target"].diff()
    fed["hike_90d"]=fed["change"].gt(0.001).astype(int).rolling("90D").sum()
    daily=pd.DataFrame(index=index)
    daily["date"]=pd.to_datetime(daily.index).astype("datetime64[ns]")
    use=fed[["hike_90d"]].reset_index().rename(columns={"index":"date"})
    use["date"]=pd.to_datetime(use["date"]).astype("datetime64[ns]")
    mapped=pd.merge_asof(daily.sort_values("date"),use.sort_values("date"),
                         on="date",direction="backward").set_index("date")
    return mapped["hike_90d"].reindex(index).fillna(0)


def qqq():
    x=yf.download("QQQ",start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    x=x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=((1+3*(x.adj_open/x.adj_close.shift(1)-1)).clip(lower=0)-1).fillna(0)
    x["in3"]=((1+3*(x.adj_close/x.adj_open-1)).clip(lower=0)-1).fillna(0)
    return x


def actual_tqqq(signal_index):
    q=yf.download("QQQ",start="2010-01-01",end=END,auto_adjust=False,progress=False,actions=False)
    t=yf.download("TQQQ",start="2010-01-01",end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(q.columns,pd.MultiIndex): q.columns=q.columns.get_level_values(0)
    if isinstance(t.columns,pd.MultiIndex): t.columns=t.columns.get_level_values(0)
    q.index=pd.to_datetime(q.index).tz_localize(None); t.index=pd.to_datetime(t.index).tz_localize(None)
    q=q.rename(columns={"Adj Close":"qqq_adj_close"})
    t=t.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x=q[["qqq_adj_close"]].join(t[["open","close","adj_close"]],how="inner").sort_index().dropna()
    x["adj_open"]=x.open*x.adj_close/x.close
    x["on3"]=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    x["in3"]=(x.adj_close/x.adj_open-1).fillna(0)
    return x


def weights(signal_close,hikes,dma,defense):
    ma=signal_close.rolling(dma).mean()
    armed=False
    out=np.ones(len(signal_close))
    for i,(px,m,h) in enumerate(zip(signal_close.to_numpy(),ma.to_numpy(),hikes.to_numpy())):
        if not np.isfinite(m):
            out[i]=1.0
            continue
        if not armed and px < m and h > 0:
            armed=True
        elif armed and px >= m:
            armed=False
        out[i]=defense if armed else 1.0
    return pd.Series(out,index=signal_close.index)


def eval_frame(frame,source,dma,defense,hikes,signal_col):
    sig=weights(frame[signal_col],hikes.reindex(frame.index).fillna(0),dma,defense)
    eq=next_open_equity(sig,frame["on3"],frame["in3"],INITIAL)
    peak=np.maximum.accumulate(eq); dd=eq/peak-1
    years=(frame.index[-1]-frame.index[0]).days/365.25
    return {"source":source,"dma":dma,"defense_exposure":defense,
            "final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1),
            "max_drawdown":float(dd.min()),"minimum_equity":float(eq.min()),
            "avg_exposure":float(sig.mean()),"defensive_days":int((sig<1).sum())}


def main():
    DATA.mkdir(parents=True,exist_ok=True)
    q=qqq(); hikes=fed_state(q.index)
    rows=[]
    for dma in DMAS:
        for d in EXPOSURES:
            rows.append(eval_frame(q,"synthetic_qqq_3x",dma,d,hikes,"adj_close"))
    a=actual_tqqq(q.index)
    # Recompute Fed state on the actual overlapping index.
    ah=fed_state(a.index)
    for dma in DMAS:
        for d in EXPOSURES:
            rows.append(eval_frame(a,"actual_tqqq_with_qqq_signal",dma,d,ah,"qqq_adj_close"))
    out=pd.DataFrame(rows).sort_values(["source","final_balance"],ascending=[True,False])
    out.to_csv(DATA/"tqqq_fed_active_dma_sticky_matrix.csv",index=False)
    print(out.to_string(index=False))


if __name__=="__main__":
    main()
