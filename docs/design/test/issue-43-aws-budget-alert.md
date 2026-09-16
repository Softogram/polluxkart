# Test plan: E01-04 AWS monthly budget alert

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-16)**
Ticket: #43.
Design: [../low-level/issue-43-aws-budget-alert.md](../low-level/issue-43-aws-budget-alert.md)

This ticket changes the live AWS account, not code, so the "tests" are checks run once, before and after the action, by someone other than the person clicking in the console.
Terms such as AWS Budget, actual spend and forecasted spend are explained at the top of the design.

## How these checks run

- **Before:** Claude runs read-only checks and confirms the starting state, so the owner is aimed at the right account.
- **During:** the owner runs each step; the console or command output is the first evidence.
- **After:** Claude runs independent read-only checks. A check is never "the console said so": each is a separate read.
- **A second look, on a later day:** Claude repeats A2, A3 and A4, so the test amount was not left in place.
- Results go to the ticket as pass or fail by check name. The email address and account id stay in the private reference.
- AWS reads use the PolluxKart profile named in the private reference. If that profile cannot read Budgets, the owner pastes the read-only output in the session.

## Before the changes

| Id | Check | Expected |
|---|---|---|
| B1 | The AWS account the profile signs in to | PolluxKart's account |
| B2 | Whether a monthly cost budget already exists | Recorded privately as none, or its amount and alert levels |
| B3 | The email AWS already has for the account, and the GuardDuty destination | They match each other and the private reference; the address is never written in this repository |

If B1 or B3 differs, stop and ask the owner before changing anything.

## After the changes

| Id | Check | Expected |
|---|---|---|
| A1 | The AWS account the profile signs in to | Still PolluxKart's account |
| A2 | Monthly cost budgets | Exactly one, amount $10 |
| A3 | Alert levels on that budget | 80% actual, 100% actual, 100% forecasted |
| A4 | Alert subscriber | The GuardDuty address, matching the private reference |
| A5 | Test emails | The owner confirms receiving the 80% and 100% actual mails after the $0.01 test, then $10 is restored (A2) |
| A6 | `docs/platform/runbook.md` | A dated line that the monthly budget alert exists, with no email and no amount |
| A7 | Comments on #85 and #175 | Each points at this decision so the later raise is not forgotten |

**Passing partner.** B2 shows the old state, so A2 passing after a "none" start means the budget was created.

## Second look, on a later day

| Id | Check | Expected |
|---|---|---|
| S1 | Monthly cost budgets | Still exactly one, still $10 |
| S2 | Alert levels | Still 80% actual, 100% actual, 100% forecasted |
| S3 | Alert subscriber | Still the GuardDuty address |

## When a step fails

| Failure | What to do |
|---|---|
| B1 fails | Nothing changed; fix the profile with the owner, then start again |
| B2 finds a budget that is not this one | Do not create a second; ask the owner |
| B3 or A4 does not match the private reference | Do not add a new email; ask the owner |
| A5 emails have not arrived after 24 hours | See the design; restore $10 once the owner is satisfied the alerts fired |
| S1 shows $0.01 still | Restore $10 the same day; tell the owner |

## Acceptance criteria and the checks that prove them

| Acceptance criterion | Checks |
|---|---|
| The budget exists with the owner's $10 limit and three alert levels | A2, A3, S1, S2 |
| An alert email was received at the chosen address | A5, A4, S3 |
| The limit and recipient are recorded in the private operations reference | A4, and the private file itself |

## What is deliberately not covered, and why

- **A unit test in CI:** this work is in a live account, not in `api/` or `web/`.
- **Proving AWS will email on a real cost spike months later:** A5 proves mail delivery once; S1 to S3 prove the settings stayed.
- **The new staging and production amounts:** #85 and #175.
