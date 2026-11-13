from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

import httpx

from gon_stock02.feed import FEEDS, parse_ticks, probe_feed
from gon_stock02.kis import Credentials, KisFailure


def frame(symbol="005930", tr_id="H0NXCNT0", **changes):
    row = ["0"] * 47
    for index, value in {0: symbol, 1: "160000", 2: "100000", 10: "100100", 11: "100000",
                         12: "2", 13: "1000", 14: "100000000", 33: "20261113", 35: "N",
                         36: "100", 37: "200", 43: "0", 46: "3", **{int(k): v for k, v in changes.items()}}.items():
        row[index] = value
    return "0|" + tr_id + "|001|" + "^".join(row)


class Socket:
    def __init__(self, messages):
        self.messages = iter(messages)
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def send(self, value):
        self.sent.append(json.loads(value))

    def recv(self, **kwargs):
        try:
            return next(self.messages)
        except StopIteration:
            raise TimeoutError


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.credentials = Credentials("fixture-app", "fixture-secret", "12345678", "01")
        self.received = datetime(2026, 11, 13, 7, 0, 1, tzinfo=timezone.utc)

    def test_nxt_uses_official_trade_layout_with_date_and_venue(self):
        tick = parse_ticks(frame(), "NXT", self.received)[0]
        self.assertEqual(tick["event_time"], "2026-11-13T16:00:00+09:00")
        self.assertEqual(tick["venue"], "NXT")
        self.assertEqual(tick["price"], "100000")
        self.assertEqual(tick["event_age_seconds"], 1)
        self.assertTrue(tick["fresh_at_receipt"])
        self.assertTrue(tick["valid_two_sided_quote"])
        self.assertFalse(tick["order_submission_enabled"])

    def test_multiple_records_count_is_checked(self):
        payload = frame().split("|", 3)[3]
        ticks = parse_ticks("0|H0NXCNT0|002|" + payload + "^" + payload, "NXT", self.received)
        self.assertEqual(len(ticks), 2)
        with self.assertRaises(KisFailure):
            parse_ticks("0|H0NXCNT0|002|" + payload, "NXT", self.received)

    def test_old_future_halted_or_crossed_data_cannot_qualify(self):
        for values in ({"33": "20261112"}, {"1": "160010"}):
            self.assertFalse(parse_ticks(frame(**values), "NXT", self.received)[0]["fresh_at_receipt"])
        for values in ({"35": "Y"}, {"43": "C"}, {"10": "99900"}, {"11": "0"}):
            self.assertFalse(parse_ticks(frame(**values), "NXT", self.received)[0]["valid_two_sided_quote"])

    def test_unknown_venue_symbol_layout_and_nonfinite_price_rejected(self):
        for message in (frame(symbol="036930"), frame(tr_id="H0STCNT0"), frame(**{"2": "NaN"}),
                        frame(**{"33": "20260231"}), frame() + "^extra"):
            with self.assertRaises(KisFailure):
                parse_ticks(message, "NXT", self.received)

    def test_subscription_ack_alone_does_not_verify_realtime(self):
        messages = [json.dumps({"header": {"tr_id": "H0NXCNT0", "tr_key": symbol}, "body": {"rt_cd": "0", "output": {"key": "fixture-hidden"}}}) for symbol in FEEDS["NXT"][4]]
        socket = Socket(messages)
        requests = []
        def handler(request):
            requests.append(request)
            return httpx.Response(200, json={"approval_key": "fixture-approval"})
        def connector(url, **kwargs):
            self.assertEqual(url, "ws://ops.koreainvestment.com:21000")
            self.assertIsNone(kwargs["proxy"])
            return socket
        with patch("gon_stock02.feed.time.sleep"):
            report = probe_feed("NXT", 1, credentials=self.credentials, transport=httpx.MockTransport(handler), connector=connector)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].method, "POST")
        self.assertEqual(requests[0].url.path, "/oauth2/Approval")
        self.assertNotIn(b"12345678", requests[0].content)
        self.assertEqual(len(report["subscriptions"]), 3)
        self.assertFalse(report["fresh_ticks_received_for_all"])
        self.assertNotIn("fixture-", json.dumps(report))
        self.assertTrue(all(msg["body"]["input"]["tr_id"] == "H0NXCNT0" for msg in socket.sent))

    def test_approval_redirect_or_error_never_reaches_websocket(self):
        for response in (httpx.Response(302, headers={"Location": "https://example.invalid"}),
                         httpx.Response(200, json={"error": "fixture-secret"})):
            report = probe_feed("KRX", 1, credentials=self.credentials,
                                transport=httpx.MockTransport(lambda _: response),
                                connector=lambda *a, **k: self.fail("must not connect"))
            self.assertIn("error", report)
            self.assertFalse(report["fresh_ticks_received_for_all"])
            self.assertNotIn("fixture-secret", json.dumps(report))

    def test_invalid_probe_cannot_load_credentials(self):
        for venue, seconds in (("UNIFIED", 15), ("NXT", 0), ("NXT", 61), ("NXT", True)):
            with self.assertRaises(KisFailure):
                probe_feed(venue, seconds)


if __name__ == "__main__":
    unittest.main()
