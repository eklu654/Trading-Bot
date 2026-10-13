import unittest
from datetime import datetime, timezone
from decimal import Decimal
from qqq_intraday_monitor import evaluate, MonitorError

class IntradayMonitorTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime.fromisoformat("2026-10-12T14:00:00+00:00")
        self.clock={"is_open":True}
        self.trade={"trade":{"t":"2026-10-12T13:59:30+00:00","p":"95.49"}}
        self.bars=[
            {"t":"2026-10-08T00:00:00Z","c":"100"},
            {"t":"2026-10-09T00:00:00Z","c":"100"},
            {"t":"2026-10-12T00:00:00Z","c":"99"}
        ]
    def test_breach_at_or_below_minus_4_5_percent(self):
        r=evaluate(self.clock,self.trade,self.bars,self.now)
        self.assertEqual(r["status"],"THRESHOLD_BREACHED")
        self.assertTrue(r["threshold_breached"])
        self.assertEqual(r["prior_completed_session"],"2026-10-09")
        self.assertEqual(r["session"],"2026-10-12")
        self.assertEqual(r["qqq_price"],"95.49")
        self.assertEqual(r["prior_close"],"100")
        self.assertEqual(r["threshold_pct"],"4.5")
        self.assertFalse(r["orders_submitted"])
    def test_no_breach_above_threshold(self):
        trade={"trade":{"t":"2026-10-12T13:59:30+00:00","p":"95.51"}}
        r=evaluate(self.clock,trade,self.bars,self.now)
        self.assertEqual(r["status"],"MONITORING")
        self.assertFalse(r["threshold_breached"])
    def test_closed_market_does_not_need_trade_or_bars(self):
        r=evaluate({"is_open":False},{},[],self.now)
        self.assertEqual(r["status"],"MARKET_CLOSED")
    def test_stale_trade_fails_closed(self):
        trade={"trade":{"t":"2026-10-12T13:50:00+00:00","p":"95"}}
        r=evaluate(self.clock,trade,self.bars,self.now)
        self.assertEqual(r["status"],"STALE_TRADE_FAIL_CLOSED")
    def test_missing_prior_completed_close_fails_closed(self):
        with self.assertRaisesRegex(MonitorError,"no completed prior-session"):
            evaluate(self.clock,self.trade,[{"t":"2026-10-12T00:00:00Z","c":"100"}],self.now)
    def test_bad_trade_timestamp_fails_closed(self):
        with self.assertRaisesRegex(MonitorError,"timestamp invalid"):
            evaluate(self.clock,{"trade":{"t":"bad","p":"95"}},self.bars,self.now)
    def test_prior_close_selection_ignores_current_day_bar(self):
        r=evaluate(self.clock,self.trade,self.bars,self.now)
        self.assertEqual(r["prior_close"],"100")
    def test_exact_threshold_is_breach(self):
        trade={"trade":{"t":"2026-10-12T13:59:30+00:00","p":"95.5"}}
        r=evaluate(self.clock,trade,self.bars,self.now)
        self.assertEqual(r["status"],"THRESHOLD_BREACHED")

if __name__=="__main__": unittest.main()
