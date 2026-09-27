# Test plan: E03-01 Confirm the database and versions, and spike library compatibility with Spring Boot 4.1

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-27)**
Ticket: #55 (E03-01).
Design: [../low-level/issue-55-backend-versions-spike.md](../low-level/issue-55-backend-versions-spike.md)

This ticket exposes no request flows, so the usual shape of a plan does not fit it.
It is a spike: a throwaway experiment whose output is an answer, not a feature.
So this plan is a checklist of proofs, and every one of them is written to be able to fail.
Terms such as spike, BOM, unmanaged library, Jackson 3, Testcontainers and UUIDv7 are explained at the top of the design.

## Words used below

- **Proof:** one small test that shows a library really works, rather than merely downloading.
- **Negative half:** the matching case that must fail. A check that cannot fail proves nothing, so most proofs here have two halves.
- **Throwaway:** the spike project is deleted when the ticket closes. These tests are not kept; the ones marked "carries over" are rewritten as real tests in E03-02.

## How these run

- All of them run inside the throwaway Maven project at `spike/boot41-compat/`, which is git-ignored and never merged.
- They run against **PostgreSQL 18 in Testcontainers**, not a substitute, so Docker must be running.
- They run on the Java and Spring Boot versions the owner confirms in question 2 and question 3. If those answers change, the whole checklist is re-run; results from an unconfirmed version are not recorded.
- The result of each row is recorded as pass or fail with the version tested and the date, in `docs/platform/stack.md`.
- `make ci` does not run any of this. The spike is not part of the build.

## Flow 1: the platform itself

| Id | Proof | Expected | Negative half |
|---|---|---|---|
| V1.1 | The project builds and the Spring context starts | Context loads on the confirmed Boot version | A deliberately bad bean definition fails the context, proving the test would notice |
| V1.2 | The running JVM is the confirmed Java version | Version matches exactly | |
| V1.3 | Testcontainers starts PostgreSQL 18 and the app connects | A query returns a row | |
| V1.4 | `select uuidv7()` works, and two ids generated a second apart sort in time order | Both true | A random UUIDv4 pair does not reliably sort, which is the reason for the choice |
| V1.5 | `citext` and `pg_trgm` install on the container image | Both extensions create | |
| V1.6 | Flyway runs one migration against the container | Schema history table shows it applied once | Running twice does not apply it again |

## Flow 2: each unmanaged library

These are the six libraries Spring Boot does not manage, which is why they are the risk.
Every row must name the exact version tested.

| Id | Library | Proof | Negative half |
|---|---|---|---|
| L2.1 | springdoc-openapi | A request to the OpenAPI path returns a document describing one test endpoint | The document actually contains that endpoint's path, not just an empty shell |
| L2.2 | Spring Modulith, boundaries | A boundary test passes for legal code | A module reaching into another module's internals fails the test |
| L2.3 | Spring Modulith, events | One event is published and recorded complete in the database | An event whose listener throws is left incomplete, not silently lost |
| L2.4 | ArchUnit | A rule that should hold passes | A deliberately broken rule fails, naming the class |
| L2.5 | ShedLock | Two simultaneous scheduled runs compete | Exactly one takes the lock; the other does not run |
| L2.6 | Bucket4j core, behind our own filter, not the third-party starter (see question 5) | Requests under the limit succeed | The request over the limit is refused with 429 |
| L2.7 | OpenHTMLtoPDF | One HTML page renders to a PDF of at least one page | The rendered PDF contains a visible Indian rupee sign, which is where font embedding usually fails |

## Flow 3: the Jackson 3 move

Spring Boot 4 moves to Jackson 3, and that is the most likely cause of a library failing in a way that looks like something else.

| Id | Proof | Expected |
|---|---|---|
| J3.1 | A record holding a `BigDecimal` and an `Instant` survives a round trip to JSON and back | Values identical, and the `BigDecimal` keeps its scale |
| J3.2 | Money is serialised as an integer number of paise, not a floating point number | No `.0` or exponent appears in the JSON |
| J3.3 | The dependency tree is checked for Jackson 2 | springdoc is the one expected source, through Swagger's core library, and that is accepted. **Any other library pulling in `com.fasterxml.jackson` counts as failing**, per the design's edge case table |
| J3.4 | The OpenAPI document and the error responses both serialise through Jackson 3 | Both produce valid JSON |

## Flow 4: all of them together

| Id | Proof | Why |
|---|---|---|
| T4.1 | One project with every library present starts and passes every check above | Two libraries can each work alone and still conflict. Testing them separately would miss it |
| T4.2 | `mvn dependency:tree` has no version conflict warnings for the libraries under test | A silently downgraded transitive dependency is the failure that shows up months later |

## What is recorded, pass or fail

The point of the spike is the written record, so a failure is as much of a result as a pass.

For every row: the library, the exact version, pass or fail, and the date.
For every failure, additionally: what the error was, whether a pre-release exists, whether a replacement exists, and which of the owner's ranked options from question 5 applies.

The owner is told before anything is chosen. The spike reports; it does not decide.

## What carries over into E03-02

These are rewritten as real tests when the Maven modules are built, so the spike's value outlives its code:

- V1.3, V1.6: Testcontainers and Flyway, which become the base of every integration test.
- L2.2, L2.4: the boundary and architecture tests, which are ticket E03-03.
- J3.1, J3.2: money and time serialisation, which become the contract round-trip harness in E03-04.
- V1.4, V1.5: the id and extension checks, which move into the first migration in E03-06.

L2.1, L2.3, L2.5, L2.6 and L2.7 belong to their own later tickets (E03-12, E03-02, the scheduled jobs ticket, E03-11 and E15-03), and each rewrites its own proof there.

## What is deliberately not covered, and why

- **Performance of any library.** Not a day-one question, and a spike is the wrong instrument.
- **Whether the libraries are the right choices.** That was settled in stack.md. This ticket asks only whether they work on Boot 4.1.
- **Anything in `api/`.** No product code exists yet, by design.
- **Windows or Linux developer machines.** The spike runs on the one machine that exists. A note goes in stack.md if that ever stops being true.
- **The upgrade path from Boot 4.1 to 4.2.** There is no 4.2 to test against.
