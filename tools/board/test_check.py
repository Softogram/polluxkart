"""Unit tests for the live board checker. A fake `gh` stands in for GitHub."""

from __future__ import annotations

import io
import json
import sys
import unittest
from types import SimpleNamespace

from board import (
    EPICS_VIEW,
    STAGES,
    TICKETS_VIEW,
    GhError,
    Issue,
    RealGh,
    compare,
    is_tracked,
)
from check import OK, main


def ticket(number, title, label, status=None, **kwargs):
    status = STAGES[label] if status is None else status
    values = {
        "number": number,
        "title": title,
        "labels": [label],
    }
    values.update(kwargs)
    return Issue(**values)


def good_views():
    return [dict(TICKETS_VIEW), dict(EPICS_VIEW)]


def good_project(entries, **overrides):
    project = {
        "title": "PolluxKart",
        "public": True,
        "status_order": list(STAGES.values()),
        "views": good_views(),
        "board_entries": entries,
    }
    project.update(overrides)
    return project


def entries_for(*issues):
    return [
        {"number": issue.number, "title": issue.title, "status": STAGES[issue.labels[0]]}
        for issue in issues
    ]


class FakeCheckGh:
    def __init__(self, project, issues=None, error=None):
        self._project = project
        self._issues = list(issues or [])
        self.error = error

    def project(self):
        if self.error:
            raise GhError(self.error)
        return self._project

    def list_tracked(self):
        if self.error:
            raise GhError(self.error)
        return list(self._issues)


class CompareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.a = ticket(1, "E00-01 Approval gate and label guard", "stage: planning")
        self.b = ticket(2, "E00-02 GitHub Project board", "stage: in-progress")
        self.c = ticket(3, "Epic E00: Engineering", "stage: done")

    def test_b1_1_clean_board(self) -> None:
        issues = [self.a, self.b, self.c]
        problems = compare(good_project(entries_for(*issues)), issues)
        self.assertEqual([p.message for p in problems], [])
        code, out, err = self._run_main(good_project(entries_for(*issues)), issues)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), OK)
        self.assertEqual(err, "")

    def test_b1_2_missing_from_board(self) -> None:
        issues = [self.a, self.b, self.c]
        project = good_project(entries_for(self.a, self.c))
        messages = [p.message for p in compare(project, issues)]
        self.assertTrue(any("2" in m and "not on the board" in m for m in messages))
        self.assertEqual(len(messages), 1)

    def test_b1_3_on_board_twice(self) -> None:
        issues = [self.a]
        entries = entries_for(self.a) + entries_for(self.a)
        messages = [p.message for p in compare(good_project(entries), issues)]
        self.assertTrue(any("2 times" in m for m in messages))

    def test_b1_4_untracked_item(self) -> None:
        issues = [self.a]
        entries = entries_for(self.a) + [{"number": 99, "title": "Random note", "status": "Planning"}]
        messages = [p.message for p in compare(good_project(entries), issues)]
        self.assertTrue(any("Random note" in m for m in messages))

    def test_b1_5_no_stage_label(self) -> None:
        issue = ticket(4, "E00-04 Makefile", "stage: planning")
        project = good_project(entries_for(issue))
        issue.labels = []
        messages = [p.message for p in compare(project, [issue])]
        self.assertTrue(any("no stage label" in m for m in messages))

    def test_b1_6_two_stage_labels(self) -> None:
        issue = ticket(4, "E00-04 Makefile", "stage: planning")
        issue.labels = ["stage: planning", "stage: in-review"]
        messages = [p.message for p in compare(good_project(entries_for(issue)), [issue])]
        self.assertTrue(any("planning" in m and "in-review" in m for m in messages))

    def test_b1_7_status_mismatch(self) -> None:
        issue = ticket(5, "E00-05 Git hooks", "stage: in-review", status="In progress")
        entries = [{"number": 5, "title": issue.title, "status": "In progress"}]
        messages = [p.message for p in compare(good_project(entries), [issue])]
        self.assertTrue(any("In progress" in m and "in-review" in m for m in messages))

    def test_b1_7_empty_status_is_mismatch(self) -> None:
        issue = ticket(5, "E00-05 Git hooks", "stage: in-review")
        entries = [{"number": 5, "title": issue.title, "status": None}]
        messages = [p.message for p in compare(good_project(entries), [issue])]
        self.assertTrue(any("None" in m and "in-review" in m for m in messages))

    def test_views_unreadable(self) -> None:
        messages = [p.message for p in compare(good_project(entries_for(self.a), views=None), [self.a])]
        self.assertTrue(any("could not read view settings" in m for m in messages))

    def test_epics_sort_by_title(self) -> None:
        views = good_views()
        views[1]["sort_by"] = ["Status"]
        messages = [p.message for p in compare(good_project(entries_for(self.a), views=views), [self.a])]
        self.assertTrue(any("Epics" in m and "sort-by" in m and "Title" in m for m in messages))

    def test_b1_8_private_board(self) -> None:
        issues = [self.a]
        messages = [p.message for p in compare(good_project(entries_for(self.a), public=False), issues)]
        self.assertTrue(any("not public" in m for m in messages))

    def test_b1_9_renamed_board(self) -> None:
        issues = [self.a]
        messages = [p.message for p in compare(good_project(entries_for(self.a), title="Other"), issues)]
        self.assertTrue(any("Other" in m for m in messages))

    def test_b1_10_tickets_view_table(self) -> None:
        views = good_views()
        views[0]["layout"] = "TABLE_LAYOUT"
        messages = [p.message for p in compare(good_project(entries_for(self.a), views=views), [self.a])]
        self.assertTrue(any("Tickets" in m and "TABLE_LAYOUT" in m for m in messages))

    def test_b1_11_tickets_filter(self) -> None:
        views = good_views()
        views[0]["filter"] = "is:issue"
        messages = [p.message for p in compare(good_project(entries_for(self.a), views=views), [self.a])]
        self.assertTrue(any("filter" in m and "-label:epic" in m for m in messages))

    def test_b1_12_missing_parent_issue_field(self) -> None:
        views = good_views()
        views[0]["fields"] = [name for name in views[0]["fields"] if name != "Parent issue"]
        messages = [p.message for p in compare(good_project(entries_for(self.a), views=views), [self.a])]
        self.assertTrue(any("Parent issue" in m for m in messages))

    def test_b1_13_epics_view_missing(self) -> None:
        views = [dict(TICKETS_VIEW)]
        messages = [p.message for p in compare(good_project(entries_for(self.a), views=views), [self.a])]
        self.assertTrue(any("Epics" in m and "missing" in m for m in messages))

    def test_b1_14_status_order(self) -> None:
        order = list(reversed(list(STAGES.values())))
        messages = [
            p.message
            for p in compare(good_project(entries_for(self.a), status_order=order), [self.a])
        ]
        self.assertTrue(any("Status options" in m and "Planning" in m for m in messages))

    def test_b1_15_several_problems(self) -> None:
        issue = ticket(8, "E00-08 Dependabot", "stage: planning")
        project = good_project(
            [{"number": 8, "title": issue.title, "status": "Done"}],
            public=False,
            title="Wrong",
        )
        messages = [p.message for p in compare(project, [issue])]
        self.assertGreaterEqual(len(messages), 3)

    def _run_main(self, project, issues):
        buf_out, buf_err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = main(gh=FakeCheckGh(project, issues))
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, buf_out.getvalue(), buf_err.getvalue()


class HelperTest(unittest.TestCase):
    def test_h2_4_offline_never_reports_success(self) -> None:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = main(gh=FakeCheckGh({}, error="gh: Not logged in"))
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        self.assertEqual(code, 1)
        self.assertIn("Not logged in", buf_err.getvalue())
        self.assertNotIn(OK, buf_out.getvalue())

    def test_h2_3_pages_are_followed(self) -> None:
        pages = [
            {
                "repository": {
                    "issues": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "aaa"},
                        "nodes": [
                            {
                                "id": "1",
                                "number": 1,
                                "title": "E00-01 Approval gate",
                                "state": "OPEN",
                                "stateReason": None,
                                "labels": {"nodes": [{"name": "stage: planning"}]},
                                "timelineItems": {"nodes": []},
                            }
                        ],
                    }
                }
            },
            {
                "repository": {
                    "issues": {
                        "pageInfo": {"hasNextPage": False, "endCursor": "bbb"},
                        "nodes": [
                            {
                                "id": "2",
                                "number": 2,
                                "title": "Epic E00: Engineering",
                                "state": "OPEN",
                                "stateReason": None,
                                "labels": {"nodes": [{"name": "stage: done"}]},
                                "timelineItems": {"nodes": []},
                            }
                        ],
                    }
                }
            },
            {
                "organization": {
                    "projectV2": {
                        "id": "p",
                        "title": "PolluxKart",
                        "public": True,
                        "field": {"id": "f", "options": [{"id": "o", "name": "Planning"}]},
                        "views": {"nodes": []},
                        "items": {
                            "pageInfo": {"hasNextPage": True, "endCursor": "p1"},
                            "nodes": [
                                {
                                    "id": "item-1",
                                    "fieldValueByName": {"name": "Planning"},
                                    "content": {"number": 1, "title": "E00-01 Approval gate"},
                                }
                            ],
                        },
                    }
                }
            },
            {
                "organization": {
                    "projectV2": {
                        "id": "p",
                        "title": "PolluxKart",
                        "public": True,
                        "field": {"id": "f", "options": [{"id": "o", "name": "Planning"}]},
                        "views": {"nodes": []},
                        "items": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {
                                    "id": "item-2",
                                    "fieldValueByName": {"name": "Done"},
                                    "content": {"number": 2, "title": "Epic E00: Engineering"},
                                }
                            ],
                        },
                    }
                }
            },
        ]

        def run(command, check=False, capture_output=False, text=False):
            payload = pages.pop(0)
            return SimpleNamespace(returncode=0, stdout=json.dumps({"data": payload}), stderr="")

        gh = RealGh(run=run)
        issues = gh.list_tracked()
        self.assertEqual([issue.number for issue in issues], [1, 2])
        self.assertTrue(is_tracked(issues[0].title))
        self.assertTrue(is_tracked(issues[1].title))
        project = gh.project()
        self.assertEqual([entry["number"] for entry in project["board_entries"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
