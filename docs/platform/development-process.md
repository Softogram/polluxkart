# Development process: tickets, stages and the owner's approval

Parent: [platform/](README.md) | Index: [docs/](../README.md)

**Status: Owner decision, 2026-09-13.** Recorded in [decisions.md](decisions.md), "Nothing is implemented without the owner's approval".

## The rule

**Nothing is implemented without the owner's explicit approval.**

The owner (GitHub `CosmicSaaurabh`) is responsible for every product and design decision.
Everyone else, people and AI agents alike, works only on tickets the owner has marked implementation ready.
No product or design answer is ever assumed or invented: if it is not recorded as an owner decision, it is asked.

## Glossary

- **Epic:** a GitHub issue for a large piece of work, such as "GST invoices", labelled `epic`. Its tickets are attached to it as GitHub sub-issues (a native parent and child link between issues).
- **Ticket:** a GitHub issue for one feature or one piece of work, small enough for one implementation pull request.
- **Stage label:** a label on a ticket showing where it stands, such as `stage: planning`.
- **Planning pull request:** a pull request that adds or changes documents only: a design, a test plan, a decision.
- **Implementation pull request:** a pull request that changes code, configuration or infrastructure, together with its tests.
- **Approval gate:** an automated check that fails an implementation pull request unless its ticket was approved by the owner.

## Who does what

| Role | Does | Never does |
|---|---|---|
| **Owner** (`CosmicSaaurabh`) | Answers product and design questions; reviews designs and test plans; applies `stage: implementation-ready` by hand on GitHub | Delegates that label to anyone or to an agent |
| **Contributors** (2 to 3 people) | Pick up implementation-ready tickets; write the implementation and its tests; propose designs for planning tickets | Start implementation on a ticket that is not implementation ready; decide a product or design question |
| **AI agents** | Draft designs, test plans and tickets for the owner to review; implement approved tickets | Apply `stage: implementation-ready`; implement an unapproved ticket; fill a missing decision with a guess |

## How work is broken down

1. The plan in [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md) is split into **epics**.
2. Each epic is split into **tickets**, one per feature or piece of work, attached as sub-issues.
3. Every ticket links to the design documents it depends on and lists, separately:
   - what the owner has already decided, with the date;
   - what the docs propose but the owner has not confirmed;
   - open questions for the owner.
4. Tickets that only the owner can complete (account sign-ups, sign-offs, business details) also carry the `owner-action` label.

## The six stages

| Stage label | Meaning | Who moves it here | What must be true |
|---|---|---|---|
| `stage: planning` | Design and product questions are being discussed | Anyone creating the ticket | The ticket exists with its details |
| `stage: awaiting-approval` | The design and test plan are written; waiting for the owner | The person who wrote the plan | Every open question has a dated owner answer in [decisions.md](decisions.md); the design and test plan are in a planning pull request |
| `stage: implementation-ready` | **Approved by the owner** | **The owner only, by hand** | The owner has reviewed the design and test plan |
| `stage: in-progress` | Being implemented | The contributor who picks it up (and assigns themselves) | The ticket was implementation ready |
| `stage: in-review` | The implementation pull request is open | The contributor | The pull request contains the feature and its tests |
| `stage: done` | Merged with a verified test run | The contributor, when the pull request merges | The verified test run is recorded; the issue is closed |

A ticket carries exactly one stage label.
If the owner changes their mind after approval, they move the ticket back to `stage: planning`, and any implementation pull request stops passing the gate.

## One ticket owns all five parts

Every ticket is responsible, from start to finish, for:

1. **Feature planning:** a design in `docs/design/low-level/issue-<N>-<slug>.md`.
2. **Test planning:** a test plan in `docs/design/test/issue-<N>-<slug>.md`.
3. **Feature implementation.**
4. **Test implementation.**
5. **A verified test run:** `make ci` passing locally, with the output recorded in the pull request. GitHub Actions CI runs at release and on demand, not on every pull request.

Parts 1 and 2 may be one or more **planning pull requests**.
Parts 3 and 4 are **one implementation pull request**: the feature and its tests always arrive together.
Part 5 is evidence in that same implementation pull request.

## Pull request rules

| | Planning pull request | Implementation pull request |
|---|---|---|
| Changes | Markdown documents only | Anything else (code, configuration, workflows, infrastructure), plus any documents it updates |
| Links its ticket with | `Plans #N` on its own line | `Implements #N` on its own line, and `Closes #N` so merging closes the ticket |
| Ticket stage required | Any open ticket | `stage: implementation-ready`, `stage: in-progress` or `stage: in-review`, with the approval label applied by the owner |
| Tests | Not applicable | Required: if it changes `api/**/src/main`, it also changes `api/**/src/test`; if it changes `web/src`, it also changes a test in `web/` or `e2e/` |
| May use closing words (`closes`, `fixes`, `resolves`) | **No**, because planning must not close the ticket | Yes, for its one ticket |

Exceptions:
- Pull requests opened by Dependabot (automated dependency updates) pass the gate without a ticket.
- The pull request that introduces this process (ticket E00-01) cannot be checked by a gate that does not exist yet; it waits for the owner's approval label and is merged at the owner's request.

## How the rule is enforced

- **Approval gate** (`.github/workflows/approval-gate.yml` running `tools/approval_gate/gate.py`): a required check on every pull request. It reads the linked ticket, its current stage label, and the ticket's label history, and fails unless the approval label was applied by the owner. It runs from the base branch definition, so a pull request cannot change the check that judges it.
- **Label guard** (`.github/workflows/approval-label-guard.yml`): if anyone other than the owner applies `stage: implementation-ready`, the label is removed at once and a comment explains why.
- **Agent guard** (`.claude/settings.json` with `.claude/hooks/guard_approval_label.py`): Claude Code refuses any command that would apply, create, rename or delete the approval label, so an agent cannot approve a ticket even when it runs with the owner's GitHub login.
- **Branch rulesets** on `development` and `main` make the approval gate and the docs check required before merging (set up after this process lands).
- **Written rules:** this page, the repository `CLAUDE.md`, the `polluxkart-workflow` skill, the pull request template and the issue templates.

**A known limit, stated plainly:** GitHub cannot tell the owner apart from an agent using the owner's own login. The agent guard closes that gap for Claude Code sessions in this repository; the owner should still apply the approval label by hand in the GitHub website, never through an agent.

## Recording decisions

- Every product or design answer the owner gives goes into [decisions.md](decisions.md) as a dated entry marked "Owner decision", in the planning pull request for its ticket.
- The ticket's "Decided by the owner" section links to that entry.
- A changed decision gets a new dated entry; the old one is marked superseded. The latest dated entry holds.
- Anything not chosen by the owner stays marked "Proposed" until it is.

## For contributors: picking up a ticket

1. Filter issues by `stage: implementation-ready` and pick one without an assignee.
2. Assign yourself and change the stage to `stage: in-progress`.
3. Create a git worktree from a freshly fetched `origin/development`.
4. Read the ticket's design and test plan; if something is unclear or missing, ask on the ticket and wait for the owner's answer instead of guessing.
5. Implement the feature and its tests together; run `make ci`.
6. Open one pull request with `Implements #N` and `Closes #N`, and change the stage to `stage: in-review`.
7. After merge, the ticket closes; set `stage: done`.

## See also (do not follow recursively)

- [../design/low-level/README.md](../design/low-level/README.md) - how a design document is written
- [../design/test/README.md](../design/test/README.md) - how a test plan is written
- [testing.md](testing.md) - what a verified test run includes
