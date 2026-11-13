import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import sqlite3

from gon_stock02.kis import KisFailure, PaperClient, SYMBOLS, load_credentials
from gon_stock02.feed import probe_feed
from gon_stock02.orders import OrderService


def probe(client):
    report = {"environment": "mock", "started_at": datetime.now(timezone.utc).isoformat(), "orders_sent": 0,
              "checks": [], "realtime_verified": False, "nxt_order_support": "unverified"}
    try:
        client.authenticate()
    except KisFailure as exc:
        report["checks"].append({"operation": "authenticate", "status": "failed", "reason": str(exc)})
        report["stopped_early"] = True
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        return report
    checks = [("balance", None, None)] + [("quote", symbol, venue) for symbol in SYMBOLS for venue in ("KRX", "NXT", "UNIFIED")] + [("bars", symbol, None) for symbol in SYMBOLS]
    for operation, symbol, venue in checks:
        check = {"operation": operation, "symbol": symbol, "venue": venue}
        try:
            if operation == "balance":
                result = client.balance_status()
            elif operation == "quote":
                result = client.quote(symbol, venue)
            else:
                result = client.bars(symbol)
            check.update(status="read_ok", result=result)
        except KisFailure as exc:
            check.update(status="failed", reason=str(exc))
        report["checks"].append(check)
        print(json.dumps({key: value for key, value in check.items() if key != "result"}, ensure_ascii=False), flush=True)
        if check.get("reason") in ("rate_limited", "network_error", "timeout", "authentication_failed"):
            report["stopped_early"] = True
            break
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    return report


def check_orders(service):
    result = service.reconcile()
    states = {}
    for row in service.all_orders():
        states[row['state']] = states.get(row['state'], 0) + 1
    return {'environment': 'mock', 'checked_at': datetime.now(timezone.utc).isoformat(),
            **result, 'states': states, 'private_values_logged': False,
            'broker_order_lifecycle_verified': False}


def main():
    parser = argparse.ArgumentParser(description="KIS connection checks; no orders")
    parser.add_argument("command", choices=("probe", "feed-probe", "order-check"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--venue", choices=("KRX", "NXT"), default="KRX")
    parser.add_argument("--seconds", type=int, default=15)
    parser.add_argument("--policy", type=Path, default=Path("config/paper.json"))
    args = parser.parse_args()
    try:
        if args.command == "feed-probe":
            report = probe_feed(args.venue, args.seconds)
        elif args.command == "order-check":
            policy = json.loads(args.policy.read_text())
            with PaperClient(load_credentials()) as client, OrderService(client, policy) as service:
                report = check_orders(service)
        else:
            with PaperClient(load_credentials()) as client:
                report = probe(client)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"report": str(args.output), "orders_sent": 0, "checks": len(report.get("checks", []))}))
        if args.command == "feed-probe":
            print(json.dumps({key: report.get(key) for key in ("venue", "subscriptions", "tick_counts", "fresh_tick_counts", "fresh_ticks_received_for_all", "error")}))
            if not report["fresh_ticks_received_for_all"]:
                raise SystemExit(1)
        elif args.command == "order-check":
            print(json.dumps(report, ensure_ascii=False))
            if not report['consistent']:
                raise SystemExit(1)
        elif report.get("stopped_early") or any(check["status"] != "read_ok" for check in report["checks"]):
            raise SystemExit(1)
    except (KisFailure, OSError, sqlite3.Error, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc) if isinstance(exc, KisFailure) else "local_state_or_input_error", "orders_sent": 0}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
