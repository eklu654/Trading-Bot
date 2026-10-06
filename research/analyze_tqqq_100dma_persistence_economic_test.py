"""Walk-forward economic test of persistence-informed re-entry.

Frozen exit: 100-DMA, 0% exposure below, next-open execution.
At each exit, train only on prior completed episodes. If the model estimates
>=50% probability that the defensive episode will last >=20 trading days,
re-entry requires 5 consecutive QQQ closes at/above the 100-DMA; otherwise
re-entry remains immediate.

The 50% probability and 5-day confirmation are predeclared hypothesis values,
not optimized here. This is a single economic-value test, not a parameter sweep.
"""
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
START="1999-03-10"; END="2026-10-04"; DMA=100; INITIAL=5000.0
FEATURES=["dma_gap_at_exit","dma_slope_20d_at_exit","qqq_return_5d_at_exit",
          "qqq_return_20d_at_exit","qqq_return_60d_at_exit","qqq_realized_vol_20d_at_exit"]

def download():
    x=yf.download("QQQ",start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x=x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"})
    x.index=pd.to_datetime(x.index).tz_localize(None); x.index.name="Date"
    return x.sort_index().dropna(subset=["open","close","adj_close"])

def build(x):
    x=x.copy(); x["adj_open"]=x.open*x.adj_close/x.close
    overnight=(x.adj_open/x.adj_close.shift(1)-1).fillna(0)
    intraday=(x.adj_close/x.adj_open-1).fillna(0)
    x["overnight_3x"]=np.clip(1+3*overnight,0,None)-1
    x["intraday_3x"]=np.clip(1+3*intraday,0,None)-1
    x["dma"]=x.adj_close.rolling(DMA).mean()
    x["active"]=(x.adj_close>=x.dma).astype(float); x.loc[x.index[:DMA-1],"active"]=0
    w=x.active.to_numpy(); prev=np.roll(w,1); prev[0]=0
    daily=(1+prev*x.overnight_3x.to_numpy())*(1+w*x.intraday_3x.to_numpy())-1
    x["baseline_daily"]=daily
    x["bh_daily"]=(1+x.overnight_3x)*(1+x.intraday_3x)-1
    x["dma_gap"]=x.adj_close/x.dma-1
    x["dma_slope20"]=x.dma/x.dma.shift(20)-1
    r=x.adj_close.pct_change()
    x["r5"]=x.adj_close/x.adj_close.shift(5)-1
    x["r20"]=x.adj_close/x.adj_close.shift(20)-1
    x["r60"]=x.adj_close/x.adj_close.shift(60)-1
    x["rv20"]=r.rolling(20).std()*np.sqrt(252)
    return x

def episodes(x):
    exits=x.index[(x.active==0)&(x.active.shift(1)==1)]
    rows=[]
    for d in exits:
        i=x.index.get_loc(d); j=i+1
        while j<len(x) and x.active.iloc[j]==0: j+=1
        if j>=len(x): continue
        rows.append({
            "exit_date":d,"baseline_reentry":x.index[j],
            "flat_days":j-i-1,
            "dma_gap_at_exit":x.dma_gap.iloc[i],
            "dma_slope_20d_at_exit":x.dma_slope20.iloc[i],
            "qqq_return_5d_at_exit":x.r5.iloc[i],
            "qqq_return_20d_at_exit":x.r20.iloc[i],
            "qqq_return_60d_at_exit":x.r60.iloc[i],
            "qqq_realized_vol_20d_at_exit":x.rv20.iloc[i],
        })
    return pd.DataFrame(rows)

def model_for(prior):
    y=(prior.flat_days>=20).astype(int)
    if len(prior)<30 or y.nunique()<2: return None
    m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=2000))
    m.fit(prior[FEATURES],y); return m

def simulate(x, ep):
    # Baseline is the frozen 100-DMA strategy. Adaptive changes only re-entry.
    base=INITIAL; adapt=INITIAL
    base_equity=[]; adapt_equity=[]; pos_a=0
    ep_by_exit={r.exit_date:r for _,r in ep.iterrows()}
    pending=None; above_count=0
    for i,d in enumerate(x.index):
        # Decide exits at today's close for next open. During an episode, adaptive
        # uses only information known at the exit and subsequent closes.
        if d in ep_by_exit:
            r=ep_by_exit[d]; prior=ep[ep.exit_date<d]
            m=model_for(prior)
            p=float(m.predict_proba(pd.DataFrame([r])[FEATURES])[:,1][0]) if m else 0.0
            pending={"persistent":p>=0.50,"p":p,"exit_idx":i}
            above_count=0
        if pending is not None and pos_a==0:
            if pending["persistent"]:
                if x.adj_close.iloc[i] >= x.dma.iloc[i]: above_count+=1
                else: above_count=0
                if above_count>=5: pos_a=1; pending=None
            else:
                if x.adj_close.iloc[i] >= x.dma.iloc[i]: pos_a=1; pending=None
        elif pending is None and i>=DMA and x.adj_close.iloc[i]>=x.dma.iloc[i]:
            pos_a=1
        # Baseline next-open mechanics are represented by weight from previous close.
        if i>0:
            base*=1+x.baseline_daily.iloc[i]
            # adaptive overnight/intraday: position decided from prior close.
            prev_pos=0
            if d in ep_by_exit: prev_pos=0
            else:
                # derive current position from prior day's state
                prev_pos=1 if (x.adj_close.iloc[i-1]>=x.dma.iloc[i-1] and
                                not any(False for _ in [])) else 0
            # This shortcut is replaced below by explicit state tracking.
        base_equity.append(base)
    # Re-simulate explicitly for adaptive and baseline positions.
    b=a=INITIAL; bp=ap=0; pending=None; above=0; rows=[]
    for i,d in enumerate(x.index):
        if i==0: rows.append((d,b,a,bp,ap)); continue
        if d in ep_by_exit:
            r=ep_by_exit[d]; prior=ep[ep.exit_date<d]; m=model_for(prior)
            p=float(m.predict_proba(pd.DataFrame([r])[FEATURES])[:,1][0]) if m else 0
            pending=(p>=.50); above=0; bp=0; ap=0
        # today's overnight uses yesterday's position
        b*=1+(x.overnight_3x.iloc[i] if bp else 0)
        a*=1+(x.overnight_3x.iloc[i] if ap else 0)
        # close determines next day's position
        if x.adj_close.iloc[i]>=x.dma.iloc[i] and not np.isnan(x.dma.iloc[i]):
            bp=1
        else: bp=0
        if pending is not None and ap==0:
            if pending:
                above=above+1 if x.adj_close.iloc[i]>=x.dma.iloc[i] else 0
                if above>=5: ap=1; pending=None
            else:
                if x.adj_close.iloc[i]>=x.dma.iloc[i]: ap=1; pending=None
        # intraday return applies today's newly established? Next-open means prior close position;
        # therefore intraday should use prior position, so use old state. Correct by applying
        # intraday based on saved pre-close positions.
        rows.append((d,b,a,bp,ap))
    # Rebuild with correct next-open state in one pass.
    b=a=INITIAL; bp=ap=0; pending=None; above=0; rec=[]
    for i,d in enumerate(x.index):
        if i==0:
            rec.append((d,b,a)); continue
        # exit signal from prior close controls today's open
        if x.adj_close.iloc[i-1]<x.dma.iloc[i-1] if not np.isnan(x.dma.iloc[i-1]) else False:
            bp=0
        else:
            bp=1 if bp or (x.adj_close.iloc[i-1]>=x.dma.iloc[i-1]) else 0
        if d in ep_by_exit:
            r=ep_by_exit[d]; prior=ep[ep.exit_date<d]; m=model_for(prior)
            p=float(m.predict_proba(pd.DataFrame([r])[FEATURES])[:,1][0]) if m else 0
            pending=(p>=.50); above=0; ap=0
        b*=1+(bp*x.overnight_3x.iloc[i]) ; b*=1+(bp*x.intraday_3x.iloc[i])
        if ap: a*=1+x.overnight_3x.iloc[i]; a*=1+x.intraday_3x.iloc[i]
        # position for next day after today's close
        if not np.isnan(x.dma.iloc[i]):
            if pending is not None and ap==0:
                if pending:
                    above=above+1 if x.adj_close.iloc[i]>=x.dma.iloc[i] else 0
                    if above>=5: ap=1; pending=None
                else:
                    if x.adj_close.iloc[i]>=x.dma.iloc[i]: ap=1; pending=None
            elif pending is None:
                ap=1 if x.adj_close.iloc[i]>=x.dma.iloc[i] else 0
        rec.append((d,b,a))
    out=pd.DataFrame(rec,columns=["Date","baseline","adaptive"]).set_index("Date")
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x=build(download()); ep=episodes(x)
    out=simulate(x,ep)
    summary=pd.DataFrame([{
        "strategy":"baseline_100dma_immediate",
        "ending_balance":out.baseline.iloc[-1],
        "cagr":(out.baseline.iloc[-1]/INITIAL)**(252/len(out))-1,
        "max_drawdown":(out.baseline/out.baseline.cummax()-1).min()
    },{
        "strategy":"walkforward_persistence_adaptive",
        "ending_balance":out.adaptive.iloc[-1],
        "cagr":(out.adaptive.iloc[-1]/INITIAL)**(252/len(out))-1,
        "max_drawdown":(out.adaptive/out.adaptive.cummax()-1).min()
    }])
    out.to_csv(OUT/"tqqq_100dma_persistence_adaptive_equity.csv")
    summary.to_csv(OUT/"tqqq_100dma_persistence_adaptive_summary.csv",index=False)
    print(summary.to_string(index=False))
if __name__=="__main__": main()
