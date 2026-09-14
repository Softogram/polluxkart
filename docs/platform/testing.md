# Testing

Parent: [platform/](README.md) | Index: [docs/](../README.md)

**Status: PROPOSED (2026-09-13).** Written from the plan the owner approved on 2026-09-13. Owner decisions are marked in [decisions.md](decisions.md); everything else here is confirmed or changed in its GitHub ticket before anything is built on it.
The bar a pull request has to clear, and the kinds of test that prove it.

## The rules

1. **`make ci` passes locally before a pull request is opened.** GitHub Actions runs the same checks on every pull request.
2. **A bug fix starts with a failing end-to-end reproduction**, as close as possible to what a shopper or admin actually does. Then the fix makes it pass.
3. **Flaky tests get fixed, not retried.** End-to-end tests run with zero retries in CI, and traces are kept for every failure.
4. **A test that skips itself when its data is missing is a failing test.** The first version's suite passed while testing nothing.
5. **Every new database write has a reachability check:** a real request that causes it, and a test that reads the table back.
6. **Lint failures, test failures and flakiness are fixed even when unrelated to the change at hand.**

## The kinds of test

| Kind | What it proves | Tools | Lives in (planned) |
|---|---|---|---|
| Unit | Pure logic: tax maths, discount allocation, state transitions, financial-year dates, signatures | JUnit 5, AssertJ, injected `Clock` | `api/<service>/src/test/java` |
| Integration | Repositories, controllers and migrations against a real database | Testcontainers PostgreSQL 18 | `api/<service>/src/test/java` |
| Boundary | No service reaches into another's internals; entities never leave a service | Spring Modulith verify, ArchUnit | `api/app/src/test/java` |
| Contract | Every service interface call survives serialization; committed OpenAPI equals generated; frontend types are current; no breaking API change unnoticed | Round-trip test, spec drift test, `oasdiff` | `api/app`, `web/` |
| Authorization | Every admin endpoint refuses customers; no user reads another user's order, invoice or address | Generated sweep, IDOR tests | `api/app/src/test/java` |
| Concurrency | 50 buyers for the last 5 units produce exactly 5 orders; coupon limits hold; invoice numbers have no gaps | Parallel threads against Testcontainers | per service |
| Failure injection | A crash between reserving stock and saving an order leaks nothing; late payment capture after expiry is handled | Injected faults | `api/order`, `api/payment` |
| Webhook | Replaying one event 10 times gives one transition and one email; out-of-order events converge; amount mismatch is flagged | Razorpay documented signature examples | `api/payment` |
| Frontend component | Money formatting, URL filter state, error-code mapping, the four list states | Vitest, Testing Library, MSW with fixtures typed from the API schema | `web/src/**/*.test.tsx` |
| End-to-end | The golden paths on the full stack at phone and desktop sizes | Playwright on Docker Compose with vendor stubs | `e2e/` |
| Accessibility | Zero serious or critical violations on every page; keyboard-only checkout | axe in Playwright | `e2e/` |
| Performance | Budgets below | Lighthouse CI, first-load JavaScript size check | `web/`, `e2e/` |
| Staging nightly | Real Razorpay test mode, SES simulator, security baseline scan, load test | Playwright, OWASP ZAP, k6 | `e2e/nightly/` |

## Golden paths covered end to end

- Browse, add to cart as a guest, sign in, carts merge, check out with cash on delivery, confirmation page, order email.
- Pay with Razorpay (stub in CI, test mode nightly on staging), retry after a dismissed payment.
- Admin packs and ships an order; the shopper's email has a working tracking link; the invoice downloads.
- Register, verify by the emailed link, reset password, old session stops working.
- Sign in with Google through a mock provider.

## Performance budgets (mobile, Lighthouse CI)

- Home, category and product pages: Performance at least 90, SEO 100.
- Largest Contentful Paint at most 2.5 seconds, Cumulative Layout Shift at most 0.1, Total Blocking Time at most 200 ms.
- Storefront first-load JavaScript at most 150 KB compressed.
- API: p95 (the time 95% of requests finish within) under 500 ms for browse and checkout in the nightly load test.

## What `make ci` runs (planned)

- Repository checks: gitleaks, workflow lint, Dockerfile lint, docslint.
- `ci-api`: `./mvnw -B verify` with formatting, all tests, boundary checks, spec drift and vulnerability scan.
- `ci-web`: lint with accessibility rules, type check, formatting, generated type check, Vitest, production build, bundle budget.
- `ci-e2e`: build the Docker Compose stack, then Playwright, axe and Lighthouse CI.

Docker must be running for integration and end-to-end tests.

## Today (2026-09-13)

Only `tools/docslint` exists, with its own unit tests, run by `.github/workflows/docs.yml`.

## See also (do not follow recursively)

- [../design/test/README.md](../design/test/README.md) - per-issue test plans
- [security.md](security.md) - the security rules these tests prove
