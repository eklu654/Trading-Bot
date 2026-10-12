import unittest
from alpaca_paper_order_executor import order_payload, ExecutorBlocked, PAPER_URL

class PaperOrderPayloadTests(unittest.TestCase):
    def intent(self, **changes):
        x={"endpoint":PAPER_URL,"mode":"PLAN_ONLY_NO_SUBMISSION","symbol":"TQQQ",
           "side":"buy","qty":"61.450","client_order_id":"tb-0123456789abcdef0123456789abcdef"}
        x.update(changes)
        return x
    def test_payload_is_paper_market_day_order(self):
        self.assertEqual(order_payload(self.intent()),{
            "symbol":"TQQQ","qty":"61.450","side":"buy","type":"market",
            "time_in_force":"day","client_order_id":"tb-0123456789abcdef0123456789abcdef"})
    def test_live_endpoint_is_rejected(self):
        with self.assertRaisesRegex(ExecutorBlocked,"paper-only"):
            order_payload(self.intent(endpoint="https://api.alpaca.markets"))
    def test_wrong_symbol_or_side_is_rejected(self):
        with self.assertRaisesRegex(ExecutorBlocked,"symbol or side"):
            order_payload(self.intent(symbol="SOXL"))
        with self.assertRaisesRegex(ExecutorBlocked,"symbol or side"):
            order_payload(self.intent(side="short"))
    def test_zero_negative_and_nonfinite_quantity_are_rejected(self):
        for qty in ("0","-1","NaN"):
            with self.subTest(qty=qty),self.assertRaises(ExecutorBlocked):
                order_payload(self.intent(qty=qty))
    def test_invalid_client_order_id_is_rejected(self):
        with self.assertRaisesRegex(ExecutorBlocked,"client order ID"):
            order_payload(self.intent(client_order_id="not-a-bot-id"))

if __name__=="__main__": unittest.main()
