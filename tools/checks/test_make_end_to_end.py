"""End-to-end: the real make command on throwaway copies of this checkout.

The copy leaves this file out so make ci does not recurse.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).name

CHECK_ORDER = [
    "docslint-tests",
    "docslint",
    "approval-gate-tests",
    "agent-hook-tests",
    "board-tests",
    "githooks-tests",
    "rulesets-tests",
    "checks-tests",
    "actionlint",
]
DOCS_CHECKS = CHECK_ORDER[:2]
TOOLING_CHECKS = CHECK_ORDER[2:]


def _copy_repo(dest: Path) -> None:
    listed = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=str(ROOT),
        text=True,
    ).splitlines()
    for rel in listed:
        if os.path.basename(rel) == SELF:
            continue
        src = ROOT / rel
        if not src.is_file():
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    subprocess.check_call(["git", "init", "-q"], cwd=str(dest))


def _run_make(dest: Path, *args: str, env=None, timeout=180):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        ["make", *args],
        cwd=str(dest),
        env=merged,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _summary_names(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("passed") or stripped.startswith("failed") or stripped.startswith("not run"):
            parts = stripped.split()
            if len(parts) >= 2:
                names.append(parts[1])
    return names


def _failed_names(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("failed"):
            parts = stripped.split()
            if len(parts) >= 2:
                names.append(parts[1])
    return names


class MakeEndToEndTest(unittest.TestCase):
    def test_e1_1_clean_copy_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertEqual(_summary_names(combined), CHECK_ORDER)
            self.assertRegex(combined, r"\d+\.\d+s")

    def test_e1_2_broken_docs_link_then_fix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            readme = dest / "docs" / "README.md"
            readme.write_text(readme.read_text() + "\n[missing](this-file-does-not-exist.md)\n")
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(_failed_names(combined), ["docslint"])
            readme.write_text(readme.read_text().replace("\n[missing](this-file-does-not-exist.md)\n", "\n"))
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)

    def test_e1_3_failing_docslint_test(self) -> None:
        self._assert_only_one_failure("tools/docslint/test_deliberate_fail.py", "docslint-tests")

    def test_e1_4_failing_approval_gate_test(self) -> None:
        self._assert_only_one_failure("tools/approval_gate/test_deliberate_fail.py", "approval-gate-tests")

    def test_e1_5_failing_hook_test(self) -> None:
        self._assert_only_one_failure(".claude/hooks/test_deliberate_fail.py", "agent-hook-tests")

    def test_e1_6_failing_checks_test(self) -> None:
        self._assert_only_one_failure("tools/checks/test_deliberate_fail.py", "checks-tests")

    def test_e1_7_unknown_github_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            (dest / ".github" / "workflows" / "broken.yml").write_text(
                "name: broken\n"
                "on: push\n"
                "jobs:\n"
                "  x:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo ${{ github.no_such_field }}\n"
            )
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(_failed_names(combined), ["actionlint"])
            self.assertIn("broken.yml", combined)

    def test_e1_8_unquoted_shell_variable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            (dest / ".github" / "workflows" / "shell.yml").write_text(
                "name: shell\n"
                "on: push\n"
                "jobs:\n"
                "  x:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo $UNQUOTED\n"
            )
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(_failed_names(combined), ["actionlint"])
            self.assertRegex(combined, r"SC[0-9]+")

    def test_e1_9_two_failures_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            readme = dest / "docs" / "README.md"
            readme.write_text(readme.read_text() + "\n[missing](this-file-does-not-exist.md)\n")
            (dest / ".github" / "workflows" / "broken.yml").write_text(
                "name: broken\n"
                "on: push\n"
                "jobs:\n"
                "  x:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo ${{ github.no_such_field }}\n"
            )
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(_failed_names(combined), ["docslint", "actionlint"])
            self.assertIn("2 of 9 checks failed: docslint, actionlint", combined)

    def test_e1_10_actionlint_missing_from_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            for name, src in (
                ("python3", sys.executable),
                ("make", shutil.which("make")),
                ("git", shutil.which("git")),
            ):
                os.symlink(src, bindir / name)
            path = str(bindir) + os.pathsep + "/usr/bin" + os.pathsep + "/bin"
            which_actionlint = subprocess.run(
                ["which", "actionlint"],
                env={**os.environ, "PATH": path},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(which_actionlint.returncode, 0, "actionlint was still findable; PATH isolation failed")
            result = _run_make(dest, "ci", env={"PATH": path})
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            failed = _failed_names(combined)
            self.assertIn("actionlint", failed)
            self.assertIn("checks-tests", failed)
            self.assertIn("not installed; run make doctor", combined)
            for name in ("docslint-tests", "docslint", "approval-gate-tests", "agent-hook-tests", "board-tests", "githooks-tests", "rulesets-tests"):
                self.assertIn(name, _summary_names(combined))

    def test_e2_1_ci_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            result = _run_make(dest, "ci-docs")
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertEqual(_summary_names(combined), DOCS_CHECKS)

    def test_e2_2_ci_tooling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            result = _run_make(dest, "ci-tooling")
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertEqual(_summary_names(combined), TOOLING_CHECKS)

    def test_e2_3_ci_docs_ignores_broken_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            (dest / ".github" / "workflows" / "broken.yml").write_text(
                "name: broken\n"
                "on: push\n"
                "jobs:\n"
                "  x:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo ${{ github.no_such_field }}\n"
            )
            result = _run_make(dest, "ci-docs")
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)

    def test_d3_1_doctor_with_fake_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            self._write_fake_tools(bindir, include_later=False)
            path = str(bindir)
            result = _run_make(dest, "doctor", env={"PATH": path})
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertIn("ok", combined)
            self.assertIn("not installed", combined)
            self.assertIn("All tools needed today are ready", combined)

    def test_d3_2_doctor_missing_actionlint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            self._write_fake_tools(bindir, include_later=False, skip=("actionlint",))
            path = str(bindir)
            result = _run_make(dest, "doctor", env={"PATH": path})
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn("missing", combined)
            self.assertIn("actionlint", combined)
            self.assertIn("brew install actionlint", combined)

    def test_e5_1_make_help(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            result = _run_make(dest)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined)
            self.assertIn("make doctor", combined)
            self.assertIn("make ci", combined)
            self.assertIn("make ci-docs", combined)
            self.assertIn("make ci-tooling", combined)
            self.assertNotIn("make ci summary", combined)

    def _assert_only_one_failure(self, relpath: str, expected: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "repo"
            dest.mkdir()
            _copy_repo(dest)
            path = dest / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "import unittest\n"
                "class DeliberateFail(unittest.TestCase):\n"
                "    def test_fail(self):\n"
                "        self.fail('deliberate')\n"
            )
            result = _run_make(dest, "ci")
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertEqual(_failed_names(combined), [expected])

    def _write_fake_tools(self, bindir: Path, include_later: bool, skip=()) -> None:
        scripts = {
            "python3": "#!/bin/sh\nexec %s \"$@\"\n" % sys.executable,
            "make": None,
            "git": "#!/bin/sh\n"
            "if [ \"$1\" = config ] && [ \"$2\" = --get ] && [ \"$3\" = core.hooksPath ]; then echo .githooks; exit 0; fi\n"
            "echo 'git version 2.52.0'\n",
            "gh": "#!/bin/sh\necho 'gh version 2.96.0'\n",
            "actionlint": "#!/bin/sh\necho '1.7.12'\n",
            "shellcheck": "#!/bin/sh\necho 'version: 0.11.0'\n",
        }
        real_make = shutil.which("make")
        for name, body in scripts.items():
            if name in skip:
                continue
            target = bindir / name
            if name == "make":
                os.symlink(real_make, target)
                continue
            if name == "python3":
                os.symlink(sys.executable, target)
                continue
            target.write_text(body)
            target.chmod(target.stat().st_mode | stat.S_IEXEC)
        if include_later:
            (bindir / "java").write_text("#!/bin/sh\necho openjdk version 25.0.1\n")
            (bindir / "java").chmod((bindir / "java").stat().st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    unittest.main()
