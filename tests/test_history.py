from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from gon_stock02.history import collect_history
from gon_stock02.kis import Credentials, KisFailure, PaperClient


def row(day, hour=None, **changes):
    value = {'stck_bsop_date': day, 'stck_oprc': '100', 'stck_hgpr': '120',
             'stck_lwpr': '90', 'acml_tr_pbmn': '5000', 'private_field': 'fixture-secret'}
    if hour is None:
        value.update(stck_clpr='110', acml_vol='50', mod_yn='N', prtt_rate='0')
    else:
        value.update(stck_cntg_hour=hour, stck_prpr='110', cntg_vol='5')
    return {**value, **changes}


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.requests = []
        sleep = patch('gon_stock02.kis.time.sleep')
        sleep.start()
        self.addCleanup(sleep.stop)

    def collect(self, handler, *, start=date(2026, 1, 5), end=date(2026, 1, 9),
                minute_start=date(2026, 1, 8), output=None):
        def transport(request):
            self.requests.append(request)
            if request.url.path == '/oauth2/tokenP':
                return httpx.Response(200, json={'access_token': 'fixture-token', 'expires_in': 86400, 'token_type': 'Bearer'})
            return handler(request)

        with PaperClient(Credentials('fixture-app', 'fixture-secret', '12345678', '01'),
                         transport=httpx.MockTransport(transport), state_root=self.root / 'state') as client:
            return collect_history(client, start, end, minute_start, output or self.root / 'bundle')

    def market(self, request):
        params = request.url.params
        self.assertEqual(params['FID_COND_MRKT_DIV_CODE'], 'J')
        if request.url.path.endswith('inquire-daily-itemchartprice'):
            self.assertEqual(params['FID_ORG_ADJ_PRC'], '1')
            values = [row(f'202601{day:02}') for day in range(9, 4, -1)
                      if f'202601{day:02}' <= params['FID_INPUT_DATE_2']]
        elif request.url.path.endswith('inquire-time-dailychartprice'):
            self.assertEqual(params['FID_PW_DATA_INCU_YN'], 'N')
            values = [row(params['FID_INPUT_DATE_1'], hour) for hour in ('153000', '151900', '090100', '090000')
                      if hour <= params['FID_INPUT_HOUR_1']]
        else:
            self.fail('시세 이외의 요청')
        return httpx.Response(200, json={'rt_cd': '0', 'output1': {'account': '12345678'}, 'output2': values[:2]})

    def test_collects_every_page_and_preserves_hashes_without_private_fields(self):
        report = self.collect(self.market)
        self.assertTrue(report['collection_complete'])
        self.assertFalse(report['backtest_ready'])
        self.assertFalse(report['session_calendar_verified'])
        self.assertEqual(len(report['datasets']), 8)
        self.assertEqual(sum(dataset['rows'] for dataset in report['datasets']), 52)
        self.assertEqual(report['orders_sent'], 0)
        bundle = self.root / 'bundle'
        for name, expected in report['sha256'].items():
            self.assertEqual(hashlib.sha256((bundle / name).read_bytes()).hexdigest(), expected)
        raw = (bundle / 'pages.jsonl').read_text()
        self.assertNotIn('fixture-secret', raw)
        self.assertNotIn('12345678', raw)
        bars = [json.loads(line) for line in (bundle / 'bars.jsonl').read_text().splitlines()]
        minute = [bar for bar in bars if bar['timeframe'] == '1m']
        self.assertIn('cumulative_turnover', minute[0])
        self.assertNotIn('turnover', minute[0])
        self.assertTrue(all(request.url.host == 'openapivts.koreainvestment.com' for request in self.requests))
        self.assertTrue(all(request.method == 'GET' or request.url.path == '/oauth2/tokenP' for request in self.requests))
        self.assertEqual(json.loads((bundle / 'manifest.json').read_text()), report)

    def test_candidate_gaps_remain_unknown_and_do_not_become_zero_volume_bars(self):
        report = self.collect(self.market)
        minute = [dataset for dataset in report['datasets'] if dataset['timeframe'] == '1m']
        self.assertTrue(all(dataset['candidate_missing_minutes'] > 0 for dataset in minute))
        self.assertTrue(all(dataset['rows'] == 8 for dataset in minute))
        self.assertIn('calendar_and_no_trade_unverified', report['limitations'])

    def test_invalid_dates_and_existing_output_fail_before_network(self):
        for args in ({'start': date(2026, 1, 10)}, {'end': date(2099, 1, 9)},
                     {'minute_start': date(2026, 1, 4)}):
            with self.subTest(args=args), self.assertRaisesRegex(KisFailure, '^invalid_history_dates$'):
                self.collect(self.market, **args)
            self.assertEqual(self.requests, [])
        bundle = self.root / 'existing'
        bundle.mkdir()
        marker = bundle / 'user-data'
        marker.write_text('preserve')
        with self.assertRaises(FileExistsError):
            self.collect(self.market, output=bundle)
        self.assertEqual(marker.read_text(), 'preserve')
        self.assertEqual(self.requests, [])

    def test_duplicate_reverse_time_invalid_ohlc_and_fractional_volume_fail_closed(self):
        scenarios = [
            [row('20260109'), row('20260109')],
            [row('20260108'), row('20260109')],
            [row('20260109', stck_hgpr='105')],
            [row('20260109', acml_vol='1.5')],
            [row('20990109')],
            [row('20260109', stck_clpr='NaN')],
        ]
        for index, values in enumerate(scenarios):
            with self.subTest(index=index):
                report = self.collect(lambda _: httpx.Response(200, json={'rt_cd': '0', 'output2': values}),
                                      output=self.root / str(index))
                self.assertFalse(report['collection_complete'])
                self.assertEqual(report['datasets'][0]['status'], 'failed')
                self.assertTrue((self.root / str(index) / 'manifest.json').exists())

    def test_rate_limit_stops_requests_and_retains_partial_evidence(self):
        report = self.collect(lambda _: httpx.Response(429, json={'msg1': 'fixture-secret'}))
        self.assertFalse(report['collection_complete'])
        self.assertEqual(report['datasets'][0]['reason'], 'rate_limited')
        self.assertEqual(len(self.requests), 2)
        self.assertNotIn('fixture-secret', json.dumps(report))

    def test_stalled_page_is_rejected_instead_of_looping_or_deduplicating(self):
        report = self.collect(lambda _: httpx.Response(200, json={'rt_cd': '0', 'output2': [row('20260109')]}))
        self.assertFalse(report['collection_complete'])
        self.assertEqual(report['datasets'][0]['reason'], 'invalid_history_time')
        self.assertLess(len(self.requests), 20)

    def test_minute_cursor_avoids_broker_rounding_seconds_up_to_previous_boundary(self):
        def rounded(request):
            if request.url.path.endswith('inquire-time-dailychartprice') and request.url.params['FID_INPUT_HOUR_1'] == '151859':
                day = request.url.params['FID_INPUT_DATE_1']
                return httpx.Response(200, json={'rt_cd': '0', 'output2': [row(day, '151900'), row(day, '090100')]})
            return self.market(request)
        self.assertTrue(self.collect(rounded)['collection_complete'])


if __name__ == '__main__':
    unittest.main()
