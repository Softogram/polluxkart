# Test plan: E01-05 Retire the credentials used by the first version

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-16)**
Ticket: #44.
Design: [../low-level/issue-44-retire-first-version-credentials.md](../low-level/issue-44-retire-first-version-credentials.md)

This ticket changes live logins, not code, so the "tests" are checks run once, before and after the action.
Terms such as credential, revoke and private inventory are explained at the top of the design.
No check output in git, a ticket or chat may contain a secret value or a live-or-dead status for a named key.

## How these checks run

- **Before:** Claude and the owner confirm the private inventory is complete, from `legacy/` and the owner's logins.
- **During:** the owner runs each step; the provider's response is the first evidence.
- **After:** Claude runs independent read-only checks on the rebuild's configuration, and the owner confirms each inventory line.
- **A second look, on a later day:** Claude repeats the rebuild-config search and the owner re-reads any line that was "in progress".
- Results go to the ticket as pass or fail by check name only.

## Before the changes

| Id | Check | Expected |
|---|---|---|
| B1 | The private inventory against `legacy/` (payment gateway, Firebase, image hosting, and any other outside login) | Every kind of outside account found in `legacy/` has a line. Missing lines are added before anything is revoked |
| B2 | The rebuild outside `legacy/` | Recorded privately: which inventory credentials, if any, still appear in `.env` or config the rebuild uses |

If B1 is incomplete, stop and finish the inventory first.

## After the changes

| Id | Check | Expected |
|---|---|---|
| A1 | Payment-gateway keys on the first version's merchant account | A harmless request using each old key is refused. The account is still there for records |
| A2 | First version's Firebase project | Gone, or in Google's deletion grace period with deletion already requested |
| A3 | Every other inventory line | Closed, or keys replaced and the account kept, or marked "not ours to rotate", with a date |
| A4 | Rebuild configuration outside `legacy/` | None of the inventory's credentials |
| A5 | The owner has read every inventory line | Confirmed in the session |
| A6 | `docs/platform/runbook.md` | A dated line that the first version's credentials were retired, with no names |
| A7 | This issue | No credential names, values or status |

**Passing partner.** B2 shows whether the rebuild was still holding an old key, so A4 passing after a "found" start means it was removed.

## Second look, on a later day

| Id | Check | Expected |
|---|---|---|
| S1 | Rebuild configuration outside `legacy/` | Still none of the inventory's credentials |
| S2 | Any line that was "deletion requested" | Deletion finished, or still in grace period with a date to look again |

## When a step fails

| Failure | What to do |
|---|---|
| B1 missing a service found in `legacy/` | Add the line; do not revoke anything else until the list is complete |
| A1 still accepts an old key | Disable it again; do not tick the line |
| Cannot sign in to the payment-gateway account | Recover from the registered email; do not skip |
| A4 finds a first-version key in the rebuild | Remove it the same day; rotate if it was still live |
| A7 would need a status on the public issue | Put that status only in the private reference |

## Acceptance criteria and the checks that prove them

| Acceptance criterion | Checks |
|---|---|
| Every inventory line is revoked, rotated, closed, or not ours, with a date | A1, A2, A3, A5 |
| No first-version credential is in the rebuild's configuration | A4, S1, B2 |
| Firebase is handled as the owner answered | A2, S2 |
| This issue contains no credential names, values or status | A7 |

## What is deliberately not covered, and why

- **A unit test in CI:** secrets must not be fixtures in the public repository.
- **Proving git history no longer contains the secret:** history is public and is not rewritten. A1 is what makes a leaked copy useless.
- **AWS keys:** #42.
