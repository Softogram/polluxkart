# Decisions

Parent: [platform/](README.md) | Index: [docs/](../README.md)

Every product and design choice, and why, written in plain language.
See [glossary.md](glossary.md) for any term you do not recognize.

## How to read this log (owner rule, 2026-09-13)

- **Every entry has a date and a status.** The status is one of:
  - **Owner decision:** the owner chose this. The entry says when and how (for example, answering a question with options).
  - **Proposed:** written into the plan or the docs, but not yet explicitly chosen by the owner. It is confirmed, changed or rejected in its GitHub ticket before anything is built on it.
  - **Superseded:** replaced by a later entry, kept for the record.
- **The latest dated entry on a topic is the one that holds.** When a decision changes, a new dated entry is added and the old one is marked superseded, never deleted.
- **Nothing is assumed.** If a ticket needs a choice that is not recorded here as an owner decision, it becomes an open question for the owner in that ticket. Nobody, person or agent, picks a product or design answer on the owner's behalf.
- **Revised 2026-09-13 (later the same day):** earlier entries in this file were written as flat "Decision" statements. They are now marked "Owner decision" or "Proposed" so it is clear which ones the owner actually chose.

The process that uses this log is in [development-process.md](development-process.md).

---

## Nothing is implemented without the owner's approval (2026-09-13)

**Status: Owner decision, 2026-09-13, stated by the owner, then four setup questions answered the same day.**

- The owner (GitHub `CosmicSaaurabh`) is responsible for every product and design decision. The other 2 to 3 people work only on tickets the owner has approved.
- All work is split into epics, and each epic into tickets. Every ticket is a GitHub issue with its details and links to its design documents.
- Every ticket owns five parts: feature planning, test planning, feature implementation, test implementation, and a verified test run.
- Feature implementation and its tests go in one pull request. Planning and documentation may use separate pull requests.
- Each ticket's design and product decisions are discussed with the owner; nothing is assumed or invented.
- Answers the owner chose on 2026-09-13:
  - **Stages:** six: planning, awaiting approval, implementation ready, in progress, in review, done.
  - **Enforcement:** an automated gate plus the written rule. A check blocks implementation pull requests unless the owner applied the approval label, and a bot removes that label if anyone else applies it.
  - **Board:** a GitHub Project board with a column per stage.
  - **Creation:** every epic and ticket created at once, all starting in planning.

Details: [development-process.md](development-process.md).

---

## Rebuild instead of patching (2026-09-13)

**Status: Owner decision, 2026-09-13, by approving the rebuild plan.**

Rebuild the store from scratch and keep the first version only as reference in `legacy/`.

An audit of the first version found an unauthenticated password reset that could take over any account, admin actions open to every signed-in user, stock that could be sold twice, float money, mock data shown to shoppers, and no tests of any of it.
The full list is in [../legacy/audit-2026-09.md](../legacy/audit-2026-09.md).
The plan's phases are in [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md); approving the plan approved its direction, and each ticket's details are still confirmed before implementation.

---

## Nothing is carried over from the old database (2026-09-13)

**Status: Owner decision, 2026-09-13, answering "Is there real data to carry over?" with "Nothing to keep".**

Start with a clean database and enter the real catalog through admin.

---

## Backend language and framework: Java with Spring Boot (2026-09-13)

**Status: Owner decision, 2026-09-13.** Offered Go, Python FastAPI with PostgreSQL, or FastAPI with MongoDB, the owner asked for Java Spring Boot instead.

## Database: PostgreSQL (2026-09-13)

**Status: Proposed.** The owner chose Spring Boot but did not separately choose the database.
PostgreSQL was proposed because transactions and database constraints (unique emails, stock that cannot go negative, exact integer money) prevent the classes of bugs the first version had.
**Open question for the owner:** confirm PostgreSQL. Tracked in the backend foundation epic.

---

## Versions: the latest Java, Spring Boot and PostgreSQL (2026-09-13)

**Status: Owner decision, 2026-09-13:** "use latest java and springboot and postgresql versions".

## Which "latest": Java 25 LTS, Spring Boot 4.1.x, PostgreSQL 18 (2026-09-13)

**Status: Proposed.**
- **Java 25 LTS** was proposed over Java 26 or 27, which are six-month releases that stop getting fixes after six months. The owner was told this but did not explicitly confirm it.
- **Spring Boot 4.1.x** is the newest release line (4.1.1, 21 August 2026).
- **PostgreSQL 18** is the newest stable version on RDS; 19 is in beta.

**Open question for the owner:** confirm Java 25 LTS, or choose the newest short-term release with an upgrade every six months.
Version sources and upgrade policy: [stack.md](stack.md).

---

## Frontend: Next.js with TypeScript, server-rendered (2026-09-13)

**Status: Owner decision, 2026-09-13, answering the frontend question** (options were Next.js with TypeScript, Vite with React and TypeScript, or keeping Create React App).

Storefront rendered on the server so search engines and WhatsApp link previews see product names, prices and photos; admin in the same app.

---

## Catalog: mainly electronics (2026-09-13)

**Status: Owner decision, 2026-09-13, answering "What does the shop sell?"**

---

## Services are independent, live in one codebase, and run together at launch (2026-09-13)

**Status: Owner decision, 2026-09-13, reached in three messages.**

1. The owner asked whether to follow a microservices architecture while living in one codebase.
2. The owner rejected describing it as a "modular monolith": services must be genuinely independent, called through their interfaces in-process now and replaceable by gRPC calls later.
3. Asked how services should run at launch, the owner chose "run together at launch, split per service later" over separate programs from day one or a few grouped programs.

The rules proposed to make this real are in [../design/high-level/service-boundaries.md](../design/high-level/service-boundaries.md) and are confirmed in their tickets.

## One repository for frontend and backend (2026-09-13)

**Status: Owner decision, 2026-09-13:** the owner stated the services "live in same codebase". `api/` and `web/` share the repository and deploy as two separate images.

## Service dependencies point one way (2026-09-13)

**Status: Proposed** (by Claude, while drafting the backend skills).
A fixed table of which service may depend on which: notification and audit depend on no other service, order orchestrates, payment never calls order.
It avoids module loops that Maven refuses to build and that would stop services moving to their own servers.
Rule 7 in [../design/high-level/service-boundaries.md](../design/high-level/service-boundaries.md).

---

## Sessions: opaque cookies, not JWTs (2026-09-13)

**Status: Proposed.**
A random session token in an httpOnly, Secure, SameSite=Lax cookie; the server stores only its hash and reloads the user on every request, so a disabled user or removed role takes effect immediately.

## Frontend and API on one origin behind Caddy (2026-09-13)

**Status: Proposed.**
Caddy serves `polluxkart.com`, sending `/api/*` to the API and everything else to Next.js, which removes cross-origin setup.

## Data rules live in the database (2026-09-13)

**Status: Proposed.**
One PostgreSQL schema per service owned by Flyway migrations; money as integer paise; timestamps with time zone; UUIDv7 ids; constraints for every invariant.
Details: [../design/high-level/data-model.md](../design/high-level/data-model.md).

---

## Login: email and Google at launch, phone OTP later (2026-09-13)

**Status: Owner decision, 2026-09-13, answering the login question.**

Email and password plus Sign in with Google at launch; phone OTP after DLT registration (the Indian SMS sender registration).
The details (email verification, reset links, admin two-step sign-in) are proposed and confirmed in the identity tickets.

---

## Payments: Razorpay (2026-09-13)

**Status: Owner decision, 2026-09-13:** the owner is setting up a new Razorpay merchant account for the relaunch, and its keys are kept only locally and, on servers, in a secrets store; never in git, documents or chat.

## Cash on delivery (2026-09-13)

**Status: Proposed.** Cash on delivery was in the first version and in the approved plan, but the owner has not explicitly confirmed it or its rules.
**Open question for the owner:** offer cash on delivery at launch, and with which limits.

---

## Shipping: manual at launch (2026-09-13)

**Status: Owner decision, 2026-09-13, answering the shipping question.**

The shop books couriers itself and records courier and tracking number in admin; a provider seam leaves room for Shiprocket later.

---

## GST tax invoices (2026-09-13)

**Status: Owner decision, 2026-09-13:** the shop has a GSTIN and the site should produce GST invoices.

The calculation, numbering and credit-note rules are proposed in [../design/high-level/data-model.md](../design/high-level/data-model.md) and [../product/compliance.md](../product/compliance.md), and need the owner's and a chartered accountant's confirmation.

---

## Hosting: AWS Mumbai (2026-09-13)

**Status: Owner decision, 2026-09-13, answering the hosting question.**

## Hosting details: EC2 with Docker, RDS, S3 and CloudFront, SES, SSM, Terraform, a staging environment (2026-09-13)

**Status: Proposed.** Confirmed in the infrastructure tickets. Details: [../design/high-level/infrastructure.md](../design/high-level/infrastructure.md).

---

## The store's colours, fonts and theme are fixed (2026-09-13)

**Status: Owner decision, 2026-09-13:** "don't change any color or theme of the website, it stays as it is".

The first plan proposed three new visual directions; the owner rejected that.
Several existing colour pairs fail accessibility contrast; which in-palette pairing to use for each is an **open question for the owner** in [../design/high-level/design-system.md](../design/high-level/design-system.md).

---

## Firebase is not used by the store (2026-09-13)

**Status: Proposed.** Sign in with Google can work without Firebase. The owner said they will create a new Firebase project, so whether the store should use it is an **open question for the owner**.

---

## Git workflow (2026-09-13)

**Status: Owner decision, 2026-09-13:** the owner asked for `development` as the default branch; the owner's standing engineering rules require one worktree per task, explicit staging, and no history rewrites.
`main` is the release branch and pull requests are squash-merged.

---

## Documentation follows the ryup structure (2026-09-13)

**Status: Owner decision, 2026-09-13:** "add everything in a document, follow the document structure same like ryup".

---

## Agent skills (2026-09-13)

**Status: Owner decision, 2026-09-13:** the owner asked for the ryup backend and ryup-admin frontend skills plus well-known skills such as ui-ux-pro-max, and asked for the pull request to be merged.

---

## The old server is stopped (2026-09-13)

**Status: Owner decision, 2026-09-13:** "stop the instance". The server was stopped, not terminated. Terminating it, removing its API address and publishing the maintenance page are tracked as tickets.

## Maintenance page content (2026-09-13)

**Status: Proposed.** A static page in the existing theme, without business contact details until they are provided. Source: `ops/maintenance/`.

---

## The first version's open issues are closed (2026-09-13)

**Status: Owner decision, 2026-09-13:** issues #3, #4 and #5, reported against the first version, were closed as not planned; their concerns are carried into rebuild tickets.

## See also (do not follow recursively)

- [stack.md](stack.md) - versions and upgrade policy
- [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md) - the plan these decisions belong to
