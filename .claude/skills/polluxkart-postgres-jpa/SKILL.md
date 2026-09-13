---
name: polluxkart-postgres-jpa
description: Use whenever writing or reviewing a Flyway migration, a JPA entity, a Spring Data repository, a native or JPQL query, a @Transactional method, or anything that changes stock, money, counters or status in PolluxKart's PostgreSQL database. Covers schema-per-service migrations, column types (money, time, ids, status), constraints, N+1 prevention, parameterized SQL, transactions, locking, database roles and Testcontainers.
---

# PolluxKart's data layer: PostgreSQL 18, Flyway and JPA

Source of truth this skill summarizes: `docs/design/high-level/data-model.md`, `docs/platform/stack.md` and `docs/platform/decisions.md`.
If this skill and those documents disagree, the documents win - update this skill to match, do not guess.
No backend code exists yet, so every path under `api/` below is planned.
Service boundaries (who owns which schema) are in `polluxkart-architecture`; read that first.

## Words used here

- **JPA (Jakarta Persistence)**: the standard Java way to map classes to database tables; **Hibernate** is the library that implements it here.
- **Entity**: a Java class JPA maps to one table row.
- **Aggregate**: a group of rows that change together and are loaded through one root, such as an order with its lines.
- **Flyway**: a tool that applies numbered SQL files (migrations) to the database in order and records which ones ran.
- **Constraint**: a rule the database itself enforces on every write, such as `UNIQUE`, `CHECK` or `NOT NULL`.
- **N+1 query**: one query to load a list, then one more query per row, which turns 1 page view into hundreds of queries.
- **Row lock**: a mark PostgreSQL puts on a row so other transactions wait before changing it.
- **Optimistic locking**: no lock is taken; a version number detects that someone else changed the row in the meantime.
- **Testcontainers**: a library that starts a real PostgreSQL in Docker for tests and throws it away afterwards.
- **Paise**: one hundredth of a rupee; ₹1,299.00 is 129900 paise.

## Settings that are never changed (decided 2026-09-13)

```yaml
spring:
  jpa:
    open-in-view: false                 # no lazy loading while the HTTP response is written
    hibernate:
      ddl-auto: validate                # Hibernate checks the schema, never changes it
    properties:
      hibernate:
        jdbc.time_zone: UTC
        default_batch_fetch_size: 50
        query.fail_on_pagination_over_collection_fetch: true
  flyway:
    enabled: false                      # Boot's single Flyway would mix every service's migrations; app wires one per schema
```

- **Flyway owns the schema.**
  Hibernate only validates it at startup, and the app fails to boot if an entity maps a column the database lacks.
- **`open-in-view=false`** stops Spring from keeping the database session open while JSON is rendered.
  With it on, a forgotten fetch silently becomes an N+1 in production; with it off, the same mistake throws `LazyInitializationException` in the first test.
- **PostgreSQL 18** everywhere: RDS in AWS, `postgres:18` in Docker Compose and in Testcontainers.
  Bump all three in the same pull request.
- The JVM runs with `-Duser.timezone=UTC`, so no code path can pick up the server's local time by accident.

## Migrations: one Flyway per service schema

- Files live in the owning service module at `src/main/resources/db/migration/<schema>/`.
- Name: `V<UTC timestamp>__<what_it_does>.sql`, for example `V20260913103000__create_inventory.sql`.
- Start each file with a comment saying what it does and why.
- Schema-qualify every name (`inventory.stock_reservations`), so a file cannot write to the wrong schema.
- Each schema has its own Flyway history table inside that schema, so a service can later move to its own database with its history intact.
- Migrations run as `pk_migrator` in a one-shot step before the new version starts (planned in `ops/deploy.sh`); the running app connects as `pk_app` and never runs DDL (statements that create or change tables).
- In tests, migrations run from an empty database on every test run, through the same per-schema wiring (planned in `app`).

**Forward-only.**
Never edit or delete a migration that has been merged; write a new one.
There are no "down" migrations; a mistake is fixed by the next forward migration.
If your migration's timestamp is older than one already merged into `development` for the same schema, rename it to a fresh timestamp before merging, because Flyway refuses to apply an older file after a newer one.

**Expand, then contract.**
Deploys run migrations first, and an automatic rollback restarts the previous image against the already-migrated schema.
So every migration must work with the code of the release before it.

1. **Expand** (release 1): add the new column or table, nullable or with a default; the code writes both old and new.
2. **Migrate** (release 1 or 2): backfill existing rows; the code reads the new shape.
3. **Contract** (a later release): drop the old column once no deployed image maps it.

Hibernate's `validate` ignores extra columns, but fails on a mapped column that is missing, so the entity stops mapping a column one release before the column is dropped.
`CREATE INDEX CONCURRENTLY` cannot run inside a transaction, so that file gets a sibling `.sql.conf` file containing `executeInTransaction=false`.

## Two database roles (decided 2026-09-13)

- `pk_migrator` owns every schema and table, and is used only by the migration step and test setup.
- `pk_app` is what the running app uses: `USAGE` on schemas and `SELECT, INSERT, UPDATE, DELETE` on tables, nothing else.
- Append-only tables (`audit.audit_log`, `inventory.stock_movements`, and any table `data-model.md` marks append-only) give `pk_app` only `SELECT, INSERT`.
- The roles are created once per database outside service migrations (see `docs/platform/stack.md`); each service's first migration grants `pk_app` what that schema needs.

```sql
-- V20260913100000__create_audit_log.sql: grants for the app role and the append-only audit log.
-- Flyway creates the audit schema itself, owned by pk_migrator.
GRANT USAGE ON SCHEMA audit TO pk_app;
ALTER DEFAULT PRIVILEGES FOR ROLE pk_migrator IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pk_app;

CREATE TABLE audit.audit_log (
    id          uuid        PRIMARY KEY DEFAULT uuidv7(),
    actor_id    uuid,
    action      text        NOT NULL,
    target_type text        NOT NULL,
    target_id   uuid        NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now()
);
REVOKE UPDATE, DELETE ON audit.audit_log FROM pk_app;   -- history cannot be rewritten by the app
```

A test (planned) connects as `pk_app` and asserts that `UPDATE` and `DELETE` on every append-only table fail with "permission denied".

## Three shapes per aggregate

1. **JPA entity** in `internal.persistence`: maps 1:1 to the table's columns, and never leaves the service.
2. **Domain object** in `internal`: the shape business rules work with, which may hold computed values no column has (a discount percentage).
3. **Boundary record**: an `api` record for other services, or a response record in `internal.web` for HTTP.

Mapping is one small explicit method per direction.
Never return an entity from a controller or an api method, and never put JSON annotations on an entity.
Doing so leaks columns to clients by accident (a password hash, a cost price), and turns a column rename into a silent API break.

```java
@Entity
@Table(schema = "catalog", name = "skus")
class SkuEntity {                                    // internal.persistence
    @Id UUID id;
    @Column(name = "product_id", nullable = false) UUID productId;
    @Column(name = "mrp_paise", nullable = false) long mrpPaise;
    @Column(name = "price_paise", nullable = false) long pricePaise;
    @Enumerated(EnumType.STRING) @Column(nullable = false) SkuStatus status;
    @Version Long version;                           // wrapper type: see ids below
    protected SkuEntity() {}
}

record Sku(SkuId id, ProductId productId, Money mrp, Money price, SkuStatus status) {   // internal
    int discountPercent() { return (int) (100 * (mrp.paise() - price.paise()) / mrp.paise()); }
}

public record SkuView(SkuId id, ProductId productId, Money mrp, Money price, SkuStatus status) {}   // api
```

## Column types

| Kind | PostgreSQL | Java | Never |
|---|---|---|---|
| Id | `uuid PRIMARY KEY DEFAULT uuidv7()` | `UUID` inside a typed id record | `bigserial` ids in URLs, random UUIDv4 keys |
| Money | `bigint` paise with a `CHECK` | `long`, or `Money` | `numeric` in JSON, `float`, `double` |
| Tax rate | `integer` basis points (1800 = 18%) | `int` | a floating percentage |
| Moment in time | `timestamptz` | `Instant` | `timestamp` without time zone, `LocalDateTime` |
| Business date | `date` | `LocalDate` computed in `Asia/Kolkata` | a date taken from the server's zone |
| Status | `text NOT NULL CHECK (status IN (...))` | enum with `@Enumerated(EnumType.STRING)` | `EnumType.ORDINAL`, PostgreSQL enum types |
| Email | `citext` with `UNIQUE` | `String` | lower-casing in code as the only guard |
| Flag | `boolean NOT NULL DEFAULT false` | `boolean` | a nullable boolean |

**Money is an integer count of paise (decided 2026-09-13).**
Floating-point numbers cannot represent 0.10 exactly, so totals drift by a paisa and invoices stop matching payments.
Never `float` or `double` anywhere, and never `BigDecimal` in a column or JSON.
Tax maths is integer arithmetic with explicit rounding, specified in `polluxkart-commerce`.

**Time is stored in UTC, and business dates are computed in India time.**
A `timestamptz` is an exact moment; `Instant` is its Java twin.
Anything a person reads as a date (invoice date, financial year, "delivered by") is computed with `ZoneId.of("Asia/Kolkata")` from an injected `Clock`, never from `Instant.now()`.
The case that bites: an invoice issued at 00:30 IST on 1 April is still 19:00 UTC on 31 March, yet it belongs to the new financial year and its new number series.

**Ids are UUIDv7 (decided 2026-09-13).**
UUIDv7 starts with a timestamp, so new ids land at the end of the index instead of at random places, which keeps inserts fast.
PostgreSQL 18 generates them natively with `uuidv7()`, used as the column default for rows inserted by SQL.
The app assigns ids before saving, through the shared-kernel id factory (planned), so the id is known for events, idempotency records and logs before commit.
With an assigned id, Spring Data decides "new row or existing row" from the `@Version` field, so it must be `Long`, not `long`.
A primitive version makes Spring Data call `merge`, which runs an extra `SELECT` before every insert.
Entities without `@Version` implement `Persistable<UUID>` for the same reason.
A UUIDv7 is not a secret and reveals its creation time; access is protected by ownership checks (`polluxkart-http-api`), never by an id being hard to guess.

**Status is text with a CHECK.**
`ORDINAL` stores the enum's position, so reordering the enum silently changes the meaning of every stored row.
Adding a status is a migration that replaces the `CHECK`, merged before any code writes the new value.

## Constraints are the last line of defence

Code checks give friendly error messages; constraints guarantee the rule holds on every path that writes, including an admin import, a manual fix and a future service.
If a rule matters, it is a constraint, and the code check is a courtesy on top.

```sql
CREATE TABLE inventory.stock (
    sku_id   uuid    PRIMARY KEY,                          -- catalog's id; no foreign key across schemas
    on_hand  integer NOT NULL CHECK (on_hand >= 0),
    reserved integer NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    CONSTRAINT stock_reserved_within_on_hand CHECK (reserved <= on_hand)
);

ALTER TABLE catalog.skus ADD CONSTRAINT skus_price_within_mrp CHECK (price_paise > 0 AND price_paise <= mrp_paise);
ALTER TABLE orders.idempotency_keys ADD CONSTRAINT idempotency_keys_user_key_uq UNIQUE (user_id, idempotency_key);
ALTER TABLE payment.payment_events ADD CONSTRAINT payment_events_provider_event_uq UNIQUE (provider_event_id);
```

- Name every constraint.
  The repository catches `DataIntegrityViolationException`, reads the constraint name, and turns a known one into this service's own exception (`idempotency_keys_user_key_uq` becomes `DuplicateIdempotencyKey`).
- Idempotency records live in the owning service's own schema and are written in the same transaction as the change they protect, so they stay correct after the service is extracted.
- Foreign keys are used inside a schema, never across schemas.
- Every column is `NOT NULL` unless "unknown" is a real business state.

## Queries: no N+1, parameters only

- Every `@ManyToOne` and `@OneToOne` declares `fetch = FetchType.LAZY`, because the JPA default is eager.
- A list loads what it shows up front, with `join fetch` or `@EntityGraph` for single associations, and batch fetching (`default_batch_fetch_size`) for collections.
- A paginated query never fetch-joins a collection; the setting above makes Hibernate throw instead of paginating in memory.
- Read-heavy screens select only the columns they show, through a record projection or `JdbcClient`.
- Data from another service is fetched with one batch api call for the whole page, never one call per row.
- Every list endpoint has a test that asserts a fixed query count, whatever the number of rows.

```java
// WRONG: 1 query for the page, then 1 per product for the brand and 1 per product for its SKUs
List<ProductEntity> page = products.findByCategoryId(categoryId, pageable);
page.forEach(p -> cards.add(new Card(p.getBrand().getName(), p.getSkus().getFirst().getPricePaise())));

// RIGHT: a fixed number of queries; SKUs arrive in one IN (...) query through batch fetching
@Query("""
    select p from ProductEntity p join fetch p.brand
    where p.categoryId = :categoryId and p.status = :status
    order by p.createdAt desc, p.id
    """)
List<ProductEntity> findPageWithBrand(UUID categoryId, ProductStatus status, Pageable pageable);

@Test
void categoryPageUsesAFixedNumberOfQueries() {
    seed.products(40);
    long queries = queryCounter.count(() -> catalog.listCategory(PHONES, PageRequest.of(0, 24)));   // planned helper
    assertThat(queries).isLessThanOrEqualTo(3);
}
```

**Never build SQL from strings.**
Every value is a bound parameter; the only text ever joined into SQL is a constant picked by a `switch` over an enum.

```java
// WRONG: SQL injection, and the sort column comes straight from the URL
jdbc.sql("select id, name from catalog.products where name ilike '%" + q + "%' order by " + sortParam);

// RIGHT
String orderBy = switch (sort) {
    case NAME_ASC -> "name asc, id";
    case NEWEST   -> "created_at desc, id";
};
jdbc.sql("select id, name from catalog.products where name ilike :pattern order by " + orderBy + " limit :limit")
    .param("pattern", "%" + escapeLike(q) + "%")    // escapes % and _ typed by the user
    .param("limit", size)
    .query(ProductRow.class)
    .list();
```

## Transactions: short, and nothing remote inside

- `@Transactional` goes on public application service methods, with `readOnly = true` for reads; never on controllers.
- Spring ignores `@Transactional` on private methods and on a method called from inside the same class, so such a call runs with no transaction at all.
- **No remote call while a transaction is open**: not Razorpay, not SES (Amazon's email service), not S3, not another service's api.
  A slow network call holds a database connection and row locks for its whole duration, and a small pool runs dry under load.
- After any failed statement, PostgreSQL rejects every further statement in that transaction.
  Never catch a database exception and carry on inside the same transaction; use `INSERT ... ON CONFLICT DO NOTHING` or check first.
- Do not run queries in parallel threads inside one transaction; a transaction is bound to one connection, which runs one query at a time.
- The isolation level stays PostgreSQL's default, READ COMMITTED; correctness comes from the locking patterns below, not from a stricter level.

```java
// WRONG: Razorpay is called inside the transaction, holding the connection and its locks for seconds
@Transactional
public PaymentAttempt start(StartPayment cmd) {                                // order passes orderId and amountPaise
    var created = razorpay.createOrder(cmd.amountPaise());                     // network call
    return attempts.save(PaymentAttemptEntity.pending(cmd, created.id()));
}

// RIGHT: short transaction, call outside, short transaction
public PaymentAttempt start(StartPayment cmd) {
    var attempt = tx.execute(s -> attempts.insertPending(cmd));
    var created = razorpay.createOrder(cmd.amountPaise(), attempt.id());      // receipt = our attempt id
    return tx.execute(s -> attempts.recordProviderOrder(attempt.id(), created.id()));
}
```

## Concurrency: pick the right tool

| Problem | Tool |
|---|---|
| A counter must never cross a limit (stock) | Conditional `UPDATE`, then check the affected row count |
| Several rows must change together consistently (coupon and its redemptions, invoice sequence) | `SELECT ... FOR UPDATE`, locks taken in sorted id order |
| Two admins may edit the same record (product, store settings) | Optimistic `@Version`, answered with 409 on conflict |
| Several workers drain one queue (email outbox, expiry jobs) | `FOR UPDATE SKIP LOCKED`, plus ShedLock on the schedule |

**Conditional UPDATE.**
The check and the change happen in one statement, so two buyers can never both take the last unit.

```java
@Modifying(flushAutomatically = true, clearAutomatically = true)   // keep loaded entities in step with the bulk update
@Query(nativeQuery = true, value = """
    UPDATE inventory.stock
       SET reserved = reserved + :quantity
     WHERE sku_id = :skuId AND on_hand - reserved >= :quantity
    """)
int tryReserve(UUID skuId, int quantity);

// InventoryService, inside one transaction
for (var line : Ids.inLockOrder(command.lines(), Line::skuId)) {
    if (inventoryRows.tryReserve(line.skuId().value(), line.quantity()) != 1) {
        throw new InsufficientStock(line.skuId());                    // rolls back the lines already reserved
    }
}
```

The read-modify-write version (load the row, check `onHand - reserved` in Java, save) oversells: two threads read the same number and both pass the check.

**Locks in sorted order.**
If one transaction locks SKU A then B while another locks B then A, each waits for the other forever (a deadlock).
Every code path that locks several rows sorts them the same way.
Java's `UUID.compareTo` compares signed numbers and can disagree with PostgreSQL's byte order, so sort through the shared-kernel's lock-order helper (planned `Ids.inLockOrder`) or with `ORDER BY id` in the locking query itself.

**`FOR UPDATE` locks only rows that exist.**
Two transactions that lock "all redemptions of this coupon" both lock nothing when there are none yet, and both proceed.
Lock a parent row that always exists instead, creating it first if needed.

```sql
INSERT INTO invoice.invoice_sequences (financial_year, last_number) VALUES (:fy, 0)
ON CONFLICT (financial_year) DO NOTHING;

SELECT last_number FROM invoice.invoice_sequences WHERE financial_year = :fy FOR UPDATE;   -- every issuer waits here
UPDATE invoice.invoice_sequences SET last_number = last_number + 1 WHERE financial_year = :fy RETURNING last_number;
```

**A lock only one writer takes protects nothing.**
Every code path that writes a shared row takes the same lock, in the same transaction, and re-reads the row after taking it, because anything read before the lock may already be stale.

**Optimistic locking.**
Update requests carry the `version` the admin's form was loaded with.
Loading the entity fresh and saving it uses the fresh version, which silently overwrites the other admin's change, so compare `request.version()` with the loaded version explicitly and reject a mismatch with 409 `concurrent_update`.

**SKIP LOCKED for job queues.**
A worker claims a batch with `SELECT ... WHERE status = 'PENDING' AND next_attempt_at <= now() ORDER BY next_attempt_at LIMIT 20 FOR UPDATE SKIP LOCKED`, marks the rows as claimed with a lease time, and commits.
It then does the slow work (sending the email) outside the transaction, and records the result in a new short transaction.
ShedLock (a table-based lock for `@Scheduled` jobs) keeps a second instance from running the same schedule at once.

## Testing against the real database

- Tests use Testcontainers with `postgres:18`, the same major version as RDS; never H2 or another in-memory stand-in, which lacks `uuidv7()`, `SKIP LOCKED` and PostgreSQL's constraint behaviour.
- One container is shared by the whole test run, and every migration is applied to it from empty.
- App code in tests connects as `pk_app` and migrations as `pk_migrator` (planned), so a missing grant fails in CI rather than in production.
- Concurrency tests use real threads released together by a `CountDownLatch`; the stock test sends 50 buyers at the last 5 units and expects exactly 5 successes and `reserved = 5`.
- Docker must be running; `make doctor` checks it.
- The full testing approach is in `docs/platform/testing.md` and `polluxkart-testing`.

## Checklist before you open a pull request

- [ ] Every schema change is a new, schema-qualified Flyway file in the owning service; no merged migration was edited.
- [ ] The migration works with the previous release's code (expand, then contract), and the whole chain applies from empty.
- [ ] New tables grant `pk_app` only what it needs, and append-only tables revoke `UPDATE` and `DELETE`.
- [ ] Money is `bigint` paise, moments are `timestamptz`, ids are UUIDv7, statuses are text with a `CHECK`.
- [ ] Business dates use `Asia/Kolkata` and an injected `Clock`.
- [ ] Every business rule that must always hold is also a named database constraint.
- [ ] No entity leaves the service; entity, domain object and boundary record are separate types.
- [ ] Every `@ManyToOne` is lazy, and every new list has a query-count assertion.
- [ ] No SQL is built from user input; sort fields come from an enum.
- [ ] No transaction contains a remote call or a call to another service.
- [ ] Stock and counters change through conditional updates; multi-row locks are taken in sorted order; edits check `@Version`.
- [ ] New queries were run against Testcontainers `postgres:18`, and `make ci` passes locally.
