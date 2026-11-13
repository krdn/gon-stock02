import json
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from gon_stock02.buzz import BuzzFailure, RELAY, execute, main


class BuzzIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.name = "ggw-gon-stock02-quant"
        self.key = "0" * 63 + "1"
        self.public = "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
        self.record = {"name": self.name, "relay": RELAY, "owner": "b" * 64,
                       "pubkey": self.public, "channel": "12345678-1234-1234-1234-123456789abc"}
        self.path = self.root / (self.name + ".json")
        self.path.write_text(json.dumps(self.record))
        self.calls = []

    def runner(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[0].endswith("secret-tool"):
            return subprocess.CompletedProcess(args, 0, json.dumps({"private_key": self.key, "pubkey": self.public, "auth_tag": "test-auth"}), "")
        return subprocess.CompletedProcess(args, 0, '{"accepted":true,"event_id":"' + "e" * 64 + '"}', "")

    def test_reply_uses_own_channel_and_stdin_without_credentials_in_argv(self):
        result = execute(self.name, "reply", "a" * 64, "Research result", state_dir=self.root, runner=self.runner)
        self.assertTrue(result["accepted"])
        args, kwargs = self.calls[-1]
        self.assertEqual(args[args.index("--channel") + 1], self.record["channel"])
        self.assertEqual(kwargs["input"], "Research result")
        self.assertNotIn(self.key, str(args))
        self.assertNotIn("test-auth", str(args))
        self.assertNotIn(self.key, json.dumps(result))

    def test_foreign_identity_and_invalid_events_rejected_before_key_access(self):
        for name, event in [("gon-stock-research", "a" * 64), (self.name, "bad")]:
            with self.assertRaises(BuzzFailure):
                execute(name, "read", event, state_dir=self.root, runner=self.runner)
        self.assertEqual(self.calls, [])

    def test_corrupted_public_key_never_publishes(self):
        self.record["pubkey"] = "d" * 64
        self.path.write_text(json.dumps(self.record))
        with self.assertRaisesRegex(BuzzFailure, "identity_mismatch"):
            execute(self.name, "reply", "a" * 64, "result", state_dir=self.root, runner=self.runner)
        self.assertEqual(len(self.calls), 1)

    def test_cli_error_does_not_disclose_secret_output(self):
        def fail(args, **kwargs):
            if args[0].endswith("secret-tool"):
                return self.runner(args, **kwargs)
            return subprocess.CompletedProcess(args, 1, self.key, "test-auth")
        with self.assertRaisesRegex(BuzzFailure, "^relay_request_failed$"):
            execute(self.name, "reply", "a" * 64, "result", state_dir=self.root, runner=fail)

    def test_rejected_event_is_not_success(self):
        def reject(args, **kwargs):
            if args[0].endswith("secret-tool"):
                return self.runner(args, **kwargs)
            return subprocess.CompletedProcess(args, 0, '{"accepted":false}', "")
        with self.assertRaisesRegex(BuzzFailure, "reply_not_accepted"):
            execute(self.name, "reply", "a" * 64, "result", state_dir=self.root, runner=reject)

    def test_invalid_utf8_file_has_sanitized_cli_error(self):
        path = self.root / "invalid.txt"
        path.write_bytes(b"\xff")
        output = StringIO()
        code = None
        with patch("sys.argv", ["gs02-buzz", "--name", self.name, "reply", "--event", "a" * 64, "--file", str(path)]), redirect_stderr(output):
            try:
                main()
            except SystemExit as exc:
                code = exc.code
            except UnicodeError:
                pass
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["error"], "input_file_unavailable")


if __name__ == "__main__":
    unittest.main()
