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

## Board sync GitHub App

The `board-sync` workflow moves cards on the PolluxKart project board to match each ticket's stage label.
GitHub's built-in workflow token cannot change an organisation project, so this uses a GitHub App.

### Create the App (once)

1. In the Softogram organisation, create a GitHub App named `polluxkart-board-sync`.
2. Permissions: repository Issues read and write, Metadata read; organisation Projects read and write. Webhooks off.
3. Install it only on `Softogram/polluxkart`.
4. Store the App's id as the Actions variable `BOARD_SYNC_APP_ID`, and its private key as the Actions secret `BOARD_SYNC_PRIVATE_KEY`.
5. Record the App id and the date the key was created in the private operations reference, never in this repository.

### Rotate the key

Create a new private key on the App, put it in `BOARD_SYNC_PRIVATE_KEY`, then delete the old key on the same day. Record the rotation privately.

### A red `board-sync` run

Open the failed run. If the token step failed, the App is missing, uninstalled, or the key is wrong. If the script step failed, it names the ticket and the problem (no stage label, two stage labels, or "re-apply the approval by hand"). Fix that ticket's labels; the next event or the nightly run will retry. Installation tokens expire within an hour and are not stored.

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
