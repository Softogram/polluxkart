# E01-01, E01-02, E01-07 Retire the first version's server and publish the maintenance page

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Tickets: #40 (E01-01), #41 (E01-02) and #46 (E01-07), part of epic #11.
They share one document because one prepared script does #40 and #41 together, and #46 is the last step of the same clean-up.
Test plan: [../test/issue-40-41-46-legacy-teardown.md](../test/issue-40-41-46-legacy-teardown.md)

## Words used below

- **Server (EC2 instance):** the rented computer in AWS that ran the first version's backend. It was stopped on 2026-09-13.
- **Terminate:** permanently delete a server and its disk. It cannot be undone.
- **Snapshot:** a saved copy of a server's disk, from which a new server could be built.
- **Fixed public address (Elastic IP):** an internet address reserved for the account. Once released, it can be given to someone else and cannot be taken back.
- **DNS record:** the internet address book entry that turns a name, such as the old API's name, into an address.
- **Firewall rules (security group):** the list of which network connections a server accepts.
- **Key pair:** the login key used to reach the old server.
- **Website bucket:** the S3 storage holding the files polluxkart.com serves.
- **Versioning:** the bucket keeps earlier copies of changed or deleted files, so they can be restored.
- **CloudFront cache:** copies of the site that AWS keeps close to visitors; clearing it makes a change visible straight away.
- **Private operations reference:** the owner's private file, outside the repository, holding every account and resource id.

## What was already decided before this document

- **Rebuild instead of patching; nothing carried over from the old database** (owner decisions, 2026-09-13, [decisions.md](../../platform/decisions.md)).
- **The old server is stopped** (owner decision, 2026-09-13, "The old server is stopped").
- **How the first version is retired** (owner decision, 2026-09-14, "Retiring the first version", answered while planning these tickets):
  - E01 tickets follow the ticket process: a short plan, the owner's approval label, then the action, with the result recorded on the ticket;
  - the owner runs every step that needs AWS rights, in this session, and Claude prepares the steps and verifies the results with read-only checks;
  - the whole prepared script runs now: the server is retired and the maintenance page published together, and the contact card follows when #45 provides the details;
  - the server is terminated, with nothing copied out first;
  - the maintenance page keeps its wording, with no contact details until #45;
  - the snapshot is kept 30 days, until 2026-10-13, and a Google Calendar reminder is set for that date.

## What exists today (2026-09-14)

- The first version's server is stopped, with its disk, a fixed public address, firewall rules and a key pair.
- A complete snapshot of its disk was taken on 2026-09-13 and tagged with its deletion date.
- A DNS record still points the old API's name at the fixed address.
- polluxkart.com still serves the first version's app from the website bucket through CloudFront.
- The maintenance page is ready in `ops/maintenance/index.html`, and the script uses an identical copy (compared byte for byte on 2026-09-14).
- Every id is in the private operations reference, section 2, and in the script next to it.

## The change

### The script

The owner runs `bash ~/softogram/polluxkart-ops/legacy-teardown.sh` in this session (as `! bash ...`), so its output appears in the conversation.
It uses the AWS profile the private reference names for PolluxKart, and it is safe to run again: every step first checks whether its work is already done.

| Step | What it does | Can it be undone? |
|---|---|---|
| Preflight | Stops unless the AWS account is PolluxKart's, the snapshot is complete, and the maintenance page is present and has no reference to the old app builder | Nothing changed yet |
| 1 | Deletes the DNS record for the old API's name | Yes: the record can be recreated |
| 2 | Terminates the server; its disk is deleted with it | **No.** A new server could be built from the snapshot until it is deleted |
| 3 | Releases the fixed public address | **No.** The address may go to another AWS customer. Step 1 ran first, so the domain never points at it |
| 4 | Deletes the firewall rules and the key pair | Recreatable, but not needed |
| 5 | Turns on versioning for the website bucket, with earlier copies removed after 30 days | Yes |
| 6 | Uploads the maintenance page and removes the old site's files | Yes, for 30 days, because step 5 keeps the removed files as earlier copies |
| 7 | Clears the CloudFront cache and checks the site, the page text and that the old API name no longer resolves | Nothing changed |

The script stops at the first error (`set -e`), so a failure leaves the steps before it done and the rest untouched; running it again continues from there.

### Verification, by Claude, read-only

After the script, Claude checks each result independently with read-only commands and public requests, as listed in the test plan, and reports anything that does not match before the tickets move on.

### Recording the result

- **Private operations reference, section 2:** the date each resource was removed, and "pending" lines ticked. Claude edits it with the owner's agreement in the session.
- **Tickets #40 and #41:** a comment with the date and "done and verified", listing the checks by name only, with no ids. Then `stage: done`, and the tickets are closed as completed.
- **Decision log:** a dated entry "The old server is terminated" follows the 2026-09-13 "The old server is stopped" entry, and `docs/platform/runbook.md`, "Current state", says the server is retired and the maintenance page is live. These go in a small documents pull request that says `Plans #40`.

### #46: the snapshot, on or after 2026-10-13

- After #40 is done, Claude adds a Google Calendar event on 2026-10-13 titled "PolluxKart: delete the old server snapshot (#46)", with no ids in it.
- On or after that date, the owner deletes the snapshot with one command from the private reference, and Claude confirms with a read-only check that it no longer exists.
- #46 is then recorded and closed the same way as #40.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| The AWS profile points at a different account | The preflight stops before anything changes |
| The snapshot is not complete | The preflight stops |
| The DNS change takes a while | Step 1 waits for Route 53 to confirm the change before continuing |
| The firewall rules cannot be deleted yet, because the server's network card is still detaching | Step 4 retries for about two and a half minutes, then warns; running the script again finishes it |
| The bucket already has lifecycle rules | Step 5 leaves them unchanged and says so; the owner checks them |
| The page is not visible straight after step 7 | DNS and caches can take up to about five minutes; the verification is repeated |
| Something turns out to be needed from the old server | Until 2026-10-13, a new server can be built from the snapshot, by a new ticket |
| The old site must come back urgently | Until 30 days after step 6, the earlier file copies can be restored in the bucket, by a new ticket |
| Someone visits an old deep link, such as a product page | CloudFront already sends missing pages to `index.html`, so they see the maintenance page |

## What is deliberately not covered

- **The contact card:** added when #45 provides the business details.
- **Replacing the deploy key and the other account security work:** #42 and #44.
- **The old media bucket, unused certificates and the CloudFront setup itself:** later tickets (Phase 3 and E19-07).
- **Copying anything off the old server:** the owner chose not to.

## Open questions for the owner

None open.
All questions these tickets and their epic raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Retiring the first version".
