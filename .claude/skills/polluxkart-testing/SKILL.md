---
name: polluxkart-testing
description: Use before writing, reviewing, or changing any test in PolluxKart (Java unit, Testcontainers integration, contract, Vitest, Playwright end-to-end, accessibility, Lighthouse budgets), and before starting any bug fix. Covers the six rules, where each kind of test lives, the concurrency, webhook, authorization and crash tests that money and stock require, the traps the first version fell into, and the local `make ci` gate.
---

# Writing tests in PolluxKart

**Status: DRAFT (2026-09-13).**
Written before any application code exists, so every path and command below is the approved plan, not built code.
When the repository disagrees with this skill, the repository wins; fix this skill in the same pull request.

Why each kind of test is required: `docs/platform/testing.md`.
Per-issue test plans: `docs/design/test/issue-<N>-<slug>.md`.
Money, tax and order rules the tests check: the `polluxkart-commerce` skill.

## Words used below

- **Unit test:** checks one piece of logic with no database, no network and no Spring context.
- **Integration test:** runs the real Spring Boot application against a real PostgreSQL database.
- **Testcontainers:** a Java library that starts a throwaway Docker container (here PostgreSQL 18) for a test run, so Docker must be running.
- **End-to-end (E2E) test:** a real browser drives the whole local stack, the way a shopper or admin would.
- **Contract test:** checks that two things which must agree still agree, such as the committed API description and the code.
- **Fixture:** the data a test prepares before it runs.
- **Flaky test:** a test that sometimes passes and sometimes fails with no code change.
- **IDOR (Insecure Direct Object Reference):** changing an id in a request shows or changes someone else's data.
- **Idempotent:** safe to repeat; doing it twice has the same effect as doing it once.
- **Paise:** one hundredth of a rupee; all money is a whole number of paise.

## Tests belong to the ticket (owner rule, 2026-09-13)

A ticket owns its test plan, its test implementation and a verified test run (`polluxkart-workflow`).
The test plan is approved by the owner with the design; the tests ship in the same implementation pull request as the feature, and the approval gate fails a pull request that changes backend or frontend code without tests.
The verified test run is `make ci` passing locally, pasted in that pull request. GitHub Actions does not re-run the checks on every pull request.

## The six rules

1. **A test must prove the expected thing happens**, not that code ran without crashing.
   Assert the order row exists with the right total in paise, not only that the endpoint returned 201.
2. **Every failing test needs a passing partner** that proves the failure is real and not a broken fixture.
   "50 buyers oversell 5 units" is paired with "one buyer buys 1 unit", so a failure points at the race, not at checkout itself.
3. **Never skip.**
   A skipped test reads as a passing test in CI (see "Skips" below).
4. **A test that proves a bug is a success.**
   Keep it; never delete, disable or weaken it to get green.
   This repository has no list of tolerated failures (2026-09-13), and a red test cannot merge, so the test and its fix travel in one pull request.
   The pull request shows the test failing before the fix and passing after, with the output pasted in.
   If the fix cannot happen now, file an issue containing the test and its failing output.
5. **Never test a mechanism that does not exist.**
   Assert behaviour that is wrong, never machinery that is absent.
   "Reset for an unknown email returns a different response than for a known one" is a useful failing test.
   "The reset token expires after 30 minutes", written before tokens exist, fails for a reason nobody can act on.
6. **A comment claiming a guard is not a guard.**
   If a comment, document or skill says a rule is enforced, open the test that enforces it.
   The first version's admin users query removed a field called `password` while the stored field was `password_hash`, so hashes leaked while the code looked safe (`docs/legacy/audit-2026-09.md`, section 1.5).
   **Write the guard in the same change as the sentence, never after.**

## Where each kind of test lives (planned)

| Testing | Location | Tools | Needs Docker |
|---|---|---|---|
| Pure logic: tax, rounding, discount split, state transitions, financial year, signatures | `api/<service>/src/test/java/...` | JUnit 5, AssertJ | no |
| Queries, constraints, controllers, authorization, concurrency, webhooks | `api/<service>/src/test/java/...` | Spring Boot test, Testcontainers PostgreSQL 18 | yes |
| Whole-app guards: migrations from empty, admin sweep, module boundaries, API round trip, spec drift | `api/app/src/test/java/...` | Spring Boot test, Spring Modulith, ArchUnit | yes |
| Components, hooks, API error mapping | `web/src/**/*.test.ts(x)`, next to the code | Vitest, Testing Library, MSW | no |
| Shopper and admin journeys, accessibility, performance budgets | `e2e/` | Playwright, axe, Lighthouse CI | yes |

Whether Testcontainers tests are named `*IT.java` and run by Maven's Failsafe plugin is settled by the scaffold pull request (PR 2.1); follow what it chose.

## Backend unit tests

- **Time comes from an injected `java.time.Clock`.**
  Production code never calls `Instant.now()` or `LocalDate.now()` without it, and tests pass `Clock.fixed(...)`.
- **Test the boundaries that cost money.**
  31 March 23:59:59 IST against 1 April 00:00 IST decides which financial year an invoice number belongs to.
  18:30 UTC is already the next day in India.
- **Tables, not one example:** use `@ParameterizedTest` for tax, with price, GST rate in basis points and same-state flag in, taxable value, CGST, SGST and IGST in paise out.
- **Money assertions are exact:** compare `long` paise with `isEqualTo`, never with a tolerance, never as `double`.
- **Every state transition, legal and illegal:** generate every pair from the order status enum, so adding a status fails the test until someone classifies each new pair.
- **Never wait out a real duration:** advance the clock instead of sleeping.

## Integration tests with Testcontainers

- Migrations run as `pk_migrator` and the app connects as `pk_app`, exactly as in production, so a missing database grant fails here and not on launch day.
- **A test that asserts absence, or an exact count across a whole table, owns its database.**
  On a shared database the answer depends on which tests ran first.
  A count filtered to rows the test itself created is fine on the shared one.
- **Controller tests send a real HTTP request** through the full filter chain (session cookie, CSRF token, rate limit).
  They assert the exact status and the exact Problem Details `code`, the stable error code in our standard JSON error body, and never the message text.
- **Query counts are exact:** count the SQL statements a listing runs, so a loop running one query per product (the "N+1" problem) fails the build.

### Migrations from empty

Create a brand-new database, run every Flyway migration in order, and start the app with Hibernate set to `validate`.
Assert that `pk_app` cannot `UPDATE` or `DELETE` rows in `audit_log`.
Anything production needs after a deploy must be created by a migration, not by a test fixture.

### Admin authorization sweep

Read every route under `/api/v1/admin/**` from Spring's route registry, so a new admin route is covered without anyone remembering to add it.
Call each one with no session (expect 401) and as a verified customer (expect 403).
Assert the route list is not empty and contains one known route, so a broken enumeration cannot pass by testing nothing.

### IDOR tests

Create customers A and B.
B asks for A's order, invoice PDF, address, payment retry, cancellation and review, using A's real ids.
Assert the documented refusal (planned: 404, the same answer as a missing resource, per `polluxkart-error-handling`) and that the body contains none of A's data.
For writes, read A's row back and assert it is unchanged.

### Concurrency

- **50 threads buy the last 5 units and exactly 5 orders exist.**
  The other 45 get the out-of-stock code, and `on_hand - reserved` never goes below zero.
- **Coupon limits:** more redeemers than the limit allows produce exactly the limit in `coupon_redemptions`.
- **Invoice numbers:** concurrent shipments produce contiguous numbers with no gaps and no duplicates, including when one issuing transaction rolls back.
- **Double submit:** two requests with the same `Idempotency-Key` return the same order number and create one order.
- **Stock adjustment against reservation** never breaks the CHECK constraints.

How to make a race test real:

- Hold every thread on a `CountDownLatch` and release them together; otherwise they run one after another and prove nothing.
- Run several rounds with fresh stock and assert the invariant in every round, because one burst is a coin toss.
- Assert both outcomes happened at least once (some succeeded, some were refused), so "nothing happened" never reads as "the limit held".

### Payment webhooks

- Razorpay's documented signature examples pass, and the same body with one byte changed fails.
- The signature is checked over the raw request bytes, so a re-serialized copy of the same JSON must fail.
- **10 concurrent replays of one event produce exactly 1 status transition and 1 email** in `email_outbox`, across several rounds.
- **Out of order:** deliver the webhook before the browser's verify call, then after it, and assert both orderings end in identical rows.
- An amount or currency that differs from `orders.total` is flagged, never confirmed.
- A capture arriving after the reservation expired re-reserves stock or triggers an automatic refund, which the Razorpay stub records.
- A missing webhook secret stops the application context from starting.

### A crash between cross-service steps leaks nothing

Placing an order crosses services: inventory reserves (its own commit), the order saves, a failure releases the reservation, and an expiry job is the safety net.
For every such step, **make the step succeed and the very next step fail**, using a test double of the next service's `api` interface, never a flag in production code.
Then assert four things:

1. `reserved` is back to its earlier value, and no order row or outbox email is left behind.
2. The shopper gets a clean Problem Details error, not a 500 with a stack trace.
3. If the release also fails, advancing the clock past expiry and running the job frees the stock, after checking the Razorpay stub for a late payment.
4. Retrying with the same idempotency key creates one order and one reservation, not two.

## Contract tests

- The committed `api/openapi/openapi.json` equals the spec generated from the running code.
- The generated TypeScript types in `web/src/lib/api/` match that spec.
- `oasdiff`, a tool that compares two API specs, flags breaking changes.
- **Every method on every service `api` interface round-trips through serialization.**
  Find the methods by reflection, serialize sample arguments and results, read them back, and assert equality.
  A method without a sample fails the test, so a new call cannot slip past.
- Generated files are never edited by hand: change the code, then run `make gen-api`.

## Frontend tests (Vitest, Testing Library, MSW)

MSW (Mock Service Worker) intercepts network requests in tests and answers with prepared responses, so components run unchanged.

- **Fixtures are typed from the generated schema**, for example `satisfies components["schemas"]["ProductDetail"]` (the name is illustrative), so an API change stops the fixture compiling.
- **Mock data never lives in app code.**
  The first version's homepage ran on `data/products.js`, full of products that did not exist (audit section 4).
  Fixtures live in test files only.
- **Every list has four states and each gets a test:** loading skeleton, empty, no matches, and error showing the request id.
- **Errors are asserted by Problem Details code**, for example a 409 `price_changed` shows the fresh quote.
- **Filter state lives in the URL:** render with search parameters and assert the filters come back.
- Find elements by role and label, the way a screen reader does, not by CSS class.

## End-to-end tests (Playwright)

- They run against the docker compose stack from `make up`: Caddy, api, web, PostgreSQL, Mailpit (a fake inbox), an S3 mock, a Razorpay stub and a mock Google sign-in server.
- Every journey runs at a mobile size and a desktop size.
- **`retries: 0`, because a flaky test is a bug in the test or the app.**
  Find the cause and fix it; never add retries, `waitForTimeout` or a longer timeout to hide it.
- Use assertions that wait for a condition (`await expect(locator).toBeVisible()`), never fixed sleeps.
- **axe, an automated accessibility checker, runs on every page visited with zero violations of impact serious or critical.**
- Required journeys: cash on delivery checkout, stubbed Razorpay payment, keyboard-only checkout, guest cart merge on login, admin ships an order, invoice download, password reset read from Mailpit, Google sign-in through the mock.
- Each test creates its own user and data through the app, and nothing depends on data another test left behind.
- Each worktree uses its own `COMPOSE_PROJECT_NAME`, so two agents' stacks never share containers or databases.

### Lighthouse CI budgets (mobile)

Performance at least 90, SEO 100, LCP (Largest Contentful Paint: when the biggest element appears) at most 2.5 s, CLS (Cumulative Layout Shift: how much the page jumps while loading) at most 0.1, storefront first-load JavaScript at most 150 KB gzip.
A missed budget is a failing test.
Raising a budget is an owner decision, dated in `docs/platform/decisions.md`.

## The reachability check

A function that writes correctly but that nothing calls passes every unit test, because the test is its only caller.
**For every new database write, name the real request that causes it, send that request in a test, then read the table back.**

## Skips, and the other traps the first version fell into

**A test that skips itself when data is missing is a failing test.**
The first version's suite skipped every admin test when the admin login failed (`legacy/backend/tests/conftest.py`), so the most important checks silently never ran.
If a test cannot run, it must fail loudly; restructure it so it always can.

Banned: `@Disabled`, JUnit `Assumptions`, `@EnabledIf...` and `@DisabledIf...` conditions, `@Testcontainers(disabledWithoutDocker = true)`, `it.skip`, `test.skipIf`, `describe.skip`, `test.fixme`, `it.todo`, and `.only` (which silently skips everything else).
Nothing in `make ci` blocks these yet (2026-09-13).
Adding that check is welcome; until then, run these before every pull request and expect no output:

```
grep -rnE '@Disabled|@(En|Dis)abledIf|Assumptions\.|assume(True|False|That)\(|disabledWithoutDocker' api
grep -rnE '(it|test|describe)\.(skip|skipIf|runIf|todo|fixme|only)\(' web/src e2e
```

The other traps:

- **Tests that need a running server and seeded data**, as in the first version: every test prepares its own state from nothing.
- **Substring search on a JSON body:** decode it and assert on the field you mean.
- **A fixture supplying what production does not.**
  If a fixture inserts the invoice sequence row, the suite is green while the first real invoice fails.
  Ask what each fixture quietly provides.
- **Failure messages that say only `expected 5 but was 6`.**
  Say what it costs: "6 orders for 5 units: one shopper paid for a phone we cannot ship."

## A bug fix starts with a failing end-to-end reproduction

1. Reproduce it the way the shopper or admin hit it: a Playwright test on the compose stack, or at least a real HTTP request through the full application.
2. Run it and watch it fail for the reported reason, then paste that output in the pull request.
3. Add a narrower unit or integration test if it helps locate the fault.
4. Fix the code so both tests pass without changing any other test's assertions.

## Running the checks

```
make doctor      # tools needed today: python3, make, git, gh, actionlint, ShellCheck
make ci          # every check a pull request must pass
make ci-docs     # docs checks only (the docs workflow)
make ci-tooling  # tooling checks only (the tooling-tests workflow)
```

Later, once `api/` and `web/` exist:

```
make up          # local compose stack
make ci-api      # ./mvnw -B verify, Modulith verify, spec drift, osv-scanner
make ci-web      # eslint, tsc, prettier, generated types, Vitest, next build, JS size budget
make ci-e2e      # Playwright, axe, Lighthouse CI on the compose stack
```

The `.githooks/pre-push` hook runs `make ci` when the branch has an open pull request.
It refuses a dirty folder so the checks match what is pushed, and it refuses a direct push to `development` or `main`.
`SKIP_LOCAL_CI=1 git push` skips `make ci` for emergencies; use it deliberately, never by habit, and say so in the pull request.
**If you see a lint error, a failing test or a flaky test your change did not cause, fix it anyway**, or file an issue with the output if the fix is large.

## What a test plan contains

Each `docs/design/test/issue-<N>-<slug>.md` lists every flow and its happy path.
It lists every documented rejection with the exact status and Problem Details code.
It says what the user gets when each dependency (database, Razorpay, SES, S3) fails.
It names the reachability check for each new write.
It says what is deliberately not covered, and why.
A plan with only happy paths is not finished.

## Checklist before you open a pull request

- [ ] `make ci` passed locally, with Docker running, in this branch's own worktree.
- [ ] No skipped, disabled, `.only` or self-skipping test (both greps above print nothing).
- [ ] Every assertion checks the thing that matters: decoded fields, exact paise, exact Problem Details code.
- [ ] Every failing-then-fixed test has a passing partner, and the pull request shows it red before the fix.
- [ ] Time comes from an injected `Clock`, and no test sleeps.
- [ ] Absence and whole-table count tests own their database.
- [ ] Race tests use a start gate, run several rounds, and assert both outcomes happened.
- [ ] New admin routes are covered by the sweep, and new owned resources have an IDOR test.
- [ ] Every new write has a reachability test that reads the table back.
- [ ] Cross-service steps have a "this step succeeds, the next fails" test.
- [ ] OpenAPI spec and TypeScript types are regenerated, not hand-edited, and new `api` methods have round-trip samples.
- [ ] Frontend fixtures are typed from the generated schema, app code has no mock data, and all four list states are tested.
- [ ] E2E runs at mobile and desktop sizes with `retries: 0` and zero serious or critical axe violations.
- [ ] Unrelated lint errors, failures or flakes you saw are fixed or filed.
- [ ] The test plan in `docs/design/test/` exists and is linked from that folder's README.
