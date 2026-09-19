"""Tests for the pre-commit hook: it checks staged docs only."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _without_git_vars(env: dict) -> dict:
    cleaned = dict(env)
    for key in list(cleaned):
        if key.startswith("GIT_"):
            del cleaned[key]
    return cleaned


class PreCommitTest(unittest.TestCase):
    def test_c2_1_clean_commit(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            readme.write_text(readme.read_text().rstrip() + "\n\n")
            result = box.commit_file("docs/README.md")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(box.has_commit())

    def test_c2_2_em_dash_refused(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            readme.write_text(readme.read_text() + "\nbad — dash\n")
            result = box.commit_file("docs/README.md")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(box.has_commit())

    def test_c2_3_broken_link_refused(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            readme.write_text(
                readme.read_text().rstrip() + "\n\n## See also\n\n- [missing](nowhere.md)\n"
            )
            result = box.commit_file("docs/README.md")
            self.assertNotEqual(result.returncode, 0)
            combined = result.stderr + result.stdout
            self.assertIn("broken link", combined)
            self.assertFalse(box.has_commit())

    def test_c2_7_skip_does_not_bypass_commit(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            readme.write_text(readme.read_text() + "\nbad — dash\n")
            result = box.commit_file("docs/README.md", env={"SKIP_LOCAL_CI": "1"})
            self.assertNotEqual(result.returncode, 0)

    def test_c2_4_unstaged_em_dash_does_not_block(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            readme.write_text(readme.read_text().rstrip() + "\n\n")
            box.run(["git", "add", "docs/README.md"])
            other = box.docs / "platform" / "testing.md"
            other.write_text(other.read_text() + "\nbad — dash\n")
            result = box.commit_staged()
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_c2_5_unstaged_fix_does_not_hide_staged_em_dash(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            original = readme.read_text()
            readme.write_text(original + "\nbad — dash\n")
            box.run(["git", "add", "docs/README.md"])
            readme.write_text(original.rstrip() + "\n\n")
            result = box.commit_staged()
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(box.has_commit())

    def test_c2_6_no_temp_folder_left(self) -> None:
        with _DocSandbox() as box:
            readme = box.docs / "README.md"
            original = readme.read_text()
            readme.write_text(original.rstrip() + "\n\n")
            passed = box.commit_file("docs/README.md")
            self.assertEqual(passed.returncode, 0, passed.stderr + passed.stdout)
            self.assertEqual(box.leftover_hook_temps(), [])
            readme.write_text(readme.read_text() + "\nbad — dash\n")
            failed = box.commit_file("docs/README.md")
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(box.leftover_hook_temps(), [])

    def test_f4_2_wrapper_from_subdir(self) -> None:
        with _DocSandbox() as box:
            nested = box.repo / "docs" / "platform"
            result = subprocess.run(
                [str(box.repo / ".githooks" / "pre-commit")],
                cwd=str(nested),
                env=box._env(),
                capture_output=True,
                text=True,
            )
            combined = result.stdout + result.stderr
            self.assertIn("docslint:", combined)
            self.assertEqual(result.returncode, 0, combined)


class _DocSandbox:
    def __init__(self):
        self.temp = None
        self.repo = None
        self.docs = None
        self.tmpdir = None

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.tmpdir = base / "tmp"
        self.repo.mkdir()
        self.tmpdir.mkdir()
        host = _without_git_vars(os.environ)
        subprocess.check_call(["git", "init", "-q", "-b", "feature/a"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "config", "user.name", "test"], cwd=self.repo, env=host)
        subprocess.check_call(["git", "config", "core.hooksPath", ".githooks"], cwd=self.repo, env=host)
        for rel in (
            ".githooks/pre-commit",
            ".githooks/pre-push",
            "tools/githooks/pre_commit.py",
            "tools/githooks/pre_push.py",
        ):
            src = ROOT / rel
            dest = self.repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        listed = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=str(ROOT),
            env=host,
            text=True,
        ).splitlines()
        for rel in listed:
            if rel.startswith("tools/docslint/") and (ROOT / rel).is_file():
                dest = self.repo / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, dest)
        self.docs = self.repo / "docs"
        (self.docs / "platform").mkdir(parents=True)
        (self.docs / "README.md").write_text(
            "# Docs\n\n## Read next\n\n- [testing](platform/testing.md)\n"
        )
        (self.docs / "platform" / "testing.md").write_text("# Testing\n")
        for name in ("pre-commit", "pre-push"):
            path = self.repo / ".githooks" / name
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        self.run(["git", "add", "."])
        self.run(["git", "commit", "-q", "-m", "base", "--no-verify"])
        return self

    def __exit__(self, *exc):
        self.temp.cleanup()

    def _env(self, extra=None):
        merged = _without_git_vars(os.environ)
        merged.pop("SKIP_LOCAL_CI", None)
        merged["TMPDIR"] = str(self.tmpdir)
        if extra:
            merged.update(extra)
            merged["TMPDIR"] = str(self.tmpdir)
        return merged

    def run(self, argv, env=None):
        return subprocess.run(
            argv,
            cwd=str(self.repo),
            env=self._env(env),
            capture_output=True,
            text=True,
        )

    def leftover_hook_temps(self):
        return list(self.tmpdir.glob("polluxkart-pre-commit-*"))

    def commit_file(self, relpath: str, extra="", env=None):
        self.run(["git", "add", relpath])
        return self.commit_staged(env=env)

    def commit_staged(self, env=None):
        return self.run(["git", "commit", "-q", "-m", "change"], env=env)

    def has_commit(self) -> bool:
        log = self.run(["git", "log", "--oneline"])
        return log.stdout.count("\n") >= 2


if __name__ == "__main__":
    unittest.main()
