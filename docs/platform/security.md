# Security

Parent: [platform/](README.md) | Index: [docs/](../README.md)

**Status: PROPOSED (2026-09-13).** Written from the plan the owner approved on 2026-09-13. Owner decisions are marked in [decisions.md](decisions.md); everything else here is confirmed or changed in its GitHub ticket before anything is built on it. No code exists yet.
Every rule here answers a real failure found in the first version, listed in [../legacy/audit-2026-09.md](../legacy/audit-2026-09.md).

## The rules, in one table

| Area | Rule | Answers legacy finding |
|---|---|---|
| Sessions | Random token in an httpOnly, Secure, SameSite=Lax cookie named with the `__Host-` prefix; only its SHA-256 hash is stored; the user and role are reloaded on every request | Token in localStorage; role trusted from the token for 24 hours |
| Admin access | Every admin endpoint lives under `/api/v1/admin/**` and the security configuration requires the admin role for the whole path; admins must use TOTP; admin sessions time out after 30 minutes idle and 12 hours total | Admin actions open to any signed-in user |
| The second door | If one path to some data is guarded, every other path to the same data needs the same guard, and a test proves it | Product edits guarded in admin routes but open in public routes |
| Ownership | Every read or change by id checks the resource belongs to the caller; a test tries another user's order, invoice and address | Possible IDOR on payments |
| Password reset | Single-use token emailed to the verified address, stored hashed, valid 30 minutes; using it revokes every session; responses are identical whether the email exists | Anyone could reset anyone's password |
| Account linking | Signing in with Google onto an account whose email was never verified removes that account's password and sessions | Prevents a pre-registered attacker keeping access |
| Setup and debug | No setup, debug or data-wiping endpoints; the first admin is created by a one-off command on the server, recorded in the audit log | Public OTP debug endpoint; default admin setup key; seed wipe endpoint |
| Rate limits | Sign-in by IP and email; reset and verification by email and IP; order creation by user; a global per-IP limit; 429 responses | No rate limiting |
| CSRF | Cookie-based CSRF token checked on every state-changing request, webhooks exempt because they are signature-verified | Not applicable before; required with cookies |
| Responses | Built from explicit response records listing allowed fields; entities never serialized | Password hashes leaked by removing the wrong field name |
| Money | Totals always recomputed on the server; the client's expected total is only compared | Client-computed totals |
| Payments | Signature checked in constant time; payment fetched from Razorpay to confirm amount and capture; webhook signature over the raw bytes; events deduplicated by id; missing keys stop the app from starting | Webhook check broken; checks skipped when keys missing |
| Uploads | Presigned S3 upload with size and type limits; server reads the first bytes to confirm JPEG, PNG, WebP or AVIF; never SVG; served only from `media.polluxkart.com` | Stored XSS through uploads served from the API origin |
| Search | PostgreSQL full-text search with bound parameters, never string-built queries | Raw user input in database regular expressions |
| Browser | Content Security Policy on every page; only first-party scripts plus Razorpay on checkout; `frame-ancestors 'none'` | Third-party builder scripts that forwarded logs to framing pages |
| Headers | HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, no server version headers | None set |
| Documentation | Public API docs are not exposed in production | Public Swagger UI in production |

## Secrets

- Secrets never enter git, in three layers.
`.env` files are git-ignored.
gitleaks, an open-source secret scanner, checks the staged changes in the pre-commit hook and, in `make ci`, the branch's own commits plus every tracked file as it is now.
GitHub's own secret scanning and push protection watch the whole history and every push.
Every run redacts what it finds, so no log ever repeats a secret.
- A false alarm is allowed by one entry in `.gitleaks.toml`, added by anyone through a pull request, each with a description starting `YYYY-MM-DD:` and a reason (owner decision, 2026-09-14).
A check enforces the dated reason. Inline `gitleaks:allow` comments are refused, and an entry narrowed by commit id is refused because squash merging changes commit ids.
- The person pushing may bypass a GitHub push protection block by giving a reason; GitHub alerts the owner either way, and only the owner receives those alerts (owner decision, 2026-09-14).
Owner-only approval of a bypass needs GitHub's paid Secret Protection add-on, which is not bought.
- Development uses test-mode keys in a local `.env`.
- Production secrets live in AWS SSM Parameter Store as encrypted values and reach the server at deploy time.
- CI deploys through short-lived AWS credentials (GitHub OIDC), never stored access keys.
- Any secret that ever reaches a commit (pushed or not), a pushed branch, a document, a chat, a ticket or a log is treated as public and rotated the same day (owner decision, 2026-09-14).
A key the pre-commit hook blocked before any commit existed does not need rotating, only removing.
- The repository is public: account ids, live resource ids and credential status belong in the private operations reference described in [runbook.md](runbook.md), never in this tree.

## Personal data

- Personal data (names, emails, phones, addresses) never appears in logs; request ids are logged instead.
- Error monitoring sends no personal data.
- Addresses on orders are snapshots, so deleting an account anonymizes the account without changing issued invoices.
- A shopper can export and delete their data; invoices are kept for the period GST law requires.
- Details of the legal duties: [../product/compliance.md](../product/compliance.md).

## Dependencies and scanning

- Dependabot pull requests weekly for Maven, pnpm, Docker and GitHub Actions.
- `osv-scanner` for known vulnerabilities in CI.
- CodeQL analysis on the public repository.
- GitHub Actions pinned to full commit SHAs with read-only default permissions.
- An OWASP ZAP baseline scan runs nightly against staging.

## Infrastructure

- No SSH port on servers; access through AWS Systems Manager.
- The database sits in private subnets, reachable only from the application server.
- Two database roles: one for migrations, one for the running app, which cannot alter tables or delete audit rows.
- Root account protected with MFA; CI and servers use roles, not long-lived keys.

## Before launch

An OWASP ASVS Level 2 walkthrough (a standard checklist of web application security requirements) using the security skill, with every item either met or written up with the reason.

## See also (do not follow recursively)

- [../services/identity/README.md](../services/identity/README.md) - accounts, sessions and sign-in
- [../services/payment/README.md](../services/payment/README.md) - Razorpay verification
