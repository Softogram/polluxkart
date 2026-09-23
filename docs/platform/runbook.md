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

## Branch rulesets

The files in `.github/rulesets/` are the source of truth.
Apply them from a clone with an admin GitHub login.
Do not apply `main` or `main-owner-merge` until `main` already contains the approval gate.

First apply after the ruleset files merge into `development`:

```
make rulesets-apply RULESETS=development
make rulesets-check
```

That also writes the four repository merge settings (squash on, merge commits on, rebase off, "Update branch" on).
`main` rulesets are still missing then, which is expected.

After the first release pull request from `development` into `main` has merged:

```
make rulesets-apply RULESETS="main main-owner-merge"
make rulesets-check
```

Later rule changes: open a pull request, merge it, then apply the named rulesets that changed.
`make rulesets-apply` with no `RULESETS` applies all three; do not use that until `main` is ready.
`make rulesets-apply-dry-run` prints the planned writes and changes nothing.

A red `rulesets-drift` workflow means GitHub no longer matches the files, except hidden bypass lists, which that job cannot see.
Either someone edited a ruleset in the website, or a merged change has not been applied yet.
Run `make rulesets-check` with an admin login to compare bypass lists too, then apply if the files are right.

In a genuine emergency the owner can switch a ruleset's enforcement off in GitHub settings, merge, and switch it on again. The next drift run will show the gap if it is left off.

GitHub pauses scheduled workflows on a public repository after 60 days without activity in it.

## Handling secrets

- Development keys go only in a local `.env`, which git ignores.
- Server secrets go only in AWS SSM Parameter Store.
- If a secret is ever pasted into git, a document, a chat, a ticket or a log, rotate it the same day, then record the rotation in the private operations reference.

What to do when a scan finds something, by where it was caught:

| Where it was caught | It is a real secret | It is a false alarm |
|---|---|---|
| Pre-commit hook | Remove it from the file and unstage it. No commit exists, so no rotation is needed | Add an allow-list entry to `.gitleaks.toml` with a dated reason, in the same pull request |
| `make ci` | It is already in a commit, so rotate it the same day, record the rotation in the private operations reference, and remove it in a new commit | Allow-list entry with a dated reason |
| GitHub push protection | Do not bypass; remove it. If it was bypassed, it reached GitHub, so rotate the same day | Bypass with "false positive", then add an allow-list entry so gitleaks agrees |
| A GitHub secret scanning alert (the owner's email) | Rotate the same day, then close the alert as revoked | Close the alert as a false positive, with the reason |

Removing a secret in a later commit does not undo the leak: the earlier commit stays readable on GitHub.
Rewriting history to hide it is forbidden here and would not help, because forks and caches keep it.
Full details: [tools/secrets/README.md](../../tools/secrets/README.md).

## Dependency updates and code scanning

Dependabot opens one grouped pull request per ecosystem every Monday morning, and a separate one as soon as a vulnerability is published for a dependency in use.

- **Only the owner merges a Dependabot pull request.** Check `make ci` passed, read what changed, then merge.
- **A grouped pull request that breaks a check** is closed, or split by commenting `@dependabot ignore <dependency>` so the rest can go in. Do not merge it red.
- **A security update needing a new major version** still arrives, because a known hole outweighs an upgrade surprise. It gets the same checks.
- **A CodeQL alert** appears in the Security tab from the weekly or release run, not from a pull request. Fix it, or dismiss it with a reason starting with today's date.
- **An alert under `legacy/`** is dismissed with reason "not used" (Dependabot) or "won't fix" (CodeQL) and the comment "YYYY-MM-DD: legacy/ is the first version, kept as reference and never deployed". `legacy/` is not scanned by CodeQL, so only older alerts and Dependabot alerts appear.

Applying the settings, with an admin login, after the files merge:

```
make rulesets-apply RULESETS=development
make rulesets-check
```

That turns CodeQL default setup off. It must be off before the `codeql` workflow can upload results, because GitHub refuses results from advanced setup while default setup is on.

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
