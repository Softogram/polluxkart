# PolluxKart

<div align="center">
  <img src="legacy/frontend/public/logo192.svg" alt="PolluxKart logo" width="80" height="80">

  **An online electronics store for a family business in India.**
</div>

## Status: rebuild in progress

The first version of this store was generated with an AI app builder in early 2026.
An audit in September 2026 found it was not safe to run with real money and real customers.
We are rebuilding it properly, in the open.

While the rebuild happens, polluxkart.com shows a maintenance page and takes no orders.

## What we are building

- **Storefront:** electronics catalog with specs, brands, filters and compare; cart; checkout with Razorpay (an Indian payment gateway) and cash on delivery; GST tax invoices; order tracking.
- **Admin:** products, stock, orders, fulfilment, coupons and reviews.

The planned stack:

- **Backend:** Java 25 and Spring Boot 4.1 with PostgreSQL 18.
  The backend is split into independent services (identity, catalog, inventory, orders, payments, invoices and more) that live in this one repository and run together at launch.
  Each service talks to the others only through a defined interface, so any one of them can later be moved to its own server.
- **Frontend:** Next.js with TypeScript, rendered on the server so product pages load fast and show up well in search and link previews.
- **Hosting:** AWS in Mumbai.

## Repository layout

| Folder | What it holds |
|---|---|
| `legacy/` | The first version, kept only as reference. Not built or deployed. See [`legacy/README.md`](legacy/README.md). |
| `docs/legacy/` | The audit of the first version and the feature checklist the rebuild must match. |
| `ops/maintenance/` | The maintenance page shown at polluxkart.com during the rebuild. |

More folders (`api/`, `web/`, `infra/`, `e2e/`) arrive as the rebuild progresses.

## Read next

- [`docs/legacy/audit-2026-09.md`](docs/legacy/audit-2026-09.md): what went wrong in the first version, and the rule we follow now for each problem.
- [`docs/legacy/parity-checklist.md`](docs/legacy/parity-checklist.md): features the rebuild must cover before the old code is deleted.

## Reporting a security problem

Please do not open a public issue.
Email the maintainer through the contact address on the GitHub profile of the repository owner instead.

## License

MIT
