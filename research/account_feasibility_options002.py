"""Account feasibility replay for defined-risk OPTIONS-002.

BPR is modeled as maximum defined loss. This is a research estimate, not a
broker buying-power preview. One contract and one concurrent position are
used so account feasibility is measured without silently increasing size.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--outcomes",required=True);p.add_argument("--marks",required=True)
    p.add_argument("--starting-nlv",type=float,default=5000);p.add_argument("--max-bpr-pct",type=float,default=.50)
    p.add_argument("--max-risk-pct",type=float,default=.07);p.add_argument("--fee-per-contract",type=float,default=.65)
    p.add_argument("--output",required=True);return p.parse_args()

def replay(candidates,outcomes,marks,args):
    c=candidates.copy();o=outcomes.copy();m=marks.copy()
    c["entry_date"]=pd.to_datetime(c["entry_date"])
    o["exit_date"]=pd.to_datetime(o["exit_date"])
    m["date"]=pd.to_datetime(m["date"]) if not m.empty else pd.Series(dtype="datetime64[ns]")
    if o["candidate_id"].duplicated().any(): raise ValueError("duplicate outcome candidate_id")
    if not m.empty and m.duplicated(["candidate_id","date"]).any(): raise ValueError("duplicate mark candidate/date")
    c=c.merge(o[["candidate_id","exit_date","pnl","exit_debit"]],on="candidate_id",how="left",validate="one_to_one")
    marks_by={cid:g.sort_values("date") for cid,g in m.groupby("candidate_id")} if not m.empty else {}
    cash=float(args.starting_nlv);active=None;rows=[];snapshots=[]
    for _,r in c.sort_values(["entry_date","candidate_id"]).iterrows():
        entry=pd.Timestamp(r.entry_date)
        if active is not None and pd.Timestamp(active["exit_date"])<=entry:
            cash += float(active["exit_cash_flow"]); active=None
        nlv_before=cash if active is None else cash+float(active["position_value"])
        if active is not None:
            rows.append({"candidate_id":r.candidate_id,"entry_date":entry,"accepted":False,
                         "rejection_codes":"POSITION_ALREADY_OPEN","pre_trade_nlv":nlv_before})
            continue
        credit=float(r.entry_credit);max_loss=float(r.max_defined_loss);rejects=[]
        if credit<=0:rejects.append("NONPOSITIVE_CREDIT")
        if not pd.notna(r.exit_date):rejects.append("UNRESOLVED_LIFECYCLE_DATA")
        if max_loss>nlv_before*args.max_bpr_pct:rejects.append("BUYING_POWER_LIMIT")
        if max_loss>nlv_before*args.max_risk_pct:rejects.append("DEFINED_RISK_SIZE_LIMIT")
        if rejects:
            rows.append({"candidate_id":r.candidate_id,"entry_date":entry,"accepted":False,
                         "rejection_codes":";".join(rejects),"pre_trade_nlv":nlv_before,
                         "entry_credit":credit,"max_defined_loss":max_loss});continue
        fee=args.fee_per_contract*4
        cash += credit*100-fee
        exit_date=pd.Timestamp(r.exit_date);exit_debit=float(r.exit_debit)
        exit_cash_flow=-exit_debit*100-fee
        active={"candidate_id":r.candidate_id,"exit_date":exit_date,
                "position_value":-credit*100,"exit_cash_flow":exit_cash_flow}
        net_pnl=(credit-exit_debit)*100-fee*2
        rows.append({"candidate_id":r.candidate_id,"entry_date":entry,"accepted":True,
                     "rejection_codes":"","pre_trade_nlv":nlv_before,"entry_credit":credit,
                     "max_defined_loss":max_loss,"entry_fee":fee,"exit_fee":fee,
                     "exit_date":exit_date,"exit_debit":exit_debit,
                     "strategy_pnl":float(r.pnl),"net_pnl":net_pnl,
                     "post_trade_nlv":nlv_before+net_pnl})
        for _,mr in marks_by.get(r.candidate_id,pd.DataFrame()).iterrows():
            d=pd.Timestamp(mr.date)
            if d<entry or d>exit_date:continue
            debit=float(mr.mark_debit)
            mark_nlv=cash-debit*100
            snapshots.append({"date":d,"nlv":mark_nlv,"bpr":max_loss,
                               "bpr_pct":max_loss/mark_nlv if mark_nlv>0 else None})
        # Do not settle until the next candidate reaches/passes the exit date.
    if active is not None: cash += float(active["exit_cash_flow"])
    ledger=pd.DataFrame(rows)
    accepted=ledger[ledger.accepted] if not ledger.empty else ledger
    summary={"candidate_count":len(ledger),"accepted_count":int(ledger.accepted.sum()) if not ledger.empty else 0,
             "rejected_count":int((~ledger.accepted).sum()) if not ledger.empty else 0,
             "ending_nlv":float(cash),"total_net_pnl":float(accepted.net_pnl.sum()) if not accepted.empty else 0.0,
             "max_loss_pct":args.max_risk_pct,"max_bpr_pct":args.max_bpr_pct}
    if not ledger.empty:
        counts=ledger.loc[~ledger.accepted,"rejection_codes"].str.split(";").explode().value_counts()
        for k,v in counts.items():summary[f"reject_{k.lower()}"]=int(v)
        if not accepted.empty:
            summary["win_rate"]=float((accepted.net_pnl>0).mean())
            summary["worst_trade"]=float(accepted.net_pnl.min())
            summary["max_defined_loss"]=float(accepted.max_defined_loss.max())
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame([summary]).to_csv(out.with_name(out.stem+"_summary.csv"),index=False)
    return ledger,summary

def main():
    a=parse_args();c=pd.read_csv(a.input);o=pd.read_csv(a.outcomes);m=pd.read_csv(a.marks)
    ledger,summary=replay(c,o,m,a);Path(a.output).parent.mkdir(parents=True,exist_ok=True);ledger.to_csv(a.output,index=False)
    print("OPTIONS-002 account feasibility",summary)

if __name__=="__main__":main()
