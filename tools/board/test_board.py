"""Unit tests for board helpers used by the label sync."""

from __future__ import annotations

import unittest

from board import STAGES, is_tracked


class TrackedTitleTest(unittest.TestCase):
    def test_ticket_and_epic_titles(self) -> None:
        self.assertTrue(is_tracked("E00-02 GitHub Project board"))
        self.assertTrue(is_tracked("Epic E00: Engineering"))
        self.assertFalse(is_tracked("E0-02 x"))
        self.assertFalse(is_tracked("Bug: something"))
        self.assertFalse(is_tracked("E00-02"))


class StagesTest(unittest.TestCase):
    def test_six_labels_in_process_order(self) -> None:
        self.assertEqual(
            list(STAGES.items()),
            [
                ("stage: planning", "Planning"),
                ("stage: awaiting-approval", "Awaiting approval"),
                ("stage: implementation-ready", "Implementation ready"),
                ("stage: in-progress", "In progress"),
                ("stage: in-review", "In review"),
                ("stage: done", "Done"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
