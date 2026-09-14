# The road from here to a production-class PolluxKart

Parent: [high-level/](README.md) | Index: [docs/](../../README.md)

**Status: the plan's direction was approved by the owner on 2026-09-13.** Its phases are now GitHub epics and tickets; every ticket's details are confirmed by the owner before implementation ([development-process.md](../../platform/development-process.md)).
Progress is recorded in the "Status" column of each phase, dated.

## Where things stand (2026-09-13)

- The first version is in `legacy/`, merged into `development` in pull request #7.
- `development` is the default branch; `main` is the release branch.
- polluxkart.com is going into maintenance, and the first version's server is being retired.
- No rebuilt code exists yet. This documentation tree and the agent skills are the first deliverables.

## How work is done

- Every task gets its own git worktree, created from a freshly fetched `origin/development`, and is removed after merge.
- Every change is a pull request into `development`, squash-merged, with `make ci` passing locally first and GitHub Actions running on the pull request.
- Changes stage explicit paths only; nobody stashes, hard-resets, rebases or force-pushes shared branches.
- Bug fixes start with a failing end-to-end reproduction.
- Commits carry no agent co-author lines, and written text uses no em dashes.

## Phases at a glance

| Phase | Goal | Status |
|---|---|---|
| 0 | Emergency actions and repository bootstrap | In progress (2026-09-13) |
| 1 | Skills, documentation, design system | In progress (2026-09-13) |
| 2 | Walking skeleton: backend and frontend foundations, local stack, CI | Not started |
| 3 | Staging infrastructure and deploy pipeline | Not started |
| 4 | Feature slices S1 to S9 | Not started |
| 5 | Legal and compliance pages | Writing starts now; pages ship with S2 and S5 |
| 6 | Production environment and hardening | Not started |
| 7 | Launch cutover | Not started |

## Phase 0: emergency actions and repository bootstrap

**Owner actions**
- Set up the new Razorpay merchant account; keep its keys only in a local `.env` and, later, SSM.
- Delete the first version's Firebase project; the rebuild does not use Firebase.
- Rotate any credential that ever appeared in the repository's history.
- Grant a short-lived admin session for the AWS tasks the deploy user cannot perform (IAM review, GuardDuty, a budget alert).
- Gather business inputs later phases wait on: legal entity name, GSTIN, registered address and state, grievance officer and support contacts, return window, warranty handling, shipping fees and cash on delivery policy, a chartered accountant, and a lawyer for the legal pages.

**Agent work**
| Item | Status |
|---|---|
| Move the first version to `legacy/`, remove tracked junk, clean `.gitignore`, write the audit and parity checklist, prepare the maintenance page | Done, pull request #7 merged 2026-09-13 |
| Create `development` and make it the default branch | Done 2026-09-13 |
| Inventory the AWS account and take a safety snapshot of the old server | Done 2026-09-13 |
| Retire the old server, its DNS record and the old website files; publish the maintenance page | Script prepared 2026-09-13, waiting for the owner to run it |
| Repository tooling: `Makefile` with `make ci`, git hooks, repository `CLAUDE.md`, CI workflow, pull request template | Next |

**Exit:** polluxkart.com shows the maintenance page with no third-party builder scripts; `make ci` passes locally and in Actions; a failing pull request cannot merge.

## Phase 1: skills, documentation, design system

| Item | Status |
|---|---|
| This documentation tree, following the owner's documentation structure, with an automatic docs checker | This pull request |
| Agent skills: backend rules rewritten for Spring Boot, frontend and design rules for Next.js and the fixed theme, a commerce skill, and vetted third-party skills | In progress |
| Design system: carry the existing theme into Tailwind v4 tokens, a contrast test, layout mockups in the existing theme for review | After the owner answers the button contrast question |

## Phase 2: walking skeleton

1. **Backend foundation (`api/`).** A one-day spike confirms library versions on Spring Boot 4.1. Then: Maven modules per service with `api` and `internal` packages, shared-kernel and app modules, validated configuration, Flyway with one schema per service and two database roles, Problem Details errors, session cookie security, CSRF, rate limits, JSON logs with request ids, health and readiness, the committed OpenAPI document with a drift test, Testcontainers, boundary and contract tests.
2. **Frontend foundation (`web/`).** Next.js App Router with strict TypeScript, pnpm, Tailwind v4 carrying the existing tokens, the generated API client, route groups for store, auth, account, legal and admin, loading and error screens, sitemap and robots, content security policy.
3. **Local stack and CI.** Docker Compose with Caddy, api, web, PostgreSQL, a fake inbox, an S3 mock, a Razorpay stub and a mock Google sign-in; `make up`, `make ci` and friends; GitHub Actions, CodeQL and Dependabot.

**Exit:** from a clean clone, `make up` shows a Next.js page rendering data fetched from Spring Boot through the generated client, and `make ci` passes.

## Phase 3: staging infrastructure and deploy pipeline

1. Terraform: a bootstrap for state and GitHub OIDC; one module for an environment; staging built from it. See [infrastructure.md](infrastructure.md).
2. Deploy pipeline: images to ECR, deploy through Systems Manager, migrations as a one-shot container, smoke test and automatic rollback; production workflow with manual approval.
3. Owner: request SES production access, create Google OAuth clients, point the Razorpay test webhook at staging.

**Exit:** a merge into `development` is live on staging within 15 minutes, and a deliberately broken image rolls itself back.

## Phase 4: feature slices

Each slice ships its API, migration, pages, tests and documentation together.

| Slice | Delivers | Exit proof |
|---|---|---|
| **S1 Identity and email** | Register, verify, sign in, sign out everywhere, password reset, Google sign-in, admin two-step codes, profile and addresses, the email outbox | Register, verify, reset and old session dies end to end; a disabled user is refused on the next request; every admin route refuses customers |
| **S2 Catalog, media, storefront, SEO** | Admin catalog, image uploads with file checks, listing with filters, search, product pages, compare, structured data, link-preview images, sitemap | An admin-created product appears on the storefront; an HTML file renamed to `.png` is rejected; performance budgets pass |
| **S3 Inventory** | Receipts and adjustments, movement history, low-stock view, availability on product pages | Concurrent adjustment and reservation never break the stock constraints |
| **S4 Cart and wishlist** | Guest cart, merge on sign-in, current prices with change notices, mini cart, wishlist | Guest cart merges on sign-in; a changed price shows a notice |
| **S5 Checkout with cash on delivery** | Pincode directory, delivery estimate, the server quote and tax engine, idempotent order placement, cash on delivery rules, confirmation, order history, cancel before packing | 50 buyers for the last 5 units produce exactly 5 orders; a double submit returns one order |
| **S6 Razorpay** | Payment creation, verification, webhooks, retry, reconciliation and expiry, late capture handling, refunds | Signature examples pass; 10 replays of one event cause one change and one email; an amount mismatch is flagged |
| **S7 Fulfilment** | The order state machine, admin order screens, shipping with courier and tracking, cash collection | Admin ships and the shopper's email has a working tracking link |
| **S8 GST invoices** | Store tax settings, invoices issued at shipping, gapless numbering per financial year, PDFs, credit notes, GSTR-1 export | Rounding and financial-year boundary tests pass; no number gaps under concurrency; **the chartered accountant signs off** |
| **S9 Reviews, coupons, dashboard, data rights** | Verified reviews with moderation, coupons with limits, an honest dashboard, users admin, audit viewer, data export and account deletion | Coupon limits hold under concurrency; deleted accounts keep invoices anonymized |

## Phase 5: legal and compliance

The pages and rules in [../../product/compliance.md](../../product/compliance.md), reviewed by a lawyer, live on staging before Razorpay's website review.

## Phase 6: production environment and hardening

Production built from the same Terraform module; cross-region backup copies; a restore drill; alarms routed to the owner; a security walkthrough against OWASP ASVS Level 2; runbooks for deploys, rollbacks, restores, incidents, and daily shop operations written for the owner's family.

**Exit:** a test alarm reaches the owner's phone, the restore drill passes, and a security baseline scan shows no high findings.

## Phase 7: launch cutover

1. Sign-offs: chartered accountant, lawyer, SES production access, Google OAuth consent screen.
2. Real catalog, pincodes and stock entered; admin two-step codes enrolled; the owner's family trained.
3. Razorpay live keys in SSM and the production webhook configured.
4. DNS time-to-live lowered a day ahead; apex and `www` moved to the production server.
5. Production smoke test: a real cash on delivery order, a live ₹1 payment and refund, the invoice PDF, email authentication passing, WhatsApp link previews.
6. Sitemap submitted to Google Search Console.
7. A pull request deletes `legacy/`; the old CloudFront setup is removed after two stable weeks.

## After launch

Phone OTP after DLT registration, a Shiprocket adapter, a dedicated search engine past about 5,000 SKUs, B2B invoices with buyer GSTIN and e-invoicing when required, self-service returns, back-in-stock and price-drop alerts, WhatsApp notifications, EMI display, guest checkout with fraud checks, a second server behind a load balancer, staff roles, and an accounting export.

## Risks and lead times

- **Business content is the long pole, not code:** product data and photos, HSN codes, and the accountant's and lawyer's reviews.
- **SES production access** can take days or be refused; request it with legal pages live on staging.
- **Razorpay's website review** needs products, rupee prices and the policy pages on the registered domain.
- **Google sign-in branding verification** takes days to weeks.
- **DLT registration** takes weeks, which is why phone OTP comes after launch.
- **Library support for Spring Boot 4.1** is confirmed in the Phase 2 spike.
- **Docker must be running** for integration tests and `make ci`.
- **One server per environment is a single point of failure,** accepted and mitigated by automatic recovery and a rebuild in under 30 minutes.

## See also (do not follow recursively)

- [../../product/launch-scope.md](../../product/launch-scope.md) - the scope contract
- [../../platform/decisions.md](../../platform/decisions.md) - the decisions this plan rests on
