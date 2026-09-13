---
name: polluxkart-architecture
description: Use before writing or reviewing any backend Java code in PolluxKart's api/ folder, and always when adding a service, adding a class to a service, making one service call another, publishing or handling an event, or touching order placement. Covers the "microservices in one codebase, deployed together at launch" shape, Maven and package layout, wire-safe contracts, data ownership, remote-ready calls, events, and how the build enforces all of it. Load this first for any backend structural work.
---

# PolluxKart backend architecture

Source of truth this skill summarizes: `docs/platform/decisions.md`, `docs/platform/architecture.md` and `docs/design/high-level/service-boundaries.md`.
If this skill and those documents disagree, the documents win - update this skill to match, do not guess.
No backend code exists yet, so every path under `api/` below is planned.
Once code exists, the code wins over every document - then fix the document and this skill.

## Words used here

- **Service**: one business capability (catalog, inventory, order) with its own code, its own data and its own contract.
- **Maven module**: a sub-project with its own `pom.xml`; Maven is the Java build tool, and it refuses to build modules that depend on each other in a loop.
- **Contract**: the Java interface and records one service offers to the others, kept in its `api` package.
- **Record**: a Java class declared with `record` that only carries data, fixed at creation.
- **Sealed interface**: an interface that lists every class allowed to implement it, so a `switch` over it can be checked for completeness by the compiler.
- **gRPC**: a way for programs on different machines to call each other's methods over the network in a compact binary format.
- **Adapter**: a class that implements an interface by forwarding each call somewhere else, for example over gRPC.
- **Spring Modulith**: a Spring library that treats each top-level package as a module, checks which modules may use which, and stores events durably.
- **ArchUnit**: a test library that fails the build when code breaks a structural rule.
- **Schema**: a named group of tables inside one PostgreSQL database, written `catalog.skus`.
- **Transaction**: a group of database changes that either all happen or none happen.
- **Idempotency key**: a unique value sent with a change, so that repeating the request performs the change only once.
- **Compensation**: a step that undoes an earlier committed step when a later one fails, used when both cannot share one transaction.

## The shape: microservices in one codebase, deployed together at launch (decided 2026-09-13)

PolluxKart's backend is a set of independent services that live in one repository and, at launch, run inside one Java process.
Each service owns its code, its database schema and its contract.
Services call each other only through Java interfaces, so at launch a call is an ordinary method call.
Any service can later run as its own process by swapping its in-process implementation for a gRPC client adapter in configuration, without changing any caller.
The owner chose this over separate processes from day one (decided 2026-09-13): the boundaries are real now, and the cost of networks, separate deploys and distributed debugging is paid only when a service actually needs it.

**Never call this a monolith** - not in code, docs, commit messages or pull requests.
The owner rejected that word (2026-09-13) because it describes where the code runs at launch, not how it is designed, and it invites exactly the shortcuts this skill forbids.

## Maven layout

```
api/                         (planned) Maven parent: versions, plugins, module list
├── shared-kernel/           com.polluxkart.shared - Money, typed ids, ErrorCode, ServiceException. Nothing else.
├── identity/   catalog/   media/      inventory/   cart/
├── order/      payment/   invoice/    shipping/    promotion/
├── review/     notification/          audit/
└── app/                     com.polluxkart - PolluxKartApplication, security config, Flyway wiring, cross-cutting guards
```

- One Maven module per service, named exactly as above.
- A service module depends on `shared-kernel` and on the modules of the services it calls, nothing more.
- Maven refuses a dependency cycle, and listening to a service's events is a dependency too, because the listener compiles against the event record.
- Which service may depend on which is a fixed table, Rule 7 in `docs/design/high-level/service-boundaries.md` (decided 2026-09-13):

| Service | May depend on |
|---|---|
| notification, audit | shared-kernel only |
| identity | notification, audit |
| media, inventory, shipping | audit |
| catalog | media, audit |
| payment, invoice | notification, audit |
| promotion | catalog, audit |
| cart | identity, catalog, inventory |
| order | identity, catalog, inventory, cart, promotion, payment, shipping, invoice, notification, audit |
| review | order, catalog, notification, audit |

- notification and audit are called, never listeners: a service reacts to its own committed event and calls `NotificationApi` or `AuditApi` with an idempotency key.
- order orchestrates, and payment never calls order: payment publishes `PaymentCaptured`, `PaymentFailed` and `RefundProcessed`, and order listens.
- `app` is the only module that depends on every service, and it holds wiring only, never business rules.
- `shared-kernel` stays tiny, and adding a type to it needs a dated entry in `docs/platform/decisions.md`, because every service is coupled to everything inside it.
- Which service owns which tables, endpoint prefixes and events is recorded in `docs/design/high-level/service-boundaries.md` and in each `docs/services/<service>/README.md`.

## Packages inside a service (set 2026-09-13)

```
com.polluxkart.inventory
├── package-info.java                @ApplicationModule(allowedDependencies = {"shared", "audit::api"})
├── api/                             the contract - public and wire-safe
│   ├── package-info.java            @NamedInterface("api")
│   ├── InventoryApi.java            interface other services call
│   ├── ReserveStock.java            command record
│   ├── StockReserved.java           event record
│   └── InventoryErrorCode.java      enum implementing shared ErrorCode
└── internal/                        no other service may import anything below here
    ├── InventoryService.java        application service - business rules, @Transactional
    ├── InProcessInventoryApi.java   implements InventoryApi by delegating to application services
    ├── Reservation.java             domain object
    ├── persistence/                 JPA entities, Spring Data repositories, entity-to-domain mappers
    └── web/                         REST controllers and their request and response records
```

Controllers always live in `internal.web`, and entities and repositories always live in `internal.persistence`, so the ArchUnit rules below can be written against package names.
A caller lists what it uses in its own `package-info.java`, for example `order` declares `allowedDependencies = {"shared", "identity::api", "catalog::api", "inventory::api", "cart::api", "promotion::api", "payment::api", "shipping::api", "invoice::api", "notification::api", "audit::api"}`.

## Dependencies flow one way

Across services, a caller depends only on the other service's `api` package.
Inside a service, the flow is entry point -> application service -> repository -> database.
Entry points are controllers, the in-process api implementation, event listeners and scheduled jobs.

- Never skip a layer: a controller never touches a repository.
- Never go backward: an application service never sees `HttpServletRequest`, `ResponseEntity` or an HTTP request record.
- JPA entities never leave `internal`: not in `api` records, not in events, not in controller signatures.
- Use constructor injection only, never `@Autowired` on a field, so a missing dependency fails at startup and a test can build the class by hand.
- Do not create `common`, `util` or `helpers` packages; name a package for what it provides.

## Contracts are wire-safe

A contract must survive being turned into bytes and back, because one day it will cross a network.

Allowed in `api` records, parameters and return types:

- `String`, `boolean`, `int`, `long`, enums, `java.time.Instant` and `java.time.LocalDate`.
- `List` of allowed types, and nested records built from allowed types.
- The shared-kernel value records: `Money` (a `long` count of paise, one hundredth of a rupee) and typed ids such as `SkuId`.

Forbidden:

- JPA entities, Hibernate lazy proxies, Spring Data `Page`, `Pageable` or `Sort`.
- Any type from `jakarta.persistence`, `jakarta.servlet`, `org.hibernate` or `org.springframework`.
- `Optional` as a record component, `Map<String, Object>`, `Object`, streams, lambdas and callbacks.
- `float`, `double` or `BigDecimal` for money.

Expected business outcomes the caller must branch on come back as data (an outcome enum plus fields).
Failures cross the boundary as a `ServiceException` carrying a typed `ErrorCode`, never as a framework exception.
Every error code belongs to an `ErrorCategory` (such as `NOT_FOUND`, `FAILED_PRECONDITION` or `UNAVAILABLE`) that decides the HTTP status today and the gRPC status after extraction.
The full error convention lives in `polluxkart-error-handling`.

```java
public interface InventoryApi {
    List<SkuAvailability> availability(List<SkuId> skuIds);   // batch read
    ReservationResult reserve(ReserveStock command);           // repeat with the same key returns the first result
    void release(ReleaseReservation command);                  // releasing twice is a no-op
}

public record ReserveStock(String idempotencyKey, List<Line> lines, int holdMinutes) {
    public record Line(SkuId skuId, int quantity) {}
}

public record ReservationResult(ReservationOutcome outcome, ReservationId reservationId, List<Shortfall> shortfalls) {}

public enum ReservationOutcome { RESERVED, INSUFFICIENT_STOCK }
```

## Data ownership

- One PostgreSQL schema per service, named after it; `order` is a reserved SQL word, so its schema is planned as `orders` (`docs/design/high-level/data-model.md` has the final names).
- A service reads and writes only its own schema.
- Cross-service references are ids only: `orders.order_items.sku_id` is a plain `uuid` column with no foreign key to `catalog.skus`.
- No SQL join across schemas, not even for a read-only admin screen.
- Data another service needs later is fetched by a batch api call, or copied as a snapshot at write time.
  An order line snapshots name, price, HSN code (the tax classification number for goods) and tax, which the GST invoice legally needs anyway.
- Because the database cannot check a cross-service id, the owner of a row archives it instead of deleting it once anything may reference it: a sold SKU (one buyable variant, such as "128 GB, black") is archived, never deleted.
- Flyway migrations live inside the owning module, and every storage rule is in `polluxkart-postgres-jpa`.
- Process-wide tables (`event_publication`, `shedlock`) are planned in a small `platform` schema owned by `app`; `data-model.md` is the authority.

## Calls must be remote-ready

Write every cross-service call as if it already went over a network.

- **Batch, never chatty.**
  Ask for 30 SKUs in one call, never one call per SKU inside a loop.
- **Every mutation carries an idempotency key.**
  The receiving service stores the key under a UNIQUE constraint in its own schema, in the same transaction as the change, and returns the first result on a repeat.
- **Never call another service while your transaction is open.**
  In-process, Spring would silently join the callee to your transaction, so your rollback would undo work the callee reported as done; over gRPC that can never happen.
  A planned aspect in `app` wraps every `*Api` implementation and throws if a transaction is already active, so this mistake fails the first test that exercises it.
- **Pass context explicitly.**
  The acting user id goes in the command record; a callee never reads `SecurityContextHolder` or a thread-local set by the caller, because a remote callee would find it empty.
- **Expect partial failure.**
  A call can fail after the callee committed, so the caller either retries with the same idempotency key or compensates.
- **Return data, not live objects.**
  No lazy loading, no identity comparisons, no mutating a returned object to change the callee's state.

Swapping transport is configuration, not a code change for callers:

```java
@Component
@ConditionalOnProperty(name = "polluxkart.services.inventory.transport", havingValue = "in-process", matchIfMissing = true)
class InProcessInventoryApi implements InventoryApi { /* delegates to InventoryService */ }

// Only when inventory is extracted, in its own client module (not built):
@Component
@ConditionalOnProperty(name = "polluxkart.services.inventory.transport", havingValue = "grpc")
class GrpcInventoryApi implements InventoryApi { /* same interface, network underneath */ }
```

## Events for side effects

A side effect is work that should follow a change but that the caller does not wait for: an email, an audit row, a cache refresh.

- Publish with `ApplicationEventPublisher.publishEvent(...)` inside the transaction that made the change.
- Spring Modulith's event publication registry writes the event to the `event_publication` table in that same transaction, so a committed change always has its event recorded, and a rolled-back change never does.
- Listen with `@ApplicationModuleListener`, which runs after the commit, on another thread, in its own new transaction.
- The registry marks the event complete only when the listener succeeds; unfinished events are resubmitted on restart and by a scheduled retry (`IncompleteEventPublications`).
- Delivery is at-least-once, meaning a listener can see the same event twice, so every listener is idempotent.
- Event records live in the publisher's `api` package and follow the wire-safe rules; they carry ids plus the facts listeners need, never entities.
- Use a call, not an event, when the caller needs the answer now (reserving stock is a call).
- Audit rows are written by the changing service's own listener calling `AuditApi`: the registry makes that call as durable as the change itself.
- Events can be sent to a message broker later with `@Externalized`, once a listening service is extracted; there is no broker at launch.

```java
// order.internal
@Transactional
public Order confirm(ConfirmOrder command) {
    var order = orders.markConfirmed(command.orderId(), clock.instant());
    events.publishEvent(new OrderConfirmed(order.id(), order.userId(), order.number()));
    return order;
}

// order.internal: order reacts to its own event, because notification may not depend on order (Rule 7)
@ApplicationModuleListener
void on(OrderConfirmed event) {
    var contact = identity.contact(event.userId());                              // order may call identity
    notification.enqueue(new EnqueueEmail("order-confirmed:" + event.orderId(),   // dedupe key absorbs duplicates
            EmailTemplate.ORDER_CONFIRMED, contact.email(), List.of(new TemplateValue("orderNumber", event.number()))));
}
```

## Order placement across services

Placing an order touches `inventory` and `order`, which cannot share a transaction, so it is a short sequence with compensation.
The full state machine, including payment capture and late capture, is in `docs/design/high-level/order-lifecycle.md`.

1. **Quote.**
   `order` builds the quote from batch calls to `catalog` and `promotion`, and returns `price_changed` if the total differs from the one the customer saw.
2. **Reserve.**
   `inventory.reserve` runs in inventory's own transaction, with the order attempt's idempotency key and a hold time.
   Inside, each SKU is reserved with a conditional UPDATE in sorted SKU id order, so stock can never oversell and two orders can never deadlock.
   The reservation is born `ACTIVE` with an expiry, Cash on Delivery included.
3. **Save.**
   `order` saves the order, its lines, its status history and its idempotency record (UNIQUE `(user_id, idempotency_key)` in the `orders` schema) in one short transaction of its own.
4. **Compensate.**
   If the save fails, `order` calls `inventory.release` for that reservation, then reports the failure.
5. **Commit.**
   Once the order is confirmed (COD placed, or payment verified), `inventory.commit` turns the reservation `COMMITTED`, with no expiry.
6. **Safety net (decided 2026-09-13).**
   The payment expiry job runs in `order`: for orders past their payment hold it asks `payment` for the latest status, then confirms and commits, or cancels and releases.
   `inventory` never reads order state (that would be a Maven cycle); its own sweeper releases only `ACTIVE` reservations past their hold time plus a grace period, which catches reservations that never got an order because the process died between reserve and save.

The reservation states and hold times are in `polluxkart-commerce`.

**A duplicate-key failure in step 3 is not a failure.**
It means another request with the same key already saved the order, and the reservation belongs to that order: return it and do not release anything.
What a repeat does after compensation already ran is specified in `order-lifecycle.md`; do not improvise it.

An earlier draft of the plan reserved stock and saved the order in one transaction; superseded 2026-09-13 by the services decision, because a remote inventory can never join the order's transaction.

```java
// order.internal - deliberately NOT @Transactional: it coordinates two services
PlacementOutcome place(PlaceOrder cmd) {
    var quote = quotes.current(cmd.userId(), cmd.cartId());
    if (quote.totalPaise() != cmd.expectedTotalPaise()) return new PriceChanged(quote);

    var held = inventory.reserve(new ReserveStock(cmd.idempotencyKey(), quote.linesSortedBySku(), HOLD_MINUTES));
    if (held.outcome() == ReservationOutcome.INSUFFICIENT_STOCK) return new OutOfStock(held.shortfalls());

    try {
        return new Placed(orderWriter.save(cmd, quote, held.reservationId()));          // own short transaction
    } catch (DuplicateIdempotencyKey duplicate) {
        return new Placed(orderWriter.findByKey(cmd.userId(), cmd.idempotencyKey()));  // not ours to release
    } catch (RuntimeException failure) {
        inventory.release(new ReleaseReservation(held.reservationId(), "release:" + cmd.idempotencyKey()));
        throw failure;
    }
}

public sealed interface PlacementOutcome permits Placed, PriceChanged, OutOfStock {}   // records; the controller switches over them
```

Required tests: 50 threads buying the last 5 units produce exactly 5 orders; a double submit returns the same order; a crash injected between reserve and save leaves `reserved` unchanged once the expiry job runs.

## How the build enforces this

A rule that only lives in this file will be broken, so each one has a check that fails the build.

1. **Maven** refuses cycles between service modules.
2. **Spring Modulith** verifies module boundaries in a test in `app`: no cycles between modules, and no access to anything not exposed as a named interface.
3. **ArchUnit** adds the finer rules Modulith does not cover.
4. **A contract round-trip test** proves every contract survives serialization.

```java
@Test
void servicesRespectTheirBoundaries() {
    ApplicationModules.of(PolluxKartApplication.class).verify();
}

@ArchTest
static final ArchRule contractsAreFrameworkFree = noClasses()
        .that().resideInAPackage("com.polluxkart.*.api..").and().doNotHaveSimpleName("package-info")
        .should().dependOnClassesThat().resideInAnyPackage(
                "jakarta.persistence..", "jakarta.servlet..", "org.hibernate..", "org.springframework..");

@ArchTest
static final ArchRule controllersNeverTouchPersistence = noClasses()
        .that().resideInAPackage("..internal.web..")
        .should().dependOnClassesThat().resideInAPackage("..internal.persistence..");
```

Other ArchUnit rules (planned): `@Entity` classes live only in `internal.persistence`; `@RestController` classes live only in `internal.web`; `shared` depends on no service; no `@Transactional` on controllers.
The contract test (planned) walks every `*Api` interface, builds a sample of every type it can reach with no field left at its default value, turns it into JSON and back, and asserts the result equals the original.
It also fails if any reachable type is outside the allowed list above.

## Extraction triggers and what is not built yet (decided 2026-09-13)

A service leaves the shared process only when one of these is true, as recorded in the ADR (Architecture Decision Record, a short dated file saying what was decided and why):

- Search outgrows PostgreSQL, around 5,000 SKUs.
- Notifications need to scale independently of the store.
- A separate team owns a service.

Do not build any of these without the owner's approval, and flag the task if it seems to need one:

- gRPC adapters or protobuf files, until the first extraction.
- A message broker; events stay in the registry until a listener is extracted.
- Redis or any shared cache.
- A dedicated search engine.
- A second API instance; the in-memory rate limiter in `polluxkart-http-api` assumes one.

## How to add a new service

1. Record the service, what it owns and whom it calls in `docs/platform/decisions.md` and `docs/design/high-level/service-boundaries.md`, dated.
2. Create the Maven module under `api/`, add it to the parent's module list and to `app`'s dependencies.
3. Create `com.polluxkart.<service>` with `package-info.java` declaring `@ApplicationModule(allowedDependencies = ...)`.
4. Create `api/` with `@NamedInterface("api")`, the interface, command and result records, events and an error code enum.
5. Create `internal/`, `internal/persistence/` and `internal/web/`, plus the in-process api implementation.
6. Add the first migration that creates the schema and its grants, and register the schema's Flyway setup in `app` (see `polluxkart-postgres-jpa`).
7. Give the controllers an endpoint prefix no other service uses, and record it in the service README (see `polluxkart-http-api`).
8. Write `docs/services/<service>/README.md`.
9. Confirm the Modulith test, ArchUnit rules and contract round-trip test all see the new service, then run `make ci`.

## Wrong vs right

```java
// WRONG: order reaches into inventory's internals, joins across schemas, and holds one transaction around both services
@Transactional
public Order place(PlaceOrder cmd) {
    for (var line : cmd.lines()) {                                           // chatty: one round trip per line
        InventoryEntity stock = inventoryRepository.findBySkuId(line.skuId()); // imports inventory.internal
        stock.setReserved(stock.getReserved() + line.quantity());             // read-modify-write: oversells
    }
    return orderRepository.save(new OrderEntity(cmd));                        // one rollback "undoes" inventory too
}

// RIGHT: one batch call through the contract, outside any transaction, with an idempotency key and compensation
public PlacementOutcome place(PlaceOrder cmd) {
    var quote = quotes.current(cmd.userId(), cmd.cartId());                   // batch calls to catalog and promotion
    var held = inventory.reserve(new ReserveStock(cmd.idempotencyKey(), quote.linesSortedBySku(), HOLD_MINUTES));
    return switch (held.outcome()) {
        case INSUFFICIENT_STOCK -> new OutOfStock(held.shortfalls());
        case RESERVED -> saveOrRelease(cmd, quote, held.reservationId());
    };
}
```

## Checklist before you open a pull request

- [ ] Nothing outside a service imports its `internal` packages, and every new dependency is listed in `allowedDependencies`.
- [ ] Every new `api` type uses only the allowed types, and the contract round-trip test covers it.
- [ ] No JPA entity, `Page`, `Optional` component or framework type appears in a contract or an event.
- [ ] No SQL touches another service's schema, and cross-service references are plain ids with no foreign key.
- [ ] Every cross-service mutation carries an idempotency key and is stored under a UNIQUE constraint by the callee.
- [ ] No cross-service call happens while a transaction is open, and every multi-service flow has compensation plus a safety-net job.
- [ ] Side effects go through events, and every listener tolerates the same event twice.
- [ ] Controllers call application services only, never repositories.
- [ ] The word "monolith" appears nowhere in code, docs, commits or the pull request.
- [ ] Nothing from "not built yet" was added without the owner's approval.
- [ ] `service-boundaries.md` and the service README match what the code now does, with dated decisions.
- [ ] `make ci` passes locally, including Modulith verify, ArchUnit and the contract test.
