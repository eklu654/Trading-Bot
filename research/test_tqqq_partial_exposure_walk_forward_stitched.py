from pathlib import Path
import itertools, numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"research"; INITIAL=5000.0
WINDOWS=(("2018","2019-01-01","2020-12-31","2018-12-31"),("2020","2021-01-01","2022-12-31","2020-12-31"),("2022","2023-01-01","2024-12-31","2022-12-31"),("2024","2025-01-01","2026-10-02","2024-12-31"))
DMAS=(100,125,150,175,200,225,250,300); GRID=(.005,.01,.02,.03,.05,.075,.10,.15,.20); EXP=(0,.25,.5,.75)
THRESHOLDS=tuple(itertools.combinations(GRID,3)); WEIGHTS=tuple(w for w in itertools.product(EXP,repeat=4) if w[0]>=w[1]>=w[2]>=w[3])
def frame():
 x=pd.read_csv(DATA/"tqqq_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index().loc["2010-03-11":"2026-10-02"].copy()
 if len(x)!=4167: raise RuntimeError(f"Expected 4167 observations, got {len(x)}")
 x["adj_open"]=x["open"]*x["adj_close"]/x["close"]; return x
def exposure(x,dma,t,w):
 ma=x.adj_close.rolling(dma).mean().shift(1); d=x.adj_close.shift(1)/ma-1; a=np.zeros(len(x)); v=ma.notna().to_numpy(); z=d.to_numpy(); a[v&(z>=0)]=1
 lows=-np.array(t); ms=(v&(z<0)&(z>=lows[0]),v&(z<lows[0])&(z>=lows[1]),v&(z<lows[1])&(z>=lows[2]),v&(z<lows[2]))
 for m,q in zip(ms,w): a[m]=q
 return a
def daily_returns(x,a):
 if len(x)!=len(a): raise ValueError("Exposure length must match dataframe length")
 oo=(x.adj_open/x.adj_close.shift(1)-1).fillna(0).to_numpy(); ii=(x.adj_close/x.adj_open-1).fillna(0).to_numpy(); p=np.roll(a,1); p[0]=0
 r=(1+p*oo)*(1+a*ii)-1; r[0]=0; return r
def matrix(x):
 rows=[]
 for dma,t,w in itertools.product(DMAS,THRESHOLDS,WEIGHTS):
  a=exposure(x,dma,t,w); r=daily_returns(x,a); eq=INITIAL*np.cumprod(1+r); dd=eq/np.maximum.accumulate(eq)-1
  rows.append((dma,*t,*w,eq[-1],dd.min()))
 return pd.DataFrame(rows,columns=["dma","t1","t2","t3","w1","w2","w3","w4","final","dd"])
def choose(m,lim):
 q=m if lim is None else m[m.dd>=lim]
 return q.sort_values(["final","dd"],ascending=[False,False]).iloc[0]
def main():
 x=frame(); selected=[]
 for _,_,_,train_end in WINDOWS:
  m=matrix(x.loc[:train_end])
  for obj,lim in (("WEALTH",None),("DD50",-0.5),("DD60",-0.6)):
   q=choose(m,lim); selected.append((obj,int(q.dma),(q.t1,q.t2,q.t3),(q.w1,q.w2,q.w3,q.w4)))
 strategies=[("BUY_AND_HOLD",None),("200DMA_BINARY",(200,(0.005,0.01,0.02),(0,0,0,0)))]
 for obj,dma,t,w in selected: strategies.append((f"WF_{obj}",(dma,t,w)))
 full_returns={}
 for label,params in strategies:
  a=np.ones(len(x)) if label=="BUY_AND_HOLD" else exposure(x,*params)
  full_returns[label]=daily_returns(x,a)
 rows=[]; stitched=[]
 for label,_ in strategies:
  equity=INITIAL; peak=INITIAL; maxdd=0.0; details=[]; r_full=full_returns[label]
  for name,start,end,_ in WINDOWS:
   mask=(x.index>=pd.Timestamp(start))&(x.index<=pd.Timestamp(end)); r=r_full[mask]; eq=equity*np.cumprod(1+r); equity=float(eq[-1])
   running_peak=np.maximum.accumulate(np.r_[peak,eq])[1:]; maxdd=min(maxdd,float((eq/running_peak-1).min())); peak=max(peak,float(eq.max())); details.append((name,equity))
  years=(pd.Timestamp("2026-10-02")-pd.Timestamp("2019-01-01")).days/365.25; cagr=(equity/INITIAL)**(1/years)-1
  rows.append((label,equity,cagr,maxdd)); stitched.extend((label,n,e) for n,e in details)
 result=pd.DataFrame(rows,columns=["strategy","stitched_final","stitched_cagr","stitched_dd"]); result.to_csv(DATA/"tqqq_partial_exposure_walk_forward_stitched.csv",index=False)
 pd.DataFrame(stitched,columns=["strategy","window","ending_equity"]).to_csv(DATA/"tqqq_partial_exposure_walk_forward_stitched_windows.csv",index=False); print(result.to_string(index=False))
if __name__=="__main__": main()
