# Third-party skills

This file records the Claude Code skills in this folder that were written by other people and copied in (vendored), and every local change made to them.
A skill is a folder of instructions (a `SKILL.md` file plus helper files) that an AI coding agent reads before doing a task.
Because agents follow these files, every file was read and checked before it was copied in.

Every skill folder was byte-identical to the upstream folder at the pinned commit when copied (checked with `diff -r` on 2026-09-13).
The local changes made afterwards are listed in "Local modifications" below; nothing else differs from upstream.
No symlinks are present; every file is a real file.

## Glossary

- **Upstream**: the original GitHub repository a skill was copied from.
- **Pinned commit (SHA)**: the exact version of the upstream repository, named by its git commit hash, so the copy can be checked later.
- **Vendoring**: copying third-party files into your own repository instead of downloading them at run time.
- **Unpinned remote instruction source**: a skill that tells the agent to download fresh instructions from the internet each time it runs, so the instructions can change without anyone reviewing them.
- **Paise**: the smallest unit of the Indian rupee (100 paise = 1 rupee). PolluxKart stores money as a whole number of paise.

## Inventory

| Skill | Upstream repo | Path inside upstream | Commit SHA | Commit date | Licence | Files | Size (bytes) |
|---|---|---|---|---|---|---|---|
| vercel-react-best-practices (upstream folder `react-best-practices`) | https://github.com/vercel-labs/agent-skills | `skills/react-best-practices` | `063bee94c3f4df8453406c830b0a7df0f2860278` | 2026-08-28T15:36:07+02:00 | MIT (declared only; see note) | 76 | 230,383 |
| web-design-guidelines | https://github.com/vercel-labs/agent-skills | `skills/web-design-guidelines` | `063bee94c3f4df8453406c830b0a7df0f2860278` | 2026-08-28T15:36:07+02:00 | MIT (declared only; see note) | 3 | 10,059 |
| (web-design-guidelines/guidelines.md) | https://github.com/vercel-labs/web-interface-guidelines | `command.md` | `e3d624baaf29dc1fc645aff3e38f03e564d2d6b1` | 2026-08-17T17:21:06-07:00 | MIT (LICENSE file present) | (included above) | 7,760 |
| vercel-composition-patterns (upstream folder `composition-patterns`) | https://github.com/vercel-labs/agent-skills | `skills/composition-patterns` | `063bee94c3f4df8453406c830b0a7df0f2860278` | 2026-08-28T15:36:07+02:00 | MIT (declared only; see note) | 14 | 50,339 |
| spring-data-jpa | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/spring-data-jpa` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 6 | 17,816 |
| flyway-migrations | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/flyway-migrations` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 7 | 12,493 |
| transactional-patterns | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/transactional-patterns` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 6 | 15,273 |
| problem-details-rfc9457 | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/problem-details-rfc9457` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 10 | 14,900 |
| idempotency-patterns | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/idempotency-patterns` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 5 | 6,596 |
| testing-pyramid | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/testing-pyramid` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 5 | 8,248 |
| configuration-properties | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/configuration-properties` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 6 | 5,668 |
| production-observability | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/production-observability` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 6 | 5,541 |
| rest-api-conventions | https://github.com/rrezartprebreza/spring-boot-skills | `skills/spring-boot-4/rest-api-conventions` | `c43b0b6b7937f63b7e86ab1e19cc229cdc63ddd8` | 2026-09-07T14:29:13+02:00 | MIT | 8 | 15,458 |
| ui-ux-pro-max | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | `.claude/skills/ui-ux-pro-max` (real-file mirror of `src/ui-ux-pro-max`) | `7f69fed6a2717900085f1bc3b263721f8ba025e2` | 2026-09-10T13:53:40+07:00 | MIT | 74 | 3,573,688 |

File counts and sizes are as copied, before the local modifications below, and include the added `LICENSE` files.

## Local modifications (2026-09-13)

| Skill | Change | Why |
|---|---|---|
| vercel-react-best-practices, vercel-composition-patterns | Folder renamed to match the skill `name` in each `SKILL.md` frontmatter | Claude Code identifies skills by name; a folder that differs from the name is confusing |
| every vendored skill except web-design-guidelines | A "PolluxKart override" block inserted right after the frontmatter of `SKILL.md`, listing the known conflicts below | Agents read `SKILL.md` when a skill triggers, so the override has to be where they read |
| ui-ux-pro-max | `"${CLAUDE_PLUGIN_ROOT}/.claude/` replaced by `".claude/` in 11 script paths in `SKILL.md` | That variable exists only for plugin installs; the paths now work from the repository root |
| ui-ux-pro-max | `scripts/tests/` removed | Those tests walk up parent folders looking for scripts and run them |
| web-design-guidelines | Upstream `SKILL.md` replaced by a PolluxKart-written `SKILL.md` that reads the pinned `guidelines.md` | Upstream `SKILL.md` declared no licence and fetched unpinned remote instructions before every review (see the vetting notes) |

**Licence decision (2026-09-13):** for `vercel-react-best-practices` and `vercel-composition-patterns`, the MIT grant declared in the upstream `README.md` and in each `SKILL.md` frontmatter is accepted as the licence.
The unlicensed upstream `web-design-guidelines/SKILL.md` is not redistributed; only the MIT-licensed `guidelines.md` from `vercel-labs/web-interface-guidelines` is.
Total: 226 skill files, 3,966,462 bytes (about 3.8 MiB); with this file, 227 files and 3,997,262 bytes (4.3 MB on disk).

## Licence notes

- **vercel-labs/agent-skills has no LICENSE file**, and GitHub reports no licence for it.
  It has never had one (checked through the GitHub commits API).
  MIT is declared only in its `README.md` ("## License / MIT") and in the `license: MIT` frontmatter of `react-best-practices/SKILL.md` and `composition-patterns/SKILL.md`.
  `web-design-guidelines/SKILL.md` declares no licence at all.
  No `LICENSE` file was invented for these three folders, because the MIT text needs a copyright line that upstream never published.
  Before publishing, either ask Vercel to add a LICENSE file or accept the README declaration as the licence grant.
- `web-design-guidelines/guidelines-LICENSE` is the MIT licence (Copyright (c) 2025 Vercel Labs) from `vercel-labs/web-interface-guidelines`, and it covers `guidelines.md` only.
- The nine Spring skills and `ui-ux-pro-max` had no licence file of their own, so the upstream repository `LICENSE` was copied in as `LICENSE`.
  Spring: MIT, Copyright (c) 2026 Rrezart Prebreza.
  ui-ux-pro-max: MIT, Copyright (c) 2024 Next Level Builder.

## Vetting notes

Vetting method.
Every `SKILL.md`, `AGENTS.md`, `README.md`, rule, reference, template, example and script was read in full.
Large generated `AGENTS.md` files were checked line by line against their source rule files, and every line not found in a rule file was read.
Large CSV and JSON data files were scanned with search patterns for URLs, shell commands, `curl`, `wget`, `eval`, base64 blobs, prompt-injection phrases, text addressed to an AI, and hidden Unicode control characters.

PolluxKart decisions that override these skills (the project's own skills must win on these):
(a) the existing colours, fonts and theme are fixed;
(b) sessions are opaque httpOnly cookies, not JWT;
(c) the OpenAPI spec is generated from code;
(d) services are independent Maven modules in one codebase;
(e) money is integer paise;
(f) PostgreSQL 18, Java 25, Spring Boot 4.1;
front end is self-hosted Next.js on AWS, not Vercel.

### react-best-practices

Contents: `SKILL.md`, `README.md`, `metadata.json`, `AGENTS.md` (108 KB, generated), `rules/` (70 rules plus `_sections.md`, `_template.md`).
Every rule file, `SKILL.md`, `README.md` and `metadata.json` was read in full.
`AGENTS.md` has 2,764 non-blank lines; the 400 not found verbatim in a rule file are all build scaffolding (header, table of contents, headings, impact lines, reference lines). Checked rule by rule: no line in any rule's section comes from outside that rule's own file, so `AGENTS.md` adds no instructions.
It does drop 31 source lines (the build keeps only the last code block under each label, e.g. `rules/bundle-barrel-imports.md:29-36`), so `rules/*.md` is the more complete source.

What it tells the agent: 70 React and Next.js performance rules in 8 groups (async waterfalls, bundle size, server rendering and caching, client fetching, re-renders, rendering, JavaScript micro-optimisations, advanced hooks), each with an incorrect and a correct example.

- No remote fetch instructions, no WebFetch or curl, no telemetry, no auto-update, no prompt injection, no HTML comments, no hidden Unicode. All URLs are citations (react.dev, nextjs.org, vercel.com, MDN, npmjs.com and similar).
- Install or run steps:
  - `rules/rendering-svg-precision.md:27` `npx svgo --precision=1 --multipass icon.svg` runs an unpinned npm package if an agent executes it. Pin the version or add `svgo` as a dev dependency.
  - `README.md:20-35`, `:105-108`, `:118` describe `pnpm install/build/validate` for upstream's build tooling, which is not vendored. Running them inside the host repo would act on the host `package.json`. Do not run them.
- **Security-relevant examples that conflict with (b) cookie sessions:**
  - `rules/server-after-nonblocking.md:46-48` logs the raw `session-id` cookie value (`logUserAction({ sessionCookie, userAgent })`). That writes a live credential into logs. Never copy.
  - `rules/js-cache-function-results.md:68` detects login with `document.cookie.includes('auth=')`. Client code cannot read an httpOnly cookie, and must not try.
  - `rules/rendering-hydration-no-flicker.md:82` recommends the inline localStorage script for "authentication states". Auth state must come from the server, not localStorage.
  - `rules/advanced-init-once.md:18`, `:35` call `checkAuthToken()` on the client.
  - `rules/async-defer-await.md:63-76` checks resource existence before permission, so 404 versus 403 leaks which resources exist.
  - `rules/server-auth-actions.md:23`, `:49`, `:84` write to the database directly from a Next.js server action, and `:46` returns "unauthorized" for a permission failure (should be 403). In PolluxKart, writes go through the Spring API, which re-checks permission. The `verifySession()` idea itself (lines 33, 38) fits opaque cookies; no JWT appears anywhere.
  - `rules/client-localstorage-schema.md:10`, `:71` correctly say not to store tokens or personal data in localStorage.
- **Vercel-hosting specific (self-hosted Next.js on AWS):**
  - `rules/server-cache-lru.md:37` and `rules/server-hoist-static-io.md:147` rely on Vercel "Fluid Compute" to share an in-process cache. Self-hosted, each Node process or container has its own cache; use Redis (`server-cache-lru.md:39`) when running several tasks.
  - `rules/server-cache-lru.md:17-28` caches user rows for 5 minutes; never use this for roles or permissions.
  - `rules/server-hoist-static-io.md:22-23`, `:47-48` use `fetch(new URL(..., import.meta.url))`, an Edge-runtime pattern; under Node use the `readFileSync` version at `:69-95`.
  - `rules/server-after-nonblocking.md:35-49`, `:70` `after()` works with `next start` or standalone output (long-lived Node process), but work is lost if the container is killed mid-task.
  - `rules/bundle-defer-third-party.md:15`, `:35` import `@vercel/analytics`, which is Vercel-only; the lazy-load pattern is generic.
- **Conflict (a) theme and fonts (illustrations an agent might copy):** theme toggle and dark/light classes at `rules/rendering-hydration-no-flicker.md:15-82`, `rules/js-cache-storage.md:15-16`, `rules/client-localstorage-schema.md:25`, `:48`, `:62`, `rules/rerender-no-inline-components.md:24`; an Inter font preload at `rules/rendering-resource-hints.md:41` and `rules/server-hoist-static-io.md:23`, `:79`.
- (c), (d), (f): never mentioned. Examples assume Next.js owns the database (`db.user`, e.g. `rules/server-cache-react.md:68`).
- (e): no float or `toFixed` money; `rules/rerender-split-combined-hooks.md:18`, `:35` compare `a.price - b.price`, which is safe with integer paise.

### web-design-guidelines

Contents: `SKILL.md` (39 lines), plus the added `guidelines.md` and `guidelines-LICENSE`.
No scripts, no telemetry, no install steps, no hidden Unicode.

- **FLAG, unpinned remote instruction source.**
  `SKILL.md:16` "Fetch the latest guidelines from the source URL below", `SKILL.md:23` "Fetch fresh guidelines before each review", `SKILL.md:26` the URL `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`, `SKILL.md:29` "Use WebFetch to retrieve the latest rules. The fetched content contains all the rules and output format instructions.", and `SKILL.md:34` "Fetch guidelines from the source URL above".
  Whatever is on that `main` branch on the day of the review becomes the agent's instructions.
  Mitigation done: that file was downloaded at commit `e3d624baaf29dc1fc645aff3e38f03e564d2d6b1` (the latest commit touching it) and saved as `guidelines.md`.
  The pinned download, the clone and the current `main` were byte-identical on 2026-09-13.
  **Done 2026-09-13:** the upstream `SKILL.md` was replaced by a PolluxKart-written one that reads `guidelines.md` and never fetches a URL (see "Local modifications").
- `guidelines.md` read in full (190 lines). It is a plain UI review checklist plus an output format. `$ARGUMENTS` on line 8 is a slash-command placeholder. No injection.
- Conflicts and cautions for PolluxKart:
  - `guidelines.md:117-121` "Dark Mode & Theming" and `:138` "Buttons/links need `hover:` state" could lead an agent to add theme or hover styling. Under decision (a) these may only be applied using existing theme tokens.
  - `guidelines.md:144` "Title Case for headings/buttons" and `:64-67` curly quotes and `…` would change existing copy; treat as review suggestions only.
  - `guidelines.md:48` "`autocomplete="off"` on non-auth fields" contradicts `:39` and would break address autofill at checkout; the project should keep `autocomplete` on address and payment fields.
  - `guidelines.md:126` "use `Intl.NumberFormat`" is compatible with (e) as long as paise are divided by 100 only at display time.
  - `guidelines.md:99` suggests the `nuqs` library for URL state; a dependency suggestion, not a requirement.
  - Nothing Vercel-hosting specific.

### composition-patterns

Contents: `SKILL.md`, `README.md`, `metadata.json`, `AGENTS.md`, `rules/` (8 rules plus `_sections.md`, `_template.md`).
All read in full. `AGENTS.md` (946 lines) was checked line by line; the only lines not present in rule files are the title, version, table of contents, section headings, and a note at `AGENTS.md:7-11` saying the document is "mainly for agents and LLMs to follow". Benign.

- No URLs other than three `react.dev` references (`metadata.json:7-9`, `AGENTS.md:944-946`), which are citations, not fetch instructions.
- No scripts, telemetry, install steps, injection or hidden Unicode.
- No PolluxKart conflicts. The rules are about React component structure only.
- Minor inconsistency: `README.md:18` labels Component Architecture "CRITICAL" while `SKILL.md:36` and `rules/_sections.md:10` say "HIGH".
- `rules/react19-no-forwardref.md` applies only on React 19+; the rule itself says so (line 10).
- Nothing Vercel-hosting specific (the name "vercel-composition-patterns" in `SKILL.md:2` is just the skill name).

### Spring Boot 4 skills (all nine)

Common to all nine: each folder has an `agents/openai.yaml` file, which is display metadata for OpenAI Codex (`default_prompt: "Use $<skill> ..."`). Claude Code ignores it. It is harmless.
The `.java`, `.sql` and `.yml` files are illustrative templates and examples, never executed by the skill.
No scripts, no network fetches, no telemetry, no install commands, no prompt injection, no hidden Unicode.
All URLs are documentation citations (docs.spring.io, postgresql.org, rfc-editor.org) or placeholders (`api.example.com`, `orders.example.com`, `otel-collector:4318`).
No JWT, bearer-token or localStorage auth advice appears in these nine skills (the JWT skill upstream was not taken).
Templates use layer-first packages inside one module (`com.example.order.entity`, `.repository`, `.service`, `.config`, `.exception`) plus a shared `com.example.common.*` package; under decision (d) this is fine inside a module, but `common` must not become a shared runtime module that couples services.

#### spring-data-jpa

- **Conflict (e) money:** `SKILL.md:101-134` defines `Money` as `BigDecimal amount` with `precision = 19, scale = 2` plus a currency string. `SKILL.md:64`, `SKILL.md:79` and `examples/good-entity.java:79` use `Money.zero("EUR")`. `SKILL.md:140` exposes `BigDecimal total` in `OrderResponse`.
- Caution (d): `examples/good-entity.java:62-64` maps a `@ManyToOne Account` from `Order`. Across independent service modules, reference other aggregates by ID, not by JPA association.
- Otherwise sound and current for Boot 4 / Hibernate 7 (jakarta imports, LAZY to-one, STRING enums, wrapper `@Version`).

#### flyway-migrations

- **Conflict (e) money:** `SKILL.md:70` `total_amount NUMERIC(12, 2)`; `templates/V1__create_table_template.sql:8` and `:21` `NUMERIC(19, 2)`; `templates/DevDataSeeder.java:34-39` `new BigDecimal("79.99")` etc. PolluxKart should use `BIGINT` paise columns.
- Caution (d): `SKILL.md:30` and `SKILL.md:126` assume one `classpath:db/migration` location. With independent modules, each module should own its own migration location or schema and Flyway history table.
- Caution, security: `SKILL.md:145` seeds `User.createAdmin("admin@dev.local", "password123")` in a `@Profile("dev")` seeder. Never copy this into a shared or deployed environment.
- Caution: `SKILL.md:127` `baseline-on-migrate: true` can silently baseline a wrong or non-empty database. Use only deliberately.
- Inconsistency: `templates/DevDataSeeder.java:33-36` calls `Order.create(String)` and `addItem(..., String, int, BigDecimal)`, which do not match the `Order` API in spring-data-jpa.

#### transactional-patterns

- **Conflict (d):** `SKILL.md:26` `inventoryService.reserve(request.items()); // participates in same TX` assumes inventory writes share the order transaction and database. With independent service modules that is only true if both modules share one datasource; otherwise use the outbox pattern from idempotency-patterns.
- **Bad example to override:** `SKILL.md:163-183` `OrderSaga.execute` is `@Transactional` and calls `inventoryClient.reserve` and `paymentClient.charge` (remote calls) inside the open database transaction. This contradicts the skill's own rule at `SKILL.md:188-189` ("Never fire an external side effect ... inside the transaction") and `idempotency-patterns/SKILL.md:40-42`. `request.total()` at `:173` has an unspecified money type.
- Questionable: `SKILL.md:107` `noRollbackFor = OptimisticLockException.class` (Hibernate marks the transaction rollback-only anyway). `templates/TransactionalOrderService.java:26` says `readOnly = true` lets the "DB use read replicas", which is only true with a routing datasource.
- Caution: `examples/good-transactional-service.java:24` and the template's `OrderEventPublisher` write audit rows with `REQUIRES_NEW`, so an "order created" audit row survives even when the order itself rolls back.
- Dangling link: `SKILL.md:210` `[[domain-driven-design]]` points to a skill that was not vendored.
- Current for Boot 4.1: `@Retryable` / `@EnableResilientMethods` from core Spring Framework 7 (`SKILL.md:131-157`).

#### problem-details-rfc9457

- No PolluxKart conflicts. Good default: `SKILL.md:5` and `:82` say to preserve an existing error contract unless asked to migrate.
- `templates/ProblemDetailExceptionHandler.java:11` imports `org.springframework.security.access.AccessDeniedException`, so the template needs Spring Security on the classpath.
- Placeholder `ERROR_BASE_URI = "https://api.example.com/errors/"` at `templates/ProblemDetailExceptionHandler.java:28` and `examples/good-exception-handler.java:7` must be replaced with a PolluxKart-owned URI. It is never fetched.
- Clash to resolve: this handler and `rest-api-conventions/templates/GlobalExceptionHandler.java` both declare `@RestControllerAdvice` with `@ExceptionHandler(Exception.class)`. Pick one error contract per service.
- `SKILL.md:72` refers to an upstream "repository verification fixture" that was not vendored; harmless.

#### idempotency-patterns

- Minor conflict (f): `SKILL.md:11` "The examples use Java 17". PolluxKart is Java 25.
- `examples/good-idempotency.sql:3` keys on `tenant_id UUID`; PolluxKart should scope keys by customer or session principal instead.
- Good for (b): `SKILL.md:36` says never persist cookies or bearer tokens in replayed responses.
- Otherwise sound; PostgreSQL-specific and consistent with PostgreSQL 18.

#### testing-pyramid

- **Conflict (f):** `SKILL.md:140` `new PostgreSQLContainer<>("postgres:16-alpine")`. Use `postgres:18`.
- **Outdated for Boot 4.1:** `SKILL.md:187-191` adds `org.testcontainers:postgresql`. Spring Boot 4.1.0 manages Testcontainers 2.0.5 (checked in `spring-boot-dependencies-4.1.0.pom`), where the module is `org.testcontainers:testcontainers-postgresql`; the old artifact stops at 1.21.4 and gets no managed version. The generic `PostgreSQLContainer<?>` class at `:139` is the old 1.x API.
- Inconsistency: `SKILL.md:85-86` and `:96-97` assert a `$.success` / `$.error.code` envelope, which contradicts problem-details-rfc9457 error bodies. Follow whichever error contract the service uses.
- `SKILL.md:73`, `:90`, `:200` use `@WithMockUser`, which is compatible with cookie sessions.

#### configuration-properties

- Minor conflict (f): `SKILL.md:11` "The examples use Java 17".
- Otherwise clean. Good security advice: no default credentials (`SKILL.md:22`, `:53`), do not expose `configprops`/`env` actuator endpoints (`SKILL.md:38`).

#### production-observability

- No conflicts. `examples/good-observability.yml:17` and `:22` point OTLP at a placeholder `http://otel-collector:4318`; on AWS this would be an ADOT (AWS Distro for OpenTelemetry) collector or similar.
- Dangling reference: `SKILL.md:6` mentions an `ai-observability` skill that was not vendored.

#### rest-api-conventions

- No hard conflict with (c): `SKILL.md:13` says to inspect existing OpenAPI before choosing a contract, which is compatible with a generated spec.
- The success envelope (`SKILL.md:22-66`, `templates/ApiResponse.java`) is explicitly optional (`SKILL.md:15-16`). Do not introduce it unless PolluxKart already uses it.
- Clash: `templates/GlobalExceptionHandler.java` versus problem-details-rfc9457's handler, as noted above.
- Current for Boot 4: `spring-boot-starter-webmvc` (`SKILL.md:222`), Jackson 3 names (`SKILL.md:223`), native API versioning (`SKILL.md:102-142`).

### ui-ux-pro-max

Upstream version 2.13.0.
Canonical folder: upstream keeps its source of truth in `src/ui-ux-pro-max/` (data and scripts) and mirrors it as real files, not symlinks, into `.claude/skills/ui-ux-pro-max/`, which adds a hand-written `SKILL.md` and `references/`.
`data/` and `scripts/` in the two places were verified identical with `diff -r`, so the `.claude/skills/ui-ux-pro-max/` folder was taken.
The repo contains exactly one symlink (`gallery/data/styles.csv`), outside the skill.

Contents: `SKILL.md`, `references/quick-reference.md`, `references/pro-rules.md`, `scripts/` (5 Python scripts), `scripts/tests/` (13 test files plus fixtures), `data/` (13 CSV, 4 JSON, 22 stack CSVs).

Scripts, read in full:
- `scripts/core.py`: stdlib only (`csv`, `difflib`, `re`, `math`, `pathlib`, `collections`). A BM25 plus regex search over the CSV files. Reads data only; no writes, no environment variables, no network.
- `scripts/search.py`: stdlib (`argparse`, `json`, `sys`, `io`) plus local modules. The CLI entry point. On import it rewraps stdout and stderr as UTF-8 (`:36-39`). Prints to stdout; writes files only with `--design-system --persist`.
- `scripts/design_system.py`: stdlib (`csv`, `json`, `os`, `re`, `sys`, `io`, `tempfile`, `datetime`, `pathlib`). Reads environment variable `COLORTERM` (`:615`) for terminal colour swatches. **Writes files only with `--persist`:** creates `design-system/<slug>/` and `pages/` under `--output-dir`, or the current directory if none is given (`:1013-1029`); writes `MASTER.md` via a temp file and `os.link` (no overwrite) or `os.replace` with `--force` (`:975-992`); `--page` writes `pages/<slug>.md` (`:1053-1056`). Font URLs and `@import` lines are printed as text, never fetched.
- `scripts/reasoning_contract.py`: `json`, `re`. A strict JSON rule parser; runs no code.
- `scripts/validate_data.py`: stdlib plus `urllib.parse` (string parsing only). Read-only data validator; URL literals are allowlists, never fetched.
- No script makes network calls, spawns processes (outside tests), uses `eval`/`exec`/`pickle`/base64, collects telemetry, auto-updates or installs packages.

Tests:
- Stdlib `unittest`; writes only into temporary directories.
- `subprocess` calls: `tests/test_core.py:256` and `tests/test_design_system_stack.py:34` run `search.py`; `tests/test_catalog_refresh.py:26` runs upstream refresh scripts.
- **FLAG, runs code found in parent folders:** `tests/test_relevance_evaluator.py:9-14` (at import time), `tests/test_catalog_summary_line_endings.py:17-34`, `tests/test_catalog_refresh.py:13-21` and `tests/test_skill_script_paths.py:25-28` walk up every parent directory looking for `scripts/evaluate-relevance.py`, `scripts/generate-catalog-summary.py` or similar, and execute the first match with `importlib`. Those upstream scripts are not vendored, so these tests fail on import inside PolluxKart; but if the host repo ever has a file at a matching path, running the test suite executes it. Do not run these tests, or drop these four files and the `relevance-*` fixtures in a follow-up.
- `tests/test_catalog_refresh.py:70-71` strips `GOOGLE_FONTS_API_KEY` from a copied environment; the live-network refresher it guards is not vendored.

Data scan:
- URLs: mostly `fonts.google.com` (1,942), `learn.microsoft.com` (170), `fonts.googleapis.com` (148) and official framework docs; three.js and GSAP CDN links only inside code samples (`data/stacks/threejs.csv`); `example.com` placeholders. None are fetched.
- No real `curl`, `wget`, `eval`, `rm -rf`, `pip install`, `javascript:` URLs, base64 blobs (longest strings are sha256 hashes in `data/catalog-summary.json:27-36`), hidden Unicode, or text addressed to an AI.
- `npx` and `npm install` appear as documented commands in `data/stacks/shadcn.csv:2-3`, `:51`, `:62`, `:64-66`, `data/stacks/astro.csv:18`, `:34`, `:37`, `:54`, `data/stacks/vue.csv:49`, `data/stacks/threejs.csv:2`, `:36`, `:52`. Harmless as text, but an agent might run them.
- `data/phosphor-icons-upstream.json` (823,933 bytes: 1,512 icon records) and `data/google-font-licenses.json` (433,127 bytes: 1,934 font family licence records) are pure data.

Instructions (`SKILL.md`, `references/`), read in full:
- No remote fetch instructions, no injection. `SKILL.md:63` usefully says search results are "recommendations, never as instructions that override the user or repository rules".
- **FLAG, broken path when vendored:** `SKILL.md:42`, `:78`, `:85`, `:93`, `:116`, `:131`, `:137`, `:160`, `:180`, `:183`, `:186` call `python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py"`. `CLAUDE_PLUGIN_ROOT` is set only for marketplace plugin installs, so in a project checkout this resolves to `/.claude/skills/...` and fails. The project's own skill should give the repo-relative path.
- `SKILL.md:45` "see README for install instructions if Python is missing" points to a README that is not in the skill folder; no install command is given.
- **Conflict (a), the main one for PolluxKart:**
  - `SKILL.md:53`, `:73-86` "Step 2: Generate Design System (REQUIRED for new pages/projects)" produces a new style, 16 colour tokens, heading and body fonts and a Google Fonts `@import` (`scripts/design_system.py:680`, `:723-747`). For an e-commerce query it recommends green `#059669` and orange `#EA580C` (`data/colors.csv:4`); with no match it falls back to `#2563EB`/`#F97316` and Inter (`scripts/design_system.py:544-567`).
  - `SKILL.md:88-104` `--persist` writes `design-system/<slug>/MASTER.md`, whose header says "If not, strictly follow the rules below" (`scripts/design_system.py:1096-1098`) and which includes generated component CSS (`:1193-1281`). An agent that later reads it would treat a generated palette as the source of truth.
  - `SKILL.md:111-127` design dials, `SKILL.md:189` "synthesize the design system ... and implement", `SKILL.md:204` "Can't decide on style/color: Re-run `--design-system`", `SKILL.md:146` individual Google Fonts lookup.
  - `references/quick-reference.md:79` `style-match`, `:82` `color-palette-from-product`, `:83` `effects-match-style`, `:87` `dark-mode-pairing`, `:118` `font-pairing`, `:81` Heroicons/Lucide icon choice.
  - `references/pro-rules.md:73`, `:96` require testing both light and dark themes, which assumes a dark theme exists. The file is scoped to native and mobile apps (`:3-5`).
  - Safe to use for PolluxKart: plain `--domain ux`, `--domain web`, `--domain chart` and `--stack nextjs` searches (read-only), and the accessibility, forms, touch and layout rules in `references/quick-reference.md` sections 1, 2, 3, 5, 8 and 9.
- **Vercel-hosting specific:** `data/stacks/nextjs.csv:49` "Use Vercel for easiest deploy", with "Self-host without knowledge" as the thing not to do and "Complex Docker setup" as the bad example; this contradicts self-hosting on AWS. `data/react-performance.csv:9` uses `@vercel/analytics`. `data/stacks/nextjs.csv:35` suggests an "Edge-compatible auth check". `data/stacks/nextjs.csv:12` ISR `revalidate` works self-hosted but needs a shared cache handler across several instances.
- (b): no JWT or localStorage token advice; localStorage appears only for theme preference.
- (e): no float money handling, but `data/styles.csv:37` uses `--currency-symbol: $` with 2 decimal places and `data/icons.csv:50` offers only a dollar icon.

#### Difference from the local copy at `/Users/saurabhmishra/softogram/softogram/.claude/skills/ui-ux-pro-max`

The local copy is an older, locally modified release, not the pinned upstream.
- Its `SKILL.md` (693 lines) advertises 67 styles and 161 palettes (upstream now 79 and 192), has sections in Chinese, mentions a "shadcn/ui MCP" integration, and includes OS install commands for Python (`brew install python3`, `sudo apt install python3`, `winget install`) around lines 308-328. Its git blob matches none of the last 12 upstream versions of the file.
- Only in local: `data/_sync_all.py` (a maintenance script that rewrites `colors.csv` and `ui-reasoning.csv` in place; stdlib only, no network), `data/design.csv` and `data/draft.csv` (Chinese design notes marked as not read by the engine), `scripts/__pycache__/` (Python 3.14 bytecode from a local run).
- Only in upstream: `references/`, `scripts/reasoning_contract.py`, `scripts/validate_data.py`, `scripts/tests/`, `data/catalog-summary.json`, `data/data-provenance.json`, `data/google-font-licenses.json`, `data/phosphor-icons-upstream.json`.
- Every shared file differs: `SKILL.md`, `scripts/core.py` (274 lines local vs 993 upstream), `scripts/search.py` (127 vs 177), `scripts/design_system.py` (1,329 vs 1,643), and all 13 top-level and 22 stack CSV files.
