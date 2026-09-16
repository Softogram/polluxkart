# End-to-end test plans

Parent: [design/](../README.md) | Index: [docs/](../../README.md)

One file per ticket, `issue-<N>-<slug>.md`, with the same naming as `../low-level/`.
Written alongside that ticket's design, by whoever writes the design, as part 2 of the ticket's five parts ([development-process.md](../../platform/development-process.md)).
The tests it plans are written in the same implementation pull request as the feature, and the ticket is only done after a verified test run.
It is a plan for what real, full-request coverage the feature needs, not the test code itself.

## What goes in a plan

For each request flow the feature exposes:

- **The flow:** method, path, and in one sentence what it is for.
- **The happy path:** a representative request, the expected status code, and the shape of the response.
- **The error paths that matter:** the specific refusals the issue's acceptance criteria call out, such as "another user's order", "out of stock", "price changed", "illegal transition". Point each back at its acceptance criterion.
- **Fixtures or seed state** a test needs first, and how to create it through real interfaces rather than raw SQL.
- **What the user gets when a dependency fails:** for every dependency the flow touches (database, Razorpay, SES, S3, another service), what happens when it is unreachable, slow, or returns an error.
- **The reachability check:** for every new database write, the real request that causes it, and that the test reads the table back.
- **Concurrency and replay,** where money, stock, coupons or invoice numbers are involved.
- **What is deliberately not covered, and why.**

**A plan containing only happy paths is not finished.**

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

## See also (do not follow recursively)

- [../../platform/testing.md](../../platform/testing.md) - the kinds of test and the bar for a pull request
