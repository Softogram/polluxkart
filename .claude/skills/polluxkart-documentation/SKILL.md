---
name: polluxkart-documentation
description: Use when writing or revising anything under docs/ in PolluxKart, a design or test plan, a README or a skill, or when a decision or a code change makes an existing document wrong. Covers dating every decision, superseding instead of overwriting, writing for the founder, the docs tree and its link rules checked by docslint, exactly where each kind of document belongs, and what must never be written in this public repository.
---

# Writing documentation in PolluxKart

**Status: DRAFT (2026-09-13).**
When the repository disagrees with this skill, the repository wins; fix this skill.

Sources of truth this skill summarizes: `docs/README.md` (the only entry point to the docs), `docs/platform/decisions.md` (the running decision log), and the repository's `CLAUDE.md`.

## Words used below

- **Decision log:** `docs/platform/decisions.md`, the dated list of choices made and why, including ADRs (Architecture Decision Records: a short entry saying what was decided, what else was considered, and why).
- **Low-level design:** a per-issue document concrete enough to build from.
- **Test plan:** a per-issue document saying which tests will prove the feature works.
- **Supersede:** mark an old decision as replaced, and keep it, instead of deleting it.
- **docslint:** the script `tools/docslint/docslint.py`, which checks the docs tree's links and style on every pull request.
- **Generated file:** a file written by a tool, such as the OpenAPI spec, which nobody edits by hand.

## Date every decision

**Every decision written anywhere carries the date it was made.**
Not the date the file was created, and not "recently": the actual day the call was taken.

```markdown
**Decision (2026-09-13): customers sign in with email and password or Google at launch.**
**Status: DRAFT (2026-09-13)**
**Status: APPROVED 2026-09-13 (describes the plan; no code exists yet).**
**Revised 2026-09-13:** was <old choice>, now <new choice>, because <one line>.
**Superseded 2026-09-13** by "<new decision title>": <one line on why>.
```

**Why it is a rule and not a nicety.**
Most of the rebuild's decisions were taken on one day, and many will be revised as the work proceeds.
Two documents can each be right about a different day.
Without a date, a reader cannot tell which is current, and the older one silently wins because it was found first.

Apply it to:

- **Any decision**, wherever it is written: a design document, the decision log, an issue comment, a pull request description, a skill.
- **Any revision:** say what it was, what it is now, and when it changed.
- **Status lines** on every design document and plan.
- **Plan-only documents:** until code exists, a document describing `api/` or `web/` says in its status line that it describes the plan, and the pull request that builds the feature updates that line.

## Supersede, never quietly overwrite

When a decision changes, **do not delete the old one**.
Mark it superseded, date it, and add one line on why it changed.

The reasoning is what makes a document worth keeping.
A reader who only sees the current answer will re-open the discarded option, because nothing records that it was considered and rejected.
Example: the first version relied on phone OTP (one-time password) codes.
The rebuild ships email, password and Google sign-in first (decided 2026-09-13), because business SMS in India needs DLT registration, the sender and message-template registry the telecom regulator requires, which takes weeks.
Writing that down stops the next person proposing OTP login for launch.

The exception is a plain factual error, such as a wrong file path or a typo.
Fix those outright.
A changed number that somebody chose, such as the cash on delivery order limit, is a decision, not a typo.

## Say what is already decided

A design document opens with **"What was already decided before this document"**: each earlier decision, its date, and a link to its decision log entry.
This stops settled questions being asked again in every new design.

Questions for the owner go in their own **"Open questions for the owner"** section, written as questions, with every term explained inside the question itself.

## Write for the founder, not for an engineer

The owner owns the store, not the codebase, and the owner's father runs the shop day to day.
A document they cannot follow is a document that cannot be approved.

- **Explain every technical term where it first appears**, in plain words, right there.
- When a document uses several terms, put a short glossary near the top, and add lasting terms to `docs/platform/glossary.md`.
- Use short sentences, short paragraphs and concrete comparisons.
- Keep the technical accuracy; explain the term, never hide it.
- **Put each sentence on its own line** in markdown, keeping normal headings, lists and tables.
- **Never use the em dash character:** use a plain hyphen, a colon, or two sentences, because docslint fails the build on it.
- Write money for people in rupees, adding paise only where exactness matters, for example "₹1,499 (149900 paise)".
- Use obviously fake examples (`asha@example.com`, pincode `560001`), never real customer data.

## The docs tree

`docs/` is a tree with a single entry point, `docs/README.md`.

- Every folder has a `README.md` saying in a line or two what lives beneath it.
- Every non-README document starts with a parent line, for example `Parent: [product/](README.md) | Index: [docs/](../README.md)`.
- **"Read next"** links point downward only, into the same folder or below; these links form the tree.
- **"See also (do not follow recursively)"** holds every sideways or upward link, and readers take one hop, then stop.
- **Every document must be reachable from `docs/README.md` by following "Read next" links alone.**
- A new document is added to its folder README's "Read next" list in the same change that creates it.

**These rules are enforced, not just written down.**
`tools/docslint/docslint.py` runs in CI on every pull request and fails on a broken link, a "Read next" link pointing sideways or upward, a loop, an unreachable document, or an em dash.
Run `python3 tools/docslint/docslint.py` and `python3 -m unittest discover -s tools/docslint` locally before committing any docs change.

## Where a document belongs

This is the tree, and nothing outside it gets created without a dated decision in the decision log:

```
docs/
  README.md                          the only entry point
  product/                           what the store is and why
    prd.md                           product requirements
    launch-scope.md                  what ships first, what is cut, what comes after
    compliance.md                    Indian e-commerce, GST, consumer and data protection duties
  platform/                          how the whole system fits together
    architecture.md  stack.md  decisions.md  glossary.md
    security.md  testing.md  cost.md  runbook.md
  services/<service>/README.md       one per service (list below)
  design/
    high-level/                      forward-looking, system-wide
      road-to-launch.md  service-boundaries.md  data-model.md
      order-lifecycle.md  infrastructure.md  design-system.md
    low-level/issue-<N>-<slug>.md    per-issue design
    test/issue-<N>-<slug>.md         per-issue test plan
  legacy/                            the first version
    README.md  audit-2026-09.md  parity-checklist.md  emergent-prd.md
```

The services are identity, catalog, media, inventory, cart, order, payment, invoice, shipping, promotion, review, notification and audit.

| You are writing | It goes in |
|---|---|
| A decision and its reasoning | a dated entry in `platform/decisions.md` |
| What the store sells, to whom, and the launch scope | `product/prd.md`, `product/launch-scope.md` |
| Legal pages required, seller details, GST invoice rules, data protection duties | `product/compliance.md` |
| How the built system fits together, and the versions chosen and why | `platform/architecture.md`, `platform/stack.md` |
| A term that will be used again | `platform/glossary.md` |
| Security rules the code must keep (never live ids) | `platform/security.md` |
| Which kinds of test are required, and why | `platform/testing.md` |
| What the system costs to run | `platform/cost.md` |
| Deploy, rollback, restore, incident, secret rotation, daily shop operations | `platform/runbook.md` |
| What one service owns: its schema, `api` interface, routes, events, rules, and what it must never do | `services/<service>/README.md` |
| System-wide plans: build order, service boundaries, tables, order states, AWS setup | `design/high-level/` |
| The fixed colours, fonts and theme tokens | `design/high-level/design-system.md` |
| A design for one GitHub issue, and its paired test plan | `design/low-level/` and `design/test/`, same `issue-<N>-<slug>.md` name |
| Anything about the first version | `legacy/` |

**Older paths in the planning notes.**
The planning notes of 2026-09-13, kept outside the repository, mention `docs/glossary.md`, `docs/design/data-model.md`, `docs/design/order-lifecycle.md`, `docs/design-system/MASTER.md`, `docs/runbooks/` and `docs/legal/`.
Those documents live at `platform/glossary.md`, `design/high-level/data-model.md`, `design/high-level/order-lifecycle.md`, `design/high-level/design-system.md`, `platform/runbook.md` and `product/compliance.md`.
Do not create the older folders.

**A low-level design contains:** what was already decided, the problem, tables and migrations, `api` and route changes with their Problem Details error codes, events, what the user gets when each dependency fails, what is cut, and open questions for the owner.
**A test plan contains** what `polluxkart-testing` lists, and a plan with only happy paths is not finished.

**Legacy documents are records.**
The audit and the old Emergent PRD are not rewritten.
The parity checklist is the one that changes: tick a line only when the feature works end to end on staging, or the owner has dropped it in writing, with the reason next to the line.

## The repository is public

Anyone on the internet can read every document, skill, commit message, issue and pull request.
**Never write these anywhere in the repository:**

- AWS account ids, or ids tied to live systems: instance ids, Elastic IPs, RDS identifiers, hosted zone ids.
- The incident status of credentials: which keys leaked, which are rotated, which are still pending.
- Parameter values from AWS SSM Parameter Store, staging basic-auth passwords, or webhook URLs carrying a secret.
- Admin account email addresses, and the owner's personal contacts beyond the seller details the law requires on the site.
- Customer data of any kind, including in screenshots and examples.
- A description of an unfixed weakness in a live system.

These belong in the private operations reference outside the repository, `~/softogram/POLLUXKART_OPERATIONS.md`.
Documents refer to it by description ("see the private operations reference"), and `platform/runbook.md` explains how the owner reaches it; never copy its contents into `docs/`.

gitleaks (a secret scanner in the pre-commit hook and CI) catches keys, not account ids or incident notes, so this rule depends on the writer.
**If something sensitive was committed**, tell the owner at once and treat it as public.
Do not try to hide it with a follow-up commit or a history rewrite: forks and caches keep it, and rewriting pushed history is forbidden here.

## Generated and auto-maintained files

Never hand-edit `CHANGELOG` files, `api/openapi/openapi.json`, the generated TypeScript client in `web/src/lib/api/`, or lockfiles.
Change the source, then regenerate.

## When code and a document disagree

**The code wins, then fix the document.**
Do not guess which one is stale, and do not leave both standing.
Skills under `.claude/skills/` are documents too, and follow the same rule.
Documentation changes in the same pull request as the behaviour it describes, never "in a follow-up".
If a document claims a rule is enforced, name the test or constraint that enforces it, or do not write the claim.

## Checklist before you open a pull request

- [ ] Every decision, revision and status line carries its date.
- [ ] Changed decisions are marked superseded with a reason, not deleted.
- [ ] Design documents open with what was already decided, and owner questions sit in their own section.
- [ ] Every technical term is explained at first use, and lasting terms are in `docs/platform/glossary.md`.
- [ ] One sentence per line, and no em dash character anywhere.
- [ ] Each new document sits in the folder the table above names, and no folder outside the tree was created.
- [ ] Each new document has a parent line and appears in its folder README's "Read next" list.
- [ ] Sideways and upward links are only under "See also (do not follow recursively)".
- [ ] `tools/docslint/docslint.py` passes locally.
- [ ] No account ids, live resource ids, credential status, secrets or customer data were written.
- [ ] No `CHANGELOG`, generated file or lockfile was hand-edited.
- [ ] Documents describing changed behaviour were updated in this same pull request, and any claimed guard points at a real test.
- [ ] `make ci` passed locally.
