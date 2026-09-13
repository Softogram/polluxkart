# audit

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slice S1, used by every later slice.**

## Owns

The append-only record of every admin action and security-relevant event.
Schema: `audit`.

## Promises

- Every admin change (catalog, stock, orders, refunds, coupons, settings, users) and every security event (sign-in failures past a threshold, password reset, session revocation, role change, first-admin creation) is recorded with actor, action, entity, before and after values, request id and time.
- The running application's database role can insert audit rows but never update or delete them.
- Personal data in before and after values is limited to what an investigation needs.
- Admins can search the log; nobody can edit it.

## Interface (planned)

`AuditApi`: record an entry (also fed by events).

## Endpoints (planned)

Admin: `GET /api/v1/admin/audit` with filters.

## Events

Consumes the admin and security events published by other services.

## Refuses

- Any change or deletion of an existing entry.

## See also (do not follow recursively)

- [../../platform/security.md](../../platform/security.md) - what counts as security-relevant
