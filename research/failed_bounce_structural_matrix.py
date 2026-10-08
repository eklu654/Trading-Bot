"""Expanded failed-bounce structural/regime matrix.

Extends the canonical +10% recovery experiment with:
- shock thresholds 3%, 4%, 4.5%, 5%, 6%
- medium-term 60/120/200-day structural trend features
- composite structural-damage scores
- causal event labels and event-driven TQQQ equity
No AI; QQQ is signal asset, TQQQ is traded asset.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
INITIAL=5000.0; START="2010-01-01"; END="2026-10-08"
NORMAL=.10; FAIL=-.10; SUCCESS=.20; HORIZON=252
SHOCKS=(-.03,-.04,-.045,-.05,-.06)
TARGETS=(.15,.20,.30)

def dl(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def features(p):
    sma={n:p.rolling(n).mean() for n in (10,20,50,60,100,120,150,200)}
    f={}
    for n in (20,60,120):
        f[f"ret{n}"]=p/p.shift(n)-1
        f[f"slope_sma{n}"]=sma[n]/sma[n].shift(20)-1
        f[f"price_vs_sma{n}"]=p/sma[n]-1
    f["state_60_120"]=sma[60]/sma[120]-1
    f["state_60_200"]=sma[60]/sma[200]-1
    f["state_120_200"]=sma[120]/sma[200]-1
    f["sma60_slope60"]=sma[60]/sma[60].shift(60)-1
    f["sma120_slope60"]=sma[120]/sma[120].shift(60)-1
    f["sma200_slope60"]=sma[200]/sma[200].shift(60)-1
    # Structural damage score: independent medium/long-term bearish conditions.
    conds=[
        f["ret60"]<0, f["ret120"]<0,
        f["slope_sma60"]<0, f["slope_sma120"]<0,
        f["price_vs_sma60"]<0, f["price_vs_sma120"]<0,
        f["state_60_120"]<0, f["state_60_200"]<0,
        f["state_120_200"]<0, f["sma60_slope60"]<0,
        f["sma120_slope60"]<0,
    ]
    f["structural_score"]=sum(c.astype(int) for c in conds)
    f["damage_ge6"]=(f["structural_score"]>=6).astype(int)
    f["damage_ge7"]=(f["structural_score"]>=7).astype(int)
    f["damage_ge8"]=(f["structural_score"]>=8).astype(int)
    # A stricter secular-bear proxy: 60/120/200 hierarchy all damaged.
    f["secular_bear"]=((
        (f["ret120"]<0)&(f["slope_sma60"]<0)&(f["slope_sma120"]<0)&
        (f["state_60_120"]<0)&(f["state_120_200"]<0)&
        (f["price_vs_sma120"]<0))).astype(int)
    # Repair-versus-structure: short-term improvement while medium/long damage remains.
    f["repair_damage"]=((
        (f["ret20"]>0)&(f["ret60"]<0)&(f["state_60_120"]<0)&
        (f["state_120_200"]<0))).astype(int)
    return pd.DataFrame(f,index=p.index)

def events(p,shock):
    r=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy()
    armed=False; low=np.nan; li=None; out=[]
    for i in range(1,len(p)):
        if not armed and r[i]<=shock:
            armed=True; low=px[i]; li=i
        if armed:
            if px[i]<low: low=px[i]; li=i
            if px[i]/low-1>=NORMAL:
                out.append({"decision_i":i,"decision_date":p.index[i].date(),
                    "low_i":li,"low_date":p.index[li].date(),"speed_days":i-li})
                armed=False
    return out

def label(p,e):
    i=e["decision_i"]; base=float(p.iloc[i]); end=min(len(p)-1,i+HORIZON)
    z=p.iloc[i+1:end+1].to_numpy()/base-1
    a=np.where(z<=FAIL)[0]; b=np.where(z>=SUCCESS)[0]
    if not len(a) and not len(b): return "censored",None,None
    ai=int(a[0]) if len(a) else 10**9; bi=int(b[0]) if len(b) else 10**9
    if ai<bi: return "failed",ai+1,float(z[ai])
    return "successful",bi+1,float(z[bi])

def event_frame(p,f,shock):
    rows=[]
    for e in events(p,shock):
        lab,d,r=label(p,e); i=e["decision_i"]
        row={"shock":-shock,"shock_pct":shock,**e,"label":lab,"label_days":d,"label_return":r}
        for k,v in f.iloc[i].items(): row[k]=float(v) if np.isfinite(v) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)

def rules():
    return {
      "ret60_negative":lambda r:r.ret60<0,
      "ret120_negative":lambda r:r.ret120<0,
      "sma60_slope_negative":lambda r:r.slope_sma60<0,
      "sma120_slope_negative":lambda r:r.slope_sma120<0,
      "60_120_bear":lambda r:r.state_60_120<0,
      "120_200_bear":lambda r:r.state_120_200<0,
      "price_below_120":lambda r:r.price_vs_sma120<0,
      "damage_ge6":lambda r:r.structural_score>=6,
      "damage_ge7":lambda r:r.structural_score>=7,
      "damage_ge8":lambda r:r.structural_score>=8,
      "secular_bear":lambda r:r.secular_bear==1,
      "repair_damage":lambda r:r.repair_damage==1,
      "repair_and_damage6":lambda r:r.repair_damage==1 and r.structural_score>=6,
      "repair_and_damage7":lambda r:r.repair_damage==1 and r.structural_score>=7,
      "repair_and_damage8":lambda r:r.repair_damage==1 and r.structural_score>=8,
    }

def equity(p,t,shock,rule=None,target=.10,flagged_exposure=0.0):
    qr=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy(); ar=t.pct_change().fillna(0).to_numpy()
    f=features(p); invested=np.ones(len(p)); armed=False; low=np.nan; flagged=False
    for i in range(1,len(p)):
        if not armed and qr[i]<=shock:
            armed=True; low=px[i]; flagged=False
        if armed:
            if px[i]<low: low=px[i]
            gain=px[i]/low-1
            if not flagged and gain>=NORMAL:
                if rule is not None:
                    row=f.iloc[i]
                    try: flagged=np.isfinite(row.to_numpy(float)).all() and bool(rule(row))
                    except Exception: flagged=False
            invested[i]=flagged_exposure if flagged else 0.0
            if gain>=NORMAL:
                armed=False; low=np.nan
        else:
            invested[i]=1.0
    ex=np.roll(invested,1); ex[0]=1.0
    return INITIAL*np.cumprod(1+ex*ar)

"""Expanded failed-bounce structural/regime matrix.

Extends the canonical +10% recovery experiment with:
- shock thresholds 3%, 4%, 4.5%, 5%, 6%
- medium-term 60/120/200-day structural trend features
- composite structural-damage scores
- causal event labels and event-driven TQQQ equity
No AI; QQQ is signal asset, TQQQ is traded asset.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
INITIAL=5000.0; START="2010-01-01"; END="2026-10-08"
NORMAL=.10; FAIL=-.10; SUCCESS=.20; HORIZON=252
SHOCKS=(-.03,-.04,-.045,-.05,-.06)
TARGETS=(.15,.20,.30)

def dl(symbol):
    x=yf.download(symbol,start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def features(p):
    sma={n:p.rolling(n).mean() for n in (10,20,50,60,100,120,150,200)}
    f={}
    for n in (20,60,120):
        f[f"ret{n}"]=p/p.shift(n)-1
        f[f"slope_sma{n}"]=sma[n]/sma[n].shift(20)-1
        f[f"price_vs_sma{n}"]=p/sma[n]-1
    f["state_60_120"]=sma[60]/sma[120]-1
    f["state_60_200"]=sma[60]/sma[200]-1
    f["state_120_200"]=sma[120]/sma[200]-1
    f["sma60_slope60"]=sma[60]/sma[60].shift(60)-1
    f["sma120_slope60"]=sma[120]/sma[120].shift(60)-1
    f["sma200_slope60"]=sma[200]/sma[200].shift(60)-1
    # Structural damage score: independent medium/long-term bearish conditions.
    conds=[
        f["ret60"]<0, f["ret120"]<0,
        f["slope_sma60"]<0, f["slope_sma120"]<0,
        f["price_vs_sma60"]<0, f["price_vs_sma120"]<0,
        f["state_60_120"]<0, f["state_60_200"]<0,
        f["state_120_200"]<0, f["sma60_slope60"]<0,
        f["sma120_slope60"]<0,
    ]
    f["structural_score"]=sum(c.astype(int) for c in conds)
    f["damage_ge6"]=(f["structural_score"]>=6).astype(int)
    f["damage_ge7"]=(f["structural_score"]>=7).astype(int)
    f["damage_ge8"]=(f["structural_score"]>=8).astype(int)
    # A stricter secular-bear proxy: 60/120/200 hierarchy all damaged.
    f["secular_bear"]=((
        (f["ret120"]<0)&(f["slope_sma60"]<0)&(f["slope_sma120"]<0)&
        (f["state_60_120"]<0)&(f["state_120_200"]<0)&
        (f["price_vs_sma120"]<0))).astype(int)
    # Repair-versus-structure: short-term improvement while medium/long damage remains.
    f["repair_damage"]=((
        (f["ret20"]>0)&(f["ret60"]<0)&(f["state_60_120"]<0)&
        (f["state_120_200"]<0))).astype(int)
    return pd.DataFrame(f,index=p.index)

def events(p,shock):
    r=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy()
    armed=False; low=np.nan; li=None; out=[]
    for i in range(1,len(p)):
        if not armed and r[i]<=shock:
            armed=True; low=px[i]; li=i
        if armed:
            if px[i]<low: low=px[i]; li=i
            if px[i]/low-1>=NORMAL:
                out.append({"decision_i":i,"decision_date":p.index[i].date(),
                    "low_i":li,"low_date":p.index[li].date(),"speed_days":i-li})
                armed=False
    return out

def label(p,e):
    i=e["decision_i"]; base=float(p.iloc[i]); end=min(len(p)-1,i+HORIZON)
    z=p.iloc[i+1:end+1].to_numpy()/base-1
    a=np.where(z<=FAIL)[0]; b=np.where(z>=SUCCESS)[0]
    if not len(a) and not len(b): return "censored",None,None
    ai=int(a[0]) if len(a) else 10**9; bi=int(b[0]) if len(b) else 10**9
    if ai<bi: return "failed",ai+1,float(z[ai])
    return "successful",bi+1,float(z[bi])

def event_frame(p,f,shock):
    rows=[]
    for e in events(p,shock):
        lab,d,r=label(p,e); i=e["decision_i"]
        row={"shock":-shock,"shock_pct":shock,**e,"label":lab,"label_days":d,"label_return":r}
        for k,v in f.iloc[i].items(): row[k]=float(v) if np.isfinite(v) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)

def rules():
    return {
      "ret60_negative":lambda r:r.ret60<0,
      "ret120_negative":lambda r:r.ret120<0,
      "sma60_slope_negative":lambda r:r.slope_sma60<0,
      "sma120_slope_negative":lambda r:r.slope_sma120<0,
      "60_120_bear":lambda r:r.state_60_120<0,
      "120_200_bear":lambda r:r.state_120_200<0,
      "price_below_120":lambda r:r.price_vs_sma120<0,
      "damage_ge6":lambda r:r.structural_score>=6,
      "damage_ge7":lambda r:r.structural_score>=7,
      "damage_ge8":lambda r:r.structural_score>=8,
      "secular_bear":lambda r:r.secular_bear==1,
      "repair_damage":lambda r:r.repair_damage==1,
      "repair_and_damage6":lambda r:r.repair_damage==1 and r.structural_score>=6,
      "repair_and_damage7":lambda r:r.repair_damage==1 and r.structural_score>=7,
      "repair_and_damage8":lambda r:r.repair_damage==1 and r.structural_score>=8,
    }

def equity(p,t,shock,rule=None,target=.10):
    qr=p.pct_change().fillna(0).to_numpy(); px=p.to_numpy(); ar=t.pct_change().fillna(0).to_numpy()
    f=features(p); invested=np.ones(len(p)); armed=False; low=np.nan; required=NORMAL
    for i in range(1,len(p)):
        if not armed and qr[i]<=shock:
            armed=True; low=px[i]; required=NORMAL
        if armed:
            if px[i]<low: low=px[i]
            gain=px[i]/low-1
            if required==NORMAL and gain>=NORMAL:
                flag=False
                if rule is not None:
                    row=f.iloc[i]
                    try: flag=np.isfinite(row.to_numpy(float)).all() and bool(rule(row))
                    except Exception: flag=False
                required=target if flag else NORMAL
            if gain>=required:
                armed=False; low=np.nan; required=NORMAL
            else: invested[i]=0
    ex=np.roll(invested,1); ex[0]=1
    return INITIAL*np.cumprod(1+ex*ar)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    q=dl("QQQ"); t=dl("TQQQ"); idx=q.index.intersection(t.index)
    p=q.reindex(idx)["Close"].squeeze().astype(float); t=t.reindex(idx)["Close"].squeeze().astype(float)
    f=features(p); all_events=[]; stats=[]; full=[]
    rdefs=rules()
    for shock in SHOCKS:
        ev=event_frame(p,f,shock); all_events.append(ev)
        lab=ev[ev.label!="censored"] if len(ev) else ev
        base=(lab.label=="failed").mean() if len(lab) else np.nan
        for name,fn in rdefs.items():
            flag=lab.apply(fn,axis=1) if len(lab) else pd.Series(dtype=bool)
            n=int(flag.sum()); fail=int(((lab.label=="failed")&flag).sum()) if len(lab) else 0
            succ=int(((lab.label=="successful")&flag).sum()) if len(lab) else 0
            stats.append({"shock_pct":-shock,"rule":name,"events":len(ev),"resolved":len(lab),
              "base_fail_rate":base,"flagged":n,"failed_flagged":fail,"success_flagged":succ,
              "fail_rate_flagged":fail/n if n else np.nan})
        years=(p.index[-1]-p.index[0]).days/365.25
        bh=INITIAL*np.cumprod(1+t.pct_change().fillna(0).to_numpy())[-1]
        full.append({"shock_pct":-shock,"strategy":"baseline","target":10,
                     "final_balance":float(equity(p,t,shock)[-1]),"cagr":np.nan})
        for name,fn in rdefs.items():
            for target in TARGETS:
                eq=equity(p,t,shock,fn,target)
                full.append({"shock_pct":-shock,"strategy":name,"target":int(target*100),
                  "final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(1/years)-1)})
    events_df=pd.concat([x for x in all_events if len(x)],ignore_index=True)
    events_df.to_csv(OUT/"failed_bounce_structural_events.csv",index=False)
    pd.DataFrame(stats).to_csv(OUT/"failed_bounce_structural_signal_stats.csv",index=False)
    full_df=pd.DataFrame(full).sort_values("final_balance",ascending=False)
    full_df.to_csv(OUT/"failed_bounce_structural_strategy_full.csv",index=False)
    print("\nEVENT COUNTS / FAILURE RATES")
    print(events_df.groupby("shock_pct").apply(lambda x: pd.Series({"events":len(x),"resolved":(x.label!="censored").sum(),"failed":(x.label=="failed").sum(),"fail_rate":(x.label=="failed").sum()/max(1,(x.label!="censored").sum())})).to_string())
    print("\nTOP STRATEGIES")
    print(full_df.head(30).to_string(index=False))
    print("\nBEST SIGNAL SEPARATION")
    print(pd.DataFrame(stats).sort_values(["fail_rate_flagged","flagged"],ascending=[False,False]).head(30).to_string(index=False))
    print("\nCANONICAL 4.5% EVENT SNAPSHOT")
    print(events_df[events_df.shock_pct==4.5][["decision_date","low_date","speed_days","label","ret60","ret120","slope_sma60","slope_sma120","state_60_120","state_120_200","structural_score","secular_bear","repair_damage"]].to_string(index=False))

if __name__=="__main__": main()    rows=[]
    for shock in SHOCKS:
        for name,rule in rules().items():
            for exposure in [0.25,0.50,0.75]:
                eq=equity(p,t,shock,rule=rule,flagged_exposure=exposure)
                rows.append({"shock_pct":shock,"strategy":name,"target":10,"flagged_exposure":exposure,"final_balance":float(eq[-1]),"cagr":float((eq[-1]/INITIAL)**(252/max(1,len(eq)-1))-1)})
    pd.DataFrame(rows).to_csv(OUT/"failed_bounce_structural_partial_exposure.csv",index=False)

