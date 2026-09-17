"""Shared board helpers: stage names, tracked titles, and GitHub calls.

Used by the live checker (#32) and the label sync (#33).
`gh` is passed in so tests can use a fake and never call GitHub.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field

PROJECT_OWNER = "Softogram"
PROJECT_NUMBER = 2
REPO = "Softogram/polluxkart"
APPROVAL_LABEL = "stage: implementation-ready"

# Label to the project's Status option, in the order of development-process.md.
STAGES: dict[str, str] = {
    "stage: planning": "Planning",
    "stage: awaiting-approval": "Awaiting approval",
    "stage: implementation-ready": "Implementation ready",
    "stage: in-progress": "In progress",
    "stage: in-review": "In review",
    "stage: done": "Done",
}

STAGE_LABELS = tuple(STAGES.keys())

_TICKET_TITLE = re.compile(r"^E\d{2}-\d{2} .+$")
_EPIC_TITLE = re.compile(r"^Epic E\d{2}: .+$")


def is_tracked(title: str) -> bool:
    """True for `EXX-NN ...` tickets and `Epic EXX: ...` epics."""
    text = title or ""
    return bool(_TICKET_TITLE.match(text) or _EPIC_TITLE.match(text))


@dataclass
class Problem:
    message: str


@dataclass
class LabelEvent:
    label: str
    action: str  # "added" or "removed"
    actor: str


@dataclass
class Issue:
    number: int
    title: str
    state: str = "open"  # "open" or "closed"
    state_reason: str | None = None  # "completed", "not_planned", ...
    labels: list[str] = field(default_factory=list)
    events: list[LabelEvent] = field(default_factory=list)
    on_board: bool = True
    node_id: str = ""
    item_id: str = ""
    board_status: str | None = None


class GhError(Exception):
    """A GitHub call failed."""


class RealGh:
    """Talks to GitHub through `gh api graphql`. Never prints the token."""

    def __init__(self, run=None) -> None:
        self._run = run or subprocess.run

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        command = ["gh", "api", "graphql", "-f", f"query={query}"]
        for key, value in (variables or {}).items():
            if value is None:
                command.extend(["-F", f"{key}=null"])
                continue
            flag = "-f" if isinstance(value, str) else "-F"
            command.extend([flag, f"{key}={value if isinstance(value, str) else json.dumps(value)}"])
        result = self._run(command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "gh api graphql failed").strip()
            raise GhError(err)
        payload = json.loads(result.stdout)
        if payload.get("errors"):
            raise GhError(json.dumps(payload["errors"]))
        return payload["data"]

    def list_tracked(self) -> list[Issue]:
        issues: dict[int, Issue] = {}
        cursor = None
        owner, name = REPO.split("/")
        while True:
            data = self.graphql(
                """
                query($owner:String!, $name:String!, $cursor:String) {
                  repository(owner:$owner, name:$name) {
                    issues(first:100, after:$cursor, states:[OPEN, CLOSED]) {
                      pageInfo { hasNextPage endCursor }
                      nodes {
                        id number title state stateReason
                        labels(first:20) { nodes { name } }
                        timelineItems(first:100, itemTypes:[LABELED_EVENT, UNLABELED_EVENT]) {
                          nodes {
                            __typename
                            ... on LabeledEvent { createdAt actor { login } label { name } }
                            ... on UnlabeledEvent { createdAt actor { login } label { name } }
                          }
                        }
                      }
                    }
                  }
                }
                """,
                {"owner": owner, "name": name, "cursor": cursor},
            )
            conn = data["repository"]["issues"]
            for node in conn["nodes"]:
                title = node["title"] or ""
                if not is_tracked(title):
                    continue
                reason = node.get("stateReason")
                issues[node["number"]] = Issue(
                    number=node["number"],
                    title=title,
                    state=(node.get("state") or "OPEN").lower(),
                    state_reason=(reason or "").lower() or None,
                    labels=[n["name"] for n in (node.get("labels") or {}).get("nodes") or []],
                    events=_events_from_timeline(node.get("timelineItems") or {}),
                    on_board=False,
                    node_id=node["id"],
                )
            if not conn["pageInfo"]["hasNextPage"]:
                break
            cursor = conn["pageInfo"]["endCursor"]
        self._attach_board(issues)
        return [issues[n] for n in sorted(issues)]

    def fetch_issue(self, number: int) -> Issue | None:
        for issue in self.list_tracked():
            if issue.number == number:
                return issue
        return None

    def issue(self, number: int) -> Issue:
        found = self.fetch_issue(number)
        if found is None:
            raise GhError(f"#{number} is not a tracked issue")
        return found

    def _attach_board(self, issues: dict[int, Issue]) -> None:
        project = self.project()
        for number, item_id, status in project["items"]:
            issue = issues.get(number)
            if issue is None:
                continue
            issue.on_board = True
            issue.item_id = item_id
            issue.board_status = status
        self._project = project

    def project(self) -> dict:
        if getattr(self, "_project", None):
            return self._project
        cursor = None
        items: list[tuple[int, str, str | None]] = []
        project_id = None
        field_id = None
        options: dict[str, str] = {}
        title = ""
        public = False
        while True:
            data = self.graphql(
                """
                query($owner:String!, $number:Int!, $cursor:String) {
                  organization(login:$owner) {
                    projectV2(number:$number) {
                      id title public
                      field(name:"Status") {
                        ... on ProjectV2SingleSelectField {
                          id
                          options { id name }
                        }
                      }
                      items(first:100, after:$cursor) {
                        pageInfo { hasNextPage endCursor }
                        nodes {
                          id
                          fieldValueByName(name:"Status") {
                            ... on ProjectV2ItemFieldSingleSelectValue { name }
                          }
                          content { ... on Issue { number } }
                        }
                      }
                    }
                  }
                }
                """,
                {"owner": PROJECT_OWNER, "number": PROJECT_NUMBER, "cursor": cursor},
            )
            proj = data["organization"]["projectV2"]
            project_id = proj["id"]
            title = proj.get("title") or ""
            public = bool(proj.get("public"))
            field = proj.get("field") or {}
            field_id = field.get("id")
            options = {opt["name"]: opt["id"] for opt in field.get("options") or []}
            conn = proj["items"]
            for node in conn["nodes"]:
                content = node.get("content") or {}
                number = content.get("number")
                if number is None:
                    continue
                status = (node.get("fieldValueByName") or {}).get("name")
                items.append((number, node["id"], status))
            if not conn["pageInfo"]["hasNextPage"]:
                break
            cursor = conn["pageInfo"]["endCursor"]
        self._project = {
            "id": project_id,
            "title": title,
            "public": public,
            "field_id": field_id,
            "options": options,
            "items": items,
        }
        return self._project

    def add_to_board(self, issue: Issue) -> None:
        project = self.project()
        data = self.graphql(
            """
            mutation($project:ID!, $content:ID!) {
              addProjectV2ItemById(input:{projectId:$project, contentId:$content}) {
                item { id }
              }
            }
            """,
            {"project": project["id"], "content": issue.node_id},
        )
        issue.item_id = data["addProjectV2ItemById"]["item"]["id"]
        issue.on_board = True
        self._project = None

    def set_status(self, issue: Issue, status: str) -> None:
        project = self.project()
        option = project["options"].get(status)
        if not option:
            raise GhError(f"unknown Status option {status!r} for #{issue.number}")
        if not issue.item_id:
            self.add_to_board(issue)
        self.graphql(
            """
            mutation($project:ID!, $item:ID!, $field:ID!, $option:String!) {
              updateProjectV2ItemFieldValue(
                input:{
                  projectId:$project
                  itemId:$item
                  fieldId:$field
                  value:{singleSelectOptionId:$option}
                }
              ) { projectV2Item { id } }
            }
            """,
            {
                "project": project["id"],
                "item": issue.item_id,
                "field": project["field_id"],
                "option": option,
            },
        )
        issue.board_status = status

    def add_label(self, number: int, label: str) -> None:
        if label == APPROVAL_LABEL:
            raise GhError("the sync never adds stage: implementation-ready")
        result = self._run(
            ["gh", "issue", "edit", str(number), "--repo", REPO, "--add-label", label],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GhError((result.stderr or result.stdout or "add-label failed").strip())

    def remove_label(self, number: int, label: str) -> None:
        result = self._run(
            ["gh", "issue", "edit", str(number), "--repo", REPO, "--remove-label", label],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GhError((result.stderr or result.stdout or "remove-label failed").strip())


def _events_from_timeline(timeline: dict) -> list[LabelEvent]:
    events: list[LabelEvent] = []
    for node in timeline.get("nodes") or []:
        kind = node.get("__typename")
        label = (node.get("label") or {}).get("name") or ""
        actor = (node.get("actor") or {}).get("login") or ""
        if kind == "LabeledEvent":
            events.append(LabelEvent(label=label, action="added", actor=actor))
        elif kind == "UnlabeledEvent":
            events.append(LabelEvent(label=label, action="removed", actor=actor))
    return events
