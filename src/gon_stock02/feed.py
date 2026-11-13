from datetime import datetime, timezone
import json
import re
import time
from zoneinfo import ZoneInfo

import httpx
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

from gon_stock02.kis import HOST, SYMBOLS, KisFailure, _load_credentials, number


FEEDS = {
    "KRX": ("mock", HOST, "ws://ops.koreainvestment.com:31000", "H0STCNT0", tuple(SYMBOLS)),
    "NXT": ("real", "https://openapi.koreainvestment.com:9443", "ws://ops.koreainvestment.com:21000", "H0NXCNT0", ("005930", "000660", "009150")),
}


def parse_ticks(message, venue, received_at):
    try:
        flag, tr_id, count, payload = message.split("|", 3)
        if flag != "0" or tr_id != FEEDS[venue][3] or not re.fullmatch(r"[0-9]{1,3}", count):
            raise KisFailure("unexpected_feed_frame")
        count = int(count)
        fields = payload.split("^")
        if count < 1 or len(fields) != count * 47:
            raise KisFailure("invalid_feed_layout")
        ticks = []
        for offset in range(0, len(fields), 47):
            row = fields[offset:offset + 47]
            if row[0] not in FEEDS[venue][4] or not re.fullmatch(r"[0-9]{14}", row[33] + row[1]):
                raise KisFailure("invalid_feed_instrument_or_time")
            event_time = datetime.strptime(row[33] + row[1], "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("Asia/Seoul"))
            age = (received_at - event_time).total_seconds()
            price = number(row[2], positive=True)
            ask, bid = number(row[10]), number(row[11])
            ticks.append({
                "symbol": row[0], "venue": venue, "tr_id": tr_id,
                "event_time": event_time.isoformat(), "received_at": received_at.isoformat(),
                "event_age_seconds": age, "fresh_at_receipt": 0 <= age <= 5,
                "price": str(price), "ask": str(ask), "bid": str(bid),
                "trade_volume": str(number(row[12])), "cumulative_volume": str(number(row[13])),
                "cumulative_value": str(number(row[14])),
                "ask_size": str(number(row[36])), "bid_size": str(number(row[37])),
                "halt_code": row[35], "hour_class": row[43], "market_class": row[46],
                "valid_two_sided_quote": 0 < bid <= ask and row[35] == "N" and row[43] == "0",
                "order_submission_enabled": False,
            })
        return ticks
    except KisFailure:
        raise
    except (ValueError, TypeError, KeyError, AttributeError):
        raise KisFailure("invalid_feed_frame") from None


def probe_feed(venue, seconds, *, credentials=None, transport=None, connector=connect):
    if venue not in FEEDS or type(seconds) is not int or not 1 <= seconds <= 60:
        raise KisFailure("invalid_feed_probe")
    environment, rest, websocket, tr_id, symbols = FEEDS[venue]
    credentials = credentials or _load_credentials(environment)
    report = {"venue": venue, "credential_environment": environment, "purpose": "market_data_only",
              "started_at": datetime.now(timezone.utc).isoformat(), "orders_sent": 0,
              "subscriptions": [], "tick_counts": {symbol: 0 for symbol in symbols},
              "fresh_tick_counts": {symbol: 0 for symbol in symbols}, "latest": {}}
    try:
        with httpx.Client(transport=transport, timeout=15, follow_redirects=False, trust_env=False) as http:
            response = http.post(rest + "/oauth2/Approval", json={"grant_type": "client_credentials",
                                 "appkey": credentials.app_key, "secretkey": credentials.secret_key})
            if response.status_code != 200:
                raise KisFailure("feed_approval_failed")
            approval = response.json().get("approval_key")
            if not isinstance(approval, str) or not re.fullmatch(r"[!-~]+", approval):
                raise KisFailure("invalid_feed_approval")
        with connector(websocket, proxy=None, open_timeout=10, close_timeout=5, max_size=1048576) as socket:
            for symbol in symbols:
                socket.send(json.dumps({"header": {"approval_key": approval, "custtype": "P", "tr_type": "1", "content-type": "utf-8"},
                                        "body": {"input": {"tr_id": tr_id, "tr_key": symbol}}}))
                time.sleep(0.1)
            approval = ""
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                try:
                    message = socket.recv(timeout=max(0.01, deadline - time.monotonic()))
                except TimeoutError:
                    break
                if not isinstance(message, str):
                    raise KisFailure("invalid_feed_frame")
                if message.startswith("{"):
                    data = json.loads(message)
                    header = data.get("header", {})
                    if header.get("tr_id") == "PINGPONG":
                        socket.pong(message.encode())
                        continue
                    if header.get("tr_id") != tr_id or header.get("tr_key") not in symbols:
                        raise KisFailure("unexpected_feed_ack")
                    if data.get("body", {}).get("rt_cd") != "0":
                        raise KisFailure("feed_subscription_rejected")
                    if header["tr_key"] not in report["subscriptions"]:
                        report["subscriptions"].append(header["tr_key"])
                    continue
                for tick in parse_ticks(message, venue, datetime.now(timezone.utc)):
                    symbol = tick["symbol"]
                    previous = report["latest"].get(symbol)
                    if previous and tick["event_time"] < previous["event_time"]:
                        raise KisFailure("feed_time_regression")
                    report["latest"][symbol] = tick
                    report["tick_counts"][symbol] += 1
                    report["fresh_tick_counts"][symbol] += int(tick["fresh_at_receipt"])
    except KisFailure as exc:
        report["error"] = str(exc)
    except (httpx.HTTPError, WebSocketException, OSError, TimeoutError):
        report["error"] = "feed_connection_failed"
    except (ValueError, TypeError, KeyError, AttributeError):
        report["error"] = "invalid_feed_response"
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["fresh_ticks_received_for_all"] = not report.get("error") and set(report["subscriptions"]) == set(symbols) and all(report["fresh_tick_counts"].values())
    return report
