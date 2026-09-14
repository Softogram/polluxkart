# Test plan: E00-02 GitHub Project board with a column per stage

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #32 (E00-02).
Design: [../low-level/issue-32-project-board.md](../low-level/issue-32-project-board.md)

This ticket has no web requests.
Its flows are the checker, `make board-check`, and the board's settings and views on GitHub.
Terms such as project, board, view, field and parent issue are explained at the top of the design.

## Words used below

- **Fake `gh`:** a small Python object standing in for the GitHub CLI in unit tests, returning prepared project and issue data.
- **Passing partner:** the matching test that passes, proving a failing test fails for the intended reason.

## How these tests run

- Unit tests are standard library `unittest` files in `tools/board/`, run by the `board-tests` check in `make ci` and the `tooling-tests` workflow. They never call GitHub.
- The live check is `make board-check` against the real board, run after the owner finishes the settings and views, with its output pasted into the implementation pull request.

## Flow 1: `compare` (unit tests with a fake `gh`)

| Id | Fake data | Expected |
|---|---|---|
| B1.1 | Three tracked issues, each on the board once with the Status matching its one stage label; public board named PolluxKart; both views as designed | No problems; exit 0 |
| B1.2 | As B1.1, one issue missing from the board | One problem naming the issue. Partner: B1.1 (AC2) |
| B1.3 | One issue on the board twice | Problem naming it (AC2) |
| B1.4 | A board item whose title is not `EXX-NN ...` or `Epic EXX: ...` | Problem naming it |
| B1.5 | An issue with no stage label | Problem naming it; not silently placed (ticket's test list) |
| B1.6 | An issue with two stage labels | Problem naming it and both labels (ticket's test list) |
| B1.7 | An issue labelled `stage: in-review` whose Status is In progress | Problem naming both values (AC3) |
| B1.8 | Board private | Problem "board is not public" (AC5) |
| B1.9 | Board renamed | Problem naming the name found (AC5) |
| B1.10 | The Tickets view uses a table layout | Problem naming the view and layout |
| B1.11 | The Tickets view filter lacks `-label:epic` | Problem naming the filter |
| B1.12 | The Tickets view hides Parent issue | Problem naming the missing field |
| B1.13 | The Epics view is missing | Problem naming it |
| B1.14 | The Status options out of stage order, or one renamed | Problem listing the expected order (AC1) |
| B1.15 | Several problems at once | All listed, not only the first |

## Flow 2: helpers (unit tests)

| Id | Case | Expected |
|---|---|---|
| H2.1 | `is_tracked` on `E00-02 GitHub Project board`, `Epic E00: Engineering`, `E0-02 x`, `Bug: something`, `E00-02` with no name | True, True, False, False, False |
| H2.2 | `STAGES` | Exactly the six labels in the order of development-process.md, mapped to the six Status options |
| H2.3 | The fake `gh` returns a page cursor | Every page is read, so a board with more than 100 items is fully checked |
| H2.4 | The fake `gh` raises an error (offline, not logged in) | `main` exits 1 with the error, never reports success |

## Flow 3: the live board (by hand, once)

| Id | Action | Expected | Acceptance criterion |
|---|---|---|---|
| L3.1 | Owner sets visibility, description and readme; creates the two views as designed | Done in the website | Setup |
| L3.2 | `make board-check` | Exit 0, "every tracked issue is on the board once with a matching status; settings and views match" | AC1 to AC5 |
| L3.3 | Open `https://github.com/orgs/Softogram/projects/2` in a private browser window, signed out | The board is visible, showing the Tickets view with six columns in stage order and no epic cards | Public; epics separate |
| L3.4 | Open the Epics view signed out | 21 epics with progress bars | Epics view |
| L3.5 | Temporarily change one card's Status by hand, run `make board-check`, then change it back and run again | First run names the mismatch and exits 1; second run exits 0 | The live checker really detects drift |

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #32, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: exactly six stage columns, in order | B1.14, H2.2, L3.3 |
| AC2: every ticket and epic appears once | B1.2, B1.3, L3.2 |
| AC3: each card's column matches its label | B1.7, L3.2, L3.5 |
| AC4: the board is linked from development-process.md | docslint checks the link exists and is well-formed; reviewed in the pull request |
| AC5: name, visibility, edit access and fields match the owner's answers | B1.8 to B1.13, L3.2, L3.3; edit access is checked by hand in project settings |

## What the owner gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| GitHub API | Offline, not logged in, rate limited | Exit 1 with the error | H2.4 |
| GitHub website | A view setting cannot be read through the API | The checker reports "could not read view settings" as a problem, never as a match | B1.10 to B1.13 use the fields the API does return; confirmed live in L3.2 |

## Reachability check

No database rows are written.
The equivalent risk is a checker that passes because it read nothing: B1.1's partners prove each rule fires, and L3.5 proves the live run reads the real board.

## What is deliberately not covered, and why

- **Automatic card moves:** #33.
- **Who can edit the project, through the API:** GitHub does not expose it reliably; the runbook lists a manual check.
- **The board's appearance:** GitHub renders it; L3.3 and L3.4 are the human check.
