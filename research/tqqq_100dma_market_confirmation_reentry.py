"""100-DMA fixed exit + broader market/volatility re-entry hypotheses.

No threshold sweep. Each rule is predeclared before evaluation.
All inputs are known at the close; execution is next open.

Signals:
- QQQ momentum + falling VIX
- QQQ momentum + VIX below its 10-day average
- QQQ momentum + VIX below VIX3M (volatility term structure)
- QQQ 10d momentum + SPY 10d momentum
- QQQ 10d momentum + RSP/SPY relative strength improving
- QQQ 20d momentum + volatility normalization
- QQQ reclaim 20DMA + volatility normalization
- QQQ 5d momentum + 20d momentum
- QQQ 5d momentum + VIX term structure
"""
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from causal_execution import next_open_daily_returns
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
INITIAL=5000.; START="2010-01-01"; END="2026-10-07"

def dl(s):
    x=yf.download(s,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()

def ret(s,n): return s.pct_change(n)
def make(trigger, vix, vix3m, spy, rsp, rule):
    q=trigger; ma20=q.rolling(20).mean(); ma100=q.rolling(100).mean()
    v10=vix.rolling(10).mean(); v3=vix.rolling(3).mean()
    rs=(rsp/spy)
    rs20=rs.pct_change(20)
    out=[]; on=False
    for i in range(len(q)):
        if on and i>=99 and q.iloc[i]<ma100.iloc[i]: on=False
        elif not on and i>=99:
            m5=ret(q,5).iloc[i]; m10=ret(q,10).iloc[i]; m20=ret(q,20).iloc[i]
            vfall=(vix.iloc[i]<vix.iloc[i-1]<vix.iloc[i-2])
            vnorm=vix.iloc[i]<v10.iloc[i]
            term=(vix.iloc[i]<vix3m.iloc[i])
            spy10=ret(spy,10).iloc[i]>0
            rsi=rs20.iloc[i]>0
            x={
              "MOM5_VIXFALL":m5>0 and vfall,
              "MOM10_VIXNORM":m10>0 and vnorm,
              "MOM10_TERM":m10>0 and term,
              "MOM10_SPY":m10>0 and spy10,
              "MOM10_BREADTH":m10>0 and rsi,
              "MOM20_VIX":m20>0 and vnorm,
              "20DMA_VIX":q.iloc[i]>=ma20.iloc[i] and vnorm,
              "MOM5_MOM20":m5>0 and m20>0,
              "MOM5_TERM":m5>0 and term,
            }[rule]
            if bool(x): on=True
        out.append(float(on))
    return pd.Series(out,index=q.index)

def treturns(t):
    ao=t.open*t.adj_close/t.close
    return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)

def stat(name,sig,daily,idx):
    eq=INITIAL*np.cumprod(1+daily); w=pd.Series(eq,index=idx); yrs=(idx[-1]-idx[0]).days/365.25
    dd=w/w.cummax()-1
    return {"strategy":name,"final":w.iloc[-1],"cagr":(w.iloc[-1]/INITIAL)**(1/yrs)-1,
            "max_dd":dd.min(),"avg_exposure":sig.shift(1).fillna(0).mean(),
            "switches":sig.diff().abs().fillna(0).sum()}

def main():
    q,t,v,v3,spy,rsp=[dl(x) for x in ["QQQ","TQQQ","^VIX","^VIX3M","SPY","RSP"]]
    idx=q.index.intersection(t.index)
    for s in [v,v3,spy,rsp]: idx=idx.intersection(s.index)
    q,t,v,v3,spy,rsp=[x.reindex(idx) for x in [q,t,v,v3,spy,rsp]]
    on,inn=treturns(t); rules=["MOM5_VIXFALL","MOM10_VIXNORM","MOM10_TERM","MOM10_SPY",
        "MOM10_BREADTH","MOM20_VIX","20DMA_VIX","MOM5_MOM20","MOM5_TERM"]
    rows=[]
    for trigname,p in [("QQQ",q.adj_close),("TQQQ",t.adj_close)]:
        for rule in rules:
            sig=make(p,v.adj_close,v3.adj_close,spy.adj_close,rsp.adj_close,rule)
            rows.append(stat(f"TQQQ | {trigname if False else trigname} 100DMA exit + {rule}",
                             sig,next_open_daily_returns(sig,on,inn),idx))
    bh=pd.Series(1.,index=idx); rows.append(stat("TQQQ buy_and_hold",bh,next_open_daily_returns(bh,on,inn),idx))
    r=pd.DataFrame(rows).sort_values("final",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True); r.to_csv(OUT/"tqqq_100dma_market_confirmation_reentry.csv",index=False)
    print(r.to_string(index=False))
if __name__=="__main__": main()
