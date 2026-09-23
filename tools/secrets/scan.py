#!/usr/bin/env python3
"""Scan for secrets with gitleaks, for the pre-commit hook and for make ci.

A secret is a password, API key, token or private key. This repository is
public, so anything that reaches it is readable by anyone, forever.

Two commands:

    scan.py staged   the pre-commit hook: the staged changes
    scan.py ci       the `secrets` check in make ci: the branch's commits,
                     then every tracked file as it is now

Both first check the allow-list rules, then run the pinned gitleaks with
--redact, so no output ever prints a value that was found.

Design: docs/design/low-level/issue-37-secret-scanning.md
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# The marker gitleaks obeys in a source comment to silence a finding. The
# owner refused inline allows (2026-09-14), so this file must look for the
# marker without containing it, or the scan would fail on itself.
INLINE_MARKER = "gitleaks" + ":allow"

CONFIG_NAME = ".gitleaks.toml"
DEFAULT_BASE_BRANCH = "origin/development"
NOT_INSTALLED = "gitleaks is not installed; run make doctor"
FETCH_FIRST = "%s was not found, so the commits to scan are unknown; fetch origin first" % DEFAULT_BASE_BRANCH

# Entries in .gitleaks.toml are read with a small line reader rather than a
# TOML library, because tomllib needs Python 3.11 and the repository supports
# 3.10. Anything this reader cannot understand is reported as a problem, so
# the check fails closed.
ALLOWLIST_HEADER_RE = re.compile(r"^\s*\[\[\s*allowlists\s*\]\]\s*$")
ANY_HEADER_RE = re.compile(r"^\s*\[")
KEY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
DESCRIPTION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*:\s*(.*)$")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
DATED_REASON_HINT = 'each entry needs description = "YYYY-MM-DD: why this is not a secret"'


class ScanError(Exception):
    """Something stopped the scan from running at all."""


def repo_root(run=subprocess.run, cwd=None):
    result = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise ScanError((result.stderr or result.stdout or "git rev-parse failed").strip())
    return result.stdout.strip()


def _git(run, root, args):
    return run(["git"] + list(args), capture_output=True, text=True, cwd=root)


# ---------------------------------------------------------------- allow list


def parse_allowlists(config_text):
    """Return one dict of raw key text per [[allowlists]] entry, in order."""
    entries = []
    current = None
    key = None
    for number, line in enumerate(config_text.splitlines(), start=1):
        if ALLOWLIST_HEADER_RE.match(line):
            current = {"_line": number, "_keys": {}}
            entries.append(current)
            key = None
            continue
        if ANY_HEADER_RE.match(line) and not ALLOWLIST_HEADER_RE.match(line):
            current = None
            key = None
            continue
        if current is None:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = KEY_RE.match(line)
        if match:
            key = match.group(1)
            current["_keys"][key] = match.group(2).strip()
        elif key is not None:
            current["_keys"][key] += " " + stripped
    return entries


def _unquote(text):
    for quote in ("'''", '"""', "'", '"'):
        if text.startswith(quote) and text.endswith(quote) and len(text) >= 2 * len(quote):
            return text[len(quote):-len(quote)]
    return text


def check_allowlist(config_text):
    """Check every allow-list entry carries a real date and a reason."""
    problems = []
    for index, entry in enumerate(parse_allowlists(config_text), start=1):
        where = "allow-list entry %s (line %s)" % (index, entry["_line"])
        keys = entry["_keys"]
        if "commits" in keys:
            problems.append(
                "%s uses commits, which stop matching after a squash merge; narrow it by path, regex or rule"
                % where
            )
        raw = keys.get("description")
        if raw is None:
            problems.append("%s has no description; %s" % (where, DATED_REASON_HINT))
            continue
        description = _unquote(raw).strip()
        match = DESCRIPTION_RE.match(description)
        if not match:
            problems.append("%s description does not start with a date; %s" % (where, DATED_REASON_HINT))
            continue
        try:
            datetime.date.fromisoformat(match.group(1))
        except ValueError:
            problems.append("%s description starts with %s, which is not a real date" % (where, match.group(1)))
            continue
        if not match.group(2).strip():
            problems.append("%s description has a date but no reason; %s" % (where, DATED_REASON_HINT))
    return problems


def _markdown_marker_is_quoted(line, index):
    """True when the marker at this position sits inside `backticks`."""
    for span in CODE_SPAN_RE.finditer(line):
        if span.start() < index < span.end():
            return True
    return False


def find_inline_allows(root, paths):
    """Find tracked files that silence gitleaks with an inline comment."""
    problems = []
    for path in paths:
        full = os.path.join(root, path)
        try:
            with open(full, "r", encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        is_markdown = path.lower().endswith(".md")
        for number, line in enumerate(lines, start=1):
            index = line.find(INLINE_MARKER)
            while index != -1:
                if not (is_markdown and _markdown_marker_is_quoted(line, index)):
                    problems.append(
                        "%s:%s has an inline allow comment; allow it in %s with a dated reason instead"
                        % (path, number, CONFIG_NAME)
                    )
                    break
                index = line.find(INLINE_MARKER, index + 1)
    return problems


def tracked_files(root, run=subprocess.run):
    result = _git(run, root, ["ls-files", "-z"])
    if result.returncode != 0:
        raise ScanError((result.stderr or "git ls-files failed").strip())
    return [name for name in (result.stdout or "").split("\0") if name]


def allowlist_problems(root, run=subprocess.run):
    config = os.path.join(root, CONFIG_NAME)
    try:
        with open(config, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return ["%s is missing" % CONFIG_NAME]
    return check_allowlist(text) + find_inline_allows(root, tracked_files(root, run=run))


# ------------------------------------------------------------------ gitleaks


def _gitleaks_argv(root, subcommand, extra):
    return [
        "gitleaks",
        subcommand,
    ] + list(extra) + [
        "--config", os.path.join(root, CONFIG_NAME),
        "--redact",
        "--no-banner",
        "--ignore-gitleaks-allow",
        "--report-format", "json",
    ]


def _run_gitleaks(root, subcommand, extra, run=subprocess.run, which=shutil.which):
    """Run gitleaks and return its findings, already redacted by gitleaks."""
    if which("gitleaks") is None:
        raise ScanError(NOT_INSTALLED)
    handle, report_path = tempfile.mkstemp(prefix="polluxkart-gitleaks-", suffix=".json")
    os.close(handle)
    try:
        argv = _gitleaks_argv(root, subcommand, extra) + ["--report-path", report_path]
        completed = run(argv, cwd=root, capture_output=True, text=True)
        try:
            with open(report_path, "r", encoding="utf-8") as report:
                text = report.read().strip()
        except OSError:
            text = ""
        if not text:
            if completed.returncode not in (0, 1):
                detail = (completed.stderr or completed.stdout or "").strip()
                raise ScanError("gitleaks failed: %s" % (detail or "exit code %s" % completed.returncode))
            return []
        try:
            findings = json.loads(text)
        except json.JSONDecodeError:
            raise ScanError("gitleaks wrote a report this scan could not read")
        return findings or []
    finally:
        os.unlink(report_path)


def format_findings(findings):
    """One line per finding: rule, file and line, and the commit when there is one.

    Only these fields are printed. The matched value is never read from the
    report, so no log can repeat a secret even if gitleaks stopped redacting.
    """
    lines = []
    for item in findings:
        rule = item.get("RuleID") or item.get("Description") or "unknown rule"
        where = "%s:%s" % (item.get("File") or "?", item.get("StartLine") or "?")
        commit = (item.get("Commit") or "").strip()
        if commit:
            lines.append("  %s  %s  in commit %s" % (rule, where, commit[:12]))
        else:
            lines.append("  %s  %s" % (rule, where))
    return lines


# --------------------------------------------------------------- scan ranges


def resolve_base(root, environ, run=subprocess.run):
    """The commit the branch's own commits start after.

    On GitHub the workflow passes the pull request's base commit as
    SCAN_BASE. On a laptop it is where the branch left origin/development.
    """
    given = (environ.get("SCAN_BASE") or "").strip()
    if given:
        found = _git(run, root, ["rev-parse", "--verify", "--quiet", given + "^{commit}"])
        if found.returncode != 0:
            raise ScanError("SCAN_BASE %s is not a commit in this repository" % given)
        return found.stdout.strip()
    known = _git(run, root, ["rev-parse", "--verify", "--quiet", DEFAULT_BASE_BRANCH + "^{commit}"])
    if known.returncode != 0:
        raise ScanError(FETCH_FIRST)
    merge_base = _git(run, root, ["merge-base", DEFAULT_BASE_BRANCH, "HEAD"])
    if merge_base.returncode != 0:
        raise ScanError(FETCH_FIRST)
    return merge_base.stdout.strip()


def scan_range(root, base, run=subprocess.run, which=shutil.which):
    """Scan every commit after base up to HEAD, including ones later undone."""
    head = _git(run, root, ["rev-parse", "--verify", "--quiet", "HEAD^{commit}"])
    if head.returncode != 0:
        return []
    if base and base == head.stdout.strip():
        return []
    listed = _git(run, root, ["rev-list", "%s..HEAD" % base])
    if listed.returncode != 0 or not (listed.stdout or "").strip():
        return []
    return _run_gitleaks(root, "git", ["--log-opts=%s..HEAD" % base], run=run, which=which)


def scan_tracked_files(root, run=subprocess.run, which=shutil.which):
    """Scan the tracked files as they are now, ignoring anything git ignores.

    gitleaks dir would also read ignored files such as a contributor's own
    .env, so the tracked files are copied into a temporary folder, scanned
    there, and the folder is deleted whatever happens.
    """
    paths = tracked_files(root, run=run)
    temp = tempfile.mkdtemp(prefix="polluxkart-secrets-")
    try:
        for path in paths:
            source = os.path.join(root, path)
            if not os.path.isfile(source) or os.path.islink(source):
                continue
            target = os.path.join(temp, path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(source, target)
        return _run_gitleaks(root, "dir", [temp], run=run, which=which)
    finally:
        shutil.rmtree(temp, ignore_errors=True)


# ----------------------------------------------------------------- commands


def _report(stream, problems, findings):
    for problem in problems:
        stream.write("  %s\n" % problem)
    for line in format_findings(findings):
        stream.write(line + "\n")
    total = len(findings)
    if total == 0:
        stream.write("No secrets found\n")
    elif total == 1:
        stream.write("1 possible secret found\n")
    else:
        stream.write("%s possible secrets found\n" % total)
    if problems:
        stream.write("%s allow-list problem%s\n" % (len(problems), "" if len(problems) == 1 else "s"))
    return 1 if (problems or findings) else 0


def command_staged(root, stream, run=subprocess.run, which=shutil.which):
    problems = allowlist_problems(root, run=run)
    findings = _run_gitleaks(root, "git", ["--pre-commit", "--staged"], run=run, which=which)
    return _report(stream, problems, findings)


def command_ci(root, environ, stream, run=subprocess.run, which=shutil.which):
    problems = allowlist_problems(root, run=run)
    base = resolve_base(root, environ, run=run)
    findings = scan_range(root, base, run=run, which=which)
    findings = findings + scan_tracked_files(root, run=run, which=which)
    return _report(stream, problems, findings)


def main(argv=None, environ=None, stream=None, run=subprocess.run, which=shutil.which, cwd=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    environ = os.environ if environ is None else environ
    stream = sys.stdout if stream is None else stream
    command = argv[0] if argv else ""
    if command not in ("staged", "ci"):
        sys.stderr.write("usage: scan.py staged|ci\n")
        return 2
    try:
        root = repo_root(run=run, cwd=cwd)
        if command == "staged":
            return command_staged(root, stream, run=run, which=which)
        return command_ci(root, environ, stream, run=run, which=which)
    except ScanError as error:
        stream.write("%s\n" % error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
