from pathlib import Path
import itertools
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"research"
INITIAL=5000.0
DMAS=(100,125,150,175,200,225,250,300)
GRID=(.005,.01,.02,.03,.05,.075,.10,.15,.20)
EXPOSURES=(0,.25,.5,.75)
THRESHOLDS=tuple(itertools.combinations(GRID,3))
WEIGHTS=tuple(w for w in itertools.product(EXPOSURES,repeat=4) if w[0]>=w[1]>=w[2]>=w[3])
WINDOWS=(
 ("2018","2019-01-01","2020-12-31","2018-12-31"),
 ("2020","2021-01-01","2022-12-31","2020-12-31"),
 ("2022","2023-01-01","2024-12-31","2022-12-31"),
 ("2024","2025-01-01","2026-10-02","2024-12-31"),
)

def frame():
    x=pd.read_csv(DATA/"tqqq_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index()
    x=x.loc["2010-03-11":"2026-10-02"].copy()
    if len(x)!=4167: raise RuntimeError(f"Expected 4167 rows, got {len(x)}")
    x["adj_open"]=x["open"]*x["adj_close"]/x["close"]
    return x

def exposure(x,dma,t,w):
    ma=x.adj_close.rolling(dma).mean().shift(1)
    d=x.adj_close.shift(1)/ma-1
    a=np.zeros(len(x))
    v=ma.notna().to_numpy(); z=d.to_numpy()
    a[v&(z>=0)]=1
    lows=-np.array(t)
    masks=(v&(z<0)&(z>=lows[0]),v&(z<lows[0])&(z>=lows[1]),v&(z<lows[1])&(z>=lows[2]),v&(z<lows[2]))
    for m,q in zip(masks,w): a[m]=q
    return a

def metrics(x,a):
    oo=(x.adj_open/x.adj_close.shift(1)-1).fillna(0).to_numpy()
    ii=(x.adj_close/x.adj_open-1).fillna(0).to_numpy()
    prev=np.roll(a,1); prev[0]=0
    r=(1+prev*oo)*(1+a*ii)-1; r[0]=0
    eq=INITIAL*np.cumprod(1+r); dd=eq/np.maximum.accumulate(eq)-1
    years=max((x.index[-1]-x.index[0]).days/365.25,1/365.25)
    return float(eq[-1]),float((eq[-1]/INITIAL)**(1/years)-1),float(dd.min()),float(a.mean())

def matrix(x):
    rows=[]
    for dma,t,w in itertools.product(DMAS,THRESHOLDS,WEIGHTS):
        rows.append((dma,*t,*w,*metrics(x,exposure(x,dma,t,w))))
    return pd.DataFrame(rows,columns=["dma","t1","t2","t3","w1","w2","w3","w4","final","cagr","dd","avg"])

def choose(m,limit):
    q=m if limit is None else m[m.dd>=limit]
    if q.empty: raise RuntimeError(f"No candidate satisfies DD limit {limit}")
    return q.sort_values(["final","cagr","dd"],ascending=[False,False,False]).iloc[0]

def main():
    x=frame(); out=[]
    for name,test_start,test_end,train_end in WINDOWS:
        train=matrix(x.loc[:train_end])
        test=x.loc[test_start:test_end]
        for objective,limit in (("WEALTH",None),("DD50",-0.50),("DD60",-0.60)):
            row=choose(train,limit)
            t=(row.t1,row.t2,row.t3); w=(row.w1,row.w2,row.w3,row.w4)
            full_a=exposure(x,int(row.dma),t,w)
            test_a=full_a[x.index.get_indexer(test.index)]
            final,cagr,dd,avg=metrics(test,test_a)
            out.append({"window":name,"objective":objective,"dma":int(row.dma),"t1_pct":row.t1*100,"t2_pct":row.t2*100,"t3_pct":row.t3*100,"w1_pct":row.w1*100,"w2_pct":row.w2*100,"w3_pct":row.w3*100,"w4_pct":row.w4*100,"train_final":row.final,"train_dd":row.dd,"test_final":final,"test_cagr":cagr,"test_dd":dd,"test_avg_exposure":avg})
        binary_full=exposure(x,200,(.005,.01,.02),(0,0,0,0))
        binary_test=binary_full[x.index.get_indexer(test.index)]
        for label,a in (("BUY_AND_HOLD",np.ones(len(test))),("200DMA_BINARY",binary_test)):
            final,cagr,dd,avg=metrics(test,a)
            out.append({"window":name,"objective":label,"test_final":final,"test_cagr":cagr,"test_dd":dd,"test_avg_exposure":avg})
    result=pd.DataFrame(out)
    result.to_csv(DATA/"tqqq_partial_exposure_walk_forward.csv",index=False)
    print(result.to_string(index=False))

if __name__=="__main__":
    main()
