"""Actual-TQQQ validation of B0 + partial-exposure DMA combinations.

Primary candidates combine the QQQ -4.5% shock / +10% recovery control (B0)
with a QQQ-DMA exposure overlay. B0's defensive state takes precedence;
outside B0 defensive windows, exposure is 100% above DMA and the predeclared
partial level below DMA. B0 re-entry is immediate. DMA-only variants remain
diagnostic rows, not candidate strategies.
"""
from pathlib import Path
import hashlib, json
import numpy as np, pandas as pd, yfinance as yf
from causal_execution import next_open_cost_equity, next_open_daily_returns
from reentry_isolation import target_exposure

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"research"
INITIAL=5000.0
START="2010-01-01"
END="2026-10-08"
DMAS=[100,125,150,175,200,250]
BELOW=[1.0,0.75,0.50,0.25,0.0]
COSTS=(0,10,25,50)
PERIODS=(
    ("2011_2015","2011-02-07","2015-12-31"),
    ("2016_2019","2016-01-01","2019-12-31"),
    ("covid","2020-01-01","2021-12-31"),
    ("2022_2024","2022-01-01","2024-12-31"),
    ("2025_to_latest","2025-01-01","2026-10-02"),
)

def dl(t, start=START):
    x=yf.download(t,start=start,end=END,auto_adjust=False,progress=False,actions=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    x.index=pd.to_datetime(x.index).tz_localize(None)
    return x.rename(columns={"Open":"open","Close":"close","Adj Close":"adj_close"}).sort_index().dropna()

def canonical_b0_signal(close):
    """Independent implementation of canonical -4.5% shock / +10% recovery."""
    px = close.to_numpy(dtype=float)
    daily = close.pct_change().fillna(0.0).to_numpy()
    signal = np.ones(len(close), dtype=float)
    armed = False
    low_i = None
    for i in range(1, len(close)):
        if not armed and daily[i] <= -0.045:
            armed = True
            low_i = i
            signal[i] = 0.0
            continue
        if armed:
            if px[i] < px[low_i]:
                low_i = i
            if px[i] / px[low_i] - 1.0 >= 0.10:
                armed = False
                signal[i] = 1.0
            else:
                signal[i] = 0.0
    return signal


def main():
    # QQQ starts before TQQQ so B0's running-low state is initialized from
    # the full signal history; evaluation capital still begins on the shared
    # post-250-DMA date below.
    q=dl("QQQ",start="1999-03-10"); t=dl("TQQQ",start=START)
    b0_signal=target_exposure(q.rename(columns={"adj_close":"Adj Close"}),"B0")
    x=q.join(t[["open","close","adj_close"]].add_prefix("tqqq_"),how="inner")
    x["b0_signal"]=b0_signal.reindex(x.index)
    canonical_signal=canonical_b0_signal(x.adj_close)
    if not np.array_equal(x["b0_signal"].to_numpy(dtype=float),canonical_signal):
        mismatch=np.flatnonzero(x["b0_signal"].to_numpy(dtype=float)!=canonical_signal)
        i=int(mismatch[0])
        raise AssertionError(f"Canonical B0 signal mismatch at {x.index[i]}: "
                             f"{x['b0_signal'].iloc[i]} vs {canonical_signal[i]}")
    t_adj_open=x.tqqq_open*x.tqqq_adj_close/x.tqqq_close
    x["tqqq_adj_open"]=t_adj_open
    x["on"]=(t_adj_open/x.tqqq_adj_close.shift(1)-1).fillna(0)
    x["in"]=(x.tqqq_adj_close/t_adj_open-1).fillna(0)

    # Moving averages use full QQQ history, so TQQQ evaluation starts at
    # inception on the same dates as canonical B0, not after an extra 250
    # joined TQQQ observations. END is exclusive, matching the canonical replay.
    max_dma=max(DMAS)
    x["eval_date"] = x.index
    for dma in DMAS:
        x[f"ma_{dma}"] = x.adj_close.rolling(dma).mean()

    frozen_cols=["adj_close","tqqq_adj_open","tqqq_adj_close","on","in","b0_signal"]+[f"ma_{dma}" for dma in DMAS]
    frozen=x[frozen_cols].copy()
    frozen.index.name="date"
    OUT.mkdir(parents=True,exist_ok=True)
    frozen_path=OUT/"tqqq_actual_partial_dma_frozen_input.csv"
    frozen.to_csv(frozen_path,index_label="date",float_format="%.15g")

    x=x.loc[x.index >= pd.Timestamp("2010-02-11")].copy()
    if x.empty or x.index[0].date().isoformat() != "2010-02-11":
        raise AssertionError(f"Expected canonical TQQQ start 2010-02-11, got {x.index[0] if len(x) else 'no rows'}")
    if x.index[-1].date().isoformat() != "2026-10-07":
        raise AssertionError(f"Expected canonical end 2026-10-07, got {x.index[-1]}")
    years=(x.index[-1]-x.index[0]).days/365.2425
    rows=[]
    period_rows=[]

    def record(label,dma,below,sig,cost_bps):
        eq=next_open_cost_equity(sig,x.on,x["in"],cost_bps,INITIAL)
        dd=eq/np.maximum.accumulate(eq)-1
        trough=int(np.argmin(dd))
        peak=int(np.argmax(eq[:trough+1]))
        rows.append({"strategy":label,"dma":dma,"below_exposure":below,
                     "cost_bps_per_exposure_change":cost_bps,
                     "evaluation_start":x.index[0].date().isoformat(),
                     "evaluation_end":x.index[-1].date().isoformat(),
                     "final":float(eq[-1]),
                     "cagr":(float(eq[-1])/INITIAL)**(1/years)-1,
                     "max_dd":float(dd.min()),
                     "max_dd_peak_date":x.index[peak].date().isoformat(),
                     "max_dd_trough_date":x.index[trough].date().isoformat(),
                     "avg_exposure":float(np.mean(sig))})
        for period_name,period_start,period_end in PERIODS:
            dates=pd.DatetimeIndex(x.index)
            mask=(dates>=pd.Timestamp(period_start))&(dates<=pd.Timestamp(period_end))
            positions=np.flatnonzero(mask)
            if len(positions)<2:
                continue
            first,last=int(positions[0]),int(positions[-1])
            prior_equity=INITIAL if first==0 else float(eq[first-1])
            segment=np.concatenate(([INITIAL],INITIAL*eq[first:last+1]/prior_equity))
            segment_dd=segment/np.maximum.accumulate(segment)-1
            span_days=(dates[last]-(dates[first-1] if first>0 else dates[first])).days
            period_years=max(span_days/365.25,1/365.25)
            period_rows.append({
                "strategy":label,"dma":dma,"below_exposure":below,
                "cost_bps_per_exposure_change":cost_bps,"period":period_name,
                "period_start":dates[first].date().isoformat(),
                "period_end":dates[last].date().isoformat(),
                "observations":int(len(positions)),
                "ending_balance":float(segment[-1]),
                "cagr":float((segment[-1]/INITIAL)**(1/period_years)-1),
                "max_drawdown":float(segment_dd.min()),
                "minimum_equity":float(segment.min()),
            })

    for cost_bps in COSTS:
        record("BUY_HOLD",0,1.0,np.ones(len(x)),cost_bps)
        b0=x.b0_signal.to_numpy(dtype=float)
        record("B0_SHOCK_RECOVERY",-1,np.nan,b0,cost_bps)
        for dma in DMAS:
            ma=x[f"ma_{dma}"].to_numpy()
            above=(x.adj_close.to_numpy()>=ma)
            for below in BELOW:
                sig=np.where(above,1.0,below)
                combined=np.minimum(b0,sig)
                record("B0_PLUS_DMA_PARTIAL",dma,below,combined,cost_bps)
                record("DMA_ONLY_DIAGNOSTIC",dma,below,sig,cost_bps)

    out=pd.DataFrame(rows).sort_values("final",ascending=False)
    # Independent same-input B0 equity reconciliation against canonical daily
    # return construction, not merely B0-versus-itself identity.
    canonical_daily=next_open_daily_returns(canonical_signal,x["on"].to_numpy(),x["in"].to_numpy())
    canonical_equity=INITIAL*np.cumprod(1.0+canonical_daily)
    matrix_b0=float(out[(out["strategy"]=="B0_SHOCK_RECOVERY") &
                        (out["cost_bps_per_exposure_change"]==0)]["final"].iloc[0])
    if not np.isclose(matrix_b0,float(canonical_equity[-1]),rtol=1e-10,atol=1e-5):
        raise AssertionError(f"Canonical B0 terminal mismatch: matrix={matrix_b0}, independent={canonical_equity[-1]}")
    # Baseline reconstruction invariant: a 100% DMA exposure overlay must
    # leave B0 unchanged for every cost assumption and every DMA lookback.
    # This catches accidental signal/combination drift before artifacts publish.
    b0_rows=out[out["strategy"]=="B0_SHOCK_RECOVERY"].set_index("cost_bps_per_exposure_change")
    invariant_rows=out[(out["strategy"]=="B0_PLUS_DMA_PARTIAL") & (out["below_exposure"]==1.0)]
    for _, candidate in invariant_rows.iterrows():
        base=b0_rows.loc[candidate["cost_bps_per_exposure_change"]]
        if not np.isclose(candidate["final"],base["final"],rtol=1e-12,atol=1e-8):
            raise AssertionError(f"B0 invariant failed: DMA={candidate['dma']} cost={candidate['cost_bps_per_exposure_change']}")
        if not np.isclose(candidate["max_dd"],base["max_dd"],rtol=1e-12,atol=1e-12):
            raise AssertionError(f"B0 drawdown invariant failed: DMA={candidate['dma']} cost={candidate['cost_bps_per_exposure_change']}")
    if len(invariant_rows) != len(DMAS)*len(COSTS):
        raise AssertionError(f"Expected {len(DMAS)*len(COSTS)} B0 identity rows, got {len(invariant_rows)}")
    periods=pd.DataFrame(period_rows)
    matrix_path=OUT/"tqqq_actual_partial_dma_matrix.csv"
    periods_path=OUT/"tqqq_actual_partial_dma_periods.csv"
    manifest_path=OUT/"tqqq_actual_partial_dma_manifest.json"
    out.to_csv(matrix_path,index=False,float_format="%.15g")
    periods.to_csv(periods_path,index=False,float_format="%.15g")
    manifest={
        "status":"PASS",
        "frozen_input_file":frozen_path.name,
        "frozen_input_sha256":hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
        "matrix_sha256":hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        "periods_sha256":hashlib.sha256(periods_path.read_bytes()).hexdigest(),
        "input_rows":int(len(frozen)),
        "evaluation_start":x.index[0].date().isoformat(),
        "evaluation_end":x.index[-1].date().isoformat(),
        "initial_balance":INITIAL,
        "warmup_sessions":max_dma,
        "cost_bps_per_exposure_change":list(COSTS),
        "dma_sessions":DMAS,
        "below_dma_exposures":BELOW,
        "b0_shock_threshold":-0.045,
        "b0_recovery_threshold":0.10,
        "execution":"close signal executes next open; prior exposure earns overnight return, new exposure earns intraday return",
        "combined_exposure":"min(B0 exposure, DMA exposure); standalone DMA rows are diagnostics only",
        "trade_asset":"actual TQQQ; DMA signal asset QQQ adjusted close",
        "canonical_b0_signal_match":True,
        "canonical_b0_final_independent":float(canonical_equity[-1]),
        "canonical_b0_final_abs_diff":float(abs(matrix_b0-canonical_equity[-1])),
    }
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    print("ACTUAL TQQQ; QQQ DMA signal; next-open execution")
    print("COMMON EVALUATION WINDOW",x.index[0].date(),"to",x.index[-1].date(),
          "| initial capital",INITIAL)
    print(out.to_string(index=False))
    print("\\nBY DMA")
    print(out.sort_values(["dma","below_exposure"]).to_string(index=False))
if __name__=="__main__": main()
