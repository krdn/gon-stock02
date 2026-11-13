import importlib.util
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/evolve_runtime.py"
spec = importlib.util.spec_from_file_location("evolve_runtime", SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class EvolveRuntimeTests(unittest.TestCase):
    def test_prepare_handles_a_git_clone_without_info_directory(self):
        data = b"verified"
        name = ".evolve/profiles/builder.json"
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:gz") as output:
            member = tarfile.TarInfo("upstream/" + name)
            member.size = len(data)
            output.addfile(member, io.BytesIO(data))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config/evolve-goal.md").write_text("orders OFF")
            (root / "config/evolve-upstream.json").write_text(json.dumps({"sha256": {name: hashlib.sha256(data).hexdigest()}}))

            def execute(args, **kwargs):
                if args[:2] == ["git", "clone"]:
                    (Path(args[-1]) / ".git").mkdir(parents=True)
                return subprocess.CompletedProcess(args, 0, stdout="evolve 23.2.1")

            with patch.object(runtime.urllib.request, "urlopen", return_value=io.BytesIO(archive.getvalue())), patch.object(runtime.subprocess, "run", side_effect=execute):
                runtime.prepare(root)
            target = root / ".local/evolve/runtime"
            self.assertEqual((target / name).read_bytes(), data)
            self.assertIn("/.evolve/", (target / ".git/info/exclude").read_text())
            self.assertEqual(json.loads((target / ".evolve/policy.json").read_text())["chain"]["max_batches"], 3)
            self.assertEqual(json.loads((target / ".evolve/gon-stock02-prepared.json").read_text())["status"], "configured")

    def test_weakened_applied_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".evolve").mkdir()
            policy = runtime.initial_policy()
            policy["chain"]["max_batches"] = 999
            (root / ".evolve/policy.json").write_text(json.dumps(policy))
            with self.assertRaisesRegex(RuntimeError, "policy limits"):
                runtime.validate_policy(root)

    def test_partial_preparation_cannot_pass_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runtime.sys, "platform", "darwin"), patch.object(runtime.subprocess, "run") as run:
                run.return_value.stdout = "evolve 23.2.1"
                with self.assertRaisesRegex(RuntimeError, "preparation is incomplete"):
                    runtime.check(Path(tmp))

    def test_runtime_cannot_replace_the_trusted_hash_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / ".evolve").mkdir()
            (root / "config/evolve-upstream.json").write_text('{"sha256": {}}')
            (root / ".evolve/policy.json").write_text(json.dumps(runtime.initial_policy()))
            (root / ".evolve/gon-stock02-prepared.json").write_text(json.dumps({"status": "configured", "version": runtime.VERSION, "commit": runtime.COMMIT}))
            with patch.object(runtime.sys, "platform", "darwin"), patch.object(runtime.subprocess, "run") as run:
                run.return_value.stdout = "evolve 23.2.1"
                with self.assertRaises(FileNotFoundError):
                    runtime.check(root)

    def test_native_failure_exit_code_is_preserved(self):
        with patch.object(runtime.sys, "argv", ["evolve_runtime.py", "status"]), patch.object(runtime.subprocess, "run", side_effect=subprocess.CalledProcessError(5, ["evolve"])):
            self.assertEqual(runtime.main(), 5)

    def test_environment_uses_subscription_without_changing_parent(self):
        original = {"PATH": "/usr/local/bin:/usr/bin", "OPENAI_API_KEY": "sentinel", "CODEX_API_KEY": "sentinel"}
        with tempfile.TemporaryDirectory() as tmp:
            env = runtime.environment(Path(tmp), original)
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("CODEX_API_KEY", env)
        self.assertEqual(original["OPENAI_API_KEY"], "sentinel")
        self.assertTrue(env["PATH"].startswith("/usr/bin:"))

    def test_linux_cannot_dispatch_despite_native_preflight_exit_zero(self):
        with patch.object(runtime.sys, "platform", "linux"), patch.object(runtime.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "linked-worktree"):
                runtime.dispatch(Path("/unused"), "start")
        run.assert_not_called()

    def test_unrecognized_version_refuses_dispatch(self):
        with patch.object(runtime.sys, "platform", "darwin"), patch.object(runtime.subprocess, "run") as run:
            run.return_value.stdout = "evolve 99.0.0"
            with self.assertRaisesRegex(RuntimeError, "version"):
                runtime.dispatch(Path("/unused"), "start")
        self.assertEqual(run.call_count, 1)

    def test_start_has_finite_cycles_and_no_bypass(self):
        args = runtime.loop_arguments("start", Path("/repo"))
        self.assertEqual(args[args.index("--cycles") + 1], "1")
        self.assertIn("--until-inbox-empty", args)
        self.assertNotIn("--sandbox-off", args)
        self.assertNotIn("--skip-preflight", args)
        self.assertNotIn("--bypass-policy", args)

    def test_resume_preserves_checkpoint_budget(self):
        args = runtime.loop_arguments("auto-resume", Path("/repo"))
        self.assertIn("--auto-resume", args)
        self.assertNotIn("--resume", args)
        self.assertNotIn("--force-fresh", args)

    def test_tampered_upstream_file_never_writes_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(RuntimeError, "hash"):
                runtime.install_files(root, {"agents/evolve-scout.md": b"tampered"}, {"agents/evolve-scout.md": "0" * 64})
            self.assertFalse((root / "agents").exists())

    def test_existing_runtime_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / ".local/evolve/runtime"
            target.mkdir(parents=True)
            sentinel = target / "sentinel"
            sentinel.write_text("keep")
            with patch.object(runtime.subprocess, "run") as run:
                with self.assertRaisesRegex(RuntimeError, "already exists"):
                    runtime.prepare(root)
            run.assert_not_called()
            self.assertEqual(sentinel.read_text(), "keep")

    def test_policy_bounds_retries_and_keeps_provider_fallback_off(self):
        policy = runtime.initial_policy()
        self.assertEqual(policy["chain"]["max_batches"], 3)
        self.assertEqual(policy["workflow"]["max_cycles_cap"], 3)
        self.assertEqual(policy["workflow"]["max_consecutive_fails"], 1)
        self.assertFalse(policy["workflow"]["universal_fallback"])


if __name__ == "__main__":
    unittest.main()
