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


BOARD_NAME = "PolluxKart"
TICKETS_VIEW = {
    "name": "Tickets",
    "layout": "BOARD_LAYOUT",
    "filter": "is:issue -label:epic",
    "group_by": ["Status"],
    "fields": ["Title", "Parent issue", "Assignees", "Linked pull requests", "Labels"],
}
EPICS_VIEW = {
    "name": "Epics",
    "layout": "TABLE_LAYOUT",
    "filter": "label:epic",
    "sort_by": ["Title"],
    "fields": ["Title", "Status", "Sub-issues progress"],
}


def fetch_project(gh):
    return gh.project()


def fetch_tracked_issues(gh):
    return gh.list_tracked()


def compare(project, issues):
    """Return every mismatch between the live board and the stage labels."""
    problems = []
    title = project.get("title") or ""
    if title != BOARD_NAME:
        problems.append(Problem("board is named %r, expected %s" % (title, BOARD_NAME)))
    if not project.get("public"):
        problems.append(Problem("board is not public"))
    expected_order = list(STAGES.values())
    found_order = list(project.get("status_order") or [])
    if found_order != expected_order:
        problems.append(
            Problem("Status options are %s, expected %s" % (found_order, expected_order))
        )
    problems.extend(_view_problems(project.get("views")))
    entries = list(project.get("board_entries") or [])
    counts = {}
    for entry in entries:
        number = entry.get("number")
        counts[number] = counts.get(number, 0) + 1
        item_title = entry.get("title") or ""
        if not is_tracked(item_title):
            problems.append(Problem("board item %r is not a tracked issue" % item_title))
    for issue in issues:
        count = counts.get(issue.number, 0)
        if count == 0:
            problems.append(Problem("#%s %s is not on the board" % (issue.number, issue.title)))
        elif count > 1:
            problems.append(
                Problem("#%s %s is on the board %s times" % (issue.number, issue.title, count))
            )
        stage_labels = [label for label in issue.labels if label in STAGES]
        if not stage_labels:
            problems.append(Problem("#%s %s has no stage label" % (issue.number, issue.title)))
        elif len(stage_labels) > 1:
            problems.append(
                Problem(
                    "#%s %s has more than one stage label: %s"
                    % (issue.number, issue.title, ", ".join(stage_labels))
                )
            )
        else:
            expected = STAGES[stage_labels[0]]
            found_status = None
            for entry in entries:
                if entry.get("number") == issue.number:
                    found_status = entry.get("status")
                    break
            if count == 1 and found_status != expected:
                problems.append(
                    Problem(
                        "#%s %s Status is %r, label is %s (%s)"
                        % (issue.number, issue.title, found_status, stage_labels[0], expected)
                    )
                )
    return problems


def _view_problems(views):
    problems = []
    if views is None:
        problems.append(Problem("could not read view settings"))
        return problems
    by_name = {view.get("name"): view for view in views}
    for expected in (TICKETS_VIEW, EPICS_VIEW):
        found = by_name.get(expected["name"])
        if found is None:
            problems.append(Problem("view %s is missing" % expected["name"]))
            continue
        if found.get("layout") != expected["layout"]:
            problems.append(
                Problem(
                    "view %s layout is %s, expected %s"
                    % (expected["name"], found.get("layout"), expected["layout"])
                )
            )
        if expected.get("filter") and expected["filter"] not in (found.get("filter") or ""):
            problems.append(
                Problem(
                    "view %s filter is %r, expected %s"
                    % (expected["name"], found.get("filter"), expected["filter"])
                )
            )
        if expected.get("group_by"):
            group_by = found.get("group_by") or []
            if group_by != expected["group_by"]:
                problems.append(
                    Problem(
                        "view %s group-by is %s, expected %s"
                        % (expected["name"], group_by, expected["group_by"])
                    )
                )
        if expected.get("sort_by"):
            sort_by = found.get("sort_by") or []
            if sort_by != expected["sort_by"]:
                problems.append(
                    Problem(
                        "view %s sort-by is %s, expected %s"
                        % (expected["name"], sort_by, expected["sort_by"])
                    )
                )
        missing_fields = [name for name in expected["fields"] if name not in (found.get("fields") or [])]
        for name in missing_fields:
            problems.append(Problem("view %s is missing field %s" % (expected["name"], name)))
    return problems


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
        board_entries: list[dict] = []
        project_id = None
        field_id = None
        options: dict[str, str] = {}
        status_order: list[str] = []
        views: list[dict] | None = None
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
                      views(first: 20) {
                        nodes {
                          name
                          layout
                          filter
                          groupByFields(first: 10) {
                            nodes {
                              ... on ProjectV2Field { name }
                              ... on ProjectV2IterationField { name }
                              ... on ProjectV2SingleSelectField { name }
                            }
                          }
                          sortByFields(first: 10) {
                            nodes {
                              field {
                                ... on ProjectV2Field { name }
                                ... on ProjectV2IterationField { name }
                                ... on ProjectV2SingleSelectField { name }
                              }
                            }
                          }
                          fields(first: 20) {
                            nodes {
                              ... on ProjectV2Field { name }
                              ... on ProjectV2IterationField { name }
                              ... on ProjectV2SingleSelectField { name }
                            }
                          }
                        }
                      }
                      items(first:100, after:$cursor) {
                        pageInfo { hasNextPage endCursor }
                        nodes {
                          id
                          fieldValueByName(name:"Status") {
                            ... on ProjectV2ItemFieldSingleSelectValue { name }
                          }
                          content { ... on Issue { number title } }
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
            if not status_order:
                status_order = [opt["name"] for opt in field.get("options") or []]
            if views is None:
                views = [_parse_view(node) for node in (proj.get("views") or {}).get("nodes") or []]
            conn = proj["items"]
            for node in conn["nodes"]:
                content = node.get("content") or {}
                number = content.get("number")
                item_title = content.get("title") or ""
                status = (node.get("fieldValueByName") or {}).get("name")
                board_entries.append({"number": number, "title": item_title, "status": status})
                if number is None:
                    continue
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
            "status_order": status_order,
            "views": views,
            "items": items,
            "board_entries": board_entries,
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
        self._project = None

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


def _field_name(node) -> str:
    if not node:
        return ""
    if "name" in node:
        return node.get("name") or ""
    field = node.get("field") or {}
    return field.get("name") or ""


def _parse_view(node: dict) -> dict:
    fields = [_field_name(item) for item in (node.get("fields") or {}).get("nodes") or []]
    group_by = [_field_name(item) for item in (node.get("groupByFields") or {}).get("nodes") or []]
    sort_by = [_field_name(item) for item in (node.get("sortByFields") or {}).get("nodes") or []]
    return {
        "name": node.get("name") or "",
        "layout": node.get("layout") or "",
        "filter": node.get("filter") or "",
        "group_by": [name for name in group_by if name],
        "sort_by": [name for name in sort_by if name],
        "fields": [name for name in fields if name],
    }


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
