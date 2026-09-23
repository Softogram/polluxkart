"""Unit tests for make doctor. No real programs are started."""

from __future__ import annotations

import io
import os
import subprocess
import sys
import unittest
from types import SimpleNamespace

import doctor
from linters import LINTERS


NEEDED = ("python3", "make", "git", "gh", "actionlint", "shellcheck", "gitleaks")


def _basename(argv0: str) -> str:
    base = os.path.basename(argv0)
    if argv0 == sys.executable or base.startswith("python"):
        return "python3"
    return base


class RecordingRun:
    def __init__(self, versions=None, info_code=0, timeouts=None, text=None, hooks_path=".githooks"):
        self.versions = dict(versions or {})
        self.info_code = info_code
        self.timeouts = set(timeouts or [])
        self.text = dict(text or {})
        self.hooks_path = hooks_path
        self.calls = []

    def __call__(self, argv, capture_output=False, text=False, timeout=None):
        self.calls.append((list(argv), timeout))
        name = _basename(argv[0])
        if name in self.timeouts:
            raise subprocess.TimeoutExpired(argv, timeout)
        if argv[:3] == ["git", "config", "--get"] and argv[3:] == ["core.hooksPath"]:
            if self.hooks_path is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout=self.hooks_path + "\n", stderr="")
        if len(argv) >= 2 and argv[1] == "info":
            return SimpleNamespace(returncode=self.info_code, stdout="", stderr="Cannot connect")
        body = self.text.get(name, self.versions.get(name, "1.0.0"))
        if not body.endswith("\n"):
            body = body + "\n"
        return SimpleNamespace(returncode=0, stdout=body, stderr="")


class FakeWhich:
    def __init__(self, present):
        self.present = set(present)

    def __call__(self, name):
        key = _basename(name)
        if key in self.present:
            return "/bin/%s" % key
        return None


def _ok_versions():
    return {
        "python3": "Python 3.14.0",
        "make": "GNU Make 3.81",
        "git": "git version 2.52.0",
        "gh": "gh version 2.96.0",
        "actionlint": "1.7.12",
        "shellcheck": "version: 0.11.0",
        "gitleaks": "8.30.1",
    }


def _run_main(which, run, version_info=None, environ=None):
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = buf_out, buf_err
    try:
        code = doctor.main(version_info=version_info, run=run, which=which, environ=environ)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, buf_out.getvalue(), buf_err.getvalue()


class DoctorUnitTest(unittest.TestCase):
    def test_d3_3_two_missing_named_in_last_line(self) -> None:
        which = FakeWhich({"python3", "make", "git", "shellcheck"})
        run = RecordingRun(_ok_versions())
        code, out, _err = _run_main(which, run)
        self.assertEqual(code, 1)
        self.assertIn("actionlint", out)
        self.assertIn("gh", out)
        last = [line for line in out.splitlines() if line][-1]
        self.assertIn("actionlint", last)
        self.assertIn("gh", last)

    def test_d3_4_actionlint_version_boundary(self) -> None:
        which = FakeWhich(NEEDED)
        versions = _ok_versions()
        versions["actionlint"] = "1.7.11"
        code, out, _err = _run_main(which, RecordingRun(versions))
        self.assertEqual(code, 1)
        self.assertIn("too old", out)
        versions["actionlint"] = "1.7.12"
        code, out, _err = _run_main(which, RecordingRun(versions))
        self.assertEqual(code, 0)
        self.assertIn("All tools needed today are ready", out)

    def test_d3_5_make_version_boundary(self) -> None:
        which = FakeWhich(NEEDED)
        versions = _ok_versions()
        versions["make"] = "GNU Make 3.80"
        code, out, _err = _run_main(which, RecordingRun(versions))
        self.assertEqual(code, 1)
        self.assertIn("too old", out)
        versions["make"] = "GNU Make 3.81"
        code, _out, _err = _run_main(which, RecordingRun(versions))
        self.assertEqual(code, 0)

    def test_d3_6_old_python_exits_1(self) -> None:
        which = FakeWhich(NEEDED)
        run = RecordingRun(_ok_versions())
        code, _out, err = _run_main(which, run, version_info=(3, 9, 6))
        self.assertEqual(code, 1)
        self.assertIn("3.10", err)
        self.assertIn("3.9.6", err)
        code, _out, err = _run_main(which, run, version_info=(3, 10, 0))
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

    def test_d3_7_later_tools_found(self) -> None:
        which = FakeWhich(list(NEEDED) + ["java", "node", "pnpm", "docker"])
        versions = _ok_versions()
        versions.update({
            "java": "openjdk version 25.0.1",
            "node": "v24.12.0",
            "pnpm": "10.34.3",
            "docker": "Docker version 29.0.2",
        })
        code, out, _err = _run_main(which, RecordingRun(versions, info_code=0))
        self.assertEqual(code, 0)
        self.assertIn("java", out)
        self.assertIn("25", out)
        self.assertIn("node", out)
        self.assertIn("24", out)
        self.assertIn("pnpm", out)
        self.assertIn("docker", out)

    def test_d3_8_docker_installed_not_running(self) -> None:
        which = FakeWhich(list(NEEDED) + ["docker"])
        versions = _ok_versions()
        versions["docker"] = "Docker version 29.0.2"
        code, out, _err = _run_main(which, RecordingRun(versions, info_code=1))
        self.assertEqual(code, 0)
        self.assertIn("installed, not running", out)

    def test_d3_9_java_21_is_information(self) -> None:
        which = FakeWhich(list(NEEDED) + ["java"])
        versions = _ok_versions()
        versions["java"] = "openjdk version 21.0.1"
        code, out, _err = _run_main(which, RecordingRun(versions))
        self.assertEqual(code, 0)
        self.assertIn("21", out)
        self.assertIn("#55", out)

    def test_d3_10_timeout(self) -> None:
        which = FakeWhich(NEEDED)
        run = RecordingRun(_ok_versions(), timeouts={"gh"})
        code, out, _err = _run_main(which, run)
        self.assertEqual(code, 1)
        self.assertIn("no answer", out)
        which_later = FakeWhich(list(NEEDED) + ["java"])
        run_java = RecordingRun(_ok_versions(), timeouts={"java"})
        run_java.versions["java"] = "25.0.1"
        code, out, _err = _run_main(which_later, run_java)
        self.assertEqual(code, 0)
        self.assertIn("no answer", out)

    def test_d3_11_timeout_limit_is_ten_seconds(self) -> None:
        which = FakeWhich(NEEDED)
        run = RecordingRun(_ok_versions())
        _run_main(which, run)
        self.assertTrue(run.calls)
        self.assertTrue(all(timeout == 10 for _argv, timeout in run.calls))

    def test_d3_12_unreadable_versus_unknown(self) -> None:
        which = FakeWhich(NEEDED)
        versions = _ok_versions()
        versions["actionlint"] = "hello"
        code, out, _err = _run_main(which, RecordingRun(versions, text={"actionlint": "hello"}))
        self.assertEqual(code, 1)
        self.assertIn("version unreadable", out)
        versions = _ok_versions()
        versions["gh"] = "hello"
        code, out, _err = _run_main(which, RecordingRun(versions, text={"gh": "hello"}))
        self.assertEqual(code, 0)
        self.assertIn("version unknown", out)

    def test_d3_13_doctor_minimum_matches_pin(self) -> None:
        for item in LINTERS:
            tool = [t for t in doctor.TOOLS if t["name"] == item["name"]][0]
            self.assertEqual(tool["minimum"], item["version"])

    def test_hooks_enabled(self) -> None:
        which = FakeWhich(NEEDED)
        code, out, _err = _run_main(which, RecordingRun(_ok_versions(), hooks_path=".githooks"))
        self.assertEqual(code, 0)
        self.assertIn("git hooks", out)
        self.assertIn("ok", out)

    def test_hooks_not_enabled(self) -> None:
        which = FakeWhich(NEEDED)
        code, out, _err = _run_main(which, RecordingRun(_ok_versions(), hooks_path=None))
        self.assertEqual(code, 1)
        self.assertIn("not enabled", out)
        self.assertIn("git config core.hooksPath .githooks", out)

    def test_hooks_point_elsewhere(self) -> None:
        which = FakeWhich(NEEDED)
        code, out, _err = _run_main(which, RecordingRun(_ok_versions(), hooks_path="/somewhere/else"))
        self.assertEqual(code, 1)
        self.assertIn("points elsewhere", out)
        self.assertIn("/somewhere/else", out)

    def test_hooks_missing_on_github_is_information(self) -> None:
        which = FakeWhich(NEEDED)
        code, out, _err = _run_main(
            which,
            RecordingRun(_ok_versions(), hooks_path=None),
            environ={"GITHUB_ACTIONS": "true"},
        )
        self.assertEqual(code, 0)
        self.assertIn("not enabled", out)
        self.assertIn("All tools needed today are ready", out)


if __name__ == "__main__":
    unittest.main()
