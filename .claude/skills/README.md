# Agent skills for PolluxKart

A skill is a folder holding a `SKILL.md` file: instructions an AI coding agent (such as Claude Code) loads before it does a matching kind of task.
Each `SKILL.md` starts with a `description` saying when it applies, and the agent reads the rest when the task matches.
These skills turn the decisions in `docs/` into rules an agent follows while writing and reviewing code.

**Status: added 2026-09-13, before any application code exists.**
Paths under `api/` and `web/` in the skills describe the approved plan.
When code and a skill disagree, the code wins and the skill is fixed in the same pull request.

## Rule one: nothing is implemented without the owner's approval

**Owner rule, 2026-09-13.** Before any work, load [`polluxkart-workflow`](polluxkart-workflow/SKILL.md).
Only tickets the owner labelled `stage: implementation-ready` are implemented, agents never apply that label, and no product or design decision is ever assumed.
It wins over every other skill on process.

## Which source wins

1. The code, once it exists.
2. `docs/`, starting at [`docs/README.md`](../../docs/README.md).
3. A `polluxkart-*` skill (`polluxkart-workflow` first, on process).
4. A vendored third-party skill.

Every vendored skill carries a "PolluxKart override" block at the top listing where it conflicts with PolluxKart's rules.

## PolluxKart skills

| Skill | Use it when | Ported from |
|---|---|---|
| [`polluxkart-workflow`](polluxkart-workflow/SKILL.md) | **Before any work:** checking a ticket's stage, planning, asking and recording owner decisions, opening planning or implementation pull requests | New for PolluxKart (owner rule, 2026-09-13) |
| [`polluxkart-architecture`](polluxkart-architecture/SKILL.md) | Any backend structure: adding a service or class, one service calling another, events, order placement | ryup architecture skill, rewritten for Spring Boot and independent services in one codebase |
| [`polluxkart-postgres-jpa`](polluxkart-postgres-jpa/SKILL.md) | Flyway migrations, JPA entities, repositories, queries, transactions, locking | ryup Postgres skill, rewritten for JPA and PostgreSQL 18 |
| [`polluxkart-http-api`](polluxkart-http-api/SKILL.md) | REST endpoints, filters, sessions, CSRF, pagination, OpenAPI, health checks | ryup HTTP API skill, rewritten for Spring Web MVC |
| [`polluxkart-error-handling`](polluxkart-error-handling/SKILL.md) | Throwing, catching, logging or mapping errors; new error codes; frontend error handling | ryup error handling skill |
| [`polluxkart-security-checklist`](polluxkart-security-checklist/SKILL.md) | Sessions, login, admin routes, by-id reads, uploads, webhooks, prices, secrets, personal data | ryup security checklist |
| [`polluxkart-third-party-integration`](polluxkart-third-party-integration/SKILL.md) | Calling Razorpay, SES, S3, Google sign-in or a future vendor; webhooks; stubs; where keys live | ryup third-party integration skill |
| [`polluxkart-observability`](polluxkart-observability/SKILL.md) | Logging, request ids, health checks, scheduled jobs, alarms, Sentry | ryup observability skill |
| [`polluxkart-testing`](polluxkart-testing/SKILL.md) | Writing or reviewing any test, and before any bug fix | ryup testing skill |
| [`polluxkart-code-review`](polluxkart-code-review/SKILL.md) | Reviewing any change, including your own before a pull request | ryup code review skill |
| [`polluxkart-documentation`](polluxkart-documentation/SKILL.md) | Writing or revising anything under `docs/`, a design, a README or a skill | ryup documentation skill |
| [`polluxkart-frontend`](polluxkart-frontend/SKILL.md) | Any code in `web/`: pages, API calls, rendering and caching, forms, SEO, frontend tests | ryup-admin frontend skill, adapted to the Next.js App Router |
| [`polluxkart-design`](polluxkart-design/SKILL.md) | Any visual markup, Tailwind class, state screen, logo use or UI copy; the theme is fixed | ryup-admin design skill, adapted to the existing PolluxKart theme |
| [`polluxkart-commerce`](polluxkart-commerce/SKILL.md) | Money, GST, discounts, stock, reservations, orders, payments, invoices, consumer rules | New for PolluxKart |

## Vendored third-party skills

Copied at pinned commits after every file was read; sources, licences, vetting notes and local changes are in [`THIRD_PARTY.md`](THIRD_PARTY.md).

| Skill | Use it for | Upstream |
|---|---|---|
| [`ui-ux-pro-max`](ui-ux-pro-max/SKILL.md) | UX guidelines, accessibility, interaction and stack-specific UI patterns. **Never for palette or fonts** | nextlevelbuilder/ui-ux-pro-max-skill |
| [`web-design-guidelines`](web-design-guidelines/SKILL.md) | Reviewing UI code against Vercel's Web Interface Guidelines | vercel-labs/web-interface-guidelines (rules), wrapper written for PolluxKart |
| [`vercel-react-best-practices`](vercel-react-best-practices/SKILL.md) | React and Next.js performance patterns | vercel-labs/agent-skills |
| [`vercel-composition-patterns`](vercel-composition-patterns/SKILL.md) | React component composition | vercel-labs/agent-skills |
| [`spring-data-jpa`](spring-data-jpa/SKILL.md) | Spring Data JPA and Hibernate 7 details | rrezartprebreza/spring-boot-skills |
| [`flyway-migrations`](flyway-migrations/SKILL.md) | Flyway mechanics | rrezartprebreza/spring-boot-skills |
| [`transactional-patterns`](transactional-patterns/SKILL.md) | Spring transaction pitfalls | rrezartprebreza/spring-boot-skills |
| [`problem-details-rfc9457`](problem-details-rfc9457/SKILL.md) | Background on RFC 9457 in Spring | rrezartprebreza/spring-boot-skills |
| [`idempotency-patterns`](idempotency-patterns/SKILL.md) | Idempotency key mechanics | rrezartprebreza/spring-boot-skills |
| [`testing-pyramid`](testing-pyramid/SKILL.md) | Spring Boot test slices and Testcontainers mechanics | rrezartprebreza/spring-boot-skills |
| [`configuration-properties`](configuration-properties/SKILL.md) | Validated `@ConfigurationProperties` | rrezartprebreza/spring-boot-skills |
| [`production-observability`](production-observability/SKILL.md) | Actuator, Micrometer and tracing mechanics | rrezartprebreza/spring-boot-skills |
| [`rest-api-conventions`](rest-api-conventions/SKILL.md) | General REST design background | rrezartprebreza/spring-boot-skills |

Deliberately not vendored: Spring skills for JWT security, OpenAPI-first design and layered architecture, because they contradict PolluxKart's cookie sessions, code-generated OpenAPI and independent service modules.

## Adding or updating a skill

- **A PolluxKart skill:** follow `polluxkart-documentation`. Date its decisions, explain every term, one sentence per line, no em dashes, and end with a pull request checklist.
- **A vendored skill:** copy it at a specific upstream commit, read every file, add a "PolluxKart override" block for any conflict, and record the source, commit, licence and every local change in `THIRD_PARTY.md` in the same pull request.
- Never add a skill that fetches its instructions from a URL at run time.
