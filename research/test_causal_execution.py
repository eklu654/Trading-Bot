import numpy as np
from causal_execution import next_open_daily_returns, next_open_equity

def test_close_signal_cannot_capture_pre_execution_overnight():
    signal=np.array([0.0,1.0,0.0])
    overnight=np.array([0.0,0.10,0.20])
    intraday=np.array([0.0,0.30,0.40])
    daily=next_open_daily_returns(signal,overnight,intraday)
    # The signal set at close of day 1 executes at open of day 2.
    # Therefore day-2 overnight still has zero exposure; day-2 intraday has 1x.
    np.testing.assert_allclose(daily,[0.0,0.0,0.40])

def test_buy_hold_owns_overnight_after_initial_execution():
    signal=np.ones(4)
    overnight=np.array([0.0,0.10,0.20,0.05])
    intraday=np.array([0.02,0.03,0.04,0.01])
    daily=next_open_daily_returns(signal,overnight,intraday)
    expected=np.array([
        0.02,
        (1.10)*(1.03)-1,
        (1.20)*(1.04)-1,
        (1.05)*(1.01)-1,
    ])
    np.testing.assert_allclose(daily,expected)

def test_equity_matches_daily_returns():
    signal=np.array([0.0,1.0,1.0])
    overnight=np.array([0.0,0.10,0.20])
    intraday=np.array([0.0,0.30,0.40])
    eq=next_open_equity(signal,overnight,intraday,5000.0)
    assert eq[-1] == 7000.0
