"""Tests for the pre-push hook. A fake gh stands in for GitHub."""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import sys
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


def _without_git_vars(env: dict) -> dict:
    cleaned = dict(env)
    for key in list(cleaned):
        if key.startswith("GIT_"):
            del cleaned[key]
    return cleaned


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
        stream = io.StringIO()
        code = pre_push.main(
            stdin=io.StringIO(line("refs/heads/feature/a", SHA, "refs/heads/feature/a", ZERO) + "\n"),
            run=run,
            which=lambda n: "/bin/gh",
            stream=stream,
        )
        self.assertEqual(code, 0)
        self.assertIn("Could not check", stream.getvalue())
        self.assertNotIn("No open pull request", stream.getvalue())


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

    def test_p1_4_refuse_delete_development(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "branch", "development"])
            seeded = box.run(["git", "push", "--no-verify", "origin", "development"])
            self.assertEqual(seeded.returncode, 0, seeded.stderr)
            self.assertTrue(box.remote_has("development"))
            result = box.push(":development")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("development", result.stderr)
            self.assertTrue(box.remote_has("development"))

    def test_p1_5_refuse_mixed_push(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "branch", "development"])
            result = box.push("feature/a", "development")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(box.remote_has("feature/a"))
            self.assertFalse(box.remote_has("development"))

    def test_p1_6_skip_does_not_allow_development(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "branch", "development"])
            result = box.push("development", env={"SKIP_LOCAL_CI": "1"})
            self.assertNotEqual(result.returncode, 0)

    def test_p1_7_tag_push_does_not_call_gh(self) -> None:
        with _Sandbox() as box:
            box.commit("start")
            box.run(["git", "tag", "v1"])
            result = box.push("refs/tags/v1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(box.gh_was_called())
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_p1_8_first_push_of_new_branch(self) -> None:
        with _Sandbox(gh_body="[]") as box:
            box.commit("start")
            box.run(["git", "checkout", "-q", "-b", "feature/new"])
            result = box.push("feature/new")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())
            self.assertTrue(box.remote_has("feature/new"))

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

    def test_p1_12_skip_true_is_not_the_hatch(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]', ci_ok=False) as box:
            box.commit("start")
            result = box.push("feature/a", env={"SKIP_LOCAL_CI": "true"})
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((box.repo / ".make-ci-ran").exists())
            self.assertFalse(box.remote_has("feature/a"))

    def test_p1_13_uncommitted_file(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            (box.repo / "README").write_text("dirty\n")
            result = box.push("feature/a")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("README", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_p1_14_untracked_file(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            (box.repo / "extra.txt").write_text("untracked\n")
            result = box.push("feature/a")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("extra.txt", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())
            self.assertFalse(box.remote_has("feature/a"))

    def test_p1_15_gitignored_file_does_not_refuse(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            (box.repo / ".gitignore").write_text("ignored.txt\n")
            box.commit("start")
            (box.repo / "ignored.txt").write_text("secret\n")
            result = box.push("feature/a")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((box.repo / ".make-ci-ran").exists())

    def test_p1_16_more_than_twenty_dirty_files(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            for index in range(21):
                (box.repo / ("dirty-%02d.txt" % index)).write_text("x\n")
            result = box.push("feature/a")
            self.assertNotEqual(result.returncode, 0)
            combined = result.stderr + result.stdout
            listed = sum(1 for index in range(21) if ("dirty-%02d.txt" % index) in combined)
            self.assertEqual(listed, 20)
            self.assertIn("and 1 more", combined)
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_p1_17_push_other_branch_while_checked_out(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            box.run(["git", "checkout", "-q", "-b", "feature/b"])
            (box.repo / "README").write_text("on-b\n")
            box.run(["git", "add", "README"])
            box.run(["git", "commit", "-q", "-m", "on-b", "--no-verify"])
            box.run(["git", "checkout", "-q", "feature/a"])
            result = box.push("feature/b")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("own worktree", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())
            self.assertFalse(box.remote_has("feature/b"))

    def test_p1_18_second_worktree_uses_own_files(self) -> None:
        with _Sandbox(gh_body='[{"number":12}]') as box:
            box.commit("start")
            worktree = Path(box.temp.name) / "wt2"
            added = box.run(["git", "worktree", "add", str(worktree), "-b", "feature/b"])
            self.assertEqual(added.returncode, 0, added.stderr)
            result = box.push("feature/b", cwd=worktree)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((worktree / ".make-ci-ran").exists())
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_p1_19_gh_missing(self) -> None:
        with _Sandbox(include_gh=False) as box:
            box.commit("start")
            result = box.push("feature/a")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("gh is not installed", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_p1_20_gh_not_logged_in(self) -> None:
        with _Sandbox(gh_exit=1, gh_stderr="not logged in") as box:
            box.commit("start")
            result = box.push("feature/a")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("not logged in", result.stderr)
            self.assertIn("Could not check", result.stderr)
            self.assertFalse((box.repo / ".make-ci-ran").exists())

    def test_f4_1_hooks_are_executable_in_index(self) -> None:
        env = _without_git_vars(os.environ)
        for name in ("pre-commit", "pre-push"):
            listed = subprocess.check_output(
                ["git", "ls-files", "-s", ".githooks/%s" % name],
                cwd=str(ROOT),
                env=env,
                text=True,
            )
            self.assertTrue(listed.strip(), ".githooks/%s is not in the index" % name)
            self.assertTrue(listed.startswith("100755"), listed)


class _Sandbox:
    def __init__(self, gh_body="[]", ci_ok=True, include_gh=True, gh_exit=0, gh_stderr=""):
        self.gh_body = gh_body
        self.ci_ok = ci_ok
        self.include_gh = include_gh
        self.gh_exit = gh_exit
        self.gh_stderr = gh_stderr
        self.temp = None
        self.repo = None
        self.remote = None
        self.bindir = None
        self._git_exec_path = None
        self._gh_log = None

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.remote = base / "remote.git"
        self.bindir = base / "bin"
        self.repo.mkdir()
        self.bindir.mkdir()
        host = _without_git_vars(os.environ)
        subprocess.check_call(["git", "init", "-q", "-b", "feature/a"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "config", "user.name", "test"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "config", "core.hooksPath", ".githooks"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "init", "-q", "--bare", str(self.remote)], env=host)
        subprocess.check_call(["git", "remote", "add", "origin", str(self.remote)], cwd=self.repo, env=host)
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
        self._install_path()
        return self

    def __exit__(self, *exc):
        self.temp.cleanup()

    def _install_path(self) -> None:
        git_bin = shutil.which("git")
        make_bin = shutil.which("make")
        if not git_bin or not make_bin:
            raise RuntimeError("run make doctor: git or make is missing")
        self._link(git_bin, "git")
        self._link(make_bin, "make")
        self._link(sys.executable, "python3")
        exec_path = subprocess.check_output([git_bin, "--exec-path"], text=True).strip()
        self._git_exec_path = exec_path
        for helper in ("git-receive-pack", "git-upload-pack"):
            helper_path = Path(exec_path) / helper
            if helper_path.exists():
                self._link(str(helper_path), helper)
        for extra in ("sh", "uname", "tr", "sed", "basename", "dirname", "cat"):
            found = "/bin/%s" % extra if extra == "sh" else shutil.which(extra)
            if found:
                self._link(found, extra)
        if self.include_gh:
            self._write_gh()
        self._path = str(self.bindir)

    def _link(self, source: str, name: str) -> None:
        dest = self.bindir / name
        if dest.exists() or dest.is_symlink():
            return
        os.symlink(source, dest)

    def _write_gh(self) -> None:
        self._gh_log = self.bindir / "gh-calls.log"
        gh = self.bindir / "gh"
        lines = [
            "#!/bin/sh",
            'echo "$@" >> "%s"' % self._gh_log,
        ]
        if self.gh_exit != 0:
            lines.append("echo '%s' >&2" % self.gh_stderr.replace("'", "'\"'\"'"))
            lines.append("exit %s" % self.gh_exit)
        else:
            lines.append("cat <<'EOF'")
            lines.append(self.gh_body)
            lines.append("EOF")
        gh.write_text("\n".join(lines) + "\n")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    def _env(self, extra=None):
        merged = _without_git_vars(os.environ)
        merged.pop("SKIP_LOCAL_CI", None)
        merged["PATH"] = self._path
        if self._git_exec_path:
            merged["GIT_EXEC_PATH"] = self._git_exec_path
        if extra:
            merged.update(extra)
            merged["PATH"] = self._path
        return merged

    def run(self, argv, env=None, check=True, cwd=None):
        return subprocess.run(
            argv,
            cwd=str(cwd or self.repo),
            env=self._env(env),
            capture_output=True,
            text=True,
            check=check,
        )

    def commit(self, message: str) -> None:
        self.run(["git", "add", "README", "Makefile", ".githooks", "tools"])
        if (self.repo / ".gitignore").exists():
            self.run(["git", "add", ".gitignore"])
        self.run(["git", "commit", "-q", "-m", message, "--no-verify"])

    def push(self, *refs, env=None, cwd=None):
        if not refs:
            raise ValueError("push needs at least one ref")
        return subprocess.run(
            ["git", "push", "origin", *refs],
            cwd=str(cwd or self.repo),
            env=self._env(env),
            capture_output=True,
            text=True,
        )

    def gh_was_called(self) -> bool:
        if self._gh_log is None or not self._gh_log.exists():
            return False
        return bool(self._gh_log.read_text().strip())

    def remote_has(self, branch: str) -> bool:
        listed = subprocess.run(
            ["git", "show-ref", "--heads"],
            cwd=str(self.remote),
            env=self._env(),
            capture_output=True,
            text=True,
        )
        return "refs/heads/%s" % branch in (listed.stdout or "")


if __name__ == "__main__":
    unittest.main()
