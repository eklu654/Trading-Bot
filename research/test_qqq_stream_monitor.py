import tempfile, unittest
from datetime import datetime
from pathlib import Path
from qqq_stream_monitor import EventStore, MonitorError, evaluate_trade

class StreamMonitorTests(unittest.TestCase):
    def now(self): return datetime.fromisoformat("2026-10-12T14:00:00+00:00")
    def test_breach_at_exact_threshold(self):
        r=evaluate_trade("95.5","100","2026-10-12T13:59:59Z",self.now())
        self.assertEqual(r["status"],"THRESHOLD_BREACHED")
        self.assertFalse(r["orders_submitted"])
    def test_no_breach_above_threshold(self):
        self.assertEqual(evaluate_trade("95.51","100","2026-10-12T13:59:59Z",self.now())["status"],"MONITORING")
    def test_stale_trade_fails_closed(self):
        self.assertEqual(evaluate_trade("95","100","2026-10-12T13:55:00Z",self.now())["status"],"STALE_TRADE_FAIL_CLOSED")
    def test_future_trade_fails_closed(self):
        self.assertEqual(evaluate_trade("95","100","2026-10-12T14:01:00Z",self.now())["status"],"STALE_TRADE_FAIL_CLOSED")
    def test_rejects_bad_price(self):
        with self.assertRaises(MonitorError): evaluate_trade("NaN","100","2026-10-12T13:59:59Z",self.now())
    def test_rejects_timezone_naive_timestamp(self):
        with self.assertRaises(MonitorError): evaluate_trade("95","100","2026-10-12T13:59:59",self.now())
    def test_outside_regular_session_ignored(self):
        r=evaluate_trade("90","100","2026-10-12T12:00:00Z",datetime.fromisoformat("2026-10-12T12:00:01+00:00"))
        self.assertEqual(r["status"],"OUTSIDE_REGULAR_SESSION")
    def test_event_store_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=EventStore(str(Path(tmp)/"events.sqlite3"))
            self.assertTrue(store.record_once("2026-10-12","THRESHOLD_BREACHED",{"status":"THRESHOLD_BREACHED"}))
            self.assertFalse(store.record_once("2026-10-12","THRESHOLD_BREACHED",{"status":"THRESHOLD_BREACHED"}))
            store.close()
    def test_event_store_recovery_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=EventStore(str(Path(tmp)/"events.sqlite3"))
            self.assertTrue(store.record_once("2026-10-12","THRESHOLD_BREACHED",{"x":1}))
            self.assertTrue(store.record_once("2026-10-12","RECOVERED_ABOVE_THRESHOLD",{"x":2}))
            store.close()

if __name__=="__main__": unittest.main(verbosity=2)
