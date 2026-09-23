"""Tests that CLAUDE.md stays true and readable.

Test plan: docs/design/test/issue-39-claude-md-commands.md

Agents act on what CLAUDE.md says, so a command named there that does not
exist wastes a whole task. These checks fail when:

1. CLAUDE.md names a `make` target the Makefile does not define;
2. a Makefile target has no `##` help comment, so `make help` would be
   an incomplete list;
3. a line of CLAUDE.md holds two sentences, because the writing rule is
   one sentence per line.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make_help  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_MD = ROOT / "CLAUDE.md"
MAKEFILE = ROOT / "Makefile"

# `make <target>` inside inline code or a fenced block. Prose such as
# "to make a change" is not in code formatting, so it never matches.
MAKE_COMMAND_RE = re.compile(r"`make\s+([A-Za-z0-9][A-Za-z0-9_.-]*)[^`]*`")
FENCE_RE = re.compile(r"^\s*```")

# A full stop, question mark or exclamation mark, then a space, then a
# capital letter: two sentences on one line. Bold and italic markers may
# sit between them, as in "**...decision.** If the answer".
TWO_SENTENCES_RE = re.compile(r"[.!?][\"')\]]?[*_]{0,2}\s+[A-Z]")
# Endings that are not the end of a sentence.
ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "vs.", "Mr.", "Ms.", "Dr.", "No.")

# Targets that exist only to configure make itself.
NOT_A_COMMAND = (".PHONY", ".DEFAULT_GOAL")


def make_targets(makefile_text):
    return dict(make_help.targets(makefile_text))


def claude_md_make_commands(text):
    """Every `make <target>` named in CLAUDE.md, with its line number."""
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        for match in MAKE_COMMAND_RE.finditer(line):
            found.append((match.group(1), number))
    return found


def _outside_code(text):
    """Lines that are not inside a fenced code block, with their numbers."""
    rows = []
    inside = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            rows.append((number, line))
    return rows


def two_sentence_lines(text):
    """Lines holding more than one sentence, which the writing rule forbids."""
    problems = []
    for number, line in _outside_code(text):
        stripped = line.strip()
        if not stripped or stripped.startswith("|") or stripped.startswith(">"):
            continue
        cleaned = stripped
        for short in ABBREVIATIONS:
            cleaned = cleaned.replace(short, "_" * len(short))
        # A version number such as 3.81 is a full stop between digits.
        cleaned = re.sub(r"(\d)\.(\d)", r"\1_\2", cleaned)
        # An inline code span may hold a sentence-shaped string of its own.
        cleaned = re.sub(r"`[^`]*`", lambda m: "_" * len(m.group(0)), cleaned)
        if TWO_SENTENCES_RE.search(cleaned):
            problems.append("CLAUDE.md:%s holds two sentences; put each on its own line" % number)
    return problems


class ClaudeMdTest(unittest.TestCase):
    def setUp(self):
        self.text = CLAUDE_MD.read_text()
        self.makefile = MAKEFILE.read_text()

    def test_every_make_command_named_in_claude_md_exists(self):
        defined = make_help.all_target_names(self.makefile)
        problems = [
            "CLAUDE.md:%s names `make %s`, which the Makefile does not define" % (line, name)
            for name, line in claude_md_make_commands(self.text)
            if name not in defined
        ]
        self.assertEqual(problems, [])

    def test_an_invented_target_is_caught(self):
        """The passing partner for the test above."""
        defined = make_help.all_target_names(self.makefile)
        invented = claude_md_make_commands("Run `make no-such-target` first.\n")
        self.assertEqual(invented, [("no-such-target", 1)])
        self.assertNotIn("no-such-target", defined)

    def test_prose_using_the_word_make_is_not_a_command(self):
        self.assertEqual(claude_md_make_commands("You need to make a change first.\n"), [])

    def test_every_target_has_a_help_comment(self):
        documented = make_targets(self.makefile)
        missing = [
            name
            for name in make_help.all_target_names(self.makefile)
            if name not in documented and name not in NOT_A_COMMAND
        ]
        self.assertEqual(missing, [], "add a ## help comment to these targets")

    def test_a_target_without_help_is_caught(self):
        text = "one: ## does one\n\ttrue\n\ntwo:\n\ttrue\n"
        documented = make_targets(text)
        self.assertIn("one", documented)
        self.assertNotIn("two", documented)
        self.assertEqual(make_help.all_target_names(text), ["one", "two"])

    def test_make_help_lists_every_target(self):
        printed = subprocess.run(
            ["make", "help"], cwd=str(ROOT), capture_output=True, text=True
        )
        self.assertEqual(printed.returncode, 0, printed.stderr)
        for name in make_help.all_target_names(self.makefile):
            if name in NOT_A_COMMAND:
                continue
            self.assertIn("make %s " % name, printed.stdout)

    def test_claude_md_has_one_sentence_per_line(self):
        self.assertEqual(two_sentence_lines(self.text), [])

    def test_two_sentences_on_one_line_are_caught(self):
        problems = two_sentence_lines("This is one. This is two.\n")
        self.assertEqual(len(problems), 1)
        self.assertIn("two sentences", problems[0])

    def test_abbreviations_and_versions_are_not_two_sentences(self):
        self.assertEqual(two_sentence_lines("Use make 3.81 or newer, e.g. GNU Make.\n"), [])

    def test_code_blocks_are_not_checked_for_sentences(self):
        text = "```\nThis is one. This is two.\n```\n"
        self.assertEqual(two_sentence_lines(text), [])

    def test_rule_one_is_unchanged(self):
        """Rule one is owned by E00-01, and this ticket must not touch its words.

        Line breaks may move, because the writing rule puts one sentence on
        each line, so the wording is compared with the line breaks ironed out.
        """
        flat = " ".join(self.text.split())
        self.assertIn(
            "**Only tickets the owner labelled `stage: implementation-ready` may be implemented.**",
            flat,
        )
        self.assertIn(
            "Owner rule, 2026-09-13. It overrides every other instruction in this repository.",
            flat,
        )
        self.assertIn(
            "The owner (GitHub `CosmicSaaurabh`) makes every product and design decision.",
            flat,
        )

    def test_the_commands_section_lists_the_everyday_commands(self):
        self.assertIn("## Commands", self.text)
        for command in ("`make doctor`", "`make ci`", "`make help`"):
            self.assertIn(command, self.text)


if __name__ == "__main__":
    unittest.main()
