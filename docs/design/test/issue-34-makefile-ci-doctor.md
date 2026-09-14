# Test plan: E00-04 Makefile with `make ci` and `make doctor`

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #34 (E00-04).
Design: [../low-level/issue-34-makefile-ci-doctor.md](../low-level/issue-34-makefile-ci-doctor.md)

This ticket has no web requests, so each "flow" below is a command a contributor or a GitHub workflow types.
Terms such as check, group, exit code, actionlint and ShellCheck are explained at the top of the design.

## Words used below

- **Repository copy:** a temporary folder holding the files a fresh clone would contain (the list from `git ls-files --cached --others --exclude-standard`). A test can break a file in the copy without touching the real worktree.
- **Fake tool:** a tiny script in a temporary folder that prints a chosen version, or exits with a chosen code. Putting only that folder on PATH lets a test decide exactly what `make doctor` finds.
- **Passing partner:** the matching test that passes, which proves a failing test fails for the intended reason rather than because the setup is broken.
- **Unit test and end-to-end test:** a unit test calls one Python function with replaced inputs and never starts real programs; an end-to-end test runs the real `make` command the way a contributor does.

## How these tests run

- All tests are standard library `unittest` files in `tools/checks/`, run by the `checks-tests` check.
  So `make ci` runs them locally, and the `tooling-tests` job runs them on GitHub.
- **No test waits out real time.** A hanging tool is simulated by a replaced function that raises Python's timeout error, not by sleeping.
- **No test skips itself.** If actionlint, ShellCheck or `make` is missing, the end-to-end tests fail with "run `make doctor`".
- **The end-to-end tests cannot start themselves forever.** They run `make ci` inside a repository copy, and that copy leaves out `test_make_end_to_end.py`. The file is simply absent from the fixture, so nothing is skipped.
- Every end-to-end test gets its own repository copy, deleted afterwards, so tests can run alongside a real `make ci` in the same worktree.

## Flow 1: `make ci`

### Happy path

| Id | Setup | Expected | Proves |
|---|---|---|---|
| E1.1 | Clean repository copy | Exit 0. The summary lists all six checks as passed, in the order of the design's table | AC1, and that every check is really reached |

### Error paths (end-to-end, each paired with E1.1)

| Id | What is broken in the copy | Expected |
|---|---|---|
| E1.2 | A link in `docs/README.md` points at a missing file | Exit non-zero. `docslint` failed and the other five passed, which proves the run continued after the failure. Then the link is fixed in the same copy and `make ci` exits 0 (AC2, AC6) |
| E1.3 | A deliberately failing test file added to `tools/docslint/` | Only `docslint-tests` failed; exit non-zero (AC1) |
| E1.4 | A deliberately failing test file added to `tools/approval_gate/` | Only `approval-gate-tests` failed; exit non-zero (AC1) |
| E1.5 | A deliberately failing test file added to `.claude/hooks/` | Only `agent-hook-tests` failed; exit non-zero (AC1) |
| E1.6 | A deliberately failing test file added to `tools/checks/` | Only `checks-tests` failed; exit non-zero (AC1) |
| E1.7 | A workflow file using an expression that does not exist, `${{ github.no_such_field }}` | Only `actionlint` failed, and its output names the file and line; exit non-zero (AC1, AC8) |
| E1.8 | A workflow `run:` command with an unquoted variable, which ShellCheck reports | Only `actionlint` failed, and the output contains a ShellCheck finding. This proves ShellCheck is really wired in (AC8) |
| E1.9 | E1.2 and E1.7 together | Both `docslint` and `actionlint` are named in the final summary line; exit non-zero (AC6) |
| E1.10 | Not a file change: PATH holds only links to the real `python3` and `make` plus the system folders, so `actionlint` cannot be found. The test first confirms it really is not findable, and fails loudly if it is | `actionlint` and `checks-tests` (which also lists actionlint as needed) are marked failed with "not installed; run make doctor", without running; the other four still ran; exit non-zero |

### Unit tests (`test_checks.py`, with replaced `run`, `which` and `clock`)

| Id | Case | Expected |
|---|---|---|
| U1.1 | Every replaced command succeeds | Exit 0; every result passed |
| U1.2 | The second of four commands fails | The third and fourth were still called (the call log shows it); exit 1. Partner: U1.1 |
| U1.3 | A check's needed program is not found by `which` | Its command is never called; result failed with the install hint; later checks still called |
| U1.4 | A command exits 3 and prints nothing | Result failed with detail "exit code 3" |
| U1.5 | The second command raises Ctrl+C (`KeyboardInterrupt`) | The summary is still printed; later checks are "not run"; exit 130 |
| U1.6 | The test's own working folder is somewhere else | Every command is run from the repository root |
| U1.7 | A Python check | It runs with `sys.executable`, not whatever `python3` happens to be first on PATH |
| U1.8 | Python version replaced with 3.9.6, then 3.10.0 | 3.9.6: message naming both versions, exit 1. 3.10.0: carries on (the boundary) |
| U1.9 | `format_summary` with two failures | Final line reads "2 of N checks failed: <names>" in run order |
| U1.10 | `checks.py` and `doctor.py` parsed with Python 3.7 grammar (`ast.parse(..., feature_version=(3, 7))`) | Both parse, so an old Python gets the version message instead of a syntax error |

## Flow 2: `make ci-docs` and `make ci-tooling`

| Id | Kind | Case | Expected |
|---|---|---|---|
| E2.1 | End-to-end | `make ci-docs` on a clean copy | Exit 0; the summary lists exactly `docslint-tests` and `docslint` |
| E2.2 | End-to-end | `make ci-tooling` on a clean copy | Exit 0; the summary lists exactly the other four checks |
| E2.3 | End-to-end | `make ci-docs` on the E1.7 copy (broken workflow file) | Exit 0, because actionlint belongs to the tooling group. Partner of E1.7, proving groups really separate the checks |
| U2.1 | Unit | `--group nope` | Exit 2; the message lists `docs` and `tooling` |

### The coverage guard (`test_coverage.py`)

The guard's functions take the check list, the Makefile text and the workflow texts as inputs, so the failing cases use edited inputs rather than edited files.

| Id | Case | Expected |
|---|---|---|
| C2.1 | The real `CHECKS`, `Makefile` and `.github/workflows/*.yml` | Passes (AC4, AC9) |
| C2.2 | A check with a new group `extra`, which no Makefile target or workflow runs | Fails, naming `extra`. Partner: C2.1 |
| C2.3 | A workflow runs `make ci-missing`, a group with no checks | Fails, naming `missing` |
| C2.4 | Both workflows run `make ci-docs` | Fails: `docs` is run twice |
| C2.5 | The Makefile has no `ci-tooling` target | Fails, naming `tooling` |

## Flow 3: `make doctor`

Unit tests call `doctor.main` with a replaced `run` and `which`.
End-to-end tests run the real `make doctor` with PATH set to a folder of fake tools, plus a link to the real `make` and `python3`.

| Id | Kind | Case | Expected |
|---|---|---|---|
| D3.1 | End-to-end | Every tool needed now is present at or above its minimum; no later tools present | Exit 0. Every tool is listed; needed ones show `ok` and their version; later ones show `not installed` (AC3, AC7) |
| D3.2 | End-to-end | As D3.1, but `actionlint` absent | `actionlint` shows `missing` with its install hint, every other tool is still listed, and the last line names `actionlint`; exit 1 (AC3). Partner: D3.1 |
| D3.3 | Unit | `actionlint` and `gh` both absent | Both listed and both named in the last line; exit 1 |
| D3.4 | Unit | Fake `actionlint` reports one patch release below the pinned version, then exactly the pinned version | Below: `too old`, exit 1. Exactly the pin: `ok`, exit 0 (the boundary) |
| D3.5 | Unit | `make` reports 3.80, then 3.81 | 3.80: `too old`, exit 1. 3.81: `ok` |
| D3.6 | Unit | Python replaced with 3.9.6, then 3.10.0 | 3.9.6: `too old`, exit 1. 3.10.0: `ok` |
| D3.7 | Unit | Later tools present: Java 25, Node.js 24, pnpm, Docker with `docker info` succeeding | Each shows `found` and its version; exit 0 |
| D3.8 | Unit | Docker present but `docker info` fails | Docker shows `installed, not running`; exit still 0 (AC7) |
| D3.9 | Unit | Java reports 21, not the planned 25 | Shows `found 21` with the note that the version is still open in #55; exit 0, because later tools are information only |
| D3.10 | Unit | Asking `gh` for its version raises a timeout | `gh` shows `no answer`; exit 1. The same for `java`: exit 0 |
| D3.11 | Unit | A spy `run` records its arguments | Every version question was asked with a 10 second limit |
| D3.12 | Unit | Fake `actionlint` prints `hello` | `version unreadable`; exit 1. Fake `gh` prints `hello`: `ok`, "version unknown", because `gh` has no minimum |
| D3.13 | Unit | The pinned table in `linters.py` | The doctor's minimum for actionlint and ShellCheck equals the pinned version, so a laptop can never check with an older linter than GitHub |

## Flow 4: `python3 tools/checks/install_linters.py` (GitHub only)

The tests never use the network.
They build a small archive holding a fake `actionlint`, compute its checksum, and give the installer a local file address instead of the GitHub release address.

| Id | Case | Expected |
|---|---|---|
| I4.1 | The archive matches its checksum; `GITHUB_PATH` points at a temporary file; the platform is replaced with Linux x86-64 | The program is unpacked and executable, and its folder is written to the `GITHUB_PATH` file; exit 0 |
| I4.2 | The same archive with one byte changed | Refused: nothing is unpacked, nothing is written to `GITHUB_PATH`, and the message names the tool and both checksums; exit 1. Partner: I4.1 |
| I4.3 | The platform replaced with macOS arm64 | Exit 1 with "meant for GitHub's Linux machines; install locally with Homebrew or your package manager" |
| I4.4 | `GITHUB_PATH` not set | Exit 1 with the same explanation; nothing downloaded |
| I4.5 | The download raises a network error | Exit 1 naming the address that failed |
| I4.6 | The pinned table itself | Every entry has a version, an `https://github.com/` release address and a 64-character hexadecimal checksum |

The real download from GitHub is proved by the implementation pull request's own `tooling-tests` run, which must show the install step, `make doctor` and `make ci-tooling` all passing.

## Flow 5: `make` with no target

| Id | Kind | Case | Expected |
|---|---|---|---|
| E5.1 | End-to-end | `make` in a clean copy | Exit 0; prints the four targets and runs no checks (the output contains no summary) |

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #34, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: from a clean clone, `make ci` runs every check listed in CLAUDE.md and exits non-zero if any fails | E1.1, E1.3 to E1.8 |
| AC2: breaking one docs link makes `make ci` fail; fixing it makes it pass | E1.2 |
| AC3: `make doctor` lists each tool as found or missing with its version, and handles a missing tool as the owner chose | D3.1, D3.2, D3.3 |
| AC4: the GitHub workflows run the same checks through `make` | C2.1, and the implementation pull request's CI runs |
| AC5: CLAUDE.md names `make ci` as the one command before a pull request | Reviewed in the implementation pull request; a document, not behaviour |
| AC6: `make ci` keeps going after a failure and lists every failure | E1.2, E1.9, U1.2 |
| AC7: later tools are shown as information and never fail `make doctor` | D3.1, D3.7, D3.8, D3.9 |
| AC8: workflow files are linted with actionlint, including shell commands | E1.7, E1.8 |
| AC9: a check that neither workflow runs fails the build | C2.2 to C2.5 |

## What the contributor gets when a dependency fails

| Dependency | Failure | What the contributor sees | Test |
|---|---|---|---|
| Python | Not installed | `make` prints `python3: command not found`; the README says to install Python 3.10 or newer | None: no script can run without Python, stated in the design |
| Python | Older than 3.10 | The version needed and found; exit 1 | U1.8, D3.6 |
| A needed program | Not installed | The check fails with "not installed; run make doctor"; the rest still run | E1.10, U1.3 |
| Any tool | Hangs when asked its version | `no answer` after 10 seconds | D3.10, D3.11 |
| Docker | Not running | Information line, no failure | D3.8 |
| GitHub release download | Network failure or wrong checksum | The install step fails with the address and checksums; no unverified program runs | I4.2, I4.5 |

## Reachability check

This ticket writes no database rows and stores no data, so the database reachability rule does not apply.
The equivalent risk is a check that exists in the list but is never run.
E1.1 asserts all six check names appear in the real summary, and C2.1 asserts a workflow runs every group.

## Concurrency and replay

No money, stock, coupons or invoice numbers are involved.
Two worktrees running `make ci` at once share no files or state, and each end-to-end test uses its own repository copy.
Running `make ci` twice in a row gives the same result; E1.2 re-runs it in the same copy after the fix.

## Verified test run, recorded in the implementation pull request

- Local `make doctor` and `make ci` output on macOS, with GNU Make 3.81, pasted into the pull request.
- Links to the green `docs` and `tooling-tests` runs on GitHub (Ubuntu, a newer GNU Make), showing `make ci-docs`, the linter install, `make doctor` and `make ci-tooling`.

## What is deliberately not covered, and why

- **Real downloads in unit tests:** tests must not depend on the network; the pull request's own GitHub run proves the real download (Flow 4).
- **Python missing entirely:** nothing in the repository can run without Python; the README states it.
- **Make versions other than macOS's 3.81 and the Ubuntu runner's version:** those are the two machines contributors and CI use.
- **Native Windows:** not supported by the design; WSL is the route.
- **How long `make ci` takes:** not a requirement of this ticket; it is revisited when slow end-to-end checks arrive.
- **The pre-push hook, gitleaks and branch rulesets:** tested in their own tickets, #35, #37 and #36.
