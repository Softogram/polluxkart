"""Tests for the pre-push hook. A fake gh stands in for GitHub."""

from __future__ import annotations

import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pre_push
from pre_push import Unknown, open_pull_request, parse_push_lines, protected_refs

ROOT = Path(__file__).resolve().parents[2]
ZERO = "0" * 40
SHA = "a" * 40


def line(local_ref, local_sha, remote_ref, remote_sha) -> str:
    return "%s %s %s %s" % (local_ref, local_sha, remote_ref, remote_sha)


class ParseTest(unittest.TestCase):
    def test_p1_24_kinds(self) -> None:
        text = "\n".join([
            line("refs/heads/feature/a", SHA, "refs/heads/feature/a", "b" * 40),
            line("refs/heads/feature/new", SHA, "refs/heads/feature/new", ZERO),
            line("(delete)", ZERO, "refs/heads/old", SHA),
            line("refs/tags/v1", SHA, "refs/tags/v1", ZERO),
        ])
        refs = parse_push_lines(text)
        self.assertEqual(len(refs), 4)
        self.assertEqual(refs[0].branch, "feature/a")
        self.assertFalse(refs[0].is_delete)
        self.assertTrue(refs[1].local_sha != ZERO)
        self.assertTrue(refs[2].is_delete)
        self.assertTrue(refs[3].is_tag)
        self.assertEqual(protected_refs(refs), [])

    def test_p1_25_empty_input(self) -> None:
        self.assertEqual(pre_push.main(stdin=io.StringIO("")), 0)


class OpenPullRequestTest(unittest.TestCase):
    def test_p1_21_timeout(self) -> None:
        def run(*_a, **_k):
            raise subprocess.TimeoutExpired(["gh"], 15)

        result = open_pull_request("feature/a", run=run, which=lambda n: "/bin/gh")
        self.assertIsInstance(result, Unknown)
        self.assertIn("15 seconds", result.reason)
        stream = io.StringIO()
        code = pre_push.main(
            stdin=io.StringIO(line("refs/heads/feature/a", SHA, "refs/heads/feature/a", ZERO) + "\n"),
            run=run,
            which=lambda n: "/bin/gh",
            stream=stream,
        )
        self.assertEqual(code, 0)
        self.assertIn("Could not check", stream.getvalue())

    def test_p1_22_timeout_and_flags(self) -> None:
        calls = []

        def run(argv, capture_output=False, text=False, timeout=None, cwd=None):
            calls.append((list(argv), timeout))
            return SimpleNamespace(returncode=0, stdout="[]\n", stderr="")

        open_pull_request("feature/a", run=run, which=lambda n: "/bin/gh")
        self.assertEqual(calls[0][1], 15)
        self.assertIn("--head", calls[0][0])
        self.assertIn("feature/a", calls[0][0])
        self.assertIn("--state", calls[0][0])
        self.assertIn("open", calls[0][0])

    def test_p1_23_not_json(self) -> None:
        def run(argv, capture_output=False, text=False, timeout=None, cwd=None):
            return SimpleNamespace(returncode=0, stdout="nope\n", stderr="")

        result = open_pull_request("feature/a", run=run, which=lambda n: "/bin/gh")
        self.assertIsInstance(result, Unknown)


class SandboxPushTest(unittest.TestCase):
    def test_p1_2_refuse_development(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "branch", "development"])
            result = box.push("development")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("development", result.stderr)
            self.assertIn("development-process.md", result.stderr)
            self.assertFalse(box.remote_has("development"))

    def test_p1_3_refuse_main(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "branch", "main"])
            result = box.push("main")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("main", result.stderr)

    def test_p1_1_no_open_pr(self) -> None:
        with _Sandbox(gh_body="[]") as box:
            box.commit("start")
            result = box.push("feature/a")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())
            self.assertIn("No open pull request", result.stderr)

    def test_p1_6_skip_does_not_allow_development(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "branch", "development"])
            result = box.push("development", env={"SKIP_LOCAL_CI": "1"})
            self.assertNotEqual(result.returncode, 0)

    def test_p1_9_open_pr_runs_make_ci(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            result = box.push("feature/a")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((box.repo / ".make-ci-ran").exists())

    def test_p1_10_failing_make_ci_refuses(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]', ci_ok=False) as box:
            box.commit("start")
            result = box.push("feature/a")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SKIP_LOCAL_CI=1", result.stderr)
            self.assertFalse(box.remote_has("feature/a"))

    def test_p1_11_skip_allows_failing_ci(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]', ci_ok=False) as box:
            box.commit("start")
            result = box.push("feature/a", env={"SKIP_LOCAL_CI": "1"})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())
            self.assertIn("#12", result.stderr)

    def test_p1_13_uncommitted_file(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            (box.repo / "README").write_text("dirty\n")
            result = box.push("feature/a")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("README", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_p1_19_gh_missing(self) -> None:
        with _Sandbox(include_gh=False) as box:
            box.commit("start")
            result = box.push("feature/a")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("gh is not installed", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_f4_1_hooks_are_executable_in_index(self) -> None:
        for name in ("pre-commit", "pre-push"):
            listed = subprocess.check_output(
                ["git", "ls-files", "-s", ".githooks/%s" % name],
                cwd=str(ROOT),
                text=True,
            )
            if not listed.strip():
                mode = os.stat(ROOT / ".githooks" / name).st_mode
                self.assertTrue(mode & stat.S_IXUSR)
                continue
            self.assertTrue(listed.startswith("100755"), listed)


class _Sandbox:
    def __init__(self, gh_body="[]", ci_ok=True, include_gh=True):
        self.gh_body = gh_body
        self.ci_ok = ci_ok
        self.include_gh = include_gh
        self.temp = None
        self.repo = None
        self.remote = None
        self.bindir = None

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.remote = base / "remote.git"
        self.bindir = base / "bin"
        self.repo.mkdir()
        self.bindir.mkdir()
        subprocess.check_call(["git", "init", "-q", "-b", "feature/a"], cwd=self.repo)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=self.repo)
        subprocess.check_call(["git", "config", "user.name", "test"], cwd=self.repo)
        subprocess.check_call(["git", "config", "core.hooksPath", ".githooks"], cwd=self.repo)
        subprocess.check_call(["git", "init", "-q", "--bare", str(self.remote)])
        subprocess.check_call(["git", "remote", "add", "origin", str(self.remote)], cwd=self.repo)
        hooks = self.repo / ".githooks"
        hooks.mkdir()
        for name in ("pre-commit", "pre-push"):
            src = ROOT / ".githooks" / name
            dest = hooks / name
            dest.write_text(src.read_text())
            dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        githooks = self.repo / "tools" / "githooks"
        githooks.mkdir(parents=True)
        for name in ("pre_push.py", "pre_commit.py"):
            (githooks / name).write_text((ROOT / "tools" / "githooks" / name).read_text())
        makefile = self.repo / "Makefile"
        exit_code = 0 if self.ci_ok else 1
        makefile.write_text("ci:\n\t@echo ran > .make-ci-ran\n\t@exit %s\n" % exit_code)
        (self.repo / "README").write_text("ok\n")
        if self.include_gh:
            gh = self.bindir / "gh"
            gh.write_text("#!/bin/sh\ncat <<'EOF'\n%s\nEOF\n" % self.gh_body)
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        for cmd in ("make", "git", "python3"):
            found = shutil.which(cmd)
            if found:
                dest = self.bindir / cmd
                if not dest.exists():
                    os.symlink(found, dest)
        self._path = str(self.bindir) + os.pathsep + "/usr/bin" + os.pathsep + "/bin"
        return self

    def __exit__(self, *exc):
        self.temp.cleanup()

    def run(self, argv, env=None, check=True):
        merged = os.environ.copy()
        merged["PATH"] = self._path
        if env:
            merged.update(env)
            if "PATH" not in env:
                merged["PATH"] = self._path
        return subprocess.run(argv, cwd=str(self.repo), env=merged, capture_output=True, text=True, check=check)

    def commit(self, message: str) -> None:
        self.run(["git", "add", "README", "Makefile", ".githooks", "tools"])
        self.run(["git", "commit", "-q", "-m", message, "--no-verify"])

    def push(self, branch: str, env=None):
        env_all = os.environ.copy()
        env_all["PATH"] = self._path
        if env:
            env_all.update(env)
            env_all["PATH"] = self._path
        return subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=str(self.repo),
            env=env_all,
            capture_output=True,
            text=True,
        )

    def remote_has(self, branch: str) -> bool:
        listed = subprocess.run(
            ["git", "show-ref", "--heads"],
            cwd=str(self.remote),
            capture_output=True,
            text=True,
        )
        return "refs/heads/%s" % branch in (listed.stdout or "")


if __name__ == "__main__":
    unittest.main()
