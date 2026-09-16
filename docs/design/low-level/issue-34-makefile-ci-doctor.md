# E00-04 Makefile with `make ci` and `make doctor`

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #34 (E00-04), part of epic #10.
Test plan: [../test/issue-34-makefile-ci-doctor.md](../test/issue-34-makefile-ci-doctor.md)

## Words used below

- **Make and Makefile:** `make` is a long-standing command-line program that runs named recipes written in a file called `Makefile`. Typing `make ci` runs the recipe named `ci`.
- **Target:** one named recipe in a Makefile, such as `ci` or `doctor`.
- **Check:** in this document, one command inside `make ci` that either passes or fails, such as the docs checker.
- **Group:** a named set of checks. Each group has its own `make ci-<group>` target and is run by exactly one GitHub workflow at release.
- **Exit code:** the number a command hands back when it finishes. Zero means success; anything else means failure. Git hooks read this number to decide whether to stop.
- **Lint and linter:** checking files for mistakes without running them; a linter is the tool that does it.
- **actionlint:** a linter for GitHub Actions workflow files. It catches typos, broken expressions and wrong references.
- **ShellCheck:** a linter for shell commands. actionlint uses it to check the `run:` commands inside workflow files.
- **CI (continuous integration):** the same automated checks a contributor runs locally with `make ci`. GitHub Actions runs them at release (a push to `main`) and when someone starts the workflow by hand, not on every pull request (owner decision, 2026-09-16).
- **Workflow and job:** a workflow is a YAML file in `.github/workflows/` telling GitHub Actions what to run; a job is one named unit of work inside it.
- **PATH:** the list of folders your terminal searches when you type a program's name. A program not in any of those folders counts as "not installed".
- **Checksum (SHA-256):** a fingerprint computed from a file's bytes. If even one byte changes, the fingerprint changes, so comparing it proves a download is the exact file expected.

## What was already decided before this document

- **Nothing is implemented without the owner's approval, and every ticket ends with a verified test run:** `make ci` passing locally (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Nothing is implemented without the owner's approval"; the GitHub Actions half is revised 2026-09-16, "Local `make ci` is the pull-request gate").
- **`development` is the base of every pull request; no history rewrites** (owner decision, 2026-09-13, "Git workflow").
- **Backend in Java with Spring Boot, frontend in Next.js with TypeScript, both in one repository** (owner decisions, 2026-09-13).
- **How `make ci` and `make doctor` behave** (owner decision, 2026-09-14, "`make ci` and `make doctor`", answered while planning this ticket):
  - `make doctor` checks the full planned tool list, but only tools needed today can make it fail; the rest are shown as information.
  - `make doctor` checks every tool, prints what it found, then fails if any needed tool is missing.
  - `make ci` runs every check even after one fails, lists all failures at the end, and fails if any failed.
  - Workflow files are linted with actionlint.
  - GitHub keeps the `docs` and `tooling-tests` workflows, each running its part of `make ci`, with an automated test proving the two together run everything.
  - Those workflows run on a push to `main` and on hand dispatch, not on every pull request (owner decision, 2026-09-16, "Local `make ci` is the pull-request gate").

## Proposed in the docs and used here, confirmed when the owner approves this design

- Repository tooling uses only the Python 3.10 standard library, no packages to install ([tools/approval_gate/README.md](../../../tools/approval_gate/README.md)).
- `make ci` later grows `ci-api`, `ci-web` and `ci-e2e` ([testing.md](../../platform/testing.md)). This design only makes room for them.
- The later tool versions `make doctor` shows as information: Java 25 LTS (still an open question in #55), Node.js 24 LTS, pnpm, and Docker ([stack.md](../../platform/stack.md)).

## The problem

Today the checks a pull request must pass are four commands, run on the contributor's machine.
They are written out in `CLAUDE.md` and copied again, by hand, into two workflow files.
Nothing stops those copies drifting apart.
The first version of the store had four overlapping CI workflows and no single way to run the checks ([audit](../../legacy/audit-2026-09.md), section 5).
GitHub Actions minutes are metered; running those same checks on every pull request is what ran the organisation's budget out on Ryup and SpiceCraft.

## The change

### What a contributor types

| Command | What it does |
|---|---|
| `make doctor` | Lists every tool the checks use, with the version found. Fails if a tool needed today is missing or too old. |
| `make ci` | Runs every check, then prints a summary. Fails if any check failed. Run before every pull request. |
| `make ci-docs` | Runs only the docs group. This is what the `docs` workflow runs. |
| `make ci-tooling` | Runs only the tooling group. This is what the `tooling-tests` workflow runs. |
| `make` | Prints this list of targets. |

### Files

```
Makefile                                 new: thin targets that call the Python scripts
tools/checks/README.md                   new: what each script does and how to add a check
tools/checks/checks.py                   new: the list of checks and the runner
tools/checks/doctor.py                   new: the list of tools and the doctor
tools/checks/linters.py                  new: the pinned actionlint and ShellCheck versions and checksums
tools/checks/install_linters.py          new: installs the pinned linters on GitHub's machines
tools/checks/test_checks.py              new: tests for the runner
tools/checks/test_doctor.py              new: tests for the doctor
tools/checks/test_install_linters.py     new: tests for the installer
tools/checks/test_coverage.py            new: proves the two workflows together run every group
tools/checks/test_make_end_to_end.py     new: runs the real `make` on a copy of the repository
.github/workflows/docs.yml               changed: runs `make ci-docs`
.github/workflows/tooling-tests.yml      changed: installs linters, runs `make doctor`, runs `make ci-tooling`
CLAUDE.md                                changed: "Checks before a pull request" becomes `make doctor` and `make ci`
docs/platform/testing.md                 changed: "What `make ci` runs" and "Today"
.claude/skills/polluxkart-testing/SKILL.md   changed: "Running the checks" matches what was built
```

### The Makefile

The Makefile stays thin: each target calls one Python script.
The logic lives in Python for two reasons.
First, Make stops at the first failing step, and the owner chose "run every check, then list the failures".
Second, Python code can have unit tests like the rest of the repository's tooling.

macOS still ships GNU Make 3.81, from 2006, so the Makefile uses only features that version has.

```make
# One command for every check a pull request must pass.
# The logic is in tools/checks/; see tools/checks/README.md.

PYTHON ?= python3

.DEFAULT_GOAL := help
.PHONY: help ci ci-docs ci-tooling doctor

help:
	@echo "make doctor      check this machine has the tools the checks need"
	@echo "make ci          run every check a pull request must pass"
	@echo "make ci-docs     run only the docs checks (the docs workflow)"
	@echo "make ci-tooling  run only the tooling checks (the tooling-tests workflow)"

ci:
	@$(PYTHON) tools/checks/checks.py

ci-docs:
	@$(PYTHON) tools/checks/checks.py --group docs

ci-tooling:
	@$(PYTHON) tools/checks/checks.py --group tooling

doctor:
	@$(PYTHON) tools/checks/doctor.py
```

### The checks (`tools/checks/checks.py`)

The checks, in the order they run:

| Check | Group | Command | Programs it needs |
|---|---|---|---|
| `docslint-tests` | docs | `python3 -m unittest discover -s tools/docslint` | none beyond Python |
| `docslint` | docs | `python3 tools/docslint/docslint.py` | none beyond Python |
| `approval-gate-tests` | tooling | `python3 -m unittest discover -s tools/approval_gate` | none beyond Python |
| `agent-hook-tests` | tooling | `python3 -m unittest discover -s .claude/hooks` | none beyond Python |
| `checks-tests` | tooling | `python3 -m unittest discover -s tools/checks` | `make`, `actionlint`, `shellcheck` (the end-to-end tests use them) |
| `actionlint` | tooling | `actionlint -shellcheck=shellcheck -pyflakes=` | `actionlint`, `shellcheck` |

Python commands run with the same Python that runs `checks.py` (`sys.executable`), so the version `make doctor` checked is the version used.

**How it runs:**

1. Work out the repository root from the location of `checks.py` itself, so `make -C <repo> ci` works from any folder and each worktree checks only its own files.
2. For each selected check, in order:
   - print a header line with the check's name;
   - confirm every program in "Programs it needs" is on PATH; if one is not, record the check as failed with "`actionlint` is not installed; run `make doctor`", and move on without running it;
   - otherwise run the command from the repository root, with its output shown live;
   - record passed or failed, the exit code, and how long it took.
3. Print the summary and exit.

**Why actionlint needs ShellCheck present.**
When ShellCheck is missing, actionlint quietly skips checking `run:` commands and still passes.
GitHub's machines have ShellCheck, so a laptop without it would pass where GitHub fails.
The check therefore refuses to run until ShellCheck is installed.
`-pyflakes=` switches off actionlint's optional Python checker, because no workflow runs Python inline and nothing installs that checker.

**The summary** looks like this:

```
make ci summary
  passed  docslint-tests        0.4s
  failed  docslint              0.2s   exit code 1
  passed  approval-gate-tests   0.9s
  passed  agent-hook-tests      0.3s
  passed  checks-tests         11.8s
  failed  actionlint            0.0s   actionlint is not installed; run make doctor
2 of 6 checks failed: docslint, actionlint
```

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Every selected check passed |
| 1 | At least one check failed, or Python is older than 3.10 |
| 2 | Wrong usage, such as an unknown group name; the message lists the valid groups |
| 130 | Stopped with Ctrl+C; the checks not reached are listed as "not run" |

**Names in the code:**

- `Check`: a record of `name`, `group`, `command` and `needs`.
- `CHECKS`: the table above, in order.
- `select_checks(checks, group)`: all checks, or one group's; raises `UnknownGroup` for a name not in the table.
- `run_checks(checks, root, run=subprocess.run, which=shutil.which, clock=time.monotonic)`: runs them and returns a list of `Result` (`name`, `status` of passed, failed or not run, `detail`, `seconds`). The last three arguments are replaceable so unit tests never start real programs or wait.
- `format_summary(results)`: the summary text.
- `main(argv)`: reads `--group`, checks the Python version, and returns the exit code.

**How later tickets add checks.**
A ticket adds its `Check` entries with a new group name, a `ci-<group>` target in the Makefile, and one workflow job that runs `make ci-<group>` at release.
The coverage test below fails until all three exist.
For example, the backend CI ticket (E05-05) would add group `api`, target `ci-api` and a job running `make ci-api` on push to `main`.

### `make doctor` (`tools/checks/doctor.py`)

The tools, in the order printed:

| Tool | Needed | Minimum | Why |
|---|---|---|---|
| `python3` | now | 3.10 | Runs every check and this doctor |
| `make` | now | 3.81 | Runs the targets |
| `git` | now | none | Worktrees, commits |
| `gh` (GitHub CLI) | now | none | Moving ticket stage labels; the pre-push hook planned in #35 uses it to find a branch's open pull request |
| `actionlint` | now | the version pinned for GitHub, in `tools/checks/linters.py` | The `actionlint` check |
| `shellcheck` | now | the version pinned for GitHub, in `tools/checks/linters.py` | The `actionlint` check |
| `java` | later: backend foundation, epic #13 | shown, not enforced; planned 25 LTS, still open in #55 | Information only |
| `node` | later: frontend foundation, epic #14 | shown, not enforced; planned 24 LTS | Information only |
| `pnpm` | later: frontend foundation, epic #14 | shown, not enforced | Information only |
| `docker` installed and running | later: local stack, epic #15 | shown, not enforced | Information only |

**How it runs:**

1. Ask each tool for its version (for example `actionlint -version`), allowing at most 10 seconds per question, so a stuck tool cannot hang the doctor.
   For Docker, also run `docker info` to see whether it is running.
2. Read the first version number in the answer.
3. Give each tool a status:
   - needed now: `ok`, `missing`, `too old`, `version unreadable` (only for a tool with a minimum), or `no answer` (took more than 10 seconds);
   - needed later: `found`, `not installed`, or for Docker `installed, not running`. These never cause a failure.
4. Print every tool with its status, the version found, and for any problem an install hint (for example `brew install actionlint`, or the tool's official install page).
5. Print one final line: either "All tools needed today are ready" or "2 needed tools have a problem: actionlint, shellcheck".
6. Exit 0 when every tool needed now is `ok`, otherwise exit 1.

Sample output:

```
make doctor

Needed now
  ok         python3      3.14.0    need 3.10 or newer
  ok         make         3.81      need 3.81 or newer
  ok         git          2.52.0
  ok         gh           2.96.0
  missing    actionlint             install: brew install actionlint
  ok         shellcheck   0.11.0    need 0.11.0 or newer

Needed later (information only, never fails)
  found          java     25.0.1    backend foundation (#13); exact version still open in #55
  found          node     24.12.0   frontend foundation (#14); planned 24 LTS
  found          pnpm     10.34.3   frontend foundation (#14)
  not running    docker   29.0.2    local stack (#15); start Docker Desktop when that work begins

1 needed tool has a problem: actionlint
```

(The version numbers above are an example, not the pinned versions.)

**When a later tool becomes needed**, the ticket that first uses it moves it from "needed later" to "needed now" and sets its minimum, and says so in its own design.

**Old Python.**
`doctor.py` and `checks.py` are written only in syntax that Python 3.7 can read.
That way, running them on an older Python prints "Python 3.10 or newer is needed, found 3.9.6" instead of crashing with a confusing syntax error.
A test checks this.

**Names in the code:** `Tool` (a record of `name`, `version_command`, `needed_now`, `minimum`, `purpose`, `install_hint`), `TOOLS`, `probe(tool, run=subprocess.run, which=shutil.which)` returning a `Finding`, `format_report(findings)`, and `main(argv)`.

### Linters on GitHub (`tools/checks/linters.py` and `install_linters.py`)

GitHub's machines do not come with actionlint, and the ShellCheck they do have changes version whenever GitHub updates them.
So the tooling workflow installs a fixed version of both.

- `tools/checks/linters.py` holds one table: for actionlint and ShellCheck, the version, the download address of the official Linux x86-64 release, and the SHA-256 checksum of that file.
  The newest release of each at implementation time is pinned.
- `install_linters.py` downloads each file, compares its checksum with the table, and refuses to continue on any difference, so an altered download never runs.
  It then unpacks the program into the job's temporary folder and adds that folder to the job's PATH through the `GITHUB_PATH` file GitHub provides.
- It runs only on Linux x86-64 with `GITHUB_PATH` set, and otherwise exits 1 saying it is meant for GitHub; on a laptop, install the linters with Homebrew or the system package manager.
- `make doctor` reads the same table for its minimum versions, so a laptop can never be checking with an older linter than GitHub.
  A newer one on a laptop can only find more, never less.

### The workflows

Both keep their names and job names (`docslint`, `tooling-tests`).
They do not run on pull requests into `development` (owner decision, 2026-09-16).
Each workflow's `on:` is a push to `main` and `workflow_dispatch` only.
Both keep read-only permissions, `actions/checkout` pinned to a full commit, and their five-minute limit.

`.github/workflows/docs.yml`, job `docslint`:

```yaml
    steps:
      - name: Check out
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false

      - name: Run the docs checks
        run: make ci-docs
```

`.github/workflows/tooling-tests.yml`, job `tooling-tests`:

```yaml
    steps:
      - name: Check out
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false

      - name: Install the pinned actionlint and ShellCheck
        run: python3 tools/checks/install_linters.py

      - name: Check this machine has the tools
        run: make doctor

      - name: Run the tooling checks
        run: make ci-tooling
```

`approval-gate.yml` and `approval-label-guard.yml` do not change.

### The guard that the two workflows cover everything (`test_coverage.py`)

Keeping two workflows means a new check could be added to `make ci` but run by neither.
This test compares three lists and fails, naming the group, unless they match:

1. the groups used in `CHECKS`;
2. the `ci-<group>` targets in the `Makefile`;
3. the `make ci-<group>` commands in `.github/workflows/*.yml`, where each group must appear exactly once, so no group is run twice or not at all.

It runs inside `checks-tests`, so it runs in `make ci` locally and in the `tooling-tests` job on GitHub.

### Documents updated in the implementation pull request

- `CLAUDE.md`, "Checks before a pull request": run `make doctor` once per machine and `make ci` before every pull request; the four separate commands are removed.
- `docs/platform/testing.md`: "What `make ci` runs" lists the checks as built; "Today" is updated.
- `.claude/skills/polluxkart-testing/SKILL.md`, "Running the checks": the `make doctor` line matches the table above.
- `tools/checks/README.md`: what each script does, the exit codes, and how to add a check and a group.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| One check fails in the middle | The rest still run; the summary names it; exit 1 |
| Several checks fail | All are named in the final summary line; exit 1 |
| A program a check needs is not installed | That check is marked failed with "not installed; run `make doctor`", without running; the rest still run |
| ShellCheck missing but actionlint installed | The `actionlint` check fails as "shellcheck is not installed", because actionlint would otherwise pass while quietly skipping shell checks |
| Python is not installed at all | `make` itself prints `python3: command not found` and stops; `tools/checks/README.md` says to install Python 3.10 or newer first. No Python script can help here |
| Python older than 3.10 | Both scripts print the version needed and found, and exit 1 |
| A tool hangs when asked its version | `make doctor` stops waiting after 10 seconds and reports `no answer`; a failure for a tool needed now, information for a later one |
| A tool's version cannot be read | A tool with a minimum is reported `version unreadable` and fails; a tool without a minimum is `ok` with "version unknown" |
| Docker installed but not running | Shown as `installed, not running`; never fails today |
| Ctrl+C during `make ci` | The running check stops, the summary marks the rest "not run", exit 130 |
| Unknown group, such as `--group api` before E05 | Exit 2, listing the valid groups |
| Run from a subfolder or another worktree | Paths come from the location of `checks.py`, so each worktree checks only itself |
| Two worktrees run `make ci` at the same time | Nothing is shared: the checks only read files, and Python's cache folders (`__pycache__`, ignored by git) sit inside each worktree |
| Laptop linter newer than GitHub's pinned one | It may report more problems locally, never fewer; fix them |
| Laptop linter older than the pin | `make doctor` reports `too old` |
| Download on GitHub fails or its checksum differs | The install step fails with the file address and both checksums; the job goes red and no unverified program runs |
| A GitHub runner that is not Linux x86-64 | The install step exits 1 with a message; the workflows pin `ubuntu-24.04`, so this only happens if that line changes |

## What is deliberately not covered

- **Secret scanning with gitleaks:** ticket #37 adds it as a check.
- **The pre-push git hook** that runs `make ci`: ticket #35.
- **`ci-api`, `ci-web`, `ci-e2e` and the local stack targets** (`up`, `down`, `gen-api`): tickets E05-04 and E05-05, once `api/` and `web/` exist.
- **Dockerfile lint:** E06-04, once a Dockerfile exists.
- **Making `docslint` and `tooling-tests` required before merging:** not done. Branch rulesets (#36) require only `approval-gate` on pull requests, because those two jobs no longer run on pull requests (owner decision, 2026-09-16).
- **A check that fails on skipped tests** (the searches in the `polluxkart-testing` skill): there is no application test code to search until `api/` and `web/` exist; it belongs with those scaffold tickets.
- **Running checks in parallel:** they run one after another so the output stays readable, and today the whole run takes seconds. Worth revisiting when the slow end-to-end checks arrive.
- **Native Windows:** the Makefile and scripts assume a Unix-like system (macOS or Linux). A Windows contributor would use WSL, Windows' built-in Linux environment.

## Open questions for the owner

None open.
All five questions this ticket raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "`make ci` and `make doctor`".
When GitHub runs those workflows was revised on 2026-09-16 ("Local `make ci` is the pull-request gate").
