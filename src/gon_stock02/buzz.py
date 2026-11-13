import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric import ec


STATE = Path.home() / ".local/share/buzz-gon/agents"
CLI = "/home/gon/.local/opt/buzz-cli-8d400a695f8e/buzz"
RELAY = "https://buzz.krdn.kr"
PREFIX = "ggw-gon-stock02-"


class BuzzFailure(Exception):
    pass


def execute(name, action, event, content=None, *, state_dir=STATE, runner=subprocess.run):
    if not re.fullmatch(PREFIX + r"[a-z0-9-]{1,40}", name):
        raise BuzzFailure("invalid_agent")
    if action not in ("read", "reply") or not re.fullmatch(r"[a-f0-9]{64}", event):
        raise BuzzFailure("invalid_request")
    if action == "reply" and (not isinstance(content, str) or not content.strip() or len(content.encode()) > 60000):
        raise BuzzFailure("invalid_content")
    try:
        record = json.loads((state_dir / (name + ".json")).read_text(encoding="utf-8"))
        if record["name"] != name or record["relay"] != RELAY:
            raise BuzzFailure("identity_mismatch")
        for field in ("owner", "pubkey"):
            if not re.fullmatch(r"[a-f0-9]{64}", record[field]):
                raise BuzzFailure("invalid_identity")
        channel = str(UUID(record["channel"]))
        attrs = ["application", "buzz-gon-agent", "relay", RELAY, "owner", record["owner"], "name", name]
        saved = runner(["/usr/bin/secret-tool", "lookup", *attrs], capture_output=True, text=True, timeout=30)
        if saved.returncode:
            raise BuzzFailure("credential_unavailable")
        bundle = json.loads(saved.stdout)
        key = bundle["private_key"]
        if not isinstance(key, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", key):
            raise BuzzFailure("invalid_identity")
        public = ec.derive_private_key(int(key, 16), ec.SECP256K1()).public_key().public_numbers().x
        if public.to_bytes(32, "big").hex() != record["pubkey"] or bundle["pubkey"] != record["pubkey"]:
            raise BuzzFailure("identity_mismatch")
        auth = bundle["auth_tag"]
        if not isinstance(auth, str) or not auth or "\0" in auth:
            raise BuzzFailure("invalid_identity")
        env = os.environ.copy()
        env.update(BUZZ_PRIVATE_KEY=key, BUZZ_AUTH_TAG=auth, BUZZ_RELAY_URL=RELAY)
        args = [CLI, "--relay", RELAY, "--format", "compact", "messages"]
        if action == "read":
            args += ["thread", "--channel", channel, "--event", event, "--limit", "30"]
        else:
            args += ["send", "--channel", channel, "--reply-to", event, "--content", "-"]
        result = runner(args, input=content, env=env, capture_output=True, text=True, timeout=45)
        if result.returncode:
            raise BuzzFailure("relay_request_failed")
        output = json.loads(result.stdout)
        if action == "reply" and (not isinstance(output, dict) or output.get("accepted") is not True):
            raise BuzzFailure("reply_not_accepted")
        return output
    except BuzzFailure:
        raise
    except (OSError, ValueError, KeyError, TypeError, OverflowError, subprocess.TimeoutExpired):
        raise BuzzFailure("identity_or_response_invalid") from None


def main():
    parser = argparse.ArgumentParser(description="Project-scoped Buzz research identity")
    parser.add_argument("--name", required=True)
    parser.add_argument("action", choices=("read", "reply"))
    parser.add_argument("--event", required=True)
    parser.add_argument("--file", type=Path)
    args = parser.parse_args()
    try:
        content = args.file.read_text(encoding="utf-8") if args.file else None
        output = execute(args.name, args.action, args.event, content)
        print(json.dumps(output, ensure_ascii=False))
    except (BuzzFailure, OSError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc) if isinstance(exc, BuzzFailure) else "input_file_unavailable"}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
