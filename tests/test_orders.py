from contextlib import closing
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib
import json
from pathlib import Path
import subprocess
import sys
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import httpx
from gon_stock02.kis import Credentials, KisFailure, PaperClient


NOW = datetime(2026, 11, 13, 10, 0, tzinfo=ZoneInfo('Asia/Seoul'))
DAY = NOW.strftime('%Y%m%d')
POLICY = json.loads(Path('config/paper.json').read_text()) | {'order_submission_enabled': True}


def tick():
    now = NOW.isoformat()
    return dict(symbol='005930', venue='KRX', tr_id='H0STCNT0', event_time=now,
                received_at=now, price='100000', ask='100000', bid='99900',
                halt_code='N', hour_class='0')


def order_row(**changes):
    return dict(ord_dt=DAY, ord_gno_brno='06010', odno='0000000001', orgn_odno='0000000000',
                pdno='005930', sll_buy_dvsn_cd='02', ord_dvsn_cd='00', ord_unpr='100000',
                ord_qty='2', tot_ccld_qty='0', cncl_cfrm_qty='0', rjct_qty='0', rmn_qty='2',
                tot_ccld_amt='0', **changes) if not changes else order_row() | changes


class Broker:
    def __init__(self):
        self.rows = []
        self.holdings = []
        self.writes = []
        self.requests = []
        self.mode = 'ok'
        self.on_write = None

    def __call__(self, request):
        self.requests.append(request)
        path = request.url.path
        if path == '/oauth2/tokenP':
            return httpx.Response(200, json=dict(access_token='fixture-token', expires_in=86400, token_type='Bearer'))
        if path.endswith('inquire-daily-ccld'):
            return httpx.Response(200, headers={'tr_cont': 'E'}, json={'rt_cd': '0', 'output1': self.rows})
        if path.endswith('inquire-balance'):
            return httpx.Response(200, headers={'tr_cont': 'E'}, json={'rt_cd': '0', 'output1': self.holdings, 'output2': [{
                'tot_evlu_amt': '10000000', 'dnca_tot_amt': '10000000', 'prvs_rcdl_excc_amt': '10000000'}]})
        self.writes.append(request)
        if self.on_write:
            self.on_write()
        if self.mode == 'timeout':
            raise httpx.ReadTimeout('secret-token', request=request)
        if self.mode == 'crash':
            raise KeyboardInterrupt()
        if self.mode == 'bad':
            return httpx.Response(200, json={'rt_cd': '0', 'output': {}})
        if self.mode == 'reject':
            return httpx.Response(200, json={'rt_cd': '1', 'msg_cd': 'APBK0001', 'msg1': 'secret-token'})
        return httpx.Response(200, json={'rt_cd': '0', 'output': {
            'KRX_FWDG_ORD_ORGNO': '06010', 'ODNO': str(len(self.writes)).zfill(10), 'ORD_TMD': '100000'}})

    def fill(self, quantity, canceled=0):
        self.rows = [order_row(tot_ccld_qty=str(quantity), cncl_cfrm_qty=str(canceled),
                               rmn_qty=str(2-quantity-canceled), tot_ccld_amt=str(quantity*100000))]
        self.holdings = [dict(pdno='005930', hldg_qty=str(quantity), ord_psbl_qty=str(quantity),
                              evlu_amt=str(quantity*100000), loan_amt='0')]


class OrderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        clock = patch('gon_stock02.orders.datetime')
        self.clock = clock.start()
        self.clock.now.return_value = NOW
        self.clock.fromisoformat.side_effect = datetime.fromisoformat
        self.addCleanup(clock.stop)
        self.broker = Broker()
        self.credentials = Credentials('fixture-app', 'fixture-secret', '12345678', '01')
        patcher = patch('gon_stock02.kis.time.sleep')
        patcher.start()
        self.addCleanup(patcher.stop)

    def service(self, policy=None):
        self.assertTrue(callable(getattr(PaperClient, 'daily_orders', None)), 'persistent order API not implemented')
        module = importlib.import_module('gon_stock02.orders')
        client = PaperClient(self.credentials, transport=httpx.MockTransport(self.broker), state_root=self.root)
        self.addCleanup(client.__exit__, None, None, None)
        return module.OrderService(client, deepcopy(policy or POLICY))

    def submit(self, service, intent='entry-1', **changes):
        args = dict(intent=intent, symbol='005930', side='buy', quantity=2, price='100000', stop='99000', cost='100', quote=tick(),
                    session={'opens_at': NOW.replace(hour=9).isoformat(), 'closes_at': NOW.replace(hour=15, minute=20).isoformat(),
                             'checked_at': NOW.isoformat(), 'source': 'https://apiportal.koreainvestment.com/test-fixture'})
        return service.submit(**(args | changes))

    def test_intent_committed_before_post_and_duplicate_survives_restart(self):
        with self.service() as service:
            def observed():
                with closing(sqlite3.connect(service.path)) as db:
                    self.assertEqual(db.execute('SELECT state FROM orders').fetchone()[0], 'SUBMITTING')
            self.broker.on_write = observed
            self.assertEqual(self.submit(service)['state'], 'OPEN')
            self.assertEqual(self.submit(service)['state'], 'OPEN')
        with self.service() as service:
            self.assertEqual(self.submit(service)['state'], 'OPEN')
        self.assertEqual(len(self.broker.writes), 1)
        body = json.loads(self.broker.writes[0].content)
        self.assertEqual(body['EXCG_ID_DVSN_CD'], 'KRX')
        self.assertEqual(self.broker.writes[0].headers['tr_id'], 'VTTC0012U')
        self.assertEqual(body['ORD_DVSN'], '00')

    def test_uncertain_submission_never_retries_even_when_lookup_empty(self):
        for mode in ('timeout', 'bad', 'crash'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as root:
                self.root = Path(root)
                self.broker.mode = mode
                self.broker.writes.clear()
                with self.service() as service:
                    try:
                        self.submit(service)
                    except (KisFailure, KeyboardInterrupt):
                        pass
                self.broker.mode = 'ok'
                with self.service() as service:
                    self.assertEqual(self.submit(service)['state'], 'UNKNOWN')
                    self.assertFalse(service.reconcile()['consistent'])
                    with self.assertRaises(KisFailure):
                        self.submit(service, 'entry-2')
                self.assertEqual(len(self.broker.writes), 1)

    def test_partial_cancel_ack_reserves_until_broker_reconciliation(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(1)
            self.assertTrue(service.reconcile()['consistent'])
            self.assertEqual(service.get('entry-1')['state'], 'PARTIAL')
            self.assertEqual(service.cancel('entry-1')['state'], 'CANCEL_PENDING')
            self.assertEqual(service.cancel('entry-1')['state'], 'CANCEL_PENDING')
            self.assertEqual(len(self.broker.writes), 2)
            with self.assertRaises(KisFailure):
                self.submit(service, 'entry-2')
            self.broker.fill(1, canceled=1)
            self.assertTrue(service.reconcile()['consistent'])
            self.assertEqual(service.get('entry-1')['state'], 'CANCELED')
            self.assertEqual(service.positions(), {'005930': 1})
        body = json.loads(self.broker.writes[-1].content)
        self.assertEqual((body['RVSE_CNCL_DVSN_CD'], body['QTY_ALL_ORD_YN']), ('02', 'Y'))

    def test_fill_wins_cancel_race(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(0)
            service.cancel('entry-1')
            self.broker.fill(2)
            self.assertTrue(service.reconcile()['consistent'])
            self.assertEqual(service.get('entry-1')['state'], 'FILLED')

    def test_fill_regression_and_balance_mismatch_block(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(1)
            self.assertTrue(service.reconcile()['consistent'])
            self.broker.fill(0)
            self.assertFalse(service.reconcile()['consistent'])
            self.assertEqual(service.get('entry-1')['filled'], 1)
            with self.assertRaises(KisFailure):
                self.submit(service, 'entry-2')

    def test_external_orders_and_holdings_block_initialization(self):
        with self.service() as service:
            self.broker.rows = [order_row()]
            self.assertFalse(service.reconcile()['consistent'])
            with self.assertRaises(KisFailure):
                self.submit(service)
            self.broker.rows = []
            self.broker.fill(1)
            self.broker.rows = []
            self.assertFalse(service.reconcile()['consistent'])
        self.assertEqual(self.broker.writes, [])

    def test_same_intent_different_parameters_blocked(self):
        with self.service() as service:
            self.submit(service)
            with self.assertRaisesRegex(KisFailure, 'intent_conflict'):
                self.submit(service, quantity=3)
        self.assertEqual(len(self.broker.writes), 1)

    def test_disabled_and_stale_and_oversized_orders_never_post(self):
        with self.service(POLICY | {'order_submission_enabled': False}) as service:
            with self.assertRaises(KisFailure):
                self.submit(service)
        with self.service() as service:
            for changes in ({'quantity': 99999}, {'quantity': True}, {'side': 'sell'},
                            {'quote': tick() | {'venue': 'NXT'}},
                            {'quote': tick() | {'event_time': (NOW-timedelta(seconds=30)).isoformat()}}):
                with self.subTest(changes=changes), self.assertRaises(KisFailure):
                    self.submit(service, **changes)
        self.assertEqual(self.broker.writes, [])

    def test_account_lock_prevents_second_service(self):
        with self.service():
            with self.assertRaisesRegex(KisFailure, 'account_busy'):
                with self.service():
                    self.fail('second writer acquired lock')

    def test_explicit_rejection_is_terminal_and_not_retried(self):
        self.broker.mode = 'reject'
        with self.service() as service:
            self.assertEqual(self.submit(service)['state'], 'REJECTED')
            self.assertEqual(self.submit(service)['state'], 'REJECTED')
        self.assertEqual(len(self.broker.writes), 1)

    def test_balance_mismatch_after_confirmed_fill_keeps_previous_ledger(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(2)
            self.broker.holdings[0]['hldg_qty'] = '1'
            self.broker.holdings[0]['ord_psbl_qty'] = '1'
            result = service.reconcile()
            self.assertEqual(result['reason'], 'balance_mismatch')
            self.assertEqual(service.get('entry-1')['filled'], 0)
            with self.assertRaises(KisFailure):
                self.submit(service, 'entry-2')
            self.assertEqual(len(self.broker.writes), 1)

    def test_sell_only_owned_fills_and_reconcile_round_trip(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(2)
            self.assertTrue(service.reconcile()['consistent'])
            with self.assertRaises(KisFailure):
                self.submit(service, 'sell-too-much', side='sell', quantity=3)
            self.assertEqual(self.submit(service, 'exit-1', side='sell')['state'], 'OPEN')
            self.broker.rows.append(order_row(odno='0000000002', sll_buy_dvsn_cd='01',
                                             tot_ccld_qty='2', rmn_qty='0', tot_ccld_amt='200000'))
            self.broker.holdings = []
            self.assertTrue(service.reconcile()['consistent'])
            self.assertEqual(service.positions(), {})
            self.assertEqual(service.get('exit-1')['state'], 'FILLED')
        self.assertEqual(self.broker.writes[-1].headers['tr_id'], 'VTTC0011U')

    def test_cancel_timeout_is_never_resent_and_can_be_proved_by_original(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(0)
            self.broker.mode = 'timeout'
            self.assertEqual(service.cancel('entry-1')['state'], 'UNKNOWN')
        with self.service() as service:
            service.cancel('entry-1')
            self.broker.fill(0, canceled=2)
            self.assertTrue(service.reconcile()['consistent'])
            self.assertEqual(service.get('entry-1')['state'], 'CANCELED')
        self.assertEqual(len(self.broker.writes), 2)

    def test_bad_and_regressing_broker_fields_block_without_partial_commit(self):
        with self.service() as service:
            self.submit(service)
            for change in ({'ord_qty': '3'}, {'ord_unpr': '100001'}, {'tot_ccld_qty': '0.5'},
                           {'rmn_qty': '1'}, {'tot_ccld_amt': 'NaN'}, {'pdno': '000660'}):
                self.broker.rows = [order_row(**change)]
                self.assertFalse(service.reconcile()['consistent'])
                self.assertEqual(service.get('entry-1')['filled'], 0)

    def test_quote_is_rechecked_after_rate_wait(self):
        quote = tick()
        waits = 0
        def wait(_):
            nonlocal waits
            waits += 1
            if waits == 4:
                quote['event_time'] = (NOW-timedelta(seconds=30)).isoformat()
        with self.service() as service, patch('gon_stock02.kis.time.sleep', side_effect=wait):
            self.assertEqual(self.submit(service, quote=quote)['state'], 'UNKNOWN')
            self.assertEqual(self.broker.writes, [])

    def test_multiprocess_account_lock_and_rate_spacing(self):
        with self.service() as service:
            code = """
from pathlib import Path
import sys
from gon_stock02.kis import PaperClient, Credentials, KisFailure
from gon_stock02.orders import OrderService
with PaperClient(Credentials('fixture-app','fixture-secret','12345678','01'),state_root=Path(sys.argv[1])) as c:
    try:
        with OrderService(c, {}):
            raise SystemExit(2)
    except KisFailure as e:
        print(str(e))
"""
            result = subprocess.run([sys.executable, '-c', code, str(self.root)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), 'account_busy')
        code = """
from pathlib import Path
import sys, time
from gon_stock02.kis import PaperClient, Credentials
with PaperClient(Credentials('fixture-app','fixture-secret','12345678','01'),state_root=Path(sys.argv[1])) as c:
    with c.request_slot():
        print(time.time())
"""
        workers = [subprocess.Popen([sys.executable, '-c', code, str(self.root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        times = []
        for worker in workers:
            out, error = worker.communicate(timeout=10)
            self.assertEqual(worker.returncode, 0, error)
            times.append(float(out.strip()))
        self.assertGreaterEqual(abs(times[1]-times[0]), 1.05)

    def test_pagination_is_complete_and_repeated_cursor_is_failure(self):
        calls = []
        def handler(request):
            if request.url.path == '/oauth2/tokenP':
                return self.broker(request)
            calls.append(request)
            return httpx.Response(200, headers={'tr_cont': 'F' if len(calls) == 1 else 'D'}, json={
                'rt_cd': '0', 'output1': [order_row(odno=str(len(calls)).zfill(10))],
                'ctx_area_fk100': '', 'ctx_area_nk100': 'next'})
        with PaperClient(self.credentials, transport=httpx.MockTransport(handler), state_root=self.root) as client:
            rows = client.daily_orders(DAY, DAY)
            self.assertEqual(len(rows), 2)
            self.assertEqual(calls[-1].url.params['CTX_AREA_NK100'], 'next')
            self.assertEqual(calls[-1].headers['tr_cont'], 'N')
        def repeated(request):
            if request.url.path == '/oauth2/tokenP':
                return self.broker(request)
            return httpx.Response(200, headers={'tr_cont': 'M'}, json={'rt_cd': '0', 'output1': [], 'ctx_area_fk100': '', 'ctx_area_nk100': 'next'})
        with PaperClient(self.credentials, transport=httpx.MockTransport(repeated), state_root=self.root) as client:
            with self.assertRaisesRegex(KisFailure, 'invalid_account_pagination'):
                client.daily_orders(DAY, DAY)

    def test_conflicting_ack_spellings_remain_unknown(self):
        def handler(request):
            if request.url.path.endswith('order-cash'):
                self.broker.writes.append(request)
                return httpx.Response(200, json={'rt_cd': '0', 'output': {
                    'KRX_FWDG_ORD_ORGNO': '06010', 'ODNO': '0000000001', 'odno': '0000000002', 'ORD_TMD': '100000'}})
            return self.broker(request)
        self.assertTrue(callable(getattr(PaperClient, 'daily_orders', None)))
        from gon_stock02.orders import OrderService
        with PaperClient(self.credentials, transport=httpx.MockTransport(handler), state_root=self.root) as client, OrderService(client, POLICY) as service:
            self.assertEqual(self.submit(service)['state'], 'UNKNOWN')

    def test_unknown_pagination_marker_fails_closed(self):
        def handler(request):
            if request.url.path == '/oauth2/tokenP':
                return self.broker(request)
            return httpx.Response(200, headers={'tr_cont': 'X'}, json={'rt_cd': '0', 'output1': []})
        with PaperClient(self.credentials, transport=httpx.MockTransport(handler), state_root=self.root) as client:
            with self.assertRaisesRegex(KisFailure, 'invalid_account_pagination'):
                client.daily_orders(DAY, DAY)

    def test_copied_database_cannot_be_used_for_other_account(self):
        import shutil
        with self.service() as service:
            service.reconcile()
            source = service.path
        from gon_stock02.orders import OrderService
        with PaperClient(Credentials('fixture-app', 'fixture-secret', '87654321', '01'),
                         transport=httpx.MockTransport(self.broker), state_root=self.root) as client:
            shutil.copyfile(source, client.account_dir / 'orders.sqlite3')
            with self.assertRaisesRegex(KisFailure, 'ledger_account_mismatch'):
                with OrderService(client, POLICY):
                    self.fail('copied account accepted')

    def test_read_only_check_exposes_no_private_values_or_order_endpoint(self):
        from gon_stock02 import cli
        self.assertTrue(callable(getattr(cli, 'check_orders', None)), 'read-only order check missing')
        with self.service() as service:
            report = cli.check_orders(service)
        self.assertTrue(report['consistent'])
        self.assertEqual(report['orders_sent'], 0)
        self.assertEqual(self.broker.writes, [])
        for secret in ('12345678', 'fixture-secret', '10000000'):
            self.assertNotIn(secret, json.dumps(report))

    def test_missing_expired_or_after_hours_session_blocks(self):
        with self.service() as service:
            for session in (None, {}, {'opens_at': NOW.replace(hour=9).isoformat(),
                                      'closes_at': NOW.replace(hour=9, minute=30).isoformat(),
                                      'checked_at': NOW.isoformat(), 'source': 'https://apiportal.koreainvestment.com/test-fixture'}):
                with self.subTest(session=session), self.assertRaises(KisFailure):
                    self.submit(service, session=session)
        self.assertEqual(self.broker.writes, [])

    def test_missing_pagination_header_does_not_prove_complete_read(self):
        def handler(request):
            if request.url.path == '/oauth2/tokenP':
                return self.broker(request)
            return httpx.Response(200, json={'rt_cd': '0', 'output1': []})
        with PaperClient(self.credentials, transport=httpx.MockTransport(handler), state_root=self.root) as client:
            with self.assertRaisesRegex(KisFailure, 'invalid_account_pagination'):
                client.daily_orders(DAY, DAY)

    def test_cancel_child_must_reference_original_and_is_not_a_fill(self):
        with self.service() as service:
            self.submit(service)
            self.broker.fill(0)
            service.cancel('entry-1')
            self.broker.fill(1, canceled=1)
            child = order_row(odno='0000000002', orgn_odno='0000000999', ord_unpr='0',
                              ord_qty='1', cncl_cfrm_qty='1', rmn_qty='0')
            self.broker.rows.append(child)
            self.assertFalse(service.reconcile()['consistent'])
            self.assertEqual(service.get('entry-1')['filled'], 0)
            child['orgn_odno'] = '0000000001'
            self.assertTrue(service.reconcile()['consistent'])
            self.assertEqual(service.positions(), {'005930': 1})


if __name__ == '__main__':
    unittest.main()
