# Technology stack

Parent: [platform/](README.md) | Index: [docs/](../README.md)

**Status: PROPOSED (2026-09-13).** Written from the plan the owner approved on 2026-09-13. Owner decisions are marked in [decisions.md](decisions.md); everything else here is confirmed or changed in its GitHub ticket before anything is built on it.
Versions were checked against official release information on 2026-09-13.
The owner decided on Spring Boot, Next.js with TypeScript, AWS Mumbai and the latest versions; the database and the exact versions below are proposals.

## Backend

| Piece | Choice | Version | Why |
|---|---|---|---|
| Language | Java | **25 LTS** | The newest long-term support (LTS) release. Java 26 (March 2026) and 27 (due 15 September 2026) are short-term releases that stop getting security fixes after six months. The next LTS is Java 29, expected September 2027. |
| Framework | Spring Boot | **4.1.x** (4.1.1 released 21 August 2026) | The current supported line, with Spring Framework 7 and Spring Security 7. Transactions, security and data access are mature and well documented. Move to 4.2 when it is released. |
| Build | Maven | 3.9.x with the Maven wrapper | Boring and readable, and it refuses circular dependencies between modules, which enforces service independence. |
| Web layer | Spring Web MVC | from Boot | Plain request-per-thread code is easier to read and debug than reactive code, and Java's virtual threads handle concurrency. |
| Data access | Spring Data JPA with Hibernate | from Boot | Standard, with `ddl-auto=validate` so the database schema is owned by migrations, not by Hibernate. |
| Migrations | Flyway | from Boot | Versioned SQL files per service schema, run once before the app starts. |
| Module boundaries | Spring Modulith, ArchUnit | versions confirmed in the Phase 2 spike | Tests that fail the build when one service reaches into another's internals, plus durable in-process events. |
| API documentation | springdoc-openapi | Boot 4 compatible line | Generates the OpenAPI document from code. |
| Rate limiting | Bucket4j | Boot 4 compatible line | In-memory limits for one instance. |
| Scheduled jobs | Spring `@Scheduled` with ShedLock | Boot 4 compatible line | A database lock keeps a job from running twice if a second instance is ever added. |
| PDF invoices | Thymeleaf templates with OpenHTMLtoPDF | confirmed in the Phase 2 spike | HTML templates an accountant can review, rendered to PDF on the server. |
| Tests | JUnit 5, Testcontainers, AssertJ | from Boot | Integration tests run against a real PostgreSQL in a container. |

**Phase 2 starts with a one-day spike** to confirm the exact versions of springdoc, Spring Modulith, ShedLock, Bucket4j, OpenHTMLtoPDF and Testcontainers that work with Spring Boot 4.1 and Jackson 3.
The confirmed versions get recorded here and in [decisions.md](decisions.md).

## Database

| Piece | Choice | Version | Why |
|---|---|---|---|
| Database | PostgreSQL | **18** | The newest stable major version, supported on AWS RDS. PostgreSQL 19 is in beta as of 2026-09-13; move to it once it is released and available on RDS. PostgreSQL 18 also generates UUIDv7 ids natively. |
| Hosting | AWS RDS | PostgreSQL 18 | Managed backups, point-in-time restore and patching. |
| Extensions | `citext`, `pg_trgm` | bundled | Case-insensitive emails; fuzzy product search. |

## Frontend

| Piece | Choice | Why |
|---|---|---|
| Framework | Next.js (latest stable, App Router) | Server-side rendering for fast product pages, search engines and WhatsApp link previews. |
| Language | TypeScript, strict mode | The code states the shape of its data, so mistakes show up before running. |
| Package manager | pnpm, lockfile committed | Fast, strict, reproducible installs. |
| Runtime | Node.js 24 LTS | Long-term supported. |
| Styling | Tailwind CSS v4 | Carries the existing theme tokens unchanged. |
| Components | shadcn/ui on Radix, only the ones used | Accessible building blocks already familiar from the first version. |
| Data and forms | openapi-fetch, TanStack Query and Table (admin), react-hook-form, zod | A typed client generated from the API, and forms that show server errors on the right field. |
| Tests | Vitest, Testing Library, MSW, Playwright, axe, Lighthouse CI | Unit, component, end-to-end, accessibility and performance checks. |

## Infrastructure and vendors

| Piece | Choice | Why |
|---|---|---|
| Cloud | AWS, Mumbai region (`ap-south-1`) | Already in use, close to shoppers. |
| Compute | EC2 Graviton with Docker Compose | One server per environment is enough at launch; auto-recovery and a scripted rebuild cover failure. |
| Reverse proxy | Caddy | Automatic HTTPS certificates and a short readable config. |
| Infrastructure as code | Terraform | Staging and production built from one definition, rebuildable in minutes. |
| Images | S3 behind CloudFront | Cheap storage, fast delivery. |
| Email | AWS SES | Transactional email at very low cost. |
| Secrets | AWS SSM Parameter Store | Encrypted, readable only by the server, never in git. |
| Payments | Razorpay | Indian cards, UPI, net banking; plus cash on delivery handled by the store. |
| Sign-in | Google OAuth client | Sign in with Google without Firebase. |
| Error monitoring | Sentry (free tier), personal data sending off | Errors with context, without shopper data. |
| Analytics | Google Search Console at launch; Plausible optional | No cookie banner needed; business numbers come from our own database. |
| CI | `make ci` locally before every pull request; GitHub Actions at release (push to `main`) and on hand dispatch | The same checks locally and on GitHub. GitHub does not re-run them on every pull request. |

## Upgrade policy

- Patch releases of Spring Boot, PostgreSQL minor versions and Next.js are applied within a month, through Dependabot pull requests.
- A new Spring Boot minor line (such as 4.2) is adopted once its first patch release is out.
- Java moves only between LTS releases.
- PostgreSQL moves a major version once RDS supports it and a restore drill passes on staging.

## Sources for the version checks (2026-09-13)

- Spring Boot 4.1.1 release: https://endoflife.date/spring-boot
- Amazon RDS supports PostgreSQL 18: https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-rds-postgresql-major-version-18
- PostgreSQL 19 Beta 3 in the RDS preview environment: https://aws.amazon.com/about-aws/whats-new/2026/08/postgresql-19-beta-3-amazon-rds-database-preview-environment/
- JDK 27 release date: https://www.infoq.com/news/2026/08/java-27-so-far/

## See also (do not follow recursively)

- [decisions.md](decisions.md) - the reasoning behind each choice, dated
- [../design/high-level/infrastructure.md](../design/high-level/infrastructure.md) - how the infrastructure pieces fit
