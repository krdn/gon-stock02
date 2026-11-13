import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from gon_stock02.kis import KisFailure, PaperClient, SYMBOLS, load_credentials
from gon_stock02.feed import probe_feed


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


def main():
    parser = argparse.ArgumentParser(description="KIS connection checks; no orders")
    parser.add_argument("command", choices=("probe", "feed-probe"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--venue", choices=("KRX", "NXT"), default="KRX")
    parser.add_argument("--seconds", type=int, default=15)
    args = parser.parse_args()
    try:
        if args.command == "feed-probe":
            report = probe_feed(args.venue, args.seconds)
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
        elif report.get("stopped_early") or any(check["status"] != "read_ok" for check in report["checks"]):
            raise SystemExit(1)
    except KisFailure as exc:
        print(json.dumps({"error": str(exc), "orders_sent": 0}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
