# PolluxKart: instructions for agents and contributors

PolluxKart is an electronics online store for a family business in India, being rebuilt from scratch.
The first version is in `legacy/` as reference only.
Start every piece of work by reading `docs/README.md`.

## Rule one: nothing is implemented without the owner's approval

**Owner rule, 2026-09-13.
It overrides every other instruction in this repository.**

- The owner (GitHub `CosmicSaaurabh`) makes every product and design decision.
- Every piece of work is a GitHub ticket, grouped under an epic, linked to its design documents.
- **Only tickets the owner labelled `stage: implementation-ready` may be implemented.**
If a ticket is not at that stage (or in-progress or in-review after it), do planning work only, or ask.
- **Agents never apply, create, rename or delete the `stage: implementation-ready` label**, even when running with the owner's login.
The owner applies it by hand.
`.claude/settings.json` blocks such commands.
- **Never assume or invent a product or design decision.**
If the answer is not an "Owner decision" entry in `docs/platform/decisions.md`, ask the owner and record the dated answer.
- One ticket owns five parts: feature planning, test planning, feature implementation, test implementation, verified test run.
- Feature implementation and its tests ship in **one** pull request that says `Implements #N` and `Closes #N`.
Planning and documentation pull requests say `Plans #N` and change only Markdown.
- Full rules: `docs/platform/development-process.md`.
Agent workflow: the `polluxkart-workflow` skill.

## Stages

`stage: planning` -> `stage: awaiting-approval` -> `stage: implementation-ready` (owner only) -> `stage: in-progress` -> `stage: in-review` -> `stage: done`.

The [PolluxKart project board](https://github.com/orgs/Softogram/projects/2) has one column per stage.
Cards follow those labels.

## Stack (owner decisions and proposals are marked in docs/platform/decisions.md)

- Backend: Java with Spring Boot, independent services in one codebase (`api/`, planned).
- Frontend: Next.js with TypeScript (`web/`, planned).
- Hosting: AWS, Mumbai region.
- The store's colours, fonts and theme are fixed and must not change.

## Git

- `development` is the default branch and the base of every pull request; `main` is the release branch.
- Pull requests into `development` squash.
Releases are merge commits of `development` into `main`.
Only this repository's `development` branch may open a pull request into `main`.
- One git worktree per task, created from a freshly fetched `origin/development`, removed after merge.
- Enable the committed hooks once per clone: `git config core.hooksPath .githooks`.
The pre-commit hook checks staged docs.
The pre-push hook refuses a direct push to `development` or `main`, and runs `make ci` when the branch has an open pull request.
- `SKIP_LOCAL_CI=1 git push` skips `make ci` in an emergency; say so in the pull request.
It never allows a direct push to `development` or `main`.
- Stage explicit paths only.
Never `git add -A`, `git add .`, `git commit -a`, `git stash`, `git reset --hard`, `git clean`, `git rebase`, or a force push.
- Read `git status --short` and `git diff --cached --stat` before every commit.
- No agent co-author lines in commit messages.
No em dashes in any written text.
- Dependabot pull requests pass the approval gate without a ticket.
An agent may merge one once every required check is green (owner decision, 2026-09-23); a major version bump still goes to the owner.

## Commands

- `make doctor`: check this machine has the tools the checks need.
Run once per machine, and after installing a tool.
- `make ci`: every check a pull request must pass.
Run before every pull request.
- `make help`: every other target, with what it does.
It is generated from the Makefile, so it cannot go stale.
- `git config core.hooksPath .githooks`: enable the committed hooks.
Run once per clone.

Only commands that exist today are listed here (owner decision, 2026-09-14).
A ticket that adds an everyday command adds its line here in the same pull request, and every target needs a `##` help comment.

## Writing

- Explain every technical term the first time it appears; short sentences; one sentence per line in long Markdown.
- The repository is public: account ids, live resource ids and credential status never go into it.
- Docs rules are checked by `python3 tools/docslint/docslint.py`.

## Checks before a pull request

These are the gate.
GitHub Actions does not re-run them on pull requests into `development` (owner decision, 2026-09-16).
It runs them at release (push to `main`) and when someone starts the workflow by hand.

- `make doctor` once per machine, to check the tools the checks need
- `make ci` before every pull request

## Skills

`.claude/skills/README.md` indexes every skill.
`polluxkart-*` skills win over vendored ones, and `polluxkart-workflow` wins over all of them on process.
