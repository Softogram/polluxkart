# E00-05 Git hooks that block direct pushes and run `make ci` before pushing

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #35 (E00-05), part of epic #10.
Test plan: [../test/issue-35-git-hooks.md](../test/issue-35-git-hooks.md)
Depends on: #34 (`make ci` and `make doctor`), which these hooks run and extend.

## Words used below

- **Git hook:** a small script git runs automatically at a certain moment, such as just before a commit or a push. If the script fails, git stops that commit or push.
- **Pre-commit hook:** runs on every `git commit`, before the commit is made.
- **Pre-push hook:** runs on every `git push`, after git has worked out what it will send but before sending it.
- **`core.hooksPath`:** a git setting naming the folder git takes hooks from. Git ignores hooks committed to a repository until each clone sets it once.
- **Staged files:** the changes chosen with `git add` for the next commit. They can differ from the files on disk.
- **Failing open:** when a check cannot run, letting the action go ahead with a warning. Failing closed would stop it instead.
- **Escape hatch:** a deliberate way to skip a check in an emergency, here `SKIP_LOCAL_CI=1 git push`.
- **Remote ref:** the branch name on GitHub a push is updating, such as `refs/heads/development`.
- **`gh`:** the GitHub command-line tool, used here to ask GitHub whether a branch has an open pull request.

## What was already decided before this document

- **`development` and `main` change only through pull requests** (owner decision, 2026-09-14, [decisions.md](../../platform/decisions.md), "Branch rules for `development` and `main`"). GitHub enforces that with the rulesets in #36; these hooks only give the same answer earlier, on the contributor's own machine.
- **`make ci` runs every check, lists all failures, and exits non-zero if any failed; `make doctor` fails only on tools needed today and lists everything first** (owner decision, 2026-09-14, "`make ci` and `make doctor`").
- **How the hooks behave** (owner decision, 2026-09-14, "Git hooks", answered while planning this ticket):
  - the pre-push hook runs `make ci` only when the branch being pushed has an open pull request;
  - if `gh` is missing or GitHub cannot be reached, the push goes ahead with a warning;
  - `SKIP_LOCAL_CI=1 git push` skips `make ci`, and the hook asks for that to be noted in the pull request;
  - `make doctor` fails on a laptop where the hooks are not enabled, but only shows it as information on GitHub's machines;
  - the pre-commit hook runs the docs checker;
  - when the branch has an open pull request, the push is refused if the folder has uncommitted or untracked files, so the checks always test exactly what is pushed.

## The problem

`make ci` only helps if people run it. The first failure used to be found minutes later on GitHub; GitHub no longer re-runs those checks on every pull request (owner decision, 2026-09-16).
A direct push to `development` or `main` is refused by GitHub once #36 is live, but only after the push is attempted, with a less helpful message.
And `make ci` checks the files on disk, while a push sends commits: if the two differ, the local result means nothing.

## The change

### Files

```
.githooks/pre-commit                 new: two-line shell wrapper that runs tools/githooks/pre_commit.py
.githooks/pre-push                   new: two-line shell wrapper that runs tools/githooks/pre_push.py
tools/githooks/pre_commit.py         new: the pre-commit logic
tools/githooks/pre_push.py           new: the pre-push logic
tools/githooks/README.md             new: what each hook does, the setup command, the escape hatch
tools/githooks/test_pre_commit.py    new
tools/githooks/test_pre_push.py      new
tools/checks/checks.py               changed: adds the githooks-tests check to the tooling group
tools/checks/doctor.py               changed: adds the "git hooks enabled" row
```

Both hook files are committed as executable, and each only does this:

```sh
#!/bin/sh
# Runs tools/githooks/pre_push.py. See tools/githooks/README.md.
exec python3 "$(git rev-parse --show-toplevel)/tools/githooks/pre_push.py" "$@"
```

The logic is in Python so it can be tested like the rest of the repository's tooling, using only the standard library.

**Worktrees.**
`core.hooksPath` is set once per clone and shared by all its worktrees.
Because it is the relative path `.githooks`, git looks for the hooks inside whichever worktree the command runs in.
So each worktree uses its own copy of the hooks and runs `make ci` on its own files.

### Setting the hooks up

One command, once per clone, written in `CLAUDE.md` and `tools/githooks/README.md`:

```
git config core.hooksPath .githooks
```

`make doctor` gains a row:

| Status | When |
|---|---|
| `ok` | `core.hooksPath` is `.githooks` |
| `not enabled` | the setting is missing; a needed-now problem, and doctor prints the command above |
| `points elsewhere` | the setting names another folder; a needed-now problem, naming the folder found |
| information only | on GitHub's machines (the `GITHUB_ACTIONS` variable is `true`), where hooks never run, so the tooling workflow's `make doctor` step still passes |

`make doctor` never changes the setting itself.

### The pre-commit hook (`tools/githooks/pre_commit.py`)

1. Copy the **staged** version of every tracked file into a new temporary folder, using `git checkout-index`.
   This takes well under a second for this repository.
2. Run `python3 tools/docslint/docslint.py --root <temporary folder>`, with its output shown.
3. Delete the temporary folder, whether the check passed or failed.
4. Exit with docslint's exit code: 0 lets the commit happen, anything else stops it.

Checking the staged copy means an unfinished edit on disk that is not being committed cannot block the commit, and a fix on disk that was never staged cannot hide a problem in the commit.

`SKIP_LOCAL_CI` does not affect this hook.
Ticket #37 adds the secret scan here, and an escape hatch meant for slow checks must never switch off the secret scan.

### The pre-push hook (`tools/githooks/pre_push.py`)

Git gives the hook one line per branch or tag being pushed: the local ref, the local commit, the remote ref and the remote commit.
The hook handles the whole push in this order:

1. **Refuse any push that updates or deletes `development` or `main`.**
   The message: "Pushing straight to development is not allowed. Open a pull request instead (docs/platform/development-process.md)."
   Git then sends nothing, not even the other branches in the same push.
   `SKIP_LOCAL_CI` does not change this.
2. **Ignore tags and deleted branches**, which need no checks.
3. **For each remaining branch, ask GitHub whether it has an open pull request:** `gh pr list --head <branch> --state open --json number`, allowing at most 15 seconds.
   - `gh` not installed, not logged in, an error, or no answer within 15 seconds: print "Could not check for an open pull request (reason). Pushing without running make ci; run the local checks yourself. The approval-gate still runs on the pull request." and let the push go ahead.
   - No open pull request: let the push go ahead without running `make ci`, printing one line saying so.
4. **If any branch in the push has an open pull request:**
   1. If `SKIP_LOCAL_CI` is exactly `1`: print "SKIP_LOCAL_CI=1: make ci was not run. Say so in pull request #12." and let the push go ahead.
   2. If the folder has uncommitted changes or untracked files (anything `git status --porcelain` lists; files git ignores do not count): refuse, listing up to 20 of them, with "Commit or remove these, then push again, so make ci checks exactly what you push."
   3. If the commit being pushed is not the commit checked out in this folder (for example `git push origin other-branch` from a different branch): refuse, with "Push this branch from its own worktree, so make ci checks the commit being pushed."
   4. Run `make ci` in the worktree, with its output shown.
      If it fails, refuse: "make ci failed, so the push was stopped. Fix the failures, or in a real emergency push with SKIP_LOCAL_CI=1 and say so in the pull request."

**Exit codes:** 0 lets git push; 1 stops it.

**Names in the code:** `parse_push_lines(stdin)` returning `PushedRef` records, `protected_refs(refs)`, `open_pull_request(branch, run=subprocess.run, which=shutil.which)` returning a pull request number, `None` for none, or an `Unknown` with the reason, `uncommitted_files(run)`, `main(argv, stdin, env)`.
Programs are started through replaceable arguments, so unit tests never call GitHub or run `make`.

### Tooling wiring

- `CHECKS` gains `githooks-tests` in the `tooling` group: `python3 -m unittest discover -s tools/githooks`, needing `git` and `make`.
- No new Make target and no new workflow; the #34 coverage test is unaffected.

### Documents updated in the implementation pull request

- `CLAUDE.md`, "Git": the setup command, what the hooks do, and that `SKIP_LOCAL_CI=1` is for emergencies and noted in the pull request.
- `docs/platform/development-process.md`, "For contributors: picking up a ticket": the setup command as part of the first step.
- The `polluxkart-testing` skill, "Running the checks": the hook's behaviour as built.
- `tools/githooks/README.md`: new.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A push includes `development` or `main` together with a feature branch | The whole push is refused; nothing is sent |
| `git push origin :development` (deleting it) | Refused |
| `SKIP_LOCAL_CI=1` on a push to `development` | Still refused; the hatch only skips `make ci` |
| `SKIP_LOCAL_CI` set to anything other than `1`, such as `true` | Not treated as the hatch; the normal path runs |
| First push of a new branch | No pull request can exist yet, so no checks |
| A tag push | Allowed without checks |
| Python not installed | The hook cannot start, so git stops the push with `python3: not found`; `make doctor` already reports Python missing |
| `make ci` itself missing (a branch cut before #34 merged) | `make` reports no rule `ci`, the check fails, the push is refused; merging `development` into the branch fixes it |
| A pull request from a fork uses the same branch name | `gh` may report it, and `make ci` runs unnecessarily; it never lets a failing push through |
| The same branch pushed from two worktrees | Each runs its own hooks on its own files |
| Files ignored by git, such as `__pycache__` | Do not count as uncommitted |
| A long `make ci` (later, with end-to-end tests) | The push waits; that is the point once a pull request is open |
| Someone runs `git push --no-verify` | Git skips every hook; nothing here can stop that. GitHub's rulesets (#36) and checks still apply |
| Hooks not enabled in a clone | Nothing runs locally; `make doctor` reports it until the command is run |

## What is deliberately not covered

- **Server-side protection of the branches:** #36.
- **The secret scan in the pre-commit hook:** #37.
- **Blocking `git push --no-verify` or `git commit --no-verify`:** git offers no way for a hook to prevent its own skipping. The protection that cannot be skipped is on GitHub.
- **Recording automatically that `SKIP_LOCAL_CI` was used:** a local hook cannot write to the pull request without a token; it prints the reminder instead.
- **Native Windows:** the wrapper scripts assume a Unix-like shell, as in #34.

## Open questions for the owner

None open.
All six questions this ticket raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Git hooks".
