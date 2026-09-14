# inventory

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PROPOSED (2026-09-13), confirmed ticket by ticket. Built in slices S3 and S5.**

## Owns

Stock on hand and reserved per SKU, reservations with expiry, the append-only stock movement history, the pincode directory and delivery zones.
Schema: `inventory`.

## Promises

- **Stock is never sold twice.** A reservation is one conditional database update per SKU that succeeds only if enough unreserved stock exists; database constraints make negative stock impossible.
- SKUs are always processed in sorted id order, so two reservations can never deadlock.
- A reservation call carries an idempotency key; repeating it returns the same result.
- Online-payment reservations hold for 30 minutes. order's expiry job decides what happens to its own orders; inventory's sweeper only releases `ACTIVE` reservations past their hold time plus a grace period, which catches reservations that never got an order.
- Every change to stock writes a movement row with a reason and actor.
- Admin receipts and adjustments go only through movements, and cannot push on-hand below reserved.
- Delivery estimates and cash on delivery availability come from the pincode and zone tables.

The full rule and state table: [../../design/high-level/data-model.md](../../design/high-level/data-model.md).

## Interface (planned)

`InventoryApi`: `reserve(orderId, lines, idempotencyKey, expiresAt)`; `commit(orderId)`; `release(orderId, idempotencyKey)`; `consume(orderId)` at shipping; `restock(orderId, lines, reason)` for returns; `availability(skuIds)` (batch); `deliveryEstimate(pincode)`.

## Endpoints (planned)

Public: `GET /api/v1/delivery-estimate?pincode=`, availability on product pages.
Admin: receipts, adjustments, movements and low stock under `/api/v1/admin/inventory/**`.

## Events

Publishes `StockLow`, `ReservationExpired`.
Consumes none: the order service calls inventory's interface at each order transition, so order stays the single owner of order state.

## Refuses

- A reservation larger than available stock.
- An adjustment that would make on-hand negative or below reserved.
- Direct edits to stock numbers without a movement.

## See also (do not follow recursively)

- [../order/README.md](../order/README.md) - the caller that drives reservations
