# Test plan: E00-09 Complete the repository CLAUDE.md with commands and tooling

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #39 (E00-09).
Design: [../low-level/issue-39-claude-md-commands.md](../low-level/issue-39-claude-md-commands.md)

This ticket has no web requests.
Its flows are the CLAUDE.md check, `make help`, and running each listed command.
Terms such as make target, help comment and CLAUDE.md are explained at the top of the design.

## How these tests run

- Unit tests are standard library `unittest` files in `tools/checks/`, run by `checks-tests` in `make ci` and the `tooling-tests` workflow.
- Their functions take the Makefile and CLAUDE.md text as inputs, so failing cases use edited text in memory; one test also reads the real files.
- The commands CLAUDE.md lists are run by hand once from a fresh worktree, with the output summarised in the implementation pull request.

## Flow 1: the CLAUDE.md check

| Id | Case | Expected | Proves |
|---|---|---|---|
| C1.1 | The real CLAUDE.md and Makefile | Passes | AC3 |
| C1.2 | CLAUDE.md text containing `` `make deploy` `` | Fails, naming `deploy`. Partner: C1.1 | AC3 |
| C1.3 | `make deploy` inside a fenced code block | Fails, naming `deploy` | Code blocks are read too |
| C1.4 | Prose "to make a change" with no code formatting | Passes | No false match |
| C1.5 | `` `make ci KEEP_GOING=1` `` style arguments after a real target | Passes, reading only the target name | Arguments are ignored |
| C1.6 | A Makefile target with no help comment | Fails, naming the target | `make help` stays complete |
| C1.7 | A CLAUDE.md line "Run it. Then push." outside code and tables | Fails, naming the line number | AC4, one sentence per line |
| C1.8 | Lines "Use e.g. `make ci`.", "GNU Make 3.81 works.", and a table row with two sentences | Pass | Abbreviations, numbers and tables are not flagged |
| C1.9 | docslint on a copy of CLAUDE.md containing an em dash | Fails, naming CLAUDE.md | AC4, em dash |

## Flow 2: `make help`

| Id | Kind | Case | Expected |
|---|---|---|---|
| H2.1 | Unit | A Makefile text with three targets and help comments | Three aligned lines in file order |
| H2.2 | Unit | A variable assignment line such as `PYTHON ?= python3`, and a `.PHONY:` line | Not listed as targets |
| H2.3 | End-to-end | `make help` in the real repository | Lists every target defined in the Makefile, the same set C1.1 reads |
| H2.4 | End-to-end | `make` with no target | Prints the same as `make help` |

## Flow 3: the listed commands, by hand once

| Id | Command, from a fresh worktree | Expected | Acceptance criterion |
|---|---|---|---|
| M3.1 | `make doctor` | Runs and reports every tool | AC1 |
| M3.2 | `make ci` | Runs every check; passes | AC1 |
| M3.3 | `make help` | Lists every target | AC1 |
| M3.4 | `git diff origin/development -- CLAUDE.md` | No changed line inside the "Rule one" section | AC2 |

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #39, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: every command in CLAUDE.md runs from a clean clone, or says what it needs | M3.1 to M3.3 |
| AC2: rule one's text is unchanged | M3.4 |
| AC3: a check fails when CLAUDE.md names a target the Makefile lacks | C1.1 to C1.5 |
| AC4: no em dash, and one sentence per line | C1.7 to C1.9 |
| `make help` is the full, generated list | C1.6, H2.1 to H2.4 |

## What the contributor gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| Makefile | A target missing or undescribed | The check fails naming it | C1.2, C1.6 |
| Python | Not installed | `make help` cannot run; `make doctor` in #34 already covers Python | Stated in #34 |

## Reachability check

No database rows are written.
The equivalent risk is a check that reads the wrong file: C1.1 and H2.3 run against the real CLAUDE.md and Makefile.

## What is deliberately not covered, and why

- **Sentence-per-line checks outside CLAUDE.md:** not in this ticket's scope.
- **Whether planned commands are useful:** the owner chose to list only existing ones.
