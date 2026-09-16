# Test plan: E00-08 Dependency updates and code scanning configuration

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #38 (E00-08).
Design: [../low-level/issue-38-dependabot-codeql.md](../low-level/issue-38-dependabot-codeql.md)

This ticket has no web requests.
Its flows are Dependabot's pull requests, CodeQL's analysis, the merge rule for findings, and the pin check.
Terms such as Dependabot, ecosystem, CodeQL, advanced setup and pinned are explained at the top of the design.

## Words used below

- **Parsed configuration:** the YAML files read by a small standard library reader in the test, which understands only the shapes these files use and fails loudly on anything else.
- **Passing partner:** the matching test that passes, proving a failing test fails for the intended reason.

## How these tests run

- Automated tests are standard library `unittest` files in `tools/checks/`, run by `checks-tests` and `workflow-pins` in `make ci` and the `tooling-tests` workflow.
- Configuration mistakes GitHub itself would catch are also checked live once, because only GitHub can prove Dependabot and CodeQL accept the files.
- Live checks are done by hand in the rollout order, with results recorded on #38 (counts and pass or fail only, never alert details).

## Flow 1: the pin check (`workflow_pins.py`, unit tests)

| Id | `uses:` line | Expected |
|---|---|---|
| P1.1 | The real `.github/workflows/*.yml` | Passes |
| P1.2 | `actions/checkout@<40 hex> # v7.0.1` | Passes |
| P1.3 | `actions/checkout@v7` | Fails, naming file, line and "not pinned to a commit". Partner: P1.2 |
| P1.4 | `actions/checkout@main` | Fails |
| P1.5 | `actions/checkout@<39 hex> # v7.0.1` (one character short) | Fails |
| P1.6 | `actions/checkout@<40 hex>` with no version comment | Fails: "add the version as a comment" |
| P1.7 | `github/codeql-action/init@<40 hex> # v4.1.0` (an action in a subfolder) | Passes |
| P1.8 | `./.github/actions/local` | Passes |
| P1.9 | `docker://alpine@sha256:<64 hex>` | Passes |
| P1.10 | `docker://alpine:3.20` | Fails |
| P1.11 | `uses:` inside a YAML comment line | Ignored |
| P1.12 | In `make ci` on a repository copy with P1.3's line added to a workflow | The `workflow-pins` check fails and the other checks still run |

## Flow 2: `dependabot.yml` (unit tests on the parsed configuration)

| Id | Case | Expected |
|---|---|---|
| D2.1 | The real file | Passes: version 2; a `github-actions` entry at `/`, targeting `development`, weekly on Monday 09:00 Asia/Kolkata, one group covering major, minor and patch |
| D2.2 | A `maven` entry with the group and the major-version ignore | Passes |
| D2.3 | A `maven` entry without the major-version ignore | Fails, naming the entry. Partner: D2.2 |
| D2.4 | An `npm` or `docker` entry without a group | Fails |
| D2.5 | Any entry targeting `main` | Fails: updates go to `development` |
| D2.6 | A `github-actions` entry that ignores majors | Fails: Actions majors are proposed, per the owner's answer |
| D2.7 | An entry for a folder that does not exist in the repository | Fails, because GitHub would report a configuration error |
| D2.8 | An `open-pull-requests-limit: 0` or an auto-merge setting | Fails: updates must be proposed, and only the owner merges |

## Flow 3: CodeQL configuration (unit tests)

| Id | Case | Expected |
|---|---|---|
| Q3.1 | The real `codeql.yml` | Triggers on `pull_request` with no path filter, on pushes to `development` and `main`, and weekly; job permissions include `security-events: write` and nothing else writable; languages exactly `actions` and `python` |
| Q3.2 | `codeql.yml` with a `paths:` filter on `pull_request` | Fails: the merge rule would wait forever on skipped pull requests. Partner: Q3.1 |
| Q3.3 | The real `codeql-config.yml` | `paths-ignore` contains `legacy/**` |
| Q3.4 | A language in the matrix for a folder that does not exist (for example `java-kotlin` before `api/`) | Fails, naming the language |
| Q3.5 | `api/` exists but `java-kotlin` is missing from the matrix | Fails, so the Maven skeleton ticket cannot forget it |
| Q3.6 | #36's `validate` on the real `development.json` | The code scanning rule exists with tool CodeQL, security threshold `high_or_higher` and alerts threshold `none` |
| Q3.7 | `validate` with the threshold changed to `critical` | Fails, citing the 2026-09-14 decision. Partner: Q3.6 |
| Q3.8 | `validate` on `repository.json` | Security updates on, CodeQL default setup off |

## Flow 4: live checks on GitHub (by hand, once, in rollout order)

| Id | Action | Expected | Acceptance criterion |
|---|---|---|---|
| L4.1 | After merge, the repository's Dependabot page | No configuration errors; the `github-actions` update job ran or is scheduled | AC1 |
| L4.2 | `make rulesets-apply` then `make rulesets-check` with the owner's login | Default setup off, security updates on; exit 0 | AC3 |
| L4.3 | Dispatch the `codeql` workflow by hand, then the first push to `main` after it exists | Both languages complete; results appear in the Security tab under the `codeql` workflow's categories | AC3 |
| L4.4 | The Security tab after L4.3 | No open CodeQL alert has a path under `legacy/` from the new workflow | `legacy/` is skipped |
| L4.5 | The one-time dismissal step | The open Dependabot and CodeQL alert counts under `legacy/` drop to zero; each dismissed alert shows reason and dated comment. Record the before and after counts only | Legacy alerts dismissed |
| L4.6 | Whether a Dependabot auto-triage rule can match `legacy/` | Recorded yes or no on #38; if yes, the rule exists; if no, the runbook step exists | Future legacy alerts |
| L4.7 | The first Dependabot `github-actions` group pull request | Passes the approval gate as Dependabot's without a ticket, is not held for a CodeQL job, and is merged by the owner | AC2 |

L4.3 is a hand dispatch and a release push, because CodeQL does not run on pull requests.

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #38, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: GitHub reports no Dependabot configuration errors | D2.1, D2.7, L4.1 |
| AC2: a Dependabot pull request for a GitHub Action passes the gate without a ticket and runs every required check | L4.7 |
| AC3: CodeQL runs on `main`, weekly, and by hand for every language present, with results in the Security tab | Q3.1, Q3.4, Q3.5, L4.3 |
| AC4: every `uses:` line is pinned to a full commit | P1.1 to P1.12 |
| AC5: only the owner merges Dependabot pull requests | Written rule reviewed in the implementation pull request; L4.7 merged by the owner; D2.8 |
| Grouped weekly updates; majors skipped except Actions | D2.1 to D2.6 |
| High or critical findings are reported in the Security tab; they do not block pull-request merges | L4.3 |
| `legacy/` is not scanned and its alerts are dismissed with a dated reason | Q3.3, L4.4, L4.5, L4.6 |
| Security updates are on | Q3.8, L4.2 |

## What the owner gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| CodeQL | Fails or times out | The weekly or `main` run is red; pull requests are not held waiting | Q3.2 covers the skipped case; stated in the design |
| Dependabot | Configuration error | Shown on the Dependabot page; D2.7 prevents the known cause | L4.1 |
| GitHub default setup | Switched back on | Advanced uploads refused; the owner's `make rulesets-check` reports it | Q3.8, L4.2 |

## Reachability check

No database rows are written.
The equivalent risk is configuration that exists but never takes effect: L4.1, L4.3 and L4.7 prove GitHub actually ran Dependabot and CodeQL from these files.

## What is deliberately not covered, and why

- **Java and TypeScript analysis, and Maven, pnpm and Docker updates:** those folders do not exist yet; Q3.5 and D2.2 to D2.4 make sure their tickets add them correctly.
- **The quality of CodeQL's own rules:** that is GitHub's product; these tests prove the wiring and the merge rule.
- **Alert details in any record:** the repository is public, so only counts are recorded.
