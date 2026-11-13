from datetime import datetime, timedelta, timezone
import hashlib
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import httpx

from gon_stock02.kis import Credentials, KisFailure, PaperClient
from gon_stock02.capture import capture_minutes
from gon_stock02.cli import main


class Clock:
    def __init__(self):
        self.wall = datetime(2026, 1, 5, 5, 10, tzinfo=timezone.utc)
        self.elapsed = 0.0

    def now(self):
        return self.wall + timedelta(seconds=self.elapsed)

    def monotonic(self):
        return self.elapsed

    def sleep(self, seconds):
        self.elapsed += seconds


def minute(**changes):
    return {'stck_bsop_date': '20260105', 'stck_cntg_hour': '141000',
            'stck_oprc': '100', 'stck_hgpr': '120', 'stck_lwpr': '90',
            'stck_prpr': '110', 'cntg_vol': '5', 'acml_tr_pbmn': '5000',
            'private_field': 'fixture-secret', **changes}


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = Clock()
        self.requests = []
        sleeper = patch('gon_stock02.kis.time.sleep')
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def capture(self, handler, *, seconds=7, output=None):
        def transport(request):
            self.requests.append(request)
            if request.url.path == '/oauth2/tokenP':
                return httpx.Response(200, json={'access_token': 'fixture-token', 'expires_in': 86400, 'token_type': 'Bearer'})
            self.clock.sleep(0.1)
            return handler(request)

        with PaperClient(Credentials('fixture-app', 'fixture-secret', '12345678', '01'),
                         transport=httpx.MockTransport(transport), state_root=self.root / 'state') as client:
            return capture_minutes(client, seconds, output or self.root / 'capture',
                                   now=self.clock.now, monotonic=self.clock.monotonic, sleep=self.clock.sleep)

    def test_cli_invalid_capture_duration_cannot_load_credentials(self):
        error = io.StringIO()
        with patch('sys.argv', ['gs02', 'capture', '--seconds', '0', '--output', str(self.root / 'capture')]), \
             patch('gon_stock02.cli.load_credentials') as credentials, \
             contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as exited:
            main()
        self.assertEqual(exited.exception.code, 2)
        self.assertIn('capture requires --seconds between 1 and 120', error.getvalue())
        credentials.assert_not_called()

    def test_cli_cannot_silently_capture_krx_for_requested_nxt(self):
        error = io.StringIO()
        with patch('sys.argv', ['gs02', 'capture', '--venue', 'NXT', '--output', str(self.root / 'capture')]), \
             patch('gon_stock02.cli.load_credentials') as credentials, \
             contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as exited:
            main()
        self.assertEqual(exited.exception.code, 2)
        self.assertIn('capture supports --venue KRX only', error.getvalue())
        credentials.assert_not_called()

    def test_versions_keep_receipt_time_and_do_not_claim_finality(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={'rt_cd': '0', 'output2': [minute(cntg_vol='5' if len(calls) <= 4 else '7')]})

        report = self.capture(handler)
        self.assertTrue(report['collection_complete'])
        self.assertFalse(report['backtest_ready'])
        self.assertFalse(report['coverage_verified'])
        self.assertFalse(report['session_calendar_verified'])
        self.assertEqual(report['orders_sent'], 0)
        self.assertEqual(report['responses_saved'], 8)
        root = self.root / 'capture'
        observations = [json.loads(line) for line in (root / 'observations.jsonl').read_text().splitlines()]
        samsung = [row for row in observations if row['symbol'] == '005930']
        self.assertEqual([row['volume'] for row in samsung], ['5', '7'])
        self.assertEqual(samsung[0]['time'], samsung[1]['time'])
        self.assertLess(samsung[0]['available_at'], samsung[1]['available_at'])
        self.assertEqual(len({row['sequence'] for row in samsung}), 2)
        self.assertTrue(all(row['finality'] == 'unverified' and not row['strategy_eligible'] for row in observations))
        self.assertTrue(all(row['available_at'] == row['received_at'] for row in observations))
        for name, value in report['sha256'].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), value)
        self.assertEqual(json.loads((root / 'manifest.json').read_text()), report)
        raw = (root / 'pages.jsonl').read_text()
        self.assertNotIn('fixture-secret', raw)
        self.assertNotIn('fixture-token', raw)
        self.assertNotIn('12345678', raw)
        self.assertTrue(all(r.method == 'GET' or r.url.path == '/oauth2/tokenP' for r in self.requests))
        self.assertTrue(all(r.url.host == 'openapivts.koreainvestment.com' for r in self.requests))

    def test_cutoff_uses_current_clock_without_fixed_1530_clamp(self):
        self.clock.wall += timedelta(hours=2)

        def handler(request):
            self.assertEqual(request.url.params['FID_INPUT_HOUR_1'],
                             self.clock.now().astimezone(ZoneInfo('Asia/Seoul')).strftime('%H%M%S'))
            self.assertEqual(request.headers['tr_id'], 'FHKST03010200')
            self.assertEqual(request.url.params['FID_COND_MRKT_DIV_CODE'], 'J')
            return httpx.Response(200, json={'rt_cd': '0', 'output2': [minute(stck_cntg_hour='160900')]})

        report = self.capture(handler, seconds=7)
        self.assertTrue(report['collection_complete'])
        self.assertEqual(report['responses_saved'], 8)

    def test_short_duration_reports_partial_capture_with_realistic_slot_wait(self):
        with patch('gon_stock02.kis.time.time', side_effect=lambda: self.clock.now().timestamp()), \
             patch('gon_stock02.kis.time.sleep', side_effect=self.clock.sleep):
            report = self.capture(lambda _: httpx.Response(200, json={'rt_cd': '0', 'output2': [minute()]}), seconds=1)
        self.assertFalse(report['collection_complete'])
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['responses_saved'], 1)
        self.assertEqual(report['datasets']['005930']['observations'], 1)
        self.assertEqual(report['datasets']['000660']['responses'], 0)
        self.assertGreater(self.clock.elapsed, report['seconds_requested'])
        self.assertEqual(len(self.requests), 2)

    def test_rate_limit_preserves_partial_data_and_stops_without_retry(self):
        calls = []

        def handler(request):
            calls.append(request)
            if len(calls) == 2:
                return httpx.Response(429, json={'msg1': 'fixture-secret'})
            return httpx.Response(200, json={'rt_cd': '0', 'output2': [minute()]})

        report = self.capture(handler)
        self.assertEqual(len(calls), 2)
        self.assertEqual(report['requests_started'], 2)
        self.assertEqual(report['responses_saved'], 1)
        self.assertFalse(report['collection_complete'])
        self.assertEqual(report['error'], 'rate_limited')
        self.assertEqual(report['datasets']['005930']['observations'], 1)
        self.assertEqual(report['datasets']['009150']['responses'], 0)
        self.assertNotIn('fixture-secret', (self.root / 'capture' / 'manifest.json').read_text())

    def test_invalid_rows_are_retained_raw_and_never_become_observations(self):
        for rows in ([], [minute(stck_bsop_date='20260102')],
                     [minute(stck_cntg_hour='141100')], [minute(), minute()],
                     [minute(cntg_vol='1.5')]):
            with self.subTest(rows=rows):
                output = self.root / ('bad-' + str(len(list(self.root.glob('bad-*')))))
                report = self.capture(lambda _: httpx.Response(200, json={'rt_cd': '0', 'output2': rows}), output=output)
                self.assertFalse(report['collection_complete'])
                self.assertEqual(report['responses_saved'], 1)
                self.assertEqual(report['requests_started'], 1)
                self.assertEqual((output / 'observations.jsonl').read_text(), '')
                self.assertEqual(len((output / 'pages.jsonl').read_text().splitlines()), 1)

    def test_network_failure_leaves_running_manifest_before_response(self):
        def handler(request):
            saved = json.loads((self.root / 'capture' / 'manifest.json').read_text())
            self.assertEqual(saved['status'], 'running')
            self.assertFalse(saved['collection_complete'])
            raise httpx.ReadTimeout('fixture-secret', request=request)

        report = self.capture(handler)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['error'], 'timeout')
        self.assertEqual(report['responses_saved'], 0)

    def test_output_cannot_be_overwritten_and_duration_is_bounded_before_network(self):
        output = self.root / 'existing'
        output.mkdir()
        (output / 'keep').write_text('original')
        with self.assertRaises(FileExistsError):
            self.capture(lambda _: self.fail('must not request'), output=output)
        self.assertEqual((output / 'keep').read_text(), 'original')
        for seconds in (0, 121, True, 1.5):
            with self.subTest(seconds=seconds), self.assertRaises(KisFailure):
                self.capture(lambda _: self.fail('must not request'), seconds=seconds)
        self.assertEqual(self.requests, [])

    def test_date_rollover_stops_before_next_symbol(self):
        self.clock.wall = datetime(2026, 1, 5, 14, 59, 59, tzinfo=timezone.utc)

        def handler(request):
            self.clock.sleep(2)
            return httpx.Response(200, json={'rt_cd': '0', 'output2': [minute(stck_cntg_hour='235900')]})

        report = self.capture(handler)
        self.assertEqual(report['error'], 'capture_date_changed')
        self.assertEqual(report['requests_started'], 1)
        self.assertEqual(report['responses_saved'], 1)
        self.assertEqual((self.root / 'capture' / 'observations.jsonl').read_text(), '')


if __name__ == '__main__':
    unittest.main()
