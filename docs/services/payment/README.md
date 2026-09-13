# payment

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slice S6.**

## Owns

Razorpay orders and payment attempts, webhook events, refunds, and reconciliation of payments that got stuck.
Schema: `payment`.

## Promises

- The Razorpay order amount always comes from the order's total on the server, never from the browser.
- Calls to Razorpay happen outside any database transaction, with explicit time limits.
- Every payment attempt for an order is its own row, so retries never overwrite history.
- **Verification** checks the HMAC signature of the order and payment ids in constant time, then fetches the payment from Razorpay and confirms amount, currency (INR) and captured status before telling the order service.
- **Webhooks** check the signature over the exact raw bytes received, store the event with its provider event id (unique), and do nothing on a repeat.
- Whichever arrives first, the browser's verification or the webhook, the order ends in the same state.
- A reconciliation job asks Razorpay about attempts stuck for more than 30 minutes.
- A capture that arrives after the order was cancelled re-reserves stock if possible, otherwise refunds automatically.
- Before creating a refund, existing refunds for the payment are checked, so a retried request never refunds twice.
- Missing Razorpay configuration stops the application from starting; checks are never skipped.
- Keys live only in a local `.env` for development and in AWS SSM Parameter Store on servers.

## Interface (planned)

`PaymentApi`: create a payment attempt for an order; refund a captured payment for an order with an idempotency key; get payment status for an order.

## Endpoints (planned)

`POST /api/v1/payments/razorpay/orders` (for an order the caller owns), `POST /api/v1/payments/razorpay/verify`; `POST /api/v1/webhooks/razorpay` (signature-verified, CSRF-exempt).
Admin: payment and refund details under `/api/v1/admin/payments/**`.

## Events

Publishes `PaymentCaptured`, `PaymentFailed`, `RefundProcessed`, `PaymentAmountMismatch`.

## Refuses

- A verification whose signature fails or whose fetched amount differs from the order total; the mismatch is flagged for an admin, and the order is not confirmed.
- A webhook with an invalid signature.
- Creating a payment for someone else's order, or for an order not awaiting payment.

## See also (do not follow recursively)

- [../../design/high-level/order-lifecycle.md](../../design/high-level/order-lifecycle.md) - payment status and order status together
