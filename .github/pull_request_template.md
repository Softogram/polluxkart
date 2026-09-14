<!--
Nothing is implemented without the owner's approval (owner rule, 2026-09-13).
Rules: docs/platform/development-process.md. The approval-gate check enforces them.

Keep exactly ONE of the two ticket lines below, on its own line:
- Plans #N       for a planning pull request: Markdown documents only, and no closing keywords.
- Implements #N  for an implementation pull request: the ticket must be labelled
                 `stage: implementation-ready` by the owner, and the feature and its tests
                 ship together. Add "Closes #N" for the same ticket.
-->

Plans #N
Implements #N
Closes #N

## What changed

<!-- Two or three plain sentences. Explain any technical term. -->

## Why

<!-- The problem this solves, and the owner decisions it follows (link docs/platform/decisions.md entries). -->

## Verified test run (implementation pull requests)

<!-- Paste the end of `make ci` output and link the green CI run. -->

## Checklist

- [ ] The linked ticket's stage is correct (`stage: awaiting-approval` for a finished plan, `stage: in-review` for an implementation).
- [ ] No product or design decision was assumed; every answer used is an owner decision in `docs/platform/decisions.md`.
- [ ] Implementation only: the feature and its tests are both in this pull request.
- [ ] `make ci` passed locally.
- [ ] Staged explicit paths only; no stash, reset, rebase or force push; no agent co-author lines.
