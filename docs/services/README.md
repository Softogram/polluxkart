# Services

One folder per backend service, each holding what that service owns, promises and refuses.
[platform/architecture.md](../platform/architecture.md) summarizes how they fit together; these folders are where each service's rules live.

Parent: [docs/](../README.md)

**Status: PROPOSED (2026-09-13). No service code exists yet. Each service's details are confirmed in its tickets.**
Every service follows [../design/high-level/service-boundaries.md](../design/high-level/service-boundaries.md): its own Maven module, its own interface, its own database schema, no access to any other service's internals.

## Read next

- [identity/](identity/README.md) - accounts, email verification, password reset, Google sign-in, sessions, addresses, admin two-step codes, consent and data requests
- [catalog/](catalog/README.md) - categories, specification fields, brands, products, SKUs, specifications, search
- [media/](media/README.md) - image uploads, file type checks, image records
- [inventory/](inventory/README.md) - stock per SKU, reservations, stock movements, pincode serviceability
- [cart/](cart/README.md) - guest and signed-in carts, cart merge, wishlist
- [order/](order/README.md) - the checkout quote, the tax engine, orders and the order state machine
- [payment/](payment/README.md) - Razorpay payments, webhooks, refunds, reconciliation
- [invoice/](invoice/README.md) - GST invoices, credit notes, financial-year numbering, GSTR-1 export
- [shipping/](shipping/README.md) - shipments, couriers, tracking, the provider seam
- [promotion/](promotion/README.md) - coupons, limits, redemptions
- [review/](review/README.md) - verified-purchase reviews, moderation, rating summaries
- [notification/](notification/README.md) - email templates, the outbox, SES, bounces
- [audit/](audit/README.md) - the append-only record of admin and security actions

## See also (do not follow recursively)

- [../design/high-level/data-model.md](../design/high-level/data-model.md) - every table in every schema
- [../design/low-level/README.md](../design/low-level/README.md) - per-issue designs that build these

## Matching code (planned)

Each service will be a Maven module under `api/<service>/`, and its README there will point back here.
