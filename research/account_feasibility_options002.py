"""Account feasibility replay for defined-risk OPTIONS-002.

Buying power is modeled as maximum defined loss for one iron condor.
This is a research estimate, not a broker buying-power preview.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RESEARCH_DIR=ROOT/"data"/"research"

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--outcomes",required=True)
    p.add_argument("--marks",required=True)
    p.add_argument("--starting-nlv",type=float,default=5000)
    p.add_argument("--max-bpr-pct",type=float,default=.50)
    p.add_argument("--max-risk-pct",type=float,default=.07)
    p.add_argument("--fee-per-contract",type=float,default=.65)
    p.add_argument("--output",required=True)
    return p.parse_args()

def replay(candidates,outcomes,marks,args):
    c=candidates.copy();o=outcomes.copy();m=marks.copy()
    c["entry_date"]=pd.to_datetime(c["entry_date"]);o["exit_date"]=pd.to_datetime(o["exit_date"]);m["date"]=pd.to_datetime(m["date"])
    if o["candidate_id"].duplicated().any():raise ValueError("duplicate outcome candidate_id")
    if m.duplicated(["candidate_id","date"]).any():raise ValueError("duplicate mark candidate/date")
    c=c.merge(o[["candidate_id","exit_date","pnl","exit_debit"]],on="candidate_id",how="left",validate="one_to_one")
    marks_by={cid:g.sort_values("date") for cid,g in m.groupby("candidate_id")}
    cash=float(args.starting_nlv);active=None;rows=[];snapshots=[]
    for _,r in c.sort_values(["entry_date","candidate_id"]).iterrows():
        entry=pd.Timestamp(r.entry_date)
        if active is not None and pd.Timestamp(active["exit_date"])<=entry:
            cash += float(active["exit_cash_flow"]); active=None
        if active is not None:
            # A one-position portfolio rejects overlap rather than selecting a convenient candidate.
            rows.append({"candidate_id":r.candidate_id,"entry_date":entry,"accepted":False,
                         "rejection_codes":"POSITION_ALREADY_OPEN","pre_trade_nlv":cash+float(active["position_value"])})
            continue
        credit=float(r.entry_credit); max_loss=float(r.max_defined_loss)
        nlv=cash
        rejects=[]
        if credit<=0:rejects.append("NONPOSITIVE_CREDIT")
        if not pd.notna(r.exit_date):rejects.append("UNRESOLVED_LIFECYCLE_DATA")
        bpr_limit=min(args.starting_nlv*args.max_bpr_pct,nlv*args.max_bpr_pct)
        risk_limit=nlv*args.max_risk_pct
        if max_loss>bpr_limit:rejects.append("BUYING_POWER_LIMIT")
        if max_loss>risk_limit:rejects.append("DEFINED_RISK_SIZE_LIMIT")
        if rejects:
            rows.append({"candidate_id":r.candidate_id,"entry_date":entry,"accepted":False,
                         "rejection_codes":";".join(rejects),"pre_trade_nlv":nlv,
                         "entry_credit":credit,"max_defined_loss":max_loss})
            continue
        fee=args.fee_per_contract*4
        cash-=fee
        exit_date=pd.Timestamp(r.exit_date)
        exit_debit=float(r.exit_debit)
        position_value=-exit_debit*100
        exit_cash_flow=-exit_debit*100-fee
        active={"candidate_id":r.candidate_id,"exit_date":exit_date,
                "position_value":position_value,"exit_cash_flow":exit_cash_flow}
        rows.append({"candidate_id":r.candidate_id,"entry_date":entry,"accepted":True,
                     "rejection_codes":"","pre_trade_nlv":nlv,"entry_credit":credit,
                     "max_defined_loss":max_loss,"entry_fee":fee,"exit_fee":fee,
                     "exit_date":exit_date,"exit_debit":exit_debit,
                     "strategy_pnl":float(r.pnl),"net_pnl":float(r.pnl)-fee*2,
                     "post_trade_nlv":nlv+float(r.pnl)-fee*2})
        # Record available intratrade marks through exit. The mark model is only
        # used for risk/drawdown accounting; no synthetic marks are invented.
        for _,mr in marks_by.get(r.candidate_id,pd.DataFrame()).iterrows():
            d=pd.Timestamp(mr.date)
            if d<entry or d>exit_date:continue
            debit=float(mr.mark_debit)
            nlv_mark=cash-debit*100
            snapshots.append({"date":d,"nlv":nlv_mark,"bpr":max_loss,"bpr_pct":max_loss/nlv_mark if nlv_mark>0 else None})
        cash += float(r.pnl)-fee*2
        active=None
    if active is not None: cash += float(active["exit_cash_flow"])
    ledger=pd.DataFrame(rows)
    summary={"candidate_count":len(ledger),"accepted_count":int(ledger.accepted.sum()) if not ledger.empty else 0,
             "rejected_count":int((~ledger.accepted).sum()) if not ledger.empty else 0,
             "ending_nlv":float(cash),"total_net_pnl":float(ledger.loc[ledger.accepted,"net_pnl"].sum()) if not ledger.empty else 0.0,
             "max_loss_pct":args.max_risk_pct,"max_bpr_pct":args.max_bpr_pct}
    if not ledger.empty:
        counts=ledger.loc[~ledger.accepted,"rejection_codes"].str.split(";").explode().value_counts()
        for k,v in counts.items():summary[f"reject_{k.lower()}"]=int(v)
        accepted=ledger[ledger.accepted]
        if not accepted.empty:
            summary["win_rate"]=float((accepted.net_pnl>0).mean())
            summary["worst_trade"]=float(accepted.net_pnl.min())
            summary["max_defined_loss"]=float(accepted.max_defined_loss.max())
    pd.DataFrame([summary]).to_csv(Path(args.output).with_name(Path(args.output).stem+"_summary.csv"),index=False)
    return ledger,summary

def main():
    a=parse_args()
    c=pd.read_csv(a.input);o=pd.read_csv(a.outcomes);m=pd.read_csv(a.marks)
    ledger,summary=replay(c,o,m,a)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);ledger.to_csv(a.output,index=False)
    print("OPTIONS-002 account feasibility",summary)

if __name__=="__main__":main()
