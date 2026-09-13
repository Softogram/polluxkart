# promotion

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slice S9.**

## Owns

Coupons, their limits and validity windows, and redemptions.
Schema: `promotion`.

## Promises

- A coupon is validated and its discount computed only on the server, from the current cart, never from a total the browser sends.
- Total and per-user limits are enforced under a row lock when an order is placed, so parallel orders cannot exceed a limit.
- A redemption is tied to exactly one order; cancelling that order before shipping returns the redemption.
- Discounts never make a total negative, and respect a maximum discount when set.
- The discount appears on the quote and on the invoice.

## Interface (planned)

`PromotionApi`: evaluate a coupon for a set of lines and a user; redeem for an order with an idempotency key; release a redemption for a cancelled order.

## Endpoints (planned)

The shopper applies a coupon through `POST /api/v1/checkout/quote`.
Admin: coupons under `/api/v1/admin/promotions/**`.

## Events

None published.

## Refuses

- Expired, not-yet-started, exhausted or per-user-exhausted coupons.
- Orders below the coupon's minimum value.

## See also (do not follow recursively)

- [../order/README.md](../order/README.md) - where discounts enter the quote
