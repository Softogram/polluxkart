"""Tests for the approval gate: each rule is shown passing and failing.

Run with: python3 -m unittest discover -s tools/approval_gate
"""

from __future__ import annotations

import unittest

from gate import APPROVAL_LABEL, LabelEvent, Ticket, evaluate

OWNER = "CosmicSaaurabh"
CONTRIBUTOR = "someone-else"


def approved_ticket(number: int = 42, stage: str = APPROVAL_LABEL, **overrides) -> Ticket:
    ticket = Ticket(
        number=number,
        labels=[stage, "Feature"],
        label_events=[LabelEvent("stage: planning", OWNER), LabelEvent(APPROVAL_LABEL, OWNER)],
    )
    for key, value in overrides.items():
        setattr(ticket, key, value)
    return ticket


def run(body: str, files: list[str], tickets: dict[int, Ticket], author: str = CONTRIBUTOR):
    return evaluate(author=author, body=body, files=files, tickets=tickets, approver=OWNER)


class LinkingTest(unittest.TestCase):
    def test_no_ticket_reference_fails(self) -> None:
        result = run("Adds things", ["api/order/src/main/X.java"], {})
        self.assertFalse(result.ok)
        self.assertIn("Implements #N", result.messages[0])

    def test_both_kinds_of_reference_fail(self) -> None:
        result = run("Implements #42\nPlans #43", ["docs/a.md"], {42: approved_ticket(), 43: approved_ticket(43)})
        self.assertFalse(result.ok)

    def test_reference_must_be_on_its_own_line(self) -> None:
        result = run("This Implements #42 inline", ["api/x/src/main/A.java"], {42: approved_ticket()})
        self.assertFalse(result.ok)

    def test_dependabot_is_exempt(self) -> None:
        result = run("Bumps a dependency", ["web/package.json"], {}, author="dependabot[bot]")
        self.assertTrue(result.ok)


class PlanningTest(unittest.TestCase):
    def test_documents_only_passes_for_a_planning_ticket(self) -> None:
        ticket = Ticket(number=7, labels=["stage: planning"])
        result = run("Plans #7", ["docs/design/low-level/issue-7-x.md", "docs/platform/decisions.md"], {7: ticket})
        self.assertTrue(result.ok, result.messages)

    def test_planning_pull_request_cannot_change_code(self) -> None:
        ticket = Ticket(number=7, labels=["stage: planning"])
        result = run("Plans #7", ["docs/a.md", "api/order/src/main/A.java"], {7: ticket})
        self.assertFalse(result.ok)
        self.assertTrue(any("only Markdown" in m for m in result.messages))

    def test_planning_pull_request_cannot_close_its_ticket(self) -> None:
        ticket = Ticket(number=7, labels=["stage: planning"])
        result = run("Plans #7\n\nCloses #7", ["docs/a.md"], {7: ticket})
        self.assertFalse(result.ok)

    def test_planning_a_closed_or_missing_ticket_fails(self) -> None:
        self.assertFalse(run("Plans #7", ["docs/a.md"], {7: Ticket(number=7, state="closed")}).ok)
        self.assertFalse(run("Plans #8", ["docs/a.md"], {8: Ticket(number=8, exists=False)}).ok)
        self.assertFalse(run("Plans #9", ["docs/a.md"], {9: Ticket(number=9, is_pull_request=True)}).ok)


class ImplementationTest(unittest.TestCase):
    code_and_tests = ["api/order/src/main/Order.java", "api/order/src/test/OrderTest.java"]

    def test_owner_approved_ticket_passes(self) -> None:
        result = run("Implements #42\nCloses #42", self.code_and_tests, {42: approved_ticket()})
        self.assertTrue(result.ok, result.messages)

    def test_in_progress_and_in_review_after_approval_pass(self) -> None:
        for stage in ("stage: in-progress", "stage: in-review"):
            ticket = approved_ticket(stage=stage)
            ticket.label_events.append(LabelEvent(stage, CONTRIBUTOR))
            self.assertTrue(run("Implements #42", self.code_and_tests, {42: ticket}).ok, stage)

    def test_planning_ticket_fails(self) -> None:
        ticket = Ticket(number=42, labels=["stage: planning"], label_events=[LabelEvent("stage: planning", OWNER)])
        result = run("Implements #42", self.code_and_tests, {42: ticket})
        self.assertFalse(result.ok)

    def test_label_applied_by_someone_else_fails(self) -> None:
        ticket = Ticket(
            number=42,
            labels=[APPROVAL_LABEL],
            label_events=[LabelEvent("stage: planning", OWNER), LabelEvent(APPROVAL_LABEL, CONTRIBUTOR)],
        )
        result = run("Implements #42", self.code_and_tests, {42: ticket})
        self.assertFalse(result.ok)
        self.assertTrue(any("not by the owner" in m for m in result.messages))

    def test_revoked_approval_fails_even_if_stage_later_set_to_in_progress(self) -> None:
        ticket = Ticket(
            number=42,
            labels=["stage: in-progress"],
            label_events=[
                LabelEvent(APPROVAL_LABEL, OWNER),
                LabelEvent("stage: planning", OWNER),
                LabelEvent("stage: in-progress", CONTRIBUTOR),
            ],
        )
        result = run("Implements #42", self.code_and_tests, {42: ticket})
        self.assertFalse(result.ok)
        self.assertTrue(any("not approved now" in m for m in result.messages))

    def test_two_stage_labels_fail(self) -> None:
        ticket = approved_ticket()
        ticket.labels.append("stage: planning")
        self.assertFalse(run("Implements #42", self.code_and_tests, {42: ticket}).ok)

    def test_closed_ticket_fails(self) -> None:
        self.assertFalse(run("Implements #42", self.code_and_tests, {42: approved_ticket(state="closed")}).ok)

    def test_more_than_one_implemented_ticket_fails(self) -> None:
        result = run("Implements #42\nImplements #43", self.code_and_tests, {42: approved_ticket(), 43: approved_ticket(43)})
        self.assertFalse(result.ok)

    def test_closing_another_ticket_fails(self) -> None:
        result = run("Implements #42\nCloses #42\nFixes #50", self.code_and_tests, {42: approved_ticket()})
        self.assertFalse(result.ok)

    def test_backend_code_without_tests_fails(self) -> None:
        result = run("Implements #42", ["api/order/src/main/Order.java"], {42: approved_ticket()})
        self.assertFalse(result.ok)
        self.assertTrue(any("api/**/src/test/" in m for m in result.messages))

    def test_frontend_code_without_tests_fails_and_passes_with_e2e(self) -> None:
        self.assertFalse(run("Implements #42", ["web/src/app/page.tsx"], {42: approved_ticket()}).ok)
        self.assertTrue(run("Implements #42", ["web/src/app/page.tsx", "e2e/checkout.spec.ts"], {42: approved_ticket()}).ok)
        self.assertTrue(run("Implements #42", ["web/src/app/page.tsx", "web/src/app/page.test.tsx"], {42: approved_ticket()}).ok)

    def test_tooling_change_needs_approval_but_no_test_rule(self) -> None:
        self.assertTrue(run("Implements #42", ["Makefile", ".github/workflows/ci.yml"], {42: approved_ticket()}).ok)
        unapproved = Ticket(number=42, labels=["stage: planning"], label_events=[LabelEvent("stage: planning", OWNER)])
        self.assertFalse(run("Implements #42", ["Makefile"], {42: unapproved}).ok)

    def test_docs_only_implementation_still_needs_approval(self) -> None:
        unapproved = Ticket(number=42, labels=["stage: planning"], label_events=[LabelEvent("stage: planning", OWNER)])
        self.assertFalse(run("Implements #42", ["docs/platform/runbook.md"], {42: unapproved}).ok)


class ReleasePullRequestTest(unittest.TestCase):
    def test_development_into_main_passes(self) -> None:
        result = evaluate(
            author=CONTRIBUTOR,
            body="Release",
            files=["Makefile"],
            tickets={},
            approver=OWNER,
            base_ref="main",
            head_ref="development",
            head_repository="Softogram/polluxkart",
            repository="Softogram/polluxkart",
        )
        self.assertTrue(result.ok)
        self.assertIn("Release pull request from development into main", result.messages)

    def test_feature_into_main_fails(self) -> None:
        result = evaluate(
            author=CONTRIBUTOR,
            body="Implements #42",
            files=["Makefile"],
            tickets={42: approved_ticket()},
            approver=OWNER,
            base_ref="main",
            head_ref="feature/x",
            head_repository="Softogram/polluxkart",
            repository="Softogram/polluxkart",
        )
        self.assertFalse(result.ok)

    def test_fork_development_into_main_fails(self) -> None:
        result = evaluate(
            author=CONTRIBUTOR,
            body="Release",
            files=["Makefile"],
            tickets={},
            approver=OWNER,
            base_ref="main",
            head_ref="development",
            head_repository="other/polluxkart",
            repository="Softogram/polluxkart",
        )
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
