"""Checks on the board-sync workflow file itself."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "board-sync.yml"


class WorkflowFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text()

    def test_w4_1_triggers(self) -> None:
        for needle in (
            "opened",
            "edited",
            "labeled",
            "unlabeled",
            "closed",
            "reopened",
            "schedule:",
            "workflow_dispatch:",
        ):
            self.assertIn(needle, self.text)
        self.assertIn("issues:", self.text)
        self.assertIn('cron: "15 21 * * *"', self.text)

    def test_w4_2_contents_read_only(self) -> None:
        self.assertIn("contents: read", self.text)
        self.assertNotIn("contents: write", self.text)
        self.assertNotIn("issues: write", self.text)
        self.assertNotIn("projects: write", self.text)

    def test_w4_3_issue_title_and_body_stay_out_of_run_lines(self) -> None:
        self.assertNotIn("github.event.issue.title", self.text)
        self.assertNotIn("github.event.issue.body", self.text)
        copy = self.text + "\n      - run: echo ${{ github.event.issue.title }}\n"
        self.assertIn("github.event.issue.title", copy)
        self.assertNotEqual(copy, self.text)

    def test_w4_4_concurrency_queues_per_issue(self) -> None:
        self.assertIn("group: board-sync-${{ github.event.issue.number || 'reconcile' }}", self.text)
        self.assertIn("cancel-in-progress: false", self.text)

    def test_w4_5_actions_are_pinned(self) -> None:
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", self.text)
        self.assertIn("actions/create-github-app-token@fee1f7d63c2ff003460e3d139729b119787bc349", self.text)
        for line in self.text.splitlines():
            if "uses: actions/" in line:
                self.assertRegex(line, r"@[0-9a-f]{40}")


if __name__ == "__main__":
    unittest.main()
