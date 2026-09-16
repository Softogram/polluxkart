# E00-06 Branch rulesets on `development` and `main`

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #36 (E00-06), part of epic #10.
Test plan: [../test/issue-36-branch-rulesets.md](../test/issue-36-branch-rulesets.md)
Depends on: #34 (`make ci`), because this ticket adds a check and two targets to it.

## Words used below

- **Ruleset:** a named set of branch rules that GitHub itself enforces, such as "changes arrive only through pull requests". Unlike a local git hook, nobody can skip it from their own machine.
- **Required check:** a check, such as `docslint`, that must pass before GitHub allows a pull request to merge. GitHub matches it by its exact name.
- **Bypass:** permission for a named account to ignore the rules of one ruleset.
- **Direct push:** sending commits straight to a branch with `git push`, without a pull request.
- **Force push:** a push that replaces a branch's history instead of adding to it, which can erase other people's work.
- **Squash merge:** a pull request lands as one new commit.
- **Merge commit:** a pull request lands with its commits kept, joined by a commit that records both branches as its parents, so git knows the two branches are connected.
- **Up to date:** a pull request branch that already contains every change merged into its target since it was created.
- **Release pull request:** a pull request from `development` into `main`. Merging it is a release; from E06 on, it deploys to production.
- **Drift:** the live settings on GitHub no longer match what the repository says they should be.
- **Admin login:** a GitHub login with the admin role on this repository, which is the only kind allowed to change rulesets.
- **`pull_request_target`:** the GitHub event the approval gate uses. It runs the workflow as it exists on the pull request's target branch, not as the pull request changed it.

## What was already decided before this document

- **`development` is the default branch and `main` the release branch; one worktree per task; no history rewrites** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Git workflow").
- **Nothing is implemented without the owner's approval, enforced by an automated gate plus the written rule** (owner decision, 2026-09-13, "Nothing is implemented without the owner's approval").
- **The `docs` and `tooling-tests` workflows keep their names** and each runs its part of `make ci` at release, not on every pull request (owner decisions, 2026-09-14, "`make ci` and `make doctor`", and 2026-09-16, "Local `make ci` is the pull-request gate").
- **The branch rules themselves** (owner decision, 2026-09-14, "Branch rules for `development` and `main`", answered while planning this ticket):
  - contributors may merge into `development`; only the owner may merge into `main`;
  - no required human review; the approval-gate check must pass;
  - no bypass for anyone;
  - squash merges into `development`, merge commits into `main`, rebase merging off;
  - a pull request must be up to date with its target before merging, on both branches;
  - only `development` may open pull requests into `main`;
  - a release pull request from this repository's `development` into `main` passes the approval gate without a ticket line;
  - the rules are saved as files in the repository, applied by a script, and checked for drift;
  - agents may merge a release into `main` when the owner asks them to in the session.
- **The merge method for releases revises the 2026-09-13 "Git workflow" entry**, which said pull requests are squash-merged (revised 2026-09-14 in [decisions.md](../../platform/decisions.md)).

## The problem

Today neither branch is protected.
Anyone with write access can push straight to `development` or `main`, force push over their history, or delete them.
The approval gate reports a failure, but nothing stops a pull request with a failing gate from merging.
So the Phase 0 exit condition, "a failing pull request cannot merge" ([road-to-launch.md](../high-level/road-to-launch.md)), is not yet true.

Two further gaps appeared while planning:

1. **A release pull request would always fail the approval gate**, because it has no `Plans #N` or `Implements #N` line.
2. **`main` still holds the first version's code and workflows, without the approval gate.** Because the gate runs from the target branch (`pull_request_target`), it cannot run on a pull request into `main` until `main` contains it. If `main` required the gate today, no release could ever merge.

Nothing deploys from `main` today (checked 2026-09-14: no webhooks, no deployments, no GitHub Pages; the old server is stopped), so the first release only changes what the branch holds.

## The change

### The three rulesets

GitHub applies every ruleset whose target matches a branch, and a bypass on one ruleset does not lift the rules of another.
That is how "only the owner merges into `main`" and "no bypass for anyone" both hold: the owner's exception covers only the rule restricting who may update `main`, while the checks stay on in a separate ruleset with no bypass.

| Ruleset name | Branch | Rules | Bypass |
|---|---|---|---|
| `development` | `development` | Pull request required, 0 approvals, squash merge only; required check `approval-gate` from GitHub Actions only, branch must be up to date; no force push; no deletion | None |
| `main` | `main` | Pull request required, 0 approvals, merge commit only; required check `approval-gate` from GitHub Actions only, branch must be up to date; no force push; no deletion | None |
| `main-owner-merge` | `main` | Restrict updates: only accounts with bypass may change `main` | The owner's account, for pull requests only (never a direct push) |

Notes on the rule settings:

- **"From GitHub Actions only"** ties each required check to the GitHub Actions app, so a status with the same name reported by anything else cannot satisfy it.
- **Every review option is off:** no approvals, no code owner review, no dismissing stale reviews, no conversation resolution. This matches "no required human review". CODEOWNERS still requests the owner's review automatically; it just does not block.
- **Linear history is not required**, because merge commits into `main` are not linear.
- **"Restrict updates" also blocks merging**, since a merge updates the branch. A contributor can open a release pull request but cannot merge it.
- The owner's exception uses the "pull requests only" mode, so even the owner's account cannot push straight to `main`; the `main` ruleset refuses that too.

### Repository merge settings

| Setting | Today | After |
|---|---|---|
| Allow squash merging | on | on |
| Allow merge commits | on | on |
| Allow rebase merging | on | **off** |
| Always suggest updating pull request branches ("Update branch" button) | off | **on** |

The commit title and message settings, and automatic branch deletion after merge, are not changed.
Which merge method applies to which branch is enforced by the rulesets, not by these settings.

### The rules as files (`.github/rulesets/`)

```
.github/rulesets/development.json         the development ruleset
.github/rulesets/main.json                the main ruleset
.github/rulesets/main-owner-merge.json    the owner-only update rule for main
.github/rulesets/repository.json          the four merge settings above
```

The files follow GitHub's ruleset format with one difference: **accounts and apps are written by name, never by number.**
The owner appears as the GitHub login `CosmicSaaurabh` and the checks' source as the app `github-actions`.
The script looks up the numbers when it talks to GitHub, so no account number is ever written into this public repository.

A shortened example, `development.json`:

```json
{
  "name": "development",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/development"], "exclude": [] } },
  "bypass": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "require_code_owner_review": false,
        "dismiss_stale_reviews_on_push": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false,
        "allowed_merge_methods": ["squash"] } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          { "context": "approval-gate", "app": "github-actions" } ] } }
  ]
}
```

`main-owner-merge.json` carries `"bypass": [{ "user": "CosmicSaaurabh", "mode": "pull_request" }]` and a single `{ "type": "update", "parameters": { "update_allows_fetch_and_merge": false } }` rule.

### The script (`tools/rulesets/rulesets.py`)

Standard library Python.
It talks to GitHub through `gh api`, so it uses whoever is logged in to the GitHub CLI (`gh`), and `make doctor` already checks `gh` is installed.

| Command | Make target | Who runs it | What it does |
|---|---|---|---|
| `validate` | part of `make ci`, through the `rulesets-tests` check | everyone, offline | Checks the files make sense on their own; details below |
| `apply` | `make rulesets-apply` | the owner, or an agent at the owner's request, with an admin login | Creates each ruleset that is missing and updates each existing one by name, then sets the four merge settings. `--dry-run` prints the changes without making them. It never deletes a ruleset; any ruleset on GitHub that is not in the files is listed as a warning |
| `check` | `make rulesets-check` | the daily drift workflow, and the owner after any change | Compares GitHub's live rulesets and settings with the files. Exit 0 when they match; exit 1 listing every difference |

**What `validate` checks:**

1. Each file is valid JSON of the expected shape, and ruleset names are unique.
2. Every required check name is the name of a job in a workflow that runs for pull requests into that branch, with no path filter that could stop it running.
   This catches a renamed job, which would otherwise leave its required check waiting forever and block every merge.
   `docslint` and `tooling-tests` must not appear as required checks, because those workflows do not run on pull requests (owner decision, 2026-09-16).
3. Only `main-owner-merge` has a bypass, the bypass is in "pull requests only" mode, and its only rule is "restrict updates".
4. `development` allows only squash merges and `main` only merge commits, both require up-to-date branches, and neither requires approvals. These are the owner's 2026-09-14 answers, so changing them fails the build until the decision log is changed too.

**What GitHub hides from a login without admin rights.**
GitHub only shows who may bypass a ruleset to a login that can edit it, and may hide some merge settings too.
`check` reports any field it cannot see as "not visible with this login", not as drift, and says to run it with an admin login for the full comparison.
The daily workflow, which runs without admin rights, therefore checks everything except the bypass list and any hidden settings.
The owner's `make rulesets-check` checks all of it.

**Names in the code:** `load_files(folder)`, `validate(files, workflows)`, `resolve_names(files, gh)` (login and app names to numbers), `live_state(gh)`, `diff(expected, live)` returning a list of `Difference`, `apply(files, gh, dry_run)`, and `main(argv)`.
`gh` is passed in as a small object, so tests replace it and never call GitHub.

### The daily drift check (`.github/workflows/rulesets-drift.yml`)

- Runs once a day and on demand (`workflow_dispatch`), with read-only permissions.
- Runs `python3 tools/rulesets/rulesets.py check` with the workflow's own token.
- A failure turns the run red; GitHub emails the account that last edited the schedule line of a scheduled workflow.
- GitHub pauses scheduled workflows in a public repository after 60 days without any activity in it; the runbook notes this.

It does not run on pull requests, because a pull request that changes the rule files is expected to differ from GitHub until the owner applies it after merging.

### The approval gate learns about `main` (`tools/approval_gate/gate.py`)

A new first step in `evaluate`, before every other rule, including the Dependabot exemption:

- **The pull request targets `main`:**
  - it passes only if its branch is `development` **and** that branch belongs to this repository, and the message says "Release pull request from development into main";
  - otherwise it fails with "Pull requests into main must come from this repository's development branch". This covers a feature branch, a Dependabot branch, and a fork's branch that happens to be named `development`.
  - Ticket lines in a release pull request are ignored, because every change inside it already passed the gate on its way into `development`.
- **The pull request targets any other branch:** the existing rules apply unchanged.

`evaluate` gains three inputs: `base_ref`, `head_ref` and `head_repository`, plus `repository`.
`main()` reads them from the pull request (`base.ref`, `head.ref`, `head.repo.full_name`); a missing head repository, which happens when a fork is deleted, counts as "not this repository".

### Tooling wiring (on top of #34)

- `CHECKS` gains `rulesets-tests` in the `tooling` group: `python3 -m unittest discover -s tools/rulesets`. It includes running `validate` on the real files.
- The Makefile gains `rulesets-check` and `rulesets-apply`.
  These are not check groups, so the coverage test from #34 ignores them.

### The rollout, in order

The order matters because the gate cannot run on pull requests into `main` until `main` contains it.

1. **Rehearse on throwaway branches.** From the implementation branch, apply copies of the `development` and `main` rules to two throwaway branches, and run the live checks from the test plan there. This proves GitHub enforces the rules as written, without risking the real branches. Then delete the rehearsal rulesets and branches.
2. **Merge the implementation pull request into `development`.** No rules are active yet, so nothing blocks it.
3. **Apply the `development` ruleset and the merge settings** with `make rulesets-apply`. Confirm with `make rulesets-check`.
4. **Open the first release pull request, `development` into `main`.** The owner, or an agent the owner asks, merges it with a merge commit. `main` now contains the approval gate and the current workflows.
5. **Apply the `main` and `main-owner-merge` rulesets.** Confirm with `make rulesets-check` using the owner's login, which also shows the bypass list.
6. **Run the read-only checks on the real branches** from the test plan, and record the results as a comment on #36. The ticket moves to `stage: done` only after that comment.

Until step 5, `main` stays unprotected, as it is today.

### Documents updated in the implementation pull request

- `docs/platform/development-process.md`: "How the rule is enforced" describes the three rulesets in plain words; the pull request rules gain the release pull request and the "only `development` into `main`" rule.
- `docs/platform/runbook.md`: how to change a rule (pull request, merge, `make rulesets-apply`, `make rulesets-check`), what a red drift run means, how to switch a ruleset off in a genuine emergency and back on, and the 60-day pause.
- `tools/approval_gate/README.md` and the gate's docstring: the release rule.
- `tools/rulesets/README.md`: new.
- `CLAUDE.md`, "Git": merge methods per branch, and that releases come only from `development`.
- The `polluxkart-workflow` skill: what the gate rejects gains "a pull request into main that does not come from development".

None of these name account numbers, ruleset numbers or who holds which role; the owner's GitHub login already appears in CODEOWNERS.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A workflow job is renamed | `validate` fails in `make ci`, before the rename can merge and block every later pull request |
| A required workflow gains a path filter | `validate` fails, because a skipped required check waits forever |
| The owner approves a ticket after its implementation pull request opened | The gate's earlier failure blocks merging until the gate re-runs; re-run the check or edit the description, as today |
| Two pull requests both pass, then one merges | The other shows "out of date"; "Update branch" merges `development` in, checks re-run, then it can merge |
| A contributor tries to merge into `main` | GitHub refuses: restricted updates |
| Anyone, the owner included, tries to push straight to `development` or `main` | GitHub refuses: pull request required |
| Someone force pushes or deletes either branch | GitHub refuses |
| A merge commit is chosen for a pull request into `development`, or squash for `main` | GitHub refuses that method; the allowed one remains |
| A pull request into `main` from a feature branch or a fork | The gate fails; merging is refused |
| A Dependabot pull request aimed at `main` | The gate fails, because the `main` rule runs before the Dependabot exemption |
| Someone edits a ruleset in GitHub settings | The next daily drift run fails and lists the difference, except a bypass list change, which only the owner's `make rulesets-check` sees |
| Rule files change in a merged pull request | The drift run is red until the owner runs `make rulesets-apply`; that is the reminder |
| `make rulesets-apply` with a login that is not admin | GitHub refuses; the script exits 1 saying an admin login is needed, and changes nothing more |
| `gh` not logged in, or GitHub unreachable | `check` and `apply` exit 1 with the error; they never report "no drift" when they could not look |
| A login or app name in the files does not exist | The script stops before changing anything, naming it |
| A ruleset exists on GitHub that is not in the files | `apply` leaves it alone and warns; `check` reports it as drift |
| A genuine emergency needs a merge past a failing check | The owner switches the ruleset's enforcement off in GitHub settings, merges, and switches it on again. The drift run shows the gap if it is forgotten |
| A second person is ever given the admin role | They can change rulesets but are not in the `main` bypass list, so they still cannot merge into `main`. The drift check shows any change they make |
| An agent under the owner's login merges a release | GitHub treats it as the owner, which the owner allowed on 2026-09-14 |

## What is deliberately not covered

- **Proving on the live `main` that a second person cannot merge into it:** no second account with write access exists today. The rule is proved on the rehearsal branch for the bypass mechanism, and by reading the live rules back; the first contributor given write access confirms it for real.
- **Making CodeQL a required check:** ticket #38.
- **Checks added later**, such as the backend and frontend CI from E05-05: each of those tickets adds its check to the rule files.
- **Production deploy approvals:** E06-06.
- **Giving contributors write access:** the owner does that when someone joins; it is an account action, not code.
- **Automatic deletion of merged branches, and commit message settings:** not asked about, so unchanged.
- **Applying rule changes automatically from GitHub Actions:** that would need an admin token stored as a secret, a far more dangerous thing to keep in a public repository than one manual command.

## Open questions for the owner

None open.
All nine questions this ticket raised, including the epic's question about who may merge, were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Branch rules for `development` and `main`".
Which GitHub checks are required was revised on 2026-09-16 ("Local `make ci` is the pull-request gate"): only `approval-gate`.
