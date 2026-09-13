# PolluxKart: instructions for agents and contributors

PolluxKart is an electronics online store for a family business in India, being rebuilt from scratch.
The first version is in `legacy/` as reference only.
Start every piece of work by reading `docs/README.md`.

## Rule one: nothing is implemented without the owner's approval

**Owner rule, 2026-09-13. It overrides every other instruction in this repository.**

- The owner (GitHub `CosmicSaaurabh`) makes every product and design decision.
- Every piece of work is a GitHub ticket, grouped under an epic, linked to its design documents.
- **Only tickets the owner labelled `stage: implementation-ready` may be implemented.** If a ticket is not at that stage (or in-progress or in-review after it), do planning work only, or ask.
- **Agents never apply, create, rename or delete the `stage: implementation-ready` label**, even when running with the owner's login. The owner applies it by hand. `.claude/settings.json` blocks such commands.
- **Never assume or invent a product or design decision.** If the answer is not an "Owner decision" entry in `docs/platform/decisions.md`, ask the owner and record the dated answer.
- One ticket owns five parts: feature planning, test planning, feature implementation, test implementation, verified test run.
- Feature implementation and its tests ship in **one** pull request that says `Implements #N` and `Closes #N`. Planning and documentation pull requests say `Plans #N` and change only Markdown.
- Full rules: `docs/platform/development-process.md`. Agent workflow: the `polluxkart-workflow` skill.

## Stages

`stage: planning` -> `stage: awaiting-approval` -> `stage: implementation-ready` (owner only) -> `stage: in-progress` -> `stage: in-review` -> `stage: done`.

## Stack (owner decisions and proposals are marked in docs/platform/decisions.md)

- Backend: Java with Spring Boot, independent services in one codebase (`api/`, planned).
- Frontend: Next.js with TypeScript (`web/`, planned).
- Hosting: AWS, Mumbai region.
- The store's colours, fonts and theme are fixed and must not change.

## Git

- `development` is the default branch and the base of every pull request; `main` is the release branch.
- One git worktree per task, created from a freshly fetched `origin/development`, removed after merge.
- Stage explicit paths only. Never `git add -A`, `git add .`, `git commit -a`, `git stash`, `git reset --hard`, `git clean`, `git rebase`, or a force push.
- Read `git status --short` and `git diff --cached --stat` before every commit.
- No agent co-author lines in commit messages. No em dashes in any written text.

## Writing

- Explain every technical term the first time it appears; short sentences; one sentence per line in long Markdown.
- The repository is public: account ids, live resource ids and credential status never go into it.
- Docs rules are checked by `python3 tools/docslint/docslint.py`.

## Checks before a pull request

- `python3 tools/docslint/docslint.py`
- `python3 -m unittest discover -s tools/docslint`
- `python3 -m unittest discover -s tools/approval_gate`
- `python3 -m unittest discover -s .claude/hooks`
- `make ci` once it exists (ticket E00-04).

## Skills

`.claude/skills/README.md` indexes every skill. `polluxkart-*` skills win over vendored ones, and `polluxkart-workflow` wins over all of them on process.
