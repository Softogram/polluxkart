#!/usr/bin/env python3
"""Print every make target and what it does, read from the Makefile.

`make help` is the full list of commands (owner decision, 2026-09-14), so
it is generated rather than hand written. A hand-written list drifts from
the targets that really exist, and then an agent runs a command that is
not there.

A target describes itself with a `## ` comment on its own line:

    ci: ## run every check a pull request must pass

Make itself only runs this script, so this works with GNU Make 3.81, which
is what macOS ships.
"""

from __future__ import annotations

import re
import sys

TARGET_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)\s*:[^=]*?##\s*(.*)$")
CONTINUATION_RE = re.compile(r"^##\s+(.*)$")


def targets(makefile_text):
    """Every target with a help comment, in the order the Makefile lists them.

    A `##` line on its own after a target adds a second line to its help,
    which is how a target explains an option it takes.
    """
    found = []
    for line in makefile_text.splitlines():
        match = TARGET_RE.match(line)
        if match:
            found.append((match.group(1), [match.group(2).strip()]))
            continue
        extra = CONTINUATION_RE.match(line)
        if extra and found:
            found[-1][1].append(extra.group(1).strip())
    return found


def all_target_names(makefile_text):
    """Every target the Makefile defines, whether or not it has help."""
    names = []
    for line in makefile_text.splitlines():
        if line.startswith("\t") or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)\s*:(?!=)", line)
        if match and match.group(1) not in names:
            names.append(match.group(1))
    return names


def format_help(found):
    if not found:
        return ""
    width = max(len(name) for name, _lines in found)
    out = []
    for name, lines in found:
        out.append("make %-*s  %s" % (width, name, lines[0]))
        for extra in lines[1:]:
            out.append("     %-*s  %s" % (width, "", extra))
    return "\n".join(out)


def main(argv=None, stream=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    stream = sys.stdout if stream is None else stream
    path = argv[0] if argv else "Makefile"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as error:
        sys.stderr.write("%s\n" % error)
        return 1
    stream.write(format_help(targets(text)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
