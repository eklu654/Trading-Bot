# Near-Ruin Audit Follow-up: CAGR Denominator Check

Date: 2026-10-09

The robustness and independent-audit jobs agree on ending equity (approximately $4.040315M versus $4.040317M) and maximum drawdown (-73.5343%), but print different CAGRs (49.4874% versus 49.0757%). Source inspection explains the discrepancy: `research/failed_bounce_robustness.py` computes years from the first and last aligned market-data timestamps for its headline summary, while `research/audit_failed_bounce_canonical_independent.py` uses the fixed requested interval from 2010-01-01 through 2026-10-08. Therefore, the ending balance and drawdown reconcile, but CAGR should not be described as matching. Standardize the CAGR denominator to the actual aligned start/end dates (and report both dates) before treating the two CAGR values as a reconciliation pass.

No strategy conclusion changes from this issue, and no new backtest was run for this note.
