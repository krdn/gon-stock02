from contextlib import closing
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from gon_stock02.web import create_app
from gon_stock02.orders import OrderService


PROJECT = Path(__file__).parents[1]
POLICY = json.loads((PROJECT / 'config/paper.json').read_text())
INPUT = dict(symbol='005930', entry='100000', stop='99000', cost_per_share='200',
             equity='10000000', day_open_equity='10000000', peak_equity='10000000',
             cash='10000000', gross_exposure='0', symbol_exposure='0', reserved_loss_krw='0',
             positions=0, entries_today=0)


def bar(**changes):
    return dict(symbol='005930', timeframe='1d', time='2026-11-12', open='100',
                high='120', low='90', close='110', volume='10', zero_price=False) | changes


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        (self.root / 'config/paper.json').write_text(json.dumps(POLICY))
        self.data = self.root / '.local'
        self.data.mkdir()
        self.state = self.root / 'state'
        self.state.mkdir()
        self.client = self.make_client()
        self.addCleanup(self.client.close)

    def make_client(self, address='127.0.0.1'):
        return TestClient(create_app(self.root, state_root=self.state), base_url='http://127.0.0.1',
                          client=(address, 51000))

    def bundle(self, rows=None, name='history-test', capture=False, complete=True):
        path = self.data / name
        path.mkdir(exist_ok=True)
        filename = 'observations.jsonl' if capture else 'bars.jsonl'
        (path / 'pages.jsonl').write_text('{}\n')
        rows = rows if rows is not None else [bar(), bar(time='2026-11-13', close='115')]
        (path / filename).write_text(''.join(json.dumps(row) + '\n' for row in rows))
        manifest = dict(environment='mock', market_requested='KRX', started_at='2026-11-13T15:00:00+00:00',
                        finished_at='2026-11-13T15:00:01+00:00', collection_complete=complete,
                        datasets={'005930': {'observations': len(rows)}} if capture else [
                            dict(symbol='005930', timeframe='1d', rows=len(rows), status='read_ok')],
                        sha256={name: hashlib.sha256((path / name).read_bytes()).hexdigest()
                                for name in ('pages.jsonl', filename)})
        (path / 'manifest.json').write_text(json.dumps(manifest))
        return path

    def get_series(self, **params):
        return self.client.get('/api/series', params=dict(bundle='history-test', symbol='005930', timeframe='1d') | params)

    def test_real_routes_without_credentials_or_network(self):
        self.bundle()
        with patch('gon_stock02.kis.load_credentials', side_effect=AssertionError('credentials accessed')), \
             patch('gon_stock02.kis.PaperClient.authenticate', side_effect=AssertionError('broker accessed')):
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get('/static/app.js').status_code, 200)
            response = self.client.get('/api/overview')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data['order_execution_available'])
            self.assertFalse(data['backtest_ready'])
            self.assertEqual(data['bundles'][0]['integrity'], 'matched')
            self.assertEqual(len(self.get_series().json()['rows']), 2)
            self.assertEqual(self.client.get('/api/ledger').json()['status'], 'unavailable')
            self.assertFalse(self.client.post('/api/risk', json=INPUT).json()['allowed'])
            self.assertEqual(self.client.post('/api/orders', json={}).status_code, 404)

    def test_empty_workspace_is_not_demo_or_zero_balance(self):
        self.assertEqual(self.client.get('/api/overview').json()['bundles'], [])
        ledger = self.client.get('/api/ledger').json()
        self.assertEqual(ledger['reason'], 'ledger_not_found')
        self.assertNotIn('total', ledger)
        self.assertEqual(list(self.state.iterdir()), [])

    def test_invalid_or_live_policy_does_not_show_paper_defaults(self):
        for changes in ({'environment': 'real'}, {'risk_per_trade': 'NaN'},
                        {'initial_capital_krw': '-1'}, {'max_positions': False}):
            with self.subTest(changes=changes):
                (self.root / 'config/paper.json').write_text(json.dumps(POLICY | changes))
                response = self.client.get('/api/overview')
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['detail'], 'invalid_policy')

    def test_filters_and_csv_match_observed_prices(self):
        self.bundle()
        data = self.get_series(start='2026-11-13', end='2026-11-13').json()
        self.assertEqual([row['close'] for row in data['rows']], ['115'])
        self.assertEqual(data['observations'], 1)
        response = self.client.get('/api/export.csv', params=dict(bundle='history-test', symbol='005930', timeframe='1d', start='2026-11-13'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('2026-11-13,100,120,90,115,10', response.text)
        self.assertNotIn('2026-11-12', response.text)
        self.assertIn('unverified,False', response.text)
        self.assertIn('attachment;', response.headers['content-disposition'])
        self.assertEqual(self.get_series(start='2027-01-01').json()['rows'], [])

    def test_bad_filters_and_unknown_symbols(self):
        self.bundle()
        for args in (dict(start='2026-11-14', end='2026-11-13'), dict(start='garbage'),
                     dict(symbol='999999'), dict(timeframe='week')):
            with self.subTest(args=args):
                self.assertEqual(self.get_series(**args).status_code, 422)

    def test_corrupt_or_modified_files_fail_closed(self):
        path = self.bundle()
        (path / 'bars.jsonl').write_text('changed')
        self.assertEqual(self.client.get('/api/overview').json()['bundles'][0]['integrity'], 'failed')
        self.assertEqual(self.get_series().json()['detail'], 'integrity_failed')
        self.assertEqual(self.client.get('/api/export.csv', params=dict(bundle='history-test', symbol='005930')).status_code, 422)
        (path / 'manifest.json').write_text('{bad')
        self.assertEqual(self.client.get('/api/overview').json()['bundles'][0]['error'], 'invalid_data')

    def test_original_pages_hash_is_also_checked(self):
        path = self.bundle()
        (path / 'pages.jsonl').write_text('tampered')
        self.assertEqual(self.get_series().status_code, 422)

    def test_partial_but_intact_bundle_stays_partial(self):
        self.bundle(complete=False)
        data = self.get_series().json()
        self.assertEqual(len(data['rows']), 2)
        self.assertFalse(data['bundle']['collection_complete'])
        self.assertFalse(data['bundle']['coverage_verified'])

    def test_duplicate_invalid_ohlc_and_nonfinite_prices_rejected(self):
        cases = [[bar(), bar()], [bar(close='NaN')], [bar(high='95')], [bar(volume='-1')],
                 [bar(volume='0.5')], [bar(close='=cmd')], [bar(time='=cmd')],
                 [bar(low='0', open='0', volume='1')]]
        for rows in cases:
            with self.subTest(rows=rows):
                self.bundle(rows)
                self.assertEqual(self.get_series().status_code, 422)

    def test_zero_price_observation_remains_flagged_in_table_export(self):
        self.bundle([bar(), bar(time='2026-11-13', open='0', high='0', low='0', close='0', volume='0')])
        row = self.get_series().json()['rows'][-1]
        self.assertTrue(row['zero_price'])
        self.assertFalse(row['strategy_eligible'])
        response = self.client.get('/api/export.csv', params=dict(bundle='history-test', symbol='005930'))
        self.assertIn('zero_price', response.text)
        self.assertIn('True,unverified,False', response.text)

    def test_capture_revisions_are_not_summed_into_volume(self):
        first = bar(timeframe='1m', time='2026-11-13T09:00:00+09:00',
                    sequence=1, received_at='2026-11-13T00:01:00+00:00', volume='5')
        second = first | dict(sequence=2, received_at='2026-11-13T00:02:00+00:00', volume='7', close='112')
        path = self.bundle([second, first], name='minute-capture-test', capture=True)
        before = (path / 'observations.jsonl').read_bytes()
        data = self.get_series(bundle='minute-capture-test', timeframe='1m').json()
        self.assertEqual(data['observations'], 2)
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['volume'], '7')
        self.assertEqual(data['rows'][0]['versions'], 2)
        self.assertEqual(data['rows'][0]['close'], '112')
        self.assertFalse(data['rows'][0]['strategy_eligible'])
        self.assertEqual((path / 'observations.jsonl').read_bytes(), before)

    def test_minute_times_are_normalized_to_kst(self):
        self.bundle([bar(timeframe='1m', time='2026-11-12T23:59:00+00:00')])
        result = self.get_series(timeframe='1m', start='2026-11-13', end='2026-11-13').json()
        self.assertEqual(result['rows'][0]['time'], '2026-11-13T08:59:00+09:00')

    def test_path_traversal_and_symlinks_cannot_expose_other_files(self):
        for name in ('../config', '/etc', 'history-../../config'):
            self.assertEqual(self.get_series(bundle=name).status_code, 404)
        outside = self.root / 'history-outside'
        outside.mkdir()
        (outside / 'manifest.json').write_text('{"secret":"not-to-be-served"}')
        (self.data / 'history-link').symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.get_series(bundle='history-link').status_code, 404)
        path = self.bundle()
        (path / 'bars.jsonl').unlink()
        (path / 'bars.jsonl').symlink_to(outside / 'manifest.json')
        response = self.get_series()
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('not-to-be-served', response.text)
        self.assertEqual(self.client.get('/.local/history-test/manifest.json').status_code, 404)
        self.assertEqual(self.client.get('/static/%2e%2e/web.py').status_code, 404)

    def test_loopback_host_origin_and_security_headers(self):
        with self.make_client('192.0.2.1') as remote:
            self.assertEqual(remote.get('/api/overview').status_code, 403)
        self.assertEqual(self.client.get('/api/overview', headers={'host': 'attacker.test'}).status_code, 400)
        self.assertEqual(self.client.get('/api/overview', headers={'origin': 'https://attacker.test'}).status_code, 403)
        self.assertEqual(self.client.get('/api/overview', headers={'sec-fetch-site': 'cross-site'}).status_code, 403)
        response = self.client.get('/')
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertIn("frame-ancestors 'none'", response.headers['content-security-policy'])
        self.assertNotIn('access-control-allow-origin', response.headers)
        self.assertEqual(self.client.post('/api/risk', content='x' * 8193).status_code, 413)

    def test_link_navigation_can_open_shell_but_not_cross_site_data(self):
        headers = {'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'navigate', 'sec-fetch-dest': 'document'}
        self.assertEqual(self.client.get('/', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/overview', headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/', headers=headers | {'sec-fetch-dest': 'iframe'}).status_code, 403)
        self.assertEqual(self.client.post('/api/risk', headers=headers, json=INPUT).status_code, 403)

    def test_risk_matches_engine_and_never_enables_orders(self):
        before = (self.root / 'config/paper.json').read_bytes()
        result = self.client.post('/api/risk', json=INPUT).json()
        self.assertTrue(result['risk_passed'])
        self.assertEqual(result['quantity'], 20)
        self.assertEqual(result['planned_loss_krw'], '24000')
        self.assertFalse(result['allowed'])
        self.assertTrue(result['simulation_only'])
        self.assertEqual((self.root / 'config/paper.json').read_bytes(), before)
        (self.root / 'config/paper.json').write_text(json.dumps(POLICY | {'order_submission_enabled': True}))
        self.assertFalse(self.client.post('/api/risk', json=INPUT).json()['allowed'])

    def test_risk_cost_is_required_and_boundaries_are_enforced(self):
        missing = deepcopy(INPUT)
        del missing['cost_per_share']
        self.assertEqual(self.client.post('/api/risk', json=missing).status_code, 422)
        for changes in ({'cost_per_share': '-1'}, {'entry': 'Infinity'}, {'entry': 'NaN'},
                        {'symbol': '123456'}, {'entry': '1000000000001'}, {'positions': True},
                        {'order_submission_enabled': True}):
            with self.subTest(changes=changes):
                self.assertEqual(self.client.post('/api/risk', json=INPUT | changes).status_code, 422)
        result = self.client.post('/api/risk', json=INPUT | {'equity': '9925000'}).json()
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'loss_limit')
        self.assertEqual(self.client.post('/api/risk', json=INPUT | {'stop': '100001'}).json()['reason'], 'invalid_numbers')

    def ledger(self, name='private-account', with_order=True):
        folder = self.state / name
        folder.mkdir()
        path = folder / 'orders.sqlite3'
        with OrderService(SimpleNamespace(account_dir=folder), POLICY) as service, service.db as db:
            service.set_meta('blocked_reason', None)
            if with_order:
                details = dict(symbol='005930', side='buy', quantity=2, price='100000', stop='99000', cost='200')
                db.execute('INSERT INTO orders(intent,day,state,details,filled,canceled,remaining,amount,reason,order_id) '
                           'VALUES (?,?,?,?,?,?,?,?,?,?)',
                           ('private-intent', '20261113', 'SUBMITTING', json.dumps(details), 0, 0, 2, '0', '', 'private-broker-id'))
        return path

    def test_order_service_persisted_order_can_be_read_without_broker(self):
        folder = self.state / 'integration-fixture'
        folder.mkdir()
        now = datetime(2026, 11, 13, 10, tzinfo=ZoneInfo('Asia/Seoul'))
        posts = []

        def submit(*args, before_send):
            before_send()
            posts.append(args)
            return {'branch': 'fixture-branch', 'order_id': 'fixture-broker-id'}

        fake = SimpleNamespace(account_dir=folder, daily_orders=lambda *_: [], authenticate=lambda: None,
                               account_snapshot=lambda: {'holdings': {}, 'equity': '10000000', 'cash': '10000000'},
                               _submit_limit=submit)
        quote = dict(symbol='005930', venue='KRX', tr_id='H0STCNT0', event_time=now.isoformat(),
                     received_at=now.isoformat(), price='100000', ask='100000', bid='99900', halt_code='N', hour_class='0')
        session = dict(opens_at=now.replace(hour=9).isoformat(), closes_at=now.replace(hour=15, minute=20).isoformat(),
                       checked_at=now.isoformat(), source='https://example.com/offline-fixture')
        with patch('gon_stock02.orders.datetime', wraps=datetime) as clock:
            clock.now.return_value = now
            with OrderService(fake, POLICY | {'order_submission_enabled': True}) as service:
                recorded = service.submit(intent='fixture-only', symbol='005930', side='buy', quantity=2,
                                          price='100000', stop='99000', cost='200', quote=quote, session=session)
                self.assertEqual(recorded['state'], 'OPEN')
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        response = self.client.get('/api/ledger')
        self.assertEqual(len(posts), 1)  # In-memory stub; no HTTP transport or real account.
        self.assertEqual(response.json()['orders'][0]['state'], 'OPEN')
        self.assertEqual(response.json()['orders'][0]['quantity'], '2')
        self.assertEqual(response.json()['orders'][0]['price'], '100000')
        self.assertNotIn('fixture-broker-id', response.text)
        self.assertEqual({p.name: p.read_bytes() for p in folder.iterdir()}, before)

    def test_free_form_ledger_reasons_do_not_reveal_private_values(self):
        path = self.ledger()
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("UPDATE metadata SET value=? WHERE key='blocked_reason'", (json.dumps({'account': 'private-value'}),))
            db.execute('UPDATE orders SET reason=?', ('private-broker-message',))
        response = self.client.get('/api/ledger')
        self.assertEqual(response.json()['blocked_reason'], 'ledger_blocked')
        self.assertNotIn('private-value', response.text)
        self.assertNotIn('private-broker-message', response.text)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("UPDATE metadata SET value=? WHERE key='blocked_reason'", (json.dumps('capital_exhausted'),))
        self.assertEqual(self.client.get('/api/ledger').json()['blocked_reason'], 'capital_exhausted')

    def test_ledger_read_does_not_recover_or_modify_pending_orders(self):
        path = self.ledger()
        before = path.read_bytes()
        response = self.client.get('/api/ledger')
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['orders'][0]['state'], 'SUBMITTING')
        self.assertFalse(data['broker_reconciled_now'])
        self.assertEqual(path.read_bytes(), before)
        for private in ('private-account', 'private-intent', 'private-broker-id'):
            self.assertNotIn(private, response.text)

    def test_empty_ambiguous_and_corrupt_ledgers_are_distinct(self):
        path = self.ledger(with_order=False)
        self.assertEqual(self.client.get('/api/ledger').json()['total'], 0)
        path.write_bytes(b'not a sqlite file')
        self.assertEqual(self.client.get('/api/ledger').json()['status'], 'error')
        self.ledger(name='second-account')
        self.assertEqual(self.client.get('/api/ledger').json()['reason'], 'multiple_ledgers')


if __name__ == '__main__':
    unittest.main()
