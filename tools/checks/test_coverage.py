"""The two GitHub workflows together must run every make ci group."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import checks

ROOT = Path(__file__).resolve().parents[2]


def makefile_ci_targets(text: str) -> set[str]:
    return set(re.findall(r"^ci-([a-z0-9-]+):", text, re.M))


def workflow_ci_groups(texts: list[str]) -> list[str]:
    found = []
    for text in texts:
        found.extend(re.findall(r"(?m)^\s*run:\s*make ci-([a-z0-9-]+)", text))
    return found


def coverage_problems(check_list, makefile_text: str, workflow_texts: list[str]) -> list[str]:
    groups = []
    for _name, group, _cmd, _needs in check_list:
        if group not in groups:
            groups.append(group)
    targets = makefile_ci_targets(makefile_text)
    workflow_groups = workflow_ci_groups(workflow_texts)
    problems = []
    for group in groups:
        if group not in targets:
            problems.append("Makefile has no ci-%s target" % group)
        count = workflow_groups.count(group)
        if count == 0:
            problems.append("no workflow runs make ci-%s" % group)
        elif count > 1:
            problems.append("%s is run twice" % group)
    for group in targets:
        if group not in groups:
            problems.append("Makefile target ci-%s has no checks" % group)
    for group in set(workflow_groups):
        if group not in groups:
            problems.append("workflow runs make ci-%s, a group with no checks" % group)
    return problems


class CoverageTest(unittest.TestCase):
    def test_c2_1_real_files_match(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        workflows = [p.read_text() for p in sorted((ROOT / ".github" / "workflows").glob("*.yml"))]
        self.assertEqual(coverage_problems(checks.CHECKS, makefile, workflows), [])

    def test_c2_2_new_group_with_no_runner_fails(self) -> None:
        extra = checks.CHECKS + (("x", "extra", ["-m", "unittest"], ()),)
        makefile = (ROOT / "Makefile").read_text()
        workflows = [p.read_text() for p in sorted((ROOT / ".github" / "workflows").glob("*.yml"))]
        problems = coverage_problems(extra, makefile, workflows)
        self.assertTrue(any("extra" in p for p in problems))

    def test_c2_3_workflow_unknown_group_fails(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        problems = coverage_problems(checks.CHECKS, makefile, ["        run: make ci-missing\n"])
        self.assertTrue(any("missing" in p for p in problems))

    def test_c2_4_group_run_twice_fails(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        problems = coverage_problems(
            checks.CHECKS,
            makefile,
            ["        run: make ci-docs\n", "        run: make ci-docs\n        run: make ci-tooling\n"],
        )
        self.assertTrue(any("twice" in p for p in problems))

    def test_c2_5_missing_makefile_target_fails(self) -> None:
        makefile = "ci-docs:\n\t@echo docs\n"
        workflows = ["        run: make ci-docs\n        run: make ci-tooling\n"]
        problems = coverage_problems(checks.CHECKS, makefile, workflows)
        self.assertTrue(any("tooling" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
