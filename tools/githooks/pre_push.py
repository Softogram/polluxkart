#!/usr/bin/env python3
"""Pre-push hook: refuse direct pushes to development/main, run make ci on open PRs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

PROTECTED = ("development", "main")
PROCESS_DOC = "docs/platform/development-process.md"
ZERO = "0" * 40


@dataclass
class PushedRef:
    local_ref: str
    local_sha: str
    remote_ref: str
    remote_sha: str

    @property
    def is_delete(self) -> bool:
        return not self.local_sha.strip("0") or self.local_ref == "(delete)"

    @property
    def is_tag(self) -> bool:
        return self.remote_ref.startswith("refs/tags/")

    @property
    def branch(self):
        prefix = "refs/heads/"
        if self.remote_ref.startswith(prefix):
            return self.remote_ref[len(prefix):]
        return None


class Unknown:
    def __init__(self, reason: str) -> None:
        self.reason = reason


def parse_push_lines(text: str) -> list[PushedRef]:
    refs = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts
        refs.append(PushedRef(local_ref, local_sha, remote_ref, remote_sha))
    return refs


def protected_refs(refs: list[PushedRef]) -> list[PushedRef]:
    found = []
    for item in refs:
        branch = item.branch
        if branch in PROTECTED:
            found.append(item)
    return found


def open_pull_request(branch: str, run=subprocess.run, which=shutil.which):
    if which("gh") is None:
        return Unknown("gh is not installed")
    try:
        completed = run(
            ["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return Unknown("no answer within 15 seconds")
    if completed.returncode != 0:
        reason = (completed.stderr or completed.stdout or "gh failed").strip()
        return Unknown(reason)
    try:
        data = json.loads(completed.stdout or "")
    except json.JSONDecodeError:
        return Unknown("gh printed something that is not JSON")
    if not isinstance(data, list):
        return Unknown("gh printed something that is not JSON")
    if not data:
        return None
    number = data[0].get("number") if isinstance(data[0], dict) else None
    if not number:
        return Unknown("gh printed something that is not JSON")
    return number


def uncommitted_files(run=subprocess.run, cwd=None) -> list[str]:
    completed = run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=cwd)
    files = []
    for line in (completed.stdout or "").splitlines():
        path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            files.append(path)
    return files


def _warn(message: str, stream) -> None:
    stream.write(message + "\n")
    stream.flush()


def main(argv=None, stdin=None, env=None, run=subprocess.run, which=shutil.which, cwd=None, stream=None):
    env = os.environ if env is None else env
    stdin = sys.stdin if stdin is None else stdin
    stream = sys.stderr if stream is None else stream
    text = stdin.read() if hasattr(stdin, "read") else str(stdin)
    refs = parse_push_lines(text)
    if not refs:
        return 0
    blocked = protected_refs(refs)
    if blocked:
        names = sorted({item.branch for item in blocked if item.branch})
        name = names[0] if names else "a protected branch"
        _warn(
            "Pushing straight to %s is not allowed. Open a pull request instead (%s)."
            % (name, PROCESS_DOC),
            stream,
        )
        return 1
    branches = []
    for item in refs:
        if item.is_tag or item.is_delete:
            continue
        if item.branch:
            branches.append(item)
    if not branches:
        return 0
    pr_by_branch = {}
    for item in branches:
        result = open_pull_request(item.branch, run=run, which=which)
        pr_by_branch[item.branch] = result
        if isinstance(result, Unknown):
            _warn(
                "Could not check for an open pull request (%s). Pushing without running make ci; run the local checks yourself. The approval-gate still runs on the pull request."
                % result.reason,
                stream,
            )
    open_prs = {
        branch: number
        for branch, number in pr_by_branch.items()
        if isinstance(number, int)
    }
    if not open_prs:
        if all(result is None for result in pr_by_branch.values()):
            _warn("No open pull request for this branch; pushing without running make ci.", stream)
        return 0
    if env.get("SKIP_LOCAL_CI") == "1":
        numbers = ", ".join("#%s" % n for n in open_prs.values())
        _warn("SKIP_LOCAL_CI=1: make ci was not run. Say so in pull request %s." % numbers, stream)
        return 0
    dirty = uncommitted_files(run=run, cwd=cwd)
    if dirty:
        shown = dirty[:20]
        extra = len(dirty) - 20
        listing = "\n".join(shown)
        more = "\n... and %s more" % extra if extra > 0 else ""
        _warn(
            "Commit or remove these, then push again, so make ci checks exactly what you push.\n%s%s"
            % (listing, more),
            stream,
        )
        return 1
    head = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=cwd)
    head_sha = (head.stdout or "").strip()
    for item in branches:
        if item.branch in open_prs and item.local_sha != head_sha:
            _warn(
                "Push this branch from its own worktree, so make ci checks the commit being pushed.",
                stream,
            )
            return 1
    ci_env = dict(env)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        ci_env.pop(key, None)
    completed = run(["make", "ci"], cwd=cwd, env=ci_env)
    if completed.returncode != 0:
        _warn(
            "make ci failed, so the push was stopped. Fix the failures, or in a real emergency push with SKIP_LOCAL_CI=1 and say so in the pull request.",
            stream,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
