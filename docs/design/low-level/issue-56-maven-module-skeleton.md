# E03-02 Maven multi-module skeleton with shared kernel and app modules

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-29)**
Ticket: #56 (E03-02), part of epic #13.
Test plan: [../test/issue-56-maven-module-skeleton.md](../test/issue-56-maven-module-skeleton.md)
Depends on: #55 (E03-01), which confirms the versions this build declares. The skeleton cannot be built before the spike says those versions work.

## Words used below

- **Maven module:** one separately built part of a Java project, with its own folder and its own list of what it depends on.
- **Parent POM:** the one file at the top that names every module and fixes the version of every library, so no module picks its own.
- **Maven wrapper (`mvnw`):** a small script committed to the repository that downloads the right Maven version, so everyone builds with the same one without installing it.
- **Shared kernel:** a tiny module every service is allowed to use. It holds only types that mean the same thing everywhere, such as money.
- **`package-info.java`:** a file that carries information about a whole Java package. Here it declares which other modules this one is allowed to use.
- **Application module:** Spring Modulith's name for one service inside the build, and the thing whose boundary can be checked by a test.
- **Named interface:** the part of a module other modules may use. Everything else is private to it, even though Java would technically allow access.
- **Wire-safe contract:** a type built so it can later be sent over a network without changing its shape, so moving a service out does not rewrite its callers.
- **Constructor injection:** giving a class what it needs through its constructor, rather than letting a framework fill in fields. It makes what a class depends on impossible to hide.
- **Virtual threads:** a Java feature that lets a server handle many waiting requests cheaply, so plain request-per-thread code scales without reactive programming.

## What was already decided before this document

- **Services are genuinely independent, called through their interfaces in-process now and replaceable by a network call later** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md)). The owner rejected calling this a "modular monolith" and chose to run every service together at launch.
- **Frontend and backend share one repository and deploy as two images** (owner decision, 2026-09-13).
- **The backend is Java with Spring Boot** (owner decision, 2026-09-13).
- **Java 25 LTS, Spring Boot 4.1.x, PostgreSQL 18, and the library fallback order** (owner decision, 2026-09-27, while planning #55).
- **Dependencies point one way**, the Rule 7 table in [service-boundaries.md](../high-level/service-boundaries.md). That entry is still marked Proposed in decisions.md, which is why question 2 below asks for it.

## The problem

The owner's decision that services are independent is, today, only a sentence in a document.
Nothing stops the first feature ticket putting an order class inside the catalog service, or having payment call order.

Two things make the shape worth fixing before any feature exists.

**A dependency loop cannot be undone cheaply.**
Maven refuses to build a loop between modules, which is the mechanism that keeps services honest.
But that only helps if the direction is right from the start.
Once payment depends on order, removing it means moving code, not editing a line.

**Every later ticket needs an obvious place to put its code.**
Without the shape, thirteen feature tickets each invent their own, and the boundaries exist only in review comments.

This ticket builds the empty shape. It contains no business rules, no endpoints and no tables.

## The change

### The module list

Fifteen modules: thirteen services, plus `shared-kernel` and `app`.

```
api/
  pom.xml              the parent: module list and every library version
  mvnw, mvnw.cmd       the Maven wrapper
  shared-kernel/       Money, typed ids, ErrorCode, ServiceException. Nothing else
  identity/  catalog/  media/  inventory/  cart/  order/  payment/
  invoice/  shipping/  promotion/  review/  notification/  audit/
  app/                 the one program that wires every service together
```

Each service module has the same inside:

```
<service>/
  pom.xml
  src/main/java/com/polluxkart/<service>/
    package-info.java        @ApplicationModule(allowedDependencies = {...})
    api/                     what other services may use
      package-info.java      @NamedInterface("api")
    internal/                everything else, which nobody outside may touch
  src/test/java/...
```

`internal` is where entities, repositories, logic and controllers go in later tickets.
Nothing is created inside it here beyond the folder, because this ticket builds no behaviour.

### Who may depend on whom

Straight from the Rule 7 table, expressed twice: once as a Maven dependency and once in `package-info.java`.
Maven refuses a loop, and Spring Modulith's test in E03-03 refuses a reach into another module's `internal`.

| Module | Maven dependencies |
|---|---|
| shared-kernel | nothing |
| notification, audit | shared-kernel |
| media, inventory, shipping | shared-kernel, audit |
| identity, payment, invoice | shared-kernel, notification, audit |
| catalog | shared-kernel, media, audit |
| promotion | shared-kernel, catalog, audit |
| cart | shared-kernel, identity, catalog, inventory |
| order | shared-kernel, and identity, catalog, inventory, cart, promotion, payment, shipping, invoice, notification, audit |
| review | shared-kernel, order, catalog, notification, audit |
| app | every service, for wiring only |

Writing it in both places is deliberate rather than duplication.
Maven stops a loop at build time; the declaration in `package-info.java` is what a person reads, and what E03-03's test checks against.

### What goes in shared-kernel, and nothing else

Every service depends on it, so anything inside it couples all thirteen together.

| Type | Why it is shared |
|---|---|
| `Money` | A `long` count of paise, one hundredth of a rupee. Money has to mean the same number everywhere, and a floating point type would not |
| Typed ids, such as `SkuId` and `OrderId` | So a method taking an order id cannot be passed a customer id by mistake |
| `ErrorCode` | The catalogue of error codes every service reports through, which E03-07 fills in |
| `ServiceException` | The one exception type a service interface may throw |

Adding anything else needs a dated entry in decisions.md, which is question 4.

### The app module

`app` holds `PolluxKartApplication` and the wiring, and no business rules.
It is the only module that depends on every service, and the only one that produces a runnable program.
Services are wired in-process now; the configuration seam that would swap one for a network client arrives when a service actually moves out, not today.

### The parent POM

- Fixes every library version, taking the numbers confirmed by #55. No module declares a version of its own.
- Java 25, Spring Web MVC, virtual threads on, constructor injection only.
- No `common`, `util` or `helpers` module or package. Those names are where boundaries go to die, because anything can be justified into them.

### What this ticket does not build

E03-03 adds the Spring Modulith and ArchUnit checks that make the boundaries fail a build.
Until then the boundaries are declared and enforced by Maven's refusal of loops, but a reach into another module's `internal` would still compile.
That gap is deliberate and one ticket long.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A later ticket adds a dependency not in the table | It builds, because Maven only refuses loops, not any new edge. E03-03's test is what catches it, and Rule 7 says a new edge needs a dated decisions.md entry |
| Someone adds a reverse dependency, for example payment on order | Maven refuses the build, naming the cycle. The test plan proves this rather than assuming it |
| A service needs a type from another service's `internal` | It does not get it. Either the type belongs in that service's `api`, or the need is a sign the boundary is in the wrong place, which is a decision, not a workaround |
| Two services need the same helper | It does **not** go in shared-kernel by default. Duplicating a small helper is cheaper than coupling thirteen modules, and shared-kernel additions need the owner's approval |
| The empty modules slow the build | Fifteen modules with no code build in seconds. If that changes, Maven builds modules in parallel |
| A module has no code yet, so Spring finds nothing to start | Expected. The context test in the test plan asserts the application starts with every module present, which is the only behaviour this ticket has |
| `api/` does not exist when `make ci` runs today | `ci-api` is added by the local stack ticket. This ticket adds the modules; wiring them into `make ci` is E05 |

## What is deliberately not covered

- **Boundary checks** with Spring Modulith and ArchUnit: E03-03.
- **The contract round-trip harness:** E03-04.
- **Configuration, migrations, errors, logging, health and filters:** E03-05 to E03-10.
- **Any business logic, endpoint, database table or gRPC adapter.** Not one.
- **The OpenAPI document:** E03-12.

## Open questions for the owner

1. **Do you confirm the thirteen services and their names?**
identity, catalog, media, inventory, cart, order, payment, invoice, shipping, promotion, review, notification, audit.
Recommendation: yes, confirm them now.
Worth saying plainly though: thirteen services is a lot of structure for a shop run by one person, and `media` and `promotion` are the two most likely to feel like overhead, being small and quiet.
The reason to keep them separate anyway is that **merging two services later is a folder move, while splitting one later is a rewrite**, so the cost of being wrong is not symmetric.
If any name feels wrong, now is the cheap moment: renaming a module after thirteen feature tickets is noisy.

2. **Do you confirm the one-way dependency table (Rule 7)?**
It is the architectural commitment this ticket makes concrete, and it decides things like "payment can never call order" and "notification and audit are called, never listeners".
Recommendation: yes, unchanged. The reasoning in [service-boundaries.md](../high-level/service-boundaries.md) holds, and it is the shape that keeps Maven from finding a loop.
This entry is currently marked Proposed in decisions.md; confirming it here makes it a decision.

3. **All thirteen modules now as empty shells, or each one when its first feature ticket starts?**
Recommendation: **all thirteen now.**
The dependency graph is the part that is expensive to get wrong, and declaring it once, in full, is what makes it reviewable.
Empty modules cost seconds of build time and nothing else.
Also offered: create only what the walking skeleton needs (shared-kernel, app, identity, catalog) and add the rest per ticket, which keeps the tree smaller but re-opens the placement question thirteen times; or create each module strictly when first needed, which means E03-03's boundary checks have almost nothing to guard for months.

4. **Do you agree that adding a type to shared-kernel needs your dated approval in decisions.md?**
Recommendation: yes.
Every service depends on shared-kernel, so a type added there couples all thirteen at once, and that is exactly the kind of change that is invisible in a diff and expensive a year later.
