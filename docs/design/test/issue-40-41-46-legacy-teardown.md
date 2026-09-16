# Test plan: E01-01, E01-02, E01-07 Retire the first version's server and publish the maintenance page

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Tickets: #40, #41 and #46.
Design: [../low-level/issue-40-41-46-legacy-teardown.md](../low-level/issue-40-41-46-legacy-teardown.md)

These tickets change live accounts, not code, so the "tests" are checks run once, before and after the action, by someone other than the script.
Terms such as terminate, snapshot, fixed public address and versioning are explained at the top of the design.

## How these checks run

- **Before:** Claude runs read-only checks and confirms the starting state matches the private reference, so the script is aimed at the right things.
- **During:** the owner runs the script; its own preflight and step messages are the first evidence.
- **After:** Claude runs independent read-only checks. A check is never "the script said so": each is a separate command or public request.
- Results go to the tickets as pass or fail by check name, and ids stay in the private reference.
- AWS reads use the PolluxKart profile named in the private reference, which can read all of these resources.

## Before the script

| Id | Check | Expected |
|---|---|---|
| B1 | The AWS account the profile signs in to | PolluxKart's account |
| B2 | The old server's state | Stopped |
| B3 | The safety snapshot | Completed, with its deletion date tag |
| B4 | The DNS record for the old API name | Present, pointing at the fixed address |
| B5 | `https://polluxkart.com` | Serves the first version's app |
| B6 | The script's maintenance page and `ops/maintenance/index.html` | Identical |

If any of these differs, stop and ask the owner before running anything.

## After the script

| Id | Check | Expected | Ticket |
|---|---|---|---|
| A1 | The old API name looked up in public DNS | No address returned (retry for up to five minutes) | #40 |
| A2 | The old server's state | Terminated | #40 |
| A3 | The fixed public address in the account | No longer allocated | #40 |
| A4 | The firewall rules and the key pair | Neither exists | #40 |
| A5 | The safety snapshot | Still exists and completed, with its deletion date | #40, #46 |
| A6 | Website bucket versioning | Enabled | #41 |
| A7 | Website bucket lifecycle rules | Earlier file copies expire after 30 days (or existing rules noted for the owner) | #41 |
| A8 | Website bucket current files | Only `index.html` | #41 |
| A9 | `https://polluxkart.com` | Status 200; contains "We are rebuilding our store"; no reference to the old app builder; has the `noindex, nofollow` robots tag | #41 |
| A10 | `https://www.polluxkart.com` | The same page | #41 |
| A11 | A deep link from the old site, such as `https://polluxkart.com/products` | The same page | #41 |
| A12 | The served page compared with `ops/maintenance/index.html` | Identical | #41 |
| A13 | No other EC2 servers exist in any region | None, matching the private reference's 2026-09-13 scan | #40 |

**Passing partner.** B2, B4 and B5 show the old state existed before the script, so A1, A2 and A9 passing means the script changed something, not that the checks look at nothing.

## #46, on or after 2026-10-13

| Id | Check | Expected |
|---|---|---|
| S1 | Before deleting: the snapshot | Exists, completed, the only snapshot of the old disk |
| S2 | After the owner deletes it | It no longer exists |
| S3 | The Google Calendar event | Exists on 2026-10-13, titled with #46, with no ids |

## When a step fails

| Failure | What to do |
|---|---|
| The preflight stops | Nothing changed; read the message, fix the cause with the owner, run again |
| A step stops part-way | Run the checks for the steps before it, then run the script again; it skips finished steps |
| A9 fails after five minutes | Check A8 and whether the cache clearing completed; rerun step 7 by running the script again |
| A1 still resolves after five minutes | Check the record is gone in Route 53 itself; public resolvers may cache longer, so recheck later before closing #40 |
| A7 shows lifecycle rules that were already there | Show them to the owner; do not change them without asking |

## Acceptance criteria and the checks that prove them

| Acceptance criterion | Checks |
|---|---|
| #40: the server is terminated, its fixed address released and its API DNS record removed | A1 to A4, A13 |
| #40: the snapshot remains as the only copy until #46 | A5 |
| #41: polluxkart.com shows the maintenance page, with no third-party builder scripts and not indexed | A8 to A12 |
| #41: the old site's files are recoverable for 30 days | A6, A7 |
| #46: the snapshot is deleted after its retention date, with a reminder | S1 to S3 |

## What is deliberately not covered, and why

- **Checking the old site's files can really be restored:** restoring would put the broken app back online; A6 and A7 prove the mechanism is on.
- **Building a server from the snapshot:** it would recreate the old server and its secrets; A5 proves the snapshot is intact.
