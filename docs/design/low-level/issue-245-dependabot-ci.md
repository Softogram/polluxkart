# E00-13 Run `make ci` on a Dependabot pull request, and only on a Dependabot pull request

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-10-01)**
Ticket: #245 (E00-13), part of epic #10.
Test plan: [../test/issue-245-dependabot-ci.md](../test/issue-245-dependabot-ci.md)
Depends on: nothing outstanding. #34 gave us `make ci`, #35 the pre-push hook, #36 the rulesets, #38 Dependabot itself, and #237 removed the hard-coded commit id that this gate would have caught.

## Words used below

- **Dependabot:** GitHub's own bot that opens pull requests to upgrade dependencies. It runs on GitHub's servers, not on anybody's laptop.
- **`make ci`:** the single command that runs every check a pull request must pass. Twelve checks today, listed in `tools/checks/checks.py`.
- **Workflow:** a file under `.github/workflows/` describing work for GitHub to run. **Job:** one named unit of that work. **Trigger:** the event that starts it.
- **Runner:** the throwaway virtual machine GitHub rents us to run a job on. Its time is metered and billed, which is why this repository runs so little on GitHub.
- **Status check:** the tick or cross a job leaves on a pull request. A **required status check** is one GitHub refuses to merge without.
- **Ruleset:** GitHub's rules for a branch, kept as files in `.github/rulesets/` and pushed to GitHub with `make rulesets-apply`.
- **Context:** the name a required status check is matched by. It is the job's name, not the workflow's.
- **Fork:** somebody else's copy of this public repository. A pull request from a fork carries code we have never seen.
- **Skipped job:** a job whose `if:` condition was false. GitHub records it as finished, with the result "skipped".
- **Pending check:** a check GitHub is still waiting for. A required check that stays pending blocks the merge button forever.

## What was already decided before this document

- **A workflow runs `make ci` on `pull_request`, but only when the author is Dependabot** (owner decision, 2026-09-29, [decisions.md](../../platform/decisions.md), "A Dependabot pull request runs `make ci` before merge").
- **The new check becomes a required check in the `development` ruleset** (owner decision, 2026-10-01, "The Dependabot CI check is required on `development`").
- **GitHub Actions does not run the checks on a pull request a person opens into `development`.** The local pre-push hook is that gate, and Actions CI runs at release (owner decision, 2026-09-16, "Local `make ci` is the pull-request gate; GitHub Actions CI runs at release").
- **An agent may merge a Dependabot pull request once every required check is green**, and until this ticket ships, whoever merges runs `make ci` on the branch by hand first (owner decision, 2026-09-23, corrected 2026-09-29, "Who merges a Dependabot pull request").
- **No test names an exact dependency version or commit id** (owner decision, 2026-09-29).
- **Every `uses:` line in every workflow is pinned to a 40 character commit id with a version comment**, enforced by the `workflow-pins` check (owner decision, 2026-09-14, "Dependabot and CodeQL").
- **`development` allows only squash merges, requires no reviews, and requires an up-to-date branch** (owner decision, 2026-09-14, "Branch rules for `development` and `main`").
- **Dependabot security updates are on**, so a pull request can also arrive outside the Monday group (owner decision, 2026-09-14).

## The problem

Every pull request a person opens is checked before it reaches GitHub.
The pre-push hook in `.githooks/pre-push` runs `make ci` on the laptop when the branch has an open pull request, and refuses the push if anything is red.

Dependabot has no laptop.
It pushes from GitHub's servers, where no hook of ours can run, and Actions does not run the checks on pull requests into `development`.
So a Dependabot pull request has never been checked by anything except `approval-gate`, which only asks whether a ticket was approved.

This is how `development` went red in September.
Dependabot pull request #225 bumped `actions/create-github-app-token` from v2.2.2 to v3.2.0.
A test asserted that action's exact commit id, so eleven tests failed the moment the bump merged, and every push on a branch with an open pull request was blocked until #237 fixed it.

Two separate repairs follow from that.
The 2026-09-29 decision "No test names an exact dependency version or commit id" removes the brittle assertion, and #237 did that.
This ticket does the other half: it makes a Dependabot pull request prove `make ci` is green before it can merge, so the next brittle thing is caught on the pull request instead of on `development`.

## The change

Three files, plus the documents that currently describe the old state.

### 1. The workflow: `.github/workflows/dependabot-ci.yml`

```yaml
name: dependabot-ci

# Runs make ci on a Dependabot pull request, and only on a Dependabot pull
# request. Owner decisions: 2026-09-29 (the workflow) and 2026-10-01 (it is
# a required check on development).
#
# Pull requests from people are not covered here on purpose. The pre-push
# hook in .githooks/pre-push already ran make ci on the developer's machine,
# and Actions minutes are metered (owner decision, 2026-09-16).
#
# The trigger is pull_request, never pull_request_target: this job runs the
# pull request's own code, so it must have the read-only token and no
# access to secrets. See "Why pull_request" in the design.

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

concurrency:
  group: dependabot-ci-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  dependabot-ci:
    # The gate, in two halves, both read from GitHub's own event data, which
    # a pull request cannot edit:
    #   1. Dependabot opened it. No GitHub account can be named
    #      "dependabot[bot]", because square brackets are not allowed in a
    #      username, so no lookalike account can pass this.
    #   2. The branch lives in this repository. Dependabot always pushes its
    #      branches here, never to a fork, so a fork pull request skips.
    # This must stay a job-level if:, never a workflow-level paths: filter.
    # A skipped job satisfies a required check; a skipped workflow never
    # reports and leaves the check pending forever.
    if: >-
      github.event.pull_request.user.login == 'dependabot[bot]' &&
      github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-24.04
    # make ci takes six to seven minutes on a laptop, and checks-tests alone
    # is about five of them, because it copies the repository and runs make
    # ci inside the copy. Twenty is a ceiling, not an expectation.
    timeout-minutes: 20
    steps:
      - name: Check out the pull request
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
          # All history, so the secret scan can walk the pull request's
          # commits. The repository is small.
          fetch-depth: 0

      - name: Install the pinned actionlint, ShellCheck and gitleaks
        run: python3 tools/checks/install_linters.py

      - name: Check this machine has the tools
        run: make doctor

      - name: Run every check
        run: make ci
        env:
          # The pull request's base commit, so the secret scan covers
          # exactly the commits in the pull request.
          SCAN_BASE: ${{ github.event.pull_request.base.sha }}
```

The three steps are the same three `tooling-tests.yml` already uses, which is deliberate: this workflow introduces no new machinery, only a different trigger and the gate.

**It runs `make ci`, not `make ci-docs` plus `make ci-tooling`.**
That is not a style preference. `tools/checks/test_coverage.py` counts, across every workflow file, how many run a given check group, and fails with "<group> is run twice" when a group is run by more than one workflow. Its pattern matches `make ci-<group>` only, so plain `make ci` adds nothing to that count. Splitting the run into the two group targets would make `docs` and `tooling` both counted twice and would turn `make ci` itself red.

Checked while designing rather than assumed: the proposed file above was fed to `test_coverage.coverage_problems` beside the four real workflows. With `run: make ci` it reports no problems; with the two group targets it reports `docs is run twice`.

### 2. Why `pull_request` and not `pull_request_target`

`approval-gate.yml` uses `pull_request_target`, and that is correct there for a reason that does not transfer.
`pull_request_target` runs the base branch's copy of the workflow, with a writable token and access to the repository's secrets, so a pull request cannot edit the check that judges it. The approval gate never checks out the pull request and never runs a line of its code; it only reads the GitHub API.

This job is the opposite shape. Its whole purpose is to run the pull request's own code: its tests, its workflow files, its dependency manifests.
Running that under `pull_request_target` would hand a writable token and the repository's secrets to code from a pull request, which is the best known way to lose a repository.

With `pull_request`, GitHub gives a Dependabot pull request a read-only `GITHUB_TOKEN` and no access to repository secrets at all.
`make ci` needs neither. `install_linters.py` downloads actionlint, ShellCheck and gitleaks unauthenticated and checks each against a pinned SHA-256 hash, and no check in `make ci` reads a secret.
The workflow also declares `permissions: contents: read` explicitly, so the token is read-only even if GitHub's defaults change.

### 3. What a fork can and cannot do

A fork pull request runs the fork's copy of the workflow file, because that is how `pull_request` works. So a fork can rewrite this file. Three things keep that harmless:

- The token is read-only and no repository secret is available, so there is nothing to steal and nothing to push.
- The second half of the gate, `head.repo.full_name == github.repository`, is false for every fork pull request, so our job skips itself even when the fork's own copy of the file is identical.
- A fork cannot make the first half true either. GitHub usernames cannot contain square brackets, so no account can be registered as `dependabot[bot]`, and `pull_request.user.login` is GitHub's record of who opened the pull request, not anything the branch contains.

What remains is that a fork pull request can spend runner minutes on whatever workflow its own copy defines. That is true of this repository today and is not changed by this ticket; GitHub's own "require approval for fork pull requests" setting is where that is controlled, and it is out of scope here.

### 4. The ruleset: `.github/rulesets/development.json`

One entry is added to the `required_status_checks` list, beside the existing `approval-gate`:

```json
{ "context": "dependabot-ci", "app": "github-actions" }
```

**Why this does not freeze pull requests from people.**
The fear is reasonable: the job is skipped on a human pull request, so does the required check sit pending forever and block every merge?
No, because of how GitHub distinguishes two kinds of "did not run":

| How the job did not run | What GitHub reports | Effect on a required check |
|---|---|---|
| A job-level `if:` was false | finished, result "skipped" | Counts as satisfied; the merge button works |
| The whole workflow was filtered out by `on.paths` or `on.branches` | nothing at all | Stays pending forever; the merge button is blocked |

This design is in the first row, which is why the gate is a job-level `if:` and why the workflow has no `paths:` filter.

**The repository already refuses the shapes that would land in the second row.**
`tools/rulesets/rulesets.py` validates every required check against the workflow files and reports a problem when the context is not a job name in any workflow, when that workflow does not run on pull requests, when the workflow has a `paths:` filter, or when its `types:` list has lost `synchronize` (which would stop the check re-running on new commits).
So renaming the job, adding a path filter, or trimming the triggers fails `make ci` on a laptop rather than quietly hanging pull requests on GitHub.

Checked while designing rather than assumed, by running `rulesets.validate` over the real ruleset files with `dependabot-ci` added and the proposed workflow in place:

| What was fed to `validate` | What it reported |
|---|---|
| The design as written | no problems |
| The job renamed to `ci` | `development required check dependabot-ci is not a workflow job on branch development` |
| A `paths:` filter added | `development required check dependabot-ci has a path filter and could be skipped` |
| `synchronize` removed from the triggers | `development required check dependabot-ci would not re-run on new commits (lost synchronize)` |
| The workflow file missing altogether | the same message as the rename |

That last row is what makes the order in the next section a check rather than a convention.

**`strict_required_status_checks_policy` is already `true`** on `development`, which means a branch must be up to date with `development` before it merges. That already applies to `approval-gate` today, so this adds no new rule, only one more check that must be green on an up-to-date branch. The repository setting `allow_update_branch` is already `true`, so the "Update branch" button is there, and pressing it re-runs the check on the refreshed branch.

### 5. The order the two halves land in, which matters

The ruleset file and the workflow file change in the same implementation pull request, so `make ci` validates them together.
The live GitHub ruleset is a separate thing, changed only by `make rulesets-apply`, which needs an admin login and is therefore the owner's step.

1. The implementation pull request merges into `development`. At that moment the live ruleset still requires only `approval-gate`, so nothing can hang.
2. The owner runs `make rulesets-apply RULESETS='development'` and then `make rulesets-check`.
3. From then on a red `dependabot-ci` blocks the merge button.

Between step 1 and step 2 the file and the live ruleset disagree, so `make rulesets-check` and the nightly `rulesets-drift` run report drift. That is expected, and it is the reminder that step 2 is outstanding. Applying the ruleset before the workflow exists on `development` would be the harmful order, because the required context would name a job GitHub has never seen, and every pull request would sit pending.

### 6. Tests

`tools/checks/test_dependabot_ci.py`, a new file. It needs no new entry in `tools/checks/checks.py`, because the existing `checks-tests` entry already discovers every test in `tools/checks/`.
It reads the workflow file as text, in the manner of `tools/board/test_workflow.py`, and asserts the triggers, both halves of the gate, the read-only permissions, the absence of a `paths:` filter, that the run line is `make ci` rather than a group target, and that every `uses:` line matches `@[0-9a-f]{40}`.
Per the 2026-09-29 decision it never names which commit id or which version.

Two cases are checked against the real ruleset file rather than the workflow: that `dependabot-ci` is required on `development`, and that `tools/rulesets/rulesets.py validate` returns no problems for the pair. The second is already covered generically by `test_real_files_pass` in `tools/rulesets/test_rulesets.py`, which will start covering the new check for free.

The full plan, including the failing partner for each gate assertion and the live walk-through, is in [../test/issue-245-dependabot-ci.md](../test/issue-245-dependabot-ci.md).

### 7. Documents that describe the old state

Each of these is wrong once this ships, and is corrected in the same implementation pull request:

| File | What it says now | What it must say |
|---|---|---|
| `docs/platform/development-process.md`, "Pull request kinds" exceptions | A Dependabot pull request passes the gate without a ticket | The same, plus: a Dependabot pull request also runs `dependabot-ci`, which is required, and a person's pull request shows that check as skipped |
| `docs/platform/development-process.md`, "How the rule is enforced" | Lists the approval gate, the rulesets and the label guard | Add the Dependabot CI check and what it covers |
| `docs/platform/security.md`, "Dependencies and scanning" | A Dependabot pull request is merged once every required check is green | The same, naming `make ci` as one of those checks now |
| `docs/platform/runbook.md`, "Dependency updates and code scanning" | "Only the owner merges a Dependabot pull request. Check `make ci` passed" | Stale on both counts since 2026-09-23 and 2026-09-29: an agent may merge, and nothing ran `make ci` until now. Replace with reading the `dependabot-ci` result, and what to do when it is red |
| `.github/dependabot.yml`, the file comment | "Only the owner merges Dependabot pull requests (owner decision, 2026-09-14)" | Superseded 2026-09-23. Point at the current rule |

The runbook already documents `make rulesets-apply RULESETS=development` followed by `make rulesets-check` with an admin login after files merge, so step 2 above needs no new runbook section, only the `dependabot-ci` context named in that section's list.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| Dependabot opens its Monday grouped pull request | The job runs `make ci`. Green means it is genuinely safe to merge, which is new |
| Dependabot opens a security update outside the group | Identical. The gate is about the author, not the reason |
| Dependabot pushes a new commit to an open pull request, for example after `@dependabot rebase` | `synchronize` re-runs the job. The old run is cancelled by the concurrency group |
| A person opens a pull request | The job is skipped. No runner starts, no minutes are spent, and the required check counts as satisfied |
| An agent opens a pull request with the owner's login | Same as a person. The gate asks who opened it, and that is not Dependabot |
| A fork opens a pull request | The job skips on the second half of the gate. The token is read-only and no secret is reachable |
| `make ci` fails on a Dependabot pull request | The check is red and the merge button is blocked. The runbook's existing advice applies: close the pull request, or comment `@dependabot ignore <dependency>` so the rest of the group can go in. Never merge it red |
| The failure is a brittle test rather than a real break, as in #225 | The pull request stays red until the test is fixed by its own ticket. That is the point: `development` stays green while it is sorted out |
| `development` moves while a Dependabot pull request is open | The up-to-date-branch rule already applied through `approval-gate`. Press "Update branch", or comment `@dependabot rebase`, and the check re-runs |
| `install_linters.py` cannot reach GitHub's release downloads | The step fails, the check is red, and nothing is merged. Rerunning the job is the repair; this is a network flake, not a finding |
| A linter download's hash does not match | The installer refuses it and the job fails. Pinned hashes are the point |
| The runner takes longer than twenty minutes | GitHub cancels the job and the check is red. A real `make ci` is six to seven minutes, so this means something hung |
| Actions minutes have run out | The job fails in seconds with no steps, which looks like a broken build but is a budget problem. That risk is why nothing else runs per pull request, and it is the one real cost of making this check required |
| The owner has not yet applied the ruleset | The check runs and reports, but a red one does not block. `rulesets-drift` reports the drift nightly until it is applied |
| Somebody renames the job | `make ci` fails on a laptop, because `rulesets.py` cannot find a job named `dependabot-ci`. It cannot reach GitHub |
| Somebody adds a `paths:` filter to this workflow | Same: `make ci` fails with "has a path filter and could be skipped" |
| Dependabot's bot login ever changes | Every Dependabot pull request would skip, silently losing the gate. The live walk-through in the test plan is what catches this, and it is the one failure mode here that no local test can see |

## What is deliberately not covered

- **Pull requests from people.** Covered by the pre-push hook (owner decision, 2026-09-16). Running them here would double the work and spend metered minutes on checks already done.
- **The 13 Dependabot security alerts under `legacy/`.** The owner decided on 2026-10-01 to stop them at the source rather than keep dismissing them, and that is its own ticket. Nothing in this ticket touches `legacy/`.
- **Auto-merge.** Still off. A person or an agent still presses the button (decisions.md, 2026-09-23).
- **CodeQL on pull requests.** Unchanged since 2026-09-16.
- **Making the check required on `main`.** A pull request into `main` can only come from `development`, which is already green.
- **Speeding `make ci` up**, by caching the linter downloads or splitting `checks-tests` across jobs. Worth doing if the minutes bite; it is not needed to close the gap, and a second job would mean a second required context.
- **The open questions from #228**: whether an agent may merge a major version bump, whether a security update merges the same way, and whether the changelog must be read first. Those are about who presses merge, not about what is checked.

## Open questions for the owner

None open.
The one question this design had, whether the check becomes required in the `development` ruleset, was answered on 2026-10-01 and is recorded in [decisions.md](../../platform/decisions.md) as "The Dependabot CI check is required on `development`".
