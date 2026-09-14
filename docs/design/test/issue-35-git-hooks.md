# Test plan: E00-05 Git hooks that block direct pushes and run `make ci` before pushing

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #35 (E00-05).
Design: [../low-level/issue-35-git-hooks.md](../low-level/issue-35-git-hooks.md)

This ticket has no web requests, so each "flow" is a git command a contributor types.
Terms such as git hook, staged files, failing open and escape hatch are explained at the top of the design.

## Words used below

- **Sandbox repository:** a temporary git repository made by a test, holding a copy of the hooks and `tools/githooks/`, with the hooks enabled.
- **Bare remote:** a temporary git repository with no files on disk, standing in for GitHub, so pushes really happen but stay on the test machine.
- **Fake `gh`:** a tiny script placed first on PATH that prints a chosen answer (an open pull request, none, or an error), so a test decides what "GitHub" says.
- **Fake Makefile:** a `Makefile` in the sandbox whose `ci` target writes a marker file and then passes or fails, so a test can see whether `make ci` ran and control its result.
- **Passing partner:** the matching test that passes, proving a failing test fails for the intended reason.

## How these tests run

- All tests are standard library `unittest` files in `tools/githooks/`, run by the `githooks-tests` check in `make ci` and the `tooling-tests` workflow.
- End-to-end tests run real `git commit` and `git push` in a sandbox repository against a bare remote, with the real hook files.
  After every refused push, the test reads the bare remote and asserts nothing changed there.
- Unit tests call the Python functions with replaced program runners, for cases that would otherwise need waiting (a hanging `gh`).
- No test waits out real time, and no test skips itself; if `git` or `make` is missing, the tests fail with "run make doctor".
- No test reaches GitHub.

## Flow 1: `git push` (the pre-push hook)

### Without an open pull request

| Id | Kind | Case | Expected |
|---|---|---|---|
| P1.1 | End-to-end | Push `feature/a`; fake `gh` reports no open pull request | Push succeeds; no marker file, so `make ci` did not run; the output says there is no open pull request |
| P1.2 | End-to-end | Push to `development` | Refused with the message naming the rule and development-process.md; the bare remote has no `development` update. Partner: P1.1 (AC1) |
| P1.3 | End-to-end | Push to `main` | Refused the same way (AC1) |
| P1.4 | End-to-end | `git push origin :development` (delete) | Refused |
| P1.5 | End-to-end | One push of `feature/a` and `development` together | Refused; the bare remote has neither branch updated |
| P1.6 | End-to-end | `SKIP_LOCAL_CI=1` push to `development` | Still refused. Partner: P1.2 |
| P1.7 | End-to-end | Push a tag | Succeeds without asking `gh` (the fake `gh` records that it was not called) |
| P1.8 | End-to-end | First push of a brand-new branch | Succeeds; `make ci` did not run |

### With an open pull request

| Id | Kind | Case | Expected |
|---|---|---|---|
| P1.9 | End-to-end | Fake `gh` reports pull request #12; clean folder; fake `make ci` passes | Marker written, so `make ci` ran in this worktree; push succeeds (AC2) |
| P1.10 | End-to-end | As P1.9, but fake `make ci` fails | Refused; the message mentions the failure and `SKIP_LOCAL_CI=1`; the bare remote is unchanged. Partner: P1.9 (AC2) |
| P1.11 | End-to-end | As P1.10, with `SKIP_LOCAL_CI=1` | Push succeeds; no marker, so `make ci` did not run; output names pull request #12 and asks for a note in it |
| P1.12 | End-to-end | As P1.10, with `SKIP_LOCAL_CI=true` | Treated as not set: `make ci` runs, fails, push refused. Partner: P1.11 |
| P1.13 | End-to-end | Open pull request; a tracked file edited but not committed | Refused, listing the file; no marker; the bare remote is unchanged |
| P1.14 | End-to-end | Open pull request; an untracked file present | Refused, listing the file |
| P1.15 | End-to-end | Open pull request; only a git-ignored file present | `make ci` runs and the push succeeds. Partner: P1.14 |
| P1.16 | End-to-end | Open pull request; more than 20 uncommitted files | Refused, listing 20 and saying how many more |
| P1.17 | End-to-end | Open pull request for `feature/b`; `git push origin feature/b` while `feature/a` is checked out | Refused: the pushed commit is not the checked-out commit; no marker |
| P1.18 | End-to-end | Open pull request; a second worktree of the sandbox pushes its own branch | The marker appears in the second worktree's folder, proving its own files and hooks were used (AC5) |

### When `gh` cannot answer (AC4)

| Id | Kind | Case | Expected |
|---|---|---|---|
| P1.19 | End-to-end | `gh` not on PATH | Push succeeds; the warning says `gh` is not installed and that GitHub's checks still run; `make ci` did not run |
| P1.20 | End-to-end | Fake `gh` exits 1 with "not logged in" | Push succeeds with the warning including that reason |
| P1.21 | Unit | The runner raises a timeout for the `gh` call | `open_pull_request` returns `Unknown` with "no answer within 15 seconds"; `main` returns 0 and prints the warning |
| P1.22 | Unit | A spy runner records its arguments | `gh` is always asked with a 15 second limit, and with `--head <branch> --state open` |
| P1.23 | Unit | Fake `gh` prints something that is not JSON | Treated as `Unknown`, never as "no open pull request" silently; warning printed, push allowed |

### Parsing what git sends

| Id | Kind | Case | Expected |
|---|---|---|---|
| P1.24 | Unit | Lines for a branch update, a new branch, a deletion and a tag | Parsed into the right `PushedRef` kinds |
| P1.25 | Unit | An empty input (nothing to push) | Exit 0 without asking `gh` |

## Flow 2: `git commit` (the pre-commit hook)

The sandbox for these tests is a copy of the repository's tracked files, so docslint has a real docs tree to check.

| Id | Kind | Case | Expected |
|---|---|---|---|
| C2.1 | End-to-end | Stage a clean change to a doc and commit | Commit created |
| C2.2 | End-to-end | Stage a doc containing an em dash and commit | Refused with docslint's message; no new commit exists. Partner: C2.1 |
| C2.3 | End-to-end | Stage a doc with a broken link and commit | Refused |
| C2.4 | End-to-end | Stage a clean doc; also leave an unstaged em dash in another file on disk | Commit created, because only staged content is checked |
| C2.5 | End-to-end | Stage a doc with an em dash; fix it on disk without staging the fix | Refused, because the staged content is still wrong. Partner: C2.4 |
| C2.6 | End-to-end | After C2.1 and after C2.2 | No temporary folder is left behind in either case |
| C2.7 | End-to-end | `SKIP_LOCAL_CI=1 git commit` with a staged em dash | Still refused; the hatch does not apply to commits |

## Flow 3: `make doctor`'s hook row (unit tests in `tools/checks/test_doctor.py`)

| Id | Case | Expected |
|---|---|---|
| D3.1 | `core.hooksPath` is `.githooks` | `ok` |
| D3.2 | The setting is missing | `not enabled`, a needed-now problem, the setup command printed; exit 1. Partner: D3.1 |
| D3.3 | The setting is `/somewhere/else` | `points elsewhere`, naming the folder; exit 1 |
| D3.4 | The setting is missing and `GITHUB_ACTIONS` is `true` | Information line only; exit code unaffected. Partner: D3.2 |

## Flow 4: the hook files themselves

| Id | Case | Expected |
|---|---|---|
| F4.1 | The real repository's index | `.githooks/pre-commit` and `.githooks/pre-push` are stored as executable (mode 100755) (AC5) |
| F4.2 | Each wrapper run from a subfolder of the sandbox | It still finds its Python script through `git rev-parse --show-toplevel` |

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #35, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: with hooks enabled, a direct push to `development` or `main` is refused with a message naming the rule | P1.2 to P1.6 |
| AC2: pushing a branch with an open pull request runs `make ci`, and a failing check stops the push | P1.9, P1.10 |
| AC3: pushing a branch without a pull request goes ahead without `make ci` | P1.1, P1.8 |
| AC4: without `gh` or offline, the push goes ahead and the hook says so | P1.19 to P1.23 |
| AC5: the hook files are committed as executable and work from any worktree | F4.1, F4.2, P1.18 |
| The escape hatch works only as `SKIP_LOCAL_CI=1`, only for `make ci`, and asks for a note in the pull request | P1.6, P1.11, P1.12, C2.7 |
| Uncommitted or untracked files stop a push that would run `make ci` | P1.13 to P1.17 |
| The pre-commit hook checks the staged docs | C2.1 to C2.6 |
| `make doctor` fails locally without the hooks, not on GitHub | D3.1 to D3.4 |

## What the contributor gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| `gh` | Missing, not logged in, error, no answer, bad output | Push allowed with a warning naming the reason | P1.19 to P1.23 |
| `make ci` | A check fails | Push refused, with the way forward | P1.10 |
| Python | Not installed | Git stops the push or commit with `python3: not found` | Not automated: every test needs Python to run; stated in the design |
| docslint | Finds a problem in staged docs | Commit refused | C2.2, C2.3 |

## Reachability check

This ticket writes no database rows.
The equivalent risk is a hook that exists in the repository but never runs: P1.9 and C2.2 prove the real hook files run through git itself, not by calling the Python scripts directly.

## Concurrency and replay

Two worktrees pushing at once run separate hooks on separate files (P1.18).
Re-running a refused push after fixing the cause succeeds; P1.10 is followed by the fix and a second push in the same sandbox.

## Verified test run, recorded in the implementation pull request

- Local `make ci` output, including `githooks-tests`.
- The real pre-push output from pushing the implementation branch after its pull request was opened, showing the hook finding the pull request and running `make ci`.
- The green `tooling-tests` run on GitHub.

## What is deliberately not covered, and why

- **`--no-verify`:** git skips every hook, and no hook can prevent that; GitHub's rulesets (#36) are the protection that cannot be skipped.
- **A real `gh` talking to GitHub inside tests:** tests must not depend on the network or a login; the implementation branch's own push proves it for real.
- **Native Windows:** not supported by the design.
- **The secret scan:** #37 adds and tests it.
