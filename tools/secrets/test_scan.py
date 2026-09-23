"""Tests for the secret scan.

Test plan: docs/design/test/issue-37-secret-scanning.md

No secret-shaped value is ever written into this repository. Every test that
needs one builds it at run time from a known prefix and random characters, so
this repository's own scans stay clean. Every test that produces scanner
output also checks the generated value is not in it, which proves redaction.
"""

from __future__ import annotations

import importlib.util
import json
import os
import random
import shutil
import stat
import string
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scan  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CHECKS_DIR = ROOT / "tools" / "checks"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_secret() -> str:
    """A value shaped like a GitHub token, built now, granting nothing."""
    body = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(36))
    return "ghp_" + body


def _without_git_vars(env: dict) -> dict:
    return {key: value for key, value in env.items() if not key.startswith("GIT_")}


class _Sandbox:
    """A temporary git repository with the real config, scanner and hooks."""

    def __init__(self, with_hooks: bool = False):
        self.with_hooks = with_hooks
        self.temp = None
        self.repo = None
        self.tmpdir = None

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.tmpdir = base / "tmp"
        self.repo.mkdir()
        self.tmpdir.mkdir()
        host = _without_git_vars(os.environ)
        for argv in (
            ["git", "init", "-q", "-b", "feature/a"],
            ["git", "config", "user.email", "test@example.com"],
            ["git", "config", "user.name", "test"],
        ):
            subprocess.check_call(argv, cwd=self.repo, env=host)
        copied = [".gitleaks.toml", "tools/secrets/scan.py"]
        if self.with_hooks:
            subprocess.check_call(
                ["git", "config", "core.hooksPath", ".githooks"], cwd=self.repo, env=host
            )
            copied += [
                ".githooks/pre-commit",
                "tools/githooks/pre_commit.py",
                "tools/docslint/docslint.py",
            ]
        for rel in copied:
            dest = self.repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest)
        if self.with_hooks:
            hook = self.repo / ".githooks" / "pre-commit"
            hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
            docs = self.repo / "docs"
            (docs / "platform").mkdir(parents=True)
            (docs / "README.md").write_text(
                "# Docs\n\n## Read next\n\n- [testing](platform/testing.md)\n"
            )
            (docs / "platform" / "testing.md").write_text("# Testing\n")
        (self.repo / ".gitignore").write_text(".env\n.env.*\n!.env.example\n")
        self.git(["add", "."])
        self.git(["commit", "-q", "-m", "base", "--no-verify"])
        return self

    def __exit__(self, *exc):
        self.temp.cleanup()

    def env(self, extra=None):
        merged = _without_git_vars(os.environ)
        merged.pop("SKIP_LOCAL_CI", None)
        merged.pop("SCAN_BASE", None)
        merged["TMPDIR"] = str(self.tmpdir)
        if extra:
            merged.update(extra)
        return merged

    def run(self, argv, env=None):
        return subprocess.run(
            argv, cwd=str(self.repo), env=self.env(env), capture_output=True, text=True
        )

    def git(self, args, env=None):
        return self.run(["git"] + list(args), env=env)

    def write(self, relpath: str, text: str):
        path = self.repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def commit(self, message: str, paths):
        for path in paths:
            self.git(["add", "--", path])
        return self.git(["commit", "-q", "-m", message, "--no-verify"])

    def head(self) -> str:
        return self.git(["rev-parse", "HEAD"]).stdout.strip()

    def set_origin_development(self, commit: str | None = None):
        """Pretend origin/development exists, without a real remote."""
        self.git(["update-ref", "refs/remotes/origin/development", commit or self.head()])

    def count_commits(self) -> int:
        listed = self.git(["rev-list", "--count", "HEAD"]).stdout.strip()
        return int(listed or 0)

    def scan_ci(self, env=None):
        return self.run([sys.executable, "tools/secrets/scan.py", "ci"], env=env)

    def scan_staged(self, env=None):
        return self.run([sys.executable, "tools/secrets/scan.py", "staged"], env=env)

    def leftover_scan_temps(self):
        return list(self.tmpdir.glob("polluxkart-secrets-*"))


# --------------------------------------------- Flow 1: the pre-commit scan


class PreCommitScanTest(unittest.TestCase):
    def test_s1_1_clean_commit_is_allowed(self):
        with _Sandbox(with_hooks=True) as box:
            box.write("notes.txt", "ordinary text\n")
            box.git(["add", "notes.txt"])
            result = box.git(["commit", "-q", "-m", "notes"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(box.count_commits(), 2)

    def test_s1_2_staged_secret_is_refused(self):
        with _Sandbox(with_hooks=True) as box:
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            box.git(["add", "config.py"])
            result = box.git(["commit", "-q", "-m", "config"])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(box.count_commits(), 1)
            self.assertIn("config.py", combined)
            self.assertIn("possible secret found", combined)
            self.assertNotIn(value, combined)

    def test_s1_3_unstaged_secret_does_not_block(self):
        with _Sandbox(with_hooks=True) as box:
            box.write("config.py", 'TOKEN = "%s"\n' % fake_secret())
            box.write("notes.txt", "ordinary text\n")
            box.git(["add", "notes.txt"])
            result = box.git(["commit", "-q", "-m", "notes"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_s1_4_ignored_env_file_does_not_block(self):
        with _Sandbox(with_hooks=True) as box:
            box.write(".env", "RAZORPAY_KEY=%s\n" % fake_secret())
            box.write("notes.txt", "ordinary text\n")
            box.git(["add", "notes.txt"])
            result = box.git(["commit", "-q", "-m", "notes"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_s1_5_force_added_env_file_is_refused(self):
        with _Sandbox(with_hooks=True) as box:
            value = fake_secret()
            box.write(".env", "TOKEN=%s\n" % value)
            box.git(["add", "-f", ".env"])
            result = box.git(["commit", "-q", "-m", "env"])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(box.count_commits(), 1)
            self.assertNotIn(value, combined)

    def test_s1_6_both_checks_report(self):
        with _Sandbox(with_hooks=True) as box:
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            readme = box.repo / "docs" / "README.md"
            readme.write_text(readme.read_text() + "\nbad — dash\n")
            box.git(["add", "config.py", "docs/README.md"])
            result = box.git(["commit", "-q", "-m", "both"])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("em dash", combined)
            self.assertIn("possible secret found", combined)
            self.assertNotIn(value, combined)

    def test_s1_7_skip_local_ci_does_not_skip_the_scan(self):
        with _Sandbox(with_hooks=True) as box:
            box.write("config.py", 'TOKEN = "%s"\n' % fake_secret())
            box.git(["add", "config.py"])
            result = box.git(["commit", "-q", "-m", "config"], env={"SKIP_LOCAL_CI": "1"})
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(box.count_commits(), 1)

    def test_s1_8_inline_allow_comment_is_refused(self):
        with _Sandbox(with_hooks=True) as box:
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"  # %s\n' % (value, scan.INLINE_MARKER))
            box.git(["add", "config.py"])
            result = box.git(["commit", "-q", "-m", "config"])
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("config.py:1", combined)
            self.assertIn("inline allow comment", combined)
            self.assertNotIn(value, combined)


# ------------------------------------------------- Flow 2: the make ci scan


class CiScanTest(unittest.TestCase):
    def test_s2_1_clean_branch_passes(self):
        with _Sandbox() as box:
            box.set_origin_development()
            box.write("one.txt", "one\n")
            box.commit("one", ["one.txt"])
            box.write("two.txt", "two\n")
            box.commit("two", ["two.txt"])
            result = box.scan_ci()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("No secrets found", result.stdout)

    def test_s2_2_secret_added_then_deleted_is_still_found(self):
        with _Sandbox() as box:
            box.set_origin_development()
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            box.commit("add", ["config.py"])
            guilty = box.head()
            (box.repo / "config.py").unlink()
            box.commit("remove", ["config.py"])
            result = box.scan_ci()
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1, combined)
            self.assertIn(guilty[:12], combined)
            self.assertNotIn(value, combined)

    def test_s2_3_commits_before_the_branch_are_not_scanned(self):
        with _Sandbox() as box:
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            box.commit("add", ["config.py"])
            (box.repo / "config.py").unlink()
            box.commit("remove", ["config.py"])
            box.set_origin_development()
            box.write("later.txt", "later\n")
            box.commit("later", ["later.txt"])
            result = box.scan_ci()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_s2_4_scan_base_sets_the_range(self):
        with _Sandbox() as box:
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            box.commit("add", ["config.py"])
            (box.repo / "config.py").unlink()
            box.commit("remove", ["config.py"])
            box.set_origin_development()
            base_before_the_secret = box.git(["rev-parse", "HEAD~2"]).stdout.strip()
            box.write("later.txt", "later\n")
            box.commit("later", ["later.txt"])
            with_base = box.scan_ci(env={"SCAN_BASE": base_before_the_secret})
            self.assertEqual(with_base.returncode, 1, with_base.stdout)
            self.assertNotIn(value, with_base.stdout + with_base.stderr)
            without_base = box.scan_ci()
            self.assertEqual(without_base.returncode, 0, without_base.stdout)

    def test_s2_5_push_after_merge_scans_no_commits_but_still_checks_files(self):
        with _Sandbox() as box:
            box.write("one.txt", "one\n")
            box.commit("one", ["one.txt"])
            box.set_origin_development()
            result = box.scan_ci(env={"SCAN_BASE": ""})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("No secrets found", result.stdout)

    def test_s2_6_uncommitted_tracked_file_is_scanned(self):
        with _Sandbox() as box:
            box.write("config.py", "TOKEN = \"\"\n")
            box.commit("add", ["config.py"])
            box.set_origin_development()
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            result = box.scan_ci()
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1, combined)
            self.assertIn("config.py", combined)
            self.assertNotIn(value, combined)

    def test_s2_7_ignored_env_file_is_not_scanned(self):
        with _Sandbox() as box:
            box.set_origin_development()
            box.write(".env", "TOKEN=%s\n" % fake_secret())
            result = box.scan_ci()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_s2_8_missing_base_branch_says_fetch_first(self):
        with _Sandbox() as box:
            box.write("one.txt", "one\n")
            box.commit("one", ["one.txt"])
            result = box.scan_ci()
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("fetch origin first", result.stdout)

    def test_s2_8_on_github_a_run_without_a_base_scans_the_files(self):
        """A release push may arrive without origin/development in the checkout.

        The run must not fail for that: it has no commit range of its own,
        the tracked files are still scanned, and the log says so.
        """
        with _Sandbox() as box:
            box.write("one.txt", "one\n")
            box.commit("one", ["one.txt"])
            clean = box.scan_ci(env={"GITHUB_ACTIONS": "true"})
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            self.assertIn("No commit range", clean.stdout)
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            box.commit("secret", ["config.py"])
            dirty = box.scan_ci(env={"GITHUB_ACTIONS": "true"})
            self.assertEqual(dirty.returncode, 1, dirty.stdout)
            self.assertNotIn(value, dirty.stdout + dirty.stderr)

    def test_s2_6_findings_name_the_file_not_the_temporary_copy(self):
        with _Sandbox() as box:
            box.set_origin_development()
            box.write("app/config.py", 'TOKEN = "%s"\n' % fake_secret())
            box.commit("secret", ["app/config.py"])
            result = box.scan_ci()
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("app/config.py:1", result.stdout)
            self.assertNotIn("polluxkart-secrets-", result.stdout)

    def test_s2_9_temporary_folder_is_removed_either_way(self):
        with _Sandbox() as box:
            box.set_origin_development()
            box.write("clean.txt", "clean\n")
            box.commit("clean", ["clean.txt"])
            passing = box.scan_ci()
            self.assertEqual(passing.returncode, 0, passing.stdout)
            self.assertEqual(box.leftover_scan_temps(), [])
            box.write("config.py", 'TOKEN = "%s"\n' % fake_secret())
            box.commit("secret", ["config.py"])
            failing = box.scan_ci()
            self.assertEqual(failing.returncode, 1, failing.stdout)
            self.assertEqual(box.leftover_scan_temps(), [])

    def test_s2_10_make_ci_runs_this_scan(self):
        """The `secrets` check in make ci runs exactly this command.

        The whole of make ci is not run here because it takes minutes; the
        pull request records a real run. This asserts the check is wired in,
        and runs the very argv make ci builds against a planted secret.
        """
        checks = _load("checks_module", CHECKS_DIR / "checks.py")
        entry = [item for item in checks.CHECKS if item[0] == "secrets"]
        self.assertEqual(len(entry), 1, "make ci has no secrets check")
        name, group, command, needs = entry[0]
        self.assertEqual(group, "tooling")
        self.assertEqual(set(needs), {"git", "gitleaks"})
        argv = checks._python_command(entry[0], sys.executable)
        with _Sandbox() as box:
            box.set_origin_development()
            value = fake_secret()
            box.write("config.py", 'TOKEN = "%s"\n' % value)
            box.commit("secret", ["config.py"])
            result = box.run(argv)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn(value, result.stdout + result.stderr)


# --------------------------------------------------------- Flow 3: allow list


class AllowListTest(unittest.TestCase):
    def _entry(self, body: str) -> str:
        return "[extend]\nuseDefault = true\n\n[[allowlists]]\n%s\n" % body

    def test_a3_1_the_real_config_passes(self):
        text = (ROOT / ".gitleaks.toml").read_text()
        self.assertEqual(scan.check_allowlist(text), [])

    def test_a3_2_dated_reason_passes(self):
        text = self._entry('description = "2026-09-20: example key in a test"')
        self.assertEqual(scan.check_allowlist(text), [])

    def test_a3_3_no_description_fails(self):
        text = self._entry("paths = ['''^fixtures/example\\.py$''']")
        problems = scan.check_allowlist(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("no description", problems[0])

    def test_a3_4_description_without_a_date_fails(self):
        text = self._entry('description = "example key"')
        problems = scan.check_allowlist(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("does not start with a date", problems[0])

    def test_a3_5_impossible_date_fails(self):
        text = self._entry('description = "2026-02-30: reason"')
        problems = scan.check_allowlist(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("not a real date", problems[0])

    def test_a3_6_date_without_a_reason_fails(self):
        text = self._entry('description = "2026-09-20:"')
        problems = scan.check_allowlist(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("no reason", problems[0])

    def test_a3_7_narrowing_by_commit_fails(self):
        text = self._entry(
            'description = "2026-09-20: a reason"\ncommits = ["0123456789abcdef0123456789abcdef01234567"]'
        )
        problems = scan.check_allowlist(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("squash merge", problems[0])

    def test_a3_8_allow_listed_path_is_skipped_by_gitleaks(self):
        with _Sandbox() as box:
            value = fake_secret()
            box.set_origin_development()
            box.write("fixtures/example.py", 'TOKEN = "%s"\n' % value)
            box.commit("fixture", ["fixtures/example.py"])
            before = box.scan_ci()
            self.assertEqual(before.returncode, 1, before.stdout)
            box.write(
                ".gitleaks.toml",
                "[extend]\nuseDefault = true\n\n[[allowlists]]\n"
                'description = "2026-09-20: example key in a test"\n'
                "paths = ['''fixtures/example\\.py''']\n",
            )
            after = box.scan_ci()
            self.assertEqual(after.returncode, 0, after.stdout + after.stderr)

    def test_a3_9_inline_marker_in_code_fails(self):
        with _Sandbox() as box:
            box.write("config.py", "value = 1  # %s\n" % scan.INLINE_MARKER)
            box.commit("code", ["config.py"])
            problems = scan.find_inline_allows(str(box.repo), ["config.py"])
            self.assertEqual(len(problems), 1)
            self.assertIn("config.py:1", problems[0])

    def test_a3_10_marker_inside_backticks_in_markdown_passes(self):
        with _Sandbox() as box:
            box.write("notes.md", "An inline `%s` comment is refused.\n" % scan.INLINE_MARKER)
            self.assertEqual(scan.find_inline_allows(str(box.repo), ["notes.md"]), [])

    def test_a3_11_marker_outside_backticks_in_markdown_fails(self):
        with _Sandbox() as box:
            box.write("notes.md", "Use %s to silence it.\n" % scan.INLINE_MARKER)
            problems = scan.find_inline_allows(str(box.repo), ["notes.md"])
            self.assertEqual(len(problems), 1)
            self.assertIn("notes.md:1", problems[0])


# ------------------------------------------- Flow 4: doctor, pins, settings


class ToolingTest(unittest.TestCase):
    def setUp(self):
        if str(CHECKS_DIR) not in sys.path:
            sys.path.insert(0, str(CHECKS_DIR))
        self.doctor = _load("doctor_module", CHECKS_DIR / "doctor.py")
        self.linters = _load("linters_module", CHECKS_DIR / "linters.py")
        self.tool = [item for item in self.doctor.TOOLS if item["name"] == "gitleaks"][0]

    def test_d4_1_missing_gitleaks_is_reported(self):
        finding = self.doctor.probe(self.tool, run=None, which=lambda name: None, environ={})
        self.assertEqual(finding["status"], "missing")
        self.assertTrue(finding["needed"])
        self.assertIn("brew install gitleaks", finding["hint"])
        report, problems = self.doctor.format_report([finding])
        self.assertIn("gitleaks", problems)
        self.assertIn("brew install gitleaks", report)

    def test_d4_2_old_gitleaks_is_reported_then_the_pin_is_ok(self):
        pinned = self._pin()["version"]

        def runner(version):
            def run(argv, **kwargs):
                return subprocess.CompletedProcess(argv, 0, stdout=version + "\n", stderr="")
            return run

        old = self.doctor.probe(
            self.tool, run=runner("8.0.0"), which=lambda name: "/usr/bin/gitleaks", environ={}
        )
        self.assertEqual(old["status"], "too old")
        current = self.doctor.probe(
            self.tool, run=runner(pinned), which=lambda name: "/usr/bin/gitleaks", environ={}
        )
        self.assertEqual(current["status"], "ok")

    def _pin(self):
        found = [item for item in self.linters.LINTERS if item["name"] == "gitleaks"]
        self.assertEqual(len(found), 1, "gitleaks is not pinned")
        return found[0]

    def test_d4_3_the_pin_is_complete(self):
        pin = self._pin()
        self.assertTrue(pin["version"])
        self.assertTrue(pin["url"].startswith("https://github.com/gitleaks/gitleaks/releases/download/"))
        self.assertIn(pin["version"], pin["url"])
        self.assertEqual(len(pin["sha256"]), 64)
        self.assertEqual(self.tool["minimum"], pin["version"])

    def test_d4_4_repository_settings_require_secret_scanning(self):
        rulesets = _load("rulesets_module", ROOT / "tools" / "rulesets" / "rulesets.py")
        settings = json.loads((ROOT / ".github" / "rulesets" / "repository.json").read_text())
        for key in rulesets.SECURITY_KEYS:
            self.assertIs(settings.get(key), True, "%s must be on" % key)
        files = rulesets.load_files()
        self.assertEqual(rulesets.validate(files), [])
        weakened = json.loads(json.dumps(files))
        weakened["repository"]["secret_scanning_push_protection"] = False
        self.assertTrue(
            any("push protection" in problem for problem in rulesets.validate(weakened))
        )

    def test_d4_4_settings_are_sent_to_github_nested(self):
        rulesets = _load("rulesets_module", ROOT / "tools" / "rulesets" / "rulesets.py")
        body = rulesets.repository_payload(
            {"allow_rebase_merge": False, "secret_scanning": True, "secret_scanning_validity_checks": False}
        )
        self.assertEqual(body["allow_rebase_merge"], False)
        self.assertEqual(body["security_and_analysis"]["secret_scanning"], {"status": "enabled"})
        self.assertEqual(
            body["security_and_analysis"]["secret_scanning_validity_checks"], {"status": "disabled"}
        )
        self.assertNotIn("secret_scanning", body)

    def test_d4_5_env_files_are_ignored_but_the_example_is_not(self):
        for name in (".env", ".env.local"):
            result = subprocess.run(
                ["git", "check-ignore", "-q", name], cwd=str(ROOT), capture_output=True
            )
            self.assertEqual(result.returncode, 0, "%s should be ignored" % name)
        allowed = subprocess.run(
            ["git", "check-ignore", "-q", ".env.example"], cwd=str(ROOT), capture_output=True
        )
        self.assertEqual(allowed.returncode, 1, ".env.example should not be ignored")

    def test_d4_6_codeowners_covers_the_scanner(self):
        text = (ROOT / ".github" / "CODEOWNERS").read_text()
        self.assertIn("/.gitleaks.toml", text)
        self.assertIn("/tools/secrets/", text)


if __name__ == "__main__":
    unittest.main()
