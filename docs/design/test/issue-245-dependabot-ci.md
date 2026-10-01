# Test plan: E00-13 Run `make ci` on a Dependabot pull request, and only on a Dependabot pull request

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-10-01)**
Ticket: #245 (E00-13).
Design: [../low-level/issue-245-dependabot-ci.md](../low-level/issue-245-dependabot-ci.md)

This ticket has no web requests and writes no database rows.
Its flows are a Dependabot pull request starting the job, every other kind of pull request not starting it, and GitHub refusing a merge while the check is red.
Terms such as Dependabot, job, trigger, required status check, context, fork, skipped job and pending check are explained at the top of the design.

## Words used below

- **Gate:** the job-level `if:` condition that decides whether the job runs. Its two halves are the author check and the same-repository check.
- **Event payload:** the block of data GitHub hands a workflow describing what happened, including who opened the pull request and which repository the branch lives in.
- **Passing partner:** the matching test that passes, which proves a failing test fails for the intended reason and not by accident.
- **Throwaway pull request:** a real pull request opened only to watch the gate, changing one line of a scratch file, closed afterwards.
- **Fake event:** a Python dictionary standing in for an event payload in a unit test, so the gate's logic is tested without GitHub.

## How these tests run

- Unit tests are standard library `unittest` in `tools/checks/test_dependabot_ci.py`, discovered by the existing `checks-tests` entry in `make ci`. They read files as text and never call GitHub.
- The ruleset tests already exist: `tools/rulesets/test_rulesets.py` runs `rulesets.validate` over the real files, so the new required check is validated the moment it is added to `development.json`.
- **Three things no local test can prove**, because they are GitHub's behaviour and not ours: that a skipped job satisfies a required check, that Dependabot's login really is `dependabot[bot]` on this repository, and that a red check really does grey out the merge button. Flow 4 is the live walk-through that proves those, and the ticket is not done without it.
- **Per the owner decision of 2026-09-29, no test below names a dependency version or a commit id.** Where pinning is asserted, it is asserted as a shape (`@` followed by 40 hexadecimal characters), which needs no editing when a version moves. That decision exists because the opposite habit is what broke `development` on #225.

## Flow 1: the gate, as a condition (unit tests)

The gate expression is extracted from the workflow file once and evaluated against fake events.
This is the heart of the ticket, so each row that must not run has a passing partner that must.

| Id | Fake event | Expected | Proves |
|---|---|---|---|
| G1.1 | Author `dependabot[bot]`, branch in `Softogram/polluxkart` | Runs | AC1, the only case that should run |
| G1.2 | Author `CosmicSaaurabh`, branch in this repository | Skips | AC2. Partner: G1.1 |
| G1.3 | Author `some-contributor`, branch in this repository | Skips | AC2 |
| G1.4 | Author `dependabot[bot]`, branch in `someone-else/polluxkart` | Skips | AC3, the fork half. Partner: G1.1 |
| G1.5 | Author `dependabot-preview[bot]`, branch in this repository | Skips | The old bot name is not accepted silently |
| G1.6 | Author `Dependabot[bot]`, different capitalisation | Skips | The comparison is exact, so a near miss fails loudly rather than passing by accident |
| G1.7 | Author `dependabot`, no brackets, branch in this repository | Skips | A real account could be named this; the bracketed form cannot be registered |
| G1.8 | Author `dependabot[bot]`, branch in a fork named to look like ours, for example `Softogram-mirror/polluxkart` | Skips | The comparison is against `github.repository` in full, not a prefix |

## Flow 2: the workflow file (unit tests on its text)

| Id | Check | Expected | Proves |
|---|---|---|---|
| W2.1 | Trigger | `on: pull_request` with types including `opened`, `synchronize` and `reopened` | AC1, and the check re-runs when Dependabot pushes again |
| W2.2 | `pull_request_target` appears nowhere in the file | Passes; a copy using `pull_request_target` fails. Partner | AC4. This job runs pull request code, so it must never hold a writable token |
| W2.3 | Permissions | Top-level `contents: read`; no `write` of any kind anywhere in the file | AC4 |
| W2.4 | No `paths:` or `branches:` filter in the `on:` block | Passes; a copy with `paths:` fails. Partner | AC7. A filtered workflow never reports and would leave the required check pending forever |
| W2.5 | The gate is a job-level `if:`, not a step-level one | The `if:` sits under the job key, above `runs-on` | AC2, AC7. A step-level skip still starts a runner and still spends minutes |
| W2.6 | The run line | Exactly `make ci`; neither `make ci-docs` nor `make ci-tooling` appears | AC5, AC9. Two workflows running one group fails `test_coverage.py` |
| W2.7 | `SCAN_BASE` is set from the pull request's base commit | Present on the `make ci` step | AC5, so the secret scan covers the pull request's commits and not the whole history |
| W2.8 | `fetch-depth: 0` on the checkout | Present | AC5. Without full history the scan has no commit range to walk |
| W2.9 | `persist-credentials: false` on the checkout | Present | AC4. No token is left behind in the checkout's git configuration |
| W2.10 | Every `uses:` line matches `@` plus 40 hexadecimal characters | Passes for every line | AC8, and no version or commit id is named by the test |
| W2.11 | No `${{ ... }}` interpolation appears inside any `run:` line | Passes; a copy with a pull request title inside a `run:` line fails. Partner | AC4. This is the injection hole the board-sync workflow is tested for too |
| W2.12 | The job's name is `dependabot-ci` | Matches the context named in `development.json` | AC6. A rename is what would turn the required check into a permanent pending |
| W2.13 | `timeout-minutes` is present on the job | Present | A hung run fails rather than billing until GitHub's six hour default |
| W2.14 | `concurrency` with `cancel-in-progress: true`, grouped per pull request | Present | A superseded run is dropped instead of being paid for |

## Flow 3: the ruleset file (unit tests, mostly already written)

| Id | Check | Expected | Proves |
|---|---|---|---|
| R3.1 | `dependabot-ci` is in `development.json`'s `required_status_checks`, from the `github-actions` app | Present | AC6 |
| R3.2 | `rulesets.validate` over the real files | No problems. This is `test_real_files_pass`, which already exists and starts covering the new check for free | AC6, AC7 |
| R3.3 | A copy of the files where the job has been renamed in the workflow | `validate` reports "is not a workflow job". Partner: R3.2 | A rename cannot reach GitHub |
| R3.4 | A copy where the workflow has gained a `paths:` filter | `validate` reports "has a path filter and could be skipped". Partner: R3.2 | AC7 |
| R3.5 | A copy where `synchronize` has been removed from the triggers | `validate` reports the lost `synchronize`. Partner: R3.2 | The check would otherwise not re-run on a new commit |
| R3.6 | `approval-gate` is still required | Present and unchanged | Nothing was traded away for the new check |
| R3.7 | `strict_required_status_checks_policy` is still `true`, reviews still `0`, squash still the only merge method | Unchanged | The 2026-09-14 branch rules are untouched |

R3.3, R3.4 and R3.5 are the same three failures `tools/rulesets/test_rulesets.py` already exercises against `approval-gate`.
The new tests point them at `dependabot-ci`, so the protection is proven for this check and not only for the older one.

## Flow 4: the live walk-through on GitHub (once, after the pull request merges)

Nothing in flows 1 to 3 can prove GitHub's side of the bargain. These steps do, and their results are linked on #245.

| Id | Action | Expected | Acceptance criterion |
|---|---|---|---|
| L4.1 | Before the owner applies the ruleset: wait for, or rerun, a real Dependabot pull request, for example #240, #243 or #244 | `dependabot-ci` appears and runs `make ci` to completion, green. Its log ends with the same "all 12 checks passed" line a laptop prints | AC1, AC5 |
| L4.2 | Compare that log's check list with `make ci` on a laptop | The same twelve check names, in the same order | AC5 |
| L4.3 | Open a throwaway pull request from a branch in this repository, as a person | `dependabot-ci` is reported as skipped. The Actions tab shows no runner time billed for it | AC2 |
| L4.4 | The owner runs `make rulesets-apply RULESETS='development'`, then `make rulesets-check` | `rulesets-check` reports no drift, and the nightly `rulesets-drift` run is green again | AC6 |
| L4.5 | Reopen or open a human pull request after the ruleset is applied | `dependabot-ci` shows as skipped, **not** pending, and the merge button is available. If this one step fails, the ruleset change is reverted immediately and the check goes back to advisory | AC7. This is the riskiest assumption in the ticket, and it is the first thing checked after the apply |
| L4.6 | On a Dependabot pull request, make the check red on purpose: a throwaway branch in this repository with a deliberately failing check, opened as a person, confirms the block only for a person, so instead read GitHub's own merge state on the next genuinely red Dependabot pull request | GitHub refuses the merge while `dependabot-ci` is red | AC10 |
| L4.7 | The run logs of every run above | No token value appears, and no pull request title or branch name appears inside a command | AC4 |
| L4.8 | Afterwards | The throwaway pull request is closed and its branch deleted. `make rulesets-check` exits 0 | Clean up |

**On L4.6.** A red Dependabot pull request cannot be manufactured honestly, because Dependabot decides what it opens and when. Two things stand in for it, and the ticket says which was used:
either the next real Dependabot pull request that fails, recorded when it happens, or GitHub's reported merge state read on a Dependabot pull request while the check is still running, which is pending and therefore blocked for the same reason.
Writing a failing check into the repository to force a red run is rejected: it would mean merging a known-broken check into `development`, which is exactly what this ticket exists to prevent.

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #245) | Tests |
|---|---|
| AC1: a Dependabot pull request runs `make ci`, visibly | G1.1, W2.1, L4.1 |
| AC2: nobody else's pull request runs it, and no minutes are spent | G1.2, G1.3, G1.5 to G1.7, W2.5, L4.3 |
| AC3: a branch from a fork cannot start it | G1.4, G1.8 |
| AC4: read-only token, no secrets, no pull request value inside a command | W2.2, W2.3, W2.9, W2.11, L4.7 |
| AC5: the same twelve checks, and the scan covers exactly the pull request's commits | W2.6, W2.7, W2.8, L4.1, L4.2 |
| AC6: `dependabot-ci` required in the file, and the live ruleset agrees | R3.1, R3.2, R3.6, R3.7, L4.4 |
| AC7: a human pull request still merges, skipped rather than pending | W2.4, W2.5, R3.2, R3.4, R3.5, L4.5 |
| AC8: the pinning and gate tests name no version or commit id | W2.10, and a read of the whole test file at review |
| AC9: `make ci` green, including `test_coverage.py` | W2.6, plus the verified `make ci` run pasted in the implementation pull request |
| AC10: a green run and a blocked merge both seen on a real pull request | L4.1, L4.6 |

## What the job gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| GitHub's release downloads | Unreachable while `install_linters.py` runs | The step fails, the check is red, nothing merges. Rerunning the job is the repair | Stated in the design; seen live if it happens |
| A linter download | Hash does not match the pinned one | The installer refuses it and the job fails. Covered already by `tools/checks/test_install_linters.py` | Existing tests |
| The runner | Hangs, or `make ci` genuinely takes too long | `timeout-minutes` cancels it and the check is red | W2.13 |
| Actions minutes | Budget exhausted | The job fails in seconds with no steps. It looks like a broken build but is a billing problem, and with the check required it blocks Dependabot merges until the budget resets | Not testable; written in the design's edge cases and in the runbook |
| The ruleset | Owner has not applied it yet | The check reports but does not block; `rulesets-drift` reports drift nightly | L4.4 |
| Dependabot | Its bot login changes | Every Dependabot pull request would skip and the gate would be silently lost | Only L4.1 can see this, which is why the walk-through is part of the ticket |

## Reachability check

No database rows are written, so the equivalent risk is automation that exists, passes its own tests, and never fires on a real event.
That is precisely the failure this ticket was created to fix, so it is the one thing flow 4 is built around: L4.1 proves the job runs on a real Dependabot pull request, and L4.3 and L4.5 prove it stays out of the way on a real human one.
Flows 1 to 3 alone are not enough evidence to close the ticket.

## Concurrency and replay

No money, stock, coupon or invoice number is involved, so the usual concurrency work does not apply. Two cases still matter:

- **Dependabot pushes twice in quick succession**, which happens on `@dependabot rebase`. The `concurrency` group cancels the superseded run, so the reported result always belongs to the newest commit. Checked by W2.14.
- **A rerun of the same commit** must reach the same result, because `make ci` reads only the checkout and downloads hash-pinned tools. Any difference between two runs of one commit means a flaky check, which is a bug to fix rather than a result to rerun past, and the house rule is to fix it even when it was not caused by the work in hand.

## What is deliberately not covered, and why

- **Pull requests from people running `make ci` on GitHub.** The pre-push hook is that gate (owner decision, 2026-09-16). L4.3 and L4.5 only prove this workflow stays out of their way.
- **Whether `make ci`'s twelve checks are each correct.** Each already has its own tests. This plan proves the twelve are run, not that each one works.
- **Forcing a red Dependabot pull request.** See the note under L4.6.
- **A fork's ability to spend runner minutes on its own copy of a workflow.** That is a repository-wide GitHub setting, unchanged by this ticket, and listed as out of scope in the design.
- **The `legacy/` alerts.** A separate owner decision of 2026-10-01 and a separate ticket.
