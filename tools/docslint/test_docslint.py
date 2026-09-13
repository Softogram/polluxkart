"""Tests for docslint: each rule is shown to catch the problem it exists for.

Run with: python3 -m unittest discover -s tools/docslint
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import docslint


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class DocslintTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write(self.root, "docs/README.md", "# Index\n\n## Read next\n\n- [a](a/README.md)\n")
        write(self.root, "docs/a/README.md", "# A\n\nParent: [docs/](../README.md)\n\n## Read next\n\n- [leaf](leaf.md)\n")
        write(self.root, "docs/a/leaf.md", "# Leaf\n\nParent: [a/](README.md)\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def problems(self) -> list[str]:
        return docslint.check(self.root).problems

    def test_clean_tree_passes(self) -> None:
        self.assertEqual(self.problems(), [])

    def test_broken_link_is_reported(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\nSee [missing](nope.md).\n")
        self.assertTrue(any("broken link: nope.md" in p for p in self.problems()))

    def test_read_next_pointing_upward_is_reported(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\n## Read next\n\n- [up](../README.md)\n")
        self.assertTrue(any("must point downward" in p for p in self.problems()))

    def test_dated_read_next_heading_counts_as_read_next(self) -> None:
        write(self.root, "docs/a/README.md", "# A\n\n## Read next - approved 2026-09-13\n\n- [leaf](leaf.md)\n")
        self.assertEqual(self.problems(), [])
        write(self.root, "docs/a/leaf.md", "# Leaf\n\n## Read next - later\n\n- [up](../README.md)\n")
        self.assertTrue(any("must point downward" in p for p in self.problems()))

    def test_see_also_may_point_upward(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\n## See also (do not follow recursively)\n\n- [up](../README.md)\n")
        self.assertEqual(self.problems(), [])

    def test_cycle_within_a_folder_is_reported(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\n## Read next\n\n- [two](two.md)\n")
        write(self.root, "docs/a/two.md", "# Two\n\n## Read next\n\n- [leaf](leaf.md)\n")
        self.assertTrue(any("cycle" in p for p in self.problems()))

    def test_unreachable_document_is_reported(self) -> None:
        write(self.root, "docs/a/orphan.md", "# Orphan\n")
        self.assertTrue(any("orphan.md: not reachable" in p for p in self.problems()))

    def test_em_dash_is_reported(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\nOne — two.\n")
        self.assertTrue(any("em dash" in p for p in self.problems()))

    def test_links_inside_code_are_ignored(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\n```\n[x](nope.md)\n```\n\nInline `[y](nope.md)` too.\n")
        self.assertEqual(self.problems(), [])

    def test_folder_link_resolves_to_its_readme(self) -> None:
        write(self.root, "docs/README.md", "# Index\n\n## Read next\n\n- [a](a/)\n")
        self.assertEqual(self.problems(), [])

    def test_external_links_are_not_checked(self) -> None:
        write(self.root, "docs/a/leaf.md", "# Leaf\n\n[site](https://example.com) and [mail](mailto:x@example.com).\n")
        self.assertEqual(self.problems(), [])


if __name__ == "__main__":
    unittest.main()
