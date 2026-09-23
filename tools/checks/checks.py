#!/usr/bin/env python3
"""Run every check a pull request must pass.

Python 3.7 can parse this file so an older interpreter prints a version
message instead of a syntax error. Runtime still needs 3.10 or newer.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

MIN_PYTHON = (3, 10)

# name, group, command (without the python executable), needs
CHECKS = (
    ("docslint-tests", "docs", ["-m", "unittest", "discover", "-s", "tools/docslint"], ()),
    ("docslint", "docs", ["tools/docslint/docslint.py"], ()),
    ("approval-gate-tests", "tooling", ["-m", "unittest", "discover", "-s", "tools/approval_gate"], ()),
    ("agent-hook-tests", "tooling", ["-m", "unittest", "discover", "-s", ".claude/hooks"], ()),
    ("board-tests", "tooling", ["-m", "unittest", "discover", "-s", "tools/board"], ()),
    ("githooks-tests", "tooling", ["-m", "unittest", "discover", "-s", "tools/githooks"], ("git", "make")),
    ("rulesets-tests", "tooling", ["-m", "unittest", "discover", "-s", "tools/rulesets"], ()),
    ("secrets-tests", "tooling", ["-m", "unittest", "discover", "-s", "tools/secrets"], ("git", "gitleaks")),
    ("secrets", "tooling", ["tools/secrets/scan.py", "ci"], ("git", "gitleaks")),
    ("checks-tests", "tooling", ["-m", "unittest", "discover", "-s", "tools/checks"], ("make", "actionlint", "shellcheck")),
    ("actionlint", "tooling", None, ("actionlint", "shellcheck")),
)


class UnknownGroup(Exception):
    def __init__(self, name, valid):
        Exception.__init__(self, name)
        self.name = name
        self.valid = valid


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def groups():
    seen = []
    for _name, group, _cmd, _needs in CHECKS:
        if group not in seen:
            seen.append(group)
    return seen


def select_checks(checks, group):
    if group is None:
        return list(checks)
    selected = [c for c in checks if c[1] == group]
    if not selected:
        raise UnknownGroup(group, groups())
    return selected


def _python_command(entry, python):
    name, _group, command, _needs = entry
    if name == "actionlint":
        return ["actionlint", "-shellcheck=shellcheck", "-pyflakes="]
    if command[0] == "-m":
        return [python] + list(command)
    return [python] + list(command)


def run_checks(checks, root, run=subprocess.run, which=shutil.which, clock=time.monotonic, python=None, header=None):
    if python is None:
        python = sys.executable
    results = []
    interrupted = False
    for entry in checks:
        name, _group, _command, needs = entry
        if header is not None:
            header(name)
        start = clock()
        missing = [prog for prog in needs if which(prog) is None]
        if missing:
            results.append({
                "name": name,
                "status": "failed",
                "detail": "%s is not installed; run make doctor" % missing[0],
                "seconds": 0.0,
            })
            continue
        if interrupted:
            results.append({"name": name, "status": "not run", "detail": "", "seconds": 0.0})
            continue
        argv = _python_command(entry, python)
        try:
            completed = run(argv, cwd=root)
            code = completed.returncode
            elapsed = clock() - start
            if code == 0:
                results.append({"name": name, "status": "passed", "detail": "", "seconds": elapsed})
            else:
                results.append({
                    "name": name,
                    "status": "failed",
                    "detail": "exit code %s" % code,
                    "seconds": elapsed,
                })
        except KeyboardInterrupt:
            interrupted = True
            elapsed = clock() - start
            results.append({"name": name, "status": "failed", "detail": "interrupted", "seconds": elapsed})
    return results, interrupted


def format_summary(results):
    lines = ["make ci summary"]
    failed_names = []
    for item in results:
        status = item["status"]
        name = item["name"]
        seconds = item.get("seconds") or 0.0
        detail = item.get("detail") or ""
        if status == "passed":
            lines.append("  passed  %-22s %5.1fs" % (name, seconds))
        elif status == "not run":
            lines.append("  not run %-22s" % name)
        else:
            failed_names.append(name)
            extra = "   %s" % detail if detail else ""
            lines.append("  failed  %-22s %5.1fs%s" % (name, seconds, extra))
    if failed_names:
        lines.append("%s of %s checks failed: %s" % (len(failed_names), len(results), ", ".join(failed_names)))
    else:
        lines.append("all %s checks passed" % len(results))
    return "\n".join(lines)


def _print_header(name):
    sys.stdout.write("==> %s\n" % name)
    sys.stdout.flush()


def main(argv=None, version_info=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    version_info = sys.version_info if version_info is None else version_info
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--group", default=None)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code in (0, None):
            return 0
        return 2
    if version_info < MIN_PYTHON:
        found = "%s.%s.%s" % version_info[:3]
        sys.stderr.write("Python 3.10 or newer is needed, found %s\n" % found)
        return 1
    try:
        selected = select_checks(CHECKS, args.group)
    except UnknownGroup as exc:
        sys.stderr.write("unknown group %r; valid groups: %s\n" % (exc.name, ", ".join(exc.valid)))
        return 2
    results, interrupted = run_checks(selected, repo_root(), header=_print_header)
    sys.stdout.write(format_summary(results) + "\n")
    if interrupted:
        return 130
    for item in results:
        if item["status"] != "passed":
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
