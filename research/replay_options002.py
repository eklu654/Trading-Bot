"""OPTIONS-002: frozen defined-risk SPY iron-condor research replay.

Baseline: 45 DTE target, 30-60 DTE eligible, ~16-delta short strikes,
2-point wings, 50% credit target or 21 DTE exit. One contract. Daily EOD
quotes. Conservative entry/exit uses bid for shorts and ask for longs;
mid uses marks. Defined risk means no 2x-credit loss stop.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import duckdb
import pandas as pd
from replay_options001 import load_regime, source_sql, validate_local_source

ROOT=Path(__file__).resolve().parents[1]
RESEARCH_DIR=ROOT/"data"/"research"

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--options-source",required=True)
    p.add_argument("--candidate",default="ALL_DAYS",choices=["CURRENT","BALANCED","BROAD_SIDEWAYS","TURBULENT_ONLY","ALL_DAYS"])
    p.add_argument("--fill-model",default="conservative",choices=["conservative","mid"])
    p.add_argument("--target-dte",type=int,default=45)
    p.add_argument("--target-delta",type=float,default=0.16)
    p.add_argument("--wing-width",type=float,default=2.0)
    p.add_argument("--min-dte",type=int,default=30)
    p.add_argument("--max-dte",type=int,default=60)
    p.add_argument("--profit-target",type=float,default=0.50)
    p.add_argument("--exit-dte",type=int,default=21)
    p.add_argument("--start-date",default="2010-01-01")
    p.add_argument("--end-date",default="2025-12-31")
    return p.parse_args()

def select_entries(con,source,regime,args):
    eligible=regime.index[regime["eligible"]]
    if len(eligible)==0:return pd.DataFrame()
    con.register("eligible_dates",pd.DataFrame({"entry_date":eligible}))
    q=f"""
    WITH c AS (
      SELECT CAST(o.date AS DATE) entry_date,o.contract_id,CAST(o.expiration AS DATE) expiration,
             o.strike,o.type,o.bid,o.ask,o.mark,o.volume,o.open_interest,o.delta,
             datediff('day',CAST(o.date AS DATE),CAST(o.expiration AS DATE)) dte
      FROM {source_sql(source)} o JOIN eligible_dates d ON CAST(o.date AS DATE)=d.entry_date
      WHERE CAST(o.expiration AS DATE) BETWEEN CAST(o.date AS DATE)+INTERVAL '{args.min_dte}' DAY
        AND CAST(o.date AS DATE)+INTERVAL '{args.max_dte}' DAY
        AND o.bid>0 AND o.ask>=o.bid AND o.mark>0 AND (o.volume>0 OR o.open_interest>0)
    ),e AS (
      SELECT entry_date,expiration FROM (
        SELECT DISTINCT entry_date,expiration,dte,
          row_number() OVER(PARTITION BY entry_date ORDER BY abs(dte-{args.target_dte}),expiration) rn FROM c
      ) WHERE rn=1
    ),ch AS (SELECT c.* FROM c JOIN e USING(entry_date,expiration)),
    r AS (
      SELECT *,row_number() OVER(PARTITION BY entry_date,type ORDER BY
        CASE WHEN lower(type)='call' THEN abs(delta-{args.target_delta})
             ELSE abs(abs(delta)-{args.target_delta}) END,
        volume DESC NULLS LAST,open_interest DESC NULLS LAST) rn
      FROM ch WHERE (lower(type)='call' AND delta>0) OR (lower(type)='put' AND delta<0)
    ) SELECT * FROM r WHERE rn=1 ORDER BY entry_date,type
    """
    x=con.execute(q).fetchdf();con.unregister("eligible_dates")
    if x.empty:return x
    x["type"]=x["type"].str.lower()
    c=x[x.type=="call"].copy();p=x[x.type=="put"].copy()
    return c.merge(p,on="entry_date",suffixes=("_call","_put")).sort_values("entry_date").reset_index(drop=True)

def attach_wings(con,source,entries,args):
    if entries.empty:return entries
    rows=[]
    for _,r in entries.iterrows():
        q=f"""
        SELECT contract_id,strike,lower(type) type,bid,ask,mark,volume,open_interest
        FROM {source_sql(source)}
        WHERE CAST(date AS DATE)=DATE '{pd.Timestamp(r.entry_date).date()}'
          AND CAST(expiration AS DATE)=DATE '{pd.Timestamp(r.expiration_call).date()}'
          AND bid>0 AND ask>=bid AND mark>0 AND (volume>0 OR open_interest>0)
          AND ((lower(type)='call' AND strike>={float(r.strike_call)+args.wing_width})
            OR (lower(type)='put' AND strike<={float(r.strike_put)-args.wing_width}))
        """
        w=con.execute(q).fetchdf()
        if w.empty:continue
        calls=w[w.type=="call"].sort_values(["strike","volume"],ascending=[True,False])
        puts=w[w.type=="put"].sort_values(["strike","volume"],ascending=[False,False])
        if calls.empty or puts.empty:continue
        c=calls.iloc[0];p=puts.iloc[0]
        if float(c.strike)<=float(r.strike_call) or float(p.strike)>=float(r.strike_put):continue
        row=r.to_dict()
        row.update({
          "long_call_id":str(c.contract_id),"long_put_id":str(p.contract_id),
          "long_call_strike":float(c.strike),"long_put_strike":float(p.strike),
          "wing_width_call":float(c.strike)-float(r.strike_call),
          "wing_width_put":float(r.strike_put)-float(p.strike),
          "bid_long_call":float(c.bid),"ask_long_call":float(c.ask),"mark_long_call":float(c.mark),
          "bid_long_put":float(p.bid),"ask_long_put":float(p.ask),"mark_long_put":float(p.mark)
        })
        rows.append(row)
    return pd.DataFrame(rows)

def leg_price(qr,cid,kind,fill):
    if fill=="mid":f="mark"
    else:f="bid" if kind=="short" else "ask"
    key=(f,cid)
    if key not in qr:return None
    v=qr[key]
    return float(v) if pd.notna(v) else None

def replay(entries,quotes,regime,args):
    trades=[];marks=[]
    for _,r in entries.iterrows():
        ed=pd.Timestamp(r.entry_date);q=quotes[quotes.entry_date==ed]
        if q.empty:continue
        by=q.pivot(index="date",columns="contract_id",values=["bid","ask","mark"])
        ids=[str(r.contract_id_call),str(r.contract_id_put),str(r.long_call_id),str(r.long_put_id)]
        if args.fill_model=="mid":
            credit=float(r.mark_call+r.mark_put-r.mark_long_call-r.mark_long_put)
        else:
            credit=float(r.bid_call+r.bid_put-r.ask_long_call-r.ask_long_put)
        if credit<=0:continue
        cid=f"{ed.date()}:{':'.join(ids)}"
        max_debit=0.0;exit_date=None;exit_debit=None
        for date,qr in by.iterrows():
            vals=[]
            for leg,kind in zip(ids,["short","short","long","long"]):
                v=leg_price(qr,leg,kind,args.fill_model)
                if v is None:break
                vals.append(v)
            if len(vals)!=4:continue
            debit=max(0.0,vals[0]+vals[1]-vals[2]-vals[3])
            max_debit=max(max_debit,debit)
            underlying=float(regime.loc[pd.Timestamp(date),"spy_close"]) if pd.Timestamp(date) in regime.index else float("nan")
            marks.append({"candidate_id":cid,"date":pd.Timestamp(date),"mark_debit":debit,"underlying_close":underlying})
            dte=(pd.Timestamp(r.expiration_call)-pd.Timestamp(date)).days
            if debit<=credit*(1-args.profit_target):
                exit_date=pd.Timestamp(date);exit_debit=debit;reason="PROFIT_50";break
            if dte<=args.exit_dte:
                exit_date=pd.Timestamp(date);exit_debit=debit;reason="DTE_21";break
        if exit_date is None:continue
        max_loss=max(float(r.wing_width_call),float(r.wing_width_put))*100-credit*100
        trades.append({"candidate_id":cid,"entry_date":ed,"exit_date":exit_date,"expiration":pd.Timestamp(r.expiration_call),
                       "entry_credit":credit,"exit_debit":exit_debit,"pnl":(credit-exit_debit)*100,
                       "max_debit":max_debit,"max_loss_pnl":(credit-max_debit)*100,
                       "max_defined_loss":max_loss,"entry_dte":(pd.Timestamp(r.expiration_call)-ed).days,
                       "exit_dte":(pd.Timestamp(r.expiration_call)-exit_date).days,
                       "call_strike":float(r.strike_call),"put_strike":float(r.strike_put),
                       "long_call_strike":float(r.long_call_strike),"long_put_strike":float(r.long_put_strike),
                       "call_delta":float(r.delta_call),"put_delta":float(r.delta_put),
                       "regime":regime.loc[ed,"entry_regime"],"exit_reason":reason})
    return pd.DataFrame(trades),pd.DataFrame(marks)

def main():
    args=parse_args();validate_local_source(args.options_source)
    regime=load_regime(args.candidate,args.start_date,args.end_date)
    con=duckdb.connect()
    entries=attach_wings(con,args.options_source,select_entries(con,args.options_source,regime,args),args)
    if entries.empty:
        print("OPTIONS-002: no chain candidates");return
    selected=entries[["entry_date","expiration_call","contract_id_call","contract_id_put","long_call_id","long_put_id"]]
    con.register("selected",selected)
    q=f"""SELECT s.entry_date,s.contract_id_call,s.contract_id_put,s.long_call_id,s.long_put_id,
                  s.expiration_call expiration,CAST(o.date AS DATE) date,o.contract_id,o.bid,o.ask,o.mark
           FROM selected s JOIN {source_sql(args.options_source)} o
             ON o.contract_id IN(s.contract_id_call,s.contract_id_put,s.long_call_id,s.long_put_id)
            AND CAST(o.date AS DATE)>s.entry_date AND CAST(o.date AS DATE)<=s.expiration_call
           ORDER BY s.entry_date,o.date"""
    quotes=con.execute(q).fetchdf();con.unregister("selected")
    trades,marks=replay(entries,quotes,regime,args);con.close()
    candidates=[]
    for _,r in entries.iterrows():
        credit=float(r.mark_call+r.mark_put-r.mark_long_call-r.mark_long_put) if args.fill_model=="mid" else float(r.bid_call+r.bid_put-r.ask_long_call-r.ask_long_put)
        if credit<=0:continue
        cid=f"{pd.Timestamp(r.entry_date).date()}:{r.contract_id_call}:{r.contract_id_put}:{r.long_call_id}:{r.long_put_id}"
        candidates.append({"candidate_id":cid,"entry_date":pd.Timestamp(r.entry_date),"entry_credit":credit,
                           "call_strike":float(r.strike_call),"put_strike":float(r.strike_put),
                           "long_call_strike":float(r.long_call_strike),"long_put_strike":float(r.long_put_strike),
                           "wing_width_call":float(r.wing_width_call),"wing_width_put":float(r.wing_width_put),
                           "underlying_close":float(regime.loc[pd.Timestamp(r.entry_date),"spy_close"]),
                           "max_defined_loss":max(float(r.wing_width_call),float(r.wing_width_put))*100-credit*100})
    cdf=pd.DataFrame(candidates)
    stem=f"options002_replay_{args.candidate.lower()}_{args.fill_model}"
    cdf.to_csv(RESEARCH_DIR/f"{stem}_candidates.csv",index=False)
    (trades[["candidate_id","exit_date","pnl","exit_debit"]] if not trades.empty else pd.DataFrame(columns=["candidate_id","exit_date","pnl","exit_debit"])).to_csv(RESEARCH_DIR/f"{stem}_candidate_outcomes.csv",index=False)
    marks.to_csv(RESEARCH_DIR/f"{stem}_candidate_marks.csv",index=False)
    trades.to_csv(RESEARCH_DIR/f"{stem}.csv",index=False)
    print(f"OPTIONS-002 candidate={args.candidate} fill={args.fill_model} entries={len(entries)} trades={len(trades)}")
    if not trades.empty:
        print(f"total_pnl={trades.pnl.sum():.2f} win_rate={(trades.pnl>0).mean():.3f} worst_trade={trades.pnl.min():.2f}")
        print(trades.groupby("regime").pnl.agg(["count","mean","sum"]).to_string())

if __name__=="__main__":main()
