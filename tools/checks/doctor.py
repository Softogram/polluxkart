#!/usr/bin/env python3
"""Check that this machine has the tools the checks need.

Python 3.7 can parse this file so an older interpreter prints a version
message instead of a syntax error. Runtime still needs 3.10 or newer.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

from linters import LINTERS

MIN_PYTHON = (3, 10)
VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


def _linter_version(name):
    for item in LINTERS:
        if item["name"] == name:
            return item["version"]
    raise KeyError(name)


TOOLS = (
    {
        "name": "python3",
        "version_command": [sys.executable, "--version"],
        "needed_now": True,
        "minimum": "3.10",
        "purpose": "Runs every check and this doctor",
        "install_hint": "install Python 3.10 or newer from https://www.python.org/downloads/",
    },
    {
        "name": "make",
        "version_command": ["make", "--version"],
        "needed_now": True,
        "minimum": "3.81",
        "purpose": "Runs the targets",
        "install_hint": "install make (xcode-select --install on macOS, or your package manager)",
    },
    {
        "name": "git",
        "version_command": ["git", "--version"],
        "needed_now": True,
        "minimum": None,
        "purpose": "Worktrees, commits",
        "install_hint": "install git from https://git-scm.com/",
    },
    {
        "name": "gh",
        "version_command": ["gh", "--version"],
        "needed_now": True,
        "minimum": None,
        "purpose": "Moving ticket stage labels",
        "install_hint": "brew install gh",
    },
    {
        "name": "git hooks",
        "kind": "hooks",
        "needed_now": True,
        "minimum": None,
        "purpose": "Local pre-commit and pre-push hooks",
        "install_hint": "git config core.hooksPath .githooks",
    },
    {
        "name": "actionlint",
        "version_command": ["actionlint", "-version"],
        "needed_now": True,
        "minimum": _linter_version("actionlint"),
        "purpose": "The actionlint check",
        "install_hint": "brew install actionlint",
    },
    {
        "name": "shellcheck",
        "version_command": ["shellcheck", "--version"],
        "needed_now": True,
        "minimum": _linter_version("shellcheck"),
        "purpose": "The actionlint check",
        "install_hint": "brew install shellcheck",
    },
    {
        "name": "java",
        "version_command": ["java", "-version"],
        "needed_now": False,
        "minimum": None,
        "purpose": "backend foundation (#13); exact version still open in #55",
        "install_hint": "",
        "note": "backend foundation (#13); exact version still open in #55",
    },
    {
        "name": "node",
        "version_command": ["node", "--version"],
        "needed_now": False,
        "minimum": None,
        "purpose": "frontend foundation (#14); planned 24 LTS",
        "install_hint": "",
    },
    {
        "name": "pnpm",
        "version_command": ["pnpm", "--version"],
        "needed_now": False,
        "minimum": None,
        "purpose": "frontend foundation (#14)",
        "install_hint": "",
    },
    {
        "name": "docker",
        "version_command": ["docker", "--version"],
        "needed_now": False,
        "minimum": None,
        "purpose": "local stack (#15); start Docker Desktop when that work begins",
        "install_hint": "",
        "info_command": ["docker", "info"],
    },
)


def probe_hooks(tool, run=subprocess.run, environ=None):
    environ = os.environ if environ is None else environ
    on_github = environ.get("GITHUB_ACTIONS") == "true"
    needed = bool(tool.get("needed_now")) and not on_github
    try:
        completed = run(
            ["git", "config", "--get", "core.hooksPath"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return {"name": tool["name"], "status": "no answer", "version": "", "needed": needed, "hint": tool["install_hint"]}
    value = (completed.stdout or "").strip()
    if completed.returncode != 0 or not value:
        return {"name": tool["name"], "status": "not enabled", "version": "", "needed": needed, "hint": tool["install_hint"]}
    if value == ".githooks":
        return {"name": tool["name"], "status": "ok", "version": value, "needed": needed, "hint": ""}
    return {
        "name": tool["name"],
        "status": "points elsewhere",
        "version": value,
        "needed": needed,
        "hint": tool["install_hint"],
    }


def parse_version(text):
    match = VERSION_RE.search(text or "")
    if not match:
        return None
    return match.group(1)


def version_tuple(text):
    parts = []
    for bit in text.split("."):
        try:
            parts.append(int(bit))
        except ValueError:
            break
    return tuple(parts)


def probe(tool, run=subprocess.run, which=shutil.which, environ=None):
    environ = os.environ if environ is None else environ
    if tool.get("kind") == "hooks":
        return probe_hooks(tool, run=run, environ=environ)
    name = tool["name"]
    needed = tool["needed_now"]
    if which(tool["version_command"][0]) is None and name != "python3":
        if needed:
            return {"name": name, "status": "missing", "version": "", "needed": True, "hint": tool["install_hint"]}
        return {"name": name, "status": "not installed", "version": "", "needed": False, "hint": ""}
    try:
        completed = run(
            tool["version_command"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        status = "no answer"
        return {"name": name, "status": status, "version": "", "needed": needed, "hint": tool["install_hint"]}
    output = (completed.stdout or "") + (completed.stderr or "")
    version = parse_version(output)
    if name == "docker" and tool.get("info_command"):
        try:
            info = run(tool["info_command"], capture_output=True, text=True, timeout=10)
            if info.returncode != 0:
                return {
                    "name": name,
                    "status": "installed, not running",
                    "version": version or "",
                    "needed": False,
                    "hint": "",
                }
        except subprocess.TimeoutExpired:
            return {
                "name": name,
                "status": "installed, not running",
                "version": version or "",
                "needed": False,
                "hint": "",
            }
    if needed:
        if version is None:
            if tool["minimum"]:
                return {"name": name, "status": "version unreadable", "version": "", "needed": True, "hint": tool["install_hint"]}
            return {"name": name, "status": "ok", "version": "version unknown", "needed": True, "hint": ""}
        if tool["minimum"] and version_tuple(version) < version_tuple(tool["minimum"]):
            return {"name": name, "status": "too old", "version": version, "needed": True, "hint": tool["install_hint"]}
        return {"name": name, "status": "ok", "version": version, "needed": True, "hint": ""}
    return {"name": name, "status": "found", "version": version or "", "needed": False, "hint": tool.get("note") or tool["purpose"]}


def format_report(findings):
    lines = ["make doctor", "", "Needed now"]
    problems = []
    for item in findings:
        if not item["needed"]:
            continue
        extra = ""
        if item["status"] == "ok" and item["name"] in ("python3", "make"):
            extra = "    need %s or newer" % {"python3": "3.10", "make": "3.81"}[item["name"]]
        elif item["status"] == "ok" and item["name"] in ("actionlint", "shellcheck"):
            extra = "    need %s or newer" % _linter_version(item["name"])
        elif item["status"] == "missing":
            extra = "    install: %s" % item["hint"]
        elif item["status"] == "not enabled":
            extra = "    %s" % item["hint"]
        elif item["status"] == "points elsewhere":
            extra = "    found %s; want .githooks" % item["version"]
        elif item["status"] == "too old":
            extra = "    need %s or newer" % _linter_version(item["name"]) if item["name"] in ("actionlint", "shellcheck") else "    too old"
        lines.append("  %-12s %-12s %-10s%s" % (item["status"], item["name"], item["version"], extra))
        if item["status"] != "ok":
            problems.append(item["name"])
    lines.extend(["", "Needed later (information only, never fails)"])
    for item in findings:
        if item["needed"]:
            continue
        note = item.get("hint") or ""
        lines.append("  %-20s %-10s %-10s %s" % (item["status"], item["name"], item["version"], note))
    if problems:
        if len(problems) == 1:
            lines.append("")
            lines.append("1 needed tool has a problem: %s" % problems[0])
        else:
            lines.append("")
            lines.append("%s needed tools have a problem: %s" % (len(problems), ", ".join(problems)))
    else:
        lines.append("")
        lines.append("All tools needed today are ready")
    return "\n".join(lines), problems


def main(argv=None, version_info=None, run=subprocess.run, which=shutil.which, environ=None):
    version_info = sys.version_info if version_info is None else version_info
    environ = os.environ if environ is None else environ
    if version_info < MIN_PYTHON:
        found = "%s.%s.%s" % version_info[:3]
        sys.stderr.write("Python 3.10 or newer is needed, found %s\n" % found)
        return 1
    findings = [probe(tool, run=run, which=which, environ=environ) for tool in TOOLS]
    report, problems = format_report(findings)
    sys.stdout.write(report + "\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
