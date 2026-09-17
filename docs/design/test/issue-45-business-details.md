# Test plan: E01-06 Business details for the site, invoices and legal pages

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-17)**
Ticket: #45.
Design: [../low-level/issue-45-business-details.md](../low-level/issue-45-business-details.md)

This ticket collects details, not code, so the "tests" are checks run once, before and after the certificate comparison.
Terms such as GSTIN, grievance officer and private operations reference are explained at the top of the design.
No check output in git, a ticket or chat may contain the legal name, address, GSTIN, email, phone or a person's name.

## How these checks run

- **Before:** Claude confirms the private operations reference has a row for every field this ticket collects, from the owner's answers.
- **During:** the owner compares the GST registration certificate with that file.
- **After:** Claude checks this repository and the waiting tickets for leaked values, and that the waiting tickets were told the details are ready.
- **A second look, on a later day:** Claude repeats the leak search.
- Results go to the ticket as pass or fail by check name only.

## Before the changes

| Id | Check | Expected |
|---|---|---|
| B1 | The private operations reference | A row for legal name, address, state, GSTIN, support email, support phone, grievance officer, DPDP contact, and invoice signature method |
| B2 | GSTIN in that file | 15 characters; first two digits are Uttar Pradesh's GST code (`09`) |
| B3 | This issue, this design, `decisions.md` and `runbook.md` | No legal name, address, GSTIN, email, phone or person's name |

If B1 is missing a row, stop and finish the private file first.

## After the changes

| Id | Check | Expected |
|---|---|---|
| A1 | Legal name, address, state and GSTIN in the private reference | Each marked as matched to the GST certificate, or updated from it, with a date |
| A2 | Grievance officer printed name and designation in the private reference | Present, taken from the certificate's authorized signatory, or the owner stopped and asked |
| A3 | DPDP contact in the private reference | The same person as the grievance officer |
| A4 | This issue, this design, `decisions.md`, `runbook.md`, and comments on #41, #154, #169, #171 and #172 | Still no values |
| A5 | Comments on #41, #154, #169, #171 and #172 | Each says the details are ready in the private operations reference |
| A6 | `docs/platform/runbook.md` | A dated line that the business details exist privately, with no values |
| A7 | The owner, on this issue | Confirms the details are complete, without pasting them |

**Passing partner.** B3 shows a clean start, so A4 passing after the comments are added means nothing leaked while recording the result.

## Second look, on a later day

| Id | Check | Expected |
|---|---|---|
| S1 | This issue, `decisions.md`, `runbook.md`, and the waiting-ticket comments | Still no values |
| S2 | The private operations reference | Still has every field from A1 and A2 |

## When a step fails

| Failure | What to do |
|---|---|
| B1 missing a field | Add it from the owner's answers; do not comment on waiting tickets yet |
| B2 fails | Stop; the owner re-reads the certificate |
| A1 does not match the certificate | Update the private reference from the certificate; do not invent lines |
| A2 has no printed name | Stop and ask; do not put "the owner" on the public grievance page |
| A4 finds a value in a public place | Remove it the same day; the value stays only in the private reference |
| A5 missing a waiting ticket | Add the comment, with no values |

## Acceptance criteria and the checks that prove them

| Acceptance criterion | Checks |
|---|---|
| Every question this ticket asked has an owner answer | B1, A1, A2, A3 |
| The GSTIN is 15 characters and matches the GST certificate | B2, A1 |
| Legal name, address and state match the GST certificate | A1 |
| The values are stored only in the private operations reference and appear nowhere in this issue | A4, A7, S1 |
| #41, #154, #169, #171 and #172 are told the details are ready | A5 |

## What is deliberately not covered, and why

- **A unit test in CI:** the values must not be fixtures in the public repository.
- **Putting the values on the live site:** #41, #154, #169, #171 and #172.
- **The signature image file:** #154.
