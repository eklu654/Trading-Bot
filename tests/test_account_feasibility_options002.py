import pandas as pd
from argparse import Namespace
from research.account_feasibility_options002 import replay

def args():
    return Namespace(starting_nlv=5000,max_bpr_pct=.50,max_risk_pct=.07,fee_per_contract=.65,output="/tmp/test.csv")

def test_defined_risk_accepts_when_max_loss_fits():
    c=pd.DataFrame([{"candidate_id":"A","entry_date":"2020-01-02","entry_credit":0.50,"max_defined_loss":150}])
    o=pd.DataFrame([{"candidate_id":"A","exit_date":"2020-01-10","pnl":50,"exit_debit":0.0}])
    m=pd.DataFrame([{"candidate_id":"A","date":"2020-01-05","mark_debit":0.2}])
    ledger,s=replay(c,o,m,args())
    assert bool(ledger.iloc[0].accepted)
    assert s["accepted_count"]==1
    assert s["max_mark_bpr_pct"] > 0

def test_defined_risk_rejects_above_small_account_risk_band():
    c=pd.DataFrame([{"candidate_id":"A","entry_date":"2020-01-02","entry_credit":0.50,"max_defined_loss":500}])
    o=pd.DataFrame([{"candidate_id":"A","exit_date":"2020-01-10","pnl":50,"exit_debit":0.0}])
    m=pd.DataFrame(columns=["candidate_id","date","mark_debit"])
    ledger,s=replay(c,o,m,args())
    assert not bool(ledger.iloc[0].accepted)
    assert "DEFINED_RISK_SIZE_LIMIT" in ledger.iloc[0].rejection_codes

def test_same_day_exit_does_not_permit_reentry():
    c=pd.DataFrame([
        {"candidate_id":"A","entry_date":"2020-01-02","entry_credit":0.50,"max_defined_loss":150},
        {"candidate_id":"B","entry_date":"2020-01-10","entry_credit":0.50,"max_defined_loss":150},
    ])
    o=pd.DataFrame([
        {"candidate_id":"A","exit_date":"2020-01-10","pnl":50,"exit_debit":0.0},
        {"candidate_id":"B","exit_date":"2020-01-20","pnl":50,"exit_debit":0.0},
    ])
    m=pd.DataFrame(columns=["candidate_id","date","mark_debit"])
    ledger,s=replay(c,o,m,args())
    b=ledger.loc[ledger["candidate_id"]=="B"].iloc[0]
    assert not bool(b.accepted)
    assert "POSITION_ALREADY_OPEN" in b.rejection_codes
