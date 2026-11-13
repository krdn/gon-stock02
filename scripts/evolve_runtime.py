import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request


VERSION = "23.2.1"
COMMIT = "577f1b88708154769bdcf3231bd2ae8b194f15a9"


def environment(root, original=None):
    original = os.environ if original is None else original
    env = {
        key: value for key, value in original.items()
        if not key.endswith("_API_KEY")
        and key != "ANTHROPIC_AUTH_TOKEN"
        and not key.startswith(("EVOLVE_", "KIS_", "GS02_", "INFISICAL_"))
    }
    if sys.platform == "linux":
        env["PATH"] = "/usr/bin:" + env.get("PATH", os.defpath)
    env.update(EVOLVE_PROJECT_ROOT=str(root), EVOLVE_PLUGIN_ROOT=str(root))
    return env


def native(root, args, capture=False):
    return subprocess.run(
        ["evolve", *args], cwd=root, env=environment(root), check=True,
        text=True, capture_output=capture,
    )


def initial_policy():
    return {
        "workflow": {
            "max_cycles_cap": 3, "max_consecutive_fails": 1,
            "universal_fallback": False,
        },
        "chain": {"enabled": True, "max_batches": 3},
        "sandbox": {"mode": "on"},
    }


def verify_version(root):
    version = native(root, ["--version"], capture=True).stdout.split()
    if len(version) < 2 or version[1] != VERSION:
        raise RuntimeError("evolve version differs from the verified upstream version")


def validate_policy(root):
    actual = json.loads((root / ".evolve/policy.json").read_text())
    for group, expected in initial_policy().items():
        if any(actual.get(group, {}).get(key) != value for key, value in expected.items()):
            raise RuntimeError("runtime policy limits differ: " + group)


def verified_files(files, hashes):
    for name, expected in hashes.items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError("invalid upstream path")
        if name not in files or hashlib.sha256(files[name]).hexdigest() != expected:
            raise RuntimeError("upstream hash mismatch: " + name)


def install_files(root, files, hashes):
    verified_files(files, hashes)
    for name in hashes:
        target = root / name
        if target.exists() and target.read_bytes() != files[name]:
            raise RuntimeError("existing file differs: " + name)
    for name in hashes:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[name])


def download_files(hashes):
    request = urllib.request.Request(
        "https://api.github.com/repos/mickeyyaya/evolve-loop/tarball/" + COMMIT,
        headers={"User-Agent": "gon-stock02-evolve-setup"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive:
            name = member.name.partition("/")[2]
            if name in hashes and member.isfile():
                files[name] = archive.extractfile(member).read()
    verified_files(files, hashes)
    return files


def prepare(project):
    target = project / ".local/evolve/runtime"
    if target.exists():
        raise RuntimeError("runtime already exists; preserve it and use inspect/status")
    verify_version(project)
    lock = json.loads((project / "config/evolve-upstream.json").read_text())
    files = download_files(lock["sha256"])
    subprocess.run(["git", "clone", "--no-hardlinks", str(project), str(target)], check=True)
    subprocess.run([
        "git", "-C", str(target), "remote", "set-url", "origin",
        "https://github.com/krdn/gon-stock02.git",
    ], check=True)
    install_files(target, files, lock["sha256"])
    exclude = target / ".git/info/exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as output:
        output.write("\n/.evolve/\n" + "\n".join("/" + name for name in lock["sha256"]) + "\n")
    (target / ".evolve/policy.json").write_text(json.dumps(initial_policy(), indent=2) + "\n")
    goal = target / "config/evolve-goal.md"
    goal.parent.mkdir(exist_ok=True)
    goal.write_bytes((project / "config/evolve-goal.md").read_bytes())
    (target / "config/evolve-upstream.json").write_bytes((project / "config/evolve-upstream.json").read_bytes())
    native(target, ["setup", "apply", "--preset", "recommended"])
    validate_policy(target)
    (target / ".evolve/gon-stock02-prepared.json").write_text(json.dumps({"status": "configured", "version": VERSION, "commit": COMMIT}) + "\n")
    print("Prepared isolated runtime:", target)
    print("Readiness and full-cycle execution remain unverified. Run check.")


def check(root):
    if sys.platform != "darwin":
        raise RuntimeError(
            "evolve 23.2.1 linked-worktree Git isolation is unsupported on "
            + sys.platform + "; no model or cycle dispatched"
        )
    verify_version(root)
    marker = root / ".evolve/gon-stock02-prepared.json"
    if not marker.is_file() or json.loads(marker.read_text()) != {"status": "configured", "version": VERSION, "commit": COMMIT}:
        raise RuntimeError("runtime preparation is incomplete")
    validate_policy(root)
    project = Path(__file__).resolve().parents[1]
    lock = json.loads((project / "config/evolve-upstream.json").read_text())
    verified_files(
        {name: (root / name).read_bytes() for name in lock["sha256"]}, lock["sha256"],
    )


def loop_arguments(action, root):
    args = ["loop", "--project-root", str(root)]
    if action == "start":
        return args + [
            "--cycles", "1", "--until-inbox-empty", "--strategy", "balanced",
            "--goal-file", str(root / "config/evolve-goal.md"),
        ]
    return args + ["--" + action]


def dispatch(root, action):
    check(root)
    return native(root, loop_arguments(action, root)).returncode


def main():
    parser = argparse.ArgumentParser(description="Bounded native Evolve Loop entry point")
    parser.add_argument("action", choices=["prepare", "inspect", "check", "start", "resume", "auto-resume", "status", "stop"])
    action = parser.parse_args().action
    project = Path(__file__).resolve().parents[1]
    root = project / ".local/evolve/runtime"
    try:
        if action == "prepare":
            prepare(project)
        elif action == "check":
            check(root)
            native(root, ["loop", "--preflight-only"])
        elif action in {"start", "resume", "auto-resume"}:
            dispatch(root, action)
        else:
            args = {"inspect": ["setup", "detect", "--json"], "status": ["status", "--json"], "stop": ["loop-stop"]}[action]
            native(root, args)
    except subprocess.CalledProcessError as error:
        print(str(error), file=sys.stderr)
        return error.returncode if error.returncode > 0 else 128 - error.returncode
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, tarfile.TarError) as error:
        print(str(error), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
