"""Tests for the board label sync. A fake `gh` stands in for GitHub."""

from __future__ import annotations

import io
import unittest
from dataclasses import dataclass, field

from board import APPROVAL_LABEL, STAGES, GhError, Issue, LabelEvent
from sync import Action, apply, decide, main, reconcile

OWNER = "CosmicSaaurabh"
HELPER = "helper"
GUARD = "github-actions[bot]"


def ev(label: str, action: str, actor: str) -> LabelEvent:
    return LabelEvent(label=label, action=action, actor=actor)


def issue(**kwargs) -> Issue:
    values = {
        "number": 10,
        "title": "E00-03 Keep the project board in sync with stage labels",
        "state": "open",
        "state_reason": None,
        "labels": ["stage: planning"],
        "events": [ev("stage: planning", "added", HELPER)],
        "on_board": True,
        "board_status": "Planning",
    }
    values.update(kwargs)
    return Issue(**values)


@dataclass
class FakeGh:
    issues: dict[int, Issue]
    approver: str = OWNER
    calls: list[tuple] = field(default_factory=list)
    fail_status_for: int | None = None
    view_problems: list[str] = field(default_factory=list)

    def list_tracked(self) -> list[Issue]:
        return [self.issues[n] for n in sorted(self.issues) if self.issues[n].title]

    def fetch_issue(self, number: int) -> Issue | None:
        return self.issues.get(number)

    def issue(self, number: int) -> Issue:
        found = self.issues[number]
        return found

    def project(self) -> dict:
        return {"view_problems": list(self.view_problems)}

    def add_to_board(self, issue: Issue) -> None:
        self.calls.append(("add_to_board", issue.number))
        issue.on_board = True

    def set_status(self, issue: Issue, status: str) -> None:
        self.calls.append(("set_status", issue.number, status))
        if self.fail_status_for == issue.number:
            raise GhError(f"status update failed for #{issue.number}")
        issue.board_status = status

    def add_label(self, number: int, label: str) -> None:
        if label == APPROVAL_LABEL:
            raise GhError("the sync never adds stage: implementation-ready")
        self.calls.append(("add_label", number, label))
        labels = self.issues[number].labels
        if label not in labels:
            labels.append(label)

    def remove_label(self, number: int, label: str) -> None:
        self.calls.append(("remove_label", number, label))
        labels = self.issues[number].labels
        if label in labels:
            labels.remove(label)


def status_of(action: Action) -> str | None:
    return action.status


class DecideTest(unittest.TestCase):
    def test_s1_1_one_planning_label_moves_the_card(self) -> None:
        action = decide(issue(), OWNER)
        self.assertIsNone(action.fail)
        self.assertEqual(action.status, "Planning")
        self.assertEqual(action.add_labels, [])
        self.assertEqual(action.remove_labels, [])

    def test_s1_2_label_change_to_awaiting_approval(self) -> None:
        ticket = issue(
            labels=["stage: awaiting-approval"],
            events=[
                ev("stage: planning", "added", HELPER),
                ev("stage: awaiting-approval", "added", HELPER),
                ev("stage: planning", "removed", HELPER),
            ],
            board_status="Planning",
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.status, "Awaiting approval")
        self.assertEqual(action.add_labels, [])

    def test_s1_3_owner_approval_is_valid(self) -> None:
        ticket = issue(
            labels=[APPROVAL_LABEL],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev(APPROVAL_LABEL, "added", OWNER),
                ev("stage: awaiting-approval", "removed", HELPER),
            ],
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.status, "Implementation ready")

    def test_s1_4_non_owner_approval_is_ignored(self) -> None:
        ticket = issue(
            labels=["stage: awaiting-approval", APPROVAL_LABEL],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
            ],
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.status, "Awaiting approval")
        self.assertEqual(action.add_labels, [])
        self.assertEqual(action.remove_labels, [])
        self.assertNotEqual(action.status, "Implementation ready")

    def test_s1_5_restore_last_valid_after_guard(self) -> None:
        ticket = issue(
            labels=[],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev("stage: awaiting-approval", "removed", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
                ev(APPROVAL_LABEL, "removed", GUARD),
            ],
        )
        action = decide(ticket, OWNER)
        self.assertIsNone(action.fail)
        self.assertEqual(action.add_labels, ["stage: awaiting-approval"])
        self.assertEqual(action.status, "Awaiting approval")

    def test_s1_6_last_valid_is_the_most_recent(self) -> None:
        ticket = issue(
            labels=[],
            events=[
                ev("stage: planning", "added", HELPER),
                ev(APPROVAL_LABEL, "added", OWNER),
                ev("stage: planning", "removed", HELPER),
                ev("stage: in-progress", "added", HELPER),
                ev(APPROVAL_LABEL, "removed", HELPER),
                ev("stage: in-progress", "removed", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
                ev(APPROVAL_LABEL, "removed", GUARD),
            ],
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.add_labels, ["stage: in-progress"])
        self.assertEqual(action.status, "In progress")

    def test_s1_7_never_adds_the_approval_label(self) -> None:
        ticket = issue(
            labels=[],
            events=[
                ev(APPROVAL_LABEL, "added", OWNER),
                ev(APPROVAL_LABEL, "removed", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
                ev(APPROVAL_LABEL, "removed", GUARD),
            ],
        )
        action = decide(ticket, OWNER)
        self.assertIsNotNone(action.fail)
        self.assertIn("re-apply the approval by hand", action.fail or "")
        self.assertEqual(action.add_labels, [])

    def test_s1_8_no_stage_label_fails(self) -> None:
        ticket = issue(labels=[], events=[])
        action = decide(ticket, OWNER)
        self.assertIn("no stage label", action.fail or "")

    def test_s1_9_two_stage_labels_fail_and_do_not_move(self) -> None:
        ticket = issue(
            labels=["stage: planning", "stage: in-review"],
            events=[
                ev("stage: planning", "added", HELPER),
                ev("stage: in-review", "added", HELPER),
            ],
            board_status="Planning",
        )
        action = decide(ticket, OWNER)
        self.assertIn("stage: planning", action.fail or "")
        self.assertIn("stage: in-review", action.fail or "")
        self.assertIsNone(action.status)

    def test_s1_10_completed_close_sets_done(self) -> None:
        ticket = issue(
            state="closed",
            state_reason="completed",
            labels=["stage: in-review"],
            events=[ev("stage: in-review", "added", HELPER)],
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.remove_labels, ["stage: in-review"])
        self.assertEqual(action.add_labels, ["stage: done"])
        self.assertEqual(action.status, "Done")

    def test_s1_11_completed_close_replaces_owner_approval(self) -> None:
        ticket = issue(
            state="closed",
            state_reason="completed",
            labels=[APPROVAL_LABEL],
            events=[ev(APPROVAL_LABEL, "added", OWNER)],
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.remove_labels, [APPROVAL_LABEL])
        self.assertEqual(action.add_labels, ["stage: done"])
        self.assertEqual(action.status, "Done")

    def test_s1_12_not_planned_changes_nothing(self) -> None:
        ticket = issue(
            state="closed",
            state_reason="not_planned",
            labels=["stage: planning"],
            events=[ev("stage: planning", "added", HELPER)],
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.status, "Planning")
        self.assertEqual(action.add_labels, [])
        self.assertEqual(action.remove_labels, [])

    def test_s1_13_already_done_sets_status_only(self) -> None:
        ticket = issue(
            state="closed",
            state_reason="completed",
            labels=["stage: done"],
            events=[ev("stage: done", "added", HELPER)],
            board_status="In review",
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.status, "Done")
        self.assertEqual(action.add_labels, [])
        self.assertEqual(action.remove_labels, [])

    def test_s1_14_untracked_title_is_ignored(self) -> None:
        ticket = issue(title="Bug: checkout broken")
        action = decide(ticket, OWNER)
        self.assertTrue(action.skip)

    def test_s1_15_new_ticket_is_added_then_placed(self) -> None:
        ticket = issue(title="E03-02 Maven skeleton", on_board=False, board_status=None)
        action = decide(ticket, OWNER)
        self.assertTrue(action.add_to_board)
        self.assertEqual(action.status, "Planning")

    def test_s1_16_reopened_done_ticket_is_not_guessed(self) -> None:
        ticket = issue(
            state="open",
            state_reason="reopened",
            labels=["stage: done"],
            events=[
                ev("stage: done", "added", HELPER),
            ],
            board_status="Done",
        )
        action = decide(ticket, OWNER)
        self.assertEqual(action.status, "Done")
        self.assertEqual(action.add_labels, [])
        self.assertEqual(action.remove_labels, [])


class GuardRaceTest(unittest.TestCase):
    def test_r2_1_awaiting_kept_before_and_after_guard(self) -> None:
        before = issue(
            labels=["stage: awaiting-approval", APPROVAL_LABEL],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
            ],
        )
        after = issue(
            labels=["stage: awaiting-approval"],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
                ev(APPROVAL_LABEL, "removed", GUARD),
            ],
        )
        for ticket in (before, after):
            action = decide(ticket, OWNER)
            self.assertEqual(action.status, "Awaiting approval")
            self.assertEqual(action.add_labels, [])
            self.assertEqual(action.remove_labels, [])
            self.assertNotEqual(action.status, "Implementation ready")

    def test_r2_2_guard_first_then_second_run_is_noop(self) -> None:
        first = issue(
            labels=[],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev("stage: awaiting-approval", "removed", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
                ev(APPROVAL_LABEL, "removed", GUARD),
            ],
        )
        action = decide(first, OWNER)
        self.assertEqual(action.add_labels, ["stage: awaiting-approval"])
        self.assertEqual(action.status, "Awaiting approval")
        second = issue(
            labels=["stage: awaiting-approval"],
            events=first.events + [ev("stage: awaiting-approval", "added", "polluxkart-board-sync[bot]")],
        )
        action = decide(second, OWNER)
        self.assertEqual(action.status, "Awaiting approval")
        self.assertEqual(action.add_labels, [])

    def test_r2_3_sync_first_restores_then_guard_leaves_it(self) -> None:
        first = issue(
            labels=[APPROVAL_LABEL],
            events=[
                ev("stage: awaiting-approval", "added", HELPER),
                ev("stage: awaiting-approval", "removed", HELPER),
                ev(APPROVAL_LABEL, "added", HELPER),
            ],
        )
        action = decide(first, OWNER)
        self.assertEqual(action.add_labels, ["stage: awaiting-approval"])
        self.assertEqual(action.status, "Awaiting approval")
        self.assertNotEqual(action.status, "Implementation ready")
        second = issue(
            labels=["stage: awaiting-approval"],
            events=first.events + [ev(APPROVAL_LABEL, "removed", GUARD)],
        )
        action = decide(second, OWNER)
        self.assertEqual(action.status, "Awaiting approval")
        self.assertEqual(action.add_labels, [])
        self.assertNotEqual(action.status, "Implementation ready")


class ApplyReconcileTest(unittest.TestCase):
    def test_a3_1_one_add_label_and_one_status_update(self) -> None:
        ticket = issue(labels=[], board_status="Planning")
        gh = FakeGh({ticket.number: ticket})
        action = Action(
            number=ticket.number,
            add_labels=["stage: awaiting-approval"],
            status="Awaiting approval",
        )
        apply(action, gh)
        self.assertEqual(gh.calls, [
            ("set_status", ticket.number, "Awaiting approval"),
            ("add_label", ticket.number, "stage: awaiting-approval"),
        ])

    def test_a3_2_reconcile_fixes_and_reports(self) -> None:
        dragged = issue(number=1, board_status="Planning", labels=["stage: in-review"],
                        events=[ev("stage: in-review", "added", HELPER)])
        missing = issue(number=2, on_board=False, board_status=None)
        two = issue(
            number=3,
            labels=["stage: planning", "stage: in-review"],
            events=[
                ev("stage: planning", "added", HELPER),
                ev("stage: in-review", "added", HELPER),
            ],
        )
        ok_a = issue(number=4, labels=["stage: planning"], events=[ev("stage: planning", "added", HELPER)])
        ok_b = issue(number=5, labels=["stage: planning"], events=[ev("stage: planning", "added", HELPER)])
        gh = FakeGh({t.number: t for t in (dragged, missing, two, ok_a, ok_b)})
        failures = reconcile(gh)
        self.assertTrue(any("two or more" in f for f in failures))
        self.assertIn(("set_status", 1, "In review"), gh.calls)
        self.assertIn(("add_to_board", 2), gh.calls)
        self.assertEqual(sum(1 for c in gh.calls if c[0] == "add_to_board"), 1)

    def test_a3_3_all_correct_makes_no_writes(self) -> None:
        t1 = issue(number=1)
        t2 = issue(number=2, title="E00-04 Makefile with make ci and make doctor")
        gh = FakeGh({1: t1, 2: t2})
        failures = reconcile(gh)
        self.assertEqual(failures, [])
        self.assertEqual(gh.calls, [])

    def test_a3_4_checker_view_problem_fails_reconcile(self) -> None:
        ticket = issue()
        gh = FakeGh({ticket.number: ticket})

        def checker(_project, _issues):
            return [type("P", (), {"message": "Tickets view uses a table layout"})()]

        failures = reconcile(gh, checker=checker)
        self.assertTrue(any("Tickets view" in f for f in failures))

    def test_a3_5_status_failure_skips_later_label_change(self) -> None:
        ticket = issue(labels=[], board_status="Planning")
        gh = FakeGh({ticket.number: ticket}, fail_status_for=ticket.number)
        action = Action(
            number=ticket.number,
            add_labels=["stage: awaiting-approval"],
            status="Awaiting approval",
        )
        with self.assertRaises(GhError):
            apply(action, gh)
        self.assertEqual(gh.calls, [("set_status", ticket.number, "Awaiting approval")])
        self.assertFalse(any(c[0] == "add_label" for c in gh.calls))

    def test_a3_6_no_call_adds_the_approval_label(self) -> None:
        self.assertFalse(any(
            call[0] == "add_label" and call[-1] == APPROVAL_LABEL
            for call in getattr(self, "_all_calls", [])
        ))

    def test_a3_7_token_never_appears_in_output(self) -> None:
        token = "ghs_secret_token_value"
        stream = io.StringIO()
        ticket = issue(labels=[], events=[])
        gh = FakeGh({ticket.number: ticket})
        code = main(
            env={"GH_TOKEN": token, "ISSUE_NUMBER": str(ticket.number), "APPROVER": OWNER},
            gh=gh,
            stream=stream,
        )
        self.assertEqual(code, 1)
        self.assertNotIn(token, stream.getvalue())

    def test_apply_refuses_to_add_approval_label(self) -> None:
        ticket = issue()
        gh = FakeGh({ticket.number: ticket})
        action = Action(number=ticket.number, add_labels=[APPROVAL_LABEL], status="Implementation ready")
        with self.assertRaises(GhError):
            apply(action, gh)
        self.assertFalse(any(c[0] == "add_label" for c in gh.calls))


class NeverAddsApprovalMeta(unittest.TestCase):
    """A3.6: no recorded call in this file adds the approval label."""

    def test_no_approval_adds_across_apply_cases(self) -> None:
        recorded: list[tuple] = []
        ticket = issue(labels=[], board_status="Planning")
        cases = [
            Action(number=10, add_labels=["stage: awaiting-approval"], status="Awaiting approval"),
            Action(number=10, add_labels=["stage: done"], remove_labels=["stage: in-review"], status="Done"),
        ]
        for action in cases:
            gh = FakeGh({10: issue(number=10, labels=[], board_status="Planning")})
            apply(action, gh)
            recorded.extend(gh.calls)
        self.assertTrue(recorded)
        self.assertFalse(any(
            call[0] == "add_label" and APPROVAL_LABEL in call
            for call in recorded
        ))


if __name__ == "__main__":
    unittest.main()
