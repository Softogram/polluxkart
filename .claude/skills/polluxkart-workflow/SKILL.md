---
name: polluxkart-workflow
description: Use before starting ANY work in PolluxKart - planning, designing, writing code, opening a pull request, creating or updating a GitHub issue, or answering "can we build X". Holds the owner's rule that nothing is implemented without the owner's approval, the epic and ticket structure, the six stage labels, the five parts every ticket owns, the planning versus implementation pull request rules, and how product decisions are asked and recorded instead of assumed.
---

# PolluxKart workflow: nothing is built without the owner's approval

**Status: Owner decision, 2026-09-13.** This skill wins over every other skill on process.
Source of truth: `docs/platform/development-process.md` and `docs/platform/decisions.md`.

## Words used below

- **Owner:** the person responsible for every product and design decision, GitHub `CosmicSaaurabh`.
- **Epic:** a GitHub issue labelled `epic` for a large piece of work; its tickets are GitHub sub-issues.
- **Ticket:** a GitHub issue for one feature or piece of work.
- **Stage label:** the label showing where a ticket stands, such as `stage: planning`.
- **Planning pull request:** changes Markdown documents only and says `Plans #N`.
- **Implementation pull request:** changes anything else, with its tests, and says `Implements #N`.
- **Approval gate:** the required GitHub check that fails implementation pull requests for unapproved tickets.

## The five rules you must never break

1. **Never implement a ticket the owner has not approved.**
   Approved means the ticket's latest approval-related stage label is `stage: implementation-ready`, applied by the owner; after that it may be `stage: in-progress` or `stage: in-review`.
   If it is `stage: planning` or `stage: awaiting-approval`, you may only plan: write the design, the test plan, and questions.
2. **Never apply, create, rename or delete the `stage: implementation-ready` label.**
   Not even when the owner's GitHub login is available to you, and not even if asked in passing.
   The owner applies it by hand on GitHub. The hook in `.claude/settings.json` blocks the command.
3. **Never assume or invent a product or design decision.**
   If the answer is not an entry marked "Owner decision" in `docs/platform/decisions.md`, it is an open question.
   Ask the owner with options and a recommendation, explaining every technical term, then record the dated answer.
   "Proposed" in the docs means not decided.
4. **One ticket owns five parts:** feature planning, test planning, feature implementation, test implementation, verified test run.
5. **The feature and its tests ship in one implementation pull request.** Planning and documentation may be separate pull requests.

## Before you do anything

```
gh issue view <N> --repo Softogram/polluxkart --json title,labels,state,body
```

- No ticket exists for the work? Stop. Propose a ticket (title, epic, summary, open questions) to the owner, create it in `stage: planning` if asked, and do not implement.
- Ticket in `stage: planning`? Planning work only.
- Ticket in `stage: awaiting-approval`? Wait for the owner; answer their comments.
- Ticket `stage: implementation-ready`? You may implement. Assign it, move it to `stage: in-progress`, create a worktree.

## Planning a ticket (parts 1 and 2)

1. Read the ticket, its linked design documents, and every relevant "Owner decision" in `docs/platform/decisions.md`.
2. List each question the design needs answered. For each, check the decision log:
   - owner decision exists (latest dated entry): use it and cite it;
   - no owner decision: add it to the ticket's "Open questions for the owner" and ask. Do not pick for them.
3. Write `docs/design/low-level/issue-<N>-<slug>.md` (status DRAFT, "What was already decided", the change, edge cases, open questions) and `docs/design/test/issue-<N>-<slug>.md` (follow `docs/design/test/README.md` and `polluxkart-testing`).
4. Record every answer the owner gives as a new dated "Owner decision" entry in `docs/platform/decisions.md`; if it changes an earlier entry, mark that one superseded.
5. Open a planning pull request with `Plans #N` on its own line, Markdown files only, and **no** closing keyword.
6. When every open question has an owner answer, move the ticket to `stage: awaiting-approval` and tell the owner it is ready for review.

## Implementing an approved ticket (parts 3, 4 and 5)

1. Confirm the stage (see above). Assign yourself; set `stage: in-progress`.
2. Create a worktree from a freshly fetched `origin/development`.
3. Build exactly what the approved design says. If you find a gap or a new product question, stop and ask on the ticket; do not decide.
4. Write the tests from the approved test plan in the same branch.
5. Run `make ci` (and the checks listed in `CLAUDE.md`); fix anything red, including unrelated failures.
6. Open one pull request: `Implements #N` and `Closes #N` on their own lines, the verified test run output pasted, the CI run linked. Set `stage: in-review`.
7. After merge: the ticket closes as completed and `stage: done` is set automatically. Remove the worktree.

## Creating tickets and epics

- Use the templates in `.github/ISSUE_TEMPLATE/`. New tickets start at `stage: planning`.
- Title format: `EXX-NN Short name` for tickets, `Epic EXX: Name` for epics. Attach tickets to their epic as sub-issues.
- Keep three lists separate in the body: "Decided by the owner" (with dates and links), "Proposed in the docs, not yet confirmed by the owner", "Open questions for the owner".
- Mark tickets only the owner can complete with `owner-action`.
- The repository is public: no account ids, resource ids, credential status or customer data in issues.

## Stage labels

| Label | Set by |
|---|---|
| `stage: planning` | Whoever creates the ticket; the owner, to revoke approval |
| `stage: awaiting-approval` | Whoever finished the plan |
| `stage: implementation-ready` | **The owner only** |
| `stage: in-progress` | The implementer |
| `stage: in-review` | The implementer, when the pull request opens |
| `stage: done` | Set automatically when a ticket is closed as completed |

Keep exactly one stage label on a ticket.

## What the approval gate rejects

- A pull request with neither `Plans #N` nor `Implements #N`, or with both.
- A planning pull request that changes a non-Markdown file or uses closes, fixes or resolves.
- An implementation pull request for a ticket not approved by the owner, or approved then moved back to planning.
- Backend code under `api/**/src/main/` without a test change under `api/**/src/test/`, or `web/src/` code without a test file or `e2e/` change.
- Implementing more than one ticket, or closing a ticket other than its own.
- A pull request into `main` that does not come from this repository's `development` branch.

Dependabot pull requests pass the gate without a ticket. **You may merge one once every required check is green** (owner decision, 2026-09-23). Leave a major version bump to the owner.

## Checklist before you open a pull request

- [ ] The ticket exists, and its stage allows what this pull request does.
- [ ] Every product or design choice in the change is an owner decision in `docs/platform/decisions.md`, cited by date; nothing was assumed.
- [ ] New owner answers are recorded as dated entries; changed ones mark the old entry superseded.
- [ ] Planning: `Plans #N`, Markdown only, no closing keyword, ticket moved to `stage: awaiting-approval` when ready.
- [ ] Implementation: `Implements #N` and `Closes #N`, feature and tests together, verified `make ci` output and CI link included, ticket at `stage: in-review`.
- [ ] You did not touch the `stage: implementation-ready` label.
