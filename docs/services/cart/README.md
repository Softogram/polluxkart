# cart

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slice S4.**

## Owns

Guest and signed-in carts, cart items, the merge of a guest cart on sign-in, and the wishlist.
Schema: `cart`.

## Promises

- A guest cart is identified by a random token in an httpOnly cookie; only its hash is stored.
- On sign-in, the guest cart merges into the account's cart, with quantities capped by stock and the per-item limit.
- The cart never stores a price it will charge. It remembers the price the shopper last saw only to show "price changed" notices.
- Each cart line shows current price, and flags for changed price, out of stock and archived product.
- Quantity per SKU is between 1 and 10.
- The wishlist requires sign-in.

## Interface (planned)

`CartApi`: get a cart's lines (SKU ids and quantities) for quoting; clear the lines that became an order.

## Endpoints (planned)

`GET /api/v1/cart`, `POST /api/v1/cart/items`, `PATCH /api/v1/cart/items/{skuId}`, `DELETE /api/v1/cart/items/{skuId}`; `GET/POST/DELETE /api/v1/wishlist`.

## Events

Consumes `UserRegistered` and sign-in to merge carts; consumes `OrderPlaced` to clear ordered lines.

## Refuses

- Quantities outside 1 to 10.
- Adding an archived or unpublished product.

## See also (do not follow recursively)

- [../order/README.md](../order/README.md) - where the cart becomes a quote
