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

    def test_f4_2_wrapper_from_subdir(self) -> None:
        with _DocSandbox() as box:
            nested = box.repo / "docs" / "platform"
            result = subprocess.run(
                [str(box.repo / ".githooks" / "pre-commit")],
                cwd=str(nested),
                capture_output=True,
                text=True,
            )
            self.assertIn(result.returncode, (0, 1))


class _DocSandbox:
    def __init__(self):
        self.temp = None
        self.repo = None
        self.docs = None

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        subprocess.check_call(["git", "init", "-q", "-b", "feature/a"], cwd=self.repo)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=self.repo)
        subprocess.check_call(["git", "config", "user.name", "test"], cwd=self.repo)
        subprocess.check_call(["git", "config", "core.hooksPath", ".githooks"], cwd=self.repo)
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

    def run(self, argv, env=None):
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(argv, cwd=str(self.repo), env=merged, capture_output=True, text=True)

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
