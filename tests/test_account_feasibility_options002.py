import pandas as pd
from argparse import Namespace
from research.account_feasibility_options002 import replay

def test_defined_risk_accepts_when_max_loss_fits():
    c=pd.DataFrame([{"candidate_id":"A","entry_date":"2020-01-02","entry_credit":0.50,"max_defined_loss":150}])
    o=pd.DataFrame([{"candidate_id":"A","exit_date":"2020-01-10","pnl":50,"exit_debit":0.0}])
    m=pd.DataFrame([{"candidate_id":"A","date":"2020-01-05","mark_debit":0.2}])
    a=Namespace(starting_nlv=5000,max_bpr_pct=.50,max_risk_pct=.07,fee_per_contract=.65)
    ledger,s=replay(c,o,m,a)
    assert bool(ledger.iloc[0].accepted)
    assert s["accepted_count"]==1

def test_defined_risk_rejects_above_small_account_risk_band():
    c=pd.DataFrame([{"candidate_id":"A","entry_date":"2020-01-02","entry_credit":0.50,"max_defined_loss":500}])
    o=pd.DataFrame([{"candidate_id":"A","exit_date":"2020-01-10","pnl":50,"exit_debit":0.0}])
    m=pd.DataFrame(columns=["candidate_id","date","mark_debit"])
    a=Namespace(starting_nlv=5000,max_bpr_pct=.50,max_risk_pct=.07,fee_per_contract=.65)
    ledger,s=replay(c,o,m,a)
    assert not bool(ledger.iloc[0].accepted)
    assert "DEFINED_RISK_SIZE_LIMIT" in ledger.iloc[0].rejection_codes
