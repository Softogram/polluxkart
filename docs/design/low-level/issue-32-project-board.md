# E00-02 GitHub Project board with a column per stage

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #32 (E00-02), part of epic #10.
Test plan: [../test/issue-32-project-board.md](../test/issue-32-project-board.md)
Depends on: #34 (`make ci`), for the checker's tests.

## Words used below

- **GitHub Project:** GitHub's built-in planning tool. It holds issues as items and shows them as tables or boards.
- **Board:** a view of a project with one column per value of a field, here the stage.
- **View:** one saved way of looking at a project, such as a board of tickets or a table of epics. A project can have several.
- **Field:** a piece of information on each item, such as Status, Assignees or Parent issue.
- **Parent issue:** the epic a ticket hangs under, through GitHub's native sub-issue link.
- **Item:** one issue placed on the project.

## What was already decided before this document

- **A GitHub Project board with a column per stage, every epic and ticket created at once and starting in planning** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Nothing is implemented without the owner's approval").
- **Six stages, each a label, exactly one per ticket** (same entry).
- **How the board is set up** (owner decision, 2026-09-14, "Project board", answered while planning this ticket):
  - the board is public;
  - it keeps its name, "PolluxKart";
  - epics appear in a separate view with their progress, not on the ticket board;
  - ticket cards show the epic, assignees, linked pull requests and the `owner-action` label;
  - only the owner edits the board; cards move by the label sync (#33).

## What exists already (checked 2026-09-14)

The board was created on 2026-09-13, when the epics and tickets were created.

| Part | State |
|---|---|
| Project | "PolluxKart", number 2 in the Softogram organisation, private |
| Items | Every epic and ticket in the repository: 21 epics and 171 tickets, none twice |
| Status field | One single-select field with the six options, in stage order: Planning, Awaiting approval, Implementation ready, In progress, In review, Done |
| Status values | All match the stage labels (the five cards that moved on 2026-09-14 were updated by hand the same day) |
| Views | One table view, "View 1"; no board layout yet |

The column for approved tickets already exists, so the agent guard never needs to create it.

## The problem

The board holds the right items, but it is not yet what the owner chose: it is private, it has no board layout, epics are mixed in with tickets, and cards show none of the chosen fields.
Nothing checks that the board and the labels agree, and nothing links to the board from the docs.

## The change

### Settings

| Setting | Value | How |
|---|---|---|
| Visibility | Public | `gh project edit 2 --owner Softogram --visibility PUBLIC`, run once by the owner or an agent at the owner's request |
| Name | PolluxKart | unchanged |
| Short description | "Every PolluxKart epic and ticket, one column per stage. Stages follow the ticket labels." | same command |
| Readme | Two sentences: what the columns mean and that cards move with labels, linking `docs/platform/development-process.md` | same command |
| Who can edit | Only the owner: no collaborators added, and the organisation's default project role for members stays at no access or read; the #33 sync uses its own app | checked by hand in project settings |

### Views, created by hand

GitHub's API cannot create or change project views, so the owner creates them in the website, following this table exactly.
The checker below reads them back and fails if they differ.

| View | Layout | Filter | Group or columns | Fields shown |
|---|---|---|---|---|
| **Tickets** (first view) | Board | `is:issue -label:epic` | Columns by Status, in stage order | Title, Parent issue, Assignees, Linked pull requests, Labels |
| **Epics** | Table | `label:epic` | Sorted by title | Title, Status, Sub-issues progress |

"View 1" is renamed to **Tickets** and switched to the board layout, rather than adding a third view.
The Labels field shows all labels on a card: the stage label, and `owner-action` where a ticket has it.

### The checker (`tools/board/check.py`)

Standard library Python, talking to GitHub through `gh api graphql`.
Run with `make board-check`; the nightly sync in #33 runs the same checks.

It fails, listing every problem, when:

1. an issue titled `EXX-NN ...` or `Epic EXX: ...` is not on the board, or is on it more than once;
2. an item on the board is not such an issue;
3. an issue has no stage label or more than one;
4. an item's Status does not match its issue's single stage label;
5. the board is not public, or not named "PolluxKart";
6. the two views above are missing, or their layout, filter, grouping or shown fields differ.

It changes nothing; fixing is by hand here, and automatic in #33.

**Names in the code** (in `tools/board/board.py`, shared with #33): `STAGES` (label to Status option, in order), `is_tracked(title)`, `fetch_project(gh)`, `fetch_tracked_issues(gh)`, `compare(project, issues)` returning a list of `Problem`; `check.py` holds `main(argv)`.
`gh` is passed in, so tests use a fake and never call GitHub.

### Wiring

- `CHECKS` gains nothing: the checker needs the network and live data, so it is not part of `make ci`. Its unit tests are, as `board-tests` in the `tooling` group.
- The Makefile gains `board-check`.
- `docs/platform/development-process.md` links the board under "How work is broken down" and "The six stages".

### Documents updated in the implementation pull request

- `docs/platform/development-process.md`: the board link, the two views, and that cards follow labels.
- `tools/board/README.md`: new.
- `CLAUDE.md`, "Stages": the board link.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A new ticket is created before #33 exists | Not on the board; `make board-check` reports it; added by hand |
| A ticket's label changes before #33 exists | Status mismatch reported; fixed by hand, as on 2026-09-14 |
| A closed ticket | Stays on the board in its Status column; closing is handled in #33 |
| An issue from the public titled like a ticket | Reported as tracked; the owner closes or retitles it |
| GitHub renames a built-in field | The view check fails, naming the field; the table above is updated |
| `gh` not logged in or offline | The checker exits 1 with the error, never "all good" |
| Someone other than the owner is added to the project | Not detectable through the API in a stable way; the project settings check is manual, listed in the runbook |

## What is deliberately not covered

- **Moving cards automatically:** #33.
- **Changing any ticket's stage label:** this ticket only configures and checks the board.
- **The empty "@CosmicSaaurabh's untitled project"** in the organisation: not PolluxKart's; the owner can delete it separately.

## Open questions for the owner

None open.
All five questions this ticket raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Project board".
The ticket's sixth question, about naming the approved column, no longer applies: the column already exists.
