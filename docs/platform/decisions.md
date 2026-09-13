# Decisions

Parent: [platform/](README.md) | Index: [docs/](../README.md)

Every important choice, and why, written in plain language.
See [glossary.md](glossary.md) for any term you do not recognize.
Dates are when the decision was made, so this file doubles as a timeline.
When a decision changes, the old one stays here, marked superseded, with the reason.

---

## Rebuild instead of patching (2026-09-13)

**Decision: rebuild the store from scratch; keep the first version only as reference in `legacy/`.**

An audit of the first version found an unauthenticated password reset that could take over any account, admin actions open to every signed-in user, stock that could be sold twice, float money, mock data shown to shoppers, and no tests of any of it.
Almost every backend service needed rewriting, and the frontend was built on a deprecated tool.
Patching would have kept the structure that produced those problems.

The full list is in [../legacy/audit-2026-09.md](../legacy/audit-2026-09.md).
`legacy/` is deleted in the launch pull request once [../legacy/parity-checklist.md](../legacy/parity-checklist.md) is fully ticked.

---

## Nothing is carried over from the old database (2026-09-13)

**Decision: start with a clean database and enter the real catalog through admin.**

The owner confirmed the old database held only test data.
No migration script is needed, and the new schema is designed without compromises for old data.

---

## Backend: Java and Spring Boot, with PostgreSQL (2026-09-13)

**Decision: Java with Spring Boot, on PostgreSQL.**

### The options compared

1. Keep Python FastAPI with MongoDB and fix it in place.
2. Python FastAPI with PostgreSQL.
3. Go with PostgreSQL, matching the owner's other backend project.
4. Java with Spring Boot and PostgreSQL. **Chosen by the owner.**

### Why

- A store is about money and stock, where transactions and database constraints prevent whole classes of bugs. PostgreSQL enforces unique emails, stock that never goes negative and exact money as integers.
- Spring Boot's transactions, security, validation and data access are mature and well documented, which suits a store meant to run for years.
- MongoDB was rejected because rules like "stock cannot go below zero" would live only in application code, which is exactly where the first version's bugs came from.

### Trade-off

The owner's other projects' backend skills are written for Go, so they were rewritten for Spring Boot rather than copied.

---

## Latest versions: Java 25 LTS, Spring Boot 4.1, PostgreSQL 18 (2026-09-13)

**Decision: use the latest versions, choosing long-term support where "latest" and "supported" differ.**

The owner asked for the latest Java, Spring Boot and PostgreSQL.
- **Java 25 LTS** rather than Java 26 or 27: those are six-month releases that would force a Java upgrade twice a year. The owner was told this and the plan records Java 25.
- **Spring Boot 4.1.1**, the newest release.
- **PostgreSQL 18**, the newest stable release on RDS; 19 is still in beta.

Upgrade rules are in [stack.md](stack.md).

---

## Frontend: Next.js with TypeScript, server-rendered (2026-09-13)

**Decision: Next.js App Router with TypeScript; storefront rendered on the server; admin inside the same app.**

### The options compared

1. Keep Create React App and fix it in place. It is officially deprecated.
2. Vite with React and TypeScript, a single-page app like the owner's admin project.
3. Next.js with TypeScript. **Chosen.**

### Why

A shopper's WhatsApp link preview and a Google result both need the product's name, price and photo in the page's HTML.
A single-page app builds pages in the browser, so link previews show nothing useful.
Server rendering fixes that and makes the first load faster on phones.

---

## Services are independent, live in one codebase, and run together at launch (2026-09-13)

**Decision: a microservices design kept in one repository; all services run in one process at launch; any service can later move to its own server by switching to a gRPC client.**

### How the decision was reached

The owner asked whether the backend should follow a microservices architecture while living in one codebase.
The first proposal described this as a "modular monolith"; **the owner rejected that framing (2026-09-13)**: the services must be genuinely independent, callable through their interfaces in-process now and replaceable by gRPC calls later.
The owner was then asked how the services should run at launch, and chose:

1. **Run together at launch, split per service later. Chosen.**
2. Separate programs from day one: about thirteen Java processes, a bigger server, network failures between services from the start.
3. A few grouped programs from day one.

### What independence means in practice

Each service has its own Maven module, its own interface of plain data records, its own database schema, and no access to any other service's internals or tables.
Calls between services are designed as if they were already remote: batched, idempotent, and never sharing a database transaction.
Tests fail the build if any of this is broken.
The full rules are in [../design/high-level/service-boundaries.md](../design/high-level/service-boundaries.md).

### The honest trade-off

An order and its stock reservation cannot be saved in one transaction, because inventory commits on its own.
Order placement therefore works in steps with a compensating release and automatic reservation expiry.
The no-oversell guarantee is unchanged, because the stock check is one atomic update inside inventory, and a test injects a crash between steps to prove nothing leaks.

---

## One repository for frontend and backend (2026-09-13)

**Decision: `api/` and `web/` live in one repository and deploy as two separate images.**

The frontend's typed client is generated from the backend's OpenAPI document.
In one repository, a single pull request changes an endpoint, the page using it, and the test covering both, at one commit.
Split repositories would need versioned clients and matched versions for every end-to-end run.
Revisit if a separate team owns one side or a second client such as a mobile app appears.

---

## Sessions are opaque cookies, not JWTs (2026-09-13)

**Decision: a random session token in an httpOnly, Secure, SameSite=Lax cookie; the server stores only its hash and reloads the user on every request.**

The first version stored a JWT in the browser's localStorage, where any script on the page could read it, and trusted the role inside it for 24 hours.
With an opaque cookie, disabling a user or removing an admin role takes effect on the next request, and page scripts cannot read the token.
One indexed database lookup per request costs nothing at this scale.

---

## Frontend and API share one origin behind Caddy (2026-09-13)

**Decision: Caddy serves `polluxkart.com`, sending `/api/*` to the API and everything else to Next.js.**

No cross-origin (CORS) configuration exists to get wrong, the session cookie stays first-party, and Caddy renews HTTPS certificates automatically.

---

## Data rules live in the database (2026-09-13)

**Decision: one PostgreSQL schema per service, owned by Flyway migrations; money as integer paise; timestamps with time zone; UUIDv7 ids; constraints for every invariant.**

The first version stored money as floating-point numbers, mixed text and real dates, and had no unique indexes.
Details: [../design/high-level/data-model.md](../design/high-level/data-model.md).

---

## Service dependencies point one way (2026-09-13)

**Decision: a fixed table of which service may depend on which; notification and audit depend on nothing; order orchestrates; payment never calls order.**

While drafting the backend skills, two loops appeared.
The payment expiry job needed inventory to know order state while order already called inventory.
And if notification listened to order's events while order called identity and identity called notification, the three modules would depend on each other in a circle, which Maven refuses to build and which would stop any of them moving to its own server.

The fix keeps every service independent:
- notification and audit are called by others from after-commit listeners, and never listen to other services.
- order calls inventory, payment, cart, shipping and invoice, and listens to payment's events.
- Browser endpoints for paying an order belong to order; Razorpay's webhook belongs to payment.
- The payment expiry job runs in order; inventory keeps a sweeper for reservations that never got an order.

The table lives in [../design/high-level/service-boundaries.md](../design/high-level/service-boundaries.md) as Rule 7.

---

## Login: email and Google at launch, phone OTP later (2026-09-13)

**Decision: email and password with email verification and secure reset, plus Sign in with Google; phone OTP after launch.**

Phone OTP is what Indian shoppers expect most, but sending SMS in India requires DLT registration first, which takes weeks.
The data model keeps a place for phone sign-in so adding it later needs no redesign.

---

## Payments: Razorpay and cash on delivery (2026-09-13)

**Decision: Razorpay for online payment and cash on delivery with rules against abuse.**

**Revised 2026-09-13:** the relaunch uses a new Razorpay merchant account.
Its keys are kept only in a local, git-ignored `.env` for development and in AWS SSM Parameter Store for the server.
They are never committed, pasted into documents, or shared.

---

## Shipping: manual at launch (2026-09-13)

**Decision: the shop books couriers itself; admin records courier and tracking number; a provider interface leaves room for Shiprocket.**

---

## GST invoices from day one (2026-09-13)

**Decision: the shop has a GSTIN, so every shipped order gets a GST tax invoice with HSN codes and the CGST, SGST or IGST split, numbered without gaps per financial year.**

A chartered accountant signs off the invoice before launch.
Details: [../product/compliance.md](../product/compliance.md).

---

## Hosting: AWS Mumbai, staging and production, Terraform (2026-09-13)

**Decision: Docker containers on one EC2 server per environment, RDS PostgreSQL, S3 and CloudFront for images, SES for email, secrets in SSM, all defined in Terraform.**

The store already ran on AWS in Mumbai.
A managed platform would cost more per month and usually runs in Singapore rather than India.
Details: [../design/high-level/infrastructure.md](../design/high-level/infrastructure.md).

---

## The store's colours, fonts and theme are fixed (2026-09-13)

**Decision: carry the existing theme over unchanged.**

The first plan proposed three new visual directions.
**The owner rejected that (2026-09-13): no colour or theme changes; the website stays as it is.**
Design work covers layout, usability, accessibility and speed only.
One open question needs the owner's answer before buttons are built: white text on the teal primary colour fails the accessibility contrast minimum, and the in-palette fix is the theme's own dark text on teal.
Details: [../design/high-level/design-system.md](../design/high-level/design-system.md).

---

## Firebase is not used (2026-09-13)

**Decision: the rebuild does not use Firebase.**

Sign in with Google uses a Google Cloud OAuth client directly, and phone OTP will use an Indian SMS provider after DLT registration.
The owner may create a new Firebase project for other purposes; nothing in the store depends on it.

---

## Git workflow (2026-09-13)

**Decision: `development` is the default branch and the base for every pull request; `main` is the release branch; pull requests are squash-merged; every task is done in its own git worktree.**

- The repository is public, so GitHub Actions runs on every pull request; there is no cost reason to restrict it.
- `make ci` runs the same checks locally before a pull request is opened.
- Staging deploys from `development`; production deploys from `main` after approval.
- `development` was created from `main` and made the default branch on 2026-09-13.

---

## Maintenance page during the rebuild (2026-09-13)

**Decision: polluxkart.com shows a static maintenance page in the existing theme until relaunch, and the old backend server is retired.**

The page has no scripts and asks search engines not to index it.
It ships without business contact details until they are confirmed.
Source and upload steps: `ops/maintenance/README.md`.

---

## Agent skills (2026-09-13)

**Decision: the repository carries Claude Code skills in `.claude/skills/`.**

- Backend rules ported from the owner's Go project and rewritten for Spring Boot.
- Frontend and design rules ported from the owner's admin project and adapted to Next.js and the fixed theme.
- A new commerce skill for money, GST, stock and orders.
- Well-known third-party skills vendored at pinned commits after every file was read: ui-ux-pro-max, Vercel's React and web design guidelines, and selected Spring Boot skills.
- When a PolluxKart skill and a vendored skill disagree, the PolluxKart skill wins.

## See also (do not follow recursively)

- [stack.md](stack.md) - versions and upgrade policy
- [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md) - the plan these decisions belong to
