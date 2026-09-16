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

**Revised 2026-09-14:** was "pull requests are squash-merged", now pull requests into `development` are squash-merged and release pull requests into `main` use a merge commit, because squashing releases makes `main` and `development` drift apart until old changes reappear and conflict. See "Branch rules for `development` and `main`".

## Branch rules for `development` and `main` (2026-09-14)

**Status: Owner decision, 2026-09-14, answering nine questions while planning E00-06 (#36), including the open question of epic E00 (#10).**

- **Who merges:** contributors may merge pull requests into `development` once the checks pass; only the owner may merge into `main`. Also offered: only the owner everywhere, or any contributor everywhere.
- **Human review:** not required; the required checks must pass. Also offered: one approval from someone other than the author, or that plus code owner review. GitHub never lets an author approve their own pull request, and agents open pull requests under the owner's login.
- **Bypass:** nobody may bypass the rules, the owner included. In an emergency the owner switches a ruleset off in GitHub settings and back on afterwards. Also offered: the owner through pull requests only, or the owner always.
- **Merge methods:** squash into `development`, merge commit into `main`, rebase merging off. Also offered: squash everywhere, or all three methods left on.
- **Up to date:** a pull request must be up to date with its target before merging, on both branches. Also offered: only on `main`, or never.
- **Into `main`:** only from `development`; urgent fixes go through `development` too. Also offered: `development` and `hotfix/*` branches.
- **Releases and the approval gate:** a pull request from this repository's `development` into `main` passes the gate without a ticket line. Also offered: a release ticket per release, or not requiring the gate on `main`.
- **Rules as files:** the rulesets are saved in the repository, applied by a script, and checked for drift. Also offered: a file kept only as a record, or GitHub settings only.
- **Agents and `main`:** agents may merge a release into `main` when the owner asks in the session. Also offered: blocking agents from merging into `main` with the agent guard hook.

Design: [../design/low-level/issue-36-branch-rulesets.md](../design/low-level/issue-36-branch-rulesets.md).

**Revised 2026-09-16:** the required GitHub check on pull requests is only `approval-gate`. See "Local `make ci` is the pull-request gate".

## `make ci` and `make doctor` (2026-09-14)

**Status: Owner decision, 2026-09-14, answering five questions while planning E00-04 (#34).**

- **`make doctor` checks the full planned tool list, but only tools needed today can make it fail.** Tools for later work (Java, Node.js, pnpm, Docker) are shown as information. Also offered: check only today's tools, or check the full list and fail on all of it.
- **When a tool is missing, `make doctor` checks every tool, prints what it found, then fails** if any needed tool is missing or too old. Also offered: stop at the first missing tool, or warn and never fail.
- **`make ci` runs every check even after one fails**, lists all failures at the end, and fails if any failed. Also offered: stop at the first failure, or stop by default with a flag to run everything.
- **GitHub Actions workflow files are linted with actionlint.** Also offered: actionlint plus zizmor, a security-focused workflow checker, or no workflow lint yet.
- **GitHub keeps the separate `docs` and `tooling-tests` workflows**, each running its part of `make ci`, with an automated test proving the two together run everything. Also offered: one `ci` workflow running `make ci`.

**Revised 2026-09-16** by "Local `make ci` is the pull-request gate": the two workflows still exist and still each run one group, but they do not run on every pull request.

Design: [../design/low-level/issue-34-makefile-ci-doctor.md](../design/low-level/issue-34-makefile-ci-doctor.md).

## Commands in CLAUDE.md (2026-09-14)

**Status: Owner decision, 2026-09-14, answering two questions while planning E00-09 (#39).**

- **CLAUDE.md lists only commands that exist today**; each ticket that adds a command adds it to CLAUDE.md in the same pull request, and a check fails on a `make` target that does not exist. Also offered: also listing planned commands, marked as planned.
- **CLAUDE.md keeps only everyday commands, and `make help` is the full list**, generated from the Makefile so it cannot drift. Also offered: every command in CLAUDE.md, or the rest in a separate document.

Design: [../design/low-level/issue-39-claude-md-commands.md](../design/low-level/issue-39-claude-md-commands.md).

## Board sync (2026-09-14)
**Status: Owner decision, 2026-09-14, answering four questions while planning E00-03 (#33).**
- **The sync uses a GitHub App** installed on the organisation, not a personal access token. Also offered: a fine-grained personal token that expires and must be renewed.
- **It works one way: stage labels move cards**, and a card moved by hand goes back at the next sync. Also offered: both ways, which would let a board drag try to set the approval label.
- **A ticket closed as completed gets `stage: done` automatically**, and its card follows; closing as "not planned" changes nothing. Also offered: nothing automatic, the implementer sets it by hand.
- **After the guard removes an approval label someone else applied, the ticket goes back to its last valid stage label.** Also offered: back to planning, or stay put and fail visibly.
This changes one line of the proposed process: `stage: done` is no longer set by hand after merge.
Design: [../design/low-level/issue-33-board-label-sync.md](../design/low-level/issue-33-board-label-sync.md).

## Project board (2026-09-14)
**Status: Owner decision, 2026-09-14, answering five questions while planning E00-02 (#32).**
- **The PolluxKart project board is public**, like the repository and its tickets. Also offered: visible only to organisation members.
- **It keeps the name "PolluxKart".** Also offered: "PolluxKart rebuild".
- **Epics appear in a separate view with their progress**, not on the ticket board. Also offered: epic cards beside tickets, or epics not on the board.
- **Ticket cards show the epic, assignees, linked pull requests and the `owner-action` label.**
- **Only the owner edits the board**; cards move with the stage labels through the sync in #33. Also offered: the owner and contributors.
Design: [../design/low-level/issue-32-project-board.md](../design/low-level/issue-32-project-board.md).

## Dependabot and CodeQL (2026-09-14)
**Status: Owner decision, 2026-09-14, answering seven questions while planning E00-08 (#38).**
- **Only the owner merges Dependabot pull requests.** They still pass the approval gate without a ticket and must pass every required check. Also offered: any contributor once the checks pass.
- **Updates are grouped:** one weekly pull request per ecosystem for minor and patch updates; security fixes arrive on their own. Also offered: one pull request per library.
- **Major updates are skipped for Maven, pnpm and Docker** and left to planned tickets; GitHub Actions majors are still proposed. Also offered: skip majors everywhere, or allow all majors.
- **CodeQL uses advanced setup**, a workflow file reviewed in pull requests, with languages listed explicitly and `legacy/` skipped. Also offered: keep GitHub's default setup.
- **A new high or critical CodeQL security finding blocks merging**; lower findings are reported only. Also offered: block any security finding, or never block.
- **Alerts from `legacy/` are dismissed with a dated reason** ("reference code, never deployed"), and future ones are auto-dismissed where GitHub allows. Also offered: remove the dependency files from `legacy/`, or leave the alerts open.
- **Dependabot security updates are switched on.** Also offered: keep them off and rely on the weekly updates.
Design: [../design/low-level/issue-38-dependabot-codeql.md](../design/low-level/issue-38-dependabot-codeql.md).

**Revised 2026-09-16:** CodeQL does not run on every pull request, so it cannot block merges. Findings from weekly and `main` runs stay in the Security tab. See "Local `make ci` is the pull-request gate".

## Secret scanning (2026-09-14)
**Status: Owner decision, 2026-09-14, answering five questions while planning E00-07 (#37).**
- **The CI secret scan checks every commit in a pull request**, not the whole history each run. GitHub's own secret scanning watches the whole history and alerts the owner privately, so nothing about earlier history is written into this public repository. Also offered: the whole history on every run.
- **A false alarm is allowed by an entry in one allow-list file (`.gitleaks.toml`)**, added by anyone through a pull request, each entry carrying a dated reason that a check enforces; inline allow comments in code are refused. Also offered: only the owner adds entries, or inline comments allowed.
- **The person pushing may bypass a GitHub push protection block by giving a reason**; GitHub records an alert and emails the owner. Also offered: only the owner approves bypass requests, which needs GitHub's paid Secret Protection add-on.
- **Only the owner receives secret scanning alerts.** Also offered: the owner and future maintainers.
- **When a secret must be rotated:** the same day, once it is in any commit (pushed or not), a pushed branch, a document, a chat, a ticket or a log. A key the pre-commit hook blocked before any commit existed is removed, not rotated. Also offered: rotate even when the hook blocked it.
Design: [../design/low-level/issue-37-secret-scanning.md](../design/low-level/issue-37-secret-scanning.md).

**Revised 2026-09-16:** that scan is `make ci` on the laptop (and the pre-push hook), not a GitHub Actions job on the pull request. See "Local `make ci` is the pull-request gate".

## Git hooks (2026-09-14)
**Status: Owner decision, 2026-09-14, answering six questions while planning E00-05 (#35).**
- **The pre-push hook runs `make ci` only when the branch has an open pull request**, so work-in-progress pushes stay fast. Also offered: on every push.
- **If `gh` is missing or GitHub cannot be reached, the push goes ahead with a warning.** Also offered: refuse the push.
- **`SKIP_LOCAL_CI=1 git push` skips `make ci`**, and the hook asks for that to be noted in the pull request. Also offered: the hatch without a reminder, or no hatch.
- **`make doctor` fails on a laptop where the hooks are not enabled**, and shows it only as information on GitHub's machines. Also offered: remind only, or enable the hooks automatically.
- **The pre-commit hook runs the docs checker** until the secret scan joins it in #37. Also offered: no pre-commit hook until #37, or all of `make ci` on every commit.
- **A push that would run `make ci` is refused while the folder has uncommitted or untracked files**, so the checks test exactly what is pushed. Also offered: checking a clean temporary copy of the pushed commit, or checking the folder as it is.
Design: [../design/low-level/issue-35-git-hooks.md](../design/low-level/issue-35-git-hooks.md).

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

**Superseded 2026-09-14** by "Retiring the first version", where the owner confirmed the wording and the missing contact card.

## Retiring the first version (2026-09-14)

**Status: Owner decision, 2026-09-14, answering eight questions while planning E01-01, E01-02 and E01-07 (#40, #41, #46), including both open questions of epic E01 (#11).**

- **E01 tickets follow the ticket process:** a short plan in a planning pull request, the owner's `stage: implementation-ready` label, then the action, with the result recorded on the ticket. Also offered: the owner's go-ahead in the session instead of a planning pull request.
- **The owner runs every step that needs AWS rights**, in the Claude Code session so the output is visible; Claude prepares the steps and verifies the results with read-only checks. Also offered: a short-lived administrator session in which Claude runs the steps while the owner watches.
- **Order:** the whole prepared script runs at once, retiring the server and publishing the maintenance page; the contact card follows when the business details (#45) exist. Also offered: retire the server now and publish the page later, or wait and do both later.
- **The old server is terminated, with nothing copied out first.** Also offered: copy something first, or not yet.
- **The maintenance page keeps its wording**, "We are not taking orders right now. We will be back soon.", with no date. Also offered: adding an expected month.
- **No contact details on the page until #45**, then the full contact card at once. Also offered: one support email address now.
- **The old server's disk snapshot is kept 30 days, until 2026-10-13**, then deleted. Also offered: 90 days, or deleting it straight after termination.
- **A Google Calendar reminder** is set for the deletion date. Also offered: the ticket alone.

Design: [../design/low-level/issue-40-41-46-legacy-teardown.md](../design/low-level/issue-40-41-46-legacy-teardown.md).

## AWS account security review (2026-09-15)

**Status: Owner decision, 2026-09-15, answering five questions while planning E01-03 (#42).**

- **The root account is protected with an authenticator app.** Also offered: a hardware security key now, or an authenticator app now plus a hardware key as a backup in the same review.
- **Nobody besides the owner has an AWS console sign-in.** Family uses the shop admin, not AWS. Also offered: one family member with read-only rights, or another named person.
- **GuardDuty is switched on now,** during this review. Also offered: wait until staging (E06).
- **CloudTrail stays at the free 90-day Event history** until staging is built. Also offered: an S3 trail now.
- **GuardDuty alerts go to the email already used for this AWS account.** The address is recorded only in the private operations reference, never in this repository. Also offered: a different address given in chat.

The owner runs every step that needs AWS rights, as already decided on 2026-09-14 while planning #40, #41 and #46.
Claude prepares the steps and verifies the results with read-only checks.

Design: [../design/low-level/issue-42-aws-security-review.md](../design/low-level/issue-42-aws-security-review.md).

## Local `make ci` is the pull-request gate; GitHub Actions CI runs at release (2026-09-16)

**Status: Owner decision, 2026-09-16.** The owner asked for the same rule already used on Ryup and SpiceCraft (founder rule, 2026-09-04, global across Softogram repos).

- **Every pull request into `development` is gated by local checks**, today's four commands in `CLAUDE.md`, and `make ci` once ticket #34 exists. GitHub Actions does not run those checks on every pull request.
- **GitHub Actions CI (`docs`, `tooling-tests`, and later `make ci` jobs) runs on a push to `main` (a release) and when someone starts the workflow by hand.** Ryup's backend still runs CI on pull requests into `main`; PolluxKart follows SpiceCraft's form (push to `main` plus hand dispatch).
- **The approval-gate workflow still runs on every pull request.** That is the owner-approval rule, not CI.
- **The approval-label-guard workflow still runs when a ticket is labelled.** That is the owner-approval rule, not CI. Its `if:` must be a quoted GitHub expression, because an unquoted `stage: implementation-ready` is invalid YAML (colon then space) and was failing every push with no jobs.
- **CodeQL does not run on every pull request.** It runs on a push to `main`, on a weekly schedule, and by hand, once advanced setup lands in #38. This revises the 2026-09-14 "Dependabot and CodeQL" point that a high or critical finding blocks merging, because that needed a CodeQL run on the pull request.
- **Branch rulesets (#36) require only `approval-gate` on pull requests into `development`.** They do not require `docslint` or `tooling-tests`, which would wait forever if those workflows no longer run on pull requests.

**Why.** GitHub Actions minutes are metered, and this organisation's budget has run out more than once. A lapsed budget fails a job in two seconds with no steps, which looks like a broken build. The local gate already runs the same checks.

This revises "`make ci` and `make doctor`" (2026-09-14), "Branch rules for `development` and `main`" (2026-09-14), and "Dependabot and CodeQL" (2026-09-14).

Design updates: [../design/low-level/issue-34-makefile-ci-doctor.md](../design/low-level/issue-34-makefile-ci-doctor.md), [../design/low-level/issue-35-git-hooks.md](../design/low-level/issue-35-git-hooks.md), [../design/low-level/issue-36-branch-rulesets.md](../design/low-level/issue-36-branch-rulesets.md), [../design/low-level/issue-37-secret-scanning.md](../design/low-level/issue-37-secret-scanning.md), [../design/low-level/issue-38-dependabot-codeql.md](../design/low-level/issue-38-dependabot-codeql.md).

## AWS monthly budget alert (2026-09-16)

**Status: Owner decision, 2026-09-16, answering four questions while planning E01-04 (#43).**

- **The monthly limit now is $10.** Also offered: about $20, about $50, or another amount.
- **The limit is raised when staging is built (#85, E06-03) and again when production is built (#175, E18-01)**, using the estimates in cost.md as a guide. The exact new amounts are chosen in those tickets. Also offered: leave today's amount until production, or never raise it.
- **Emails go out at 80% actual spend, 100% actual spend, and 100% forecasted spend.** A forecast is AWS predicting the rest of the month from use so far. Also offered: 100% actual only, or 80% and 100% actual with no forecast.
- **The recipient is the same email already chosen for GuardDuty**, recorded only in the private operations reference. Also offered: a different address given in chat.

The owner runs every step that needs AWS rights, as already decided on 2026-09-14 while planning #40, #41 and #46.
Claude prepares the steps and verifies the results with read-only checks.

Design: [../design/low-level/issue-43-aws-budget-alert.md](../design/low-level/issue-43-aws-budget-alert.md).

---

## The first version's open issues are closed (2026-09-13)

**Status: Owner decision, 2026-09-13:** issues #3, #4 and #5, reported against the first version, were closed as not planned; their concerns are carried into rebuild tickets.

## See also (do not follow recursively)

- [stack.md](stack.md) - versions and upgrade policy
- [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md) - the plan these decisions belong to
