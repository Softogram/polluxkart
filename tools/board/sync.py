#!/usr/bin/env python3
"""Move PolluxKart project cards to match each ticket's stage label.

One-way: labels move cards. A card dragged by hand is put back.
The sync never adds `stage: implementation-ready`.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

from board import (
    APPROVAL_LABEL,
    STAGES,
    GhError,
    Issue,
    LabelEvent,
    RealGh,
    compare,
    is_tracked,
)

DEFAULT_APPROVER = "CosmicSaaurabh"


@dataclass
class Action:
    number: int
    skip: bool = False
    fail: str | None = None
    add_to_board: bool = False
    add_labels: list[str] = field(default_factory=list)
    remove_labels: list[str] = field(default_factory=list)
    status: str | None = None


def last_add_actor(events: list[LabelEvent], label: str) -> str | None:
    for event in reversed(events):
        if event.label == label and event.action == "added":
            return event.actor
    return None


def valid_stage_labels(labels: list[str], events: list[LabelEvent], approver: str) -> list[str]:
    valid: list[str] = []
    for label in labels:
        if label not in STAGES:
            continue
        if label == APPROVAL_LABEL and last_add_actor(events, label) != approver:
            continue
        valid.append(label)
    return valid


def _wrong_approval_index(events: list[LabelEvent], approver: str) -> int | None:
    index = None
    for i, event in enumerate(events):
        if event.label == APPROVAL_LABEL and event.action == "added" and event.actor != approver:
            index = i
    return index


def _guard_or_wrong_approval(labels: list[str], events: list[LabelEvent], approver: str) -> bool:
    if APPROVAL_LABEL in labels and last_add_actor(events, APPROVAL_LABEL) != approver:
        return True
    if _wrong_approval_index(events, approver) is not None:
        return True
    return False


def stage_to_restore(events: list[LabelEvent], approver: str) -> str | None:
    """Most recent non-approval stage added before the wrong approval.

    Returns None when that last valid stage was the owner's approval
    (the caller must fail rather than add the approval label).
    """
    index = _wrong_approval_index(events, approver)
    if index is None:
        return None
    last_non_approval = None
    saw_owner_approval = False
    for event in events[:index]:
        if event.label not in STAGES or event.action != "added":
            continue
        if event.label == APPROVAL_LABEL:
            if event.actor == approver:
                saw_owner_approval = True
            continue
        last_non_approval = event.label
    if last_non_approval:
        return last_non_approval
    if saw_owner_approval:
        return APPROVAL_LABEL
    return None


def decide(issue: Issue, approver: str) -> Action:
    if not is_tracked(issue.title):
        return Action(number=issue.number, skip=True)

    action = Action(number=issue.number, add_to_board=not issue.on_board)

    if issue.state == "closed" and issue.state_reason == "completed":
        current = [label for label in issue.labels if label in STAGES]
        if current == ["stage: done"]:
            action.status = STAGES["stage: done"]
            return action
        action.remove_labels = [label for label in current if label != "stage: done"]
        if "stage: done" not in issue.labels:
            action.add_labels = ["stage: done"]
        action.status = STAGES["stage: done"]
        return action

    valid = valid_stage_labels(issue.labels, issue.events, approver)

    if len(valid) == 1:
        action.status = STAGES[valid[0]]
        return action

    if len(valid) >= 2:
        named = ", ".join(valid)
        action.fail = f"#{issue.number} has two or more stage labels: {named}"
        return action

    # No valid stage label.
    if issue.state == "closed" and issue.state_reason == "not_planned":
        action.fail = None
        return action

    if _guard_or_wrong_approval(issue.labels, issue.events, approver):
        restore = stage_to_restore(issue.events, approver)
        if restore == APPROVAL_LABEL:
            action.fail = f"#{issue.number}: re-apply the approval by hand"
            return action
        if restore:
            if restore not in issue.labels:
                action.add_labels = [restore]
            action.status = STAGES[restore]
            return action
        action.fail = f"#{issue.number}: re-apply the approval by hand"
        return action

    action.fail = f"#{issue.number}: no stage label"
    return action


def apply(action: Action, gh) -> None:
    if action.skip or action.fail:
        return
    if APPROVAL_LABEL in action.add_labels:
        raise GhError("the sync never adds stage: implementation-ready")
    issue = gh.issue(action.number)
    if action.add_to_board:
        gh.add_to_board(issue)
    if action.status and issue.board_status != action.status:
        gh.set_status(issue, action.status)
    for label in action.remove_labels:
        gh.remove_label(action.number, label)
        if label in issue.labels:
            issue.labels.remove(label)
    for label in action.add_labels:
        gh.add_label(action.number, label)
        if label not in issue.labels:
            issue.labels.append(label)


def reconcile(gh, checker=None) -> list[str]:
    failures: list[str] = []
    for issue in gh.list_tracked():
        action = decide(issue, gh.approver)
        if action.fail:
            failures.append(action.fail)
            continue
        try:
            apply(action, gh)
        except GhError as error:
            failures.append(f"#{issue.number}: {error}")
            continue
    if checker is not None:
        project = gh.project()
        for problem in checker(project, gh.list_tracked()):
            message = problem.message if hasattr(problem, "message") else str(problem)
            failures.append(message)
    return failures


def _redact(text: str, token: str) -> str:
    if token and token in text:
        return text.replace(token, "***")
    return text


def main(env: dict[str, str] | None = None, gh=None, stream=None) -> int:
    env = env if env is not None else os.environ
    stream = stream if stream is not None else sys.stderr
    token = env.get("GH_TOKEN") or ""
    approver = env.get("APPROVER") or DEFAULT_APPROVER
    raw_number = (env.get("ISSUE_NUMBER") or "").strip()
    if gh is None:
        gh = RealGh()
    gh.approver = approver
    try:
        if raw_number:
            number = int(raw_number)
            issue = gh.fetch_issue(number)
            if issue is None:
                return 0
            action = decide(issue, approver)
            if action.fail:
                print(_redact(action.fail, token), file=stream)
                return 1
            apply(action, gh)
            return 0
        failures = reconcile(gh, checker=compare)
        for line in failures:
            print(_redact(line, token), file=stream)
        return 1 if failures else 0
    except Exception as error:
        print(_redact(str(error), token), file=stream)
        return 1


if __name__ == "__main__":
    sys.exit(main())
