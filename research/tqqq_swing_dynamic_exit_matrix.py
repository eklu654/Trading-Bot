"""Causal TQQQ swing research: dynamic exits, pullbacks, breakouts, and regime states.
Signals use QQQ close only; TQQQ executes at the next open. This is hypothesis generation,
not an OOS proof.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_daily_returns

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-07"

def dl(sym):
    x=yf.download(sym,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})[["open","close","adj_close"]].sort_index().dropna()

def returns(t):
    ao=t.open*t.adj_close/t.close
    return (ao/t.adj_close.shift(1)-1).fillna(0),(t.adj_close/ao-1).fillna(0)

def run_signal(p, kind):
    m5=p.pct_change(5); m10=p.pct_change(10); m20=p.pct_change(20)
    ma10=p.rolling(10).mean(); ma20=p.rolling(20).mean(); ma50=p.rolling(50).mean(); ma100=p.rolling(100).mean()
    hi20=p.shift(1).rolling(20).max(); hi50=p.shift(1).rolling(50).max()
    lo5=p.shift(1).rolling(5).min(); lo10=p.shift(1).rolling(10).min()
    vol=p.pct_change().rolling(20).std()
    volma=vol.rolling(20).mean()
    # state machine: enter on signal at next open; exit on exit condition at next open.
    on=False; age=0; out=[]
    for i in range(len(p)):
        if i<101:
            out.append(0.0); continue
        entry=False; exit_now=False
        if kind=="BREAK20_TRAIL10":
            entry=p.iloc[i]>hi20.iloc[i] and p.iloc[i]>ma50.iloc[i]
            exit_now=p.iloc[i]<ma10.iloc[i]
        elif kind=="BREAK50_TRAIL20":
            entry=p.iloc[i]>hi50.iloc[i] and p.iloc[i]>ma100.iloc[i]
            exit_now=p.iloc[i]<ma20.iloc[i]
        elif kind=="MOM10_TRAIL10":
            entry=m10.iloc[i]>0 and m10.iloc[i]>m10.iloc[i-1] and p.iloc[i]>ma20.iloc[i]
            exit_now=m10.iloc[i]<0 or p.iloc[i]<ma10.iloc[i]
        elif kind=="MOM20_TRAIL10":
            entry=m20.iloc[i]>0 and m20.iloc[i]>m20.iloc[i-1] and p.iloc[i]>ma50.iloc[i]
            exit_now=m20.iloc[i]<0 or p.iloc[i]<ma10.iloc[i]
        elif kind=="TREND_CROSS":
            entry=p.iloc[i]>ma20.iloc[i] and ma20.iloc[i]>ma50.iloc[i] and m10.iloc[i]>0
            exit_now=p.iloc[i]<ma20.iloc[i] or ma20.iloc[i]<ma50.iloc[i]
        elif kind=="TREND_CROSS100":
            entry=p.iloc[i]>ma50.iloc[i] and ma50.iloc[i]>ma100.iloc[i] and m20.iloc[i]>0
            exit_now=p.iloc[i]<ma20.iloc[i] or ma50.iloc[i]<ma100.iloc[i]
        elif kind=="PULLBACK5_TREND":
            entry=p.iloc[i]>ma50.iloc[i] and m5.iloc[i]<-0.015 and p.iloc[i]>p.iloc[i-1]
            exit_now=p.iloc[i]>ma10.iloc[i] or m5.iloc[i]>0
        elif kind=="PULLBACK10_TREND":
            entry=p.iloc[i]>ma100.iloc[i] and m10.iloc[i]<-0.02 and p.iloc[i]>p.iloc[i-1]
            exit_now=p.iloc[i]>ma10.iloc[i] or m10.iloc[i]>0
        elif kind=="MEANREV5":
            entry=m5.iloc[i]<-0.03 and p.iloc[i]>ma100.iloc[i] and p.iloc[i]>p.iloc[i-1]
            exit_now=m5.iloc[i]>0 or p.iloc[i]>ma10.iloc[i]
        elif kind=="MEANREV10":
            entry=m10.iloc[i]<-0.05 and p.iloc[i]>ma100.iloc[i] and p.iloc[i]>p.iloc[i-1]
            exit_now=m10.iloc[i]>0 or p.iloc[i]>ma10.iloc[i]
        elif kind=="VOL_CONTRACT_BREAK":
            entry=p.iloc[i]>hi20.iloc[i] and vol.iloc[i]<volma.iloc[i]
            exit_now=p.iloc[i]<ma10.iloc[i]
        elif kind=="VOL_EXPANSION_BREAK":
            entry=p.iloc[i]>hi20.iloc[i] and vol.iloc[i]>volma.iloc[i]
            exit_now=p.iloc[i]<ma10.iloc[i]
        else:
            raise ValueError(kind)
        if on:
            age+=1
            if exit_now or age>=30:
                on=False; age=0
        if (not on) and entry:
            on=True; age=0
        out.append(float(on))
    return pd.Series(out,index=p.index)

def stat(name,s,d,idx):
    e=INITIAL*np.cumprod(1+d); w=pd.Series(e,index=idx); dd=w/w.cummax()-1
    yrs=(idx[-1]-idx[0]).days/365.25
    return {"strategy":name,"final_balance":float(w.iloc[-1]),"cagr":float((w.iloc[-1]/INITIAL)**(1/yrs)-1),
            "max_drawdown":float(dd.min()),"avg_exposure":float(s.shift(1).fillna(0).mean()),
            "entries":int((s.diff().fillna(0)==1).sum())}

def main():
    q,t=dl("QQQ"),dl("TQQQ"); idx=q.index.intersection(t.index); q,t=q.reindex(idx),t.reindex(idx)
    overnight,intraday=returns(t)
    kinds=["BREAK20_TRAIL10","BREAK50_TRAIL20","MOM10_TRAIL10","MOM20_TRAIL10",
           "TREND_CROSS","TREND_CROSS100","PULLBACK5_TREND","PULLBACK10_TREND",
           "MEANREV5","MEANREV10","VOL_CONTRACT_BREAK","VOL_EXPANSION_BREAK"]
    rows=[]
    for k in kinds:
        s=run_signal(q.adj_close,k)
        rows.append(stat("TQQQ dynamic | "+k,s,next_open_daily_returns(s,overnight,intraday),idx))
    bh=pd.Series(1.,index=idx)
    rows.append(stat("TQQQ BUY&HOLD",bh,next_open_daily_returns(bh,overnight,intraday),idx))
    r=pd.DataFrame(rows).sort_values("final_balance",ascending=False)
    OUT.mkdir(parents=True,exist_ok=True)
    r.to_csv(OUT/"tqqq_swing_dynamic_exit_matrix.csv",index=False)
    print(r.to_string(index=False))

if __name__=="__main__": main()
