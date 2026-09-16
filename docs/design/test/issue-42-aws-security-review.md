# Test plan: E01-03 AWS account security review

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-15)**
Ticket: #42.
Design: [../low-level/issue-42-aws-security-review.md](../low-level/issue-42-aws-security-review.md)

This ticket changes the live AWS account, not code, so the "tests" are checks run once, before and after the action, by someone other than the person clicking in the console.
Terms such as root account, MFA, IAM user, access key, CloudTrail and GuardDuty are explained at the top of the design.

## How these checks run

- **Before:** Claude runs read-only checks and confirms the starting state, so the owner is aimed at the right account.
- **During:** the owner runs each step; the console or command output is the first evidence.
- **After:** Claude runs independent read-only checks. A check is never "the console said so": each is a separate read.
- **A second look, on a later day:** Claude repeats A2, A3, A4 and A6, so nothing was switched back.
- Results go to the ticket as pass or fail by check name, and ids stay in the private reference.
- AWS reads use the PolluxKart profile named in the private reference.

## Before the changes

| Id | Check | Expected |
|---|---|---|
| B1 | The AWS account the profile signs in to | PolluxKart's account |
| B2 | Whether the root account has MFA | Recorded privately as on or off, and which kind |
| B3 | Whether the root account has access keys | Recorded privately as none, or a count |
| B4 | The list of IAM users and access keys | Recorded privately, with last-used dates from the IAM credential report |
| B5 | Whether GuardDuty is on in Mumbai | Recorded privately as on or off |
| B6 | The email AWS already has for the account | Matches the private reference; the address is never written in this repository |

If B1 or B6 differs, stop and ask the owner before changing anything.

## After the changes

| Id | Check | Expected |
|---|---|---|
| A1 | The AWS account the profile signs in to | Still PolluxKart's account |
| A2 | Root MFA | On, authenticator app, unless it was already a hardware key (then keep that) |
| A3 | Root access keys | None |
| A4 | IAM console users | Only the owner. Any other console user is disabled or gone |
| A5 | Remaining access keys | Each has a one-line purpose in the private reference |
| A6 | GuardDuty in Mumbai | On |
| A7 | GuardDuty findings destination | The email already on the AWS account, matching the private reference |
| A8 | CloudTrail Event history | Was reviewed; unexpected findings were raised with the owner the same day, or none were found |
| A9 | `docs/platform/runbook.md` | A dated line that the review was done, with no ids and no findings |

**Passing partner.** B2, B3, B4 and B5 show the old state, so A2, A3, A4 and A6 passing means something changed, or was already correct and recorded.

## Second look, on a later day

| Id | Check | Expected |
|---|---|---|
| S1 | Root MFA | Still on |
| S2 | Root access keys | Still none |
| S3 | IAM console users | Still only the owner |
| S4 | GuardDuty in Mumbai | Still on |

## When a step fails

| Failure | What to do |
|---|---|
| B1 fails | Nothing changed; fix the profile with the owner, then start again |
| An IAM user has no clear purpose | Do not delete it; ask the owner |
| A8 finds unexpected activity | Stop remaining changes; tell the owner the same day; keep detail privately |
| A7 does not match the private reference | Do not add a new email; ask the owner |
| S1 to S4 fail on the later day | Tell the owner the same day; do not assume a later ticket will notice |

## Acceptance criteria and the checks that prove them

| Acceptance criterion | Checks |
|---|---|
| The root account has a second sign-in step and no access keys | A2, A3, S1, S2 |
| Every remaining IAM user and access key has a named purpose, recorded privately | A4, A5, S3 |
| The activity log was reviewed, and anything unexpected was raised with the owner | A8 |
| Threat detection matches the owner's answer (on now) | A6, A7, S4 |
| runbook.md carries a dated note that the review was done | A9 |

## What is deliberately not covered, and why

- **A unit test in CI:** this work is in a live account, not in `api/` or `web/`.
- **Proving an attack would be detected:** that would mean simulating an attack on the live account; A6 only proves GuardDuty is on.
- **The budget alert:** that is #43.
- **Writing the IAM credential report into git:** it contains live identifiers.
