from pathlib import Path
import numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"research"; INITIAL=5000.0
WINDOWS=(("2018","2019-01-01","2020-12-31"),("2020","2021-01-01","2022-12-31"),("2022","2023-01-01","2024-12-31"),("2024","2025-01-01","2026-10-02"))
DMAS=(100,125,150,175,200,225,250,300); BELOW=(0,.25,.5,.75,1.0)

def frame():
 x=pd.read_csv(DATA/"tqqq_daily.csv",parse_dates=["Date"]).set_index("Date").sort_index().loc["2010-03-11":"2026-10-02"].copy()
 if len(x)!=4186: raise RuntimeError(f"Expected 4186 observations, got {len(x)}")
 x["adj_open"]=x["open"]*x["adj_close"]/x["close"]; return x

def returns(x,dma,below):
 ma=x.adj_close.rolling(dma).mean().shift(1)
 target=np.where(ma.notna() & (x.adj_close.shift(1)>=ma),1.0,below)
 target=np.where(ma.notna(),target,0.0)
 oo=(x.adj_open/x.adj_close.shift(1)-1).fillna(0).to_numpy()
 ii=(x.adj_close/x.adj_open-1).fillna(0).to_numpy()
 p=np.roll(target,1); p[0]=0
 r=(1+p*oo)*(1+target*ii)-1; r[0]=0
 return r

def main():
 x=frame(); rows=[]; windows=[]
 for dma in DMAS:
  for below in BELOW:
   label=f"DMA{dma}_BELOW{int(below*100)}"
   r=returns(x,dma,below); equity=INITIAL; peak=INITIAL; maxdd=0
   for name,start,end in WINDOWS:
    mask=(x.index>=pd.Timestamp(start))&(x.index<=pd.Timestamp(end)); eq=equity*np.cumprod(1+r[mask]); equity=float(eq[-1])
    running=np.maximum.accumulate(np.r_[peak,eq])[1:]; maxdd=min(maxdd,float((eq/running-1).min())); peak=max(peak,float(eq.max()))
    windows.append((label,dma,below,name,equity))
   years=(pd.Timestamp("2026-10-02")-pd.Timestamp("2019-01-01")).days/365.25
   rows.append((label,dma,below,equity,(equity/INITIAL)**(1/years)-1,maxdd))
 out=pd.DataFrame(rows,columns=["strategy","dma","below_exposure","stitched_final","stitched_cagr","stitched_dd"]).sort_values("stitched_final",ascending=False)
 out.to_csv(DATA/"tqqq_fixed_partial_oos_stitched.csv",index=False)
 pd.DataFrame(windows,columns=["strategy","dma","below_exposure","window","ending_equity"]).to_csv(DATA/"tqqq_fixed_partial_oos_stitched_windows.csv",index=False)
 print(out.to_string(index=False))
if __name__=="__main__": main()
