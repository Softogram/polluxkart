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

- [issue-34-makefile-ci-doctor.md](issue-34-makefile-ci-doctor.md) - E00-04, `make ci` and `make doctor` (DRAFT, 2026-09-14)

## See also (do not follow recursively)

- [../high-level/road-to-launch.md](../high-level/road-to-launch.md) - which issues come next
- [../test/README.md](../test/README.md) - the test plan that pairs with each design
