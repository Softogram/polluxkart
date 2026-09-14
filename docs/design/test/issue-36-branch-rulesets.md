# Test plan: E00-06 Branch rulesets on `development` and `main`

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #36 (E00-06).
Design: [../low-level/issue-36-branch-rulesets.md](../low-level/issue-36-branch-rulesets.md)

This ticket has no web requests.
Its "flows" are the approval gate's decision, the rules script, and GitHub's own enforcement.
Terms such as ruleset, bypass, required check and release pull request are explained at the top of the design.

## Words used below

- **Fake `gh`:** a small Python object standing in for the GitHub CLI in unit tests. It returns prepared answers and records every call, so tests never reach GitHub.
- **Rehearsal branch:** a throwaway branch given a copy of the real rules for the live tests, so a mistake can never harm `development` or `main`.
- **Read back:** asking GitHub which rules apply to a branch (`gh api repos/<repo>/rules/branches/<branch>`), which changes nothing.
- **Passing partner:** the matching test that passes, proving a failing test fails for the intended reason.

## How these tests run

- Unit tests are standard library `unittest` files:
  - `tools/approval_gate/test_gate.py`, run by the existing `approval-gate-tests` check;
  - `tools/rulesets/test_rulesets.py`, run by the new `rulesets-tests` check.
  Both run in `make ci` and in the `tooling-tests` workflow.
- No unit test calls GitHub or the network.
- The live tests on GitHub are run once, by hand, in the order of the design's rollout.
  Every result, with the command and GitHub's exact answer, is pasted into the implementation pull request (rehearsal) or a comment on #36 (real branches).
- **Safety rule for live tests:** no live test ever attempts a change on `development` or `main` that would do harm if the rule were missing.
  Pushes, force pushes, deletions and wrong merge methods are only attempted on rehearsal branches.
  On the real branches, rules are read back first, and a merge is only attempted on a pull request that must be refused, after the read back confirms the rule is there.

## Flow 1: the approval gate and `main` (unit tests in `test_gate.py`)

| Id | Pull request | Expected | Proves |
|---|---|---|---|
| G1.1 | From this repository's `development` into `main`, no ticket line | Pass, message "Release pull request from development into main" | AC: releases pass the gate |
| G1.2 | From this repository's `feature/x` into `main`, with a valid `Implements #N` for an approved ticket | Fail, "must come from this repository's development branch". Partner: G1.1 | AC: only development into main |
| G1.3 | From a fork's branch named `development` into `main` | Fail, same message. Partner: G1.1 | A fork cannot pose as a release |
| G1.4 | Into `main` with the head repository missing (the fork was deleted) | Fail, same message | Missing data never passes |
| G1.5 | By `dependabot[bot]` into `main` | Fail. Partner: the existing test that Dependabot into `development` passes | The `main` rule runs before the exemption |
| G1.6 | From `development` into `main` whose description also says `Implements #999`, a ticket that does not exist | Pass | Ticket lines in a release are ignored, so a release never depends on old ticket state |
| G1.7 | Into `development` from `feature/x`, with no ticket line | Fail with the existing "Link this pull request" message | Pull requests into `development` are unchanged |
| G1.8 | Every existing test in `test_gate.py`, now given `base_ref="development"` | All still pass | The new inputs did not change the old rules |
| G1.9 | `pull_context(pull)` given a GitHub pull request with `head.repo` set to null | Returns head repository "none", which G1.4 then fails | `main()` reads the new inputs safely |

## Flow 2: `rulesets.py validate` (unit tests in `test_rulesets.py`)

The functions take the rule files and workflow texts as inputs, so failing cases use edited copies in memory.

| Id | Case | Expected |
|---|---|---|
| V2.1 | The real `.github/rulesets/*.json` and `.github/workflows/*.yml` | Passes |
| V2.2 | A required check `docslint` while the job is renamed `docs-lint` | Fails, naming `docslint` and the branch. Partner: V2.1 |
| V2.3 | The `docs` workflow gains `paths: ['docs/**']` under `pull_request` | Fails: a required check could be skipped |
| V2.4 | The `approval-gate` workflow's `pull_request_target` types lose `synchronize` | Fails: the check would not re-run on new commits, so an up-to-date branch could never pass |
| V2.5 | `development.json` gains a bypass | Fails: only `main-owner-merge` may have one |
| V2.6 | `main-owner-merge.json` bypass mode changed to `always` | Fails: pull requests only |
| V2.7 | `main-owner-merge.json` gains a second rule | Fails: its only rule is restrict updates |
| V2.8 | `development.json` allows `merge` as well as `squash` | Fails, citing the 2026-09-14 decision |
| V2.9 | `main.json` allows `squash` | Fails, citing the decision |
| V2.10 | `strict_required_status_checks_policy` false on either branch | Fails: up to date is required |
| V2.11 | `required_approving_review_count` set to 1 | Fails: no required review was decided |
| V2.12 | A file with a numeric `actor_id` or `integration_id` | Fails: accounts and apps are written by name in this public repository |
| V2.13 | Two files with the same ruleset name, or a file that is not valid JSON | Fails, naming the file |

## Flow 3: `rulesets.py check` (unit tests with a fake `gh`)

| Id | Live state returned by the fake `gh` | Expected |
|---|---|---|
| K3.1 | Exactly the files, with bypass lists visible | Exit 0, "GitHub matches the rule files" |
| K3.2 | `docslint` missing from `development`'s required checks | Exit 1, the difference names the ruleset, the rule and the check. Partner: K3.1 |
| K3.3 | `main` ruleset absent | Exit 1, "ruleset main is missing on GitHub" |
| K3.4 | An extra ruleset `temp` on GitHub | Exit 1, "ruleset temp is on GitHub but not in the files" |
| K3.5 | `main` enforcement set to `disabled` | Exit 1, naming it |
| K3.6 | Rebase merging switched back on | Exit 1, naming the setting |
| K3.7 | Bypass lists absent from GitHub's answer (a login without admin rights) and everything else matching | Exit 0, with the line "bypass lists not visible with this login; run with an admin login for the full check" |
| K3.8 | Bypass lists visible, and the owner's bypass removed from `main-owner-merge` | Exit 1. Partner: K3.7, proving hidden is not treated as matching when visible |
| K3.9 | The `gh` call fails (not logged in, or network error) | Exit 1 with the error, never "matches" |
| K3.10 | The login name in the files does not exist on GitHub | Exit 1 before comparing, naming the login |

## Flow 4: `rulesets.py apply` (unit tests with a fake `gh`)

| Id | Case | Expected |
|---|---|---|
| A4.1 | No rulesets on GitHub | Three create calls, each with names resolved to numbers; one settings update with exactly the four managed settings; exit 0 |
| A4.2 | All three exist but `development` differs | One update call for `development`, matched by name; no calls for the others; exit 0 |
| A4.3 | `--dry-run` with differences | Prints each planned change; the fake `gh` records no write calls; exit 0 |
| A4.4 | An unmanaged ruleset exists | Warning naming it; no delete call |
| A4.5 | GitHub refuses the first write with 403 or 404 | Exit 1, "an admin login is needed"; no further write calls |
| A4.6 | An app or login name cannot be resolved | Exit 1 before any write call |
| A4.7 | The request bodies sent | Contain no field outside GitHub's ruleset format: the name-based fields are translated, not passed through |

## Flow 5: GitHub's enforcement (live, once)

### Rehearsal, before the implementation pull request merges

Two throwaway branches, `ruleset-rehearsal-dev` and `ruleset-rehearsal-main`, both cut from the implementation branch, get rulesets `rehearsal-dev`, `rehearsal-main` and `rehearsal-main-owner-merge` with the same rules as the real files, targeting those branch names.
Throwaway pull requests are opened from short-lived branches, say `Plans #36` where the gate must pass, and are closed without merging unless the step says otherwise.

| Id | Action | Expected answer from GitHub | Acceptance criterion |
|---|---|---|---|
| R5.1 | `git push` a new commit straight to `ruleset-rehearsal-dev` | Refused, naming the pull request rule | A direct push is refused |
| R5.2 | Force push an older commit to `ruleset-rehearsal-dev` | Refused, naming the force push rule | A force push is refused |
| R5.3 | Delete `ruleset-rehearsal-dev` | Refused | Deletion is blocked |
| R5.4 | Pull request whose change breaks a docs link; wait for `docslint` to fail; `gh pr merge --squash` | Refused: required check failing | A failing docs check cannot merge |
| R5.5 | Pull request with no ticket line; wait for `approval-gate` to fail; `gh pr merge --squash` | Refused: required check failing | A failing gate cannot merge |
| R5.6 | Pull request with every check passing; `gh pr merge --merge` | Refused: merge method not allowed | Squash only into development |
| R5.7 | Two passing pull requests; squash-merge the first; try the second | Refused as out of date; after "Update branch" and green checks, it merges | Up to date is required |
| R5.8 | Partner of R5.4 to R5.7: a passing, up-to-date pull request, `gh pr merge --squash` | Merges | The rules allow the right path |
| R5.9 | Pull request into `ruleset-rehearsal-main`, all checks passing; `gh pr merge --squash` | Refused: merge method | Merge commit only into main |
| R5.10 | Same pull request, `gh pr merge --merge` with the owner's login | Merges, through the owner's pull-request-only bypass of restrict updates | The owner can merge into main |
| R5.11 | `git push` a new commit straight to `ruleset-rehearsal-main` with the owner's login | Refused | The owner's exception does not allow direct pushes |
| R5.12 | Read back the rules for `ruleset-rehearsal-main` | Lists pull request, required checks, non fast forward, deletion and update rules | The two main rulesets combine as designed |

Then delete the rehearsal rulesets, branches and pull requests, and confirm with a read back that no rehearsal ruleset remains.

The rehearsal cannot test the gate's `main` rule, because that rule looks for the branch literally named `main`; G1.1 to G1.5 cover it, and L5.5 below checks it live.

### The real branches, after the rollout

| Id | Action | Expected |
|---|---|---|
| L5.1 | After step 3: read back the rules for `development` | Exactly the `development` ruleset's rules |
| L5.2 | After step 3: `make rulesets-check` with the owner's login | Exit 0 for `development` and the settings; `main` rulesets reported missing, which is expected until step 5 |
| L5.3 | Step 4: the first release pull request | `approval-gate` does not run (not yet on `main`), `docslint` and `tooling-tests` pass; merged with a merge commit |
| L5.4 | After step 5: read back the rules for `main`; `make rulesets-check` with the owner's login | Both rulesets present with their rules; exit 0 with bypass lists compared |
| L5.5 | After L5.4 confirms the rules: open a pull request from a throwaway feature branch into `main`; wait for `approval-gate`; `gh pr merge --merge` | The gate fails with the "must come from development" message; the merge is refused. Close the pull request |
| L5.6 | Run the `rulesets-drift` workflow by hand | Green, with the "bypass lists not visible" line |

The ticket moves to `stage: done` only when L5.1 to L5.6 are recorded on #36.

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #36, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| A direct push to `development` or `main` is refused | R5.1, R5.11, L5.1, L5.4 |
| A force push to either branch is refused | R5.2, L5.1, L5.4 |
| A pull request with a failing docs check cannot be merged | R5.4 |
| A pull request whose approval gate fails cannot be merged | R5.5, L5.5 |
| Review, bypass and merge settings match the owner's answers | V2.5 to V2.11, R5.6, R5.9, R5.10, K3.1, L5.4 |
| Only the owner may merge into `main` | R5.10, R5.12, L5.4 (see "not covered" for a second account) |
| A branch must be up to date before merging | R5.7, V2.10 |
| Only `development` may open pull requests into `main`, and releases pass the gate | G1.1 to G1.5, L5.5 |
| Required check names match workflow job names | V2.2 to V2.4 |
| The rules are saved as files, applied by a script, and drift is caught | V2.1, A4.1 to A4.7, K3.1 to K3.10, L5.6 |

## What the owner gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| GitHub API | Unreachable, or `gh` not logged in | `check` and `apply` exit 1 with the error; never a false "matches" | K3.9 |
| GitHub permissions | Login is not admin | `apply` stops at the first refusal; `check` still compares what it can see and says what it could not | A4.5, K3.7 |
| GitHub Actions | A required workflow fails to start | The pull request waits with the check pending and cannot merge; re-run it | Covered by R5.4 and R5.5, which prove pending or failing checks block |
| Scheduled workflow | Paused after 60 days of no activity | No drift reports until re-enabled; the runbook says so | Not automated; stated in the design |

## Reachability check

This ticket writes no database rows.
The equivalent risk is a rule written in a file but never applied, or a check required but never run.
L5.2 and L5.4 prove the files reached GitHub; V2.2 to V2.4 prove every required check is produced by a workflow that runs.

## Concurrency and replay

- Running `apply` twice gives the same result: the second run finds no differences and makes no write calls (A4.2 with identical input).
- Two pull requests racing to merge are handled by the up-to-date rule (R5.7).
- No money, stock, coupons or invoice numbers are involved.

## Verified test run, recorded in the implementation pull request

- Local `make ci` output, including `approval-gate-tests` and `rulesets-tests`.
- The green `docs`, `tooling-tests` and `approval-gate` runs for the pull request.
- The rehearsal results R5.1 to R5.12, pasted with GitHub's answers.
- `make rulesets-apply --dry-run` output against the live repository, showing exactly the planned changes.

## What is deliberately not covered, and why

- **A second account failing to merge into the live `main`:** no second account with write access exists. R5.10 and R5.12 prove the mechanism; the first contributor with write access confirms it for real, recorded on #36 then.
- **Any live push, force push, deletion or wrong merge method against the real `development` or `main`:** if a rule were missing, the attempt itself would do harm. Rehearsal branches carry those tests instead.
- **The gate running on pull requests into `main` before the first release:** it cannot run there until `main` contains it; that is why the rollout orders steps 3 to 5.
- **CodeQL, later CI checks, deploy approvals:** their own tickets, #38, E05-05 and E06-06.
