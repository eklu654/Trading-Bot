import pandas as pd
import pytest

from research.account_feasibility_replay import (
    FeasibilityConfig,
    estimate_short_strangle_bpr,
    max_stress_loss,
    replay,
)


def candidate(**overrides):
    row = {
        "entry_date": "2020-01-02",
        "exit_date": "2020-01-10",
        "entry_credit": 2.00,
        "pnl": 50.00,
        "call_strike": 500.0,
        "put_strike": 200.0,
        "underlying_close": 320.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_cash_flow_signs_and_nlv_reconcile():
    ledger, summary = replay(candidate(), FeasibilityConfig(starting_nlv=2000, max_bpr_pct_nlv=2.0))
    row = ledger.iloc[0]
    assert row.accepted
    assert row.net_pnl == pytest.approx(47.40)
    assert row.post_trade_nlv == pytest.approx(2047.40)
    assert summary["ending_nlv"] == pytest.approx(2047.40)


def test_quantity_is_implicitly_one_integer_contract():
    ledger, _ = replay(candidate(), FeasibilityConfig(starting_nlv=2000, max_bpr_pct_nlv=2.0))
    assert len(ledger) == 1
    assert ledger.iloc[0].accepted


def test_buying_power_gate_rejects_candidate():
    ledger, summary = replay(
        candidate(underlying_close=500.0, call_strike=510.0, put_strike=490.0),
        FeasibilityConfig(starting_nlv=2000, max_bpr_pct_nlv=0.25),
    )
    assert not ledger.iloc[0].accepted
    assert "BUYING_POWER_LIMIT" in ledger.iloc[0].rejection_codes
    assert summary["ending_nlv"] == pytest.approx(2000)


def test_rejected_opportunity_is_retained():
    candidates = pd.concat([
        candidate(),
        candidate(entry_date="2020-01-03", exit_date="2020-01-12",
                   underlying_close=float("nan")),
    ], ignore_index=True)
    ledger, summary = replay(candidates, FeasibilityConfig())
    assert len(ledger) == 2
    assert "MISSING_UNDERLYING_PRICE" in ledger.iloc[1].rejection_codes
    assert summary["candidate_count"] == 2


def test_no_trade_path_is_valid():
    empty = candidate(underlying_close=float("nan"))
    ledger, summary = replay(empty, FeasibilityConfig())
    assert len(ledger) == 1
    assert summary["accepted_count"] == 0
    assert summary["rejected_count"] == 1
    assert summary["ending_nlv"] == pytest.approx(2000)


def test_bpr_is_deterministic_and_positive():
    value = estimate_short_strangle_bpr(320, 300, 340, 2)
    assert value > 0
    assert value == estimate_short_strangle_bpr(320, 300, 340, 2)


def test_stress_loss_is_explicit():
    loss = max_stress_loss(320, 300, 340, 2)
    assert loss > 0


def test_missing_required_columns_fail_fast():
    with pytest.raises(ValueError):
        replay(pd.DataFrame([{"entry_date": "2020-01-01"}]), FeasibilityConfig())


def test_account_replay_uses_independent_lifecycle_and_retains_overlap_rejection():
    candidates = pd.DataFrame([
        {
            "candidate_id": "A",
            "entry_date": "2020-01-02",
            "entry_credit": 2.0,
            "call_strike": 500.0,
            "put_strike": 200.0,
            "underlying_close": 320.0,
        },
        {
            "candidate_id": "B",
            "entry_date": "2020-01-03",
            "entry_credit": 2.0,
            "call_strike": 500.0,
            "put_strike": 200.0,
            "underlying_close": 320.0,
        },
        {
            "candidate_id": "C",
            "entry_date": "2020-01-20",
            "entry_credit": 2.0,
            "call_strike": 500.0,
            "put_strike": 200.0,
            "underlying_close": 320.0,
        },
    ])
    outcomes = pd.DataFrame([
        {"candidate_id": "A", "exit_date": "2020-01-10", "pnl": 50.0},
        {"candidate_id": "B", "exit_date": "2020-01-12", "pnl": 50.0},
        # C deliberately has no lifecycle row: it must remain auditable rather
        # than being silently dropped or treated as a zero-profit trade.
    ])

    ledger, summary = replay(
        candidates,
        FeasibilityConfig(starting_nlv=2000, max_bpr_pct_nlv=2.0),
        outcomes,
    )

    assert set(ledger["candidate_id"]) == {"A", "B", "C"}
    assert ledger["candidate_id"].is_unique
    assert ledger.loc[ledger["candidate_id"] == "A", "accepted"].iloc[0]
    assert not ledger.loc[ledger["candidate_id"] == "B", "accepted"].iloc[0]
    assert "POSITION_ALREADY_OPEN" in ledger.loc[
        ledger["candidate_id"] == "B", "rejection_codes"
    ].iloc[0]
    assert not ledger.loc[ledger["candidate_id"] == "C", "accepted"].iloc[0]
    assert "UNRESOLVED_LIFECYCLE_DATA" in ledger.loc[
        ledger["candidate_id"] == "C", "rejection_codes"
    ].iloc[0]
    assert summary["candidate_count"] == 3
    assert summary["accepted_count"] == 1


def test_pnl_mismatch_is_rejected_and_auditable():
    candidates = pd.DataFrame([{
        "candidate_id": "MISMATCH",
        "entry_date": "2020-01-02",
        "entry_credit": 2.0,
        "call_strike": 500.0,
        "put_strike": 200.0,
        "underlying_close": 320.0,
    }])
    outcomes = pd.DataFrame([{
        "candidate_id": "MISMATCH",
        "exit_date": "2020-01-10",
        "exit_debit": 1.00,
        "pnl": 40.0,
    }])
    ledger, summary = replay(
        candidates,
        FeasibilityConfig(starting_nlv=2000, max_bpr_pct_nlv=2.0),
        outcomes,
    )
    row = ledger.iloc[0]
    assert not row.accepted
    assert "PNL_RECONCILIATION_MISMATCH" in row.rejection_codes
    assert row.pnl_reconciliation_residual == pytest.approx(-60.0)
    assert summary["ending_nlv"] == pytest.approx(2000.0)


def test_overlapping_positions_use_open_position_state_and_settle_later():
    candidates = pd.DataFrame([
        {
            "candidate_id": "A", "entry_date": "2020-01-02", "entry_credit": 2.0,
            "call_strike": 500.0, "put_strike": 200.0, "underlying_close": 320.0,
        },
        {
            "candidate_id": "B", "entry_date": "2020-01-03", "entry_credit": 2.0,
            "call_strike": 500.0, "put_strike": 200.0, "underlying_close": 320.0,
        },
    ])
    outcomes = pd.DataFrame([
        {"candidate_id": "A", "exit_date": "2020-01-10", "pnl": 50.0},
        {"candidate_id": "B", "exit_date": "2020-01-12", "pnl": 50.0},
    ])
    ledger, summary = replay(
        candidates,
        FeasibilityConfig(starting_nlv=2000, max_bpr_pct_nlv=2.0, max_concurrent_positions=2),
        outcomes,
    )
    a = ledger.loc[ledger["candidate_id"] == "A"].iloc[0]
    b = ledger.loc[ledger["candidate_id"] == "B"].iloc[0]
    assert a.accepted and b.accepted
    assert b.pre_trade_nlv == pytest.approx(1998.70)
    assert b.nlv_after_entry == pytest.approx(1997.40)
    assert a.post_exit_nlv == pytest.approx(2046.10)
    assert b.post_exit_nlv == pytest.approx(2094.80)
    assert summary["ending_nlv"] == pytest.approx(2094.80)
