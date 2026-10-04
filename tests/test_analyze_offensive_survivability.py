from pathlib import Path
import importlib.util
import pandas as pd
import numpy as np
p=Path(__file__).parents[1]/"research"/"analyze_offensive_survivability.py"
s=importlib.util.spec_from_file_location("m",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def test_windows_and_positive_path():
    idx=pd.date_range("2010-01-01",periods=2600,freq="B")
    ret=pd.Series(.0005,index=idx)
    detail,summary=m.rolling(ret,"TEST")
    assert set(summary.window)==set(m.WINDOWS)
    assert (summary.worst_rolling_cagr>0).all()
    assert (summary.dd_breach_50pct==0).all()
    assert len(detail)==sum(len(ret)-w+1 for w in m.WINDOWS.values())

def test_severe_drawdown_breach():
    idx=pd.date_range("2010-01-01",periods=252,freq="B")
    ret=pd.Series(0.0,index=idx); ret.iloc[100]=-.9
    _,summary=m.rolling(ret,"TEST")
    row=summary.iloc[0]
    assert row.worst_rolling_drawdown<=-.9
    assert row.dd_breach_80pct>0
