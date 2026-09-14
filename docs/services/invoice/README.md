# invoice

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PROPOSED (2026-09-13), confirmed ticket by ticket. Built in slice S8.**

## Owns

The store's tax settings (legal name, GSTIN, address, state, invoice prefix, signature), GST invoices, credit notes, financial-year number sequences, invoice PDFs, and the GSTR-1 export.
Schema: `invoice`.

## Promises

- An invoice is issued when an order is shipped, because GST requires it when goods leave. order asks for it just before saving the `SHIPPED` state; the call is safe to repeat and always returns the one invoice for that order.
- Numbers run without gaps within each financial year (1 April to 31 March, decided in `Asia/Kolkata` time), taken by locking that year's sequence row in the same transaction that writes the invoice.
- The number format is short enough for GST's 16-character limit, for example `PK/26-27/000123`.
- Each invoice carries every field GST Rule 46 requires, from snapshots taken at issue time, so later changes to settings, products or addresses never alter an issued invoice.
- Invoices are never edited; cancellations and returns after invoicing produce credit notes with their own sequence.
- The PDF is rendered from a template, stored in a private S3 bucket with its hash, and downloaded only through an endpoint that checks the order belongs to the caller.
- Invoices are kept for the GST retention period even when the shopper deletes their account.
- A chartered accountant signs off sample invoices before launch.

## Interface (planned)

`InvoiceApi`: issue an invoice for a shipped order (idempotent per order); issue a credit note for an order with a reason; get invoice metadata for an order.

## Endpoints (planned)

`GET /api/v1/orders/{number}/invoice` (owner only).
Admin: store settings, invoices, credit notes and GSTR-1 export under `/api/v1/admin/invoices/**`.

## Events

Publishes `InvoiceIssued`, `CreditNoteIssued`.

## Refuses

- Issuing a second invoice for the same order.
- Editing an issued invoice.
- Downloading an invoice for an order the caller does not own.

## See also (do not follow recursively)

- [../../product/compliance.md](../../product/compliance.md) - the legal requirements
