# order

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slices S5 and S7.**

## Owns

The checkout quote, the GST tax engine, orders and order items, order status history, the order state machine, and idempotency keys for order actions.
Schema: `orders` (`order` is a reserved word in SQL).

## Promises

- **One source of totals.** `POST /api/v1/checkout/quote` computes prices, discount, shipping, GST split and total from current data; the frontend only displays it.
- **No surprise charges.** Placing an order sends the total the shopper saw; if it differs from a fresh quote, the order is refused with `409 price_changed` and the new quote.
- **One order per attempt.** Placing an order requires an `Idempotency-Key`; repeating it returns the same order.
- **Stock before saving.** The order service asks inventory to reserve, then saves the order; if saving fails, it releases the reservation, and expiry is the safety net.
- **Snapshots.** Each order item keeps the product name, variant, HSN code, GST rate, MRP and price it was sold at, and the order keeps the delivery address as it was.
- **Tax engine.** A pure function: prices include GST; taxable value and tax per line; CGST and SGST for same-state delivery, IGST otherwise; deterministic paisa rounding. Rules and worked examples: [../../design/high-level/data-model.md](../../design/high-level/data-model.md).
- **State machine.** Every status change goes through one transition table; illegal moves are refused with `409 illegal_transition`; every accepted change writes history and audit. See [../../design/high-level/order-lifecycle.md](../../design/high-level/order-lifecycle.md).
- **Cash on delivery rules.** Verified email, maximum order value, serviceable pincode, cap on open cash on delivery orders.
- **Ownership.** A shopper can see and act only on their own orders.

## Interface (planned)

`OrderApi`: order snapshots for review (who received which product).

order is the orchestrator: it calls inventory, payment, cart, shipping, invoice, promotion, catalog, identity, notification and audit, and listens to payment's events.
No other service calls order except review, which listens to `OrderDelivered`.
It runs the payment expiry job: for orders past their payment hold, it asks payment for the latest status, then confirms or cancels.

## Endpoints (planned)

`POST /api/v1/checkout/quote`; `POST /api/v1/orders`; `GET /api/v1/orders`, `/orders/{number}`; `POST /api/v1/orders/{number}/payments`, `/payments/verify`, `/cancellation`, `/return-requests`.
Admin: list with filters, pack, ship, deliver, record cash collected, cancel, accept or reject returns under `/api/v1/admin/orders/**`.

## Events

Publishes `OrderPlaced`, `OrderConfirmed`, `OrderPacked`, `OrderShipped`, `OrderDelivered`, `OrderCancelled`, `OrderReturned`.

## Refuses

- An order whose expected total does not match a fresh quote.
- An order without an idempotency key.
- Any transition not in the table.
- Cancelling after packing (shoppers) or after shipping (anyone).
- Reading or acting on another shopper's order.

## See also (do not follow recursively)

- [../payment/README.md](../payment/README.md) - how online orders get confirmed
- [../invoice/README.md](../invoice/README.md) - what happens at shipping
