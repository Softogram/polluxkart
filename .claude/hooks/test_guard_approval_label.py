"""Tests for the approval label guard hook.

Run with: python3 -m unittest discover -s .claude/hooks
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest import mock

import guard_approval_label as guard


def decision(command: str, tool: str = "Bash") -> str | None:
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(out):
        guard.main()
    text = out.getvalue().strip()
    return json.loads(text)["hookSpecificOutput"]["permissionDecision"] if text else None


class BlocksApprovalWrites(unittest.TestCase):
    def test_add_label_is_denied(self) -> None:
        self.assertEqual(decision('gh issue edit 42 --add-label "stage: implementation-ready"'), "deny")

    def test_create_with_label_is_denied(self) -> None:
        self.assertEqual(decision('gh issue create --title x --label "stage: implementation-ready"'), "deny")

    def test_pr_edit_is_denied(self) -> None:
        self.assertEqual(decision('gh pr edit 3 --add-label "stage: implementation-ready"'), "deny")

    def test_renaming_or_deleting_the_label_is_denied(self) -> None:
        self.assertEqual(decision('gh label edit "stage: implementation-ready" --name approved'), "deny")
        self.assertEqual(decision('gh label delete "stage: implementation-ready" --yes'), "deny")

    def test_rest_api_write_is_denied(self) -> None:
        self.assertEqual(decision('gh api repos/o/r/issues/42/labels -f "labels[]=stage: implementation-ready"'), "deny")
        self.assertEqual(decision('gh api -X POST repos/o/r/issues/42/labels --input labels-implementation-ready.json'), "deny")

    def test_graphql_mutation_is_denied(self) -> None:
        self.assertEqual(decision("gh api graphql -f query='mutation { addLabelsToLabelable(input:{labelableId:\"x\", labelIds:[\"implementation-ready\"]}) { clientMutationId } }'"), "deny")

    def test_curl_write_is_denied(self) -> None:
        self.assertEqual(decision('curl -X POST https://api.github.com/repos/o/r/issues/42/labels -d \'{"labels":["stage: implementation-ready"]}\''), "deny")

    def test_chained_write_after_a_read_is_denied(self) -> None:
        self.assertEqual(decision('gh issue list --label "stage: planning" && gh issue edit 42 --add-label "stage: implementation-ready"'), "deny")


class AllowsEverythingElse(unittest.TestCase):
    def test_listing_by_the_label_is_allowed(self) -> None:
        self.assertIsNone(decision('gh issue list --label "stage: implementation-ready"'))

    def test_viewing_and_searching_is_allowed(self) -> None:
        self.assertIsNone(decision('gh search issues "label:\\"stage: implementation-ready\\"" --repo o/r'))
        self.assertIsNone(decision("gh api 'repos/o/r/issues?labels=stage:%20implementation-ready'"))
        self.assertIsNone(decision("gh api graphql -f query='query { repository(owner:\"o\", name:\"r\") { label(name:\"stage: implementation-ready\") { name } } }'"))

    def test_other_labels_are_allowed(self) -> None:
        self.assertIsNone(decision('gh issue edit 42 --add-label "stage: awaiting-approval" --remove-label "stage: planning"'))

    def test_non_github_commands_mentioning_the_words_are_allowed(self) -> None:
        self.assertIsNone(decision("grep -rn implementation-ready docs"))

    def test_other_tools_are_ignored(self) -> None:
        self.assertIsNone(decision('gh issue edit 42 --add-label "stage: implementation-ready"', tool="Read"))


if __name__ == "__main__":
    unittest.main()
