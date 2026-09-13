# catalog

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slice S2.**

## Owns

Categories and the specification fields each category uses, brands, products, SKUs (sellable variants such as 128 GB black), specification values, product images (as references to media), and product search.
Schema: `catalog`.

## Promises

- The selling price of a SKU is never above its MRP; the database enforces it.
- Every product has an HSN code, a GST rate in basis points, country of origin and manufacturer or importer before it can be published.
- Specification fields are defined per category, with a type, unit and group, and flags for filterable, comparable and variant axis.
- Listing with filters (brand, price, filterable specifications) runs a fixed number of queries no matter how many products or categories exist.
- Search uses PostgreSQL full-text search plus trigram similarity, always with bound parameters.
- Changing a published product publishes an event so cached storefront pages refresh.

## Interface (planned)

`CatalogApi`: get SKUs by ids (batch) with current price, MRP, tax details and product snapshot fields; check a product is published; list products for the sitemap.

## Endpoints (planned)

Public: `GET /api/v1/categories`, `/categories/{slug}/products` with filters, `/products/{slug}`, `/brands`, `/brands/{slug}`, `/search`, `/compare?skus=`.
Admin: categories, specification fields, brands, products, SKUs and publishing under `/api/v1/admin/catalog/**`.

## Events

Publishes `ProductPublished`, `ProductChanged`, `ProductArchived`, `PriceChanged`.
Consumes `MediaFinalized` to attach ready images.

## Refuses

- Publishing a product missing any legally required field.
- A price above MRP or a GST rate outside 0 to 40 percent.
- Hard-deleting a product that has ever been sold; products are archived instead.

## See also (do not follow recursively)

- [../media/README.md](../media/README.md) - where product images come from
- [../../design/high-level/design-system.md](../../design/high-level/design-system.md) - how products are shown
