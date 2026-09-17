# Low-level designs

Parent: [design/](../README.md) | Index: [docs/](../../README.md)

One document per GitHub ticket, written **before** the ticket is built, and concrete enough to implement from: real class and method names, real file paths, real SQL, and the edge cases already found while designing.

This is part 1 of a ticket's five parts ([development-process.md](../../platform/development-process.md)).
It arrives in a planning pull request that says `Plans #N`, and the ticket moves to `stage: awaiting-approval` when it is ready for the owner.

Naming: `issue-<N>-<short-slug>.md`.
Several issues that ship together share one document, named after all of them.

**A design is not final until the owner has explicitly approved it.**
A document existing here does not mean it is ready to build; check its status line and the ticket's stage label.
Only a ticket labelled `stage: implementation-ready` by the owner may be implemented.

## What every design contains

- **Status line**, dated: `**Status: DRAFT (YYYY-MM-DD)**`, then `**Status: APPROVED by the owner YYYY-MM-DD**` once the owner approves it.
- **The ticket it belongs to:** `Ticket: #N`.
- **What was already decided before this document**, with dates, linking each owner decision in [decisions.md](../../platform/decisions.md), so settled questions are not re-opened.
- **Open questions for the owner**, written as questions with every term explained. A design with an unanswered question cannot move to awaiting approval.
- **The change**, by service: interface methods and records, tables and migrations, endpoints, events, frontend routes.
- **Edge cases and failure behaviour** for every dependency the change touches.
- **What is deliberately not covered**, and why.
- **A link to the matching test plan** in `../test/`.

## Read next

- [issue-32-project-board.md](issue-32-project-board.md) - E00-02, the project board with a column per stage (DRAFT, 2026-09-14)
- [issue-33-board-label-sync.md](issue-33-board-label-sync.md) - E00-03, keeping the board in sync with stage labels (DRAFT, 2026-09-14)
- [issue-34-makefile-ci-doctor.md](issue-34-makefile-ci-doctor.md) - E00-04, `make ci` and `make doctor` (DRAFT, 2026-09-14)
- [issue-35-git-hooks.md](issue-35-git-hooks.md) - E00-05, git hooks that block direct pushes and run `make ci` (DRAFT, 2026-09-14)
- [issue-36-branch-rulesets.md](issue-36-branch-rulesets.md) - E00-06, branch rulesets on `development` and `main` (DRAFT, 2026-09-14)
- [issue-37-secret-scanning.md](issue-37-secret-scanning.md) - E00-07, secret scanning in pre-commit, CI and GitHub push protection (DRAFT, 2026-09-14)
- [issue-38-dependabot-codeql.md](issue-38-dependabot-codeql.md) - E00-08, Dependabot updates and CodeQL code scanning (DRAFT, 2026-09-14)
- [issue-39-claude-md-commands.md](issue-39-claude-md-commands.md) - E00-09, everyday commands in CLAUDE.md and a generated make help (DRAFT, 2026-09-14)
- [issue-40-41-46-legacy-teardown.md](issue-40-41-46-legacy-teardown.md) - E01-01, E01-02, E01-07, retiring the old server and publishing the maintenance page (DRAFT, 2026-09-14)
- [issue-42-aws-security-review.md](issue-42-aws-security-review.md) - E01-03, AWS account security review (DRAFT, 2026-09-15)
- [issue-43-aws-budget-alert.md](issue-43-aws-budget-alert.md) - E01-04, AWS monthly budget alert (DRAFT, 2026-09-16)
- [issue-44-retire-first-version-credentials.md](issue-44-retire-first-version-credentials.md) - E01-05, retire the first version's credentials (DRAFT, 2026-09-16)

## See also (do not follow recursively)

- [../high-level/road-to-launch.md](../high-level/road-to-launch.md) - which issues come next
- [../test/README.md](../test/README.md) - the test plan that pairs with each design
