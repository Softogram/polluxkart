# E01-04 AWS monthly budget alert

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-16)**
Ticket: #43 (E01-04), part of epic #11.
Test plan: [../test/issue-43-aws-budget-alert.md](../test/issue-43-aws-budget-alert.md)

This ticket changes the live AWS account, not application code.
Sensitive details (the recipient email, the account id) stay in the private operations reference.

## Words used below

- **AWS Budget:** a monthly amount AWS compares the account's bill against. It emails; it does not stop spending.
- **Actual spend:** what AWS has already billed this month.
- **Forecasted spend:** AWS's prediction of the month's total from use so far.
- **Alert level:** a percentage of the budget that causes an email, such as 80% actual or 100% forecasted.
- **Private operations reference:** the owner's private file, outside the repository, holding every account and resource id.

## What was already decided before this document

- **Hosting on AWS in the Mumbai region** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Hosting: AWS Mumbai").
- **The owner runs every step that needs AWS rights** (owner decision, 2026-09-14, recorded while planning #40, #41 and #46). Claude prepares the steps and verifies the results with read-only checks.
- **GuardDuty alerts go to the email already used for this AWS account**, recorded only in the private operations reference (owner decision, 2026-09-15, "AWS account security review").
- **How this budget is set** (owner decision, 2026-09-16, "AWS monthly budget alert", answered while planning this ticket):
  - the monthly limit now is $10;
  - the limit is raised when staging is built (#85, E06-03) and again when production is built (#175, E18-01), using the estimates in [cost.md](../../platform/cost.md) as a guide, with the exact new amounts chosen in those tickets;
  - emails go out at 80% actual, 100% actual, and 100% forecasted;
  - the recipient is the same address already chosen for GuardDuty.

## What exists today (2026-09-16)

- Only the maintenance site and leftover first-version resources should be billing.
- The IAM user used for day-to-day AWS work cannot create budgets. The owner uses an admin sign-in.
- No amount or email is written here.

## The change

The owner runs each step in the session, using the AWS profile the private reference names for PolluxKart.
Claude first runs the read-only "before" checks in the test plan.
If any check does not match, stop and ask the owner before changing anything.

| Step | What the owner does | Can it be undone? |
|---|---|---|
| 1 | Confirm the signed-in account is PolluxKart's | Nothing changed yet |
| 2 | Create one monthly cost budget of $10, with emails at 80% actual, 100% actual, and 100% forecasted, sent to the same address GuardDuty uses | The budget can be edited or deleted |
| 3 | Confirm that address matches the private operations reference | Nothing extra changed |
| 4 | Temporarily set the budget amount to $0.01 so current spend already crosses 80% and 100%, wait for the emails, then restore $10 and confirm the settings | Yes: restoring $10 is the point of this step |
| 5 | Update the private operations reference with the date, the $10 amount, the three alert levels, and that the recipient matches GuardDuty. Add a dated one-line note to `docs/platform/runbook.md` "Current state", with no email and no account id | Yes: the runbook line can be edited |

Exact console paths and commands live in the private operations reference, not here.

The $10 amount may appear in `decisions.md` and `cost.md` because the owner chose it as a product decision. The email never does.

### Recording the result

- **Private operations reference:** the date, $10, the three alert levels, and that the recipient is the GuardDuty address.
- **Ticket #43:** a comment with the date and "done and verified", listing the checks by name only, with no email. Then `stage: done`, and the ticket is closed as completed.
- **runbook.md:** one dated line that the monthly budget alert exists, with no email and no amount.
- **#85 and #175:** a comment on each, pointing at this decision, so the raise is not forgotten when those tickets are planned.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| The AWS profile points at a different account | Stop before anything changes |
| A monthly cost budget already exists | Do not create a second one. Align its amount and alert levels with this design, or stop and ask if it is for something else |
| The GuardDuty email in the private reference does not match the AWS account email | Stop and ask the owner before sending budget mail anywhere new |
| The test emails have not arrived after 24 hours | Do not restore $10 until they have, or until the owner decides the test is good enough from the Budgets console showing the alerts as triggered. Then restore $10 |
| Restoring $10 is forgotten after the test | The later-day check fails; tell the owner the same day and restore $10 |
| AWS bills in a currency other than US dollars | Set the budget in that currency at the equivalent of $10, record the currency privately, and say so on the ticket without the account id |
| A later look shows the amount is not $10, or an alert level is missing | Tell the owner the same day |

## What is deliberately not covered

- **CloudWatch alarms for the running store:** E18-03.
- **Cost reports or dashboards.**
- **Choosing the new amounts for staging and production:** #85 and #175, using [cost.md](../../platform/cost.md) (roughly $25 to $35 staging, $40 to $100 production) and the AWS Pricing Calculator figures those tickets will have.
- **The AWS account security review:** #42.

## Open questions for the owner

None open.
All four questions this ticket raised were answered on 2026-09-16 and are recorded in [decisions.md](../../platform/decisions.md), "AWS monthly budget alert".
