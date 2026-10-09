"""Signal-only long-history rally audit triggered by 10% S&P 500 drawdowns.

This complementary event family is designed to examine prolonged bear markets
that do not contain a single-day -4.5% shock. It is not a QQQ/TQQQ backtest.
One event is opened when the index crosses below 90% of its trailing 252-day
high. After the +10% recovery decision, no new event is armed until price
regains 95% of the trigger peak, avoiding duplicate labels for one bear market.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
START="1970-01-01"
END="2026-10-08"
DRAWDOWN=-0.10
RECOVERY=0.10
FAIL=-0.10
SUCCESS=0.20
HORIZON=252


def download():
    x=yf.download("^GSPC",start=START,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    x=x.sort_index().dropna()
    return x["Close"].astype(float)


def features(p):
    sma={n:p.rolling(n).mean() for n in (20,50,100,200)}
    ema12=p.ewm(span=12,adjust=False).mean()
    ema26=p.ewm(span=26,adjust=False).mean()
    macd=ema12-ema26
    sig=macd.ewm(span=9,adjust=False).mean()
    hist=macd-sig
    f=pd.DataFrame(index=p.index)
    for n in (20,60,120,200): f[f"return_{n}"]=p/p.shift(n)-1
    for n in (50,100,200):
        f[f"price_vs_sma{n}"]=p/sma[n]-1
        f[f"sma{n}_slope20"]=sma[n]/sma[n].shift(20)-1
        f[f"sma{n}_slope60"]=sma[n]/sma[n].shift(60)-1
    f["sma50_above_sma100"]=(sma[50]>sma[100]).astype(int)
    f["sma100_above_sma200"]=(sma[100]>sma[200]).astype(int)
    f["macd_hist"]=hist
    f["macd_hist_negative"]=(hist<0).astype(int)
    f["macd_below_signal"]=(macd<sig).astype(int)
    f["macd_hist_slope5"]=hist-hist.shift(5)
    f["vol20"]=p.pct_change().rolling(20).std()*np.sqrt(252)
    return f


def label_future(px,i):
    end=min(len(px)-1,i+HORIZON)
    future=px[i+1:end+1]/px[i]-1
    fails=np.flatnonzero(future<=FAIL)
    wins=np.flatnonzero(future>=SUCCESS)
    if not len(fails) and not len(wins): return "censored",None,None
    fi=int(fails[0]) if len(fails) else 10**9
    wi=int(wins[0]) if len(wins) else 10**9
    if fi<wi: return "failed",fi+1,float(future[fi])
    return "successful",wi+1,float(future[wi])


def period(date):
    y=pd.Timestamp(date).year
    if 1970<=y<=1979: return "1970s"
    if y==1987: return "1987"
    if 2000<=y<=2002: return "2000-2002"
    if 2010<=y<=2019: return "2010-2019"
    if 2020<=y<=2021: return "2020-2021"
    if 2022<=y<=2026: return "2022-2026"
    return "other"


def build_events(p,f):
    px=p.to_numpy(float)
    peak=p.rolling(252,min_periods=252).max().to_numpy(float)
    rows=[]
    armed=False
    cooldown_peak=None
    trigger_i=low_i=None
    for i in range(1,len(p)):
        if not armed and cooldown_peak is not None and px[i]>=0.95*cooldown_peak:
            cooldown_peak=None
        prev_dd=px[i-1]/peak[i-1]-1 if np.isfinite(peak[i-1]) else np.nan
        cur_dd=px[i]/peak[i]-1 if np.isfinite(peak[i]) else np.nan
        crossed=(np.isfinite(prev_dd) and np.isfinite(cur_dd)
                 and prev_dd>DRAWDOWN and cur_dd<=DRAWDOWN)
        if not armed and cooldown_peak is None and crossed:
            armed=True; trigger_i=i; low_i=i
            cooldown_peak=float(peak[i])
        if armed:
            if px[i]<px[low_i]: low_i=i
            if px[i]/px[low_i]-1>=RECOVERY:
                lab,days,ret=label_future(px,i)
                row={
                    "trigger_type":"drawdown_10pct",
                    "trigger_date":p.index[trigger_i].date().isoformat(),
                    "trigger_drawdown":float(px[trigger_i]/peak[trigger_i]-1),
                    "low_date":p.index[low_i].date().isoformat(),
                    "decision_date":p.index[i].date().isoformat(),
                    "recovery_speed_days":i-low_i,
                    "label":lab,"label_days":days,"label_return":ret,
                    "period":period(p.index[trigger_i]),
                }
                for k,v in f.iloc[i].items():
                    row[k]=float(v) if pd.notna(v) and np.isfinite(v) else None
                rows.append(row)
                armed=False
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p=download()
    if p.empty: raise RuntimeError("No S&P 500 observations")
    f=features(p)
    ev=build_events(p,f)
    ev.to_csv(OUT/"long_history_drawdown_rally_events.csv",index=False)
    summary=ev.groupby(["period","label"],dropna=False).size().rename("events").reset_index()
    summary.to_csv(OUT/"long_history_drawdown_rally_summary.csv",index=False)
    feature_cols=[c for c in ev.columns if c not in {
        "trigger_type","trigger_date","trigger_drawdown","low_date","decision_date",
        "label","label_days","label_return","period"}]
    resolved=ev[ev.label.isin(["failed","successful"])]
    sep=[]
    for era in ["all","1970s","1987","2000-2002","2010-2019","2020-2021","2022-2026"]:
        z=resolved if era=="all" else resolved[resolved.period==era]
        for col in feature_cols:
            for lab in ["failed","successful"]:
                vals=z.loc[z.label==lab,col].dropna()
                sep.append({"period":era,"feature":col,"label":lab,"n":int(len(vals)),
                            "mean":float(vals.mean()) if len(vals) else None,
                            "median":float(vals.median()) if len(vals) else None})
    pd.DataFrame(sep).to_csv(OUT/"long_history_drawdown_rally_feature_separation.csv",index=False)
    manifest={
        "status":"SIGNAL_ONLY_DIAGNOSTIC",
        "instrument":"S&P 500 index (^GSPC), not QQQ or TQQQ",
        "start":str(p.index[0].date()),"end":str(p.index[-1].date()),"rows":int(len(p)),
        "trigger":"cross below -10% from trailing 252-session high",
        "recovery":"first close >=10% above post-trigger low",
        "rearm":"only after regaining 95% of the trigger peak",
        "label":"within 252 sessions after recovery, -10% before +20%; otherwise censored",
        "event_count":int(len(ev)),
        "label_counts":{str(k):int(v) for k,v in ev.label.value_counts(dropna=False).items()},
        "period_counts":summary.to_dict(orient="records"),
        "warning":"No leveraged ETF portfolio balance is computed; all pre-2010 results are signal-only.",
    }
    (OUT/"long_history_drawdown_rally_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    print("\nEVENT LEDGER")
    print(ev[["trigger_date","trigger_drawdown","low_date","decision_date","recovery_speed_days","label","label_days","period"]].to_string(index=False))


if __name__=="__main__": main()
