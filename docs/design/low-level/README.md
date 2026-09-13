# Low-level designs

Parent: [design/](../README.md) | Index: [docs/](../../README.md)

One document per GitHub issue, written **before** the issue is built, and concrete enough to implement from: real class and method names, real file paths, real SQL, and the edge cases already found while designing.

Naming: `issue-<N>-<short-slug>.md`.
Several issues that ship together share one document, named after all of them.

**A design is not final until the owner has explicitly approved it.**
A document existing here does not mean it is ready to build; check its status line.

## What every design contains

- **Status line**, dated: `**Status: DRAFT (YYYY-MM-DD)**` or `**Status: APPROVED YYYY-MM-DD**`.
- **What was already decided before this document**, with dates, so settled questions are not re-opened.
- **The change**, by service: interface methods and records, tables and migrations, endpoints, events, frontend routes.
- **Edge cases and failure behaviour** for every dependency the change touches.
- **What is deliberately not covered**, and why.
- **A link to the matching test plan** in `../test/`.

## Read next

No designs have been written yet (2026-09-13).
The first ones will cover Phase 2: the backend foundation, the frontend foundation, and the local stack.

## See also (do not follow recursively)

- [../high-level/road-to-launch.md](../high-level/road-to-launch.md) - which issues come next
- [../test/README.md](../test/README.md) - the test plan that pairs with each design
