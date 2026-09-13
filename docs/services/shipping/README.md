# shipping

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PROPOSED (2026-09-13), confirmed ticket by ticket. Built in slice S7.**

## Owns

Shipments, the courier list with tracking link templates, tracking numbers, and the provider seam for a shipping aggregator later.
Schema: `shipping`.

## Promises

- At launch shipping is manual: the shop books the courier, and an admin records the courier and tracking number when marking an order shipped (decided 2026-09-13).
- Tracking links are built from the courier's template and included in the shipped email.
- All shipping work goes through a `ShippingProvider` interface with a `ManualShippingProvider` implementation, so a Shiprocket adapter can be added without changing callers.

## Interface (planned)

`ShippingApi`: record a shipment for an order; mark delivered or returned to origin; get shipment details for an order.

## Endpoints (planned)

Shopper: shipment details inside `GET /api/v1/orders/{number}`.
Admin: couriers under `/api/v1/admin/shipping/couriers`, shipment actions through the order admin screens.

## Events

Publishes `ShipmentUpdated`.

## Refuses

- A shipment without a courier and tracking number.
- A second active shipment for the same order.

## See also (do not follow recursively)

- [../order/README.md](../order/README.md) - the order transitions that create shipments
