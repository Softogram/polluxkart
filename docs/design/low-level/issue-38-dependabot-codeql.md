# E00-08 Dependency updates and code scanning configuration

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #38 (E00-08), part of epic #10.
Test plan: [../test/issue-38-dependabot-codeql.md](../test/issue-38-dependabot-codeql.md)
Depends on: #34 (`make ci`) and #36 (the ruleset and settings files, and the script that applies them).

## Words used below

- **Dependency:** a library the code uses but did not write, such as Spring Boot or a GitHub Action.
- **Dependabot:** GitHub's bot that opens pull requests to update dependencies.
- **Version update:** Dependabot's scheduled pull request moving a dependency to its newest version.
- **Security update:** a pull request Dependabot opens as soon as a vulnerability is published for a dependency in use.
- **Dependabot alert:** GitHub's private notice that a dependency in the repository has a known vulnerability.
- **Ecosystem:** one kind of dependency list: GitHub Actions, Docker images, Maven (Java) or pnpm (JavaScript).
- **Major, minor and patch versions:** in `4.1.2`, `4` is major (may break things), `1` is minor (new features), `2` is patch (fixes only).
- **CodeQL:** GitHub's code scanner, which looks for security bugs such as injection or unsafe input handling.
- **Default setup and advanced setup:** CodeQL switched on in GitHub settings with no file, or run by a workflow file kept in the repository.
- **Code scanning alert:** a CodeQL finding, with a severity: critical, high, medium or low.
- **Pinned to a commit:** a workflow step names an action by its exact 40-character commit id instead of a movable tag like `v7`, so nobody can change the code it runs by moving the tag.
- **Supply-chain risk:** harm that arrives through a dependency, such as a hijacked library release.

## What was already decided before this document

- **Latest Java, Spring Boot and PostgreSQL; Java 25 LTS proposed** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Versions: the latest Java, Spring Boot and PostgreSQL").
- **Backend Java with Spring Boot; frontend Next.js with TypeScript** (owner decisions, 2026-09-13).
- **Contributors merge into `development`; no required review; no bypass; rules as files applied by script** (owner decision, 2026-09-14, "Branch rules for `development` and `main`").
- **`make ci` and its checks; pinned linters** (owner decision, 2026-09-14, "`make ci` and `make doctor`").
- **Dependencies and code scanning** (owner decision, 2026-09-14, "Dependabot and CodeQL", answered while planning this ticket):
  - only the owner merges Dependabot pull requests;
  - updates are grouped, one weekly pull request per ecosystem for minor and patch updates;
  - major updates are skipped for Maven, pnpm and Docker and left to planned tickets, but still proposed for GitHub Actions;
  - CodeQL moves to advanced setup, a workflow file in the repository;
  - a new high or critical CodeQL security finding is reported in the Security tab from the weekly and release runs; it does not block pull-request merges, because CodeQL does not run on every pull request (revised 2026-09-16);
  - the alerts from `legacy/` are dismissed with a dated reason, and `legacy/` is not scanned;
  - Dependabot security updates are switched on.

## The problem

- No `dependabot.yml` exists, so nothing proposes updates, and the stack's upgrade policy ("patch releases within a month, through Dependabot") has no mechanism ([stack.md](../../platform/stack.md)).
- CodeQL runs in default setup: its configuration is invisible in pull requests, it cannot skip folders, and it scans `legacy/`, the first version kept only as reference.
- The Security tab is full of alerts from `legacy/`, which is never deployed, so a real alert in new code would be easy to miss.
- Nothing checks that every workflow action stays pinned to a commit.

## The change

### Files

```
.github/dependabot.yml                     new: version updates
.github/workflows/codeql.yml               new: CodeQL advanced setup
.github/codeql/codeql-config.yml           new: skips legacy/
tools/checks/workflow_pins.py              new: checks every uses: line is pinned
tools/checks/test_workflow_pins.py         new
tools/checks/checks.py                     changed: adds the workflow-pins check to the tooling group
.github/rulesets/development.json          not given a code scanning merge rule (owner decision, 2026-09-16)
.github/rulesets/repository.json           changed: security updates on, CodeQL default setup off
tools/rulesets/rulesets.py                 changed: applies and checks the CodeQL default setup state
```

### `.github/dependabot.yml`

Today only GitHub Actions has dependencies, so only that entry exists.
Dependabot reports a configuration error for an ecosystem whose folder has no dependency files, so the other entries are added by the tickets that create those files.

```yaml
# Dependency updates. Rules: docs/platform/security.md, "Dependencies and scanning".
# Only the owner merges Dependabot pull requests (owner decision, 2026-09-14).
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    target-branch: development
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: Asia/Kolkata
    groups:
      github-actions:
        patterns: ["*"]
        update-types: [major, minor, patch]
```

**The entry each later ticket adds**, written in `tools/checks/README.md` so it is copied exactly:

```yaml
  - package-ecosystem: maven          # or npm for pnpm, or docker
    directory: /api                   # or /web, or the Dockerfile's folder
    target-branch: development
    schedule: { interval: weekly, day: monday, time: "09:00", timezone: Asia/Kolkata }
    groups:
      maven:
        patterns: ["*"]
        update-types: [minor, patch]
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
```

| Ecosystem | Added by | Majors |
|---|---|---|
| GitHub Actions | this ticket | proposed (grouped with minor and patch) |
| Maven, `/api` | E03-02 (Maven skeleton) | skipped; a planned ticket |
| pnpm (Dependabot's `npm` ecosystem reads `pnpm-lock.yaml`), `/web` | E04-01 (Next.js scaffold) | skipped; a planned ticket |
| Docker | E06-04 (container images) | skipped; a planned ticket |

A test (below) fails if a Maven, npm or Docker entry lacks the major-version `ignore` or the group, so a later ticket cannot forget them.

**Security updates** are separate from this file: switched on in repository settings, they open a pull request for a vulnerable dependency straight away, one per vulnerability.
The major-version `ignore` does not stop them; if the only fixed version is a new major, Dependabot still proposes it, because a known hole outweighs an upgrade surprise.

**Merging Dependabot pull requests.**
They pass the approval gate without a ticket (unchanged), and must pass every required check like any pull request.
Only the owner merges them.
GitHub's branch rules cannot single out Dependabot pull requests, so this is a written rule in `development-process.md`, `CLAUDE.md` and the `polluxkart-workflow` skill; agents do not merge them on their own initiative.

### CodeQL advanced setup

`.github/workflows/codeql.yml`:

```yaml
name: codeql

on:
  push:
    branches: [main]
  schedule:
    - cron: "30 3 * * 1"   # weekly, so new CodeQL rules reach unchanged code
  workflow_dispatch:

permissions:
  contents: read

jobs:
  analyze:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    permissions:
      contents: read
      security-events: write   # upload results to the Security tab
    strategy:
      fail-fast: false
      matrix:
        language: [actions, python]
    steps:
      - uses: actions/checkout@<commit> # v7.0.1
        with:
          persist-credentials: false
      - uses: github/codeql-action/init@<commit> # vX.Y.Z
        with:
          languages: ${{ matrix.language }}
          build-mode: none
          config-file: ./.github/codeql/codeql-config.yml
      - uses: github/codeql-action/analyze@<commit> # vX.Y.Z
        with:
          category: "/language:${{ matrix.language }}"
```

`.github/codeql/codeql-config.yml`:

```yaml
name: polluxkart
paths-ignore:
  - legacy/**
```

- **Languages now:** `actions` (the workflow files) and `python` (the repository tooling).
  E03-02 adds `java-kotlin` and E04-01 adds `javascript-typescript`, both with `build-mode: none`, which analyses the source without building it.
- **No path filters on the triggers.** CodeQL does not run on pull requests (owner decision, 2026-09-16), so there is no merge rule waiting for pull-request results.
- The `<commit>` values are the newest release commits at implementation time.
- **Default setup is switched off** before the workflow first uploads, because GitHub refuses results from advanced setup while default setup is on.
  `repository.json` records "default setup: off", and `rulesets.py apply` and `check` handle it (admin login only, like the other security settings).

### Blocking merges on findings

Not used. A high or critical finding cannot block a pull request if CodeQL does not run on that pull request (owner decision, 2026-09-16).
Findings from the weekly and `main` runs stay in the Security tab for the owner to fix or dismiss.
`development.json` does not gain a `code_scanning` rule.
#36's `validate` does not require one.

### The alerts from `legacy/`

A one-time step during rollout, run with the owner's login and recorded as a comment on #38 (counts only, no details):

1. Dismiss every open Dependabot alert whose dependency file is under `legacy/`, with reason "not used" and the comment "2026-MM-DD: legacy/ is the first version, kept as reference and never deployed (see docs/legacy/README.md)".
2. Dismiss every open CodeQL alert under `legacy/` from the old default setup, with reason "won't fix" and the same comment.
3. Where GitHub's Dependabot auto-triage rules can match by dependency file path, add one that dismisses future alerts under `legacy/` with the same reason. If they cannot, `docs/platform/runbook.md` says to dismiss such an alert by hand with the same comment when GitHub emails about it.

Dismissing never deletes an alert: it stays visible under "closed" with its reason and date.

### Every action pinned (`tools/checks/workflow_pins.py`)

Added to `CHECKS` as `workflow-pins` in the `tooling` group.
For every `uses:` line in `.github/workflows/*.yml`:

| Form | Accepted when |
|---|---|
| `owner/repo@...` or `owner/repo/path@...` | followed by a 40-character hexadecimal commit id and a `# vX` version comment |
| `./path` (an action in this repository) | always |
| `docker://image@...` | pinned by `sha256:` digest |

Anything else, such as `@v7` or `@main`, fails with the file, line and reason.
Dependabot keeps the pins current and updates the version comments with them.

### Documents updated in the implementation pull request

- `docs/platform/security.md`, "Dependencies and scanning": grouped weekly updates, majors policy, security updates, advanced CodeQL, the merge-blocking threshold, `legacy/` excluded, pins checked.
- `docs/platform/development-process.md`: Dependabot pull requests pass the gate, and only the owner merges them.
- `docs/platform/stack.md`, "Upgrade policy": majors for Maven, pnpm and Docker go through a planned ticket.
- `docs/platform/runbook.md`: handling a Dependabot pull request, a security update and a CodeQL alert; dismissing a `legacy/` alert.
- `CLAUDE.md` and the `polluxkart-workflow` skill: the Dependabot merge rule.
- `tools/checks/README.md`: the Dependabot entry template for later tickets.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A grouped weekly pull request breaks a check | It cannot merge; the owner closes it or asks for it to be split, and Dependabot's commands on the pull request can ignore the one bad dependency |
| A security update needs a new major version | Dependabot still opens it; it gets the same checks and the owner decides |
| Dependabot updates a workflow action | `workflow-pins` checks the new pin; actionlint checks the file; the approval gate passes it as Dependabot's |
| A pull request adds a high CodeQL finding | The pull request can merge; the weekly or `main` run reports it in the Security tab |
| CodeQL fails to run or times out | The weekly or `main` run is red; pull requests are not held waiting |
| A CodeQL run on a Dependabot pull request | The workflow grants `security-events: write` for the job; the first Dependabot pull request proves results arrive (test plan) |
| A later ticket adds `api/` without the Maven Dependabot entry | Nothing fails automatically for a missing entry; the Maven skeleton ticket's design lists it, and the test fails if an entry exists without the ignore rule and group |
| Default setup switched back on in settings | The advanced workflow's uploads are refused and the owner's `make rulesets-check` reports the setting |
| A new alert under `legacy/` | Auto-dismissed if the rule was possible; otherwise dismissed by hand per the runbook |
| An action pinned by commit with no version comment | `workflow-pins` fails, because reviewers cannot tell which version it is |

## What is deliberately not covered

- **osv-scanner in `make ci`:** the backend and frontend CI tickets.
- **Secret scanning:** #37.
- **Maven, pnpm and Docker Dependabot entries, and Java and TypeScript CodeQL:** added by E03-02, E04-01 and E06-04, which create those folders.
- **Deleting `legacy/` or its dependency files:** the owner chose dismissal; the reference copy stays whole.
- **Auto-merging Dependabot pull requests:** only the owner merges them.

## Open questions for the owner

None open.
All seven questions this ticket raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Dependabot and CodeQL".
When CodeQL runs, and that it does not block pull-request merges, was revised on 2026-09-16 ("Local `make ci` is the pull-request gate").
