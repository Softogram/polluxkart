---
name: polluxkart-code-review
description: Use when reviewing any PolluxKart change (Java and Spring Boot service code, Flyway migrations, Next.js pages and components, tests, or the docs that ship with them) before a pull request is approved or marked ready, including a self-review of your own work. Covers the second-door check, service boundaries, wire-safe contracts, money and idempotency, security and privacy, migrations, frontend rules, git hygiene, and how to report findings by severity.
---

# Reviewing a change in PolluxKart

**Status: DRAFT (2026-09-13).**
Written before any application code exists, so paths below are the approved plan.
When the repository disagrees with this skill, the repository wins; fix this skill.

This is a checklist, not a vague "looks good".
Each section names the skill that covers its topic in depth.

## Words used below

- **Service:** one Maven module owning one business area (identity, catalog, media, inventory, cart, order, payment, invoice, shipping, promotion, review, notification, audit).
- **`api` and `internal` packages:** every service exposes an `api` package (an interface plus plain records) that others may call, and an `internal` package nobody else may touch.
- **Schema:** a named group of tables inside PostgreSQL; each service owns exactly one.
- **Transaction:** a group of database changes that either all happen or none happen.
- **Idempotency key:** a unique value sent with a request, so a repeat returns the first result instead of doing the work twice.
- **Problem Details (RFC 9457):** a standard JSON error format; ours always carries a stable `code` the frontend branches on.
- **PII (personally identifiable information):** anything that points at a real person, such as a name, email, phone number or address.
- **Wire-safe:** data that can travel between processes as plain JSON or gRPC messages without losing meaning.
- **IDOR (Insecure Direct Object Reference):** changing an id in a request shows or changes someone else's data.
- **Design token:** a named colour, font, radius or shadow defined once in the theme and used everywhere by name.

## How to run a review

0. **Check approval first (owner rule, 2026-09-13).** An implementation pull request must say `Implements #N` for a ticket the owner labelled `stage: implementation-ready`, and the approval-gate check must be green. If not, stop the review and say so: unapproved work is a blocker regardless of quality. Any product or design choice in the diff that is not an "Owner decision" in `docs/platform/decisions.md` is also a blocker. See `polluxkart-workflow`.
1. Read the issue, its design in `docs/design/low-level/issue-<N>-<slug>.md`, and its test plan in `docs/design/test/`.
2. If the change needs a table, endpoint or contract the design does not describe, flag it back rather than approving improvised structure.
3. Read the whole diff, then open the files around it, because the guard you need to compare against usually lives beside the other door, outside the diff.
4. Run `make ci` in your own worktree, or read its full output; never take "tests pass" on trust.
5. For every sentence claiming something is enforced, find the test or constraint that enforces it.
6. Report findings by severity, using the format at the end.

## The second door: ask this first

Ask it whenever a change adds a second writer to data something else already writes, or a second route to a field something else already checks:

> **Does the new door inherit the protection the old one has, or was it simply written without it?**

Each door is correct on its own and every existing test passes, so no test suite catches this.
Only a reviewer asking "what else touches this?" sees it, at the one moment it is cheap to fix.

The first version of PolluxKart had every one of these (`docs/legacy/audit-2026-09.md`):

| The door that was guarded | The one that was not |
|---|---|
| `legacy/backend/routes/admin.py` routes required `require_admin` | product edits, order status and stock adjustment in `products.py`, `orders.py` and `inventory.py` only required a login (audit 1.3) |
| Logging in required the current password | `POST /api/auth/reset-password` set a new password with no proof of ownership (audit 1.1) |
| Verifying a phone required the OTP (one-time password) | `GET /api/otp/debug/{phone}` handed the OTP to anyone (audit 1.2) |
| The backend computed shipping and tax | the cart and checkout pages each computed their own, different numbers (audit 3.4) |

Doors the rebuild will have, and the guard every door to the same data must share:

| Data or decision | Its doors | The shared guard |
|---|---|---|
| A customer's order | detail page, invoice PDF, payment retry, cancel, review | ownership check against the session user |
| `inventory.reserved` | order placement, expiry job, late capture, cancellation, shipment | the conditional UPDATE, CHECK constraints, SKUs locked in sorted order |
| Order status | customer cancel, admin screens, Razorpay webhook, browser verify call, expiry job | the one transition table, with history and audit rows |
| Passwords and sessions | password change, reset, Google account linking, disabling a user, role change | revoke sessions, and identical responses whether an email exists or not |
| User fields in responses | profile, admin users list, account data export | an explicit response record that never includes hashes, TOTP secrets or tokens |
| Coupon usage | order placement, payment retry, re-placing after `price_changed` | the row-locked limit check |
| Rate limits | login, reset, verification resend, order creation, and any new route doing the same job | the same Bucket4j limit |

Running the check:

- [ ] **Does this write a table something else already writes?**
  Find every other writer.
  If one takes a lock, this one needs the same lock, and the value it writes must be read inside that lock.
- [ ] **Does this read or write a field another route already validates?**
  Search for the field across `api/` and apply the same rule by calling it, not by copying it.
- [ ] **Is a rule being written a second time rather than called?**
  Three copies of the totals maths is how the first version charged a different amount than it showed.
- [ ] **Does a new check fail open?**
  The first version skipped the webhook signature check when the secret was not configured (audit 1.6); a missing secret must stop startup instead.
- [ ] **Could the guard live in the database instead?**
  A CHECK, UNIQUE constraint or grant covers every door, including doors nobody has written yet.

### A comment claiming a guard is not a guard

The first version's admin users query removed a field named `password`, while the stored field was `password_hash` (audit 1.5).
The code read as safe to anyone skimming it, and every password hash leaked.
Prose and enforcement drift apart silently, and prose is what the next reader trusts.

- [ ] A comment, pull request description, document or skill says a rule is enforced, or that a test keeps two things in step: open that test or constraint.
- [ ] If it does not exist, report it as a finding at the severity of the harm it was meant to prevent.

## Service boundaries (`polluxkart-architecture`)

- [ ] Nothing imports another service's `internal` package, and no exclusion was added to Spring Modulith or ArchUnit rules to get the build green.
- [ ] Every new dependency between services follows the one-way table (Rule 7 in `docs/design/high-level/service-boundaries.md`): notification and audit depend on no service, payment never calls order.
- [ ] No SQL touches another service's schema: no cross-schema join, foreign key, view or native query; references across services are ids only.
- [ ] Calls to another service go through its `api` interface and are batched, one call for a list of SKUs rather than one call per item in a loop.
- [ ] No call relies on the caller's transaction, because the callee may run in another process one day and a rollback here would not undo its write.
- [ ] Side effects in other services (emails, audit rows, stock commit at shipment) travel as events through Spring Modulith's durable event publication registry.
- [ ] Controllers sit in the service that owns the data, under `/api/v1/...`, never touch repositories directly, and never return JPA entities.
- [ ] Flyway migrations live inside the owning service's module.

## Wire-safe contracts

- [ ] `api` records hold only strings, numbers, booleans, enums, lists and nested records.
- [ ] No JPA entity, Hibernate lazy proxy, Spring type (`Page`, `Pageable`, `ResponseEntity`), `Object`, `Map<String, Object>` or exception appears in an `api` signature.
- [ ] Failures are typed error codes that map to a gRPC status, not meaning hidden in exception messages.
- [ ] Every new `api` method has a serialization round-trip sample (`polluxkart-testing`).
- [ ] A removed or renamed REST field is a breaking change that `oasdiff` flags; confirm it is intended and that `web/` changes in the same pull request.

## Money, orders and idempotency (`polluxkart-commerce`)

- [ ] Money is `long` paise in Java, `BIGINT` in SQL and a whole number in TypeScript; any `double` or `float` near money is a blocker.
- [ ] Tax and rounding go through the one tax engine, with no second rounding anywhere else.
- [ ] Totals come only from `POST /checkout/quote`; the server never trusts a price, discount, tax or total sent by the client.
- [ ] `POST /orders` compares the client's expected total and returns 409 `price_changed` with a fresh quote when it moved.
- [ ] Every retryable mutation takes an idempotency key: `POST /orders` requires `Idempotency-Key`, mutating `api` methods take a key, and webhook events are deduplicated by provider event id.
- [ ] **No remote call inside a database transaction.**
  Look for `@Transactional` methods that call Razorpay, SES, S3 or another service's `api`.
  A slow response holds row locks, and a rollback cannot undo what the remote side already did.
- [ ] Status changes go through the one transition table, illegal moves return 409, and every change writes history and audit rows.
- [ ] Stock changes only through the conditional reserve UPDATE or recorded movements; nothing sets `on_hand` directly.
- [ ] Scheduled jobs use ShedLock and are safe to run twice.

## Security and privacy (`polluxkart-security-checklist`)

- [ ] **Every read or write by id checks the owner**, and an IDOR test proves it.
- [ ] Admin actions exist only under `/api/v1/admin/`, and no debug, setup or data-wiping endpoint exists anywhere.
- [ ] Responses are built from explicit response records, never from an entity with fields removed.
- [ ] Errors go through the central Problem Details handler; new codes appear in the OpenAPI spec and the frontend error mapping.
- [ ] No exception text, SQL or stack trace reaches a client.
- [ ] **No PII or secrets in logs:** no names, emails, phones, addresses, session or reset tokens, OTPs, TOTP secrets, payment details, Razorpay signatures or raw webhook bodies.
- [ ] Logs carry ids instead (user id, order id, request id), and Sentry's personal data sending stays off.
- [ ] New login-like or order-creating routes have a rate limit, and mutating routes require the CSRF token.
- [ ] Uploads are checked by their first bytes (JPEG, PNG, WebP, AVIF only, never SVG).
- [ ] Required configuration is a validated `@ConfigurationProperties` record, so a missing secret stops startup.
- [ ] No secret, key, account id or live resource id appears in code, config or docs, because the repository is public.

## Migrations (Flyway)

- [ ] **Forward-only:** a new file; a migration that has run anywhere, staging included, is never edited or deleted.
- [ ] **Backward-compatible with the running version**, because the deploy migrates before the new app starts and a rollback keeps the new schema.
- [ ] A new required column is added nullable or with a default first and made strict in a later release; a rename is add, copy, switch, then drop.
- [ ] Rules live in constraints (CHECK, UNIQUE, NOT NULL), timestamps are `timestamptz`, ids are UUIDv7, amounts are `BIGINT` paise.
- [ ] `pk_app` gets only the grants it needs, and never `UPDATE` or `DELETE` on `audit_log`.

## Frontend (`polluxkart-frontend`, `polluxkart-design`)

- [ ] **No `fetch`, `axios` or hand-built API URL outside `web/src/lib/api/`**; every call uses the generated typed client.
- [ ] No mock or placeholder data in app code: no invented products, reviews, ratings or addresses.
- [ ] The UI does no money maths; it shows the server quote and formats paise through one shared formatter.
- [ ] Catalog pages are server components that never read cookies, since reading one makes the page dynamic and uncacheable.
- [ ] **Every list has four states:** loading skeleton, empty, no matches, and error with the request id.
- [ ] **Filter, sort, page and variant state live in the URL**, so the back button and a shared link both work.
- [ ] Errors are handled by Problem Details code, never by matching message text, and server field errors land on their form fields.
- [ ] **Theme tokens only.**
  The owner fixed the existing colours, fonts and theme (2026-09-13).
  No raw hex, `rgb()` or `hsl()` values, no Tailwind palette classes such as `bg-teal-500`, no arbitrary values such as `text-[#14b8a6]`, and no new token.
  A new colour is a blocker even when it looks better.
- [ ] A text and background pair that fails contrast (white on the teal primary does) is raised with the owner, never solved by picking a new colour.
- [ ] **Accessibility:** every control has an accessible name, no button sits inside a link, images have alt text, focus is visible, tap targets are at least 44 px, and no action is hover-only.
- [ ] No dark patterns: no false urgency, pre-ticked boxes or invented reviews, and `aggregateRating` appears only with real reviews.
- [ ] Only first-party scripts load, Razorpay Checkout.js loads only on `/checkout`, and the Content Security Policy is not loosened.
- [ ] `dangerouslySetInnerHTML` never receives content a user can influence.

## Tests (`polluxkart-testing`)

- [ ] Every documented rejection has a test asserting the exact status and Problem Details code.
- [ ] New writes have a reachability test, owned resources an IDOR test, races a multi-round concurrency test, and cross-service steps a crash test.
- [ ] No skipped, disabled or `.only` test, and Playwright keeps `retries: 0`.
- [ ] A bug fix shows its reproduction failing before the fix.

## Git hygiene and process

- [ ] The work happened in its own worktree cut from freshly fetched `origin/development`, and the pull request targets `development`.
- [ ] Only intended files are committed: no stray lockfiles, `graphify-out/`, `.cursor/`, logs or editor folders.
- [ ] The pull request timeline shows no force push, and the author used explicit `git add <path>`, never `git add -A`, `git add .` or `git commit -a`.
- [ ] No `git stash`, `reset --hard`, `checkout -- .`, `clean`, `rebase` or `commit --amend` on pushed commits was used to produce the branch.
- [ ] No `Co-Authored-By` agent trailer in any commit message; the owner's rule overrides default attribution.
- [ ] No closing keyword such as `fixes` or `closes` sits before an issue reference unless the issue really closes, since GitHub closes it even inside "does not fix".
- [ ] `CHANGELOG` files and generated files (`api/openapi/openapi.json`, the generated TypeScript client) were regenerated, never hand-edited.
- [ ] Docs changed in the same pull request as the behaviour they describe (`polluxkart-documentation`), with no em dash characters.
- [ ] `make ci` passed locally before the pull request was opened.
- [ ] Unrelated lint errors, test failures or flaky tests you noticed are reported too, because the owner wants them fixed wherever they are found.

## Reporting findings

| Severity | Meaning | Examples | Can it merge? |
|---|---|---|---|
| **Blocker** | Harms money, stock, security, privacy or data, or breaks a fixed rule | oversell path, client-trusted total, missing ownership check, PII in a log, `double` money, edited applied migration, new colour, import of another service's `internal` | No |
| **Major** | A real defect or missing proof that will cost later | remote call inside a transaction, missing idempotency key, missing rejection test, missing list state | Fix first, unless the owner accepts it in writing, dated |
| **Minor** | Works, but harder to maintain or understand | duplicated helper, unclear name, unexplained term in a doc | Fix now or file a follow-up issue |
| **Nit** | Taste | wording, ordering | Author's choice |

Write each finding in plain English, the same way every time (the path below is illustrative):

```
[Blocker] api/payment/src/main/java/.../CreateRazorpayOrder.java:88
What: the Razorpay order is created inside the @Transactional method.
Why it matters: a slow Razorpay reply holds the stock locks, and a rollback leaves a Razorpay order we never recorded.
Evidence: line 72 opens the transaction; line 88 calls the HTTP client.
Suggested fix: create the Razorpay order after commit, one payments row per attempt.
```

End the review with three short lists: what you checked and found sound, what you did not check (for example "did not run the E2E suite"), and the findings by severity.
Never approve while a blocker is open.

## Checklist before you open a pull request

- [ ] You ran this whole review against your own diff first, second-door check included.
- [ ] Every sentence in code, docs or the pull request that claims a guard points at a real test or constraint.
- [ ] No import of another service's `internal`, no cross-schema SQL, no remote call inside a transaction.
- [ ] Contracts are wire-safe, and new `api` methods have round-trip samples.
- [ ] Money is integer paise, totals come only from the server quote, and retryable mutations take an idempotency key.
- [ ] Every by-id route checks ownership, new admin routes sit under `/api/v1/admin/`, and logs hold no PII.
- [ ] Migrations are new, forward-only and backward-compatible.
- [ ] Frontend calls go through `web/src/lib/api/`, lists have four states, filters live in the URL, and only existing theme tokens are used.
- [ ] Staged paths were explicit, `git status --short` and `git diff --cached --stat` were read, and no commit has an agent co-author trailer.
- [ ] `make ci` passed locally in your own worktree.
