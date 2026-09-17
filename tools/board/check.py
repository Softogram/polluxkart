#!/usr/bin/env python3
"""Check the live PolluxKart project board against stage labels.

Changes nothing. Run with `make board-check`.
"""

from __future__ import annotations

import sys

from board import GhError, RealGh, compare, fetch_project, fetch_tracked_issues

OK = "every tracked issue is on the board once with a matching status; settings and views match"


def main(argv=None, gh=None):
    try:
        client = gh if gh is not None else RealGh()
        project = fetch_project(client)
        issues = fetch_tracked_issues(client)
        problems = compare(project, issues)
    except GhError as error:
        sys.stderr.write("%s\n" % error)
        return 1
    if problems:
        for problem in problems:
            sys.stdout.write("%s\n" % problem.message)
        return 1
    sys.stdout.write(OK + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
