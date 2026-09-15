# E01-03 AWS account security review

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-15)**
Ticket: #42 (E01-03), part of epic #11.
Test plan: [../test/issue-42-aws-security-review.md](../test/issue-42-aws-security-review.md)

This ticket changes the live AWS account, not application code.
Sensitive details stay in the private operations reference.

## Words used below

- **Root account:** the original AWS login that can do anything in the account.
- **MFA (multi-factor authentication):** a second proof besides the password, here an authenticator app that shows a changing six-digit code.
- **IAM user:** a named login inside the account, weaker than root, with its own password or access keys.
- **Access key:** a long-lived pair of letters used by programs to call AWS.
- **CloudTrail Event history:** AWS's free 90-day list of actions taken in the account.
- **GuardDuty:** AWS's threat detection service, which watches for odd activity and can email findings.
- **Private operations reference:** the owner's private file, outside the repository, holding every account and resource id.

## What was already decided before this document

- **Hosting on AWS in the Mumbai region** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Hosting: AWS Mumbai").
- **Rebuild instead of patching** (owner decision, 2026-09-13, "Rebuild instead of patching").
- **The owner runs every step that needs AWS rights** (owner decision, 2026-09-14, recorded while planning #40, #41 and #46; restated for this ticket on 2026-09-15). Claude prepares the steps and verifies the results with read-only checks.
- **How this review is done** (owner decision, 2026-09-15, "AWS account security review", answered while planning this ticket):
  - the root account is protected with an authenticator app;
  - nobody else has an AWS console sign-in;
  - GuardDuty is switched on now;
  - CloudTrail stays at the free 90-day Event history until staging is built;
  - GuardDuty alerts go to the email already used for this AWS account, recorded only in the private operations reference.

## What exists today (2026-09-15)

- Staging and production will live in this same AWS account.
- The first version's server is being retired under #40, #41 and #46.
- The live list of root MFA, IAM users, access keys, CloudTrail and GuardDuty is not written here.
- That list is taken from AWS at implementation time and kept in the private operations reference.

## The change

The owner runs each step in the session, using the AWS profile the private reference names for PolluxKart.
Claude first runs the read-only "before" checks in the test plan.
If any check does not match, stop and ask the owner before changing anything.

| Step | What the owner does | Can it be undone? |
|---|---|---|
| 1 | Confirm the signed-in account is PolluxKart's | Nothing changed yet |
| 2 | Turn on authenticator-app MFA for the root account if it is not already on | The MFA device can be removed later, which would weaken the account |
| 3 | Confirm the root account has no access keys; if any exist, delete them | A new root key could be created; that is not part of this ticket |
| 4 | List every IAM user and access key. Keep only the owner's console login. Disable or delete any other console user after the owner confirms it is not needed. For any remaining access key, write a one-line purpose in the private reference, or delete the key | Disabled users can be re-enabled; deleted users cannot |
| 5 | Read CloudTrail Event history for unexpected activity. Raise anything unexpected with the owner the same day. Keep the findings privately | Nothing changed |
| 6 | Switch GuardDuty on in the Mumbai region, and confirm findings notify the email already on the AWS account | GuardDuty can be switched off later |
| 7 | Update the private operations reference with the date, what changed, and "pending" lines ticked. Add a dated one-line note to `docs/platform/runbook.md` "Current state", with no ids and no findings | Yes: the runbook line can be edited |

Exact console paths and commands live in the private operations reference, not here.

### Recording the result

- **Private operations reference:** the date, which users and keys remain, that root MFA is on, that GuardDuty is on, and that the alert email matches the address already on the account.
- **Ticket #42:** a comment with the date and "done and verified", listing the checks by name only, with no ids. Then `stage: done`, and the ticket is closed as completed.
- **runbook.md:** one dated line that the AWS account security review was done, with no findings.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| The AWS profile points at a different account | Stop before anything changes |
| Root MFA is already on with an authenticator app | Step 2 records that and continues |
| Root MFA is already on with a hardware key | Keep it. Do not replace it with an authenticator app. Record it privately and continue |
| An IAM user or access key has an unclear purpose | Stop and ask the owner before deleting it |
| CloudTrail shows unexpected activity | Stop the remaining change steps, tell the owner the same day, and keep the detail privately |
| GuardDuty is already on | Step 6 records that, checks the notification email, and continues |
| The account email in AWS does not match the private reference | Stop and ask the owner before sending alerts anywhere new |
| A later look, on another day, shows MFA off or a new access key | Raise it with the owner the same day; that second look is part of verification |

## What is deliberately not covered

- **The monthly budget alert:** #43 (E01-04).
- **Credentials the first version used outside AWS,** such as Razorpay or Firebase: #44 (E01-05).
- **A longer CloudTrail copy in S3:** deferred until staging is built (E06).
- **The GitHub deploy identity that uses short-lived credentials:** E06-01.
- **A hardware security key** as a second MFA device: not in this ticket. The owner chose an authenticator app.

## Open questions for the owner

None open.
All questions this ticket raised were answered on 2026-09-15 and are recorded in [decisions.md](../../platform/decisions.md), "AWS account security review".
