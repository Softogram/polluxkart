# PolluxKart documentation

**Start here. Always.**

This is the only entry point to PolluxKart's documentation.
Everything below is a tree: each folder has a README that says what lives beneath it, and nothing else.
You should be able to reach any answer in two or three files without searching.

## How to read these docs (for people and for agents)

Four rules.
They exist so that finding an answer costs a couple of files rather than twenty, and so an agent following links can never go round in circles.

1. **Enter here.** Do not search the docs tree blind. Pick a branch below, open its README, and follow it down.
2. **Follow "Read next" links only.** Every README has a "Read next" section. Those links always point downward into the tree, never sideways or back up, so following them cannot loop.
3. **"See also" links are different.** They point across branches, because inventory genuinely relates to orders. Read one only if the answer was not in the branch you are already in, and never follow a "See also" chain recursively. One hop, then stop.
4. **Stop when the question is answered.** Most answers sit two files deep. If you are four files in and still reading, you are probably in the wrong branch; come back here and pick another.

**These rules are checked automatically.**
`tools/docslint/docslint.py` runs on every pull request.
A broken link, a "Read next" link pointing sideways or upward, a loop, a document nobody can reach from this page, or an em dash all fail the check.

## The branches

| Branch | What it answers | Go here when |
|---|---|---|
| **[product/](product/)** | What PolluxKart is, who it is for, what ships at launch, which laws apply | You need the why: the store, the shopper, the launch scope, legal duties |
| **[platform/](platform/)** | How the whole system fits together | You need the architecture, the technology and versions, the decision log, security, testing, cost, or a term defined |
| **[services/](services/)** | One folder per backend service, the deep detail | You need what identity, catalog, inventory, order, payment, invoice or another service owns and promises |
| **[design/](design/)** | Design and test documents | You are about to build something, or need the plan, the data model, or the order lifecycle |
| **[legacy/](legacy/)** | The first version of the store and why it was replaced | You want to know what went wrong before, or what the rebuild must still cover |

## Read next

Pick the branch you need:

- [product/](product/README.md) - the store, the launch scope, compliance
- [platform/](platform/README.md) - architecture, stack, decisions, glossary
- [services/](services/README.md) - one folder per backend service
- [design/](design/README.md) - high-level plans, per-issue designs, test plans
- [legacy/](legacy/README.md) - the audit of the first version and the parity checklist

## Common questions, and where they are answered

Shortcuts for the things people look up most.
Each is one hop.

| Question | Answer lives in |
|---|---|
| What are we building, and in what order? | [design/high-level/road-to-launch.md](design/high-level/road-to-launch.md) |
| Why was this decided this way? | [platform/decisions.md](platform/decisions.md) |
| How do the services talk to each other, and how can one move to its own server later? | [design/high-level/service-boundaries.md](design/high-level/service-boundaries.md) |
| What tables exist, and what rules does the database enforce? | [design/high-level/data-model.md](design/high-level/data-model.md) |
| What states can an order be in? | [design/high-level/order-lifecycle.md](design/high-level/order-lifecycle.md) |
| Which Java, Spring Boot, PostgreSQL and Next.js versions, and why? | [platform/stack.md](platform/stack.md) |
| Can I change a colour or font? | [design/high-level/design-system.md](design/high-level/design-system.md) - **no, the theme is fixed** |
| What does this term mean? | [platform/glossary.md](platform/glossary.md) |
| Which legal pages and rules does an Indian store need? | [product/compliance.md](product/compliance.md) |
| What went wrong in the first version? | [legacy/audit-2026-09.md](legacy/audit-2026-09.md) |

## Three things to know before you rely on any of this

**No application code exists yet (as of 2026-09-13).**
The first version lives in `legacy/` as reference only.
Every document describing `api/` or `web/` describes the approved plan, not built code, and says so in its status line.
When code lands and disagrees with a document, the code wins, and the document gets fixed the same day.

**The repository is public.**
Account ids, live resource ids, credential status and anything else that would help an attacker are kept out of this tree.
They live in a private operations reference outside the repository, described in [platform/runbook.md](platform/runbook.md).

**The store's colours, fonts and theme are fixed (owner decision, 2026-09-13).**
The rebuild changes how the store works and how it is laid out, never how its brand looks.
