"""Research contextual Fed regimes at TQQQ 100-DMA breaks.

Purpose: replace a universal absolute-rate threshold with context-relative
features. This is diagnostic research, not a trading rule.

For each 100-DMA break, compute:
- Fed level percentile over trailing 5y/10y
- Fed level z-score over trailing 5y
- rate percentile over trailing history
- rate change over 3m/6m/12m
- distance from trailing 5y/10y minimum
- whether the Fed is in a tightening/easing/flat cycle
- QQQ 60d trend, DMA slope, volatility and VIX context
- persistence >=20 trading days and severe <=-50% outcomes

Then evaluate chronological walk-forward AUC for contextual Fed features,
market features, and combinations. No threshold optimization is performed.
"""
from pathlib import Path
import numpy as np, pandas as pd
import yfinance as yf
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"/"research"
START="1999-03-10"; END="2026-10-05"

# Same event table used by the established Fed-conditioned study.
FED_EVENTS=[
("1999-06-30",.25,5),("1999-08-24",.25,5.25),("1999-11-16",.25,5.5),
("2000-02-02",.25,5.75),("2000-03-21",.25,6),("2000-05-16",.5,6.5),
("2001-01-03",-.5,6),("2001-01-31",-.5,5.5),("2001-03-20",-.5,5),
("2001-04-18",-.5,4.5),("2001-05-15",-.5,4),("2001-06-27",-.25,3.75),
("2001-08-21",-.25,3.5),("2001-09-17",-.5,3),("2001-10-02",-.5,2.5),
("2001-11-06",-.5,2),("2001-12-11",-.25,1.75),("2002-11-06",-.5,1.25),
("2003-06-25",-.25,1),("2004-06-30",.25,1.25),("2004-08-10",.25,1.5),
("2004-09-21",.25,1.75),("2004-11-10",.25,2),("2004-12-14",.25,2.25),
("2005-02-02",.25,2.5),("2005-03-22",.25,2.75),("2005-05-03",.25,3),
("2005-06-30",.25,3.25),("2005-08-09",.25,3.5),("2005-09-20",.25,3.75),
("2005-11-01",.25,4),("2005-12-13",.25,4.25),("2006-01-31",.25,4.5),
("2006-03-28",.25,4.75),("2006-05-10",.25,5),("2006-06-29",.25,5.25),
("2007-09-18",-.5,4.75),("2007-10-31",-.25,4.5),("2007-12-11",-.25,4.25),
("2008-01-22",-.75,3.5),("2008-01-30",-.5,3),("2008-03-18",-.75,2.25),
("2008-04-30",-.25,2),("2008-10-08",-.5,1.5),("2008-10-29",-.5,1),
("2008-12-16",-.75,.125),("2015-12-17",.25,.375),("2016-12-15",.25,.625),
("2017-03-16",.25,.875),("2017-06-15",.25,1.125),("2017-12-14",.25,1.375),
("2018-03-22",.25,1.625),("2018-06-14",.25,1.875),("2018-09-27",.25,2.125),
("2018-12-20",.25,2.375),("2019-08-01",-.25,2.125),("2019-09-19",-.25,1.875),
("2019-10-31",-.25,1.625),("2020-03-04",-.5,1.125),("2020-03-16",-1,.125),
("2022-03-17",.25,.375),("2022-05-05",.5,.875),("2022-06-16",.75,1.625),
("2022-07-28",.75,2.375),("2022-09-22",.75,3.125),("2022-11-03",.75,3.875),
("2022-12-15",.5,4.375),("2023-02-02",.25,4.625),("2023-03-23",.25,4.875),
("2023-05-04",.25,5.125),("2023-07-27",.25,5.375),("2024-09-19",-.5,4.875),
("2024-11-08",-.25,4.625),("2024-12-19",-.25,4.375),("2025-09-18",-.25,4.125),
("2025-10-30",-.25,3.875),("2025-12-11",-.25,3.625),("2026-09-17",.25,3.875)]

def fed_series(idx):
 e=pd.DataFrame(FED_EVENTS,columns=["date","change","target"]); e.date=pd.to_datetime(e.date)
 vals=[]
 for d in idx:
  q=e[e.date<=d]; vals.append(float(q.target.iloc[-1]) if len(q) else np.nan)
 return pd.Series(vals,index=idx)

def download(t):
 x=yf.download(t,start=START,end=END,auto_adjust=False,progress=False,actions=False)
 if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
 x.index=pd.to_datetime(x.index).tz_localize(None); x=x.rename(columns={"Adj Close":"adj_close","Close":"close"})
 return x.sort_index().dropna()

def build():
 q=download("QQQ"); v=download("^VIX")[["close"]].rename(columns={"close":"vix"})
 x=q.join(v,how="left"); x.vix=x.vix.ffill(); x["fed"]=fed_series(x.index)
 x["dma"]=x.adj_close.rolling(100).mean(); x["gap"]=x.adj_close/x.dma-1
 # Broader economic context from public FRED graph CSVs.
 fred_ids={"dgs10":"DGS10","t3m":"DTB3","unrate":"UNRATE","cpi":"CPIAUCSL","baa_spread":"BAA10YM","nfci":"NFCI"}
 for name,sid in fred_ids.items():
  z=pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",parse_dates=["observation_date"],na_values=["."])
  z=z.rename(columns={"observation_date":"date",sid:name}).set_index("date")[name].astype(float)
  x[name]=z.reindex(x.index,method="ffill")
 x["cpi_yoy"]=x.cpi.pct_change(252)
 x["unrate_chg_6m"]=x.unrate-x.unrate.shift(126)
 x["curve_10y3m"]=x.dgs10-x.t3m
 x["curve_chg_3m"]=x.curve_10y3m-x.curve_10y3m.shift(63)
 x["baa_chg_3m"]=x.baa_spread-x.baa_spread.shift(63)
 x["nfci_chg_13w"]=x.nfci-x.nfci.shift(63)
 x["ret5"]=x.adj_close/x.adj_close.shift(5)-1; x["ret20"]=x.adj_close/x.adj_close.shift(20)-1
 x["ret60"]=x.adj_close/x.adj_close.shift(60)-1
 x["dma_slope20"]=x.dma/x.dma.shift(20)-1
 x["rv20"]=x.adj_close.pct_change().rolling(20).std()*np.sqrt(252)
 x["vix_chg20"]=x.vix/x.vix.shift(20)-1
 x["tqqq_ret"]=x.adj_close.pct_change()*3
 # Context-relative Fed features. Rolling windows contain only information available at the break.
 for w in (252*2,252*5,252*10):
  x[f"fed_pct_{w}"]=x.fed.rolling(w,min_periods=w).rank(pct=True)
  x[f"fed_z_{w}"]=(x.fed-x.fed.rolling(w,min_periods=w).mean())/x.fed.rolling(w,min_periods=w).std()
  x[f"fed_min_dist_{w}"]=x.fed-x.fed.rolling(w,min_periods=w).min()
  x[f"fed_max_dist_{w}"]=x.fed.rolling(w,min_periods=w).max()-x.fed
 for d in (63,126,252):
  x[f"fed_chg_{d}"]=x.fed-x.fed.shift(d)
 x["tightening_6m"]=(x.fed-x.fed.shift(126)>0).astype(float)
 x["easing_6m"]=(x.fed-x.fed.shift(126)<0).astype(float)
 # Identify first day of each below-DMA episode.
 below=x.adj_close<x.dma
 x["episode_start"]=below & ~below.shift(1,fill_value=False)
 starts=x.index[x.episode_start]
 rows=[]
 for d in starts:
  pos=x.index.get_loc(d); future=below.iloc[pos+1:]
  end=pos
  while end+1<len(x) and below.iloc[end+1]: end+=1
  dur=end-pos+1
  path=(1+x.tqqq_ret.iloc[pos+1:end+1].fillna(0)).cumprod().sub(1).min() if end>pos else 0.0
  r=x.loc[d].copy(); r["date"]=d; r["duration"]=dur; r["persistent20"]=int(dur>=20); r["severe50"]=int(path<=-.5)
  rows.append(r)
 return x,pd.DataFrame(rows).set_index("date")

def auc_walk(df,features,target):
 d=df.dropna(subset=[target]).copy()
 d=d.loc[d[features].notna().any(axis=1)]
 X=d[features]; y=d[target]
 if len(d)<30 or y.nunique()<2:return np.nan
 preds=[]; truth=[]
 for tr,te in TimeSeriesSplit(n_splits=5).split(X):
  if y.iloc[tr].nunique()<2 or y.iloc[te].nunique()<2: continue
  m=make_pipeline(SimpleImputer(strategy="median",add_indicator=True),LogisticRegression(max_iter=3000))
  m.fit(X.iloc[tr],y.iloc[tr]); preds.extend(m.predict_proba(X.iloc[te])[:,1]); truth.extend(y.iloc[te])
 return float(roc_auc_score(truth,preds)) if len(set(truth))==2 else np.nan

def main():
 OUT.mkdir(parents=True,exist_ok=True); x,e=build(); e.to_csv(OUT/"tqqq_contextual_fed_exit_episodes.csv")
 fed2=[c for c in e.columns if c.endswith("_504") or c in ["tightening_6m","easing_6m"]]
 fed5=[c for c in e.columns if c.endswith("_1260") or c in ["tightening_6m","easing_6m"]]
 fed10=[c for c in e.columns if c.endswith("_2520") or c in ["tightening_6m","easing_6m"]]
 market=["ret5","ret20","ret60","gap","dma_slope20","rv20","vix_chg20"]
 macro=["cpi_yoy","unrate","unrate_chg_6m","curve_10y3m","curve_chg_3m","baa_spread","baa_chg_3m","nfci","nfci_chg_13w","dgs10"]
 rows=[]
 for label,features in [("fed_2y",fed2),("fed_5y",fed5),("fed_10y",fed10),("market",market),("macro",macro),("fed_2y_plus_macro",fed2+macro),("market_plus_macro",market+macro),("fed_2y_plus_market_plus_macro",fed2+market+macro)]:
  rows.append({"model":label,"persistent20_auc":auc_walk(e,features,"persistent20"),"severe50_auc":auc_walk(e,features,"severe50"),"n":int(e[features].notna().all(axis=1).sum())})
 pd.DataFrame(rows).to_csv(OUT/"tqqq_contextual_fed_auc.csv",index=False)
 # Fixed qualitative stress-state diagnostic; thresholds are deliberately predeclared,
 # descriptive only, and are not optimized into a trading rule.
 e["state_tightening"]=e.fed_chg_126>0
 e["state_inverted"]=e.curve_10y3m<0
 e["state_inflated"]=e.cpi_yoy>0.04
 e["state_labor_deteriorating"]=e.unrate_chg_6m>0.5
 e["state_credit_widening"]=e.baa_chg_3m>0.25
 e["state_financial_stress"]=e.nfci_chg_13w>0.25
 state_cols=["state_tightening","state_inverted","state_inflated","state_labor_deteriorating","state_credit_widening","state_financial_stress"]
 e["state_count"]=e[state_cols].sum(axis=1)
 e.groupby("state_count").agg(n=("date","size"),persistent20_rate=("persistent20","mean"),severe50_rate=("severe50","mean")).reset_index().to_csv(OUT/"tqqq_contextual_macro_state_counts.csv",index=False)
 dates=["2000-09-25","2002-03-12","2008-08-29","2020-03-06","2022-04-05"]
 cols=["fed","fed_pct_504","fed_z_504","fed_min_dist_504","fed_pct_1260","fed_z_1260","fed_min_dist_1260","fed_pct_2520","fed_z_2520","fed_min_dist_2520","fed_chg_126","fed_chg_252","cpi_yoy","unrate_chg_6m","curve_10y3m","baa_chg_3m","nfci_chg_13w","state_tightening","state_inverted","state_inflated","state_labor_deteriorating","state_credit_widening","state_financial_stress","state_count","ret60","gap","dma_slope20","duration","persistent20","severe50"]
 e.loc[[d for d in dates if d in e.index],cols].to_csv(OUT/"tqqq_contextual_fed_examples.csv")
 print(pd.DataFrame(rows).to_string(index=False)); print("\nEXAMPLES\n",pd.read_csv(OUT/"tqqq_contextual_fed_examples.csv").to_string(index=False))
if __name__=="__main__":main()
