"""Fed-regime overlay for the frozen QQQ 4.5% shock / 10% recovery TQQQ control.

Purpose:
- Keep the canonical 10% recovery rule frozen.
- Test whether an ex-ante Fed tightening regime can identify prolonged
  tightening-cycle rebounds such as 2022 without delaying ordinary V-shaped
  recoveries.
- No threshold is selected from holdout performance.

Fed state is reconstructed only from FOMC effective target changes known by
the signal date.  Aggressive-tightening candidates are fixed combinations of:
  cumulative rate increase over 3/6/12 months (50/100/150/200 bp), plus an
  optional current-rate floor.  A recovery gate may raise the 10% target to
  15/20/25/30/40%.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-08"
SHOCK = -0.045
NORMAL = 0.10
TARGETS = (0.15, 0.20, 0.25, 0.30, 0.40)
WINDOWS = (63, 126, 252)
BPS_THRESHOLDS = (50, 100, 150, 200)
RATE_FLOORS = (0.0, 1.5, 2.5, 3.5)

# Historical FOMC target-range midpoint, effective after each decision.
FED_EVENTS = [
("2015-12-17",.25,.375),("2016-12-15",.25,.625),("2017-03-16",.25,.875),
("2017-06-15",.25,1.125),("2017-12-14",.25,1.375),("2018-03-22",.25,1.625),
("2018-06-14",.25,1.875),("2018-09-27",.25,2.125),("2018-12-20",.25,2.375),
("2019-08-01",-.25,2.125),("2019-09-19",-.25,1.875),("2019-10-31",-.25,1.625),
("2020-03-04",-.5,1.125),("2020-03-16",-1,.125),
("2022-03-17",.25,.375),("2022-05-05",.5,.875),("2022-06-16",.75,1.625),
("2022-07-28",.75,2.375),("2022-09-22",.75,3.125),("2022-11-03",.75,3.875),
("2022-12-15",.5,4.375),("2023-02-02",.25,4.625),("2023-03-23",.25,4.875),
("2023-05-04",.25,5.125),("2023-07-27",.25,5.375),
("2024-09-19",-.5,4.875),("2024-11-08",-.25,4.625),("2024-12-19",-.25,4.375),
("2025-09-18",-.25,4.125),("2025-10-30",-.25,3.875),("2025-12-11",-.25,3.625),
("2026-09-17",.25,3.875),
]

def dl(symbol):
    x = yf.download(symbol, start=START, end=END, auto_adjust=False,
                    progress=False, actions=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.sort_index()

def fed_frame(idx):
    e = pd.DataFrame(FED_EVENTS, columns=["date","change","midpoint"])
    e.date = pd.to_datetime(e.date)
    rows = []
    for d in idx:
        prior = e[e.date <= d]
        if prior.empty:
            rows.append((np.nan, np.nan))
        else:
            rows.append((float(prior.midpoint.iloc[-1]), float(prior.change.iloc[-1])))
    return pd.DataFrame(rows, index=idx, columns=["fed_midpoint","fed_last_change"])

def fed_features(idx):
    e = pd.DataFrame(FED_EVENTS, columns=["date","change","midpoint"])
    e.date = pd.to_datetime(e.date)
    out = pd.DataFrame(index=idx)
    for days in WINDOWS:
        vals = []
        for d in idx:
            prior = e[e.date <= d]
            if prior.empty:
                vals.append(np.nan)
                continue
            cutoff = d - pd.Timedelta(days=days)
            recent = prior[prior.date > cutoff]
            vals.append(float(recent.change[recent.change > 0].sum() * 100.0))
        out[f"hike_bp_{days}d"] = vals
    base = fed_frame(idx)
    out["fed_midpoint"] = base.fed_midpoint
    out["fed_last_change"] = base.fed_last_change
    out["active_hike_6m"] = out["hike_bp_126d"] > 0
    return out

def aggressive_flag(row, window, bp, floor):
    return (
        np.isfinite(row["fed_midpoint"])
        and row["fed_midpoint"] >= floor
        and row[f"hike_bp_{window}d"] >= bp
    )

def equity(p, asset_returns, gate=None, target=NORMAL):
    qret = p.pct_change().fillna(0).to_numpy()
    px = p.to_numpy()
    ar = asset_returns.to_numpy()
    invested = np.ones(len(p))
    armed = False
    low = np.nan
    low_i = None
    required_target = NORMAL

    for i in range(1, len(p)):
        if not armed and qret[i] <= SHOCK:
            armed = True
            low = px[i]
            low_i = i
        if armed:
            if px[i] < low:
                low = px[i]
                low_i = i
            gain = px[i] / low - 1
            if gain >= NORMAL and required_target == NORMAL:
                if gate is not None and gate.iloc[i]:
                    required_target = target
            if gain >= required_target:
                armed = False
                low = np.nan
                low_i = None
                required_target = NORMAL
            else:
                invested[i] = 0.0

    exposure = np.roll(invested, 1)
    exposure[0] = 1.0
    eq = INITIAL * np.cumprod(1 + exposure * ar)
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1
    return pd.Series(eq, index=p.index), float(dd.min())

def canonical_events(p):
    qret = p.pct_change().fillna(0).to_numpy()
    px = p.to_numpy()
    armed = False
    low = np.nan
    low_i = None
    rows = []
    for i in range(1, len(p)):
        if not armed and qret[i] <= SHOCK:
            armed, low, low_i = True, px[i], i
        if armed:
            if px[i] < low:
                low, low_i = px[i], i
            gain = px[i] / low - 1
            if gain >= NORMAL:
                rows.append((i, p.index[i], i-low_i))
                armed, low, low_i = False, np.nan, None
    return rows

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q, t = dl("QQQ"), dl("TQQQ")
    idx = q.index.intersection(t.index)
    q, t = q.reindex(idx), t.reindex(idx)
    p = q["Close"].squeeze().astype(float)
    tp = t["Close"].squeeze().astype(float)
    ar = tp.pct_change().fillna(0)

    ff = fed_features(p.index)
    events = canonical_events(p)

    # Event-level ledger: only the first 10% recovery date is inspected.
    ledger = []
    for i, d, speed in events:
        r = ff.iloc[i]
        row = {
            "date": str(d.date()), "days_to_10pct": int(speed),
            "fed_midpoint": r.fed_midpoint,
            "fed_last_change": r.fed_last_change,
            "hike_bp_63d": r.hike_bp_63d,
            "hike_bp_126d": r.hike_bp_126d,
            "hike_bp_252d": r.hike_bp_252d,
        }
        for w in WINDOWS:
            for bp in BPS_THRESHOLDS:
                for floor in RATE_FLOORS:
                    row[f"gate_{w}_{bp}_{floor:g}"] = int(
                        aggressive_flag(r, w, bp, floor))
        ledger.append(row)
    event_df = pd.DataFrame(ledger)
    event_df.to_csv(OUT / "tqqq_fed_regime_event_ledger.csv", index=False)

    # Full-period matrix.
    rows = []
    bh = INITIAL * np.cumprod(1 + ar.to_numpy())
    rows.append({
        "scope":"full_2010_2026","name":"baseline_10pct","window":0,
        "bp_threshold":0,"rate_floor":0,"target":NORMAL,
        "final_balance":bh[-1],"cagr":np.nan,"max_drawdown":np.nan,
    })

    years = (p.index[-1] - p.index[0]).days / 365.25
    # Baseline is evaluated through the same state machine, not the shortcut BH.
    base_eq, base_dd = equity(p, ar)
    rows[-1].update(final_balance=float(base_eq.iloc[-1]),
                    cagr=float((base_eq.iloc[-1]/INITIAL)**(1/years)-1),
                    max_drawdown=base_dd)

    for w in WINDOWS:
        for bp in BPS_THRESHOLDS:
            for floor in RATE_FLOORS:
                gate = ff.apply(lambda r: aggressive_flag(r,w,bp,floor),axis=1)
                for target in TARGETS:
                    eq, dd = equity(p, ar, gate, target)
                    rows.append({
                        "scope":"full_2010_2026",
                        "name":f"fed_{w}d_{bp}bp_floor{floor:g}_target{int(target*100)}",
                        "window":w,"bp_threshold":bp,"rate_floor":floor,
                        "target":target,"final_balance":float(eq.iloc[-1]),
                        "cagr":float((eq.iloc[-1]/INITIAL)**(1/years)-1),
                        "max_drawdown":dd,
                    })
    full = pd.DataFrame(rows)
    full.to_csv(OUT / "tqqq_fed_regime_full.csv", index=False)

    # Frozen chronological tests. Selection is only among a deliberately
    # small family: target is fixed at 20% and the Fed gate varies.
    candidates = [(0,0,0,"baseline_10pct")]
    for w in WINDOWS:
        for bp in BPS_THRESHOLDS:
            candidates.append((w,bp,0,f"fed_{w}d_{bp}bp"))
    folds = [
        ("F1","2010-01-01","2017-12-31","2018-01-01","2021-12-31"),
        ("F2","2010-01-01","2021-12-31","2022-01-01","2026-10-07"),
    ]
    wf = []
    for fold, ta, tb, ea, eb in folds:
        train_rows=[]
        for w,bp,_floor,name in candidates:
            if w == 0:
                eq,_=equity(p,ar)
            else:
                gate=ff.apply(lambda r: aggressive_flag(r,w,bp,0),axis=1)
                eq,_=equity(p,ar,gate,0.20)
            tr=eq.loc[ta:tb]
            te=eq.loc[ea:eb]
            train_growth=float(tr.iloc[-1]/INITIAL)
            test_growth=float(te.iloc[-1]/tr.iloc[-1])
            train_rows.append((train_growth,name,w,bp,test_growth))
        best=max(train_rows,key=lambda x:x[0])
        for tg,name,w,bp,eg in train_rows:
            wf.append({"fold":fold,"name":name,"window":w,"bp_threshold":bp,
                       "train_growth":tg,"test_growth":eg,
                       "selected":int(name==best[1])})
    wfdf=pd.DataFrame(wf)
    wfdf.to_csv(OUT / "tqqq_fed_regime_walkforward.csv", index=False)

    # V-shape preservation: report which canonical events would be gated.
    gate_hits=[]
    for w in WINDOWS:
        for bp in BPS_THRESHOLDS:
            gate=ff.apply(lambda r: aggressive_flag(r,w,bp,0),axis=1)
            hits=[]
            for i,d,speed in events:
                hits.append(int(bool(gate.iloc[i])))
            gate_hits.append({"window":w,"bp_threshold":bp,
                              "events_gated":sum(hits),
                              "event_count":len(hits),
                              "gated_dates":";".join(str(events[i][1].date()) for i,h in enumerate(hits) if h)})
    pd.DataFrame(gate_hits).to_csv(OUT / "tqqq_fed_regime_event_coverage.csv", index=False)

    print("\nFED EVENT LEDGER")
    print(event_df.to_string(index=False))
    print("\nFULL TOP 20")
    print(full.sort_values("final_balance",ascending=False).head(20).to_string(index=False))
    print("\nWALK-FORWARD")
    print(wfdf[wfdf.selected==1].to_string(index=False))
    print("\nEVENT COVERAGE")
    print(pd.DataFrame(gate_hits).to_string(index=False))

if __name__ == "__main__":
    main()
