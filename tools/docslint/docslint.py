#!/usr/bin/env python3
"""Check that the docs tree follows the rules in docs/README.md.

The rules, and why each exists:

1. Every relative link points at a file or folder that exists.
   A broken link sends a reader, or an agent, nowhere.
2. Links under a "## Read next" heading point downward only: into the same
   folder or below it, never sideways or up. Following them therefore cannot
   loop, which is what makes "follow Read next" safe advice.
3. The "Read next" links form no cycle, even within one folder.
4. Every markdown file under docs/ can be reached from docs/README.md by
   following "Read next" links. A document nobody can reach is a document
   nobody reads.
5. No em dash character appears in the checked files (a house writing rule).

Standard library only, so it runs anywhere Python 3.10+ runs.

Usage:
    python3 tools/docslint/docslint.py            # check the repository
    python3 tools/docslint/docslint.py --root DIR # check another checkout
Exit code 0 means clean; 1 means problems were printed.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

EM_DASH = "—"

# Markdown files outside docs/ whose links and em dashes are also checked.
EXTRA_FILES = ("README.md", "legacy/README.md")
EXTRA_GLOBS = ("ops/**/*.md", "tools/**/*.md", ".claude/skills/README.md")

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


@dataclass
class Report:
    problems: list[str] = field(default_factory=list)

    def add(self, path: Path, root: Path, message: str) -> None:
        self.problems.append(f"{path.relative_to(root)}: {message}")


def strip_code(text: str) -> list[str]:
    """Return the file's lines with fenced code blocks and inline code blanked.

    Links and dashes inside code samples are examples, not navigation.
    """
    lines = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            lines.append("")
            continue
        if in_fence:
            lines.append("")
            continue
        lines.append(re.sub(r"`[^`]*`", "", line))
    return lines


def links_by_section(lines: list[str]) -> list[tuple[str, str]]:
    """Return (section heading, link target) pairs for every link in the file."""
    section = ""
    found = []
    for line in lines:
        heading = HEADING_RE.match(line)
        if heading:
            section = heading.group(2).strip().lower()
            continue
        for target in LINK_RE.findall(line):
            found.append((section, target))
    return found


def is_read_next(section: str) -> bool:
    """True for "Read next" and dated variants like "Read next - approved 2026-09-13"."""
    return section == "read next" or section.startswith("read next ")


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", target)) or target.startswith("#")


def resolve(source: Path, target: str) -> Path:
    """Resolve a relative link to a path; a folder link means its README.md."""
    clean = target.split("#", 1)[0]
    path = (source.parent / clean).resolve()
    if path.is_dir():
        path = path / "README.md"
    return path


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def check(root: Path) -> Report:
    report = Report()
    root = root.resolve()
    docs = root / "docs"
    index = docs / "README.md"
    if not index.is_file():
        report.problems.append("docs/README.md: missing entry point")
        return report

    doc_files = sorted(p.resolve() for p in docs.rglob("*.md"))
    checked = list(doc_files)
    for name in EXTRA_FILES:
        path = (root / name).resolve()
        if path.is_file():
            checked.append(path)
    for pattern in EXTRA_GLOBS:
        checked.extend(p.resolve() for p in root.glob(pattern) if p.is_file())
    checked = sorted(set(checked))

    read_next: dict[Path, list[Path]] = {}
    for path in checked:
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if EM_DASH in line:
                report.add(path, root, f"line {number}: em dash; use a plain hyphen")
        lines = strip_code(text)
        edges = []
        for section, target in links_by_section(lines):
            if is_external(target):
                continue
            resolved = resolve(path, target)
            if not resolved.exists():
                report.add(path, root, f"broken link: {target}")
                continue
            if is_read_next(section) and is_within(path, docs):
                if not is_within(resolved, path.parent):
                    report.add(
                        path, root,
                        f"'Read next' link must point downward, not to {target}; "
                        "use 'See also' for sideways or upward links",
                    )
                    continue
                if resolved.suffix == ".md":
                    edges.append(resolved)
        if is_within(path, docs):
            read_next[path] = edges

    # Rule 3: no cycles among Read next links.
    state: dict[Path, int] = {}

    def visit(node: Path, trail: list[Path]) -> None:
        state[node] = 1
        for nxt in read_next.get(node, []):
            if state.get(nxt) == 1:
                cycle = trail[trail.index(nxt):] + [nxt] if nxt in trail else [node, nxt]
                shown = " -> ".join(str(p.relative_to(root)) for p in cycle)
                report.problems.append(f"'Read next' cycle: {shown}")
            elif state.get(nxt) is None:
                visit(nxt, trail + [nxt])
        state[node] = 2

    for node in read_next:
        if state.get(node) is None:
            visit(node, [node])

    # Rule 4: everything under docs/ is reachable from the index.
    reached = {index}
    frontier = [index]
    while frontier:
        node = frontier.pop()
        for nxt in read_next.get(node, []):
            if nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)
    for path in doc_files:
        if path not in reached:
            report.add(path, root, "not reachable from docs/README.md through 'Read next' links")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = check(root)
    if report.problems:
        print(f"docslint: {len(report.problems)} problem(s)")
        for problem in report.problems:
            print(f"  {problem}")
        return 1
    print("docslint: docs tree is clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
