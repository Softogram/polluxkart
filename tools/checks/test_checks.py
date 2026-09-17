"""Unit tests for the make ci runner. No real programs are started."""

from __future__ import annotations

import ast
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import checks


ROOT = Path(__file__).resolve().parents[2]


class FakeRun:
    def __init__(self, codes=None):
        self.codes = list(codes or [])
        self.calls = []

    def __call__(self, argv, cwd=None):
        self.calls.append((list(argv), cwd))
        code = self.codes.pop(0) if self.codes else 0
        if code == "interrupt":
            raise KeyboardInterrupt()
        return SimpleNamespace(returncode=code)


class ChecksUnitTest(unittest.TestCase):
    def test_u1_1_all_succeed(self) -> None:
        selected = checks.CHECKS[:4]
        runner = FakeRun([0, 0, 0, 0])
        results, interrupted = checks.run_checks(
            selected, str(ROOT), run=runner, which=lambda n: "/bin/" + n, clock=lambda: 0.0, python="/py"
        )
        self.assertFalse(interrupted)
        self.assertTrue(all(r["status"] == "passed" for r in results))
        self.assertEqual(len(runner.calls), 4)

    def test_u1_2_continues_after_failure(self) -> None:
        selected = checks.CHECKS[:4]
        runner = FakeRun([0, 1, 0, 0])
        results, _ = checks.run_checks(
            selected, str(ROOT), run=runner, which=lambda n: "/bin/" + n, clock=lambda: 0.0, python="/py"
        )
        self.assertEqual(len(runner.calls), 4)
        self.assertEqual(results[1]["status"], "failed")
        self.assertEqual(results[2]["status"], "passed")

    def test_u1_3_missing_program_skips_command(self) -> None:
        selected = [c for c in checks.CHECKS if c[0] == "actionlint"]
        runner = FakeRun()
        results, _ = checks.run_checks(
            selected, str(ROOT), run=runner, which=lambda n: None, clock=lambda: 0.0, python="/py"
        )
        self.assertEqual(runner.calls, [])
        self.assertEqual(results[0]["status"], "failed")
        self.assertIn("not installed; run make doctor", results[0]["detail"])

    def test_u1_4_exit_code_in_detail(self) -> None:
        selected = checks.CHECKS[:1]
        runner = FakeRun([3])
        results, _ = checks.run_checks(
            selected, str(ROOT), run=runner, which=lambda n: "/bin/x", clock=lambda: 0.0, python="/py"
        )
        self.assertEqual(results[0]["detail"], "exit code 3")

    def test_u1_5_ctrl_c_marks_later_not_run(self) -> None:
        selected = checks.CHECKS[:4]
        runner = FakeRun([0, "interrupt", 0, 0])
        results, interrupted = checks.run_checks(
            selected, str(ROOT), run=runner, which=lambda n: "/bin/x", clock=lambda: 0.0, python="/py"
        )
        self.assertTrue(interrupted)
        self.assertEqual(results[1]["status"], "failed")
        self.assertEqual(results[2]["status"], "not run")
        self.assertEqual(results[3]["status"], "not run")
        summary = checks.format_summary(results)
        self.assertIn("not run", summary)

    def test_u1_6_commands_run_from_repo_root(self) -> None:
        selected = checks.CHECKS[:1]
        runner = FakeRun([0])
        checks.run_checks(selected, "/repo", run=runner, which=lambda n: "/bin/x", clock=lambda: 0.0, python="/py")
        self.assertEqual(runner.calls[0][1], "/repo")

    def test_u1_7_python_checks_use_sys_executable(self) -> None:
        selected = checks.CHECKS[:1]
        runner = FakeRun([0])
        checks.run_checks(selected, "/repo", run=runner, which=lambda n: "/bin/x", clock=lambda: 0.0, python="/custom/python")
        self.assertEqual(runner.calls[0][0][0], "/custom/python")

    def test_u1_8_old_python_exits_1(self) -> None:
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            code = checks.main([], version_info=(3, 9, 6))
        finally:
            sys.stderr = old
        self.assertEqual(code, 1)
        self.assertIn("3.10", buf.getvalue())
        self.assertIn("3.9.6", buf.getvalue())
        buf = io.StringIO()
        sys.stderr = buf
        try:
            code = checks.main(["--group", "nope"], version_info=(3, 10, 0))
        finally:
            sys.stderr = old
        self.assertEqual(code, 2)

    def test_u1_9_summary_lists_failures_in_order(self) -> None:
        text = checks.format_summary([
            {"name": "a", "status": "passed", "detail": "", "seconds": 0.1},
            {"name": "b", "status": "failed", "detail": "exit code 1", "seconds": 0.2},
            {"name": "c", "status": "failed", "detail": "exit code 1", "seconds": 0.3},
        ])
        self.assertIn("2 of 3 checks failed: b, c", text)

    def test_u1_10_parses_as_python_37(self) -> None:
        for name in ("checks.py", "doctor.py"):
            source = (ROOT / "tools" / "checks" / name).read_text()
            ast.parse(source, filename=name, feature_version=(3, 7))

    def test_u2_1_unknown_group(self) -> None:
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            code = checks.main(["--group", "nope"])
        finally:
            sys.stderr = old
        self.assertEqual(code, 2)
        self.assertIn("docs", buf.getvalue())
        self.assertIn("tooling", buf.getvalue())

    def test_select_checks_docs(self) -> None:
        names = [c[0] for c in checks.select_checks(checks.CHECKS, "docs")]
        self.assertEqual(names, ["docslint-tests", "docslint"])


if __name__ == "__main__":
    unittest.main()
