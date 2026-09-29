# Test plan: E03-02 Maven multi-module skeleton with shared kernel and app modules

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-29)**
Ticket: #56 (E03-02).
Design: [../low-level/issue-56-maven-module-skeleton.md](../low-level/issue-56-maven-module-skeleton.md)

This ticket exposes no request flows and writes no database rows, so the usual shape of a plan does not fit.
What it builds is a shape, and the thing worth testing is that the shape **refuses** what it is supposed to refuse.
So most rows below have a negative half, and the negative half is the point.
Terms such as Maven module, parent POM, shared kernel, application module and named interface are explained at the top of the design.

## Words used below

- **Negative half:** the matching case that must fail. A boundary that cannot refuse anything is decoration.
- **Temporary break:** a change made by hand during the pull request to prove a check fails, then reverted. Its output is pasted into the pull request as evidence.

## How these run

- Java tests are JUnit 5 in the module they belong to, run by `./mvnw -B verify`.
- The build itself is the other half of the coverage: Maven's refusal of a dependency loop is a real check, not a formality.
- Nothing here needs Docker or a database. This ticket creates no tables, so there is nothing to start a container for.
- `make ci` does not run `ci-api` yet. That wiring is E05, so the pull request pastes the `./mvnw -B verify` output instead.

## Flow 1: the build

| Id | Case | Expected | Negative half |
|---|---|---|---|
| B1.1 | `./mvnw -B verify` from a clean clone, with no Maven installed | Every one of the fifteen modules builds | |
| B1.2 | The wrapper is used, not a local Maven | The build works on a machine where `mvn` is absent, which is what the wrapper is for | |
| B1.3 | The parent POM fixes every library version | No module declares a version of its own; a search of the module POMs finds no `<version>` outside the parent | A version added to a module POM is found by the same search |
| B1.4 | Versions match what #55 confirmed | Each library version equals the value recorded in stack.md | |

## Flow 2: the boundaries refuse what they should

This is the heart of the ticket. Each of these is a **temporary break**, run by hand, output pasted into the pull request, then reverted.

| Id | The break | Expected |
|---|---|---|
| D2.1 | Add a Maven dependency from `payment` to `order`, creating a loop with order's existing dependency on payment | `./mvnw -B verify` fails, naming the cycle. This is acceptance criterion 2 |
| D2.2 | Add a dependency from `notification` to `order` | Fails the same way, because order already depends on notification |
| D2.3 | Add a dependency from `catalog` to `review`, which is **not** a loop and **not** in the Rule 7 table | **Builds successfully.** Recorded as a known gap: Maven only refuses loops, and E03-03's Spring Modulith test is what will catch a new edge. Writing this down stops a later reader assuming it was already covered |
| D2.4 | From `cart`, import a class from `com.polluxkart.catalog.internal` | **Compiles today.** Same known gap, closed by E03-03. The pull request says so plainly rather than implying the boundary is already sealed |

D2.3 and D2.4 are the honest part of this plan: two of the four boundary breaks are **not** caught yet, and the ticket that catches them is the next one.

## Flow 3: the application starts

| Id | Case | Expected |
|---|---|---|
| A3.1 | A Spring test starts the context in `app` with every module present | It starts. This is the only behaviour this ticket has |
| A3.2 | The context starts on virtual threads | The setting is on, proving the parent POM's configuration reaches the running program |
| A3.3 | A deliberately broken bean definition | The context fails, proving A3.1 would notice if something were wrong |

## Flow 4: shared-kernel holds only what it should

| Id | Case | Expected | Negative half |
|---|---|---|---|
| S4.1 | `Money` holds a `long` count of paise | Arithmetic stays exact | |
| S4.2 | `Money` refuses a fractional value | Rejected at construction, not rounded silently. Rounding is how money quietly goes missing | A whole number of paise is accepted |
| S4.3 | `Money` refuses a negative amount where the design says it must, and allows it where a refund needs it | Whichever the design fixes, stated once and tested both ways | |
| S4.4 | A typed id cannot be passed where another typed id is expected | It does not compile. Proven by a commented-out line in the test with a note, since a compile failure cannot be asserted at runtime | |
| S4.5 | The public types in shared-kernel | Exactly the four the design lists: `Money`, typed ids, `ErrorCode`, `ServiceException`. A test lists the public types and fails on any extra | Adding a fifth public type fails the test |

S4.5 is what makes question 4 real. Without it, "shared-kernel stays tiny" is an intention rather than a rule.

## Flow 5: the words in the tree

| Id | Case | Expected |
|---|---|---|
| W5.1 | The word "monolith" in any file under `api/`, in the docs, or in this branch's commit messages | Not present. Acceptance criterion 5, and it exists because the owner rejected the term on 2026-09-13; a test is the only thing that keeps a rejected word out of a codebase a year later |
| W5.2 | A module, package or class named `common`, `util` or `helpers` | Not present. These are where boundaries erode, because anything can be argued into them |

## What the contributor gets when something is wrong

| Situation | What they see |
|---|---|
| A dependency loop | Maven names the cycle and the two modules, before any test runs |
| A version declared in a module POM | B1.3 fails, naming the module |
| An extra public type in shared-kernel | S4.5 fails, naming the type, and points at the decisions.md rule |
| The word "monolith" | W5.1 fails, naming the file and line |
| Java older than 25 | Maven refuses at once, because the parent sets the release level |

## Reachability check

No database rows are written by this ticket, so the usual reachability question does not apply.
The equivalent risk is a module that exists but is not really in the build: A3.1 starts the context with every module present, and B1.1 builds all fifteen, so a module that were silently left out of the parent's module list would fail both.

## Concurrency and replay

Nothing here has state, so neither applies.
`./mvnw -B verify` gives the same result run twice.

## What is deliberately not covered, and why

- **Boundary enforcement beyond Maven's loop check.** E03-03. Rows D2.3 and D2.4 record exactly what is still open, so nobody assumes otherwise.
- **Anything inside `internal`.** There is no code there yet.
- **Performance of the build.** Fifteen empty modules; not a question worth asking yet.
- **The wiring seam for moving a service to its own server.** Not built until a service actually moves, by the owner's 2026-09-13 decision.
