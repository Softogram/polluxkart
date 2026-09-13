#!/usr/bin/env python3
"""Claude Code PreToolUse hook: agents never approve tickets.

Only the owner applies the GitHub label `stage: implementation-ready`, by hand
(owner rule, 2026-09-13, docs/platform/development-process.md). GitHub cannot
tell an agent apart from the owner when the agent uses the owner's login, so
this hook refuses any shell command that would apply, create, rename or delete
that label. Reading issues filtered by the label stays allowed.

Input: the hook payload JSON on stdin ({"tool_name": "Bash", "tool_input": {"command": ...}}).
Output: a JSON permission decision of "deny" with a reason, or nothing to allow.
"""

from __future__ import annotations

import json
import re
import sys

LABEL_RE = re.compile(r"implementation[-_ ]?ready", re.IGNORECASE)
GITHUB_TOOL_RE = re.compile(r"(\bgh\b|api\.github\.com|\bcurl\b|\bwget\b|\bhttpie\b|\bhttp\s)", re.IGNORECASE)
SEGMENT_SPLIT_RE = re.compile(r"&&|\|\||;|\||\n")

READ_ONLY_RE = re.compile(
    r"\bgh\s+("
    r"(issue|pr)\s+(list|view|status)"
    r"|search\s+\w+"
    r"|label\s+list"
    r"|project\s+(list|view|item-list|field-list)"
    r")\b",
    re.IGNORECASE,
)
API_WRITE_RE = re.compile(
    r"(-X\s*|--method[ =]\s*)(POST|PUT|PATCH|DELETE)\b|(^|\s)(-f|-F|--field|--raw-field|--input)(\s|=)",
    re.IGNORECASE,
)

REASON = (
    "Blocked by the PolluxKart approval rule: only the owner applies `stage: implementation-ready`, "
    "by hand on GitHub. Agents never apply, create, rename or delete that label. "
    "Move the ticket to `stage: awaiting-approval` and ask the owner instead. "
    "See docs/platform/development-process.md."
)


def segment_is_blocked(segment: str) -> bool:
    if not LABEL_RE.search(segment) or not GITHUB_TOOL_RE.search(segment):
        return False
    if READ_ONLY_RE.search(segment):
        return False
    if re.search(r"\bgh\s+api\b", segment, re.IGNORECASE):
        is_graphql = re.search(r"\bgraphql\b", segment, re.IGNORECASE)
        if is_graphql:
            return bool(re.search(r"\bmutation\b", segment, re.IGNORECASE))
        return bool(API_WRITE_RE.search(segment))
    if re.search(r"\b(curl|wget|http)\b", segment, re.IGNORECASE):
        return bool(re.search(r"(-X\s*|--request\s+)(POST|PUT|PATCH|DELETE)|\s(-d|--data\S*|--json)\s", segment, re.IGNORECASE))
    return True  # any other gh subcommand mentioning the label is treated as a write


def is_blocked(command: str) -> bool:
    if not LABEL_RE.search(command):
        return False
    return any(segment_is_blocked(segment) for segment in SEGMENT_SPLIT_RE.split(command)) or (
        # A label value split across a pipeline still counts if the whole command writes.
        GITHUB_TOOL_RE.search(command) is not None
        and not READ_ONLY_RE.search(command)
        and re.search(r"--add-label|label\s+(create|edit|delete|clone)|addLabelsToLabelable|/labels", command, re.IGNORECASE)
        is not None
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if is_blocked(command):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON,
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
