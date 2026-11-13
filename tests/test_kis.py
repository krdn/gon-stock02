import json
from datetime import datetime, timedelta
import subprocess
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import httpx

from gon_stock02.kis import Credentials, KisFailure, PaperClient, load_credentials
from gon_stock02.cli import probe


class KisTests(unittest.TestCase):
    def setUp(self):
        self.credentials = Credentials("fixture-app", "fixture-secret", "12345678", "01")
        self.requests = []
        patcher = patch("gon_stock02.kis.time.sleep")
        patcher.start()
        self.addCleanup(patcher.stop)

    def client(self, handler):
        def transport(request):
            self.requests.append(request)
            if request.url.path == "/oauth2/tokenP":
                return httpx.Response(200, json={"access_token": "fixture-token", "expires_in": 86400, "token_type": "Bearer"})
            return handler(request)
        client = PaperClient(self.credentials, transport=httpx.MockTransport(transport))
        self.addCleanup(client.__exit__, None, None, None)
        return client

    def test_mock_credentials_only_and_no_secret_repr(self):
        calls = []
        def runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, json.dumps({"app_key": "fixture-app", "secret_key": "fixture-secret", "account": "12345678", "product": "01"}), "")
        value = load_credentials(runner=runner)
        self.assertEqual(calls[0][-1], "mock")
        self.assertNotIn("fixture-app", repr(value))
        self.assertNotIn("12345678", repr(value))

    def test_quote_is_mock_only_and_does_not_claim_freshness_or_nxt_support(self):
        client = self.client(lambda _: httpx.Response(200, json={"rt_cd": "0", "output": {"stck_prpr": "100000", "acml_vol": "200"}}))
        result = client.quote("005930", "NXT")
        self.assertEqual(result["market_requested"], "NXT")
        self.assertEqual(self.requests[-1].url.params["FID_COND_MRKT_DIV_CODE"], "NX")
        self.assertIsNone(result["event_time"])
        self.assertFalse(result["venue_verified"])
        self.assertEqual(result["freshness"], "unverified")
        self.assertTrue(all(r.url.host == "openapivts.koreainvestment.com" for r in self.requests))
        self.assertEqual([r.method for r in self.requests], ["POST", "GET"])

    def test_instrument_allowlist_blocks_before_network(self):
        client = self.client(lambda _: self.fail("must not request"))
        with self.assertRaises(KisFailure):
            client.quote("999999")
        self.assertEqual(self.requests, [])

    def test_invalid_price_and_broker_error_are_not_success(self):
        for data in ({"rt_cd": "0", "output": {"stck_prpr": "NaN", "acml_vol": "1"}},
                     {"rt_cd": "0", "output": {"stck_prpr": "0", "acml_vol": "1"}},
                     {"rt_cd": "1", "msg1": "fixture-secret"}):
            with self.subTest(data=data):
                client = self.client(lambda _, data=data: httpx.Response(200, json=data))
                with self.assertRaises(KisFailure) as context:
                    client.quote("005930")
                self.assertNotIn("fixture-secret", str(context.exception))

    def test_redirect_cannot_send_credentials_to_another_host(self):
        client = self.client(lambda _: httpx.Response(302, headers={"location": "https://example.com/secret"}, json={}))
        with self.assertRaises(KisFailure):
            client.quote("005930")
        self.assertEqual(len(self.requests), 2)

    def test_network_error_is_sanitized(self):
        def error(request):
            raise httpx.ConnectError("fixture-secret account=12345678", request=request)
        client = self.client(error)
        with self.assertRaisesRegex(KisFailure, "^network_error$"):
            client.quote("005930")

    def test_balance_continuation_and_private_values_are_not_returned(self):
        def handler(request):
            page = 1 if len(self.requests) == 2 else 2
            if page == 2:
                self.assertEqual(request.headers["tr_cont"], "N")
                self.assertEqual(request.url.params["CTX_AREA_NK100"], "cursor")
            return httpx.Response(200, headers={"tr_cont": "F" if page == 1 else "D"}, json={
                "rt_cd": "0", "output1": [{"account": "12345678", "qty": "15"}], "output2": [{"cash": "private-value"}],
                "ctx_area_fk100": "", "ctx_area_nk100": "cursor"})
        client = self.client(handler)
        result = client.balance_status()
        self.assertEqual(result["pages"], 2)
        self.assertNotIn("12345678", json.dumps(result))
        self.assertNotIn("private-value", json.dumps(result))
        self.assertEqual(self.requests[-1].headers["tr_id"], "VTTC8434R")

    def test_repeated_balance_cursor_fails_closed(self):
        client = self.client(lambda _: httpx.Response(200, headers={"tr_cont": "M"}, json={"rt_cd": "0", "output1": [], "output2": [], "ctx_area_fk100": "", "ctx_area_nk100": "same"}))
        with self.assertRaisesRegex(KisFailure, "invalid_balance_pagination"):
            client.balance_status()
        self.assertEqual(len(self.requests), 3)

    def test_future_and_inconsistent_bars_rejected(self):
        base = {"stck_bsop_date": datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d"), "stck_cntg_hour": "000000", "stck_oprc": "100", "stck_hgpr": "120", "stck_lwpr": "90", "stck_prpr": "110", "cntg_vol": "5"}
        for override, reason in (({"stck_bsop_date": "20990102"}, "invalid_bar_time"), ({"stck_hgpr": "105"}, "inconsistent_ohlc")):
            client = self.client(lambda _, row={**base, **override}: httpx.Response(200, json={"rt_cd": "0", "output2": [row]}))
            with self.assertRaisesRegex(KisFailure, reason):
                client.bars("005930")

    def test_empty_and_previous_day_bars_are_not_success(self):
        yesterday = (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=1)).strftime("%Y%m%d")
        old = {"stck_bsop_date": yesterday, "stck_cntg_hour": "090100", "stck_oprc": "100", "stck_hgpr": "120", "stck_lwpr": "90", "stck_prpr": "110", "cntg_vol": "5"}
        for rows in ([], [old]):
            with self.subTest(rows=rows):
                client = self.client(lambda _, rows=rows: httpx.Response(200, json={"rt_cd": "0", "output2": rows}))
                with self.assertRaises(KisFailure):
                    client.bars("005930")

    def test_authentication_failure_returns_sanitized_probe_evidence(self):
        with PaperClient(self.credentials, transport=httpx.MockTransport(lambda _: httpx.Response(401, json={"msg1": "fixture-secret"}))) as client:
            try:
                report = probe(client)
            except KisFailure:
                report = None
        self.assertIsNotNone(report)
        self.assertTrue(report["stopped_early"])
        self.assertEqual(report["checks"][0]["reason"], "authentication_failed")
        self.assertNotIn("fixture-secret", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
