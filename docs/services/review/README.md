# review

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PROPOSED (2026-09-13), confirmed ticket by ticket. Built in slice S9.**

## Owns

Product reviews from verified buyers, moderation, and per-product rating summaries.
Schema: `review`.

## Promises

- Only a shopper who bought and received the product can review it, one review per product per shopper.
- Reviews are published after moderation.
- Rating summaries count only published reviews.
- No review, rating or rating breakdown is ever invented; a product with no reviews shows none (the first version showed fake ones).
- Structured data for search engines includes a rating only when real published reviews exist.

## Interface (planned)

`ReviewApi`: rating summaries for products (batch).

## Endpoints (planned)

`GET /api/v1/products/{slug}/reviews`, `POST /api/v1/products/{slug}/reviews`.
Admin: moderation under `/api/v1/admin/reviews/**`.

## Events

Publishes `ReviewPublished`.
Consumes `OrderDelivered` to know who may review.

## Refuses

- Reviews from shoppers who have not received the product.
- A second review of the same product by the same shopper.
- Ratings outside 1 to 5.

## See also (do not follow recursively)

- [../../product/compliance.md](../../product/compliance.md) - why fake reviews are a legal problem
