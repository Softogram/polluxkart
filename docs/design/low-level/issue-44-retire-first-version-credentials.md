# E01-05 Retire the credentials used by the first version

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-16)**
Ticket: #44 (E01-05), part of epic #11.
Test plan: [../test/issue-44-retire-first-version-credentials.md](../test/issue-44-retire-first-version-credentials.md)

This ticket changes live logins at outside services, not application code.
The list of credentials, their values, and what happened to each stay in the private operations reference.
This document names kinds of service, never a key, a project id, or whether a key still works.

## Words used below

- **Credential:** a password, API key, token or private key that grants access to something.
- **Revoke / disable:** tell the provider that key must no longer work.
- **Rotate:** replace a key with a new one and switch the old one off.
- **Merchant account:** the shop's login at the payment company.
- **Firebase:** Google's hosted backend product. The rebuild signs in with Google without it.
- **Private inventory:** the table in the private operations reference of every outside account the first version used.

## What was already decided before this document

- **A new Razorpay merchant account for the relaunch**, with keys only locally and in a secrets store (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Payments: Razorpay").
- **Rebuild instead of patching**, first version kept only as reference (owner decision, 2026-09-13, "Rebuild instead of patching").
- **Email and password plus Sign in with Google at launch** (owner decision, 2026-09-13, "Login: email and Google at launch, phone OTP later").
- **The owner runs every step that needs account access** (owner decision, 2026-09-14, recorded while planning #40, #41 and #46). Claude prepares the steps and verifies with read-only checks.
- **AWS access keys and console logins** are #42, not this ticket.
- **How first-version credentials are retired** (owner decision, 2026-09-16, "Retiring the first version's credentials", answered while planning this ticket):
  - disable the old payment-gateway keys and keep that merchant account for records;
  - delete the first version's Firebase project; the store does not use Firebase;
  - close each unused outside account; replace keys only on an account the owner still needs;
  - the owner's own check that each line is retired is enough.

## What exists today (2026-09-16)

- A private inventory already lists the kinds of outside account found in `legacy/` and on the owner's machine.
- The rebuild, outside `legacy/`, must not depend on any of those credentials.
- Git history of the first version may still contain old secrets. Those copies cannot be erased from the public history. Retiring the live keys is what makes them useless. GitHub's secret scanning watches the history privately (#37).

## The change

The owner works through the private inventory, one line at a time, in the session so the result is visible.
Claude never pastes a secret into chat, a ticket, or this repository.

| Step | What the owner does | Can it be undone? |
|---|---|---|
| 1 | Confirm the private inventory lists every outside account found in `legacy/` and in the owner's logins. Add any missing line before changing anything | Nothing changed yet |
| 2 | Payment gateway: disable every API key on the first version's merchant account. Keep the account open for records. If you cannot sign in, recover the account from its registered email, then disable the keys | Disabled keys can be replaced later on that account; the new relaunch account stays separate |
| 3 | Firebase: delete the first version's project. Do not create a replacement for the store | A deleted project cannot be undeleted after Google's grace period |
| 4 | Every other inventory line (image hosting and the rest): if the rebuild does not need that account, close it, or disable its keys and close it. If the owner still needs the account for something else, replace its keys and keep it | Closed accounts usually cannot be reopened |
| 5 | Confirm the rebuild, outside `legacy/`, has none of those credentials in any `.env`, secrets store, or config the new store uses | Yes: this is a search |
| 6 | For each revoked key, a harmless request using it is refused by the provider. Record date and method on that inventory line. The owner reads every line and confirms | The check can be repeated |
| 7 | Update the private operations reference. Add a dated one-line note to `docs/platform/runbook.md` "Current state" that the first version's credentials were retired, naming none of them | Yes: the runbook line can be edited |

Exact recovery URLs, key ids and project names live only in the private operations reference.

### Recording the result

- **Private operations reference:** every inventory line has a date, the action (keys disabled / rotated / account closed / not ours to rotate), and the method of the refused-request check.
- **Ticket #44:** a comment with the date and "done and verified", listing check names only, with no credential names, values or status. Then `stage: done`, and the ticket is closed as completed.
- **runbook.md:** one dated line that the first version's credentials were retired, with no names.
- **decisions.md:** the Firebase answer is already the dated owner decision below. No project details.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| You cannot sign in to the old payment-gateway account | Recover it from the registered email, then disable the keys. Do not skip this line. The new merchant account does not retire the old keys |
| A provider needs GSTIN or PAN to prove ownership | Use the details collected in #45 if they exist; otherwise stop and ask. Do not paste those details into this repository |
| An inventory line belongs to a third-party builder, not to PolluxKart | Record "not ours to rotate" with the reason. Do not try to log in |
| An account the owner still needs | Keep it, replace its keys, and record the date. Never put the new keys in git, a document, a chat or a ticket |
| A secret is still in a local `.env` the rebuild uses | Remove it the same day. The rebuild must not load first-version keys |
| A harmless request to a disabled key still succeeds | Treat the key as live. Repeat the disable step. Do not tick that line |
| Git history still contains the old secret | Expected. The live key must be disabled; history is not rewritten |
| A later look finds a first-version key in rebuild config | Tell the owner the same day and remove it |

## What is deliberately not covered

- **The AWS access review and the deployer key:** #42 (E01-03).
- **Setting up the new Razorpay account for live payments:** E19-02.
- **Google sign-in clients for the rebuild:** E06-08.
- **Rewriting git history** to remove old secrets: not done. The history is public; retiring the live keys is the fix.
- **A second person's confirmation:** the owner chose their own check.

## Open questions for the owner

None open.
All four questions this ticket raised were answered on 2026-09-16 and are recorded in [decisions.md](../../platform/decisions.md), "Retiring the first version's credentials".
