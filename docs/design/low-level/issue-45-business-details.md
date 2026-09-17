# E01-06 Business details for the site, invoices and legal pages

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-17)**
Ticket: #45 (E01-06), part of epic #11.
Test plan: [../test/issue-45-business-details.md](../test/issue-45-business-details.md)

This ticket collects the seller details later tickets copy onto the site, invoices and legal pages.
The values stay in the private operations reference.
This document records the choices, never the legal name, address, GSTIN, email, phone or a person's name.

## Words used below

- **Legal name:** the business name on the GST registration certificate.
- **Trading name:** a different name shoppers might see. The owner chose none; shoppers see the legal name.
- **GSTIN:** the shop's 15-character GST registration number.
- **Registered state:** the state on that certificate. A delivery in that state charges CGST and SGST; a delivery to another state charges IGST.
- **Grievance officer:** the person named on the site to handle customer complaints.
- **DPDP contact:** the person named for shoppers who want to download, correct or delete their personal data, under India's Digital Personal Data Protection Act, 2023.
- **Signature image:** a picture of a handwritten signature printed on GST invoices.
- **Private operations reference:** the owner's private file, outside the repository.

## What was already decided before this document

- **The shop has a GSTIN and the site produces GST invoices** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "GST tax invoices").
- **Payments through a new Razorpay merchant account** (owner decision, 2026-09-13, "Payments: Razorpay").
- **No contact details on the maintenance page until this ticket**, then the full contact card at once (owner decision, 2026-09-14, recorded while planning #40, #41 and #46).
- **How these details are collected** (owner decision, 2026-09-17, "Business details for the site, invoices and legal pages", answered while planning this ticket):
  - shoppers see the GST-registered legal name; there is no separate trading name;
  - the business is registered in Uttar Pradesh;
  - shoppers see a support email and phone, not opening hours;
  - the details stay in the private operations reference until the site tickets copy them;
  - the owner is the grievance officer and the DPDP contact;
  - GST invoices carry a signature image.

## What exists today (2026-09-17)

- The owner has given the values in chat. They are written in the private operations reference, marked as not yet compared with the GST registration certificate.
- This repository, this ticket and this document contain none of those values.
- Waiting tickets that need the details, and must not receive the values in a public comment: #41 (maintenance contact card), #154 (store tax settings), #169 (legal page content), #171 (seller details in the footer), #172 (grievance officer page).

## The change

The owner confirms the private record against the GST registration certificate, in the session so the result is visible.
Claude never pastes a value into chat, a ticket, or this repository.

| Step | What the owner does | Can it be undone? |
|---|---|---|
| 1 | Open the GST registration certificate next to the private operations reference | Nothing changed yet |
| 2 | Compare legal name, address, state and GSTIN line by line. If the certificate has a fuller address (building, PIN) or a different spelling, update the private reference from the certificate. Do not invent a PIN or a line that is not on the certificate | Yes: the private file can be edited |
| 3 | Confirm the GSTIN is 15 characters and its first two digits are Uttar Pradesh's GST code (`09`) | Nothing extra changed |
| 4 | Copy the grievance officer's printed name and designation from the certificate's authorized signatory into the private reference, if those fields are still empty. Use the same support email and phone already recorded | Yes: the private file can be edited |
| 5 | Confirm a signature image is not required in this ticket; the file is supplied when #154 is implemented | Nothing changed |
| 6 | Comment on #41, #154, #169, #171 and #172 that the details are ready in the private operations reference, with no values | Yes: comments can be edited |
| 7 | Add a dated one-line note to `docs/platform/runbook.md` "Current state" that the business details exist in the private operations reference, naming none of them. Confirm on this ticket that the details are complete, without pasting them | Yes: the runbook line can be edited |

### Recording the result

- **Private operations reference:** every field has a value, a date, and "matched the GST certificate" or the reason a field was updated from the certificate.
- **Ticket #45:** a comment with the date and "done and verified", listing check names only, with no values. Then `stage: done`, and the ticket is closed as completed.
- **runbook.md:** one dated line that the business details are recorded privately, with no values.
- **Waiting tickets:** each has a comment that the details are ready, with no values.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| The certificate's legal name, GSTIN or state differs from the private reference | The certificate wins. Update the private reference. Do not change this repository |
| The address in the private reference is shorter than the certificate (no PIN, no building) | Copy the certificate's full address into the private reference. Do not guess a PIN |
| The GSTIN is not 15 characters, or its prefix is not `09` | Stop. Ask the owner to re-read the certificate |
| The certificate has no authorized signatory name | Stop and ask for the printed name and designation as they should appear on `/grievance` |
| A waiting-ticket comment would need a value to make sense | Put that value only in the private reference; the comment says only that the details are ready |
| A later ticket needs a field that is still "not yet given" | Stop that ticket and ask; do not invent it |
| The owner wants these values in the public repository before the site tickets copy them | That would need a new owner decision. This ticket keeps them private |

## What is deliberately not covered

- **Invoice prefix and numbering:** #154 and #155 (E15-01, E15-02).
- **The signature image file:** #154 (E15-01).
- **Legal page text:** #169 (E17-01).
- **The grievance process and timelines:** #172 (E17-04). The person is named here; the 48-hour and one-month rules stay with that ticket.
- **Putting the contact card on the live maintenance page:** #41, after this ticket is done.
- **Chartered accountant and lawyer sign-off:** #159 and #173.

## Open questions for the owner

None open.
The questions this ticket raised were answered on 2026-09-17 and are recorded in [decisions.md](../../platform/decisions.md), "Business details for the site, invoices and legal pages".
The values themselves live only in the private operations reference.
