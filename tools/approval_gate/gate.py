#!/usr/bin/env python3
"""Approval gate: a pull request may implement only a ticket the owner approved.

The rule (owner decision, 2026-09-13, docs/platform/development-process.md):
nothing is implemented without the owner's approval. The owner approves a
ticket by applying the label `stage: implementation-ready` by hand.

What this check enforces on every pull request:

1. The pull request links exactly one kind of ticket reference:
   - `Implements #N` for an implementation pull request, or
   - `Plans #N` for a planning pull request (documents only).
   Pull requests opened by Dependabot are exempt.
2. A planning pull request changes only Markdown files and never uses a
   closing keyword (closes, fixes, resolves), so planning cannot close a ticket.
3. An implementation pull request implements exactly one open ticket that:
   - carries exactly one stage label, which is implementation-ready,
     in-progress or in-review; and
   - whose most recent planning-or-approval stage label (planning,
     awaiting-approval or implementation-ready) was implementation-ready,
     applied by the approver. Moving a ticket back to planning revokes approval.
4. An implementation pull request ships its tests: code under
   `api/**/src/main/` needs a change under `api/**/src/test/`, and code under
   `web/src/` needs a changed test file in `web/` or a change under `e2e/`.
5. An implementation pull request closes no ticket other than its own.
6. A pull request into `main` passes only when it comes from this repository's `development` branch.

It runs from the base branch (pull_request_target), reads only GitHub's API,
and never executes code from the pull request.

Standard library only. Environment: GITHUB_TOKEN, GITHUB_REPOSITORY,
PR_NUMBER, APPROVER. Exit code 0 passes, 1 fails.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field

APPROVAL_LABEL = "stage: implementation-ready"
STAGE_PREFIX = "stage: "
DECISION_STAGES = {"stage: planning", "stage: awaiting-approval", APPROVAL_LABEL}
IMPLEMENTABLE_STAGES = {APPROVAL_LABEL, "stage: in-progress", "stage: in-review"}
EXEMPT_AUTHORS = {"dependabot[bot]"}

IMPLEMENTS_RE = re.compile(r"^[ \t]*Implements[ \t]+#(\d+)[ \t]*$", re.IGNORECASE | re.MULTILINE)
PLANS_RE = re.compile(r"^[ \t]*Plans[ \t]+#(\d+)[ \t]*$", re.IGNORECASE | re.MULTILINE)
CLOSING_RE = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b[ \t]*:?[ \t]+#(\d+)", re.IGNORECASE)
TEST_FILE_RE = re.compile(r"\.(?:test|spec)\.[cm]?[jt]sx?$")


@dataclass
class LabelEvent:
    label: str
    actor: str


@dataclass
class Ticket:
    number: int
    exists: bool = True
    is_pull_request: bool = False
    state: str = "open"
    labels: list[str] = field(default_factory=list)
    label_events: list[LabelEvent] = field(default_factory=list)  # "labeled" events, oldest first


@dataclass
class Result:
    ok: bool
    messages: list[str]


def references(pattern: re.Pattern[str], body: str) -> list[int]:
    return sorted({int(n) for n in pattern.findall(body or "")})


def is_document(path: str) -> bool:
    return path.lower().endswith(".md")


def missing_tests(files: list[str]) -> list[str]:
    problems = []
    api_main = [f for f in files if re.match(r"^api/.+/src/main/", f)]
    api_test = [f for f in files if re.match(r"^api/.+/src/test/", f)]
    if api_main and not api_test:
        problems.append(
            "Backend code changed under api/**/src/main/ but no test changed under api/**/src/test/. "
            "Feature implementation and its tests ship in the same pull request."
        )
    web_code = [f for f in files if f.startswith("web/src/") and not TEST_FILE_RE.search(f)]
    web_test = [f for f in files if (f.startswith("web/") and TEST_FILE_RE.search(f)) or f.startswith("e2e/")]
    if web_code and not web_test:
        problems.append(
            "Frontend code changed under web/src/ but no test file (*.test.ts(x), *.spec.ts(x)) or e2e/ change is included. "
            "Feature implementation and its tests ship in the same pull request."
        )
    return problems


def approval_state(ticket: Ticket, approver: str) -> tuple[bool, str]:
    """Return (approved, explanation) from the ticket's label history."""
    decisive = [e for e in ticket.label_events if e.label in DECISION_STAGES]
    if not decisive:
        return False, f"#{ticket.number} has never been labelled `{APPROVAL_LABEL}`."
    last = decisive[-1]
    if last.label != APPROVAL_LABEL:
        return False, (
            f"#{ticket.number} was moved to `{last.label}` after any earlier approval, "
            f"so it is not approved now."
        )
    if last.actor.lower() != approver.lower():
        return False, (
            f"`{APPROVAL_LABEL}` on #{ticket.number} was applied by `{last.actor}`, not by the owner `{approver}`."
        )
    return True, f"#{ticket.number} was approved by `{approver}`."


def evaluate(*, author: str, body: str, files: list[str], tickets: dict[int, Ticket], approver: str, base_ref: str = "development", head_ref: str = "", head_repository: str = "", repository: str = "") -> Result:
    if base_ref == "main":
        same_repo = bool(repository) and head_repository == repository
        if head_ref == "development" and same_repo:
            return Result(True, ["Release pull request from development into main"])
        return Result(False, ["Pull requests into main must come from this repository's development branch"])
    if author in EXEMPT_AUTHORS:
        return Result(True, [f"Pull request by `{author}` is exempt (automated dependency update)."])

    implements = references(IMPLEMENTS_RE, body)
    plans = references(PLANS_RE, body)
    closes = references(CLOSING_RE, body)
    messages: list[str] = []

    if not implements and not plans:
        return Result(False, [
            "Link this pull request to its ticket on its own line: `Implements #N` for code, "
            "or `Plans #N` for design, test plan or documentation changes."
        ])

    if implements and plans:
        return Result(False, [
            "Use either `Implements #N` or `Plans #N`, not both. "
            "Planning and implementation are separate pull requests."
        ])

    if plans:
        ok = True
        non_docs = [f for f in files if not is_document(f)]
        if non_docs:
            ok = False
            shown = ", ".join(non_docs[:10]) + (" ..." if len(non_docs) > 10 else "")
            messages.append(
                "A planning pull request (`Plans #N`) may change only Markdown documents, but it changes: "
                f"{shown}. Code and configuration need `Implements #N` on a ticket the owner approved."
            )
        if closes:
            ok = False
            messages.append(
                "A planning pull request must not close its ticket. Remove closing keywords "
                f"(closes, fixes, resolves) for: {', '.join('#' + str(n) for n in closes)}."
            )
        for number in plans:
            ticket = tickets.get(number)
            if ticket is None or not ticket.exists or ticket.is_pull_request:
                ok = False
                messages.append(f"#{number} is not an issue in this repository.")
            elif ticket.state != "open":
                ok = False
                messages.append(f"#{number} is closed; plan an open ticket.")
        if ok:
            messages.append("Planning pull request: documents only, linked to open tickets.")
        return Result(ok, messages)

    # Implementation pull request.
    if len(implements) != 1:
        return Result(False, [
            "An implementation pull request implements exactly one ticket, but it names: "
            f"{', '.join('#' + str(n) for n in implements)}."
        ])

    number = implements[0]
    ticket = tickets.get(number)
    if ticket is None or not ticket.exists or ticket.is_pull_request:
        return Result(False, [f"#{number} is not an issue in this repository."])

    ok = True
    if ticket.state != "open":
        ok = False
        messages.append(f"#{number} is closed; an implementation pull request needs an open ticket.")

    stages = sorted(label for label in ticket.labels if label.startswith(STAGE_PREFIX))
    if len(stages) != 1:
        ok = False
        messages.append(f"#{number} must carry exactly one stage label, but it has: {stages or 'none'}.")
    elif stages[0] not in IMPLEMENTABLE_STAGES:
        ok = False
        messages.append(
            f"#{number} is at `{stages[0]}`. Only tickets the owner approved "
            f"(`{APPROVAL_LABEL}`, then in-progress or in-review) may be implemented."
        )

    approved, why = approval_state(ticket, approver)
    messages.append(why)
    ok = ok and approved

    for problem in missing_tests(files):
        ok = False
        messages.append(problem)

    others = [n for n in closes if n != number]
    if others:
        ok = False
        messages.append(
            "An implementation pull request may close only its own ticket, but it also closes: "
            f"{', '.join('#' + str(n) for n in others)}."
        )

    if ok:
        messages.append(f"Implementation pull request for approved ticket #{number}.")
    return Result(ok, messages)


class GitHub:
    def __init__(self, token: str, repository: str) -> None:
        self.token = token
        self.repository = repository

    def get(self, path: str) -> tuple[int, object]:
        request = urllib.request.Request(
            f"https://api.github.com/repos/{self.repository}/{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, None

    def paged(self, path: str) -> list[dict]:
        items: list[dict] = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            status, data = self.get(f"{path}{separator}per_page=100&page={page}")
            if status != 200 or not isinstance(data, list):
                raise RuntimeError(f"GitHub API returned {status} for {path}")
            items.extend(data)
            if len(data) < 100:
                break
        return items

    def ticket(self, number: int) -> Ticket:
        status, issue = self.get(f"issues/{number}")
        if status == 404 or not isinstance(issue, dict):
            return Ticket(number=number, exists=False)
        events = [
            LabelEvent(label=e["label"]["name"], actor=(e.get("actor") or {}).get("login", ""))
            for e in self.paged(f"issues/{number}/events")
            if e.get("event") == "labeled" and e.get("label")
        ]
        return Ticket(
            number=number,
            is_pull_request="pull_request" in issue,
            state=issue.get("state", "open"),
            labels=[label["name"] for label in issue.get("labels", [])],
            label_events=events,
        )


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    number = os.environ.get("PR_NUMBER", "")
    approver = os.environ.get("APPROVER", "")
    if not (token and repository and number.isdigit() and approver):
        print("approval-gate: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER and APPROVER are required; failing closed.")
        return 1

    github = GitHub(token, repository)
    status, pull = github.get(f"pulls/{number}")
    if status != 200 or not isinstance(pull, dict):
        print(f"approval-gate: could not read pull request #{number} (HTTP {status}); failing closed.")
        return 1
    files = [f["filename"] for f in github.paged(f"pulls/{number}/files")]
    body = pull.get("body") or ""
    head = pull.get("head") or {}
    head_repo = ((head.get("repo") or {}) or {}).get("full_name") or ""
    wanted = set(references(IMPLEMENTS_RE, body)) | set(references(PLANS_RE, body))
    tickets = {n: github.ticket(n) for n in wanted}

    result = evaluate(
        author=(pull.get("user") or {}).get("login", ""),
        body=body,
        files=files,
        tickets=tickets,
        approver=approver,
        base_ref=(pull.get("base") or {}).get("ref") or "",
        head_ref=head.get("ref") or "",
        head_repository=head_repo,
        repository=repository,
    )
    heading = "approval-gate: PASS" if result.ok else "approval-gate: FAIL"
    print(heading)
    for message in result.messages:
        print(f"  - {message}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"## {heading}\n\n" + "".join(f"- {m}\n" for m in result.messages))
            handle.write("\nRules: docs/platform/development-process.md\n")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
