# notification

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PROPOSED (2026-09-13), confirmed ticket by ticket. Built in slice S1, extended by later slices.**

## Owns

Email templates, the email outbox, sending through AWS SES, and handling bounces and complaints.
Schema: `notification`.

## Promises

- Other services never send email directly; they call `NotificationApi` after their own change commits, and notification writes an outbox row with a unique dedupe key, so a repeated call sends one email.
- A scheduled job sends pending emails with retries and backoff, guarded by a lock so it never runs twice at once.
- Bounces and complaints reported by SES (through a signature-verified notification) add the address to a suppression list, and suppressed addresses are never emailed again.
- Templates escape every value, so a name or address cannot inject HTML.
- Locally, email goes to a fake inbox; in production, through SES using the server's role, with no stored keys.
- Email bodies and recipients never appear in logs.

## Interface (planned)

`NotificationApi`: enqueue an email from a template, recipient and data, with a dedupe key.

## Endpoints (planned)

`POST /api/v1/webhooks/ses` (SES bounce and complaint notifications, signature-verified).

## Events

None consumed. notification depends on no other service, so it cannot listen to their events.
identity, order, payment, invoice and review call `NotificationApi` from their own after-commit listeners, with a dedupe key.

## Refuses

- Sending to a suppressed address.
- Sending the same dedupe key twice.

## See also (do not follow recursively)

- [../identity/README.md](../identity/README.md) - security emails
