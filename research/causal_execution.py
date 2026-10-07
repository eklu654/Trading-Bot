"""Single source of truth for causal close-to-next-open execution.

Convention:
    signal at close[t] -> executable at open[t+1]

Therefore on session t:
    overnight close[t-1] -> open[t] uses the position held before open[t]
    intraday open[t] -> close[t] uses the position executed at open[t]

Never replace this with a same-day signal multiplication.
"""
import numpy as np

def next_open_daily_returns(signal, overnight, intraday):
    w=np.asarray(signal,float)
    on=np.asarray(overnight,float)
    inn=np.asarray(intraday,float)
    if not (len(w)==len(on)==len(inn)):
        raise ValueError("signal, overnight, and intraday must have equal length")
    exec_w=np.roll(w,1)
    exec_w[0]=0.0
    prev_exec=np.roll(exec_w,1)
    prev_exec[0]=0.0
    return (1.0 + prev_exec*on) * (1.0 + exec_w*inn) - 1.0

def next_open_equity(signal, overnight, intraday, initial=5000.0):
    daily=next_open_daily_returns(signal, overnight, intraday)
    return initial*np.cumprod(1.0+daily)

def next_open_cost_daily_returns(signal, overnight, intraday, bps):
    daily=next_open_daily_returns(signal, overnight, intraday)
    w=np.asarray(signal,float)
    exec_w=np.roll(w,1)
    exec_w[0]=0.0
    prev_exec=np.roll(exec_w,1)
    prev_exec[0]=0.0
    return daily-np.abs(exec_w-prev_exec)*(bps/10000.0)


def next_open_cost_equity(signal, overnight, intraday, bps, initial=5000.0):
    """Equity with execution costs charged when next-open exposure changes.

    Order on session t:
      1) earn the overnight return on the position held before open[t]
      2) pay transaction cost on the exposure change at open[t]
      3) earn the intraday return on the newly executed exposure
    """
    w=np.asarray(signal,float)
    on=np.asarray(overnight,float)
    inn=np.asarray(intraday,float)
    if not (len(w)==len(on)==len(inn)):
        raise ValueError("signal, overnight, and intraday must have equal length")
    exec_w=np.roll(w,1)
    exec_w[0]=0.0
    prev_exec=np.roll(exec_w,1)
    prev_exec[0]=0.0
    cost=np.abs(exec_w-prev_exec)*(bps/10000.0)
    wealth=np.empty(len(w),dtype=float)
    value=float(initial)
    for i in range(len(w)):
        value *= 1.0 + prev_exec[i]*on[i]
        value *= 1.0 - cost[i]
        value *= 1.0 + exec_w[i]*inn[i]
        wealth[i]=value
    return wealth
