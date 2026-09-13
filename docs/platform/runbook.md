# Runbook

Parent: [platform/](README.md) | Index: [docs/](../README.md)

**Status: CURRENT STATE as of 2026-09-13.**
Operating the store: where it stands today, where private details live, and what to do when something breaks.
Sections for the rebuilt system are filled in as each part ships.

## Current state (2026-09-13)

- The store is in maintenance: polluxkart.com shows a static page and takes no orders.
- The first version's backend server is being retired, and its API address removed from DNS.
- No rebuilt service is deployed yet.

## Where private operational details live

This repository is public.
Account ids, resource ids, DNS records, the status of any credential, and step-by-step infrastructure changes are kept in a private operations reference on the owner's machine, outside every git repository:

`~/softogram/POLLUXKART_OPERATIONS.md`

It is not backed up by git, so it must be kept current the same day anything changes.
Never copy its contents into this repository.

## Publishing or updating the maintenance page

Follow `ops/maintenance/README.md` in the repository.

## Handling secrets

- Development keys go only in a local `.env`, which git ignores.
- Server secrets go only in AWS SSM Parameter Store.
- If a secret is ever pasted into git, a document, a chat, a ticket or a log, rotate it the same day, then record the rotation in the private operations reference.

## When something breaks (to be completed as systems ship)

Each entry will say how to notice it, how to confirm it, and what to do.

| Situation | Where the steps will live |
|---|---|
| Site down or health check failing | Deploy and rollback steps, Phase 3 |
| A deploy made things worse | `make rollback`, Phase 3 |
| Database problem or data loss | Restore drill, Phase 6 |
| Payments stuck or webhook signature failures | Payment reconciliation, slice S6 |
| Emails bouncing | SES bounce handling, slice S1 |
| Suspected security incident or data breach | Incident and breach runbook, Phase 6 |
| Daily shop operations for the owner's family | Packing, shipping, cash on delivery, refunds, Phase 6 |

## See also (do not follow recursively)

- [../design/high-level/infrastructure.md](../design/high-level/infrastructure.md) - environments, deploys, backups
- [security.md](security.md) - the rules for secrets and personal data
