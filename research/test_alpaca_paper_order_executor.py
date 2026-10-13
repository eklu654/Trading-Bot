import unittest, os, json, tempfile, argparse
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch
import alpaca_paper_order_executor as executor
from alpaca_paper_order_executor import (order_payload, account_fingerprint, effective_target, ExecutorBlocked, PaperPostError, PAPER_URL)
from paper_virtual_portfolio import (new_state, mark_to_market, plan_target, stage_intent,
    mark_submission_attempting, state_json, activate_emergency_exit_latch)

class PaperOrderPayloadTests(unittest.TestCase):
    def intent(self, **changes):
        x={"endpoint":PAPER_URL,"mode":"PLAN_ONLY_NO_SUBMISSION","symbol":"TQQQ",
           "side":"buy","qty":"61.450","client_order_id":"tb-0123456789abcdef0123456789abcdef"}
        x.update(changes)
        return x

    def test_emergency_latch_forces_both_portfolios_flat(self):
        latch = {"active": True, "reason": "QQQ_MINUS_4_5_PERCENT"}
        b0_strategy, b0_target, b0_active = effective_target(
            "b0", Decimal("1"), Decimal("1"), {"emergency_exit_latch": latch})
        f75_strategy, f75_target, f75_active = effective_target(
            "f75", Decimal("1"), Decimal("0.75"), {"emergency_exit_latch": latch})
        self.assertEqual(b0_strategy, Decimal("1"))
        self.assertEqual(f75_strategy, Decimal("0.75"))
        self.assertEqual(b0_target, Decimal("0"))
        self.assertEqual(f75_target, Decimal("0"))
        self.assertTrue(b0_active)
        self.assertTrue(f75_active)

    def test_no_emergency_latch_preserves_strategy_targets(self):
        self.assertEqual(
            effective_target("b0", Decimal("1"), Decimal("1"), {}),
            (Decimal("1"), Decimal("1"), False))
        self.assertEqual(
            effective_target("f75", Decimal("1"), Decimal("0.75"), {}),
            (Decimal("0.75"), Decimal("0.75"), False))

    def qqq_api_responses(self, price="95.49", trade_time="2026-10-12T13:59:30+00:00"):
        return [
            {"is_open": True},
            {"bars": [
                {"t": "2026-10-08T00:00:00Z", "c": "100"},
                {"t": "2026-10-09T00:00:00Z", "c": "100"},
                {"t": "2026-10-12T00:00:00Z", "c": "99"}]},
            {"trade": {"t": trade_time, "p": price}},
        ]

    def test_qqq_preflight_activates_latch_on_intraday_breach(self):
        now=datetime.fromisoformat("2026-10-12T14:00:00+00:00")
        with patch.object(executor,"get_json",side_effect=self.qqq_api_responses()):
            result=executor.qqq_defense_preflight("key","secret",now,new_state("b0"))
        self.assertEqual(result["status"],"THRESHOLD_BREACHED")
        self.assertTrue(result["active"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["state"]["emergency_exit_latch"]["qqq_price"],"95.49")

    def test_qqq_preflight_fails_closed_on_stale_trade(self):
        now=datetime.fromisoformat("2026-10-12T14:00:00+00:00")
        with patch.object(executor,"get_json",side_effect=self.qqq_api_responses(
                price="95",trade_time="2026-10-12T13:50:00+00:00")), \
             self.assertRaisesRegex(ExecutorBlocked,"stale or invalid"):
            executor.qqq_defense_preflight("key","secret",now,new_state("b0"))

    def test_qqq_stale_observation_preserves_existing_defense_latch(self):
        now=datetime.fromisoformat("2026-10-12T14:00:00+00:00")
        state=activate_emergency_exit_latch(new_state("b0"),trigger_session="2026-10-12",
            qqq_price="95.5",prior_close="100",trigger_sha256="c"*64)
        with patch.object(executor,"get_json",side_effect=self.qqq_api_responses(
                price="95",trade_time="2026-10-12T13:50:00+00:00")):
            result=executor.qqq_defense_preflight("key","secret",now,state)
        self.assertEqual(result["status"],"STALE_TRADE_FAIL_CLOSED")
        self.assertTrue(result["active"])
        self.assertEqual(result["state"]["emergency_exit_latch"]["trigger_sha256"],"c"*64)

    def test_qqq_preflight_tracks_lower_trough_while_latched(self):
        now=datetime.fromisoformat("2026-10-12T14:00:00+00:00")
        state=activate_emergency_exit_latch(new_state("b0"),trigger_session="2026-10-12",
            qqq_price="95.5",prior_close="100",trigger_sha256="a"*64)
        with patch.object(executor,"get_json",side_effect=self.qqq_api_responses(price="90")):
            result=executor.qqq_defense_preflight("key","secret",now,state)
        self.assertTrue(result["active"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["state"]["emergency_exit_latch"]["trough_price"],"90")

    def test_submit_aborts_buy_if_last_moment_qqq_check_triggers(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root,submitting=True)
            intent=state["pending_intent"]
            a=self.args(root,state_path=state_path)
            Path(a.request).write_text(json.dumps(intent))
            Path(a.permit).write_text(json.dumps({"client_order_id":intent["client_order_id"],"permit":"single-run-only"}))
            latched=activate_emergency_exit_latch(state,trigger_session="2026-10-12",
                qqq_price="95.5",prior_close="100",trigger_sha256="b"*64)
            normal={"status":"MONITORING","active":False,"breached":False,
                    "changed":False,"state":state}
            preflight={"status":"THRESHOLD_BREACHED","active":True,"breached":True,
                       "changed":True,"state":latched}
            ctx={"price":Decimal(intent["reference_price"]),"trade_age":1,"open_orders":[]}
            with patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"get_json",side_effect=[None,[]]), \
                 patch.object(executor,"read_signal",return_value=("2026-10-09",Decimal("1"),Decimal("1"),"hash")), \
                 patch.object(executor,"qqq_defense_preflight",side_effect=[normal,preflight]), \
                 patch.object(executor,"broker_context",return_value=ctx), \
                 patch.object(executor,"post_order") as post:
                executor.submit(a)
            post.assert_not_called()
            final=json.loads(state_path.read_text())
            self.assertIsNone(final["pending_intent"])
            self.assertTrue(final["emergency_exit_latch"]["active"])
            self.assertEqual(json.loads(Path(a.report).read_text())["status"],"ABORTED_BUY_DURING_QQQ_DEFENSE")

    def test_account_fingerprint_is_stable_and_not_raw_id(self):
        a=account_fingerprint("account-uuid-b0")
        self.assertEqual(a,account_fingerprint("account-uuid-b0"))
        self.assertNotEqual(a,account_fingerprint("account-uuid-f75"))
        self.assertNotIn("account-uuid-b0",a)
        with self.assertRaisesRegex(ExecutorBlocked,"identity is missing"):
            account_fingerprint("")
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


    def files(self, root, portfolio="b0", submitting=False):
        state=mark_to_market(new_state(portfolio),"2026-10-09","100")
        if submitting:
            weight="1" if portfolio=="b0" else "0.75"
            intent=plan_target(state,signal_session="2026-10-09",target_weight=weight,
                               reference_price="100",baseline_weight="1" if portfolio=="f75" else None)
            state=stage_intent(state,intent)
            state=mark_submission_attempting(state)
        state_path=Path(root)/f"{portfolio}_state.json"
        state_path.write_text(state_json(state)+"\n",encoding="utf-8")
        return state_path,state

    def args(self, root, portfolio="b0", state_path=None):
        return argparse.Namespace(portfolio=portfolio,state=str(state_path or Path(root)/f"{portfolio}_state.json"),
            ledger=str(Path(root)/"shadow.csv"),manifest=str(Path(root)/"shadow-state.json"),
            request=str(Path(root)/f"request-{portfolio}.json"),permit=str(Path(root)/f"permit-{portfolio}.json"),
            report=str(Path(root)/f"report-{portfolio}.json"),
            state_b0=str(Path(root)/"b0_state.json"),state_f75=str(Path(root)/"f75_state.json"))

    def test_prepare_push_run_is_dry_run_and_does_not_stage(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,_=self.files(root)
            a=self.args(root,state_path=state_path)
            with patch.dict(os.environ,{"ENABLE_PAPER_ORDER_SUBMISSION":"false"}), \
                 patch.object(executor,"read_signal",return_value=("2026-10-09",Decimal("1"),Decimal("1"),"hash")), \
                 patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"broker_context",return_value={"price":Decimal("100"),"trade_age":1}):
                executor.prepare(a)
            state=json.loads(state_path.read_text())
            self.assertIsNone(state["pending_intent"])
            self.assertFalse(Path(a.request).exists())
            self.assertEqual(json.loads(Path(a.report).read_text())["status"],"DRY_RUN_INTENT")

    def test_prepare_scheduled_run_persists_staged_intent(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root)
            a=self.args(root,state_path=state_path)
            qqq_ok={"status":"MONITORING","active":False,"breached":False,"changed":False,"state":state}
            with patch.dict(os.environ,{"ENABLE_PAPER_ORDER_SUBMISSION":"true"}), \
                 patch.object(executor,"read_signal",return_value=("2026-10-09",Decimal("1"),Decimal("1"),"hash")), \
                 patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"qqq_defense_preflight",return_value=qqq_ok), \
                 patch.object(executor,"broker_context",return_value={"price":Decimal("100"),"trade_age":1}):
                executor.prepare(a)
            state=json.loads(state_path.read_text())
            self.assertEqual(state["pending_intent"]["submission_state"],"STAGED")
            self.assertTrue(Path(a.request).exists())

    def test_arm_persists_submitting_before_post(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root)
            intent=plan_target(state,signal_session="2026-10-09",target_weight="1",reference_price="100")
            staged=stage_intent(state,intent)
            state_path.write_text(state_json(staged)+"\n")
            a=self.args(root,state_path=state_path)
            Path(a.request).write_text(json.dumps(intent))
            executor.arm(a)
            self.assertEqual(json.loads(state_path.read_text())["pending_intent"]["submission_state"],"SUBMITTING")
            self.assertTrue(Path(a.permit).exists())

    def test_submit_without_ephemeral_permit_never_posts(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root,submitting=True)
            a=self.args(root,state_path=state_path)
            with patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"get_json",return_value=None), \
                 patch.object(executor,"post_order") as post:
                executor.submit(a)
            post.assert_not_called()
            self.assertEqual(json.loads(state_path.read_text())["pending_intent"]["submission_state"],"UNKNOWN")

    def test_submit_with_permit_posts_once_and_persists_broker_id(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root,submitting=True)
            intent=state["pending_intent"]
            a=self.args(root,state_path=state_path)
            Path(a.request).write_text(json.dumps(intent))
            Path(a.permit).write_text(json.dumps({"client_order_id":intent["client_order_id"],"permit":"single-run-only"}))
            response={"id":"broker-123","client_order_id":intent["client_order_id"],"status":"new"}
            ctx={"price":Decimal(intent["reference_price"]),"trade_age":1,"open_orders":[]}
            with patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"get_json",side_effect=[None,[],[]]), \
                 patch.object(executor,"read_signal",return_value=("2026-10-09",Decimal("1"),Decimal("1"),"hash")), \
                 patch.object(executor,"qqq_defense_preflight",return_value={"status":"MONITORING","active":False,"breached":False,"changed":False,"state":state}), \
                 patch.object(executor,"broker_context",return_value=ctx), \
                 patch.object(executor,"post_order",return_value=response) as post:
                executor.submit(a)
            post.assert_called_once_with(order_payload(intent),"key","secret")
            final=json.loads(state_path.read_text())
            self.assertEqual(final["pending_intent"]["broker_order_id"],"broker-123")
            self.assertEqual(final["pending_intent"]["submission_state"],"NEW")
            self.assertEqual(json.loads(Path(a.report).read_text())["status"],"SUBMITTED")

    def test_active_latch_allows_defensive_sell_when_qqq_feed_is_stale(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root)
            state["qty"]="10.000"
            state["cash"]="4000.00"
            state["equity"]="5000.00"
            intent=plan_target(state,signal_session="2026-10-09",target_weight="0",reference_price="100")
            state=stage_intent(state,intent)
            state=mark_submission_attempting(state)
            state=activate_emergency_exit_latch(state,trigger_session="2026-10-12",
                qqq_price="95.5",prior_close="100",trigger_sha256="d"*64)
            state_path.write_text(state_json(state)+"\n",encoding="utf-8")
            a=self.args(root,state_path=state_path)
            Path(a.request).write_text(json.dumps(intent))
            Path(a.permit).write_text(json.dumps({"client_order_id":intent["client_order_id"],"permit":"single-run-only"}))
            stale={"status":"STALE_TRADE_FAIL_CLOSED","active":True,"breached":False,
                   "changed":False,"state":state}
            ctx={"price":Decimal("100"),"trade_age":1,"open_orders":[]}
            response={"id":"broker-sell-123","client_order_id":intent["client_order_id"],"status":"new"}
            with patch.object(executor,"credentials",return_value=("key","secret")), \\
                 patch.object(executor,"get_json",side_effect=[None,[]]), \\
                 patch.object(executor,"read_signal",return_value=("2026-10-09",Decimal("1"),Decimal("1"),"hash")), \\
                 patch.object(executor,"qqq_defense_preflight",side_effect=[stale,stale]), \\
                 patch.object(executor,"broker_context",return_value=ctx), \\
                 patch.object(executor,"reconcile_order_fills",return_value=state), \\
                 patch.object(executor,"post_order",return_value=response) as post:
                executor.submit(a)
            post.assert_called_once_with(order_payload(intent),"key","secret")
            self.assertEqual(json.loads(Path(a.report).read_text())["status"],"SUBMITTED")

    def test_unknown_post_outcome_is_recorded_without_retry(self):
        with tempfile.TemporaryDirectory() as root:
            state_path,state=self.files(root,submitting=True)
            intent=state["pending_intent"]
            a=self.args(root,state_path=state_path)
            Path(a.permit).write_text(json.dumps({"client_order_id":intent["client_order_id"],"permit":"single-run-only"}))
            ctx={"price":Decimal(intent["reference_price"]),"trade_age":1,"open_orders":[]}
            with patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"get_json",side_effect=[None,[],None]), \
                 patch.object(executor,"read_signal",return_value=("2026-10-09",Decimal("1"),Decimal("1"),"hash")), \
                 patch.object(executor,"qqq_defense_preflight",return_value={"status":"MONITORING","active":False,"breached":False,"changed":False,"state":state}), \
                 patch.object(executor,"broker_context",return_value=ctx), \
                 patch.object(executor,"post_order",side_effect=PaperPostError()) as post:
                executor.submit(a)
            post.assert_called_once()
            self.assertEqual(json.loads(state_path.read_text())["pending_intent"]["submission_state"],"UNKNOWN")
            self.assertEqual(json.loads(Path(a.report).read_text())["status"],"SUBMISSION_UNKNOWN")

    def test_verify_accounts_binds_distinct_hashed_identities(self):
        with tempfile.TemporaryDirectory() as root:
            b0,_=self.files(root,"b0"); f75,_=self.files(root,"f75")
            a=self.args(root)
            with patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"get_json",side_effect=[
                     {"id":"uuid-b0","status":"ACTIVE","account_blocked":False,"trading_blocked":False,"currency":"USD"},
                     {"id":"uuid-f75","status":"ACTIVE","account_blocked":False,"trading_blocked":False,"currency":"USD"}]):
                executor.verify_accounts(a)
            b=json.loads(b0.read_text()); f=json.loads(f75.read_text())
            self.assertNotEqual(b["broker_account_fingerprint"],f["broker_account_fingerprint"])
            self.assertNotIn("uuid-b0",Path(a.report).read_text())

    def test_verify_accounts_rejects_same_account(self):
        with tempfile.TemporaryDirectory() as root:
            self.files(root,"b0"); self.files(root,"f75")
            a=self.args(root)
            account={"id":"same","status":"ACTIVE","account_blocked":False,"trading_blocked":False,"currency":"USD"}
            with patch.object(executor,"credentials",return_value=("key","secret")), \
                 patch.object(executor,"get_json",return_value=account), \
                 self.assertRaisesRegex(ExecutorBlocked,"same paper account"):
                executor.verify_accounts(a)

if __name__=="__main__": unittest.main()
