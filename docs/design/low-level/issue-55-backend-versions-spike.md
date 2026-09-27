# E03-01 Confirm the database and versions, and spike library compatibility with Spring Boot 4.1

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-27)**
Ticket: #55 (E03-01), part of epic #13.
Test plan: [../test/issue-55-backend-versions-spike.md](../test/issue-55-backend-versions-spike.md)
Depends on: nothing. This is the first backend ticket, and the other eleven tickets in E03 rest on its answers.

## Words used below

- **Spike:** a short, throwaway experiment whose only job is to answer a question. Its code is deleted afterwards and never becomes part of the product.
- **LTS (long-term support):** a release that keeps getting security fixes for years. A non-LTS release stops getting them after six months.
- **BOM (bill of materials):** a list of library versions that are known to work together. Spring Boot ships one, so a project that uses it does not pick those versions itself.
- **Managed by Boot:** a library whose version comes from Spring Boot's BOM. Upgrading Boot upgrades it, and the two are tested together.
- **Unmanaged library:** one Spring Boot does not list, so the project picks the version and carries the risk that it does not work with Boot.
- **Jackson:** the library that turns Java objects into JSON and back. Spring Boot 4 moves to Jackson 3, whose package names changed, which is why a library built for Jackson 2 may fail.
- **Testcontainers:** a test library that starts a real database in a container for the duration of a test, so tests run against PostgreSQL rather than a substitute.
- **UUIDv7:** a kind of unique id that sorts by the time it was created, which keeps database indexes tidy compared with a fully random id.
- **RDS:** Amazon's managed database service, where the store's PostgreSQL will run.
- **Transitive dependency:** a library pulled in by another library rather than asked for directly.

## What was already decided before this document

- **The backend is Java with Spring Boot** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Backend language and framework").
- **Use the latest Java, Spring Boot and PostgreSQL** (owner decision, 2026-09-13, "Versions: the latest Java, Spring Boot and PostgreSQL"). "Latest" is exactly what this ticket pins down, because latest can mean the newest LTS or the newest release of any kind, and those differ today.
- **Services are independent, live in one codebase, and run together at launch** (owner decision, 2026-09-13).
- **Nothing is carried over from the old database** (owner decision, 2026-09-13). So there is no migration constraint on the database choice.
- **PostgreSQL is only Proposed**, not decided ([decisions.md](../../platform/decisions.md), "Database: PostgreSQL"). The owner chose the framework but never the database.

## The problem

Every later backend ticket hard-codes these versions into build files, migrations and tests.
Changing them after E03-02 has built the Maven modules means touching every module again, so the cheap moment to be wrong is now.

Two things make this more than a formality.

**Spring Boot 4 is a new major line.**
It moves to Spring Framework 7, Spring Security 7 and Jackson 3.
Libraries that Spring Boot does not manage itself have to catch up on their own schedule, and six of the libraries this plan depends on are unmanaged: springdoc-openapi, ArchUnit, ShedLock, Bucket4j, OpenHTMLtoPDF and Spring Modulith.
If one of them has no Boot 4 release, the plan needs a different answer before any code is written, not after.

**"The latest" has moved since the stack document was written on 2026-09-13.**
Checked again on 2026-09-27:

| Thing | State today | What it means here |
|---|---|---|
| Java 27 | Released 15 September 2026 | It is newer than Java 25, but it is a six-month release, not an LTS. Choosing it means upgrading Java twice a year forever. |
| Java 25 | The current LTS, released September 2025 | The next LTS is Java 29, expected September 2027. |
| Spring Boot 4.1.1 | Released 20 August 2026, the current line | 4.1.0 was 10 June 2026. 4.2 is not out. |
| PostgreSQL 19 | Beta 4, released 24 September 2026 | Not released. General availability is expected in October 2026, and AWS RDS support has historically followed a couple of months later. |
| PostgreSQL 18 | Current stable, on RDS | Also the version that added native UUIDv7 generation. |

So the honest recommendation today is Java 25 LTS, Spring Boot 4.1.x and PostgreSQL 18, and the questions below ask the owner to confirm exactly that, with the trade-offs stated rather than hidden.

### What is already known, before the spike runs

A desk check of every library was done on 2026-09-27, reading the published build files rather than blog posts.
It does not replace the spike, because "the build file says Boot 4.1" is not the same as "it starts and works".
It does tell us where to expect trouble, and it found one item that needs an owner decision before implementation starts.

| Library | Position today |
|---|---|
| Spring Modulith 2.1.1 | Ready. Its own build targets Boot 4.1.1. Stay on 2.1.x: the 2.2 line has already moved to Boot 4.2 milestones |
| ShedLock 7.10.1 | Ready. Its build pins Spring 7.0.9 and Boot 4.1.1 |
| ArchUnit 1.5.1 | Ready, and unaffected: it reads compiled classes and depends on nothing but a logging interface |
| springdoc-openapi 3.1.1 | Works, with a caveat below. Use 3.1.1, not 3.1.0, which is missing security fixes |
| Testcontainers 2.0.5 | Ready, managed by Boot's own version list |
| Flyway | Take Boot's managed version, not the newest. Boot 4.1.1 manages 12.4.0 while Flyway has released 13.8.0 |
| OpenHTMLtoPDF 1.1.87 | Ready, and its build tests on Java 25 |
| Thymeleaf 3.1.5 | Works through the older Spring 6 integration jar. There is no Spring 7 jar yet |
| **Bucket4j Spring Boot starter** | **Not ready.** See the risk below |

**The one real problem: rate limiting.**
Bucket4j itself is healthy, but the *Spring Boot starter* around it is a separate third-party project.
Its newest release is built against Boot 4.0.3, not 4.1, and it carries an untriaged bug reported against Boot 4.0 saying rate limiting does not work.
A fix has been merged to its main branch but not released, with no date given.
This is ticket E03-11's problem, but it is cheaper to settle it here: the spike should test **Bucket4j's core library behind a small filter we write ourselves**, which has no Spring coupling and is actively released, rather than the starter.
Question 5 below asks the owner to confirm that.

**Three coordinate traps**, which would look like version problems but are not.
Each of these names in stack.md now points at an abandoned artifact, and the spike must use the replacement:

| Named in stack.md | What it actually gets | Use instead |
|---|---|---|
| `com.openhtmltopdf` | Version 1.0.10, last released 2021 | `io.github.openhtmltopdf` |
| `com.bucket4j:bucket4j-core` | Version 8.10.1, last released 2024 | `com.bucket4j:bucket4j_jdk17-core` |
| `org.testcontainers:postgresql` | A 1.x jar sitting next to the 2.x core | `org.testcontainers:testcontainers-postgresql` |

And one silent failure worth naming, because it produces no error at all: on Boot 4, depending on `flyway-core` alone starts the application and runs **no migrations**.
The spike must use `spring-boot-starter-flyway` with `flyway-database-postgresql`, and test V1.6 exists to catch exactly this.

**Two Jackson caveats** to expect rather than be surprised by.
springdoc pulls Jackson 2 in through Swagger's core library for generating the document, so a Boot 4 app has both Jackson versions present; the springdoc maintainers say this is expected and works.
That matters for Thymeleaf, which in its current jar prefers Jackson 2 when both are present, so JavaScript inlining of dates can misbehave.
The spike records whether either actually bites, and test J3.3 is written knowing springdoc is the expected source.

## The change

This ticket produces answers and a written record. It produces no product code.

### Part 1: the owner's answers

The six questions at the end of this document are answered and recorded as dated "Owner decision" entries in [decisions.md](../../platform/decisions.md).
The "Database: PostgreSQL" entry stops saying Proposed.
Nothing in part 2 starts before these are answered, because the spike has to be built against the chosen versions.

### Part 2: the spike

A throwaway Maven project at `spike/boot41-compat/`, **git-ignored and never merged**, built on the confirmed versions.
It is deleted when the ticket closes; what survives is the version table and this document's results section.
`spike/` is added to `.gitignore` by the implementation pull request, because a planning pull request may change Markdown files only.

For each library, the spike does the smallest thing that proves the library actually starts and works, rather than merely resolving as a dependency:

| Library | What the spike proves | Why that specific thing |
|---|---|---|
| springdoc-openapi | A running app serves an OpenAPI document describing one endpoint | Boot 4 changed the web stack internals springdoc reads |
| Spring Modulith | A boundary test fails when one module reaches into another's internals, and passes when it does not | A test that cannot fail is worthless, so both directions are checked |
| Spring Modulith events | One event is published and marked complete in the database | Durable events are what order placement later relies on |
| ArchUnit | One rule passes and one deliberately broken rule fails | Same reason: prove it can fail |
| ShedLock | Two scheduled runs compete and only one takes the lock | The lock is the whole point |
| Bucket4j | A request over the limit is refused with 429 | |
| OpenHTMLtoPDF | One HTML page with an Indian rupee sign renders to a PDF | The rupee sign needs font embedding, which is the usual failure |
| Testcontainers | The whole suite runs against PostgreSQL 18 in a container | |
| Flyway | One migration runs on that container | |
| Jackson 3 | A record with a `BigDecimal` and an `Instant` survives a round trip | Money and time are where JSON changes bite |

Two database checks ride along, because they are cheap and both are assumed by later tickets:

- `uuidv7()` exists and generates sortable ids.
- The `citext` and `pg_trgm` extensions install on the container image, for case-insensitive emails and fuzzy product search.

### Part 3: the record

- `docs/platform/stack.md` gains a version table: each library, the confirmed version, and the date checked.
- Anything that failed is written down with what failed and the owner's chosen way forward, rather than quietly dropped.
- The test plan says which of these checks become real tests in E03-02, so the spike's value is not thrown away with its code.

### How a failure is handled

The spike's job includes failing usefully. If a library has no Boot 4 release, the design does not pick the answer; it reports and asks.
The owner's answer to question 5 sets the order of preference in advance, so the spike does not stall waiting for a decision per library.
The four options, with what each costs:

| Option | Cost |
|---|---|
| Wait for the library | Blocks E03 for an unknown time |
| Use its pre-release version | Works now, but a pre-release can change without warning and may not be fixed quickly |
| Replace it with another library | Rewrites that one area, and the replacement needs its own check |
| Use Spring Boot 3.x for now | Everything works today, but the upgrade to 4 comes back later and touches everything |

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A library works but only through a transitive Jackson 2 dependency | Counts as a failure, because two Jackson versions on one classpath is the exact problem Boot 4 creates. The spike records it as such. |
| A library resolves but its Boot starter does not exist yet | Counts as a failure. Wiring it by hand is a maintenance cost later tickets should not inherit silently. |
| PostgreSQL 19 reaches general availability during this ticket | Does not change the answer. Question 4 already says 19 waits for RDS support and a passing restore drill. |
| Docker is not running | The spike cannot run at all; Testcontainers needs it. `make doctor` already reports Docker as needed later. |
| A library passes on Java 25 but not Java 27, or the reverse | Only the confirmed Java version is tested. This is a reason to answer question 2 before the spike, not after. |
| The spike passes but a version is later found broken in real use | The version table records the date checked, so the next reader knows how old the evidence is. |
| Two libraries each work alone but conflict together | The spike is one project with all of them present, so a conflict shows up rather than hiding. |

## What is deliberately not covered

- **The real Maven module layout**, which is E03-02. The spike is one flat throwaway project on purpose.
- **Any product code.** Nothing in `api/` is created by this ticket.
- **Frontend and Node.js versions**, which are E04-01.
- **The PDF invoice template**, which is E15-03. The spike renders one throwaway page only.
- **Performance.** Whether a library is fast enough is not a day-one question.

## Open questions for the owner

These are the ticket's questions, restated with what is true on 2026-09-27 so the choice is informed.

1. **Do you confirm PostgreSQL as the store's database?**
It was proposed after you chose Spring Boot, but you have never chosen the database itself.
Recommendation: yes. Money, stock and unique emails all need transactions and database-level rules, and those are the bugs the first version had.

2. **Which Java: 25 LTS, or the newest release?**
Java 27 arrived on 15 September 2026, so this is a live choice rather than a hypothetical.
Recommendation: Java 25 LTS. A six-month release means a forced upgrade twice a year on a shop run by one engineer, and the newer language features are not what this project is short of.

3. **Do you confirm Spring Boot 4.1.x now, moving to 4.2 once its first patch is out?**
Recommendation: yes. 4.1.1 is current, and waiting for a 4.2 that is not released would block everything.

4. **Do you confirm PostgreSQL 18 now?**
PostgreSQL 19 is at Beta 4 and is expected to be released in October 2026, but RDS support usually follows months later.
Recommendation: yes, 18 now, and 19 only once it is released, available on RDS, and a restore drill has passed on staging.

5. **If a library does not work with Spring Boot 4.1, what should the spike do?**
Please rank the four options in the table above, so the spike can act without stopping to ask each time.
Recommendation: replace, then pre-release, then wait, and treat dropping to Spring Boot 3 as a last resort that needs a fresh conversation.

**One case is already live, so it needs an answer rather than a ranking.**
The Bucket4j Spring Boot starter has no Boot 4.1 release and an untriaged bug against Boot 4.0.
Do you agree the spike should use Bucket4j's core library behind a filter we write ourselves, roughly sixty lines, instead of the starter?
Recommendation: yes.
It removes an unmaintained project from the critical path, and the alternative that does target Boot 4, Resilience4j, only limits within one process, which would stop being enough the moment a second server is added (E20-10).

6. **Do you accept the upgrade policy in stack.md?**
It is: patch releases within a month, a new Spring Boot minor line once its first patch is out, Java only between LTS releases, and PostgreSQL majors only after RDS support and a passing restore drill.
Recommendation: yes, unchanged.
