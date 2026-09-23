#!/usr/bin/env python3
"""Check every GitHub Action is pinned to an exact commit.

A workflow step names the action it runs on a `uses:` line. A movable tag
such as `@v7` points at whatever the action's author last put there, so the
code that runs in this repository could change without a pull request. A
40-character commit id cannot move.

The version comment (`# v7.0.1`) is required as well, because a reviewer
reading a bare commit id cannot tell which release it is. Dependabot keeps
both current.

Design: docs/design/low-level/issue-38-dependabot-codeql.md
"""

from __future__ import annotations

import os
import re
import sys

WORKFLOWS = os.path.join(".github", "workflows")
USES_RE = re.compile(r"^\s*(?:-\s*)?uses\s*:\s*(\S+)\s*(.*)$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
VERSION_COMMENT_RE = re.compile(r"#\s*v?\d+(\.\d+)*")


def _strip_quotes(text):
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def check_line(value, comment):
    """Return the reason this `uses:` value is not acceptable, or None."""
    value = _strip_quotes(value)
    if value.startswith("./") or value.startswith("../"):
        return None
    if value.startswith("docker://"):
        if "@" not in value:
            return "a docker image must be pinned by sha256 digest"
        _image, _, digest = value.partition("@")
        if not DIGEST_RE.match(digest):
            return "a docker image must be pinned by sha256 digest"
        return None
    if "@" not in value:
        return "not pinned to a commit"
    _action, _, reference = value.rpartition("@")
    if not COMMIT_RE.match(reference):
        return "not pinned to a commit"
    if not VERSION_COMMENT_RE.search(comment or ""):
        return "add the version as a comment, for example # v7.0.1"
    return None


def check_text(text, name):
    """Check one workflow file's text. Returns a list of problems."""
    problems = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        match = USES_RE.match(line)
        if not match:
            continue
        reason = check_line(match.group(1), match.group(2))
        if reason:
            problems.append("%s:%s %s: %s" % (name, number, match.group(1), reason))
    return problems


def workflow_files(root, folder=WORKFLOWS):
    full = os.path.join(root, folder)
    if not os.path.isdir(full):
        return []
    names = sorted(
        name for name in os.listdir(full) if name.endswith(".yml") or name.endswith(".yaml")
    )
    return [os.path.join(folder, name) for name in names]


def check_all(root, folder=WORKFLOWS):
    problems = []
    for relative in workflow_files(root, folder):
        with open(os.path.join(root, relative), "r", encoding="utf-8") as handle:
            problems.extend(check_text(handle.read(), relative))
    return problems


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None, root=None, stream=None):
    stream = sys.stdout if stream is None else stream
    root = repo_root() if root is None else root
    problems = check_all(root)
    for problem in problems:
        stream.write("  %s\n" % problem)
    if problems:
        stream.write(
            "%s action%s not pinned to a commit\n"
            % (len(problems), "" if len(problems) == 1 else "s")
        )
        return 1
    stream.write("Every action is pinned to a commit\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
